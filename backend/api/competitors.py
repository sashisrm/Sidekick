from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_session
from db.models import Competitor, CompetitorSnapshot, ScrapeStatus, User, gen_uuid

router = APIRouter(prefix="/competitors", tags=["competitors"])


class CompetitorCreate(BaseModel):
    company_name: str
    website_url: str
    category: str = ""
    scrape_interval_days: int = 7


class CompetitorOut(BaseModel):
    id: str
    company_name: str
    website_url: str
    product_name: str | None
    category: str
    scrape_status: str
    last_scraped_at: str | None
    scrape_interval_days: int
    created_at: str
    current_snapshot: dict | None = None


class SnapshotOut(BaseModel):
    id: str
    scraped_at: str
    pricing_tiers: list
    key_features: list
    target_segments: list
    integration_list: list
    scraped_claims: list
    confidence: str
    is_current: bool


@router.post("", response_model=CompetitorOut, status_code=201)
async def add_competitor(
    body: CompetitorCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    competitor = Competitor(
        id=gen_uuid(),
        user_id=current_user.id,
        company_name=body.company_name,
        website_url=str(body.website_url),
        category=body.category,
        scrape_interval_days=body.scrape_interval_days,
        scrape_status=ScrapeStatus.pending,
    )
    session.add(competitor)
    await session.commit()
    await session.refresh(competitor)

    # Trigger background scrape
    await _trigger_scrape(competitor.id)

    return _comp_out(competitor, None)


@router.get("", response_model=list[CompetitorOut])
async def list_competitors(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Competitor)
        .where(Competitor.user_id == current_user.id)
        .options(selectinload(Competitor.snapshots))
        .order_by(Competitor.created_at.desc())
    )
    competitors = result.scalars().all()
    return [
        _comp_out(c, next((s for s in c.snapshots if s.is_current), None))
        for c in competitors
    ]


@router.get("/{competitor_id}", response_model=CompetitorOut)
async def get_competitor(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    comp = await _get_comp(competitor_id, current_user.id, session)
    result = await session.execute(
        select(CompetitorSnapshot)
        .where(CompetitorSnapshot.competitor_id == competitor_id, CompetitorSnapshot.is_current == True)
    )
    snapshot = result.scalar_one_or_none()
    return _comp_out(comp, snapshot)


@router.get("/{competitor_id}/history", response_model=list[SnapshotOut])
async def get_snapshot_history(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _get_comp(competitor_id, current_user.id, session)
    result = await session.execute(
        select(CompetitorSnapshot)
        .where(CompetitorSnapshot.competitor_id == competitor_id)
        .order_by(CompetitorSnapshot.scraped_at.desc())
    )
    return [_snap_out(s) for s in result.scalars().all()]


@router.post("/{competitor_id}/scrape", status_code=202)
async def trigger_scrape(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    comp = await _get_comp(competitor_id, current_user.id, session)
    if comp.scrape_status == ScrapeStatus.scraping:
        raise HTTPException(status_code=409, detail="Scrape already in progress")

    comp.scrape_status = ScrapeStatus.pending
    await session.commit()
    await _trigger_scrape(competitor_id)
    return {"status": "queued"}


@router.delete("/{competitor_id}", status_code=204)
async def delete_competitor(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    comp = await _get_comp(competitor_id, current_user.id, session)
    await session.delete(comp)
    await session.commit()


# --- Helpers ---

async def _get_comp(competitor_id: str, user_id: str, session: AsyncSession) -> Competitor:
    result = await session.execute(
        select(Competitor).where(Competitor.id == competitor_id, Competitor.user_id == user_id)
    )
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return comp


async def _trigger_scrape(competitor_id: str) -> None:
    import arq.connections
    from config import settings
    redis = await arq.connections.create_pool(arq.connections.RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("run_scrape", competitor_id)
    await redis.close()


def _comp_out(comp: Competitor, snapshot: CompetitorSnapshot | None) -> CompetitorOut:
    current_snap = None
    if snapshot:
        current_snap = {
            "pricing_tiers_count": len(snapshot.pricing_tiers),
            "features_count": len(snapshot.key_features),
            "confidence": snapshot.confidence,
            "scraped_at": snapshot.scraped_at.isoformat(),
        }
    return CompetitorOut(
        id=comp.id,
        company_name=comp.company_name,
        website_url=comp.website_url,
        product_name=comp.product_name,
        category=comp.category,
        scrape_status=comp.scrape_status.value,
        last_scraped_at=comp.last_scraped_at.isoformat() if comp.last_scraped_at else None,
        scrape_interval_days=comp.scrape_interval_days,
        created_at=comp.created_at.isoformat(),
        current_snapshot=current_snap,
    )


def _snap_out(s: CompetitorSnapshot) -> SnapshotOut:
    return SnapshotOut(
        id=s.id,
        scraped_at=s.scraped_at.isoformat(),
        pricing_tiers=s.pricing_tiers,
        key_features=s.key_features,
        target_segments=s.target_segments,
        integration_list=s.integration_list,
        scraped_claims=s.scraped_claims,
        confidence=s.confidence,
        is_current=s.is_current,
    )
