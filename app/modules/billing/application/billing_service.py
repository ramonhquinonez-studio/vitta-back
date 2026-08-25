from ..domain.entities import Subscription, SubscriptionPlan
from ..domain.repositories import BillingProviderRepository, BillingRepository

_ENTITLED_STATUSES = {"active", "trialing"}


class BillingService:
    def __init__(self, repository: BillingRepository, provider: BillingProviderRepository):
        self._repository = repository
        self._provider = provider

    async def list_plans(self) -> list[SubscriptionPlan]:
        return await self._repository.list_plans()

    async def get_my_subscription(self, owner_id: str) -> Subscription:
        subscription = await self._repository.get_subscription_for_owner(owner_id)
        if subscription is not None:
            return subscription
        return await self.enroll_default_plan(owner_id)

    async def enroll_default_plan(self, owner_id: str) -> Subscription:
        """Every nutritionist gets a subscription from the moment they
        register — no null-plan edge case for quota checks to trip over."""
        plan = await self._repository.get_default_plan()
        if plan is None:
            raise LookupError("No default subscription plan configured")
        return await self._repository.upsert_subscription(
            Subscription(owner_id=owner_id, plan_id=plan.id, status="active")
        )

    async def start_checkout(self, owner_id: str, owner_email: str, plan_id: str) -> str:
        plan = await self._repository.get_plan(plan_id)
        if plan is None:
            raise LookupError("Plan not found")
        return await self._provider.create_checkout_session(
            owner_id=owner_id, owner_email=owner_email, plan=plan
        )

    async def open_portal(self, owner_id: str) -> str:
        subscription = await self.get_my_subscription(owner_id)
        if not subscription.provider_customer_id:
            raise ValueError("No billing account yet — start a checkout first")
        return await self._provider.create_portal_session(
            provider_customer_id=subscription.provider_customer_id
        )

    async def handle_webhook(self, *, payload: bytes, signature: str | None) -> None:
        event = self._provider.parse_webhook_event(payload=payload, signature=signature)
        owner_id = event.get("owner_id")
        customer_id = event.get("customer_id")
        subscription = None
        if owner_id:
            subscription = await self._repository.get_subscription_for_owner(owner_id)
        elif customer_id:
            subscription = await self._repository.get_subscription_for_customer(customer_id)
        if subscription is None:
            return
        status = event.get("status") or subscription.status
        await self._repository.upsert_subscription(
            Subscription(
                owner_id=subscription.owner_id,
                plan_id=subscription.plan_id,
                status=status,
                provider_customer_id=customer_id or subscription.provider_customer_id,
                provider_subscription_id=event.get("subscription_id")
                or subscription.provider_subscription_id,
                current_period_end=subscription.current_period_end,
            )
        )

    async def check_patient_quota(self, owner_id: str, *, current_patient_count: int) -> None:
        subscription = await self.get_my_subscription(owner_id)
        plan = await self._effective_plan(subscription)
        if plan is None or plan.client_limit is None:
            return
        if current_patient_count >= plan.client_limit:
            raise PermissionError(
                f"Has llegado al límite de {plan.client_limit} pacientes de tu plan actual."
            )

    async def _effective_plan(self, subscription: Subscription) -> SubscriptionPlan | None:
        """The plan whose limit actually applies right now. A lapsed
        subscription (past_due/canceled/anything not active/trialing) falls
        back to the default plan's limit rather than keeping its paid
        tier's limit forever — `plan_id` itself is left untouched by
        `handle_webhook` so the paid tier is restored automatically if the
        subscription reactivates.
        """
        if subscription.status in _ENTITLED_STATUSES:
            return await self._repository.get_plan(subscription.plan_id)
        default_plan = await self._repository.get_default_plan()
        return default_plan or await self._repository.get_plan(subscription.plan_id)
