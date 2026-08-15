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
        return []

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

    async def list_clinical_notes(self, patient_id):
        return []

    async def list_body_compositions(self, patient_id):
        return []


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
