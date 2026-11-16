import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.core.redis import close_redis, get_redis, redis_client
from app.services.rate_limiter import is_rate_limited
from app.services.url_service import resolve_short_url
from app.worker.stream_consumer import start_stream_worker

# Background worker task handle
worker_task: Optional[asyncio.Task] = None
stop_worker_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_task

    # 1. Initialize DB tables in development (if not using manual alembic upgrade)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Start background stream consumer worker
    stop_worker_event.clear()
    worker_task = asyncio.create_task(start_stream_worker(stop_worker_event))

    yield

    # Shutdown sequence
    stop_worker_event.set()
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="High-throughput, production-ready distributed URL Shortener and Analytics engine.",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 REST APIs
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Service health and readiness check."""
    redis_healthy = False
    try:
        redis_healthy = await redis_client.ping()
    except Exception:
        redis_healthy = False

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "redis_connected": redis_healthy,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/{short_code}", tags=["Redirection"], include_in_schema=False)
async def redirect_short_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Sub-millisecond redirect handler:
    1. Check sliding window rate limit
    2. Fast Redis cache lookup
    3. Non-blocking XADD to clicks:stream
    4. HTTP 302 Found redirect
    """
    client_ip = request.client.host if request.client else "unknown"

    # 1. Rate Limiting Check
    limited, retry_after = await is_rate_limited(
        redis=redis,
        key_identifier=f"redirect:{client_ip}",
        limit=settings.RATE_LIMIT_REDIRECT_PER_SEC,
        window_seconds=1,
    )
    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many redirect requests. Please slow down.",
        )

    # 2. Destination Resolution (Redis Cache-Aside -> DB)
    destination_url, error_reason = await resolve_short_url(db, redis, short_code)

    if error_reason == "NOT_FOUND" or not destination_url:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Link not found", "short_code": short_code},
        )

    if error_reason == "EXPIRED":
        return JSONResponse(
            status_code=status.HTTP_410_GONE,
            content={"error": "This link has expired", "short_code": short_code},
        )

    if error_reason in ("DISABLED", "INACTIVE", "FLAGGED"):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "This link is currently inactive or disabled", "short_code": short_code},
        )

    # 3. Publish click event to Redis Stream (non-blocking fire-and-forget)
    try:
        user_agent = request.headers.get("user-agent", "")
        referrer = request.headers.get("referer", "")
        cf_country = request.headers.get("cf-ipcountry", "Unknown")

        await redis.xadd(
            name=settings.REDIS_STREAM_KEY,
            fields={
                "code": short_code,
                "ip": client_ip,
                "ua": user_agent,
                "ref": referrer,
                "country": cf_country,
                "time": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception:
        # Never let logging failure block a redirect
        pass

    # 4. Return HTTP 302 redirect
    return RedirectResponse(url=destination_url, status_code=status.HTTP_302_FOUND)
