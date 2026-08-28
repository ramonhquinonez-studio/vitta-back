from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoUsersRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def get_user(self, user_id: str) -> dict | None:
        if not ObjectId.is_valid(user_id):
            return None
        doc = await self._db.users.find_one({"_id": ObjectId(user_id)})
        if not doc:
            return None
        return {
            "id": str(doc["_id"]),
            "email": doc.get("email"),
            "name": doc.get("name"),
            "role": doc.get("role"),
            "created_at": doc.get("created_at"),
        }
