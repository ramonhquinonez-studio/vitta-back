from __future__ import annotations

from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoWebhookEventsRepository:
    """`stripe_webhook_events`: one doc per Stripe event id we've seen.
    `mark_processing` is the idempotency gate — it inserts, and a duplicate
    key means the event was already handled (or is in flight)."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def mark_processing(self, event_id: str, event_type: str) -> bool:
        """True if this is the first time we've seen `event_id`."""
        try:
            await self._db.stripe_webhook_events.insert_one(
                {
                    "_id": event_id,
                    "type": event_type,
                    "status": "processing",
                    "received_at": datetime.utcnow(),
                }
            )
            return True
        except Exception:
            # DuplicateKeyError (or any insert failure) → treat as "seen".
            return False

    async def mark_done(self, event_id: str, *, ok: bool = True, note: str | None = None) -> None:
        await self._db.stripe_webhook_events.update_one(
            {"_id": event_id},
            {"$set": {"status": "done" if ok else "error", "note": note, "done_at": datetime.utcnow()}},
        )
