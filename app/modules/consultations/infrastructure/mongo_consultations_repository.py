from dataclasses import asdict
from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import (
    Consultation,
    DistributionInput,
    EvaluationSnapshot,
    MenuAllocationItem,
    RequirementInput,
)


class MongoConsultationsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def find_open_draft(self, owner_id: str, patient_id: str) -> Consultation | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        patient_oid = self._oid_maybe(patient_id)
        doc = await self._db.consultations.find_one(
            {"owner_id": owner_oid, "patient_id": patient_oid, "status": "draft"},
            sort=[("created_at", -1)],
        )
        if doc is None:
            return None
        return self._to_entity(doc)

    async def create_draft(
        self,
        owner_id: str,
        *,
        patient_id: str,
        appointment_id: str | None,
    ) -> Consultation:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        now = datetime.utcnow()
        doc = {
            "owner_id": owner_oid,
            "patient_id": self._oid_maybe(patient_id),
            "appointment_id": self._oid_maybe(appointment_id),
            "status": "draft",
            "current_step": 1,
            "visit_type": None,
            "evaluation": None,
            "requirement": None,
            "distribution": None,
            "menu_allocations": None,
            "private_notes": None,
            "next_appointment_id": None,
            "completed_at": None,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._db.consultations.insert_one(doc)
        created = await self.get_for_owner(owner_id, str(result.inserted_id))
        if created is None:
            raise RuntimeError("Consultation creation failed")
        return created

    async def get_for_owner(self, owner_id: str, consultation_id: str) -> Consultation | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        consultation_oid = self._as_oid(consultation_id)
        doc = await self._db.consultations.find_one(
            {"_id": consultation_oid, "owner_id": owner_oid}
        )
        if doc is None:
            return None
        return self._to_entity(doc)

    async def update_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        owner_oid = self._as_oid(owner_id, field_name="owner")
        consultation_oid = self._as_oid(consultation_id)

        mongo_updates = dict(updates)
        if "appointment_id" in mongo_updates:
            mongo_updates["appointment_id"] = self._oid_maybe(mongo_updates["appointment_id"])
        if "next_appointment_id" in mongo_updates:
            mongo_updates["next_appointment_id"] = self._oid_maybe(
                mongo_updates["next_appointment_id"]
            )
        mongo_updates["updated_at"] = datetime.utcnow()

        result = await self._db.consultations.update_one(
            {"_id": consultation_oid, "owner_id": owner_oid},
            {"$set": mongo_updates},
        )
        if result.matched_count == 0:
            return None
        return await self.get_for_owner(owner_id, consultation_id)

    async def update_evaluation_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        current = await self.get_for_owner(owner_id, consultation_id)
        if current is None:
            return None
        existing = asdict(current.evaluation) if current.evaluation else asdict(EvaluationSnapshot())
        merged = {**existing, **updates}
        return await self.update_for_owner(owner_id, consultation_id, {"evaluation": merged})

    async def update_requirement_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        current = await self.get_for_owner(owner_id, consultation_id)
        if current is None:
            return None
        existing = asdict(current.requirement) if current.requirement else asdict(RequirementInput())
        merged = {**existing, **updates}
        return await self.update_for_owner(owner_id, consultation_id, {"requirement": merged})

    async def update_distribution_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        current = await self.get_for_owner(owner_id, consultation_id)
        if current is None:
            return None
        existing = (
            asdict(current.distribution) if current.distribution else asdict(DistributionInput())
        )
        merged = {**existing, **updates}
        return await self.update_for_owner(owner_id, consultation_id, {"distribution": merged})

    async def update_menu_for_owner(
        self, owner_id: str, consultation_id: str, allocations: list[dict]
    ) -> Consultation | None:
        return await self.update_for_owner(
            owner_id, consultation_id, {"menu_allocations": allocations}
        )

    async def update_close_for_owner(
        self, owner_id: str, consultation_id: str, updates: dict
    ) -> Consultation | None:
        return await self.update_for_owner(owner_id, consultation_id, updates)

    async def complete_for_owner(self, owner_id: str, consultation_id: str) -> Consultation | None:
        return await self.update_for_owner(
            owner_id,
            consultation_id,
            {"status": "completed", "completed_at": datetime.utcnow()},
        )

    async def reopen_for_owner(self, owner_id: str, consultation_id: str) -> Consultation | None:
        return await self.update_for_owner(
            owner_id,
            consultation_id,
            {"status": "draft", "completed_at": None},
        )

    def _to_entity(self, doc: dict) -> Consultation:
        evaluation_doc = doc.get("evaluation")
        evaluation = EvaluationSnapshot(**evaluation_doc) if evaluation_doc else None
        requirement_doc = doc.get("requirement")
        requirement = RequirementInput(**requirement_doc) if requirement_doc else None
        distribution_doc = doc.get("distribution")
        distribution = DistributionInput(**distribution_doc) if distribution_doc else None
        menu_allocations_docs = doc.get("menu_allocations")
        menu_allocations = (
            [MenuAllocationItem(**item) for item in menu_allocations_docs]
            if menu_allocations_docs is not None
            else None
        )
        return Consultation(
            id=str(doc["_id"]),
            owner_id=self._stringify_maybe_oid(doc.get("owner_id")) or "",
            patient_id=self._stringify_maybe_oid(doc.get("patient_id")) or "",
            appointment_id=self._stringify_maybe_oid(doc.get("appointment_id")),
            status=doc.get("status", "draft"),
            current_step=doc.get("current_step", 1),
            visit_type=doc.get("visit_type"),
            evaluation=evaluation,
            requirement=requirement,
            distribution=distribution,
            menu_allocations=menu_allocations,
            private_notes=doc.get("private_notes"),
            next_appointment_id=self._stringify_maybe_oid(doc.get("next_appointment_id")),
            completed_at=doc.get("completed_at"),
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
