from ..domain.entities import Patient
from ..domain.repositories import PatientQuotaChecker, PatientsRepository


class PatientsService:
    def __init__(self, repository: PatientsRepository, quota_checker: PatientQuotaChecker | None = None):
        self._repository = repository
        self._quota_checker = quota_checker

    async def list_patients(
        self,
        owner_id: str,
        *,
        page: int,
        limit: int,
        query: str | None = None,
        include_archived: bool = False,
    ) -> tuple[list[Patient], int]:
        return await self._repository.list_for_owner(
            owner_id,
            page=page,
            limit=limit,
            query=query,
            include_archived=include_archived,
        )

    async def create_patient(self, owner_id: str, payload: dict) -> Patient:
        if self._quota_checker is not None:
            await self._quota_checker.check(owner_id)
        return await self._repository.create_for_owner(owner_id, payload)

    async def get_patient(self, owner_id: str, patient_id: str) -> Patient:
        patient = await self._repository.get_for_owner(owner_id, patient_id)
        if patient is None:
            raise LookupError("Patient not found")
        return patient

    async def update_patient(self, owner_id: str, patient_id: str, payload: dict) -> Patient:
        if not payload:
            raise ValueError("No fields to update")
        patient = await self._repository.update_for_owner(owner_id, patient_id, payload)
        if patient is None:
            raise LookupError("Patient not found")
        return patient

    async def archive_patient(self, owner_id: str, patient_id: str) -> Patient:
        patient = await self._repository.archive_for_owner(owner_id, patient_id)
        if patient is None:
            raise LookupError("Patient not found")
        return patient

    async def unarchive_patient(self, owner_id: str, patient_id: str) -> Patient:
        patient = await self._repository.unarchive_for_owner(owner_id, patient_id)
        if patient is None:
            raise LookupError("Patient not found")
        return patient

    async def add_body_composition(self, owner_id: str, patient_id: str, payload: dict) -> dict:
        created = await self._repository.add_body_composition(owner_id, patient_id, payload)
        if created is None:
            raise LookupError("Patient not found")
        return created

    async def list_body_compositions(self, owner_id: str, patient_id: str) -> list[dict]:
        items = await self._repository.list_body_compositions(owner_id, patient_id)
        if items is None:
            raise LookupError("Patient not found")
        return items

    async def list_food_diary_entries(self, owner_id: str, patient_id: str) -> list[dict]:
        items = await self._repository.list_food_diary_entries(owner_id, patient_id)
        if items is None:
            raise LookupError("Patient not found")
        return items

    async def list_plan_assignments(self, owner_id: str, patient_id: str) -> list[dict]:
        items = await self._repository.list_plan_assignments(owner_id, patient_id)
        if items is None:
            raise LookupError("Patient not found")
        return items

    async def list_measurements(self, owner_id: str, patient_id: str) -> list[dict]:
        items = await self._repository.list_measurements(owner_id, patient_id)
        if items is None:
            raise LookupError("Patient not found")
        return items

    async def list_checkin_responses(self, owner_id: str, patient_id: str) -> list[dict]:
        items = await self._repository.list_checkin_responses(owner_id, patient_id)
        if items is None:
            raise LookupError("Patient not found")
        return items

    async def list_workout_plan_assignments(self, owner_id: str, patient_id: str) -> list[dict]:
        items = await self._repository.list_workout_plan_assignments(owner_id, patient_id)
        if items is None:
            raise LookupError("Patient not found")
        return items

    async def list_workout_logs(self, owner_id: str, patient_id: str) -> list[dict]:
        items = await self._repository.list_workout_logs(owner_id, patient_id)
        if items is None:
            raise LookupError("Patient not found")
        return items

    async def toggle_workout_log(self, owner_id: str, patient_id: str, payload: dict) -> dict:
        workout_plan_id = payload.get("workout_plan_id")
        if not workout_plan_id:
            raise ValueError("workout_plan_id is required")
        day_index = payload.get("day_index")
        exercise_index = payload.get("exercise_index")
        if day_index is None or exercise_index is None:
            raise ValueError("day_index and exercise_index are required")
        result = await self._repository.toggle_coach_workout_log(
            owner_id,
            patient_id,
            workout_plan_id=workout_plan_id,
            day_index=day_index,
            exercise_index=exercise_index,
        )
        if result is None:
            raise LookupError("Patient not found")
        return result

    async def create_invite_code(self, owner_id: str, patient_id: str | None = None) -> dict:
        if patient_id is not None:
            patient = await self._repository.get_for_owner(owner_id, patient_id)
            if patient is None:
                raise LookupError("Patient not found")
            if patient.user_id is not None:
                raise ValueError("Patient already has a linked account")
        return await self._repository.create_invite_code(owner_id, patient_id=patient_id)

    async def get_dashboard(self, owner_id: str) -> dict:
        return await self._repository.get_dashboard(owner_id)

    async def claim_patient(self, owner_id: str, code: str) -> Patient:
        if self._quota_checker is not None:
            await self._quota_checker.check(owner_id)
        patient = await self._repository.claim_patient(owner_id, code)
        if patient is None:
            raise LookupError("Invalid or already-claimed connection code")
        return patient
