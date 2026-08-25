import secrets
import string
from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from ..domain.entities import Patient

# Sin caracteres ambiguos (0/O, 1/I/l) para que sea fácil de transcribir a mano.
_INVITE_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_INVITE_CODE_LENGTH = 8
_INVITE_CODE_EXPIRE_DAYS = 30


class MongoPatientsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_for_owner(
        self,
        owner_id: str,
        *,
        page: int,
        limit: int,
        query: str | None = None,
    ) -> tuple[list[Patient], int]:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        filters: dict[str, Any] = {"owner_id": owner_oid}
        if query:
            filters["name"] = {"$regex": query, "$options": "i"}

        total = await self._db.patients.count_documents(filters)
        cursor = (
            self._db.patients.find(filters)
            .sort("name", 1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        items = [self._to_entity(doc) async for doc in cursor]
        return items, total

    async def count_for_owner(self, owner_id: str) -> int:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        return await self._db.patients.count_documents({"owner_id": owner_oid})

    async def create_for_owner(self, owner_id: str, payload: dict) -> Patient:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        document = dict(payload)
        document["owner_id"] = owner_oid
        result = await self._db.patients.insert_one(document)
        created = await self._db.patients.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Patient creation failed")
        return self._to_entity(created)

    async def get_for_owner(self, owner_id: str, patient_id: str) -> Patient | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        document = await self._db.patients.find_one(
            {"_id": patient_oid, "owner_id": owner_oid},
        )
        if document is None:
            return None
        return self._to_entity(document)

    async def update_for_owner(self, owner_id: str, patient_id: str, payload: dict) -> Patient | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        result = await self._db.patients.update_one(
            {"_id": patient_oid, "owner_id": owner_oid},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        return await self.get_for_owner(owner_id, patient_id)

    async def delete_for_owner(self, owner_id: str, patient_id: str) -> bool:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        result = await self._db.patients.delete_one(
            {"_id": patient_oid, "owner_id": owner_oid},
        )
        return result.deleted_count > 0

    async def add_body_composition(self, owner_id: str, patient_id: str, payload: dict) -> dict | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        owned = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        if owned is None:
            return None

        document = {
            "owner_id": owner_oid,
            "patient_id": patient_oid,
            "at": payload.get("at") or datetime.utcnow(),
            "provider": payload.get("provider"),
            "metrics": payload.get("metrics", {}),
            "attachment_url": payload.get("attachment_url"),
            "attachment_type": payload.get("attachment_type"),
            "created_at": datetime.utcnow(),
        }
        result = await self._db.body_compositions.insert_one(document)
        document["_id"] = result.inserted_id
        return {
            "id": str(document["_id"]),
            "at": document["at"],
            "provider": document["provider"],
            "metrics": document["metrics"],
            "attachment_url": document["attachment_url"],
            "attachment_type": document["attachment_type"],
        }

    async def list_body_compositions(self, owner_id: str, patient_id: str) -> list[dict] | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        owned = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        if owned is None:
            return None

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

    async def list_food_diary_entries(self, owner_id: str, patient_id: str) -> list[dict] | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        owned = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        if owned is None:
            return None

        cursor = self._db.food_diary_entries.find({"patient_id": patient_oid}).sort("at", -1)
        return [
            {
                "id": str(doc["_id"]),
                "at": doc.get("at"),
                "meal_title": doc.get("meal_title"),
                "dish": doc.get("dish"),
                "restaurant": doc.get("restaurant"),
                "kcal": doc.get("kcal"),
                "protein": doc.get("protein"),
                "notes": doc.get("notes"),
            }
            async for doc in cursor
        ]

    async def list_measurements(self, owner_id: str, patient_id: str) -> list[dict] | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        owned = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        if owned is None:
            return None

        cursor = self._db.measurements.find({"patient_id": patient_oid}).sort("at", -1)
        return [
            {
                "id": str(doc["_id"]),
                "at": doc.get("at"),
                "weight_kg": doc.get("weight_kg"),
                "body_fat_pct": doc.get("body_fat_pct"),
                "waist_cm": doc.get("waist_cm"),
                "notes": doc.get("notes"),
                "attachment_url": doc.get("attachment_url"),
                "attachment_type": doc.get("attachment_type"),
            }
            async for doc in cursor
        ]

    async def list_workout_plan_assignments(self, owner_id: str, patient_id: str) -> list[dict] | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        owned = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        if owned is None:
            return None

        cursor = self._db.workout_plan_assignments.find({"patient_id": patient_oid}).sort(
            "assigned_at", -1
        )
        results = []
        async for doc in cursor:
            plan = await self._db.workout_plans.find_one({"_id": doc["plan_id"]})
            results.append(
                {
                    "plan_id": str(doc["plan_id"]),
                    "plan_name": plan.get("name") if plan else None,
                    "assigned_at": doc.get("assigned_at"),
                }
            )
        return results

    async def list_workout_logs(self, owner_id: str, patient_id: str) -> list[dict] | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        owned = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        if owned is None:
            return None

        cursor = self._db.workout_logs.find({"patient_id": patient_oid})
        return [
            {
                "workout_plan_id": str(doc["workout_plan_id"]),
                "day_index": doc["day_index"],
                "exercise_index": doc["exercise_index"],
                "completed_at": doc.get("completed_at"),
                "sets_completed": doc.get("sets_completed"),
                "reps_completed": doc.get("reps_completed"),
                "weight_kg": doc.get("weight_kg"),
                "rpe": doc.get("rpe"),
                "comment": doc.get("comment"),
            }
            async for doc in cursor
        ]

    async def list_checkin_responses(self, owner_id: str, patient_id: str) -> list[dict] | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        owned = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        if owned is None:
            return None

        cursor = self._db.checkin_responses.find({"patient_id": patient_oid}).sort(
            "submitted_at", -1
        )
        return [
            {
                "id": str(doc["_id"]),
                "template_id": str(doc["template_id"]),
                "appointment_id": str(doc["appointment_id"]) if doc.get("appointment_id") else None,
                "answers": doc.get("answers", []),
                "submitted_at": doc.get("submitted_at"),
            }
            async for doc in cursor
        ]

    async def list_plan_assignments(self, owner_id: str, patient_id: str) -> list[dict] | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        owned = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        if owned is None:
            return None

        cursor = self._db.plan_assignments.find({"patient_id": patient_oid}).sort(
            "assigned_at", -1
        )
        results = []
        async for doc in cursor:
            plan = await self._db.plans.find_one({"_id": doc["plan_id"]})
            results.append(
                {
                    "plan_id": str(doc["plan_id"]),
                    "plan_name": plan.get("name") if plan else None,
                    "assigned_at": doc.get("assigned_at"),
                }
            )
        return results

    async def create_invite_code(self, owner_id: str, patient_id: str | None = None) -> dict:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id) if patient_id is not None else None
        expires_at = datetime.utcnow() + timedelta(days=_INVITE_CODE_EXPIRE_DAYS)

        for _ in range(5):
            code = "".join(
                secrets.choice(_INVITE_CODE_ALPHABET) for _ in range(_INVITE_CODE_LENGTH)
            )
            try:
                await self._db.invite_codes.insert_one(
                    {
                        "code": code,
                        "owner_id": owner_oid,
                        "patient_id": patient_oid,
                        "created_at": datetime.utcnow(),
                        "expires_at": expires_at,
                        "used_at": None,
                        "used_by_user_id": None,
                    }
                )
                return {"code": code, "expires_at": expires_at}
            except DuplicateKeyError:
                continue
        raise RuntimeError("Could not generate a unique invite code")

    async def claim_patient(self, owner_id: str, code: str) -> Patient | None:
        """Links an unclaimed, self-registered patient (owner_id is None) to
        the calling nutritionist, matched by the connection code the patient
        shared out-of-band. Mirrors `link_user_to_patient`'s null-guarded
        `update_one` so two nutritionists racing on the same code can't both
        "succeed"."""
        owner_oid = self._as_oid(owner_id, field_name="owner")
        normalized_code = (code or "").strip().upper()
        if not normalized_code:
            return None
        document = await self._db.patients.find_one_and_update(
            {"connection_code": normalized_code, "owner_id": None},
            {"$set": {"owner_id": owner_oid}, "$unset": {"connection_code": ""}},
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            return None
        return self._to_entity(document)

    def _to_entity(self, document: dict) -> Patient:
        return Patient(
            id=str(document["_id"]),
            owner_id=self._stringify_maybe_oid(document.get("owner_id")),
            name=document["name"],
            age=document.get("age"),
            sex=document.get("sex"),
            height_cm=document.get("height_cm"),
            allergies=list(document.get("allergies") or []),
            notes=document.get("notes"),
            user_id=self._stringify_maybe_oid(document.get("user_id")),
        )

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)

    def _stringify_maybe_oid(self, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value
