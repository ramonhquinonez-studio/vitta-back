from __future__ import annotations

from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..domain.payment_entities import ConnectAccount, Payment


class MongoPaymentsRepository:
    """`payments` — the ledger for patient → nutritionist charges.
    `stripe_connect_accounts` — one Express account per nutritionist."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    # -- payments -----------------------------------------------------

    async def create_payment(self, payment: Payment) -> Payment:
        now = datetime.utcnow()
        doc = {
            "kind": payment.kind,
            "consultation_id": payment.consultation_id,
            "appointment_id": payment.appointment_id,
            "patient_id": payment.patient_id,
            "nutritionist_id": payment.nutritionist_id,
            "amount_cents": payment.amount_cents,
            "fee_cents": payment.fee_cents,
            "currency": payment.currency,
            "status": payment.status,
            "payment_intent_id": payment.payment_intent_id,
            "refunded_cents": payment.refunded_cents,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._db.payments.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._payment_to_entity(doc)

    async def get_payment(self, payment_id: str) -> Payment | None:
        doc = await self._db.payments.find_one({"_id": self._oid(payment_id)})
        return self._payment_to_entity(doc) if doc else None

    async def get_payment_by_intent(self, payment_intent_id: str) -> Payment | None:
        doc = await self._db.payments.find_one({"payment_intent_id": payment_intent_id})
        return self._payment_to_entity(doc) if doc else None

    async def update_payment(self, payment_id: str, updates: dict) -> Payment | None:
        updates = {**updates, "updated_at": datetime.utcnow()}
        await self._db.payments.update_one({"_id": self._oid(payment_id)}, {"$set": updates})
        return await self.get_payment(payment_id)

    async def list_for_patient(self, patient_id: str) -> list[Payment]:
        cursor = self._db.payments.find({"patient_id": patient_id}).sort("created_at", -1)
        return [self._payment_to_entity(d) async for d in cursor]

    async def list_for_nutritionist(self, nutritionist_id: str) -> list[Payment]:
        cursor = self._db.payments.find({"nutritionist_id": nutritionist_id}).sort("created_at", -1)
        return [self._payment_to_entity(d) async for d in cursor]

    # -- connect accounts -------------------------------------------

    async def get_connect_account(self, owner_id: str) -> ConnectAccount | None:
        doc = await self._db.stripe_connect_accounts.find_one({"owner_id": owner_id})
        return self._connect_to_entity(doc) if doc else None

    async def get_connect_account_by_id(self, account_id: str) -> ConnectAccount | None:
        doc = await self._db.stripe_connect_accounts.find_one({"account_id": account_id})
        return self._connect_to_entity(doc) if doc else None

    async def upsert_connect_account(self, account: ConnectAccount) -> ConnectAccount:
        await self._db.stripe_connect_accounts.update_one(
            {"owner_id": account.owner_id},
            {
                "$set": {
                    "owner_id": account.owner_id,
                    "account_id": account.account_id,
                    "charges_enabled": account.charges_enabled,
                    "payouts_enabled": account.payouts_enabled,
                    "requirements_due": account.requirements_due or [],
                    "disabled_reason": account.disabled_reason,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
        return await self.get_connect_account(account.owner_id)

    # -- mapping ----------------------------------------------------

    def _oid(self, id_str: str) -> ObjectId:
        if not ObjectId.is_valid(id_str):
            raise ValueError("Invalid id")
        return ObjectId(id_str)

    def _payment_to_entity(self, doc: dict) -> Payment:
        return Payment(
            id=str(doc["_id"]),
            kind=doc.get("kind", "consultation"),
            consultation_id=doc.get("consultation_id"),
            appointment_id=doc.get("appointment_id"),
            patient_id=doc.get("patient_id", ""),
            nutritionist_id=doc.get("nutritionist_id", ""),
            amount_cents=int(doc.get("amount_cents", 0)),
            fee_cents=int(doc.get("fee_cents", 0)),
            currency=doc.get("currency", "mxn"),
            status=doc.get("status", "pending"),
            payment_intent_id=doc.get("payment_intent_id", ""),
            refunded_cents=int(doc.get("refunded_cents", 0)),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )

    def _connect_to_entity(self, doc: dict) -> ConnectAccount:
        return ConnectAccount(
            owner_id=doc["owner_id"],
            account_id=doc["account_id"],
            charges_enabled=bool(doc.get("charges_enabled", False)),
            payouts_enabled=bool(doc.get("payouts_enabled", False)),
            requirements_due=doc.get("requirements_due") or [],
            disabled_reason=doc.get("disabled_reason"),
        )
