from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import Subscription, SubscriptionPlan


class MongoBillingRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)

    async def list_plans(self) -> list[SubscriptionPlan]:
        cursor = self._db.subscription_plans.find().sort("client_limit", 1)
        return [self._plan_to_entity(doc) async for doc in cursor]

    async def get_plan(self, plan_id: str) -> SubscriptionPlan | None:
        doc = await self._db.subscription_plans.find_one({"_id": self._as_oid(plan_id, "plan")})
        return self._plan_to_entity(doc) if doc else None

    async def get_default_plan(self) -> SubscriptionPlan | None:
        doc = await self._db.subscription_plans.find_one({"is_default": True})
        return self._plan_to_entity(doc) if doc else None

    async def get_subscription_for_owner(self, owner_id: str) -> Subscription | None:
        owner_oid = self._as_oid(owner_id, "owner")
        doc = await self._db.subscriptions.find_one({"owner_id": owner_oid})
        return self._subscription_to_entity(doc) if doc else None

    async def get_subscription_for_customer(self, provider_customer_id: str) -> Subscription | None:
        doc = await self._db.subscriptions.find_one({"provider_customer_id": provider_customer_id})
        return self._subscription_to_entity(doc) if doc else None

    async def upsert_subscription(self, subscription: Subscription) -> Subscription:
        owner_oid = self._as_oid(subscription.owner_id, "owner")
        document = {
            "owner_id": owner_oid,
            "plan_id": self._as_oid(subscription.plan_id, "plan"),
            "status": subscription.status,
            "provider_customer_id": subscription.provider_customer_id,
            "provider_subscription_id": subscription.provider_subscription_id,
            "current_period_end": subscription.current_period_end,
        }
        await self._db.subscriptions.update_one(
            {"owner_id": owner_oid},
            {"$set": document},
            upsert=True,
        )
        doc = await self._db.subscriptions.find_one({"owner_id": owner_oid})
        return self._subscription_to_entity(doc)

    def _plan_to_entity(self, doc: dict) -> SubscriptionPlan:
        return SubscriptionPlan(
            id=str(doc["_id"]),
            name=doc["name"],
            client_limit=doc.get("client_limit"),
            stripe_price_id=doc.get("stripe_price_id"),
            is_default=bool(doc.get("is_default", False)),
        )

    def _subscription_to_entity(self, doc: dict) -> Subscription:
        return Subscription(
            owner_id=str(doc["owner_id"]),
            plan_id=str(doc["plan_id"]),
            status=doc.get("status", "active"),
            provider_customer_id=doc.get("provider_customer_id"),
            provider_subscription_id=doc.get("provider_subscription_id"),
            current_period_end=doc.get("current_period_end"),
        )
