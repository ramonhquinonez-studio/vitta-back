from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.entities import Message


class MongoMessagingRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    def _as_oid(self, id_str: str, field_name: str = "id") -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError(f"Invalid {field_name}")
        return ObjectId(id_str)

    async def list_for_thread(
        self, owner_id: str, patient_id: str, *, since: datetime | None = None
    ) -> list[Message]:
        filt: dict = {
            "owner_id": self._as_oid(owner_id, "owner"),
            "patient_id": self._as_oid(patient_id, "patient"),
        }
        if since is not None:
            filt["created_at"] = {"$gt": since}
        cursor = self._db.messages.find(filt).sort("created_at", 1)
        return [self._to_entity(doc) async for doc in cursor]

    async def create(
        self, owner_id: str, patient_id: str, *, sender_role: str, text: str
    ) -> Message:
        document = {
            "owner_id": self._as_oid(owner_id, "owner"),
            "patient_id": self._as_oid(patient_id, "patient"),
            "sender_role": sender_role,
            "text": text,
            "created_at": datetime.utcnow(),
            "read_at": None,
        }
        result = await self._db.messages.insert_one(document)
        document["_id"] = result.inserted_id
        return self._to_entity(document)

    async def patient_exists_for_owner(self, owner_id: str, patient_id: str) -> bool:
        doc = await self._db.patients.find_one(
            {"_id": self._as_oid(patient_id, "patient"), "owner_id": self._as_oid(owner_id, "owner")}
        )
        return doc is not None

    def _to_entity(self, doc: dict) -> Message:
        return Message(
            id=str(doc["_id"]),
            owner_id=str(doc["owner_id"]),
            patient_id=str(doc["patient_id"]),
            sender_role=doc["sender_role"],
            text=doc["text"],
            created_at=doc["created_at"],
            read_at=doc.get("read_at"),
        )
