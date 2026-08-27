import unittest
from datetime import UTC, datetime, timedelta

from app.modules.me.application.me_service import MeService, parse_range
from app.schemas.workout_log import WorkoutExerciseLogIn, WorkoutSetLogIn


class _FakeMeRepository:
    def __init__(self):
        self.patient = {
            "id": "patient-1",
            "owner_id": "owner-1",
            "name": "Maria",
        }
        self.series = []
        self.created_payload = None
        self.appointments = []
        self.plans_by_id = {}
        self.body_compositions_by_id = {}
        self.food_diary_entries = []
        self.created_food_diary_entry = None
        self.hydration = {"current_ml": 0, "target_ml": 2000}
        self.messages = []
        self.message_sequence = 1
        self.created_measurement_payload = None
        self.checkin_templates = {}
        self.checkin_responses = []
        self.checkin_response_sequence = 1
        self.active_workout_plan = None
        self.workout_logs = []
        self.last_upsert_kwargs = None

    async def get_user(self, user_id):
        return {"id": user_id, "email": "maria@email.com", "name": "Maria"}

    async def get_patient_for_user(self, user_id):
        return self.patient

    async def update_patient_profile(self, patient_id, payload):
        if patient_id != self.patient["id"]:
            return None
        self.patient.update(payload)
        return self.patient

    async def list_appointments(self, patient_id, *, from_dt=None, to_dt=None):
        return self.appointments

    async def get_active_plan(self, patient_id):
        return None

    async def find_owner_overlap(self, owner_id, *, start, end, exclude_appointment_id=None):
        return None

    async def create_patient_appointment(self, **kwargs):
        self.created_payload = kwargs
        return {
            "id": "appt-1",
            "start": kwargs["start"],
            "end": kwargs["end"],
            "mode": kwargs["mode"],
            "status": "pending",
            "note": kwargs["note"],
            "owner_id": kwargs["owner_id"],
        }

    async def get_patient_appointment(self, patient_id, appointment_id):
        return None

    async def update_patient_appointment(self, patient_id, appointment_id, updates):
        return None

    async def list_measurements(self, patient_id, *, limit):
        return []

    async def create_measurement(self, *, owner_id, patient_id, payload):
        self.created_measurement_payload = payload
        return {
            "id": "measurement-1",
            "at": payload.get("at"),
            "weight_kg": payload.get("weight_kg"),
            "body_fat_pct": payload.get("body_fat_pct"),
            "waist_cm": payload.get("waist_cm"),
            "notes": payload.get("notes"),
            "attachment_url": payload.get("attachment_url"),
            "attachment_type": payload.get("attachment_type"),
        }

    async def list_measurements_since(self, patient_id, *, since):
        return self.series

    async def list_prescriptions(self, patient_id, *, limit):
        return []

    async def list_recipe_collections(self, owner_id):
        return []

    async def list_education_videos(self, owner_id):
        return []

    async def list_articles(self, owner_id):
        platform = [{"id": "platform-1", "title": "Macronutrientes", "owner_id": None}]
        if not owner_id:
            return platform
        return platform + [{"id": "mine-1", "title": "Mi consejo", "owner_id": owner_id}]

    async def get_nutritionist_profile(self, owner_id):
        if not owner_id:
            return None
        return {
            "name": "Dra. Ruiz",
            "role_label": "Nutrióloga clínica",
            "bio": "Bio de prueba",
            "years_experience": 10,
            "session_price": 500.0,
            "session_price_currency": "MXN",
            "social_links": [{"platform": "instagram", "handle": "@dra.ruiz"}],
            "patient_count": 42,
        }

    async def list_food_diary_entries(self, patient_id, *, limit):
        return self.food_diary_entries

    async def create_food_diary_entry(self, *, owner_id, patient_id, payload):
        self.created_food_diary_entry = {"owner_id": owner_id, "patient_id": patient_id, **payload}
        entry = {"id": "entry-1", **payload}
        self.food_diary_entries.append(entry)
        return entry

    async def list_recommendations(self, owner_id, *, kind=None):
        if not owner_id:
            return []
        items = [
            {"id": "rec-1", "kind": "supplement", "title": "Omega 3"},
            {"id": "rec-2", "kind": "brand", "title": "Proteína Gold Standard"},
        ]
        if kind:
            items = [i for i in items if i["kind"] == kind]
        return items

    async def list_clinical_notes(self, patient_id):
        return []

    async def list_body_compositions(self, patient_id):
        return []

    async def get_body_composition_by_id(self, body_composition_id):
        return self.body_compositions_by_id.get(body_composition_id)

    async def get_plan_summary(self, plan_id):
        return self.plans_by_id.get(plan_id)

    async def get_hydration_today(self, patient_id):
        return self.hydration

    async def add_hydration(self, patient_id, owner_id, *, delta_ml):
        target = self.hydration["target_ml"]
        next_ml = max(0, min(target, self.hydration["current_ml"] + delta_ml))
        self.hydration = {"current_ml": next_ml, "target_ml": target}
        return self.hydration

    async def list_messages(self, owner_id, patient_id, *, since=None):
        items = self.messages
        if since is not None:
            items = [m for m in items if m["created_at"] > since]
        return items

    async def create_message(
        self, owner_id, patient_id, *, text, attachment_url=None, attachment_type=None
    ):
        if owner_id is None:
            raise LookupError("No nutritionist assigned yet")
        message = {
            "id": str(self.message_sequence),
            "sender_role": "patient",
            "text": text,
            "created_at": datetime.now(UTC),
            "read_at": None,
            "attachment_url": attachment_url,
            "attachment_type": attachment_type,
        }
        self.message_sequence += 1
        self.messages.append(message)
        return message

    async def list_checkin_templates(self, owner_id):
        return [t for t in self.checkin_templates.values() if t.get("owner_id") == owner_id]

    async def get_checkin_template(self, owner_id, template_id):
        template = self.checkin_templates.get(template_id)
        if template and template.get("owner_id") == owner_id:
            return template
        return None

    async def create_checkin_response(
        self, *, owner_id, patient_id, template_id, appointment_id, answers
    ):
        response = {
            "id": str(self.checkin_response_sequence),
            "owner_id": owner_id,
            "patient_id": patient_id,
            "template_id": template_id,
            "appointment_id": appointment_id,
            "answers": answers,
            "submitted_at": datetime.now(UTC),
        }
        self.checkin_response_sequence += 1
        self.checkin_responses.append(response)
        return response

    async def list_checkin_responses(self, patient_id):
        return [r for r in self.checkin_responses if r["patient_id"] == patient_id]

    async def get_active_workout_plan(self, patient_id):
        return self.active_workout_plan

    async def list_workout_logs(self, patient_id, *, workout_plan_id=None):
        items = self.workout_logs
        if workout_plan_id is not None:
            items = [w for w in items if w["workout_plan_id"] == workout_plan_id]
        return items

    async def upsert_workout_log(
        self,
        *,
        owner_id,
        patient_id,
        workout_plan_id,
        day_index,
        exercise_index,
        sets,
        comment=None,
        photo_url=None,
        photo_content_type=None,
    ):
        self.last_upsert_kwargs = {
            "owner_id": owner_id,
            "patient_id": patient_id,
            "workout_plan_id": workout_plan_id,
            "day_index": day_index,
            "exercise_index": exercise_index,
            "sets": sets,
            "comment": comment,
            "photo_url": photo_url,
            "photo_content_type": photo_content_type,
        }
        key = (workout_plan_id, day_index, exercise_index)
        existing = next(
            (
                w
                for w in self.workout_logs
                if (w["workout_plan_id"], w["day_index"], w["exercise_index"]) == key
            ),
            None,
        )
        if existing is not None:
            self.workout_logs.remove(existing)
        document = {
            "workout_plan_id": workout_plan_id,
            "day_index": day_index,
            "exercise_index": exercise_index,
            "sets": sets,
            "comment": comment,
            "photo_url": photo_url,
            "photo_content_type": photo_content_type,
            "coach_marked_done": existing.get("coach_marked_done", False) if existing else False,
            "updated_at": datetime.now(UTC),
        }
        self.workout_logs.append(document)
        return document


class MeServiceTest(unittest.IsolatedAsyncioTestCase):
    def test_parse_range_supports_days_weeks_and_months(self):
        self.assertEqual(parse_range("15d"), timedelta(days=15))
        self.assertEqual(parse_range("2w"), timedelta(weeks=2))
        self.assertEqual(parse_range("3m"), timedelta(days=90))
        self.assertEqual(parse_range(None), timedelta(days=30))

    async def test_get_progress_computes_delta(self):
        repository = _FakeMeRepository()
        repository.series = [
            {"at": datetime(2026, 1, 1, tzinfo=UTC), "weight_kg": 80, "body_fat_pct": 20},
            {"at": datetime(2026, 2, 1, tzinfo=UTC), "weight_kg": 77.5, "body_fat_pct": 18.5},
        ]
        service = MeService(repository)

        result = await service.get_progress("user-1", "30d")

        self.assertEqual(result["delta"]["weight_kg"], -2.5)
        self.assertEqual(result["delta"]["body_fat_pct"], -1.5)

    async def test_add_measurement_round_trips_the_attachment(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        result = await service.add_measurement(
            "user-1",
            {
                "weight_kg": 78.4,
                "attachment_url": "/uploads/measurements/user-1/photo.jpg",
                "attachment_type": "image/jpeg",
            },
        )

        self.assertEqual(
            repository.created_measurement_payload["attachment_url"],
            "/uploads/measurements/user-1/photo.jpg",
        )
        self.assertEqual(result["attachment_type"], "image/jpeg")

    async def test_request_appointment_defaults_end_and_pending(self):
        repository = _FakeMeRepository()
        service = MeService(repository)
        start = datetime(2026, 3, 20, 10, 0, tzinfo=UTC)

        result = await service.request_appointment(
            "user-1",
            {"start": start.isoformat(), "mode": "online"},
        )

        self.assertEqual(result["status"], "pending")
        self.assertEqual(repository.created_payload["end"], start + timedelta(minutes=45))

    async def test_update_profile_applies_patch_to_linked_patient(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        result = await service.update_profile(
            "user-1",
            {"age": 29, "sex": "female", "height_cm": 165.0, "allergies": ["lactosa"]},
        )

        self.assertEqual(result["age"], 29)
        self.assertEqual(result["sex"], "female")
        self.assertEqual(result["height_cm"], 165.0)
        self.assertEqual(result["allergies"], ["lactosa"])

    async def test_update_profile_rejects_empty_payload(self):
        service = MeService(_FakeMeRepository())

        with self.assertRaises(ValueError):
            await service.update_profile("user-1", {})

    async def test_update_profile_rejects_user_without_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        with self.assertRaises(LookupError):
            await service.update_profile("user-1", {"age": 29})

    async def test_list_consultations_resolves_linked_plan_and_body_composition(self):
        repository = _FakeMeRepository()
        repository.appointments = [
            {
                "id": "appt-1",
                "start": datetime(2026, 1, 15, tzinfo=UTC),
                "status": "confirmed",
                "note": "Seguimiento mensual",
                "plan_id": "plan-1",
                "body_composition_id": "scan-1",
            },
            {
                "id": "appt-2",
                "start": datetime(2026, 2, 15, tzinfo=UTC),
                "status": "confirmed",
                "note": "Ajuste de plan",
                "plan_id": None,
                "body_composition_id": None,
            },
        ]
        repository.plans_by_id = {"plan-1": {"id": "plan-1", "name": "Plan semanal"}}
        repository.body_compositions_by_id = {
            "scan-1": {"id": "scan-1", "metrics": {"weight_kg": 68}}
        }
        service = MeService(repository)

        result = await service.list_consultations("user-1")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "appt-2")
        self.assertIsNone(result[0]["plan"])
        self.assertIsNone(result[0]["body_composition"])
        self.assertEqual(result[1]["id"], "appt-1")
        self.assertEqual(result[1]["plan"]["name"], "Plan semanal")
        self.assertEqual(result[1]["body_composition"]["metrics"]["weight_kg"], 68)

    async def test_list_consultations_returns_empty_for_user_without_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        result = await service.list_consultations("user-1")

        self.assertEqual(result, [])

    async def test_get_nutritionist_profile_resolves_through_the_linked_patients_owner(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        result = await service.get_nutritionist_profile("user-1")

        self.assertEqual(result["name"], "Dra. Ruiz")
        self.assertEqual(result["patient_count"], 42)

    async def test_get_nutritionist_profile_returns_none_for_user_without_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        result = await service.get_nutritionist_profile("user-1")

        self.assertIsNone(result)

    async def test_add_food_diary_entry_requires_a_dish(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        with self.assertRaises(ValueError):
            await service.add_food_diary_entry("user-1", {})

    async def test_add_food_diary_entry_resolves_owner_from_the_linked_patient(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        result = await service.add_food_diary_entry(
            "user-1", {"dish": "Tacos al pastor", "kcal": 450}
        )

        self.assertEqual(result["dish"], "Tacos al pastor")
        self.assertEqual(repository.created_food_diary_entry["owner_id"], "owner-1")
        self.assertEqual(repository.created_food_diary_entry["patient_id"], "patient-1")

    async def test_list_food_diary_entries_returns_empty_for_user_without_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        result = await service.list_food_diary_entries("user-1", limit=50)

        self.assertEqual(result, [])

    async def test_list_recommendations_filters_by_kind(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        result = await service.list_recommendations("user-1", kind="supplement")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Omega 3")

    async def test_list_recommendations_returns_empty_for_user_without_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        result = await service.list_recommendations("user-1")

        self.assertEqual(result, [])

    async def test_add_hydration_clamps_between_zero_and_target(self):
        repository = _FakeMeRepository()
        repository.hydration = {"current_ml": 100, "target_ml": 2000}
        service = MeService(repository)

        result = await service.add_hydration("user-1", -500)
        self.assertEqual(result["current_ml"], 0)

        result = await service.add_hydration("user-1", 5000)
        self.assertEqual(result["current_ml"], 2000)

    async def test_get_hydration_returns_default_for_user_without_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        result = await service.get_hydration("user-1")

        self.assertEqual(result, {"current_ml": 0, "target_ml": 2000})

    async def test_add_hydration_requires_a_linked_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        with self.assertRaises(LookupError):
            await service.add_hydration("user-1", 250)

    async def test_send_message_creates_a_message_when_owner_is_assigned(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        message = await service.send_message("user-1", "Hola doctor")

        self.assertEqual(message["text"], "Hola doctor")
        self.assertEqual(message["sender_role"], "patient")

    async def test_send_message_rejects_blank_text(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        with self.assertRaises(ValueError):
            await service.send_message("user-1", "   ")

    async def test_send_message_allows_an_attachment_with_no_text(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        message = await service.send_message(
            "user-1",
            "",
            attachment_url="/uploads/messaging/owner-1/patient-1/photo.jpg",
            attachment_type="image/jpeg",
        )

        self.assertEqual(message["text"], "")
        self.assertEqual(message["attachment_url"], "/uploads/messaging/owner-1/patient-1/photo.jpg")

    async def test_send_message_rejects_a_patient_without_a_nutritionist(self):
        repository = _FakeMeRepository()
        repository.patient["owner_id"] = None
        service = MeService(repository)

        with self.assertRaises(LookupError):
            await service.send_message("user-1", "hola")

    async def test_list_messages_returns_empty_for_a_user_without_a_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        result = await service.list_messages("user-1")

        self.assertEqual(result, [])

    async def test_list_checkin_templates_returns_the_owners_templates(self):
        repository = _FakeMeRepository()
        repository.checkin_templates["t1"] = {
            "id": "t1",
            "owner_id": "owner-1",
            "title": "Check-in semanal",
            "fields": [{"id": "f1", "type": "text", "label": "¿Cómo te sentiste?", "required": True}],
        }
        service = MeService(repository)

        result = await service.list_checkin_templates("user-1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Check-in semanal")

    async def test_list_checkin_templates_returns_empty_for_a_patient_without_a_nutritionist(self):
        repository = _FakeMeRepository()
        repository.patient["owner_id"] = None
        service = MeService(repository)

        result = await service.list_checkin_templates("user-1")

        self.assertEqual(result, [])

    async def test_submit_checkin_response_creates_a_response(self):
        repository = _FakeMeRepository()
        repository.checkin_templates["t1"] = {
            "id": "t1",
            "owner_id": "owner-1",
            "title": "Check-in semanal",
            "fields": [{"id": "f1", "type": "text", "label": "¿Cómo te sentiste?", "required": True}],
        }
        service = MeService(repository)

        result = await service.submit_checkin_response(
            "user-1",
            {"template_id": "t1", "appointment_id": None, "answers": [{"field_id": "f1", "values": ["Bien"]}]},
        )

        self.assertEqual(result["template_id"], "t1")
        self.assertEqual(repository.checkin_responses[0]["patient_id"], "patient-1")

    async def test_submit_checkin_response_rejects_a_missing_required_field(self):
        repository = _FakeMeRepository()
        repository.checkin_templates["t1"] = {
            "id": "t1",
            "owner_id": "owner-1",
            "title": "Check-in semanal",
            "fields": [{"id": "f1", "type": "text", "label": "¿Cómo te sentiste?", "required": True}],
        }
        service = MeService(repository)

        with self.assertRaises(ValueError):
            await service.submit_checkin_response(
                "user-1", {"template_id": "t1", "appointment_id": None, "answers": []}
            )

    async def test_submit_checkin_response_rejects_a_template_not_owned_by_the_patients_nutritionist(self):
        repository = _FakeMeRepository()
        repository.checkin_templates["t1"] = {
            "id": "t1",
            "owner_id": "someone-else",
            "title": "Otro",
            "fields": [],
        }
        service = MeService(repository)

        with self.assertRaises(LookupError):
            await service.submit_checkin_response(
                "user-1", {"template_id": "t1", "appointment_id": None, "answers": []}
            )

    async def test_list_checkin_responses_returns_the_patients_own_history(self):
        repository = _FakeMeRepository()
        repository.checkin_templates["t1"] = {
            "id": "t1",
            "owner_id": "owner-1",
            "title": "Check-in semanal",
            "fields": [{"id": "f1", "type": "text", "label": "x", "required": False}],
        }
        service = MeService(repository)
        await service.submit_checkin_response(
            "user-1", {"template_id": "t1", "appointment_id": None, "answers": []}
        )

        result = await service.list_checkin_responses("user-1")

        self.assertEqual(len(result), 1)

    async def test_get_active_workout_plan_returns_the_repositorys_result(self):
        repository = _FakeMeRepository()
        repository.active_workout_plan = {"id": "wp1", "name": "Rutina"}
        service = MeService(repository)

        result = await service.get_active_workout_plan("user-1")

        self.assertEqual(result["name"], "Rutina")

    async def test_get_active_workout_plan_returns_none_for_a_user_without_a_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        result = await service.get_active_workout_plan("user-1")

        self.assertIsNone(result)

    async def test_upsert_workout_log_persists_a_sets_list(self):
        repository = _FakeMeRepository()
        service = MeService(repository)
        payload = WorkoutExerciseLogIn(
            workout_plan_id="wp1",
            day_index=0,
            exercise_index=0,
            sets=[WorkoutSetLogIn(set_index=0, reps_completed=10, weight_kg=42.5, rpe=8)],
            comment="Se sintió bien",
        )

        result = await service.upsert_workout_log("user-1", payload)

        self.assertEqual(result["sets"][0]["weight_kg"], 42.5)
        self.assertEqual(result["sets"][0]["rpe"], 8)
        self.assertEqual(result["comment"], "Se sintió bien")
        self.assertEqual(repository.last_upsert_kwargs["owner_id"], "owner-1")

    async def test_upsert_workout_log_replaces_the_sets_list_on_a_second_call(self):
        repository = _FakeMeRepository()
        service = MeService(repository)
        first_payload = WorkoutExerciseLogIn(
            workout_plan_id="wp1",
            day_index=0,
            exercise_index=0,
            sets=[WorkoutSetLogIn(set_index=0, reps_completed=10, weight_kg=40)],
        )
        second_payload = WorkoutExerciseLogIn(
            workout_plan_id="wp1",
            day_index=0,
            exercise_index=0,
            sets=[
                WorkoutSetLogIn(set_index=0, reps_completed=10, weight_kg=40),
                WorkoutSetLogIn(set_index=1, reps_completed=8, weight_kg=45),
            ],
        )

        await service.upsert_workout_log("user-1", first_payload)
        await service.upsert_workout_log("user-1", second_payload)

        self.assertEqual(len(repository.workout_logs), 1)
        self.assertEqual(len(repository.workout_logs[0]["sets"]), 2)

    async def test_upsert_workout_log_rejects_a_patient_without_a_nutritionist(self):
        repository = _FakeMeRepository()
        repository.patient["owner_id"] = None
        service = MeService(repository)
        payload = WorkoutExerciseLogIn(workout_plan_id="wp1", day_index=0, exercise_index=0)

        with self.assertRaises(LookupError):
            await service.upsert_workout_log("user-1", payload)

    async def test_list_workout_logs_returns_the_patients_own_logs(self):
        repository = _FakeMeRepository()
        repository.workout_logs = [
            {"workout_plan_id": "wp1", "day_index": 0, "exercise_index": 0, "sets": [], "updated_at": datetime.now(UTC)}
        ]
        service = MeService(repository)

        result = await service.list_workout_logs("user-1")

        self.assertEqual(len(result), 1)

    async def test_list_articles_merges_platform_and_the_patients_own_nutritionist(self):
        repository = _FakeMeRepository()
        service = MeService(repository)

        result = await service.list_articles("user-1")

        self.assertEqual([a["id"] for a in result], ["platform-1", "mine-1"])

    async def test_list_articles_returns_only_platform_content_without_a_linked_patient(self):
        repository = _FakeMeRepository()
        repository.patient = None
        service = MeService(repository)

        result = await service.list_articles("user-1")

        self.assertEqual([a["id"] for a in result], ["platform-1"])
