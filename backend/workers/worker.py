"""
arq worker entry point.
Handles: document ingestion, competitor scraping, weekly re-scrape cron.
Run with: python -m workers.worker
"""

import asyncio
import logging
from datetime import datetime, timedelta

import arq
import arq.connections
from sqlalchemy import select

from config import settings
from db.database import async_session_maker
from db.models import Competitor, Document, DocumentChunk, DocumentStatus, ScrapeStatus, gen_uuid
from pipelines.ingestion.extractor import extract
from pipelines.ingestion.chunker import chunk_sections
from pipelines.ingestion.embedder import embed_texts
from pipelines.ingestion.indexer import index_chunks, delete_document_vectors
from pipelines.scraping.tasks import run_scrape
from retrieval.bm25 import rebuild_bm25_index

logger = logging.getLogger(__name__)


async def run_ingestion(ctx, doc_id: str) -> None:
    """Full ingestion pipeline: extract → chunk → embed → index."""
    logger.info(f"Starting ingestion for document {doc_id}")

    async with async_session_maker() as session:
        result = await session.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            logger.error(f"Document {doc_id} not found")
            return

        doc.status = DocumentStatus.ingesting
        await session.commit()

        try:
            sections = extract(doc.file_path)
            chunks = chunk_sections(
                sections,
                chunk_size_tokens=settings.chunk_size_tokens,
                overlap_tokens=settings.chunk_overlap_tokens,
            )

            if not chunks:
                raise ValueError("No content could be extracted from the document")

            texts = [c.text for c in chunks]
            embeddings = embed_texts(texts, settings.embedding_model)

            delete_document_vectors(doc_id)

            old_chunks = await session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == doc_id)
            )
            for old in old_chunks.scalars().all():
                await session.delete(old)

            chroma_ids = index_chunks(doc_id, doc.original_filename, chunks, embeddings)

            for i, (chunk, chroma_id) in enumerate(zip(chunks, chroma_ids)):
                db_chunk = DocumentChunk(
                    id=gen_uuid(),
                    document_id=doc_id,
                    chunk_index=i,
                    section=chunk.section,
                    page_number=chunk.page_number,
                    word_count=chunk.word_count,
                    has_table=chunk.has_table,
                    chroma_id=chroma_id,
                )
                session.add(db_chunk)

            doc.status = DocumentStatus.ready
            doc.chunk_count = len(chunks)
            doc.ingested_at = datetime.utcnow()
            await session.commit()

            rebuild_bm25_index()
            logger.info(f"Ingestion complete for {doc_id}: {len(chunks)} chunks")

        except Exception as e:
            logger.exception(f"Ingestion failed for {doc_id}: {e}")
            doc.status = DocumentStatus.failed
            doc.error_message = str(e)[:500]
            await session.commit()


async def cron_rescrape_competitors(ctx) -> None:
    """Weekly cron: re-scrape competitors whose last_scraped_at is past their interval."""
    logger.info("Running competitor re-scrape cron")
    now = datetime.utcnow()

    async with async_session_maker() as session:
        result = await session.execute(
            select(Competitor).where(Competitor.scrape_status == ScrapeStatus.ready)
        )
        competitors = result.scalars().all()

        queued = 0
        for comp in competitors:
            if comp.last_scraped_at is None:
                should_scrape = True
            else:
                due_at = comp.last_scraped_at + timedelta(days=comp.scrape_interval_days)
                should_scrape = now >= due_at

            if should_scrape:
                await ctx["redis"].enqueue_job("run_scrape", comp.id)
                queued += 1

    logger.info(f"Cron: queued {queued} competitor re-scrapes")


async def startup(ctx) -> None:
    logger.info("Worker starting up — rebuilding BM25 index")
    rebuild_bm25_index()


class WorkerSettings:
    functions = [run_ingestion, run_scrape]
    on_startup = startup
    redis_settings = arq.connections.RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 4
    job_timeout = 600

    cron_jobs = [
        arq.cron(cron_rescrape_competitors, hour={0}, minute={0}),  # daily at midnight UTC
    ]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    arq.run_worker(WorkerSettings)
