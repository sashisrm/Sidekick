"""
Hybrid retrieval: Reciprocal Rank Fusion of semantic + BM25 results.

RRF formula: score(d) = Σ 1 / (k + rank_i)   where k=60
Final result: top_k chunks after fusion, deduped, with compression.
"""

from __future__ import annotations

from config import settings
from pipelines.ingestion.embedder import embed_query
from pipelines.ingestion.indexer import semantic_search
from retrieval.bm25 import get_bm25_index

RRF_K = 60
COMPRESSION_THRESHOLD = 0.2  # drop chunks scoring < 20% of top score


def retrieve(
    query: str,
    top_k: int | None = None,
    doc_ids: list[str] | None = None,
) -> list[dict]:
    """
    Returns up to top_k chunks fused from semantic + BM25 search.
    Each result: {chroma_id, text, doc_id, doc_name, section, page_number, rrf_score}
    """
    top_k = top_k or settings.retrieval_top_k
    n_candidates = max(settings.semantic_candidates, settings.bm25_candidates)

    # 1. Semantic search
    query_vec = embed_query(query, settings.embedding_model)
    semantic_hits = semantic_search(query_vec, top_k=n_candidates, doc_ids=doc_ids)

    # 2. BM25 search
    bm25_hits = get_bm25_index().search(query, top_k=n_candidates)

    # 3. RRF fusion
    rrf_scores: dict[str, float] = {}
    hit_map: dict[str, dict] = {}

    for rank, hit in enumerate(semantic_hits):
        cid = hit["chroma_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        hit_map[cid] = hit

    for rank, hit in enumerate(bm25_hits):
        cid = hit["chroma_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        if cid not in hit_map:
            hit_map[cid] = hit

    # 4. Sort by RRF score
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    # 5. Contextual compression: drop chunks below threshold
    if ranked:
        top_score = ranked[0][1]
        min_score = top_score * COMPRESSION_THRESHOLD
        ranked = [(cid, score) for cid, score in ranked if score >= min_score]

    # 6. Dedup: keep only highest-scoring chunk per (doc_id, section)
    seen_sections: set[tuple] = set()
    final_results = []

    for cid, rrf_score in ranked[:top_k * 2]:  # over-fetch before dedup
        hit = hit_map[cid]
        key = (hit["doc_id"], hit["section"])
        if key in seen_sections:
            continue
        seen_sections.add(key)
        final_results.append({**hit, "rrf_score": rrf_score})
        if len(final_results) >= top_k:
            break

    return final_results
