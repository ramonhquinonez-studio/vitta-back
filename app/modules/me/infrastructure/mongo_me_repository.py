from datetime import datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoMeRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def get_user(self, user_id: str) -> dict | None:
        user_oid = self._as_oid(user_id)
        user = await self._db.users.find_one({"_id": user_oid})
        if user is None:
            return None
        return {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "name": user.get("name"),
        }

    async def get_patient_for_user(self, user_id: str) -> dict | None:
        user_oid = self._as_oid(user_id)
        patient = await self._db.patients.find_one({"user_id": user_oid})
        if patient is None:
            return None
        return {
            "id": str(patient["_id"]),
            "name": patient.get("name"),
            "age": patient.get("age"),
            "sex": patient.get("sex"),
            "height_cm": patient.get("height_cm"),
            "allergies": patient.get("allergies"),
            "owner_id": str(patient.get("owner_id")) if patient.get("owner_id") else None,
        }

    async def update_patient_profile(self, patient_id: str, payload: dict) -> dict | None:
        patient_oid = self._as_oid(patient_id)
        result = await self._db.patients.update_one(
            {"_id": patient_oid},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        updated = await self._db.patients.find_one({"_id": patient_oid})
        if updated is None:
            return None
        return {
            "id": str(updated["_id"]),
            "name": updated.get("name"),
            "age": updated.get("age"),
            "sex": updated.get("sex"),
            "height_cm": updated.get("height_cm"),
            "allergies": updated.get("allergies"),
            "owner_id": str(updated.get("owner_id")) if updated.get("owner_id") else None,
        }

    async def list_appointments(
        self,
        patient_id: str,
        *,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> list[dict]:
        patient_oid = self._as_oid(patient_id)
        match: dict[str, Any] = {"patient_id": patient_oid}
        if from_dt or to_dt:
            rng: dict[str, Any] = {}
            if from_dt:
                rng["$gte"] = from_dt
            if to_dt:
                rng["$lte"] = to_dt
            match["start"] = rng
        cursor = self._db.appointments.find(match).sort("start", 1)
        return [self._serialize_appointment(doc) async for doc in cursor]

    async def get_active_plan(self, patient_id: str) -> dict | None:
        patient_oid = self._as_oid(patient_id)
        assignments = await (
            self._db.plan_assignments.find({"patient_id": patient_oid})
            .sort("assigned_at", -1)
            .to_list(1)
        )
        if not assignments:
            return None
        plan_id = assignments[0].get("plan_id")
        if not plan_id:
            return None
        plan = await self._db.plans.find_one({"_id": plan_id})
        if not plan:
            return None
        return {
            "id": str(plan["_id"]),
            "name": plan.get("name"),
            "goal": plan.get("goal", "custom"),
            "duration_days": plan.get("duration_days", 7),
            "meals": plan.get("meals", []),
            "days": plan.get("days", []),
            "updated_at": plan.get("updated_at"),
            "attachment_url": plan.get("attachment_url"),
            "attachment_type": plan.get("attachment_type"),
        }

    async def find_owner_overlap(
        self,
        owner_id: str,
        *,
        start: datetime,
        end: datetime,
        exclude_appointment_id: str | None = None,
    ) -> dict | None:
        owner_oid = self._as_oid(owner_id)
        match: dict[str, Any] = {
            "owner_id": owner_oid,
            "start": {"$lt": end},
            "end": {"$gt": start},
            "status": {"$in": ["pending", "confirmed"]},
        }
        if exclude_appointment_id:
            match["_id"] = {"$ne": self._as_oid(exclude_appointment_id)}
        appointment = await self._db.appointments.find_one(match)
        if appointment is None:
            return None
        return self._serialize_appointment(appointment)

    async def create_patient_appointment(
        self,
        *,
        owner_id: str,
        patient_id: str,
        start: datetime,
        end: datetime,
        mode: str,
        note: str | None,
    ) -> dict:
        now = datetime.utcnow()
        document = {
            "owner_id": self._as_oid(owner_id),
            "patient_id": self._as_oid(patient_id),
            "start": start,
            "end": end,
            "mode": mode,
            "status": "pending",
            "note": note,
            "no_sync": True,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._db.appointments.insert_one(document)
        created = await self._db.appointments.find_one({"_id": result.inserted_id})
        return self._serialize_appointment(created)

    async def get_patient_appointment(self, patient_id: str, appointment_id: str) -> dict | None:
        appointment = await self._db.appointments.find_one(
            {
                "_id": self._as_oid(appointment_id),
                "patient_id": self._as_oid(patient_id),
            }
        )
        if appointment is None:
            return None
        return self._serialize_appointment(appointment)

    async def update_patient_appointment(self, patient_id: str, appointment_id: str, updates: dict) -> dict | None:
        patient_oid = self._as_oid(patient_id)
        appointment_oid = self._as_oid(appointment_id)
        result = await self._db.appointments.update_one(
            {"_id": appointment_oid, "patient_id": patient_oid},
            {"$set": updates},
        )
        if result.matched_count == 0:
            return None
        updated = await self._db.appointments.find_one({"_id": appointment_oid})
        if updated is None:
            return None
        return self._serialize_appointment(updated)

    async def list_measurements(self, patient_id: str, *, limit: int) -> list[dict]:
        patient_oid = self._as_oid(patient_id)
        cursor = self._db.measurements.find({"patient_id": patient_oid}).sort("at", -1).limit(limit)
        return [self._serialize_measurement(doc) async for doc in cursor]

    async def create_measurement(self, *, owner_id: str | None, patient_id: str, payload: dict) -> dict:
        patient_oid = self._as_oid(patient_id)
        at_value = payload.get("at")
        try:
            if isinstance(at_value, str):
                at_dt = datetime.fromisoformat(at_value.replace("Z", "+00:00"))
            else:
                at_dt = at_value or datetime.utcnow()
        except Exception:
            at_dt = datetime.utcnow()

        document = {
            "owner_id": self._as_oid(owner_id) if owner_id else None,
            "patient_id": patient_oid,
            "at": at_dt,
            "weight_kg": payload.get("weight_kg"),
            "body_fat_pct": payload.get("body_fat_pct"),
            "waist_cm": payload.get("waist_cm"),
            "notes": payload.get("notes"),
            "created_at": datetime.utcnow(),
        }
        result = await self._db.measurements.insert_one(document)
        document["_id"] = result.inserted_id
        return self._serialize_measurement(document)

    async def list_measurements_since(self, patient_id: str, *, since: datetime) -> list[dict]:
        patient_oid = self._as_oid(patient_id)
        cursor = self._db.measurements.find(
            {"patient_id": patient_oid, "at": {"$gte": since}}
        ).sort("at", 1)
        return [
            {
                "at": doc.get("at"),
                "weight_kg": doc.get("weight_kg"),
                "body_fat_pct": doc.get("body_fat_pct"),
            }
            async for doc in cursor
        ]

    async def list_prescriptions(self, patient_id: str, *, limit: int) -> list[dict]:
        patient_oid = self._as_oid(patient_id)
        cursor = self._db.prescriptions.find({"patient_id": patient_oid}).sort("at", -1).limit(limit)
        return [
            {
                "id": str(doc["_id"]),
                "at": doc.get("at"),
                "medications": doc.get("medications", []),
                "notes": doc.get("notes"),
            }
            async for doc in cursor
        ]

    async def list_recipe_collections(self, owner_id: str | None) -> list[dict]:
        if not owner_id:
            return []
        cursor = self._db.recipe_collections.find({"owner_id": self._as_oid(owner_id)}).sort("updated_at", -1)
        return [
            {
                "id": str(doc["_id"]),
                "title": doc.get("title"),
                "description": doc.get("description"),
                "recipes": self._serialize_recipes(doc.get("recipes", [])),
                "updated_at": doc.get("updated_at"),
            }
            async for doc in cursor
        ]

    async def get_recipe_for_owner(self, owner_id: str | None, recipe_id: str) -> dict | None:
        if not owner_id:
            return None
        cursor = self._db.recipe_collections.find({"owner_id": self._as_oid(owner_id)})
        async for doc in cursor:
            for recipe in self._serialize_recipes(doc.get("recipes", [])):
                if recipe["id"] == recipe_id:
                    return recipe
        return None

    def _serialize_recipes(self, recipes: list[dict]) -> list[dict]:
        serialized = []
        for recipe in recipes:
            item = dict(recipe)
            item["id"] = str(item.get("id") or item.get("_id") or "")
            item.pop("_id", None)
            serialized.append(item)
        return serialized

    async def list_education_videos(self, owner_id: str | None) -> list[dict]:
        if not owner_id:
            return []
        cursor = self._db.education_videos.find({"owner_id": self._as_oid(owner_id)}).sort("published_at", -1)
        return [
            {
                "id": str(doc["_id"]),
                "title": doc.get("title"),
                "description": doc.get("description"),
                "url": doc.get("url"),
                "thumbnail_url": doc.get("thumbnail_url"),
                "published_at": doc.get("published_at"),
            }
            async for doc in cursor
        ]

    async def list_clinical_notes(self, patient_id: str) -> list[dict]:
        patient_oid = self._as_oid(patient_id)
        cursor = self._db.clinical_notes.find({"patient_id": patient_oid}).sort("at", -1)
        return [
            {
                "id": str(doc["_id"]),
                "at": doc.get("at"),
                "author": doc.get("author"),
                "note": doc.get("note"),
                "attachments": doc.get("attachments", []),
            }
            async for doc in cursor
        ]

    async def list_body_compositions(self, patient_id: str) -> list[dict]:
        patient_oid = self._as_oid(patient_id)
        cursor = self._db.body_compositions.find({"patient_id": patient_oid}).sort("at", -1)
        return [
            {
                "id": str(doc["_id"]),
                "at": doc.get("at"),
                "provider": doc.get("provider"),
                "metrics": doc.get("metrics", {}),
                "attachment_url": doc.get("attachment_url"),
                "attachment_type": doc.get("attachment_type"),
            }
            async for doc in cursor
        ]

    async def get_body_composition_by_id(self, body_composition_id: str) -> dict | None:
        if not ObjectId.is_valid(body_composition_id):
            return None
        doc = await self._db.body_compositions.find_one({"_id": ObjectId(body_composition_id)})
        if doc is None:
            return None
        return {
            "id": str(doc["_id"]),
            "at": doc.get("at"),
            "provider": doc.get("provider"),
            "metrics": doc.get("metrics", {}),
            "attachment_url": doc.get("attachment_url"),
            "attachment_type": doc.get("attachment_type"),
        }

    async def get_plan_summary(self, plan_id: str) -> dict | None:
        if not ObjectId.is_valid(plan_id):
            return None
        plan = await self._db.plans.find_one({"_id": ObjectId(plan_id)})
        if plan is None:
            return None
        return {
            "id": str(plan["_id"]),
            "name": plan.get("name"),
            "goal": plan.get("goal", "custom"),
            "duration_days": plan.get("duration_days", 7),
        }

    def _serialize_appointment(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "start": doc.get("start"),
            "end": doc.get("end"),
            "mode": doc.get("mode"),
            "status": doc.get("status"),
            "note": doc.get("note"),
            "owner_id": str(doc.get("owner_id")) if doc.get("owner_id") else None,
            "plan_id": str(doc["plan_id"]) if doc.get("plan_id") else None,
            "body_composition_id": str(doc["body_composition_id"])
            if doc.get("body_composition_id")
            else None,
        }

    def _serialize_measurement(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "at": doc.get("at"),
            "weight_kg": doc.get("weight_kg"),
            "body_fat_pct": doc.get("body_fat_pct"),
            "waist_cm": doc.get("waist_cm"),
            "notes": doc.get("notes"),
        }

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid id")
        return ObjectId(id_str)
