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


def _add_months(date: datetime, months: int) -> datetime:
    """Returns the first of the month `months` away from `date` (may be
    negative). Stdlib-only month-bucket walker for dashboard trend queries."""
    month_index = date.month - 1 + months
    year = date.year + month_index // 12
    month = month_index % 12 + 1
    return datetime(year, month, 1)


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
        include_archived: bool = False,
    ) -> tuple[list[Patient], int]:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        filters: dict[str, Any] = {"owner_id": owner_oid}
        if not include_archived:
            filters["archived_at"] = None
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
        return await self._db.patients.count_documents(
            {"owner_id": owner_oid, "archived_at": None}
        )

    async def create_for_owner(self, owner_id: str, payload: dict) -> Patient:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        document = dict(payload)
        document["owner_id"] = owner_oid
        document["created_at"] = datetime.utcnow()
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

    async def archive_for_owner(self, owner_id: str, patient_id: str) -> Patient | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        result = await self._db.patients.update_one(
            {"_id": patient_oid, "owner_id": owner_oid},
            {"$set": {"archived_at": datetime.utcnow()}},
        )
        if result.matched_count == 0:
            return None
        return await self.get_for_owner(owner_id, patient_id)

    async def unarchive_for_owner(self, owner_id: str, patient_id: str) -> Patient | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        result = await self._db.patients.update_one(
            {"_id": patient_oid, "owner_id": owner_oid},
            {"$set": {"archived_at": None}},
        )
        if result.matched_count == 0:
            return None
        return await self.get_for_owner(owner_id, patient_id)

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
                "sets": doc.get("sets", []),
                "comment": doc.get("comment"),
                "photo_url": doc.get("photo_url"),
                "photo_content_type": doc.get("photo_content_type"),
                "coach_marked_done": doc.get("coach_marked_done", False),
                "updated_at": doc.get("updated_at"),
            }
            async for doc in cursor
        ]

    async def toggle_coach_workout_log(
        self,
        owner_id: str,
        patient_id: str,
        *,
        workout_plan_id: str,
        day_index: int,
        exercise_index: int,
    ) -> dict | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._as_oid(patient_id)
        owned = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        if owned is None:
            return None

        key = {
            "owner_id": owner_oid,
            "patient_id": patient_oid,
            "workout_plan_id": self._as_oid(workout_plan_id),
            "day_index": day_index,
            "exercise_index": exercise_index,
        }
        existing = await self._db.workout_logs.find_one(key)
        new_value = not (existing.get("coach_marked_done", False) if existing else False)
        await self._db.workout_logs.update_one(
            key,
            {
                "$set": {"coach_marked_done": new_value, "updated_at": datetime.utcnow()},
                "$setOnInsert": {"sets": [], "comment": None},
            },
            upsert=True,
        )
        return {"completed": new_value}

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

    async def get_dashboard(self, owner_id: str) -> dict:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        week_from_now = now + timedelta(days=7)
        inactivity_cutoff = now - timedelta(days=14)

        total_patients = await self._db.patients.count_documents(
            {"owner_id": owner_oid, "archived_at": None}
        )
        new_patients_this_month = await self._db.patients.count_documents(
            {"owner_id": owner_oid, "archived_at": None, "created_at": {"$gte": start_of_month}}
        )
        upcoming_appointments_this_week = await self._db.appointments.count_documents(
            {
                "owner_id": owner_oid,
                "start": {"$gte": now, "$lt": week_from_now},
                "status": {"$in": ["confirmed", "pending"]},
            }
        )
        completed_appointments_this_month = await self._db.appointments.count_documents(
            {
                "owner_id": owner_oid,
                "status": "completed",
                "start": {"$gte": start_of_month, "$lt": now},
            }
        )

        patient_names = {
            doc["_id"]: doc.get("name", "")
            async for doc in self._db.patients.find(
                {"owner_id": owner_oid, "archived_at": None}, {"name": 1}
            )
        }
        patient_ids = list(patient_names.keys())

        active_ids: set = set()
        if patient_ids:
            for collection, timestamp_field in (
                (self._db.measurements, "at"),
                (self._db.food_diary_entries, "at"),
                (self._db.checkin_responses, "submitted_at"),
                (self._db.workout_logs, "updated_at"),
                (self._db.appointments, "start"),
            ):
                recent_ids = await collection.distinct(
                    "patient_id",
                    {"patient_id": {"$in": patient_ids}, timestamp_field: {"$gte": inactivity_cutoff}},
                )
                active_ids.update(recent_ids)

        inactive_patients = [
            {"id": str(patient_id), "name": patient_names[patient_id]}
            for patient_id in patient_ids
            if patient_id not in active_ids
        ]

        new_patients_by_month = []
        bucket_start = _add_months(start_of_month, -5)
        for _ in range(6):
            bucket_end = _add_months(bucket_start, 1)
            count = await self._db.patients.count_documents(
                {
                    "owner_id": owner_oid,
                    "archived_at": None,
                    "created_at": {"$gte": bucket_start, "$lt": bucket_end},
                }
            )
            new_patients_by_month.append({"month": bucket_start.strftime("%Y-%m"), "count": count})
            bucket_start = bucket_end

        return {
            "total_patients": total_patients,
            "new_patients_this_month": new_patients_this_month,
            "upcoming_appointments_this_week": upcoming_appointments_this_week,
            "completed_appointments_this_month": completed_appointments_this_month,
            "active_patients": len(active_ids),
            "inactive_patients": inactive_patients,
            "new_patients_by_month": new_patients_by_month,
        }

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
            tags=list(document.get("tags") or []),
            user_id=self._stringify_maybe_oid(document.get("user_id")),
            created_at=document.get("created_at"),
            daily_kcal_goal=document.get("daily_kcal_goal"),
            daily_protein_g_goal=document.get("daily_protein_g_goal"),
            daily_carbs_g_goal=document.get("daily_carbs_g_goal"),
            daily_fat_g_goal=document.get("daily_fat_g_goal"),
            email=document.get("email"),
            phone=document.get("phone"),
            archived_at=document.get("archived_at"),
        )

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)

    def _stringify_maybe_oid(self, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value
