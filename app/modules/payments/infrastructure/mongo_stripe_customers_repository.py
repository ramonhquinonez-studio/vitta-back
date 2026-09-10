from __future__ import annotations

from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoStripeCustomersRepository:
    """`stripe_customers`: `{ user_id, customer_id, created_at }`, keyed by
    the bare JWT `sub` string (not an ObjectId — the id space is shared by
    nutritionists and patients and only ever used as an opaque key here)."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def get_customer_id(self, user_id: str) -> str | None:
        doc = await self._db.stripe_customers.find_one({"user_id": user_id})
        return doc.get("customer_id") if doc else None

    async def set_customer_id(self, user_id: str, customer_id: str) -> None:
        await self._db.stripe_customers.update_one(
            {"user_id": user_id},
            {
                "$set": {"customer_id": customer_id},
                "$setOnInsert": {"created_at": datetime.utcnow()},
            },
            upsert=True,
        )
