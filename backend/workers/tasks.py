"""
Thin wrapper to enqueue arq tasks from FastAPI routes.
"""

import arq.connections

from config import settings


async def ingest_document_task(doc_id: str) -> None:
    redis = await arq.connections.create_pool(arq.connections.RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("run_ingestion", doc_id)
    await redis.close()
