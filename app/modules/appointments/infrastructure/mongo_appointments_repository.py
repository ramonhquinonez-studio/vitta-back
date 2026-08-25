from datetime import datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import Appointment, AppointmentPatient


class MongoAppointmentsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_for_owner(
        self,
        owner_id: str,
        *,
        status: str | None,
        from_dt: datetime | None,
        to_dt: datetime | None,
        query: str | None,
        patient_id: str | None = None,
    ) -> list[Appointment]:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        match: dict[str, Any] = {"owner_id": owner_oid}
        if status:
            match["status"] = status
        if patient_id:
            match["patient_id"] = self._oid_maybe(patient_id)
        match.update(self._match_from_to(from_dt, to_dt))

        pipeline: list[dict[str, Any]] = [
            {"$match": match},
            {"$sort": {"start": 1}},
            {
                "$lookup": {
                    "from": "patients",
                    "localField": "patient_id",
                    "foreignField": "_id",
                    "as": "patient",
                }
            },
            {"$addFields": {"patient": {"$first": "$patient"}}},
        ]
        if query:
            pipeline.append(
                {
                    "$match": {
                        "$or": [
                            {"patient.name": {"$regex": query, "$options": "i"}},
                            {"note": {"$regex": query, "$options": "i"}},
                        ]
                    }
                }
            )

        cursor = self._db.appointments.aggregate(pipeline)
        appointments: list[Appointment] = []
        async for doc in cursor:
            appointments.append(self._to_entity(doc))
        return appointments

    async def get_for_owner(self, owner_id: str, appointment_id: str) -> Appointment | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        appointment_oid = self._as_oid(appointment_id)
        cursor = self._db.appointments.aggregate(
            [
                {"$match": {"_id": appointment_oid, "owner_id": owner_oid}},
                {
                    "$lookup": {
                        "from": "patients",
                        "localField": "patient_id",
                        "foreignField": "_id",
                        "as": "patient",
                    }
                },
                {"$addFields": {"patient": {"$first": "$patient"}}},
            ]
        )
        docs = await cursor.to_list(1)
        if not docs:
            return None
        return self._to_entity(docs[0])

    async def create_for_owner(
        self,
        owner_id: str,
        *,
        patient_id: str,
        start: datetime,
        end: datetime,
        mode: str,
        status: str,
        note: str | None,
        plan_id: str | None,
        body_composition_id: str | None,
        no_sync: bool,
    ) -> Appointment:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        now = datetime.utcnow()
        doc = {
            "owner_id": owner_oid,
            "patient_id": self._oid_maybe(patient_id),
            "start": start,
            "end": end,
            "mode": mode,
            "status": status,
            "note": note,
            "plan_id": self._oid_maybe(plan_id),
            "body_composition_id": self._oid_maybe(body_composition_id),
            "no_sync": no_sync,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._db.appointments.insert_one(doc)
        created = await self.get_for_owner(owner_id, str(result.inserted_id))
        if created is None:
            raise RuntimeError("Appointment creation failed")
        return created

    async def update_for_owner(
        self,
        owner_id: str,
        appointment_id: str,
        updates: dict,
    ) -> Appointment | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        appointment_oid = self._as_oid(appointment_id)

        mongo_updates = dict(updates)
        if "patient_id" in mongo_updates:
            mongo_updates["patient_id"] = self._oid_maybe(mongo_updates["patient_id"])
        if "plan_id" in mongo_updates:
            mongo_updates["plan_id"] = self._oid_maybe(mongo_updates["plan_id"])
        if "body_composition_id" in mongo_updates:
            mongo_updates["body_composition_id"] = self._oid_maybe(
                mongo_updates["body_composition_id"]
            )
        mongo_updates["updated_at"] = datetime.utcnow()

        result = await self._db.appointments.update_one(
            {"_id": appointment_oid, "owner_id": owner_oid},
            {"$set": mongo_updates},
        )
        if result.matched_count == 0:
            return None
        return await self.get_for_owner(owner_id, appointment_id)

    async def delete_for_owner(self, owner_id: str, appointment_id: str) -> Appointment | None:
        current = await self.get_for_owner(owner_id, appointment_id)
        if current is None:
            return None
        owner_oid = self._as_oid(owner_id, field_name="owner")
        await self._db.appointments.delete_one(
            {"_id": self._as_oid(appointment_id), "owner_id": owner_oid}
        )
        return current

    async def find_overlap(
        self,
        owner_id: str,
        *,
        start: datetime,
        end: datetime,
        exclude_appointment_id: str | None = None,
    ) -> Appointment | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        filt: dict[str, Any] = {
            "owner_id": owner_oid,
            "start": {"$lt": end},
            "end": {"$gt": start},
            "status": {"$in": ["pending", "confirmed"]},
        }
        if exclude_appointment_id:
            filt["_id"] = {"$ne": self._as_oid(exclude_appointment_id)}
        doc = await self._db.appointments.find_one(filt)
        if doc is None:
            return None
        return self._to_entity(doc)

    async def patient_exists_for_owner(self, owner_id: str, patient_id: str) -> bool:
        patient_oid = self._oid_maybe(patient_id)
        if not isinstance(patient_oid, ObjectId):
            return True
        owner_oid = self._as_oid(owner_id, field_name="owner")
        doc = await self._db.patients.find_one({"_id": patient_oid, "owner_id": owner_oid})
        return doc is not None

    async def set_google_event_id(
        self, owner_id: str, appointment_id: str, google_event_id: str
    ) -> Appointment | None:
        appointment_oid = self._as_oid(appointment_id)
        owner_oid = self._as_oid(owner_id, field_name="owner")
        await self._db.appointments.update_one(
            {"_id": appointment_oid, "owner_id": owner_oid},
            {"$set": {"google_event_id": google_event_id}},
        )
        doc = await self._db.appointments.find_one({"_id": appointment_oid, "owner_id": owner_oid})
        if doc is None:
            return None
        if isinstance(doc.get("patient_id"), ObjectId):
            patient = await self._db.patients.find_one(
                {"_id": doc["patient_id"]},
                {"name": 1, "email": 1},
            )
            if patient is not None:
                doc["patient"] = patient
        return self._to_entity(doc)

    def _to_entity(self, doc: dict) -> Appointment:
        patient_doc = doc.get("patient")
        patient = None
        if isinstance(patient_doc, dict):
            patient = AppointmentPatient(
                id=self._stringify_maybe_oid(patient_doc.get("_id")),
                name=patient_doc.get("name"),
                email=patient_doc.get("email"),
            )
        return Appointment(
            id=str(doc["_id"]),
            owner_id=self._stringify_maybe_oid(doc.get("owner_id")) or "",
            patient_id=self._stringify_maybe_oid(doc.get("patient_id")),
            start=doc.get("start"),
            end=doc.get("end"),
            mode=doc.get("mode"),
            status=doc.get("status"),
            note=doc.get("note"),
            plan_id=self._stringify_maybe_oid(doc.get("plan_id")),
            body_composition_id=self._stringify_maybe_oid(doc.get("body_composition_id")),
            no_sync=bool(doc.get("no_sync", False)),
            google_event_id=doc.get("google_event_id"),
            patient=patient,
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)

    def _oid_maybe(self, value: str | None):
        if value is None:
            return None
        return ObjectId(value) if ObjectId.is_valid(value) else value

    def _stringify_maybe_oid(self, value):
        if isinstance(value, ObjectId):
            return str(value)
        if value is None:
            return None
        return str(value)

    def _match_from_to(
        self,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> dict[str, Any]:
        if not from_dt and not to_dt:
            return {}
        rng: dict[str, Any] = {}
        if from_dt:
            rng["$gte"] = from_dt
        if to_dt:
            rng["$lte"] = to_dt
        return {"start": rng}
