import unittest
from datetime import UTC, datetime, timedelta

from app.modules.me.application.me_service import MeService, parse_range


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
        return {}

    async def list_measurements_since(self, patient_id, *, since):
        return self.series

    async def list_prescriptions(self, patient_id, *, limit):
        return []

    async def list_recipe_collections(self, owner_id):
        return []

    async def list_education_videos(self, owner_id):
        return []

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

    async def add_hydration(self, patient_id, *, delta_ml):
        target = self.hydration["target_ml"]
        next_ml = max(0, min(target, self.hydration["current_ml"] + delta_ml))
        self.hydration = {"current_ml": next_ml, "target_ml": target}
        return self.hydration


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
