"""
Extract structured content from crawled HTML pages using BeautifulSoup.
Focuses on pricing tables, feature lists, and headings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from pipelines.scraping.crawler import CrawledPage


@dataclass
class ExtractedPage:
    url: str
    title: str
    headings: list[str]
    pricing_text: str
    feature_items: list[str]
    body_text: str  # truncated clean body text


def extract_pages(pages: list[CrawledPage]) -> list[ExtractedPage]:
    return [_extract_page(p) for p in pages]


def _extract_page(page: CrawledPage) -> ExtractedPage:
    soup = BeautifulSoup(page.html, "html.parser")

    # Remove nav, footer, scripts, styles
    for tag in soup(["nav", "footer", "script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]

    pricing_text = _extract_pricing(soup)
    feature_items = _extract_features(soup)

    # Get cleaned body text (truncated to 3000 chars to keep token count manageable)
    body_text = _extract_body_text(soup)[:3000]

    return ExtractedPage(
        url=page.url,
        title=page.title,
        headings=headings[:30],
        pricing_text=pricing_text,
        feature_items=feature_items[:50],
        body_text=body_text,
    )


def _extract_pricing(soup: BeautifulSoup) -> str:
    """Find pricing tables and price-mention sections."""
    price_pattern = re.compile(r"(\$|€|£|USD|EUR|per\s+month|\/mo|\/year|annually|free|enterprise)", re.IGNORECASE)
    pricing_chunks = []

    # Look for tables
    for table in soup.find_all("table"):
        table_text = table.get_text(separator=" | ", strip=True)
        if price_pattern.search(table_text):
            pricing_chunks.append(table_text[:800])

    # Look for divs/sections with pricing keywords
    for elem in soup.find_all(["section", "div"], class_=re.compile(r"pric|plan|tier|cost", re.IGNORECASE)):
        text = elem.get_text(separator="\n", strip=True)
        if price_pattern.search(text):
            pricing_chunks.append(text[:600])

    # Look for any paragraph containing a price
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if price_pattern.search(text) and len(text) > 10:
            pricing_chunks.append(text)

    return "\n\n".join(pricing_chunks[:5])


def _extract_features(soup: BeautifulSoup) -> list[str]:
    """Extract feature list items — li/dt elements that look like features."""
    features = []
    noise_pattern = re.compile(r"(cookie|privacy|terms|copyright|sign up|log in|contact us)", re.IGNORECASE)

    # Look for ul/ol lists near "features" heading
    feature_sections = soup.find_all(
        ["ul", "ol"],
        # near headings containing "feature", "capability", "what you get" etc.
    )

    for lst in feature_sections:
        items = lst.find_all("li", recursive=False)
        for item in items:
            text = item.get_text(separator=" ", strip=True)
            if 5 < len(text) < 200 and not noise_pattern.search(text):
                features.append(text)

    return list(dict.fromkeys(features))  # deduplicate preserving order


def _extract_body_text(soup: BeautifulSoup) -> str:
    main = soup.find("main") or soup.find("article") or soup.body
    if not main:
        return ""
    text = main.get_text(separator="\n", strip=True)
    # Collapse blank lines
    lines = [l for l in text.splitlines() if l.strip()]
    return "\n".join(lines)
