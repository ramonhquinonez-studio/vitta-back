from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import NutritionistProfile, SocialLink


class MongoNutritionistProfileRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def get_for_owner(self, owner_id: str) -> NutritionistProfile | None:
        owner_oid = self._as_oid(owner_id)
        document = await self._db.nutritionist_profiles.find_one({"owner_id": owner_oid})
        if document is None:
            return None
        return self._to_entity(document)

    async def upsert_for_owner(self, owner_id: str, payload: dict) -> NutritionistProfile:
        owner_oid = self._as_oid(owner_id)
        await self._db.nutritionist_profiles.update_one(
            {"owner_id": owner_oid},
            {"$set": payload},
            upsert=True,
        )
        document = await self._db.nutritionist_profiles.find_one({"owner_id": owner_oid})
        if document is None:
            raise RuntimeError("Nutritionist profile upsert failed")
        return self._to_entity(document)

    async def count_patients_for_owner(self, owner_id: str) -> int:
        owner_oid = self._as_oid(owner_id)
        return await self._db.patients.count_documents({"owner_id": owner_oid})

    def _to_entity(self, document: dict) -> NutritionistProfile:
        return NutritionistProfile(
            owner_id=str(document["owner_id"]),
            role_label=document.get("role_label"),
            bio=document.get("bio"),
            years_experience=document.get("years_experience"),
            session_price=document.get("session_price"),
            session_price_currency=document.get("session_price_currency") or "MXN",
            social_links=[
                SocialLink(platform=link["platform"], handle=link["handle"])
                for link in document.get("social_links") or []
            ],
        )

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid owner id")
        return ObjectId(id_str)
