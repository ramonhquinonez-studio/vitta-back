from ..domain.repositories import WorkoutPlansRepository


class WorkoutPlansService:
    def __init__(self, repository: WorkoutPlansRepository):
        self._repository = repository

    async def create_plan(self, owner_id: str, payload: dict) -> dict:
        self._validate_payload(payload)
        return await self._repository.create_for_owner(owner_id, payload)

    async def list_plans(self, owner_id: str) -> list[dict]:
        return await self._repository.list_for_owner(owner_id)

    async def get_plan(self, owner_id: str, plan_id: str) -> dict:
        plan = await self._repository.get_for_owner(owner_id, plan_id)
        if plan is None:
            raise LookupError("Workout plan not found")
        return plan

    async def update_plan(self, owner_id: str, plan_id: str, payload: dict) -> dict:
        if not payload:
            raise ValueError("No fields to update")
        self._validate_payload(payload)
        updated = await self._repository.update_for_owner(owner_id, plan_id, payload)
        if updated is None:
            raise LookupError("Workout plan not found")
        return updated

    async def delete_plan(self, owner_id: str, plan_id: str) -> None:
        deleted = await self._repository.delete_for_owner(owner_id, plan_id)
        if not deleted:
            raise LookupError("Workout plan not found")

    async def assign_plan(self, owner_id: str, plan_id: str, patient_id: str | None) -> dict:
        if not patient_id:
            raise ValueError("patient_id is required")
        await self.get_plan(owner_id, plan_id)
        if not await self._repository.patient_exists_for_owner(owner_id, patient_id):
            raise LookupError("Patient not found")
        await self._repository.assign_plan(owner_id, plan_id, patient_id)
        return {"ok": True}

    def _validate_payload(self, payload: dict) -> None:
        if not payload.get("name"):
            raise ValueError("name is required")
        days = payload.get("days") or []
        if not days:
            raise ValueError("At least one day is required")
        seen_weekdays: set[int] = set()
        for day in days:
            for exercise in day.get("exercises") or []:
                if not exercise.get("name"):
                    raise ValueError("Every exercise needs a name")
            for weekday in day.get("weekdays") or []:
                if weekday in seen_weekdays:
                    raise ValueError(
                        f"weekday {weekday} is assigned to more than one day"
                    )
                seen_weekdays.add(weekday)
