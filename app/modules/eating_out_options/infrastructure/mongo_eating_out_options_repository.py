from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import EatingOutOption


class MongoEatingOutOptionsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_for_owner(self, owner_id: str) -> list[EatingOutOption]:
        owner_oid = self._as_oid(owner_id)
        cursor = self._db.eating_out_options.find({"owner_id": owner_oid}).sort(
            "created_at", -1
        )
        return [self._to_entity(doc) async for doc in cursor]

    async def create_for_owner(self, owner_id: str, payload: dict) -> EatingOutOption:
        owner_oid = self._as_oid(owner_id)
        document = {
            "owner_id": owner_oid,
            "restaurant": payload["restaurant"],
            "dish": payload["dish"],
            "kcal": payload.get("kcal"),
            "protein": payload.get("protein"),
            "carbs": payload.get("carbs"),
            "fat": payload.get("fat"),
            "created_at": datetime.utcnow(),
        }
        result = await self._db.eating_out_options.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_entity(document)

    async def update_for_owner(
        self, owner_id: str, option_id: str, payload: dict
    ) -> EatingOutOption | None:
        owner_oid = self._as_oid(owner_id)
        option_oid = self._as_oid(option_id)
        result = await self._db.eating_out_options.update_one(
            {"_id": option_oid, "owner_id": owner_oid},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        document = await self._db.eating_out_options.find_one({"_id": option_oid})
        return self._to_entity(document)

    async def delete_for_owner(self, owner_id: str, option_id: str) -> bool:
        owner_oid = self._as_oid(owner_id)
        option_oid = self._as_oid(option_id)
        result = await self._db.eating_out_options.delete_one(
            {"_id": option_oid, "owner_id": owner_oid},
        )
        return result.deleted_count > 0

    def _to_entity(self, document: dict) -> EatingOutOption:
        return EatingOutOption(
            id=str(document["_id"]),
            owner_id=str(document["owner_id"]),
            restaurant=document.get("restaurant") or "",
            dish=document.get("dish") or "",
            kcal=document.get("kcal"),
            protein=document.get("protein"),
            carbs=document.get("carbs"),
            fat=document.get("fat"),
        )

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid id")
        return ObjectId(id_str)
