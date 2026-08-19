import secrets
from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from ..domain.entities import AuthUser

# Same alphabet/length as the nutritionist-issued invite codes
# (`mongo_patients_repository.py`) — no ambiguous characters, easy to read
# back from the patient sharing it out loud or by text.
_CONNECTION_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CONNECTION_CODE_LENGTH = 8


class MongoAuthRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        doc = await self._db.users.find_one({"email": email})
        if doc is None:
            return None
        return self._to_entity(doc)

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        if not ObjectId.is_valid(user_id):
            return None
        doc = await self._db.users.find_one({"_id": ObjectId(user_id)})
        if doc is None:
            return None
        return self._to_entity(doc)

    async def create_user(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role: str,
    ) -> AuthUser:
        now = datetime.utcnow()
        doc = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._db.users.insert_one(doc)
        created = await self._db.users.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("User creation failed")
        return self._to_entity(created)

    async def get_invite_code(self, code: str) -> dict | None:
        doc = await self._db.invite_codes.find_one({"code": code})
        if doc is None:
            return None
        return {
            "code": doc["code"],
            "owner_id": str(doc["owner_id"]),
            "patient_id": str(doc["patient_id"]) if doc.get("patient_id") else None,
            "expires_at": doc.get("expires_at"),
            "used_at": doc.get("used_at"),
        }

    async def consume_invite_code(self, code: str, user_id: str) -> None:
        await self._db.invite_codes.update_one(
            {"code": code},
            {
                "$set": {
                    "used_at": datetime.utcnow(),
                    "used_by_user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
                }
            },
        )

    async def create_patient_for_user(
        self,
        *,
        user_id: str,
        owner_id: str,
        name: str,
    ) -> None:
        await self._db.patients.insert_one(
            {
                "user_id": ObjectId(user_id),
                "owner_id": ObjectId(owner_id),
                "name": name,
                "age": None,
                "sex": None,
                "height_cm": None,
                "allergies": [],
                "created_at": datetime.utcnow(),
            }
        )

    async def link_user_to_patient(self, *, user_id: str, patient_id: str) -> bool:
        if not ObjectId.is_valid(patient_id):
            return False
        result = await self._db.patients.update_one(
            {"_id": ObjectId(patient_id), "user_id": None},
            {"$set": {"user_id": ObjectId(user_id)}},
        )
        return result.modified_count > 0

    async def create_unowned_patient_for_user(self, *, user_id: str, name: str) -> str:
        for _ in range(5):
            code = "".join(
                secrets.choice(_CONNECTION_CODE_ALPHABET)
                for _ in range(_CONNECTION_CODE_LENGTH)
            )
            try:
                await self._db.patients.insert_one(
                    {
                        "user_id": ObjectId(user_id),
                        "owner_id": None,
                        "name": name,
                        "age": None,
                        "sex": None,
                        "height_cm": None,
                        "allergies": [],
                        "connection_code": code,
                        "created_at": datetime.utcnow(),
                    }
                )
                return code
            except DuplicateKeyError:
                continue
        raise RuntimeError("Could not generate a unique connection code")

    async def get_patient_name(self, patient_id: str) -> str | None:
        if not ObjectId.is_valid(patient_id):
            return None
        doc = await self._db.patients.find_one({"_id": ObjectId(patient_id)}, {"name": 1})
        return doc.get("name") if doc else None

    async def update_password_hash(self, user_id: str, password_hash: str) -> None:
        await self._db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": password_hash, "updated_at": datetime.utcnow()}},
        )

    def _to_entity(self, doc: dict) -> AuthUser:
        return AuthUser(
            id=str(doc["_id"]),
            email=str(doc.get("email") or ""),
            name=doc.get("name"),
            role=str(doc.get("role") or "user"),
            password_hash=doc.get("password_hash"),
        )
