from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import MacroSplit, NutritionistProfile, SocialLink


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

    async def mark_onboarding_completed(self, owner_id: str) -> NutritionistProfile:
        return await self.upsert_for_owner(
            owner_id, {"onboarding_completed_at": datetime.utcnow()}
        )

    def _to_entity(self, document: dict) -> NutritionistProfile:
        macro_split_doc = document.get("macro_split")
        macro_split = (
            MacroSplit(
                protein_pct=macro_split_doc["protein_pct"],
                carbs_pct=macro_split_doc["carbs_pct"],
                fat_pct=macro_split_doc["fat_pct"],
            )
            if macro_split_doc
            else None
        )
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
            cedula=document.get("cedula"),
            practice_name=document.get("practice_name"),
            logo_url=document.get("logo_url"),
            brand_color=document.get("brand_color"),
            city=document.get("city"),
            specializations=list(document.get("specializations") or []),
            energy_equation=document.get("energy_equation"),
            portions_mode=document.get("portions_mode"),
            macro_split=macro_split,
            units=document.get("units"),
            meals_per_day=document.get("meals_per_day"),
            onboarding_completed_at=document.get("onboarding_completed_at"),
        )

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid owner id")
        return ObjectId(id_str)
