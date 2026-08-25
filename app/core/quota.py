from typing import Awaitable, Callable

from app.modules.billing.application.billing_service import BillingService


class PatientQuotaCheckerAdapter:
    """Concrete adapter satisfying the `PatientQuotaChecker` Protocol
    declared independently in both `patients/domain/repositories.py` and
    `auth/domain/repositories.py` — composes `BillingService` with whatever
    patient-count source the caller supplies, so neither module needs to
    import the other.
    """

    def __init__(self, billing_service: BillingService, count_patients: Callable[[str], Awaitable[int]]):
        self._billing_service = billing_service
        self._count_patients = count_patients

    async def check(self, owner_id: str) -> None:
        count = await self._count_patients(owner_id)
        await self._billing_service.check_patient_quota(owner_id, current_patient_count=count)
