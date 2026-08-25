from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import FormField, FormTemplate


class MongoCheckinRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    async def create_template(self, owner_id: str, payload: dict) -> FormTemplate:
        owner_oid = self._as_oid(owner_id)
        now = datetime.utcnow()
        document = {
            "owner_id": owner_oid,
            "title": payload["title"],
            "description": payload.get("description"),
            "fields": [self._field_to_doc(f) for f in payload["fields"]],
            "archived": False,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._db.checkin_templates.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_entity(document)

    async def list_templates(
        self, owner_id: str, *, include_archived: bool = False
    ) -> list[FormTemplate]:
        owner_oid = self._as_oid(owner_id)
        filters: dict = {"owner_id": owner_oid}
        if not include_archived:
            filters["archived"] = {"$ne": True}
        cursor = self._db.checkin_templates.find(filters).sort("created_at", -1)
        return [self._to_entity(doc) async for doc in cursor]

    async def get_template(self, owner_id: str, template_id: str) -> FormTemplate | None:
        owner_oid = self._as_oid(owner_id)
        template_oid = self._as_oid(template_id)
        document = await self._db.checkin_templates.find_one(
            {"_id": template_oid, "owner_id": owner_oid}
        )
        if document is None:
            return None
        return self._to_entity(document)

    async def update_template(
        self, owner_id: str, template_id: str, payload: dict
    ) -> FormTemplate | None:
        owner_oid = self._as_oid(owner_id)
        template_oid = self._as_oid(template_id)
        result = await self._db.checkin_templates.update_one(
            {"_id": template_oid, "owner_id": owner_oid},
            {
                "$set": {
                    "title": payload["title"],
                    "description": payload.get("description"),
                    "fields": [self._field_to_doc(f) for f in payload["fields"]],
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        if result.matched_count == 0:
            return None
        return await self.get_template(owner_id, template_id)

    async def archive_template(self, owner_id: str, template_id: str) -> bool:
        owner_oid = self._as_oid(owner_id)
        template_oid = self._as_oid(template_id)
        result = await self._db.checkin_templates.update_one(
            {"_id": template_oid, "owner_id": owner_oid},
            {"$set": {"archived": True, "updated_at": datetime.utcnow()}},
        )
        return result.matched_count > 0

    def _field_to_doc(self, field_payload: dict) -> dict:
        return {
            "id": field_payload["id"],
            "type": field_payload["type"],
            "label": field_payload["label"],
            "required": bool(field_payload.get("required", False)),
            "options": field_payload.get("options") or [],
            "scale_min": field_payload.get("scale_min"),
            "scale_max": field_payload.get("scale_max"),
        }

    def _to_entity(self, document: dict) -> FormTemplate:
        return FormTemplate(
            id=str(document["_id"]),
            owner_id=str(document["owner_id"]),
            title=document["title"],
            description=document.get("description"),
            fields=[
                FormField(
                    id=f["id"],
                    type=f["type"],
                    label=f["label"],
                    required=f.get("required", False),
                    options=f.get("options") or [],
                    scale_min=f.get("scale_min"),
                    scale_max=f.get("scale_max"),
                )
                for f in document.get("fields", [])
            ],
            archived=document.get("archived", False),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

    def _as_oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid id")
        return ObjectId(id_str)
