"""
Write chunks + embeddings to ChromaDB.
Also maintains an in-memory BM25 corpus (rebuilt on worker startup).
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings
from pipelines.ingestion.chunker import Chunk


COLLECTION_NAME = "sidekick_docs"


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=settings.chroma_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def index_chunks(doc_id: str, doc_name: str, chunks: list[Chunk], embeddings: list[list[float]]) -> list[str]:
    """Store chunks in ChromaDB. Returns list of chroma_ids."""
    collection = get_collection()

    chroma_ids = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chroma_id = f"{doc_id}_{i}"
        chroma_ids.append(chroma_id)

        collection.upsert(
            ids=[chroma_id],
            embeddings=[embedding],
            documents=[chunk.text],
            metadatas=[{
                "doc_id": doc_id,
                "doc_name": doc_name,
                "section": chunk.section or "",
                "page_number": chunk.page_number or 0,
                "chunk_index": i,
                "has_table": str(chunk.has_table),
                "word_count": chunk.word_count,
            }],
        )

    return chroma_ids


def delete_document_vectors(doc_id: str) -> None:
    collection = get_collection()
    # ChromaDB supports where filter for deletion
    results = collection.get(where={"doc_id": doc_id}, include=[])
    if results["ids"]:
        collection.delete(ids=results["ids"])


def semantic_search(query_embedding: list[float], top_k: int = 25, doc_ids: list[str] | None = None) -> list[dict]:
    collection = get_collection()

    where = {"doc_id": {"$in": doc_ids}} if doc_ids else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    if results["ids"] and results["ids"][0]:
        for chroma_id, text, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append({
                "chroma_id": chroma_id,
                "text": text,
                "doc_id": meta.get("doc_id", ""),
                "doc_name": meta.get("doc_name", ""),
                "section": meta.get("section", ""),
                "page_number": int(meta.get("page_number", 0)) or None,
                "has_table": meta.get("has_table") == "True",
                "score": 1.0 - dist,  # cosine distance → similarity
            })

    return hits
