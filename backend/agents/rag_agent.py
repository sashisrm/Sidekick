"""
RAG agent: retrieves relevant chunks and streams a grounded answer via Claude Sonnet.
"""

from __future__ import annotations

from typing import AsyncGenerator

import anthropic

from config import settings
from retrieval.hybrid import retrieve

SYSTEM_PROMPT = """You are a knowledgeable assistant for a company's internal product documentation.
Your job is to answer questions accurately using ONLY the provided context from internal documents.

Rules:
- Base your answer strictly on the provided context. Do not use outside knowledge.
- Always cite your sources using the Source numbers provided (e.g., "According to Source 1...").
- If the answer is not in the provided context, say: "I couldn't find this information in the available documents."
- Be specific and precise. Quote exact values (specs, prices, part numbers) when available.
- Format your response in clear markdown."""

SOURCE_TEMPLATE = "## Source {n}: {doc_name} — {section}{page}"


def _build_context(chunks: list[dict]) -> tuple[str, list[dict]]:
    """Build context string and source list for Claude."""
    context_parts = []
    sources = []

    for i, chunk in enumerate(chunks, start=1):
        page_str = f" (page {chunk['page_number']})" if chunk.get("page_number") else ""
        header = SOURCE_TEMPLATE.format(
            n=i,
            doc_name=chunk["doc_name"],
            section=chunk["section"] or "General",
            page=page_str,
        )
        context_parts.append(f"{header}\n{chunk['text']}")
        sources.append({
            "source_number": i,
            "doc_id": chunk["doc_id"],
            "doc_name": chunk["doc_name"],
            "section": chunk["section"],
            "page_number": chunk.get("page_number"),
            "chroma_id": chunk["chroma_id"],
        })

    return "\n\n".join(context_parts), sources


async def stream_rag_response(
    query: str,
    conversation_history: list[dict],
    doc_ids: list[str] | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Yields events:
      {"type": "sources", "sources": [...]}
      {"type": "text", "delta": "..."}
      {"type": "done", "tokens_used": N}
    """
    # Retrieve relevant chunks
    chunks = retrieve(query, doc_ids=doc_ids)

    if not chunks:
        yield {"type": "sources", "sources": []}
        yield {"type": "text", "delta": "I couldn't find relevant information in the available documents for your question. Please make sure the relevant documents have been uploaded and processed."}
        yield {"type": "done", "tokens_used": 0}
        return

    context, sources = _build_context(chunks)
    yield {"type": "sources", "sources": sources}

    # Build messages for Claude
    messages = []
    for hist_msg in conversation_history[-6:]:  # last 3 turns
        messages.append({"role": hist_msg["role"], "content": hist_msg["content"]})

    user_message = f"""Please answer the following question based on the provided context.

<context>
{context}
</context>

Question: {query}"""

    messages.append({"role": "user", "content": user_message})

    # Stream from Claude
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    total_tokens = 0

    async with client.messages.stream(
        model=settings.claude_sonnet_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield {"type": "text", "delta": text}

        final = await stream.get_final_message()
        total_tokens = final.usage.input_tokens + final.usage.output_tokens

    yield {"type": "done", "tokens_used": total_tokens}
