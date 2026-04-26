"""
BM25 index maintained over all ChromaDB documents.
Rebuilt whenever new documents are ingested.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from rank_bm25 import BM25Okapi


@dataclass
class BM25Entry:
    chroma_id: str
    text: str
    doc_id: str
    doc_name: str
    section: str
    page_number: int | None


class BM25Index:
    def __init__(self):
        self._lock = threading.Lock()
        self._entries: list[BM25Entry] = []
        self._index: BM25Okapi | None = None

    def rebuild(self, entries: list[BM25Entry]) -> None:
        tokenized = [e.text.lower().split() for e in entries]
        with self._lock:
            self._entries = entries
            self._index = BM25Okapi(tokenized) if tokenized else None

    def search(self, query: str, top_k: int = 25) -> list[dict]:
        with self._lock:
            if self._index is None or not self._entries:
                return []
            tokens = query.lower().split()
            scores = self._index.get_scores(tokens)
            ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
            results = []
            for idx, score in ranked:
                if score <= 0:
                    continue
                entry = self._entries[idx]
                results.append({
                    "chroma_id": entry.chroma_id,
                    "text": entry.text,
                    "doc_id": entry.doc_id,
                    "doc_name": entry.doc_name,
                    "section": entry.section,
                    "page_number": entry.page_number,
                    "score": float(score),
                })
            return results


# Global singleton — populated at worker/server startup
_bm25_index = BM25Index()


def get_bm25_index() -> BM25Index:
    return _bm25_index


def rebuild_bm25_index() -> None:
    """Pull all docs from ChromaDB and rebuild the BM25 index."""
    from pipelines.ingestion.indexer import get_collection
    collection = get_collection()

    # ChromaDB get() with no filter returns all documents
    results = collection.get(include=["documents", "metadatas"])

    entries = []
    for chroma_id, text, meta in zip(
        results.get("ids", []),
        results.get("documents", []) or [],
        results.get("metadatas", []) or [],
    ):
        entries.append(BM25Entry(
            chroma_id=chroma_id,
            text=text or "",
            doc_id=meta.get("doc_id", ""),
            doc_name=meta.get("doc_name", ""),
            section=meta.get("section", ""),
            page_number=int(meta.get("page_number", 0)) or None,
        ))

    _bm25_index.rebuild(entries)
