from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoExerciseLibraryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_for_owner(self, owner_id: str) -> list[dict]:
        cursor = self._db.exercise_library.find(
            {"owner_id": self._as_oid(owner_id, field_name="owner")}
        ).sort("name", 1)
        return [self._serialize(doc) async for doc in cursor]

    async def create_for_owner(self, owner_id: str, payload: dict) -> dict:
        document = {
            "owner_id": self._as_oid(owner_id, field_name="owner"),
            "name": payload["name"],
            "default_sets": payload.get("default_sets"),
            "default_reps": payload.get("default_reps"),
            "default_weight_kg": payload.get("default_weight_kg"),
            "default_duration_seconds": payload.get("default_duration_seconds"),
            "default_rest_seconds": payload.get("default_rest_seconds"),
            "video_url": payload.get("video_url"),
            "notes": payload.get("notes"),
        }
        result = await self._db.exercise_library.insert_one(document)
        document["_id"] = result.inserted_id
        return self._serialize(document)

    async def delete_for_owner(self, owner_id: str, item_id: str) -> bool:
        result = await self._db.exercise_library.delete_one(
            {
                "_id": self._as_oid(item_id),
                "owner_id": self._as_oid(owner_id, field_name="owner"),
            }
        )
        return result.deleted_count > 0

    def _serialize(self, doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "name": doc["name"],
            "default_sets": doc.get("default_sets"),
            "default_reps": doc.get("default_reps"),
            "default_weight_kg": doc.get("default_weight_kg"),
            "default_duration_seconds": doc.get("default_duration_seconds"),
            "default_rest_seconds": doc.get("default_rest_seconds"),
            "video_url": doc.get("video_url"),
            "notes": doc.get("notes"),
        }

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)
