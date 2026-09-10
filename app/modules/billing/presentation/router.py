from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.deps import get_current_user, get_db, require_role
from app.modules.payments.application.stripe_customers import StripeCustomers
from app.modules.payments.infrastructure.mongo_stripe_customers_repository import (
    MongoStripeCustomersRepository,
)
from app.modules.payments.infrastructure.stripe_client import get_stripe
from app.schemas.billing import (
    CheckoutIn,
    CheckoutSessionOut,
    SubscriptionOut,
    SubscriptionPlanOut,
    SubscriptionSheetIn,
    SubscriptionSheetOut,
    SubscriptionVerifyIn,
    SubscriptionVerifyOut,
)

from ..application.billing_service import BillingService
from ..application.stripe_subscriptions_service import StripeSubscriptionsService
from ..domain.repositories import BillingProviderRepository
from ..infrastructure.mock_billing_provider import MockBillingProvider
from ..infrastructure.mongo_billing_repository import MongoBillingRepository

router = APIRouter(prefix="/billing", tags=["billing"])


def get_billing_provider() -> BillingProviderRepository:
    if settings.BILLING_PROVIDER == "stripe":
        from ..infrastructure.stripe_billing_provider import StripeBillingProvider

        return StripeBillingProvider()
    return MockBillingProvider()


def get_billing_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> BillingService:
    return BillingService(MongoBillingRepository(db), get_billing_provider())


def get_subscriptions_service(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> StripeSubscriptionsService:
    stripe = get_stripe()
    customers = StripeCustomers(stripe, MongoStripeCustomersRepository(db))
    return StripeSubscriptionsService(MongoBillingRepository(db), stripe, customers)


def _require_native() -> None:
    if not settings.stripe_native_enabled:
        raise HTTPException(status_code=503, detail="Pagos con tarjeta no disponibles todavía.")


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


@router.get("/plans", response_model=list[SubscriptionPlanOut])
async def list_plans(service: BillingService = Depends(get_billing_service)):
    plans = await service.list_plans()
    return [
        SubscriptionPlanOut(
            id=p.id, name=p.name, client_limit=p.client_limit, is_default=p.is_default
        )
        for p in plans
    ]


@router.get("/subscription", response_model=SubscriptionOut)
async def my_subscription(
    current=Depends(require_role("nutritionist")),
    service: BillingService = Depends(get_billing_service),
):
    subscription = await service.get_my_subscription(_owner_id(current))
    return SubscriptionOut(
        plan_id=subscription.plan_id,
        status=subscription.status,
        current_period_end=subscription.current_period_end,
    )


@router.post("/checkout", response_model=CheckoutSessionOut)
async def start_checkout(
    payload: CheckoutIn,
    current=Depends(require_role("nutritionist")),
    service: BillingService = Depends(get_billing_service),
):
    try:
        url = await service.start_checkout(_owner_id(current), current["email"], payload.plan_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CheckoutSessionOut(url=url)


@router.post("/portal", response_model=CheckoutSessionOut)
async def open_portal(
    current=Depends(require_role("nutritionist")),
    service: BillingService = Depends(get_billing_service),
):
    try:
        url = await service.open_portal(_owner_id(current))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CheckoutSessionOut(url=url)


@router.post("/subscription-sheet", response_model=SubscriptionSheetOut)
async def subscription_sheet(
    payload: SubscriptionSheetIn,
    current=Depends(require_role("nutritionist")),
    service: StripeSubscriptionsService = Depends(get_subscriptions_service),
):
    """Native-card-sheet counterpart to `POST /billing/checkout`. Creates
    the Stripe Subscription `incomplete` and returns the first invoice's
    PaymentIntent client secret for the SDK to confirm."""
    _require_native()
    try:
        return await service.start_subscription_sheet(
            _owner_id(current), current.get("email"), payload.plan_id
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/subscription/verify", response_model=SubscriptionVerifyOut)
async def verify_subscription(
    payload: SubscriptionVerifyIn,
    current=Depends(require_role("nutritionist")),
    service: StripeSubscriptionsService = Depends(get_subscriptions_service),
):
    _require_native()
    try:
        return await service.verify_subscription(_owner_id(current), payload.subscription_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/webhook", deprecated=True)
async def stripe_webhook(
    request: Request,
    service: BillingService = Depends(get_billing_service),
):
    # Superseded by `POST /stripe/webhook` (the shared idempotent dispatcher,
    # spec 077). Left only for the legacy `BILLING_PROVIDER=stripe` redirect
    # provider that predates the native rails; 404 otherwise.
    if settings.BILLING_PROVIDER != "stripe":
        raise HTTPException(status_code=404, detail="Not found")
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        await service.handle_webhook(payload=payload, signature=signature)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.get("/mock-confirm", response_class=HTMLResponse)
async def mock_confirm_checkout(
    owner_id: str,
    plan_id: str,
    token: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Local-dev only stand-in for what a completed Stripe checkout would
    do: activates the chosen plan immediately. `MockBillingProvider` is the
    only thing that ever generates a URL pointing here."""
    if settings.BILLING_PROVIDER != "mock":
        raise HTTPException(status_code=404, detail="Not found")
    repo = MongoBillingRepository(db)
    from ..domain.entities import Subscription

    plan = await repo.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    await repo.upsert_subscription(
        Subscription(
            owner_id=owner_id,
            plan_id=plan_id,
            status="active",
            provider_customer_id=f"mock-{owner_id}",
        )
    )
    return f"<html><body>Suscripción activada: {plan.name}. Puedes cerrar esta ventana.</body></html>"


@router.get("/mock-portal", response_class=HTMLResponse)
async def mock_portal(customer_id: str):
    if settings.BILLING_PROVIDER != "mock":
        raise HTTPException(status_code=404, detail="Not found")
    return (
        "<html><body>Portal de facturación (simulado).<br>"
        f'<a href="/billing/mock-cancel?customer_id={customer_id}">Cancelar suscripción</a>'
        "</body></html>"
    )


@router.get("/mock-cancel", response_class=HTMLResponse)
async def mock_cancel_subscription(
    customer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Local-dev-only stand-in for a customer canceling in Stripe's real
    portal — flips status to `canceled` without touching `plan_id`, so
    `BillingService._effective_plan` falls back to the default plan's
    limit exactly as it would from a real Stripe webhook."""
    if settings.BILLING_PROVIDER != "mock":
        raise HTTPException(status_code=404, detail="Not found")
    repo = MongoBillingRepository(db)
    from ..domain.entities import Subscription

    subscription = await repo.get_subscription_for_customer(customer_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await repo.upsert_subscription(
        Subscription(
            owner_id=subscription.owner_id,
            plan_id=subscription.plan_id,
            status="canceled",
            provider_customer_id=subscription.provider_customer_id,
            provider_subscription_id=subscription.provider_subscription_id,
            current_period_end=subscription.current_period_end,
        )
    )
    return "<html><body>Suscripción cancelada. Puedes cerrar esta ventana.</body></html>"
