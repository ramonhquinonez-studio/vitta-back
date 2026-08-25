"""Seeds the default (free) subscription plan every nutritionist is
enrolled in at registration. Idempotent — re-running upserts by
`is_default: True` rather than a fixed id, since `_id` here is a real Mongo
ObjectId (unlike content_library's stable string ids), matched by
`MongoBillingRepository._as_oid`.
"""
import asyncio

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db


async def seed_default_plan() -> None:
    db = get_db()
    await db.subscription_plans.update_one(
        {"is_default": True},
        {
            "$set": {
                "name": "Gratis",
                "client_limit": 3,
                "stripe_price_id": None,
                "is_default": True,
            }
        },
        upsert=True,
    )
    print("Plan por defecto (Gratis, 3 pacientes) listo.")


async def main() -> None:
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        await seed_default_plan()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
