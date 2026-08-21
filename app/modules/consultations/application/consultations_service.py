from ..domain.entities import Consultation
from ..domain.repositories import ConsultationsRepository


class ConsultationsService:
    def __init__(self, repository: ConsultationsRepository):
        self._repository = repository

    async def start(
        self, owner_id: str, *, patient_id: str, appointment_id: str | None
    ) -> Consultation:
        """Resumes the patient's open draft if one exists, otherwise starts a
        new one — the client never has to know which case it is."""
        existing = await self._repository.find_open_draft(owner_id, patient_id)
        if existing is not None:
            if appointment_id and not existing.appointment_id:
                updated = await self._repository.update_for_owner(
                    owner_id, existing.id, {"appointment_id": appointment_id}
                )
                if updated is not None:
                    return updated
            return existing
        return await self._repository.create_draft(
            owner_id, patient_id=patient_id, appointment_id=appointment_id
        )

    async def get_consultation(self, owner_id: str, consultation_id: str) -> Consultation:
        consultation = await self._repository.get_for_owner(owner_id, consultation_id)
        if consultation is None:
            raise LookupError("Consultation not found")
        return consultation

    async def update_consultation(
        self,
        owner_id: str,
        consultation_id: str,
        *,
        visit_type: str | None,
        current_step: int | None,
    ) -> Consultation:
        updates: dict = {}
        if visit_type is not None:
            updates["visit_type"] = visit_type
        if current_step is not None:
            updates["current_step"] = current_step
        if not updates:
            raise ValueError("No fields to update")

        updated = await self._repository.update_for_owner(owner_id, consultation_id, updates)
        if updated is None:
            raise LookupError("Consultation not found")
        return updated

    async def update_evaluation(
        self,
        owner_id: str,
        consultation_id: str,
        *,
        weight_kg: float | None,
        height_cm: float | None,
        body_fat_pct: float | None,
        waist_cm: float | None,
        hip_cm: float | None,
        arm_cm: float | None,
        notes: str | None,
    ) -> Consultation:
        updates = {
            key: value
            for key, value in {
                "weight_kg": weight_kg,
                "height_cm": height_cm,
                "body_fat_pct": body_fat_pct,
                "waist_cm": waist_cm,
                "hip_cm": hip_cm,
                "arm_cm": arm_cm,
                "notes": notes,
            }.items()
            if value is not None
        }
        if not updates:
            raise ValueError("No fields to update")

        updated = await self._repository.update_evaluation_for_owner(
            owner_id, consultation_id, updates
        )
        if updated is None:
            raise LookupError("Consultation not found")
        return updated

    async def update_requirement(
        self,
        owner_id: str,
        consultation_id: str,
        *,
        wrist_cm: float | None,
        activity_factor: float | None,
        calorie_adjustment: float | None,
    ) -> Consultation:
        updates = {
            key: value
            for key, value in {
                "wrist_cm": wrist_cm,
                "activity_factor": activity_factor,
                "calorie_adjustment": calorie_adjustment,
            }.items()
            if value is not None
        }
        if not updates:
            raise ValueError("No fields to update")

        updated = await self._repository.update_requirement_for_owner(
            owner_id, consultation_id, updates
        )
        if updated is None:
            raise LookupError("Consultation not found")
        return updated

    async def update_distribution(
        self,
        owner_id: str,
        consultation_id: str,
        *,
        target_kcal: float | None,
        carbs_pct: float | None,
        protein_pct: float | None,
        fat_pct: float | None,
    ) -> Consultation:
        updates = {
            key: value
            for key, value in {
                "target_kcal": target_kcal,
                "carbs_pct": carbs_pct,
                "protein_pct": protein_pct,
                "fat_pct": fat_pct,
            }.items()
            if value is not None
        }
        if not updates:
            raise ValueError("No fields to update")

        updated = await self._repository.update_distribution_for_owner(
            owner_id, consultation_id, updates
        )
        if updated is None:
            raise LookupError("Consultation not found")
        return updated

    async def update_menu(
        self,
        owner_id: str,
        consultation_id: str,
        *,
        allocations: list[dict],
    ) -> Consultation:
        updated = await self._repository.update_menu_for_owner(
            owner_id, consultation_id, allocations
        )
        if updated is None:
            raise LookupError("Consultation not found")
        return updated

    async def update_close(
        self,
        owner_id: str,
        consultation_id: str,
        *,
        private_notes: str | None,
        next_appointment_id: str | None,
    ) -> Consultation:
        updates = {
            key: value
            for key, value in {
                "private_notes": private_notes,
                "next_appointment_id": next_appointment_id,
            }.items()
            if value is not None
        }
        if not updates:
            raise ValueError("No fields to update")

        updated = await self._repository.update_close_for_owner(
            owner_id, consultation_id, updates
        )
        if updated is None:
            raise LookupError("Consultation not found")
        return updated

    async def complete(self, owner_id: str, consultation_id: str) -> Consultation:
        current = await self._repository.get_for_owner(owner_id, consultation_id)
        if current is None:
            raise LookupError("Consultation not found")
        if current.status == "completed":
            raise ValueError("Consultation already completed")

        updated = await self._repository.complete_for_owner(owner_id, consultation_id)
        if updated is None:
            raise LookupError("Consultation not found")
        return updated

    async def reopen(self, owner_id: str, consultation_id: str) -> Consultation:
        current = await self._repository.get_for_owner(owner_id, consultation_id)
        if current is None:
            raise LookupError("Consultation not found")
        if current.status != "completed":
            raise ValueError("Consultation is not completed")

        updated = await self._repository.reopen_for_owner(owner_id, consultation_id)
        if updated is None:
            raise LookupError("Consultation not found")
        return updated
