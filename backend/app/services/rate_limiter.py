import time
from typing import Tuple
import redis.asyncio as aioredis


async def is_rate_limited(
    redis: aioredis.Redis,
    key_identifier: str,
    limit: int,
    window_seconds: int,
) -> Tuple[bool, int]:
    """
    Redis-backed sliding window log rate limiter.
    Returns: (is_limited, retry_after_seconds)
    """
    try:
        now_ms = int(time.time() * 1000)
        window_start_ms = now_ms - (window_seconds * 1000)
        rate_key = f"ratelimit:{key_identifier}"

        async with redis.pipeline(transaction=True) as pipe:
            # 1. Remove timestamps older than the sliding window
            pipe.zremrangebyscore(rate_key, 0, window_start_ms)
            # 2. Add current request timestamp
            pipe.zadd(rate_key, {str(now_ms): now_ms})
            # 3. Count requests in the current window
            pipe.zcard(rate_key)
            # 4. Set TTL slightly longer than window
            pipe.expire(rate_key, window_seconds + 5)
            results = await pipe.execute()

        current_count = results[2]
        if current_count > limit:
            return True, window_seconds
        return False, 0
    except Exception:
        # If Redis fails, fail open to prevent blocking traffic
        return False, 0
