from ..domain.entities import Consultation
from ..domain.repositories import ConsultationsRepository


class ConsultationsService:
    def __init__(
        self,
        repository: ConsultationsRepository,
        appointments_repository=None,
        patients_repository=None,
    ):
        self._repository = repository
        # Optional: keeps the linked appointment's status in sync with the
        # consultation's own status. None in contexts (tests) that don't
        # care about that side effect.
        self._appointments_repository = appointments_repository
        # Optional: used only by list_consultations to attach each row's
        # patient name for list UIs (dashboard "Consultas en progreso").
        self._patients_repository = patients_repository

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

    async def list_consultations(
        self,
        owner_id: str,
        *,
        status: str | None = None,
        patient_id: str | None = None,
    ) -> list[tuple[Consultation, str | None]]:
        """Returns (consultation, patient_name) pairs — the name is resolved
        here (when a patients repository is available) so list UIs don't have
        to fan out one lookup per row."""
        consultations = await self._repository.list_for_owner(
            owner_id, status=status, patient_id=patient_id
        )
        names: dict[str, str | None] = {}
        if self._patients_repository is not None:
            for consultation in consultations:
                if consultation.patient_id in names:
                    continue
                try:
                    patient = await self._patients_repository.get_for_owner(
                        owner_id, consultation.patient_id
                    )
                except Exception:
                    patient = None
                names[consultation.patient_id] = getattr(patient, "name", None)
        return [(c, names.get(c.patient_id)) for c in consultations]

    async def delete(self, owner_id: str, consultation_id: str) -> None:
        current = await self._repository.get_for_owner(owner_id, consultation_id)
        if current is None:
            raise LookupError("Consultation not found")
        if current.status != "draft":
            raise ValueError("Only a draft consultation can be discarded")
        deleted = await self._repository.delete_for_owner(owner_id, consultation_id)
        if not deleted:
            raise LookupError("Consultation not found")

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
        plan_id: str | None = None,
        next_appointment_id: str | None,
    ) -> Consultation:
        updates = {
            key: value
            for key, value in {
                "private_notes": private_notes,
                "plan_id": plan_id,
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
        await self._sync_appointment_status(owner_id, updated.appointment_id, "completed")
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
        await self._sync_appointment_status(owner_id, updated.appointment_id, "confirmed")
        return updated

    async def _sync_appointment_status(
        self, owner_id: str, appointment_id: str | None, status: str
    ) -> None:
        if not appointment_id or self._appointments_repository is None:
            return
        try:
            await self._appointments_repository.update_for_owner(
                owner_id, appointment_id, {"status": status}
            )
        except Exception:
            # Mirrors the Google Calendar sync posture elsewhere: never let a
            # side-effect update block the consultation's own status change.
            pass
