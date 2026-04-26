"""
arq task: scrape a competitor website and store the result as a CompetitorSnapshot.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select

from db.database import async_session_maker
from db.models import Competitor, CompetitorSnapshot, ScrapeStatus, gen_uuid
from pipelines.scraping.crawler import crawl_site
from pipelines.scraping.extractor import extract_pages
from pipelines.scraping.normalizer import normalize_pages

logger = logging.getLogger(__name__)


async def run_scrape(ctx, competitor_id: str) -> None:
    """Full scrape pipeline: crawl → extract → normalize → store snapshot."""
    logger.info(f"Starting scrape for competitor {competitor_id}")

    async with async_session_maker() as session:
        result = await session.execute(select(Competitor).where(Competitor.id == competitor_id))
        competitor = result.scalar_one_or_none()
        if not competitor:
            logger.error(f"Competitor {competitor_id} not found")
            return

        competitor.scrape_status = ScrapeStatus.scraping
        await session.commit()

        try:
            # 1. Crawl
            pages = await crawl_site(competitor.website_url)
            if not pages:
                raise ValueError("No pages crawled from competitor site")

            # 2. Extract structured content from HTML
            extracted = extract_pages(pages)

            # 3. Normalize via Claude Haiku
            normalized = await normalize_pages(extracted, competitor.website_url)

            # 4. Mark all previous snapshots as not current
            old_snapshots = await session.execute(
                select(CompetitorSnapshot).where(
                    CompetitorSnapshot.competitor_id == competitor_id,
                    CompetitorSnapshot.is_current == True,
                )
            )
            for snap in old_snapshots.scalars().all():
                snap.is_current = False

            # 5. Save new snapshot
            raw_pages_data = [
                {"url": p.url, "title": p.title, "content_preview": p.body_text[:300]}
                for p in extracted
            ]
            snapshot = CompetitorSnapshot(
                id=gen_uuid(),
                competitor_id=competitor_id,
                scraped_at=datetime.utcnow(),
                pricing_tiers=normalized.get("pricing_tiers", []),
                key_features=normalized.get("key_features", []),
                target_segments=normalized.get("target_segments", []),
                integration_list=normalized.get("integration_list", []),
                scraped_claims=normalized.get("scraped_claims", []),
                raw_pages=raw_pages_data,
                confidence=normalized.get("confidence", "low"),
                is_current=True,
            )
            session.add(snapshot)

            # 6. Update competitor record
            competitor.scrape_status = ScrapeStatus.ready
            competitor.last_scraped_at = datetime.utcnow()
            if normalized.get("product_name"):
                competitor.product_name = normalized["product_name"]
            if normalized.get("company_name") and not competitor.company_name:
                competitor.company_name = normalized["company_name"]

            await session.commit()
            logger.info(f"Scrape complete for {competitor_id}: {len(pages)} pages, confidence={normalized.get('confidence')}")

        except Exception as e:
            logger.exception(f"Scrape failed for {competitor_id}: {e}")
            competitor.scrape_status = ScrapeStatus.failed
            await session.commit()
