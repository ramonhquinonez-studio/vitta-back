from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_db


def rate_limit(bucket: str, *, limit: int, window_seconds: int):
    """Dependency factory for a lightweight, Mongo-backed IP throttle —
    no new dependency needed, just an event per (bucket, ip) in
    `rate_limit_events` with a TTL index (see `init_indexes.py`) so old
    events self-expire. Registration became worth throttling once it
    creates a billable tenant, not just a user account.
    """

    async def _check(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)) -> None:
        ip = request.client.host if request.client else "unknown"
        key = f"{bucket}:{ip}"
        since = datetime.utcnow() - timedelta(seconds=window_seconds)
        recent = await db.rate_limit_events.count_documents({"key": key, "at": {"$gte": since}})
        if recent >= limit:
            raise HTTPException(status_code=429, detail="Too many attempts, try again later.")
        await db.rate_limit_events.insert_one({"key": key, "at": datetime.utcnow()})

    return _check
