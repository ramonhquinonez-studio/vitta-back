from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import EquivalencyFood, EquivalencyGroup


class MongoEquivalenciesRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_groups(self) -> list[EquivalencyGroup]:
        cursor = self._db.equivalency_groups.find({}).sort("name", 1)
        return [
            EquivalencyGroup(
                id=doc["_id"],
                name=doc["name"],
                kcal=doc["kcal"],
                carbs_g=doc["carbs_g"],
                protein_g=doc["protein_g"],
                fat_g=doc["fat_g"],
            )
            async for doc in cursor
        ]

    async def list_foods(
        self, owner_id: str, *, group_id: str | None = None
    ) -> list[EquivalencyFood]:
        owner_oid = self._as_oid(owner_id)
        filters: dict = {"$or": [{"owner_id": None}, {"owner_id": owner_oid}]}
        if group_id:
            filters["group_id"] = group_id
        cursor = self._db.equivalency_foods.find(filters).sort("name", 1)
        return [self._to_entity(doc) async for doc in cursor]

    async def create_food(self, owner_id: str, payload: dict) -> EquivalencyFood:
        owner_oid = self._as_oid(owner_id)
        document = {
            "owner_id": owner_oid,
            "group_id": payload["group_id"],
            "name": payload["name"],
            "portion_description": payload.get("portion_description") or "",
        }
        result = await self._db.equivalency_foods.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_entity(document)

    async def delete_food(self, owner_id: str, food_id: str) -> bool:
        owner_oid = self._as_oid(owner_id)
        food_oid = self._as_oid(food_id)
        result = await self._db.equivalency_foods.delete_one(
            {"_id": food_oid, "owner_id": owner_oid},
        )
        return result.deleted_count > 0

    def _to_entity(self, document: dict) -> EquivalencyFood:
        owner_id = document.get("owner_id")
        return EquivalencyFood(
            id=str(document["_id"]),
            group_id=document["group_id"],
            name=document["name"],
            portion_description=document.get("portion_description") or "",
            owner_id=str(owner_id) if owner_id else None,
        )

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid id")
        return ObjectId(id_str)
