from __future__ import annotations

from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import BookingPolicy

_FIELDS = (
    "payment_mode",
    "deposit_type",
    "deposit_value",
    "requires_approval",
    "reschedule_limit",
    "reschedule_notice_hours",
    "cancellation_cutoff_hours",
    "slot_hold_minutes",
    "policy_text",
    "updated_at",
)


class MongoBookingPolicyRepository:
    """`booking_policies`: one document per nutritionist, keyed by the bare
    `owner_id` string (opaque key, same convention as `stripe_customers`)."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def get_for_owner(self, owner_id: str) -> BookingPolicy | None:
        doc = await self._db.booking_policies.find_one({"owner_id": owner_id})
        return _to_entity(doc) if doc else None

    async def upsert_for_owner(self, policy: BookingPolicy) -> BookingPolicy:
        await self._db.booking_policies.update_one(
            {"owner_id": policy.owner_id},
            {
                "$set": {f: getattr(policy, f) for f in _FIELDS},
                "$setOnInsert": {"owner_id": policy.owner_id, "created_at": datetime.utcnow()},
            },
            upsert=True,
        )
        return policy


def _to_entity(doc: dict) -> BookingPolicy:
    return BookingPolicy(
        owner_id=doc["owner_id"],
        payment_mode=doc.get("payment_mode", "none"),
        deposit_type=doc.get("deposit_type", "percentage"),
        deposit_value=doc.get("deposit_value", 30.0),
        requires_approval=bool(doc.get("requires_approval", False)),
        reschedule_limit=doc.get("reschedule_limit", 1),
        reschedule_notice_hours=doc.get("reschedule_notice_hours", 24),
        cancellation_cutoff_hours=doc.get("cancellation_cutoff_hours", 24),
        slot_hold_minutes=doc.get("slot_hold_minutes", 15),
        policy_text=doc.get("policy_text"),
        updated_at=doc.get("updated_at"),
    )
