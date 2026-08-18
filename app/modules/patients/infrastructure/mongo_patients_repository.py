import secrets
import string
from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
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

    async def create_invite_code(self, owner_id: str) -> dict:
        owner_oid = self._as_oid(owner_id, field_name="owner")
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
