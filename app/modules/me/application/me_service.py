from datetime import UTC, datetime, timedelta
from typing import Any

from ..domain.repositories import MeRepository


def parse_range(value: str | None) -> timedelta:
    if not value:
        return timedelta(days=30)
    try:
        unit = value[-1].lower()
        number = int(value[:-1])
        if unit == "d":
            return timedelta(days=number)
        if unit == "w":
            return timedelta(weeks=number)
        if unit == "m":
            return timedelta(days=30 * number)
        return timedelta(days=int(value))
    except Exception:
        return timedelta(days=30)


class MeService:
    def __init__(self, repository: MeRepository):
        self._repository = repository

    async def get_profile(self, user_id: str) -> dict[str, Any]:
        user = await self._repository.get_user(user_id)
        patient = await self._repository.get_patient_for_user(user_id)
        return {
            "user": {
                "id": user_id,
                "email": (user or {}).get("email"),
                "name": (user or {}).get("name"),
            },
            "patient": patient,
        }

    async def update_profile(self, user_id: str, payload: dict[str, Any]) -> dict:
        if not payload:
            raise ValueError("No fields to update")
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            raise LookupError("Patient not found")
        updated = await self._repository.update_patient_profile(patient["id"], payload)
        if updated is None:
            raise LookupError("Patient not found")
        return updated

    async def list_appointments(
        self,
        user_id: str,
        *,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_appointments(
            patient["id"],
            from_dt=from_dt,
            to_dt=to_dt,
        )

    async def list_consultations(self, user_id: str) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        appointments = await self._repository.list_appointments(patient["id"])

        consultations = []
        for appointment in appointments:
            plan = None
            plan_id = appointment.get("plan_id")
            if plan_id:
                plan = await self._repository.get_plan_summary(plan_id)

            body_composition = None
            body_composition_id = appointment.get("body_composition_id")
            if body_composition_id:
                body_composition = await self._repository.get_body_composition_by_id(
                    body_composition_id
                )

            consultations.append(
                {**appointment, "plan": plan, "body_composition": body_composition}
            )

        consultations.sort(
            key=lambda item: item.get("start") or datetime.min,
            reverse=True,
        )
        return consultations

    async def get_active_plan(self, user_id: str) -> dict | None:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return None
        return await self._repository.get_active_plan(patient["id"])

    async def request_appointment(self, user_id: str, payload: dict[str, Any]) -> dict:
        patient = await self._require_patient(user_id)
        owner_id = patient.get("owner_id")
        if not owner_id:
            raise ValueError("Patient has no owner assigned")

        start = self._parse_datetime(payload.get("start"), required=True, field_name="start")
        end = self._parse_datetime(payload.get("end"), required=False, field_name="end")
        end = end or (start + timedelta(minutes=45))
        mode = payload.get("mode") or "online"
        note = payload.get("note")

        overlap = await self._repository.find_owner_overlap(
            owner_id,
            start=start,
            end=end,
        )
        if overlap:
            raise RuntimeError(
                {
                    "code": "OVERLAP",
                    "message": "Ya existe una cita en ese horario.",
                    "conflict_id": overlap.get("id"),
                    "conflict_start": overlap.get("start"),
                    "conflict_end": overlap.get("end"),
                }
            )

        return await self._repository.create_patient_appointment(
            owner_id=owner_id,
            patient_id=patient["id"],
            start=start,
            end=end,
            mode=mode,
            note=note,
        )

    async def get_appointment_detail(self, user_id: str, appointment_id: str) -> dict:
        patient = await self._require_patient(user_id)
        appointment = await self._repository.get_patient_appointment(patient["id"], appointment_id)
        if appointment is None:
            raise LookupError("Appointment not found")
        return appointment

    async def cancel_appointment(self, user_id: str, appointment_id: str) -> dict:
        patient = await self._require_patient(user_id)
        appointment = await self._repository.get_patient_appointment(patient["id"], appointment_id)
        if appointment is None:
            raise LookupError("Appointment not found")
        if appointment.get("status") == "canceled":
            return appointment
        updated = await self._repository.update_patient_appointment(
            patient["id"],
            appointment_id,
            {
                "status": "canceled",
                "updated_at": datetime.now(UTC),
            },
        )
        if updated is None:
            raise LookupError("Appointment not found")
        return updated

    async def reschedule_appointment(self, user_id: str, appointment_id: str, payload: dict[str, Any]) -> dict:
        patient = await self._require_patient(user_id)
        appointment = await self._repository.get_patient_appointment(patient["id"], appointment_id)
        if appointment is None:
            raise LookupError("Appointment not found")
        if appointment.get("status") == "canceled":
            raise ValueError("Canceled appointments cannot be rescheduled")

        start = self._parse_datetime(payload.get("start"), required=True, field_name="start")
        end = self._parse_datetime(payload.get("end"), required=False, field_name="end")
        if end is None:
            previous_start = appointment.get("start")
            previous_end = appointment.get("end")
            default_duration = (
                previous_end - previous_start
                if previous_start is not None and previous_end is not None
                else timedelta(minutes=45)
            )
            end = start + default_duration

        overlap = await self._repository.find_owner_overlap(
            appointment.get("owner_id"),
            start=start,
            end=end,
            exclude_appointment_id=appointment_id,
        )
        if overlap:
            raise RuntimeError(
                {
                    "code": "OVERLAP",
                    "message": "Ya existe una cita en ese horario.",
                    "conflict_id": overlap.get("id"),
                    "conflict_start": overlap.get("start"),
                    "conflict_end": overlap.get("end"),
                }
            )

        new_status = "pending" if appointment.get("status") == "confirmed" else appointment.get("status") or "pending"
        updated = await self._repository.update_patient_appointment(
            patient["id"],
            appointment_id,
            {
                "start": start,
                "end": end,
                "status": new_status,
                "note": payload.get("note") or appointment.get("note"),
                "updated_at": datetime.now(UTC),
            },
        )
        if updated is None:
            raise LookupError("Appointment not found")
        return updated

    async def list_measurements(self, user_id: str, *, limit: int) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_measurements(patient["id"], limit=max(1, min(limit, 365)))

    async def add_measurement(self, user_id: str, payload: dict[str, Any]) -> dict:
        patient = await self._require_patient(user_id)
        return await self._repository.create_measurement(
            owner_id=patient.get("owner_id"),
            patient_id=patient["id"],
            payload=payload,
        )

    async def get_progress(self, user_id: str, range_value: str | None) -> dict[str, Any]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return {"series": [], "latest": None, "delta": {}}

        since = datetime.now(UTC) - parse_range(range_value)
        series = await self._repository.list_measurements_since(patient["id"], since=since)
        latest = series[-1] if series else None
        first = series[0] if series else None
        delta: dict[str, Any] = {}
        if latest and first:
            try:
                if latest.get("weight_kg") is not None and first.get("weight_kg") is not None:
                    delta["weight_kg"] = float(latest["weight_kg"]) - float(first["weight_kg"])
                if latest.get("body_fat_pct") is not None and first.get("body_fat_pct") is not None:
                    delta["body_fat_pct"] = float(latest["body_fat_pct"]) - float(first["body_fat_pct"])
            except Exception:
                pass
        return {"series": series, "latest": latest, "delta": delta}

    async def list_prescriptions(self, user_id: str, *, limit: int) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_prescriptions(patient["id"], limit=max(1, min(limit, 50)))

    async def list_recipe_collections(self, user_id: str) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_recipe_collections(patient.get("owner_id"))

    async def list_education_videos(self, user_id: str) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_education_videos(patient.get("owner_id"))

    async def list_articles(self, user_id: str) -> list[dict]:
        # Unlike recipe_collections/education_videos, platform-curated
        # articles (owner_id None) should still show even for a patient
        # with no assigned nutritionist — so no early return on `not patient`.
        patient = await self._repository.get_patient_for_user(user_id)
        owner_id = patient.get("owner_id") if patient else None
        return await self._repository.list_articles(owner_id)

    async def get_nutritionist_profile(self, user_id: str) -> dict | None:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return None
        return await self._repository.get_nutritionist_profile(patient.get("owner_id"))

    async def get_clinical_history(self, user_id: str) -> dict[str, Any]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return {"notes": [], "body_compositions": []}
        notes = await self._repository.list_clinical_notes(patient["id"])
        body_compositions = await self._repository.list_body_compositions(patient["id"])
        return {"notes": notes, "body_compositions": body_compositions}

    async def list_body_compositions(self, user_id: str) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_body_compositions(patient["id"])

    async def get_recipe(self, user_id: str, recipe_id: str) -> dict:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            raise LookupError("Recipe not found")
        recipe = await self._repository.get_recipe_for_owner(patient.get("owner_id"), recipe_id)
        if recipe is None:
            raise LookupError("Recipe not found")
        return recipe

    async def list_food_diary_entries(self, user_id: str, *, limit: int) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_food_diary_entries(
            patient["id"], limit=max(1, min(limit, 365))
        )

    async def add_food_diary_entry(self, user_id: str, payload: dict[str, Any]) -> dict:
        if not payload.get("dish"):
            raise ValueError("dish is required")
        patient = await self._require_patient(user_id)
        return await self._repository.create_food_diary_entry(
            owner_id=patient.get("owner_id"),
            patient_id=patient["id"],
            payload=payload,
        )

    async def list_recommendations(self, user_id: str, *, kind: str | None = None) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_recommendations(patient.get("owner_id"), kind=kind)

    async def get_hydration(self, user_id: str) -> dict[str, Any]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return {"current_ml": 0, "target_ml": 2000}
        return await self._repository.get_hydration_today(patient["id"])

    async def add_hydration(self, user_id: str, delta_ml: int) -> dict[str, Any]:
        patient = await self._require_patient(user_id)
        return await self._repository.add_hydration(patient["id"], delta_ml=delta_ml)

    async def _require_patient(self, user_id: str) -> dict:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            raise LookupError("Patient not found")
        return patient

    def _parse_datetime(self, value: Any, *, required: bool, field_name: str) -> datetime | None:
        if value is None:
            if required:
                raise ValueError(f"{field_name} is required")
            return None
        try:
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            if isinstance(value, datetime):
                return value
        except Exception as exc:
            raise ValueError(f"Invalid {field_name} datetime") from exc
        raise ValueError(f"Invalid {field_name} datetime")
