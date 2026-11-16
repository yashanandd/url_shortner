import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.url import URL
from app.models.user import User
from app.schemas.url import URLCreate, URLResponse, URLUpdate
from app.services.rate_limiter import is_rate_limited
from app.services.url_service import (
    URLConflictError,
    URLForbiddenError,
    URLNotFoundError,
    create_short_url,
    delete_user_url,
    get_user_urls,
    update_user_url,
)
from app.services.url_validator import ValidationError

router = APIRouter(prefix="/urls", tags=["URLs"])


@router.post("/", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url(
    request: Request,
    data: URLCreate,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Shorten a URL. Available for both authenticated users and guests.
    Rate limited per IP / user.
    """
    identifier = str(current_user.id) if current_user else (request.client.host if request.client else "unknown")
    limit = settings.RATE_LIMIT_CREATE_PER_MIN if current_user else 10

    limited, retry_after = await is_rate_limited(
        redis=redis,
        key_identifier=f"url:create:{identifier}",
        limit=limit,
        window_seconds=60,
    )
    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"URL creation limit exceeded. Please retry in {retry_after} seconds.",
        )

    try:
        url_record = await create_short_url(
            db=db,
            redis=redis,
            url_data=data,
            user_id=current_user.id if current_user else None,
        )
        return URLResponse(
            id=url_record.id,
            short_code=url_record.short_code,
            short_url=f"{settings.BASE_URL}/{url_record.short_code}",
            original_url=url_record.original_url,
            custom_alias=url_record.custom_alias,
            status=url_record.status,
            expires_at=url_record.expires_at,
            created_at=url_record.created_at,
            total_clicks=0,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except URLConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/", response_model=List[URLResponse])
async def list_urls(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve shortened URLs created by the authenticated user."""
    return await get_user_urls(db=db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{url_id}", response_model=URLResponse)
async def get_url(
    url_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific shortened URL owned by the user."""
    url = await db.scalar(select(URL).where(URL.id == url_id))
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found.")
    if url.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return URLResponse(
        id=url.id,
        short_code=url.short_code,
        short_url=f"{settings.BASE_URL}/{url.short_code}",
        original_url=url.original_url,
        custom_alias=url.custom_alias,
        status=url.status,
        expires_at=url.expires_at,
        created_at=url.created_at,
        total_clicks=0,
    )


@router.patch("/{url_id}", response_model=URLResponse)
async def update_url(
    url_id: uuid.UUID,
    data: URLUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Update URL destination, status, or expiration date."""
    try:
        updated = await update_user_url(
            db=db,
            redis=redis,
            url_id=url_id,
            user_id=current_user.id,
            update_data=data,
        )
        return URLResponse(
            id=updated.id,
            short_code=updated.short_code,
            short_url=f"{settings.BASE_URL}/{updated.short_code}",
            original_url=updated.original_url,
            custom_alias=updated.custom_alias,
            status=updated.status,
            expires_at=updated.expires_at,
            created_at=updated.created_at,
            total_clicks=0,
        )
    except URLNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found.")
    except URLForbiddenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(
    url_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Delete a shortened URL."""
    try:
        await delete_user_url(db=db, redis=redis, url_id=url_id, user_id=current_user.id)
    except URLNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found.")
    except URLForbiddenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
