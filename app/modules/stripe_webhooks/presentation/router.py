from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.db.mongo import get_db
from app.modules.payments.infrastructure.stripe_client import get_stripe

from ..application.webhook_dispatcher import WebhookDispatcher
from ..infrastructure.mongo_webhook_events_repository import MongoWebhookEventsRepository

router = APIRouter(prefix="/stripe", tags=["stripe_webhooks"])


def get_dispatcher(db: AsyncIOMotorDatabase = Depends(get_db)) -> WebhookDispatcher:
    return WebhookDispatcher(
        get_stripe(),
        settings.STRIPE_WEBHOOK_SECRET,
        MongoWebhookEventsRepository(db),
    )


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    dispatcher: WebhookDispatcher = Depends(get_dispatcher),
):
    payload = await request.body()
    event = dispatcher.verify(payload=payload, signature=stripe_signature)
    return await dispatcher.dispatch(event)
