"""
Singleton sentence-transformer embedder.
Loaded once at worker startup to avoid re-loading the model for every task.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_model(model_name: str) -> "SentenceTransformer":
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], model_name: str) -> list[list[float]]:
    model = get_model(model_name)
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(query: str, model_name: str) -> list[float]:
    return embed_texts([query], model_name)[0]
