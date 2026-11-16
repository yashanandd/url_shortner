import json
from typing import Any, Dict, Optional
import redis.asyncio as aioredis

CACHE_KEY_PREFIX = "url:"
DEFAULT_CACHE_TTL = 86400  # 24 hours
NEGATIVE_CACHE_TTL = 60    # 60 seconds (anti-stampede / scan defense)


async def get_cached_url(redis: aioredis.Redis, short_code: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached URL metadata or negative cache marker from Redis."""
    try:
        raw_data = await redis.get(f"{CACHE_KEY_PREFIX}{short_code}")
        if raw_data:
            return json.loads(raw_data)
        return None
    except Exception:
        # If Redis is temporarily unreachable, fail open to DB query
        return None


async def set_cached_url(
    redis: aioredis.Redis,
    short_code: str,
    original_url: str,
    status: str,
    expires_at: Optional[str] = None,
    ttl: int = DEFAULT_CACHE_TTL,
) -> None:
    """Store URL metadata in Redis cache."""
    try:
        payload = {
            "original_url": original_url,
            "status": status,
            "expires_at": expires_at,
        }
        await redis.setex(
            f"{CACHE_KEY_PREFIX}{short_code}",
            ttl,
            json.dumps(payload),
        )
    except Exception:
        pass


async def set_negative_cache(redis: aioredis.Redis, short_code: str) -> None:
    """Store negative lookup sentinel in Redis to protect DB from repetitive scanning."""
    try:
        payload = {"status": "NOT_FOUND"}
        await redis.setex(
            f"{CACHE_KEY_PREFIX}{short_code}",
            NEGATIVE_CACHE_TTL,
            json.dumps(payload),
        )
    except Exception:
        pass


async def invalidate_cache(redis: aioredis.Redis, short_code: str) -> None:
    """Evict cached entry when a link is edited, deleted, or disabled."""
    try:
        await redis.delete(f"{CACHE_KEY_PREFIX}{short_code}")
    except Exception:
        pass
