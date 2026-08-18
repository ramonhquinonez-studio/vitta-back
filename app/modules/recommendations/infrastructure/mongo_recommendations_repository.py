from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import Recommendation


class MongoRecommendationsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def list_for_owner(
        self, owner_id: str, *, kind: str | None = None
    ) -> list[Recommendation]:
        owner_oid = self._as_oid(owner_id)
        filters: dict = {"owner_id": owner_oid}
        if kind:
            filters["kind"] = kind
        cursor = self._db.recommendations.find(filters).sort("created_at", -1)
        return [self._to_entity(doc) async for doc in cursor]

    async def create_for_owner(self, owner_id: str, payload: dict) -> Recommendation:
        owner_oid = self._as_oid(owner_id)
        document = {
            "owner_id": owner_oid,
            "kind": payload["kind"],
            "title": payload["title"],
            "subtitle": payload.get("subtitle"),
            "category": payload.get("category"),
            "brand": payload.get("brand"),
            "description": payload.get("description"),
            "benefits": payload.get("benefits") or [],
            "usage": payload.get("usage"),
            "notes": payload.get("notes"),
            "price": payload.get("price"),
            "rating": payload.get("rating"),
            "emoji": payload.get("emoji"),
            "created_at": datetime.utcnow(),
        }
        result = await self._db.recommendations.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_entity(document)

    async def update_for_owner(
        self, owner_id: str, recommendation_id: str, payload: dict
    ) -> Recommendation | None:
        owner_oid = self._as_oid(owner_id)
        rec_oid = self._as_oid(recommendation_id)
        result = await self._db.recommendations.update_one(
            {"_id": rec_oid, "owner_id": owner_oid},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        document = await self._db.recommendations.find_one({"_id": rec_oid})
        return self._to_entity(document)

    async def delete_for_owner(self, owner_id: str, recommendation_id: str) -> bool:
        owner_oid = self._as_oid(owner_id)
        rec_oid = self._as_oid(recommendation_id)
        result = await self._db.recommendations.delete_one(
            {"_id": rec_oid, "owner_id": owner_oid},
        )
        return result.deleted_count > 0

    def _to_entity(self, document: dict) -> Recommendation:
        return Recommendation(
            id=str(document["_id"]),
            owner_id=str(document["owner_id"]),
            kind=document.get("kind") or "supplement",
            title=document.get("title") or "",
            subtitle=document.get("subtitle"),
            category=document.get("category"),
            brand=document.get("brand"),
            description=document.get("description"),
            benefits=list(document.get("benefits") or []),
            usage=document.get("usage"),
            notes=document.get("notes"),
            price=document.get("price"),
            rating=document.get("rating"),
            emoji=document.get("emoji"),
        )

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid id")
        return ObjectId(id_str)
