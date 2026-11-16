import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import redis.asyncio as aioredis
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.url import URL
from app.models.analytics import ClickEvent
from app.schemas.url import URLCreate, URLUpdate
from app.services.cache_service import (
    get_cached_url,
    invalidate_cache,
    set_cached_url,
    set_negative_cache,
)
from app.services.code_generator import generate_short_code, is_valid_custom_alias
from app.services.url_validator import (
    ValidationError,
    is_reserved_code,
    validate_destination_url,
)


class URLConflictError(Exception):
    pass


class URLNotFoundError(Exception):
    pass


class URLForbiddenError(Exception):
    pass


async def create_short_url(
    db: AsyncSession,
    redis: aioredis.Redis,
    url_data: URLCreate,
    user_id: Optional[uuid.UUID] = None,
) -> URL:
    """Create a shortened URL with validation, collision retries, and cache warming."""
    # 1. Validate destination URL (syntax, scheme, SSRF loopback check)
    clean_url = validate_destination_url(url_data.original_url)

    # 2. Handle Custom Alias vs Generated Code
    short_code: str
    custom_alias: Optional[str] = None

    if url_data.custom_alias and url_data.custom_alias.strip():
        alias = url_data.custom_alias.strip()
        if not is_valid_custom_alias(alias):
            raise ValidationError(
                "Custom alias must be 3-30 characters long and contain only letters, numbers, hyphens, or underscores."
            )
        if is_reserved_code(alias):
            raise ValidationError(f"The alias '{alias}' is a reserved system route and cannot be used.")

        # Check DB uniqueness
        existing = await db.scalar(select(URL).where(URL.short_code == alias))
        if existing:
            raise URLConflictError(f"Custom alias '{alias}' is already in use.")

        short_code = alias
        custom_alias = alias
    else:
        # Retry loop for generated Base62 codes
        code_found = False
        for _ in range(5):
            candidate = generate_short_code()
            if is_reserved_code(candidate):
                continue

            existing = await db.scalar(select(URL).where(URL.short_code == candidate))
            if not existing:
                short_code = candidate
                code_found = True
                break

        if not code_found:
            raise RuntimeError("Failed to generate a unique short code. Please try again.")

    # 3. Create database record
    new_url = URL(
        id=uuid.uuid4(),
        user_id=user_id,
        short_code=short_code,
        original_url=clean_url,
        custom_alias=custom_alias,
        status="ACTIVE",
        expires_at=url_data.expires_at,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(new_url)
    await db.commit()
    await db.refresh(new_url)

    # 4. Warm Redis cache
    await set_cached_url(
        redis=redis,
        short_code=short_code,
        original_url=clean_url,
        status="ACTIVE",
        expires_at=url_data.expires_at.isoformat() if url_data.expires_at else None,
    )

    return new_url


async def resolve_short_url(
    db: AsyncSession,
    redis: aioredis.Redis,
    short_code: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Fast-path redirect resolver using Cache-Aside + Negative Caching.
    Returns: (destination_url, error_reason)
    """
    # 1. Check Redis cache
    cached = await get_cached_url(redis, short_code)
    if cached is not None:
        if cached.get("status") == "NOT_FOUND":
            return None, "NOT_FOUND"

        if cached.get("status") != "ACTIVE":
            return None, cached.get("status", "INACTIVE")

        # Check expiration
        expires_at_str = cached.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now(timezone.utc) > expires_at:
                return None, "EXPIRED"

        return cached.get("original_url"), None

    # 2. Cache miss -> Query PostgreSQL
    url_record = await db.scalar(select(URL).where(URL.short_code == short_code))

    if not url_record:
        # Negative cache for 60s
        await set_negative_cache(redis, short_code)
        return None, "NOT_FOUND"

    # Populate Redis cache
    await set_cached_url(
        redis=redis,
        short_code=short_code,
        original_url=url_record.original_url,
        status=url_record.status,
        expires_at=url_record.expires_at.isoformat() if url_record.expires_at else None,
    )

    if url_record.status != "ACTIVE":
        return None, url_record.status

    if url_record.expires_at and datetime.now(timezone.utc) > url_record.expires_at:
        return None, "EXPIRED"

    return url_record.original_url, None


async def get_user_urls(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Fetch paginated list of URLs owned by user along with click count."""
    query = (
        select(
            URL,
            func.count(ClickEvent.id).label("total_clicks"),
        )
        .outerjoin(ClickEvent, ClickEvent.short_code == URL.short_code)
        .where(URL.user_id == user_id)
        .group_by(URL.id)
        .order_by(desc(URL.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    urls_with_stats = []
    for url, clicks in rows:
        urls_with_stats.append({
            "id": url.id,
            "short_code": url.short_code,
            "short_url": f"{settings.BASE_URL}/{url.short_code}",
            "original_url": url.original_url,
            "custom_alias": url.custom_alias,
            "status": url.status,
            "expires_at": url.expires_at,
            "created_at": url.created_at,
            "total_clicks": clicks or 0,
        })
    return urls_with_stats


async def update_user_url(
    db: AsyncSession,
    redis: aioredis.Redis,
    url_id: uuid.UUID,
    user_id: uuid.UUID,
    update_data: URLUpdate,
) -> URL:
    """Update URL destination, status, or expiration, and invalidate cache."""
    url = await db.scalar(select(URL).where(URL.id == url_id))
    if not url:
        raise URLNotFoundError("URL not found.")
    if url.user_id != user_id:
        raise URLForbiddenError("You do not have permission to modify this URL.")

    if update_data.original_url:
        clean_url = validate_destination_url(update_data.original_url)
        url.original_url = clean_url

    if update_data.status:
        valid_statuses = {"ACTIVE", "DISABLED", "EXPIRED"}
        status_upper = update_data.status.upper()
        if status_upper not in valid_statuses:
            raise ValidationError(f"Invalid status. Choose from {valid_statuses}")
        url.status = status_upper

    if update_data.expires_at is not None:
        url.expires_at = update_data.expires_at

    url.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(url)

    # Invalidate cache
    await invalidate_cache(redis, url.short_code)

    return url


async def delete_user_url(
    db: AsyncSession,
    redis: aioredis.Redis,
    url_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Delete URL and evict from cache."""
    url = await db.scalar(select(URL).where(URL.id == url_id))
    if not url:
        raise URLNotFoundError("URL not found.")
    if url.user_id != user_id:
        raise URLForbiddenError("You do not have permission to delete this URL.")

    short_code = url.short_code
    await db.delete(url)
    await db.commit()

    # Invalidate cache
    await invalidate_cache(redis, short_code)
