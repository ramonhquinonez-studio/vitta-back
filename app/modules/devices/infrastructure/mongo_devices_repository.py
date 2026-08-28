from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoDevicesRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def register_device(self, *, user_id: str, token: str, platform: str) -> None:
        uid = ObjectId(user_id)
        now = datetime.utcnow()
        await self._db.devices.update_one(
            {"user_id": uid, "token": token},
            {
                "$set": {"platform": platform, "updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    async def list_tokens_for_user(self, user_id: str) -> list[str]:
        uid = ObjectId(user_id)
        cursor = self._db.devices.find({"user_id": uid}, {"token": 1, "_id": 0})
        return [doc["token"] async for doc in cursor]
