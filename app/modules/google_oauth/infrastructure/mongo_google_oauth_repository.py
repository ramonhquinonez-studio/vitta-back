from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoGoogleOAuthRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def get_tokens(self, user_id: str) -> dict | None:
        return await self._db.google_tokens.find_one({"user_id": ObjectId(user_id)})

    async def save_tokens(self, user_id: str, tokens: dict) -> None:
        await self._db.google_tokens.update_one(
            {"user_id": ObjectId(user_id)}, {"$set": tokens}, upsert=True
        )

    async def delete_tokens(self, user_id: str) -> dict | None:
        doc = await self._db.google_tokens.find_one({"user_id": ObjectId(user_id)})
        if doc is None:
            return None
        await self._db.google_tokens.delete_one({"user_id": ObjectId(user_id)})
        return doc
