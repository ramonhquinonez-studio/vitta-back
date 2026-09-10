"""Seeds the subscription plans.

- The default (free) plan every nutritionist is enrolled in at registration.
- Paid plans, each with its real Stripe recurring Price id. Create the
  Product + Price in the Stripe dashboard first, then pass the id via an
  env var (e.g. `STRIPE_PRICE_PRO`). Until it's set the plan is seeded with
  `stripe_price_id: None`, which the native `subscription-sheet` treats as
  "free" — i.e. it won't charge for it — so set the price before launch.

Idempotent — upserts by `is_default: True` for the free plan and by `name`
for the paid ones. `_id` is a real Mongo ObjectId (matched by
`MongoBillingRepository._as_oid`).
"""
import asyncio
import os

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db

# name, client_limit (None = unlimited), env var holding the Stripe price id
PAID_PLANS = [
    ("Pro", 50, "STRIPE_PRICE_PRO"),
]


async def seed_default_plan() -> None:
    db = get_db()
    await db.subscription_plans.update_one(
        {"is_default": True},
        {"$set": {"name": "Gratis", "client_limit": 3, "stripe_price_id": None, "is_default": True}},
        upsert=True,
    )
    print("Plan por defecto (Gratis, 3 pacientes) listo.")


async def seed_paid_plans() -> None:
    db = get_db()
    for name, limit, env_var in PAID_PLANS:
        price_id = getattr(settings, env_var, "") or os.getenv(env_var) or ""
        await db.subscription_plans.update_one(
            {"name": name, "is_default": {"$ne": True}},
            {
                "$set": {
                    "name": name,
                    "client_limit": limit,
                    "stripe_price_id": price_id or None,
                    "is_default": False,
                }
            },
            upsert=True,
        )
        state = f"price {price_id}" if price_id else f"SIN price id (define ${env_var})"
        print(f"Plan {name} ({limit} pacientes) listo — {state}.")


async def main() -> None:
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        await seed_default_plan()
        await seed_paid_plans()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
