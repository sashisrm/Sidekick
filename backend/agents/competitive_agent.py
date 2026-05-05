"""
Competitive agent: combines internal RAG context with competitor snapshot data
to produce a streaming comparison and positioning analysis.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

import anthropic
from sqlalchemy import select

from config import settings
from db.database import async_session_maker
from db.models import Competitor, CompetitorSnapshot, Product
from retrieval.hybrid import retrieve

SYSTEM_PROMPT = """You are a product intelligence analyst helping a sales team understand their competitive position.

You have access to:
1. Internal product documentation (from the company's knowledge base)
2. Competitor data scraped from their public websites

Your job is to provide accurate, specific competitive analysis with clear citations.

Rules:
- Always distinguish between "our product" (from internal docs) and competitor claims
- Cite sources: use [Internal Doc: ...] for internal sources, [Competitor: CompanyName] for scraped data
- Be specific about features, pricing, and positioning differences
- Flag where competitor data may be outdated or uncertain (low confidence scrapes)
- Highlight competitive advantages AND gaps honestly
- Format response as clear markdown with sections"""


async def stream_competitive_response(
    query: str,
    product_id: str | None,
    competitor_ids: list[str],
    user_id: str,
    conversation_history: list[dict],
) -> AsyncGenerator[dict, None]:
    """
    Yields events:
      {"type": "sources", "sources": [...]}
      {"type": "text", "delta": "..."}
      {"type": "done", "tokens_used": N}
    """
    async with async_session_maker() as session:
        # Load competitor snapshots
        comp_data = await _load_competitor_data(session, competitor_ids, user_id)

        # Optionally load product context
        product_context = ""
        if product_id:
            product_context = await _load_product_context(session, product_id, user_id)

    # Retrieve internal RAG context
    internal_chunks = retrieve(query)
    sources = [
        {
            "source_number": i + 1,
            "doc_id": c["doc_id"],
            "doc_name": c["doc_name"],
            "section": c["section"],
            "page_number": c.get("page_number"),
            "chroma_id": c["chroma_id"],
        }
        for i, c in enumerate(internal_chunks)
    ]

    yield {"type": "sources", "sources": sources}

    # Build context for Claude
    internal_context = _format_internal_context(internal_chunks)
    competitor_context = _format_competitor_context(comp_data)

    user_message = f"""Please analyze the following question with the provided context.

{'**Internal Product Context:**\n' + product_context + '\n\n' if product_context else ''}

**Internal Documentation Context:**
{internal_context}

**Competitor Intelligence:**
{competitor_context}

---

Question: {query}

Please provide a thorough competitive analysis addressing this question. Include:
1. Our product's position on this topic (from internal docs)
2. How competitors compare (from scraped data)
3. Key differentiators and gaps
4. Recommendations for positioning"""

    messages = [*[{"role": m["role"], "content": m["content"]} for m in conversation_history[-4:]], {"role": "user", "content": user_message}]

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    total_tokens = 0

    async with client.messages.stream(
        model=settings.claude_sonnet_model,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield {"type": "text", "delta": text}
        final = await stream.get_final_message()
        total_tokens = final.usage.input_tokens + final.usage.output_tokens

    yield {"type": "done", "tokens_used": total_tokens}


async def _load_competitor_data(session, competitor_ids: list[str], user_id: str) -> list[dict]:
    if not competitor_ids:
        # Load all competitors for user
        result = await session.execute(
            select(Competitor).where(Competitor.user_id == user_id)
        )
        competitors = result.scalars().all()
        competitor_ids = [c.id for c in competitors]

    comp_data = []
    for comp_id in competitor_ids:
        result = await session.execute(
            select(Competitor).where(Competitor.id == comp_id, Competitor.user_id == user_id)
        )
        comp = result.scalar_one_or_none()
        if not comp:
            continue

        snap_result = await session.execute(
            select(CompetitorSnapshot).where(
                CompetitorSnapshot.competitor_id == comp_id,
                CompetitorSnapshot.is_current == True,
            )
        )
        snapshot = snap_result.scalar_one_or_none()
        comp_data.append({"competitor": comp, "snapshot": snapshot})

    return comp_data


async def _load_product_context(session, product_id: str, user_id: str) -> str:
    result = await session.execute(
        select(Product).where(Product.id == product_id, Product.user_id == user_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        return ""

    lines = [f"**{product.name}**", product.description]
    if product.features:
        lines.append("Features: " + ", ".join(str(f) for f in product.features[:20]))
    return "\n".join(lines)


def _format_internal_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant internal documentation found."
    parts = []
    for i, chunk in enumerate(chunks, 1):
        page = f" (page {chunk['page_number']})" if chunk.get("page_number") else ""
        parts.append(f"[Internal Doc {i}: {chunk['doc_name']} — {chunk['section']}{page}]\n{chunk['text']}")
    return "\n\n".join(parts)


def _format_competitor_context(comp_data: list[dict]) -> str:
    if not comp_data:
        return "No competitor data available. Add competitors in the Competitive Intelligence section."

    parts = []
    for item in comp_data:
        comp = item["competitor"]
        snap = item["snapshot"]

        section = f"### {comp.company_name}"
        if comp.product_name:
            section += f" ({comp.product_name})"
        section += f"\nWebsite: {comp.website_url}"

        if not snap:
            section += "\n*No data scraped yet — scrape in progress or pending.*"
        else:
            section += f"\n*Data scraped: {snap.scraped_at.strftime('%Y-%m-%d')} | Confidence: {snap.confidence}*\n"

            if snap.pricing_tiers:
                section += "\n**Pricing:**\n"
                tiers = snap.pricing_tiers
                if isinstance(tiers, dict):
                    # stored as {tier_name: price_string}
                    for name, price in list(tiers.items())[:8]:
                        section += f"- {name}: {price}\n"
                else:
                    # stored as [{name, price, billing_period, features}]
                    for tier in tiers[:8]:
                        section += f"- {tier.get('name', 'Tier')}: {tier.get('price', 'N/A')} {tier.get('billing_period', '')}\n"
                        if tier.get('features'):
                            section += "  Features: " + ", ".join(str(f) for f in tier['features'][:5]) + "\n"

            if snap.key_features:
                section += "\n**Key Features:**\n"
                for f in snap.key_features[:15]:
                    section += f"- {f}\n"

            if snap.target_segments:
                section += "\n**Target Segments:** " + ", ".join(str(s) for s in snap.target_segments[:5]) + "\n"

            if snap.scraped_claims:
                section += "\n**Marketing Claims:**\n"
                for claim in snap.scraped_claims[:5]:
                    section += f"- \"{claim}\"\n"

        parts.append(section)

    return "\n\n".join(parts)
