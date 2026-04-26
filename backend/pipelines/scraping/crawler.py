"""
Async Playwright-based web crawler.
Crawls a competitor site up to max_pages / max_depth, respecting robots.txt.
Returns a list of CrawledPage objects.
"""

from __future__ import annotations

import asyncio
import logging
import re
import urllib.robotparser
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

MAX_PAGES = 20
MAX_DEPTH = 3
REQUEST_DELAY = 2.0  # seconds between requests (polite crawling)

# URL path patterns worth crawling for competitive intel
PRIORITY_PATTERNS = re.compile(
    r"/(pricing|features?|product|solutions?|compare|why|about|platform|plans?|capabilities?)(/|$)",
    re.IGNORECASE,
)


@dataclass
class CrawledPage:
    url: str
    title: str
    html: str
    text_content: str
    depth: int


async def crawl_site(start_url: str, max_pages: int = MAX_PAGES, max_depth: int = MAX_DEPTH) -> list[CrawledPage]:
    """Crawl start_url and linked pages up to max_pages/max_depth."""
    from playwright.async_api import async_playwright

    parsed_root = urlparse(start_url)
    base_domain = parsed_root.netloc
    robot_parser = _build_robot_parser(start_url)

    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(start_url, 0)]  # (url, depth)
    pages: list[CrawledPage] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; SideKickBot/1.0; +https://sidekick.internal/bot)",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        page.set_default_timeout(15000)

        while queue and len(pages) < max_pages:
            url, depth = queue.pop(0)
            normalized = _normalize_url(url)
            if normalized in visited:
                continue
            visited.add(normalized)

            if not _is_same_domain(url, base_domain):
                continue
            if not _is_allowed(robot_parser, url):
                logger.debug(f"robots.txt disallows: {url}")
                continue

            try:
                logger.info(f"Crawling [{depth}] {url}")
                await page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(REQUEST_DELAY)

                title = await page.title()
                html = await page.content()
                text = await page.evaluate("() => document.body.innerText")

                pages.append(CrawledPage(
                    url=url,
                    title=title,
                    html=html,
                    text_content=_clean_text(text),
                    depth=depth,
                ))

                # Discover links for next depth level
                if depth < max_depth:
                    links = await page.eval_on_selector_all(
                        "a[href]",
                        "els => els.map(e => e.href)",
                    )
                    for link in links:
                        normalized_link = _normalize_url(link)
                        if normalized_link and normalized_link not in visited:
                            abs_link = urljoin(url, link)
                            if _is_same_domain(abs_link, base_domain):
                                # Prioritize competitive-intel-rich pages
                                priority = PRIORITY_PATTERNS.search(abs_link) is not None
                                if priority:
                                    queue.insert(0, (abs_link, depth + 1))
                                else:
                                    queue.append((abs_link, depth + 1))

            except Exception as e:
                logger.warning(f"Failed to crawl {url}: {e}")
                continue

        await browser.close()

    logger.info(f"Crawl complete: {len(pages)} pages from {start_url}")
    return pages


def _normalize_url(url: str) -> str:
    """Strip fragment and trailing slash for dedup."""
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}{p.path.rstrip('/')}{'?' + p.query if p.query else ''}".lower()
    except Exception:
        return url.lower()


def _is_same_domain(url: str, base_domain: str) -> bool:
    try:
        return urlparse(url).netloc == base_domain
    except Exception:
        return False


def _is_allowed(rp: urllib.robotparser.RobotFileParser | None, url: str) -> bool:
    if rp is None:
        return True
    return rp.can_fetch("SideKickBot", url)


def _build_robot_parser(start_url: str) -> urllib.robotparser.RobotFileParser | None:
    try:
        parsed = urlparse(start_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp
    except Exception:
        return None


def _clean_text(text: str) -> str:
    """Remove excessive whitespace from extracted text."""
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [l for l in lines if l]
    return "\n".join(non_empty)
