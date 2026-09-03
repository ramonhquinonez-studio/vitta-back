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
            "equivalency_group_id": payload.get("equivalency_group_id"),
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

    async def list_platform_recommendations(
        self, *, kind: str | None = None
    ) -> list[Recommendation]:
        filters: dict = {"owner_id": None}
        if kind:
            filters["kind"] = kind
        cursor = self._db.recommendations.find(filters).sort("created_at", -1)
        return [self._to_entity(doc) async for doc in cursor]

    async def assign_to_patients(
        self, owner_id: str, recommendation_id: str, patient_ids: list[str]
    ) -> int:
        owner_oid = self._as_oid(owner_id)
        rec_oid = self._as_oid(recommendation_id)
        rec = await self._db.recommendations.find_one({"_id": rec_oid, "owner_id": owner_oid})
        if rec is None:
            return 0
        count = 0
        for patient_id in patient_ids:
            patient_oid = self._as_oid(patient_id)
            result = await self._db.recommendation_assignments.update_one(
                {
                    "owner_id": owner_oid,
                    "recommendation_id": rec_oid,
                    "patient_id": patient_oid,
                },
                {"$setOnInsert": {"assigned_at": datetime.utcnow()}},
                upsert=True,
            )
            if result.upserted_id is not None or result.matched_count > 0:
                count += 1
        return count

    async def unassign_from_patient(
        self, owner_id: str, recommendation_id: str, patient_id: str
    ) -> bool:
        owner_oid = self._as_oid(owner_id)
        rec_oid = self._as_oid(recommendation_id)
        patient_oid = self._as_oid(patient_id)
        result = await self._db.recommendation_assignments.delete_one(
            {"owner_id": owner_oid, "recommendation_id": rec_oid, "patient_id": patient_oid}
        )
        return result.deleted_count > 0

    async def list_assigned_patient_ids(
        self, owner_id: str, recommendation_id: str
    ) -> list[str]:
        owner_oid = self._as_oid(owner_id)
        rec_oid = self._as_oid(recommendation_id)
        cursor = self._db.recommendation_assignments.find(
            {"owner_id": owner_oid, "recommendation_id": rec_oid}
        )
        return [str(doc["patient_id"]) async for doc in cursor]

    def _to_entity(self, document: dict) -> Recommendation:
        owner_id = document.get("owner_id")
        return Recommendation(
            id=str(document["_id"]),
            owner_id=str(owner_id) if owner_id is not None else None,
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
            equivalency_group_id=document.get("equivalency_group_id"),
        )

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid id")
        return ObjectId(id_str)
