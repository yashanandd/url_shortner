from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.core.database import get_db
from app.models.analytics import ClickEvent
from app.models.url import URL
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse, DailyClickPoint

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/{short_code}", response_model=AnalyticsResponse)
async def get_url_analytics(
    short_code: str,
    days: int = Query(30, ge=1, le=90),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed click analytics for a specific short code."""
    # 1. Verify URL exists
    url_record = await db.scalar(select(URL).where(URL.short_code == short_code))
    if not url_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with code '{short_code}' not found.",
        )

    # 2. Check permission if URL has an owner
    if url_record.user_id:
        if not current_user or current_user.id != url_record.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view analytics for this URL.",
            )

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # 3. Aggregate totals
    total_clicks = await db.scalar(
        select(func.count(ClickEvent.id)).where(ClickEvent.short_code == short_code)
    ) or 0

    unique_visitors = await db.scalar(
        select(func.count(func.distinct(ClickEvent.ip_hash))).where(
            ClickEvent.short_code == short_code
        )
    ) or 0

    # 4. Device Breakdown
    device_rows = (
        await db.execute(
            select(ClickEvent.device_type, func.count(ClickEvent.id))
            .where(ClickEvent.short_code == short_code, ClickEvent.clicked_at >= start_date)
            .group_by(ClickEvent.device_type)
        )
    ).all()
    devices = {dtype or "other": count for dtype, count in device_rows}

    # 5. Browser Breakdown
    browser_rows = (
        await db.execute(
            select(ClickEvent.browser, func.count(ClickEvent.id))
            .where(ClickEvent.short_code == short_code, ClickEvent.clicked_at >= start_date)
            .group_by(ClickEvent.browser)
            .order_by(desc(func.count(ClickEvent.id)))
            .limit(10)
        )
    ).all()
    browsers = {b or "unknown": count for b, count in browser_rows}

    # 6. Country Breakdown
    country_rows = (
        await db.execute(
            select(ClickEvent.country, func.count(ClickEvent.id))
            .where(ClickEvent.short_code == short_code, ClickEvent.clicked_at >= start_date)
            .group_by(ClickEvent.country)
            .order_by(desc(func.count(ClickEvent.id)))
            .limit(10)
        )
    ).all()
    countries = {c or "Unknown": count for c, count in country_rows}

    # 7. Referrer Breakdown
    ref_rows = (
        await db.execute(
            select(ClickEvent.referrer, func.count(ClickEvent.id))
            .where(ClickEvent.short_code == short_code, ClickEvent.clicked_at >= start_date)
            .group_by(ClickEvent.referrer)
            .order_by(desc(func.count(ClickEvent.id)))
            .limit(10)
        )
    ).all()
    referrers = {r or "direct": count for r, count in ref_rows}

    # 8. Daily Clicks Trend
    daily_rows = (
        await db.execute(
            select(
                func.date(ClickEvent.clicked_at).label("day"),
                func.count(ClickEvent.id).label("clicks"),
            )
            .where(ClickEvent.short_code == short_code, ClickEvent.clicked_at >= start_date)
            .group_by(func.date(ClickEvent.clicked_at))
            .order_by(func.date(ClickEvent.clicked_at))
        )
    ).all()
    daily_clicks = [
        DailyClickPoint(date=str(row[0]), clicks=row[1]) for row in daily_rows
    ]

    return AnalyticsResponse(
        short_code=short_code,
        total_clicks=total_clicks,
        unique_visitors=unique_visitors,
        devices=devices,
        browsers=browsers,
        countries=countries,
        referrers=referrers,
        daily_clicks=daily_clicks,
    )
