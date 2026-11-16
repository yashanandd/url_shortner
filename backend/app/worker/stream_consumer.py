import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from user_agents import parse as parse_user_agent

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.analytics import AnalyticsAggregate, ClickEvent

logger = logging.getLogger("linkflow.worker")
logging.basicConfig(level=logging.INFO)


def anonymize_ip(ip: str) -> str:
    """Create a salted SHA-256 hash of IP for privacy compliance."""
    if not ip or ip == "unknown":
        return "anonymous"
    return hashlib.sha256(f"{ip}:{settings.SECRET_KEY}".encode()).hexdigest()[:16]


def parse_device_info(ua_string: str) -> Dict[str, str]:
    """Parse User-Agent string to extract device category, browser family, and OS family."""
    if not ua_string:
        return {"device_type": "unknown", "browser": "unknown", "os": "unknown"}

    ua = parse_user_agent(ua_string)
    if ua.is_bot:
        device_type = "bot"
    elif ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "desktop"
    else:
        device_type = "other"

    return {
        "device_type": device_type,
        "browser": ua.browser.family if ua.browser.family else "unknown",
        "os": ua.os.family if ua.os.family else "unknown",
    }


async def init_consumer_group(redis: aioredis.Redis) -> None:
    """Ensure Redis Stream and Consumer Group exist."""
    try:
        await redis.xgroup_create(
            name=settings.REDIS_STREAM_KEY,
            groupname=settings.REDIS_STREAM_GROUP,
            id="0",
            mkstream=True,
        )
        logger.info(f"Created consumer group '{settings.REDIS_STREAM_GROUP}' on stream '{settings.REDIS_STREAM_KEY}'")
    except aioredis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            # Group already exists
            pass
        else:
            logger.warning(f"Consumer group init response: {e}")


async def process_click_events_batch(events_data: List[Dict[str, Any]]) -> None:
    """Batch-insert raw click events and update aggregate daily statistics in PostgreSQL."""
    if not events_data:
        return

    async with AsyncSessionLocal() as db:
        try:
            for item in events_data:
                payload = item["data"]
                short_code = payload.get("code")
                if not short_code:
                    continue

                raw_time = payload.get("time")
                clicked_at = (
                    datetime.fromisoformat(raw_time)
                    if raw_time
                    else datetime.now(timezone.utc)
                )

                ua_info = parse_device_info(payload.get("ua", ""))
                ip_hash = anonymize_ip(payload.get("ip", ""))
                country = payload.get("country", "Unknown")
                referrer = payload.get("ref") or None

                # 1. Create ClickEvent record
                click_record = ClickEvent(
                    short_code=short_code,
                    clicked_at=clicked_at,
                    referrer=referrer,
                    user_agent=payload.get("ua"),
                    ip_hash=ip_hash,
                    country=country,
                    device_type=ua_info["device_type"],
                    browser=ua_info["browser"],
                    os=ua_info["os"],
                )
                db.add(click_record)

                # 2. Upsert Daily Analytics Aggregate
                click_date = clicked_at.date()
                device_type = ua_info["device_type"]

                desktop_inc = 1 if device_type == "desktop" else 0
                mobile_inc = 1 if device_type == "mobile" else 0
                tablet_inc = 1 if device_type == "tablet" else 0

                stmt = insert(AnalyticsAggregate).values(
                    short_code=short_code,
                    date=click_date,
                    total_clicks=1,
                    unique_visitors=1,
                    desktop_clicks=desktop_inc,
                    mobile_clicks=mobile_inc,
                    tablet_clicks=tablet_inc,
                ).on_conflict_do_update(
                    constraint="uq_short_code_date",
                    set_={
                        "total_clicks": AnalyticsAggregate.total_clicks + 1,
                        "desktop_clicks": AnalyticsAggregate.desktop_clicks + desktop_inc,
                        "mobile_clicks": AnalyticsAggregate.mobile_clicks + mobile_inc,
                        "tablet_clicks": AnalyticsAggregate.tablet_clicks + tablet_inc,
                    },
                )
                await db.execute(stmt)

            await db.commit()
            logger.info(f"Processed batch of {len(events_data)} click events.")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing click batch: {e}", exc_info=True)
            raise


async def start_stream_worker(stop_event: asyncio.Event = None) -> None:
    """Continuously poll Redis Stream for new click events and process in batches."""
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await init_consumer_group(redis)
    logger.info("Click analytics consumer worker started.")

    try:
        while stop_event is None or not stop_event.is_set():
            try:
                # Read new messages from consumer group
                response = await redis.xreadgroup(
                    groupname=settings.REDIS_STREAM_GROUP,
                    consumername=settings.REDIS_STREAM_CONSUMER,
                    streams={settings.REDIS_STREAM_KEY: ">"},
                    count=100,
                    block=2000,
                )

                if not response:
                    continue

                for stream_name, messages in response:
                    if not messages:
                        continue

                    batch = []
                    message_ids = []
                    for message_id, data in messages:
                        message_ids.append(message_id)
                        batch.append({"id": message_id, "data": data})

                    # Process batch to DB
                    await process_click_events_batch(batch)

                    # Acknowledge processed messages
                    if message_ids:
                        await redis.xack(
                            settings.REDIS_STREAM_KEY,
                            settings.REDIS_STREAM_GROUP,
                            *message_ids,
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker iteration error: {e}")
                await asyncio.sleep(1)
    finally:
        await redis.aclose()
        logger.info("Click analytics consumer worker stopped.")


if __name__ == "__main__":
    asyncio.run(start_stream_worker())
