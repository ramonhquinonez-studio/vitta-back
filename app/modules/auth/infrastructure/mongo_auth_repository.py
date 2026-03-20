from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import AuthUser


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

    def _to_entity(self, doc: dict) -> AuthUser:
        return AuthUser(
            id=str(doc["_id"]),
            email=str(doc.get("email") or ""),
            name=doc.get("name"),
            role=str(doc.get("role") or "user"),
            password_hash=doc.get("password_hash"),
        )
