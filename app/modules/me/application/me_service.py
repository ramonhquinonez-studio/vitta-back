from datetime import UTC, date, datetime, timedelta
from typing import Any

from ..domain.repositories import MeRepository
from .availability import AvailabilityConfig, generate_days
from app.modules.booking_policy.application.enforcement import (
    BY_PATIENT,
    REFUND,
    evaluate_cancellation,
    evaluate_reschedule,
)


def _booking_timezone() -> str:
    try:
        from app.core.config import settings

        return settings.BOOKING_TIMEZONE
    except Exception:  # pragma: no cover - config always importable in practice
        return "America/Mexico_City"


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
    def __init__(
        self,
        repository: MeRepository,
        booking_policy_service=None,
        booking_payments_service=None,
    ):
        self._repository = repository
        # Optional so existing MeService(repo) call sites / tests keep working
        # (same pattern as the optional repos wired in spec 076).
        self._booking_policy_service = booking_policy_service
        # Executes the deposit refund on a within-policy cancellation
        # (spec 080 Phase 3). Optional — when absent the outcome is still
        # recorded on the appointment, the money just isn't moved yet.
        self._booking_payments_service = booking_payments_service

    async def _resolve_booking_policy(self, owner_id: str | None) -> dict | None:
        if not owner_id or self._booking_policy_service is None:
            return None
        profile = await self._repository.get_nutritionist_profile(owner_id)
        price = (profile or {}).get("session_price")
        currency = (profile or {}).get("session_price_currency") or "MXN"
        return await self._booking_policy_service.resolve_for_owner(
            owner_id, session_price=price, currency=currency
        )

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

        # Booking-protection policy (spec 080). When the nutritionist's policy
        # requires a deposit/prepay or manual approval, the patient must have
        # accepted it; we snapshot the resolved terms onto the appointment as
        # an immutable consent record.
        policy_snapshot = None
        policy_accepted_at = None
        resolved_policy = await self._resolve_booking_policy(owner_id)
        if resolved_policy and resolved_policy.get("needs_consent"):
            if payload.get("policy_accepted") is not True:
                raise ValueError(
                    "Debes aceptar la política de reserva del nutriólogo para agendar."
                )
            policy_snapshot = resolved_policy
            policy_accepted_at = datetime.now(UTC)

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
            policy_snapshot=policy_snapshot,
            policy_accepted_at=policy_accepted_at,
        )

    async def get_availability(
        self, user_id: str, *, from_date: date | None = None, days: int = 21
    ) -> dict:
        """Open booking slots for the patient's assigned nutritionist (spec
        086), from the nutritionist's configured window minus their live
        appointments."""
        patient = await self._require_patient(user_id)
        owner_id = patient.get("owner_id")
        if not owner_id:
            raise ValueError("Patient has no owner assigned")

        now_utc = datetime.now(UTC).replace(tzinfo=None)
        from_date = from_date or now_utc.date()
        days = max(1, min(int(days), 60))

        profile = await self._repository.get_nutritionist_profile(owner_id)
        config = AvailabilityConfig.from_profile(profile)

        # Widen the appointment window by a day either side so a local-time slot
        # near midnight still sees an appointment stored in UTC.
        window_start = datetime.combine(from_date, datetime.min.time()) - timedelta(days=1)
        window_end = window_start + timedelta(days=days + 2)
        busy = await self._repository.list_owner_appointments_between(
            owner_id, start=window_start, end=window_end
        )

        day_slots = generate_days(
            config,
            from_date=from_date,
            day_count=days,
            busy=busy,
            now_utc=now_utc,
            tz_name=_booking_timezone(),
        )
        return {
            "slot_minutes": config.slot_minutes,
            "modality": config.modality,
            "days": day_slots,
        }

    async def get_appointment_detail(self, user_id: str, appointment_id: str) -> dict:
        patient = await self._require_patient(user_id)
        appointment = await self._repository.get_patient_appointment(patient["id"], appointment_id)
        if appointment is None:
            raise LookupError("Appointment not found")
        return appointment

    def _cancellation_outcome(self, appointment: dict, *, by: str) -> dict:
        start = appointment.get("start")
        return evaluate_cancellation(
            appointment.get("policy_snapshot"),
            start=start if isinstance(start, datetime) else datetime.now(UTC),
            now=datetime.now(UTC),
            by=by,
        )

    async def get_cancellation_preview(self, user_id: str, appointment_id: str) -> dict:
        """What cancelling now would cost the patient (spec 080 Phase 3) —
        `{outcome, refund_cents, reason}`."""
        patient = await self._require_patient(user_id)
        appointment = await self._repository.get_patient_appointment(
            patient["id"], appointment_id
        )
        if appointment is None:
            raise LookupError("Appointment not found")
        outcome = self._cancellation_outcome(appointment, by=BY_PATIENT)
        return {
            "outcome": outcome["outcome"],
            "refund_cents": outcome["refund_cents"],
            "reason": outcome["reason"],
        }

    async def cancel_appointment(self, user_id: str, appointment_id: str) -> dict:
        patient = await self._require_patient(user_id)
        appointment = await self._repository.get_patient_appointment(patient["id"], appointment_id)
        if appointment is None:
            raise LookupError("Appointment not found")
        if appointment.get("status") in ("canceled", "no_show"):
            return appointment

        outcome = self._cancellation_outcome(appointment, by=BY_PATIENT)
        refunded_cents = 0
        if (
            outcome["outcome"] == REFUND
            and outcome["refund_cents"] > 0
            and self._booking_payments_service is not None
            and appointment.get("payment_id")
        ):
            await self._booking_payments_service.refund(appointment["payment_id"])
            refunded_cents = outcome["refund_cents"]

        updated = await self._repository.update_patient_appointment(
            patient["id"],
            appointment_id,
            {
                "status": outcome["status"],
                "cancellation_outcome": outcome["outcome"],
                "refunded_cents": refunded_cents,
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
        if appointment.get("status") in ("canceled", "no_show"):
            raise ValueError("Canceled appointments cannot be rescheduled")

        # Policy limits (spec 080 Phase 3) — count + minimum notice.
        rule = evaluate_reschedule(
            appointment.get("policy_snapshot"),
            start=appointment.get("start") or datetime.now(UTC),
            now=datetime.now(UTC),
            reschedule_count=int(appointment.get("reschedule_count") or 0),
            by=BY_PATIENT,
        )
        if not rule["allowed"]:
            raise PermissionError(rule["reason"])

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
                "reschedule_count": int(appointment.get("reschedule_count") or 0) + 1,
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
        if patient.get("progress_log_enabled", True) is False:
            raise PermissionError(
                "Tu nutriólogo desactivó el registro de progreso."
            )
        return await self._repository.create_measurement(
            owner_id=patient.get("owner_id"),
            patient_id=patient["id"],
            payload=payload,
        )

    async def add_body_measurements(self, user_id: str, payload: dict[str, Any]) -> dict:
        """Circumference set from the patient's interactive body figure
        (spec 084) — a `measurements` doc with no photo. Same self-log gate
        as `add_measurement` (spec 083)."""
        patient = await self._require_patient(user_id)
        if patient.get("progress_log_enabled", True) is False:
            raise PermissionError(
                "Tu nutriólogo desactivó el registro de progreso."
            )
        if not payload.get("circumferences") and payload.get("waist_cm") is None:
            raise ValueError("Registra al menos una medida.")
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
        owner_id = patient.get("owner_id")
        profile = await self._repository.get_nutritionist_profile(owner_id)
        if profile is not None:
            resolved = await self._resolve_booking_policy(owner_id)
            if resolved is not None:
                profile = {**profile, "booking_policy": resolved}
        return profile

    async def get_booking_policy(self, user_id: str) -> dict | None:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return None
        return await self._resolve_booking_policy(patient.get("owner_id"))

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
        return await self._repository.list_recommendations(
            patient.get("owner_id"), patient["id"], kind=kind
        )

    async def get_hydration(self, user_id: str) -> dict[str, Any]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return {"current_ml": 0, "target_ml": 2000}
        return await self._repository.get_hydration_today(patient["id"])

    async def add_hydration(self, user_id: str, delta_ml: int) -> dict[str, Any]:
        patient = await self._require_patient(user_id)
        return await self._repository.add_hydration(
            patient["id"], patient.get("owner_id"), delta_ml=delta_ml
        )

    async def list_messages(self, user_id: str, *, since: datetime | None = None) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_messages(patient.get("owner_id"), patient["id"], since=since)

    async def get_my_patient_record(self, user_id: str) -> dict | None:
        """Exposed so the router can look up the owner/patient ids it needs
        to push-notify the nutritionist after a successful send, without
        reaching into the service's repository directly."""
        return await self._repository.get_patient_for_user(user_id)

    async def send_message(
        self,
        user_id: str,
        text: str,
        *,
        attachment_url: str | None = None,
        attachment_type: str | None = None,
    ) -> dict:
        text = (text or "").strip()
        if not text and not attachment_url:
            raise ValueError("text or attachment_url is required")
        patient = await self._require_patient(user_id)
        if not patient.get("owner_id"):
            raise LookupError("No tienes un nutriólogo asignado todavía")
        return await self._repository.create_message(
            patient.get("owner_id"),
            patient["id"],
            text=text,
            attachment_url=attachment_url,
            attachment_type=attachment_type,
        )

    async def list_checkin_templates(self, user_id: str) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient or not patient.get("owner_id"):
            return []
        return await self._repository.list_checkin_templates(patient["owner_id"])

    async def submit_checkin_response(self, user_id: str, payload: dict) -> dict:
        patient = await self._require_patient(user_id)
        owner_id = patient.get("owner_id")
        if not owner_id:
            raise LookupError("No tienes un nutriólogo asignado todavía")
        template_id = payload.get("template_id")
        if not template_id:
            raise ValueError("template_id is required")
        template = await self._repository.get_checkin_template(owner_id, template_id)
        if template is None:
            raise LookupError("Template not found")
        answers = payload.get("answers") or []
        self._validate_checkin_answers(template, answers)
        return await self._repository.create_checkin_response(
            owner_id=owner_id,
            patient_id=patient["id"],
            template_id=template_id,
            appointment_id=payload.get("appointment_id"),
            answers=answers,
        )

    async def list_checkin_responses(self, user_id: str) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_checkin_responses(patient["id"])

    def _validate_checkin_answers(self, template: dict, answers: list[dict]) -> None:
        answered_field_ids = {a.get("field_id") for a in answers if a.get("values")}
        for field in template.get("fields", []):
            if field.get("required") and field.get("id") not in answered_field_ids:
                raise ValueError(f"Missing required field: {field.get('label')}")

    async def get_active_workout_plan(self, user_id: str) -> dict | None:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return None
        return await self._repository.get_active_workout_plan(patient["id"])

    async def list_workout_logs(self, user_id: str, *, workout_plan_id: str | None = None) -> list[dict]:
        patient = await self._repository.get_patient_for_user(user_id)
        if not patient:
            return []
        return await self._repository.list_workout_logs(
            patient["id"], workout_plan_id=workout_plan_id
        )

    async def upsert_workout_log(self, user_id: str, payload) -> dict:
        patient = await self._require_patient(user_id)
        owner_id = patient.get("owner_id")
        if not owner_id:
            raise LookupError("No tienes un nutriólogo asignado todavía")
        return await self._repository.upsert_workout_log(
            owner_id=owner_id,
            patient_id=patient["id"],
            workout_plan_id=payload.workout_plan_id,
            day_index=payload.day_index,
            exercise_index=payload.exercise_index,
            sets=[s.model_dump() for s in payload.sets],
            comment=payload.comment,
            photo_url=payload.photo_url,
            photo_content_type=payload.photo_content_type,
        )

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
