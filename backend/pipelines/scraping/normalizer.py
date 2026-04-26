"""
Use Claude Haiku to normalize raw extracted page content into structured competitor JSON.
"""

from __future__ import annotations

import json
import logging
import re

import anthropic

from config import settings
from pipelines.scraping.extractor import ExtractedPage

logger = logging.getLogger(__name__)

NORMALIZE_PROMPT = """You are extracting competitive intelligence from a competitor's website.
Analyze the provided page content and extract structured information.

Return ONLY valid JSON matching this exact schema (no markdown, no explanation):
{
  "company_name": "string or null",
  "product_name": "string or null",
  "pricing_tiers": [
    {
      "name": "string",
      "price": "string (e.g. '$49/mo' or 'Custom' or 'Free')",
      "billing_period": "monthly|annual|one-time|custom|free",
      "features": ["string"]
    }
  ],
  "key_features": ["string"],
  "target_segments": ["string - who is this product for?"],
  "integration_list": ["string - tools/platforms it integrates with"],
  "scraped_claims": ["string - verbatim marketing claims"],
  "confidence": "high|medium|low"
}

Rules:
- Only include information actually present in the content. Never fabricate.
- If pricing isn't visible, set pricing_tiers to []
- Confidence = "high" if pricing and features both found, "medium" if only one, "low" if neither
- key_features: max 20 items, each under 15 words
"""


async def normalize_pages(pages: list[ExtractedPage], competitor_url: str) -> dict:
    """Send all page extracts to Claude Haiku and return normalized structured data."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Build a condensed representation of all pages
    page_summaries = []
    for p in pages[:10]:  # limit to top 10 pages
        summary = f"URL: {p.url}\nTitle: {p.title}\n"
        if p.headings:
            summary += f"Headings: {' | '.join(p.headings[:10])}\n"
        if p.pricing_text:
            summary += f"Pricing content:\n{p.pricing_text[:500]}\n"
        if p.feature_items:
            summary += f"Features found:\n" + "\n".join(f"- {f}" for f in p.feature_items[:20]) + "\n"
        if p.body_text:
            summary += f"Body text (excerpt):\n{p.body_text[:800]}\n"
        page_summaries.append(summary)

    combined = f"Competitor website: {competitor_url}\n\n" + "\n---\n".join(page_summaries)

    try:
        response = await client.messages.create(
            model=settings.claude_haiku_model,
            max_tokens=2048,
            system=NORMALIZE_PROMPT,
            messages=[{"role": "user", "content": combined}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Haiku response as JSON: {e}")
        return _empty_result(competitor_url)
    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        return _empty_result(competitor_url)


def _empty_result(url: str) -> dict:
    return {
        "company_name": None,
        "product_name": None,
        "pricing_tiers": [],
        "key_features": [],
        "target_segments": [],
        "integration_list": [],
        "scraped_claims": [],
        "confidence": "low",
    }
