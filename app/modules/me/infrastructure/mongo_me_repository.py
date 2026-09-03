from datetime import datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

_DEFAULT_HYDRATION_TARGET_ML = 2000


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
            # Only present (non-null) while self-registered and unclaimed —
            # cleared the moment a nutritionist redeems it.
            "connection_code": patient.get("connection_code"),
            "daily_kcal_goal": patient.get("daily_kcal_goal"),
            "daily_protein_g_goal": patient.get("daily_protein_g_goal"),
            "daily_carbs_g_goal": patient.get("daily_carbs_g_goal"),
            "daily_fat_g_goal": patient.get("daily_fat_g_goal"),
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
            "attachment_url": payload.get("attachment_url"),
            "attachment_type": payload.get("attachment_type"),
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

    async def list_articles(self, owner_id: str | None) -> list[dict]:
        platform_cursor = self._db.content_articles.find({"owner_id": None}).sort("order", 1)
        platform = [self._article_dict(doc) async for doc in platform_cursor]
        if not owner_id:
            return platform
        mine_cursor = self._db.content_articles.find(
            {"owner_id": self._as_oid(owner_id)}
        ).sort("updated_at", -1)
        mine = [self._article_dict(doc) async for doc in mine_cursor]
        return platform + mine

    def _article_dict(self, document: dict) -> dict:
        return {
            "id": str(document["_id"]),
            "category": document.get("category") or "",
            "title": document.get("title"),
            "description": document.get("description") or "",
            "read_time": document.get("read_time") or "",
            "emoji": document.get("emoji") or "📖",
            "sections": document.get("sections") or [],
            "owner_id": str(document["owner_id"]) if document.get("owner_id") else None,
            "video_url": document.get("video_url"),
            "source_url": document.get("source_url"),
        }

    async def get_nutritionist_profile(self, owner_id: str | None) -> dict | None:
        if not owner_id:
            return None
        owner_oid = self._as_oid(owner_id)
        user = await self._db.users.find_one({"_id": owner_oid})
        if user is None:
            return None
        profile = await self._db.nutritionist_profiles.find_one({"owner_id": owner_oid})
        patient_count = await self._db.patients.count_documents({"owner_id": owner_oid})
        profile = profile or {}
        return {
            "name": user.get("name"),
            "role_label": profile.get("role_label"),
            "bio": profile.get("bio"),
            "years_experience": profile.get("years_experience"),
            "session_price": profile.get("session_price"),
            "session_price_currency": profile.get("session_price_currency") or "MXN",
            "social_links": profile.get("social_links") or [],
            "practice_name": profile.get("practice_name"),
            "logo_url": profile.get("logo_url"),
            "brand_color": profile.get("brand_color"),
            "patient_count": patient_count,
        }

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

    async def list_food_diary_entries(self, patient_id: str, *, limit: int) -> list[dict]:
        patient_oid = self._as_oid(patient_id)
        cursor = (
            self._db.food_diary_entries.find({"patient_id": patient_oid})
            .sort("at", -1)
            .limit(limit)
        )
        return [self._serialize_food_diary_entry(doc) async for doc in cursor]

    async def create_food_diary_entry(
        self, *, owner_id: str | None, patient_id: str, payload: dict
    ) -> dict:
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
            "meal_title": payload.get("meal_title"),
            "dish": payload.get("dish"),
            "restaurant": payload.get("restaurant"),
            "kcal": payload.get("kcal"),
            "protein": payload.get("protein"),
            "carbs": payload.get("carbs"),
            "fat": payload.get("fat"),
            "notes": payload.get("notes"),
            "created_at": datetime.utcnow(),
        }
        result = await self._db.food_diary_entries.insert_one(document)
        document["_id"] = result.inserted_id
        return self._serialize_food_diary_entry(document)

    def _serialize_food_diary_entry(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "at": doc.get("at"),
            "meal_title": doc.get("meal_title"),
            "dish": doc.get("dish"),
            "restaurant": doc.get("restaurant"),
            "kcal": doc.get("kcal"),
            "protein": doc.get("protein"),
            "carbs": doc.get("carbs"),
            "fat": doc.get("fat"),
            "notes": doc.get("notes"),
        }

    async def list_recommendations(
        self, owner_id: str | None, patient_id: str, *, kind: str | None = None
    ) -> list[dict]:
        if not owner_id:
            return []
        assignment_cursor = self._db.recommendation_assignments.find(
            {"owner_id": self._as_oid(owner_id), "patient_id": self._as_oid(patient_id)}
        )
        assigned_ids = [doc["recommendation_id"] async for doc in assignment_cursor]
        if not assigned_ids:
            return []
        filters: dict = {"_id": {"$in": assigned_ids}}
        if kind:
            filters["kind"] = kind
        cursor = self._db.recommendations.find(filters).sort("created_at", -1)
        return [
            {
                "id": str(doc["_id"]),
                "kind": doc.get("kind"),
                "title": doc.get("title"),
                "subtitle": doc.get("subtitle"),
                "category": doc.get("category"),
                "brand": doc.get("brand"),
                "description": doc.get("description"),
                "benefits": doc.get("benefits") or [],
                "usage": doc.get("usage"),
                "notes": doc.get("notes"),
                "price": doc.get("price"),
                "rating": doc.get("rating"),
                "emoji": doc.get("emoji"),
                "equivalency_group_id": doc.get("equivalency_group_id"),
            }
            async for doc in cursor
        ]

    async def get_hydration_today(self, patient_id: str) -> dict:
        patient_oid = self._as_oid(patient_id)
        date_key = datetime.utcnow().strftime("%Y-%m-%d")
        doc = await self._db.hydration_logs.find_one(
            {"patient_id": patient_oid, "date": date_key}
        )
        if doc is None:
            return {"current_ml": 0, "target_ml": _DEFAULT_HYDRATION_TARGET_ML}
        return {
            "current_ml": doc.get("current_ml", 0),
            "target_ml": doc.get("target_ml", _DEFAULT_HYDRATION_TARGET_ML),
        }

    async def add_hydration(self, patient_id: str, owner_id: str | None, *, delta_ml: int) -> dict:
        patient_oid = self._as_oid(patient_id)
        owner_oid = self._as_oid(owner_id) if owner_id else None
        date_key = datetime.utcnow().strftime("%Y-%m-%d")
        existing = await self._db.hydration_logs.find_one(
            {"patient_id": patient_oid, "date": date_key}
        )
        target_ml = (
            existing.get("target_ml", _DEFAULT_HYDRATION_TARGET_ML)
            if existing
            else _DEFAULT_HYDRATION_TARGET_ML
        )
        current_ml = existing.get("current_ml", 0) if existing else 0
        next_ml = max(0, min(target_ml, current_ml + delta_ml))
        await self._db.hydration_logs.update_one(
            {"patient_id": patient_oid, "date": date_key},
            {
                "$set": {
                    "current_ml": next_ml,
                    "target_ml": target_ml,
                    "updated_at": datetime.utcnow(),
                    "owner_id": owner_oid,
                },
                "$setOnInsert": {
                    "patient_id": patient_oid,
                    "date": date_key,
                    "created_at": datetime.utcnow(),
                },
            },
            upsert=True,
        )
        return {"current_ml": next_ml, "target_ml": target_ml}

    async def list_messages(
        self, owner_id: str | None, patient_id: str, *, since: datetime | None = None
    ) -> list[dict]:
        if owner_id is None:
            return []
        filt: dict = {
            "owner_id": self._as_oid(owner_id),
            "patient_id": self._as_oid(patient_id),
        }
        if since is not None:
            filt["created_at"] = {"$gt": since}
        cursor = self._db.messages.find(filt).sort("created_at", 1)
        return [self._serialize_message(doc) async for doc in cursor]

    async def create_message(
        self,
        owner_id: str | None,
        patient_id: str,
        *,
        text: str,
        attachment_url: str | None = None,
        attachment_type: str | None = None,
    ) -> dict:
        if owner_id is None:
            raise LookupError("No nutritionist assigned yet")
        document = {
            "owner_id": self._as_oid(owner_id),
            "patient_id": self._as_oid(patient_id),
            "sender_role": "patient",
            "text": text,
            "attachment_url": attachment_url,
            "attachment_type": attachment_type,
            "created_at": datetime.utcnow(),
            "read_at": None,
        }
        result = await self._db.messages.insert_one(document)
        document["_id"] = result.inserted_id
        return self._serialize_message(document)

    def _serialize_message(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "sender_role": doc.get("sender_role"),
            "text": doc.get("text"),
            "created_at": doc.get("created_at"),
            "read_at": doc.get("read_at"),
            "attachment_url": doc.get("attachment_url"),
            "attachment_type": doc.get("attachment_type"),
        }

    async def list_checkin_templates(self, owner_id: str) -> list[dict]:
        owner_oid = self._as_oid(owner_id)
        cursor = self._db.checkin_templates.find(
            {"owner_id": owner_oid, "archived": {"$ne": True}}
        ).sort("created_at", -1)
        return [self._serialize_checkin_template(doc) async for doc in cursor]

    async def get_checkin_template(self, owner_id: str, template_id: str) -> dict | None:
        owner_oid = self._as_oid(owner_id)
        template_oid = self._as_oid(template_id)
        document = await self._db.checkin_templates.find_one(
            {"_id": template_oid, "owner_id": owner_oid}
        )
        if document is None:
            return None
        return self._serialize_checkin_template(document)

    async def create_checkin_response(
        self,
        *,
        owner_id: str,
        patient_id: str,
        template_id: str,
        appointment_id: str | None,
        answers: list[dict],
    ) -> dict:
        document = {
            "owner_id": self._as_oid(owner_id),
            "patient_id": self._as_oid(patient_id),
            "template_id": self._as_oid(template_id),
            "appointment_id": self._as_oid(appointment_id) if appointment_id else None,
            "answers": [
                {"field_id": a["field_id"], "values": a.get("values") or []} for a in answers
            ],
            "submitted_at": datetime.utcnow(),
        }
        result = await self._db.checkin_responses.insert_one(document)
        document["_id"] = result.inserted_id
        return self._serialize_checkin_response(document)

    async def list_checkin_responses(self, patient_id: str) -> list[dict]:
        patient_oid = self._as_oid(patient_id)
        cursor = self._db.checkin_responses.find({"patient_id": patient_oid}).sort(
            "submitted_at", -1
        )
        return [self._serialize_checkin_response(doc) async for doc in cursor]

    def _serialize_checkin_template(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "title": doc.get("title"),
            "description": doc.get("description"),
            "fields": doc.get("fields", []),
            "archived": doc.get("archived", False),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }

    def _serialize_checkin_response(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "template_id": str(doc["template_id"]),
            "appointment_id": str(doc["appointment_id"]) if doc.get("appointment_id") else None,
            "answers": doc.get("answers", []),
            "submitted_at": doc.get("submitted_at"),
        }

    async def get_active_workout_plan(self, patient_id: str) -> dict | None:
        patient_oid = self._as_oid(patient_id)
        assignments = await (
            self._db.workout_plan_assignments.find({"patient_id": patient_oid})
            .sort("assigned_at", -1)
            .to_list(1)
        )
        if not assignments:
            return None
        plan_id = assignments[0].get("plan_id")
        if not plan_id:
            return None
        plan = await self._db.workout_plans.find_one({"_id": plan_id})
        if not plan:
            return None
        return {
            "id": str(plan["_id"]),
            "name": plan.get("name"),
            "goal": plan.get("goal"),
            "days": plan.get("days", []),
            "updated_at": plan.get("updated_at"),
        }

    async def list_workout_logs(
        self, patient_id: str, *, workout_plan_id: str | None = None
    ) -> list[dict]:
        filt: dict = {"patient_id": self._as_oid(patient_id)}
        if workout_plan_id is not None:
            filt["workout_plan_id"] = self._as_oid(workout_plan_id)
        cursor = self._db.workout_logs.find(filt)
        return [self._serialize_workout_log(doc) async for doc in cursor]

    async def upsert_workout_log(
        self,
        *,
        owner_id: str,
        patient_id: str,
        workout_plan_id: str,
        day_index: int,
        exercise_index: int,
        sets: list[dict],
        comment: str | None = None,
        photo_url: str | None = None,
        photo_content_type: str | None = None,
    ) -> dict:
        key = {
            "owner_id": self._as_oid(owner_id),
            "patient_id": self._as_oid(patient_id),
            "workout_plan_id": self._as_oid(workout_plan_id),
            "day_index": day_index,
            "exercise_index": exercise_index,
        }
        await self._db.workout_logs.update_one(
            key,
            {
                "$set": {
                    "sets": sets,
                    "comment": comment,
                    "photo_url": photo_url,
                    "photo_content_type": photo_content_type,
                    "updated_at": datetime.utcnow(),
                },
                "$setOnInsert": {"coach_marked_done": False},
            },
            upsert=True,
        )
        doc = await self._db.workout_logs.find_one(key)
        return self._serialize_workout_log(doc)

    def _serialize_workout_log(self, doc: dict) -> dict:
        return {
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
            "attachment_url": doc.get("attachment_url"),
            "attachment_type": doc.get("attachment_type"),
        }

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid id")
        return ObjectId(id_str)
