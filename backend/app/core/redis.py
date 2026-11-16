from typing import AsyncGenerator
import redis.asyncio as aioredis
from app.core.config import settings

def _make_redis_client() -> aioredis.Redis:
    """Create async Redis client, with TLS support for rediss:// (e.g. Upstash)."""
    kwargs: dict = dict(decode_responses=True, max_connections=50)
    if settings.REDIS_URL.startswith("rediss://"):
        # Upstash / managed TLS: don't verify certificate chain
        kwargs["ssl_cert_reqs"] = "none"
    return aioredis.from_url(settings.REDIS_URL, **kwargs)

# Global async Redis client
redis_client = _make_redis_client()


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency that yields the async Redis client."""
    yield redis_client


async def close_redis() -> None:
    """Closes Redis connections on app shutdown."""
    await redis_client.aclose()
