from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import Patient


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

    def _to_entity(self, document: dict) -> Patient:
        return Patient(
            id=str(document["_id"]),
            owner_id=str(document["owner_id"]),
            name=document["name"],
            age=document.get("age"),
            sex=document.get("sex"),
            height_cm=document.get("height_cm"),
            allergies=list(document.get("allergies") or []),
            notes=document.get("notes"),
        )

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)
