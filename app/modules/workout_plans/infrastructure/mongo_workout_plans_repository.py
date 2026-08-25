from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoWorkoutPlansRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def create_for_owner(self, owner_id: str, payload: dict) -> dict:
        now = datetime.utcnow()
        document = {
            "owner_id": self._as_oid(owner_id, field_name="owner"),
            "name": payload["name"],
            "goal": payload.get("goal"),
            "days": payload.get("days", []),
            "created_at": now,
            "updated_at": now,
        }
        result = await self._db.workout_plans.insert_one(document)
        created = await self._db.workout_plans.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Workout plan creation failed")
        return self._serialize(created)

    async def list_for_owner(self, owner_id: str) -> list[dict]:
        cursor = self._db.workout_plans.find(
            {"owner_id": self._as_oid(owner_id, field_name="owner")}
        ).sort("updated_at", -1)
        return [self._serialize(doc) async for doc in cursor]

    async def get_for_owner(self, owner_id: str, plan_id: str) -> dict | None:
        plan = await self._db.workout_plans.find_one(
            {
                "_id": self._as_oid(plan_id),
                "owner_id": self._as_oid(owner_id, field_name="owner"),
            }
        )
        if plan is None:
            return None
        return self._serialize(plan)

    async def update_for_owner(self, owner_id: str, plan_id: str, payload: dict) -> dict | None:
        updates = dict(payload)
        updates["updated_at"] = datetime.utcnow()
        result = await self._db.workout_plans.update_one(
            {
                "_id": self._as_oid(plan_id),
                "owner_id": self._as_oid(owner_id, field_name="owner"),
            },
            {"$set": updates},
        )
        if result.matched_count == 0:
            return None
        return await self.get_for_owner(owner_id, plan_id)

    async def delete_for_owner(self, owner_id: str, plan_id: str) -> bool:
        result = await self._db.workout_plans.delete_one(
            {
                "_id": self._as_oid(plan_id),
                "owner_id": self._as_oid(owner_id, field_name="owner"),
            }
        )
        return result.deleted_count > 0

    async def patient_exists_for_owner(self, owner_id: str, patient_id: str) -> bool:
        pid = self._oid_maybe(patient_id)
        if not isinstance(pid, ObjectId):
            return False
        patient = await self._db.patients.find_one(
            {"_id": pid, "owner_id": self._as_oid(owner_id, field_name="owner")}
        )
        return patient is not None

    async def assign_plan(self, owner_id: str, plan_id: str, patient_id: str) -> None:
        await self._db.workout_plan_assignments.insert_one(
            {
                "owner_id": self._as_oid(owner_id, field_name="owner"),
                "plan_id": self._as_oid(plan_id),
                "patient_id": self._oid_maybe(patient_id),
                "assigned_at": datetime.utcnow(),
            }
        )

    def _serialize(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "name": doc["name"],
            "goal": doc.get("goal"),
            "days": doc.get("days", []),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)

    def _oid_maybe(self, value: str | None):
        if value is None:
            return None
        return ObjectId(value) if ObjectId.is_valid(value) else value
