import unittest
from datetime import datetime

from app.modules.patients.application.patients_service import PatientsService
from app.modules.patients.domain.entities import Patient


class _FakePatientsRepository:
    def __init__(self):
        self.patients: dict[str, Patient] = {}
        self.sequence = 1
        self.body_compositions: dict[str, list[dict]] = {}
        self.food_diary_entries: dict[str, list[dict]] = {}
        self.plan_assignments: dict[str, list[dict]] = {}
        self.measurements: dict[str, list[dict]] = {}
        self.checkin_responses: dict[str, list[dict]] = {}
        self.workout_plan_assignments: dict[str, list[dict]] = {}
        self.workout_logs: dict[str, list[dict]] = {}
        self.invite_sequence = 0
        self.last_invite_patient_id = "unset"
        self.connection_codes: dict[str, str] = {}
        self.dashboard_data: dict = {}
        self.workout_logs_by_key: dict[tuple, bool] = {}

    async def list_for_owner(self, owner_id, *, page, limit, query=None, include_archived=False):
        items = [p for p in self.patients.values() if p.owner_id == owner_id]
        if not include_archived:
            items = [p for p in items if p.archived_at is None]
        if query:
            items = [p for p in items if query.lower() in p.name.lower()]
        return items[:limit], len(items)

    async def create_for_owner(self, owner_id, payload):
        patient = Patient(
            id=str(self.sequence),
            owner_id=owner_id,
            name=payload["name"],
            age=payload.get("age"),
            sex=payload.get("sex"),
            height_cm=payload.get("height_cm"),
            allergies=list(payload.get("allergies") or []),
            notes=payload.get("notes"),
            tags=list(payload.get("tags") or []),
            user_id=payload.get("user_id"),
            email=payload.get("email"),
            phone=payload.get("phone"),
        )
        self.patients[patient.id] = patient
        self.sequence += 1
        return patient

    async def get_for_owner(self, owner_id, patient_id):
        patient = self.patients.get(patient_id)
        if patient and patient.owner_id == owner_id:
            return patient
        return None

    async def update_for_owner(self, owner_id, patient_id, payload):
        current = await self.get_for_owner(owner_id, patient_id)
        if current is None:
            return None
        updated = Patient(
            id=current.id,
            owner_id=current.owner_id,
            name=payload.get("name", current.name),
            age=payload.get("age", current.age),
            sex=payload.get("sex", current.sex),
            height_cm=payload.get("height_cm", current.height_cm),
            allergies=payload.get("allergies", current.allergies),
            notes=payload.get("notes", current.notes),
            tags=payload.get("tags", current.tags),
            daily_kcal_goal=payload.get("daily_kcal_goal", current.daily_kcal_goal),
            daily_protein_g_goal=payload.get(
                "daily_protein_g_goal", current.daily_protein_g_goal
            ),
            daily_carbs_g_goal=payload.get("daily_carbs_g_goal", current.daily_carbs_g_goal),
            daily_fat_g_goal=payload.get("daily_fat_g_goal", current.daily_fat_g_goal),
            email=payload.get("email", current.email),
            phone=payload.get("phone", current.phone),
            archived_at=current.archived_at,
        )
        self.patients[patient_id] = updated
        return updated

    async def archive_for_owner(self, owner_id, patient_id):
        current = await self.get_for_owner(owner_id, patient_id)
        if current is None:
            return None
        updated = Patient(**{**current.__dict__, "archived_at": datetime.utcnow()})
        self.patients[patient_id] = updated
        return updated

    async def unarchive_for_owner(self, owner_id, patient_id):
        current = await self.get_for_owner(owner_id, patient_id)
        if current is None:
            return None
        updated = Patient(**{**current.__dict__, "archived_at": None})
        self.patients[patient_id] = updated
        return updated

    async def list_body_compositions(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.body_compositions.get(patient_id, [])

    async def list_food_diary_entries(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.food_diary_entries.get(patient_id, [])

    async def list_plan_assignments(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.plan_assignments.get(patient_id, [])

    async def list_measurements(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.measurements.get(patient_id, [])

    async def list_checkin_responses(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.checkin_responses.get(patient_id, [])

    async def list_workout_plan_assignments(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.workout_plan_assignments.get(patient_id, [])

    async def list_workout_logs(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.workout_logs.get(patient_id, [])

    async def get_dashboard(self, owner_id):
        return self.dashboard_data

    async def toggle_coach_workout_log(
        self, owner_id, patient_id, *, workout_plan_id, day_index, exercise_index
    ):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        key = (patient_id, workout_plan_id, day_index, exercise_index)
        new_value = not self.workout_logs_by_key.get(key, False)
        self.workout_logs_by_key[key] = new_value
        return {"completed": new_value}

    async def create_invite_code(self, owner_id, patient_id=None):
        self.invite_sequence += 1
        self.last_invite_patient_id = patient_id
        return {"code": f"CODE{self.invite_sequence}", "expires_at": None}

    async def create_unclaimed(self, name, code):
        patient = Patient(id=str(self.sequence), owner_id=None, name=name)
        self.patients[patient.id] = patient
        self.connection_codes[code] = patient.id
        self.sequence += 1
        return patient

    async def claim_patient(self, owner_id, code):
        patient_id = self.connection_codes.get(code)
        if patient_id is None:
            return None
        patient = self.patients.get(patient_id)
        if patient is None or patient.owner_id is not None:
            return None
        updated = Patient(
            id=patient.id,
            owner_id=owner_id,
            name=patient.name,
            age=patient.age,
            sex=patient.sex,
            height_cm=patient.height_cm,
            allergies=patient.allergies,
            notes=patient.notes,
            user_id=patient.user_id,
        )
        self.patients[patient_id] = updated
        del self.connection_codes[code]
        return updated


class _FakeQuotaChecker:
    def __init__(self, *, allow: bool):
        self._allow = allow

    async def check(self, owner_id):
        if not self._allow:
            raise PermissionError("Has llegado al límite de tu plan actual.")


class PatientsServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_list_patients_returns_items_and_total(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        await repository.create_for_owner("owner-1", {"name": "Maria"})
        await repository.create_for_owner("owner-1", {"name": "Mario"})

        items, total = await service.list_patients(
            "owner-1",
            page=1,
            limit=20,
            query="Mari",
        )

        self.assertEqual(total, 2)
        self.assertEqual([item.name for item in items], ["Maria", "Mario"])

    async def test_update_patient_rejects_empty_payload(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)

        with self.assertRaises(ValueError):
            await service.update_patient("owner-1", "1", {})

    async def test_update_patient_sets_daily_nutrition_goals(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        updated = await service.update_patient(
            "owner-1",
            patient.id,
            {"daily_kcal_goal": 1800, "daily_protein_g_goal": 120},
        )

        self.assertEqual(updated.daily_kcal_goal, 1800)
        self.assertEqual(updated.daily_protein_g_goal, 120)
        self.assertIsNone(updated.daily_carbs_g_goal)

    async def test_list_body_compositions_returns_the_patients_scans(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.body_compositions[patient.id] = [
            {"id": "bc-1", "at": None, "metrics": {"weight_kg": 68.5}}
        ]

        result = await service.list_body_compositions("owner-1", patient.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metrics"]["weight_kg"], 68.5)

    async def test_list_body_compositions_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.list_body_compositions("owner-2", patient.id)

    async def test_list_food_diary_entries_returns_the_patients_entries(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.food_diary_entries[patient.id] = [
            {"id": "entry-1", "dish": "Tacos al pastor", "kcal": 450}
        ]

        result = await service.list_food_diary_entries("owner-1", patient.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["dish"], "Tacos al pastor")

    async def test_list_food_diary_entries_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.list_food_diary_entries("owner-2", patient.id)

    async def test_list_plan_assignments_returns_the_patients_history(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.plan_assignments[patient.id] = [
            {"plan_id": "plan-2", "plan_name": "Plan B", "assigned_at": "2026-08-10"},
            {"plan_id": "plan-1", "plan_name": "Plan A", "assigned_at": "2026-08-01"},
        ]

        result = await service.list_plan_assignments("owner-1", patient.id)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["plan_name"], "Plan B")

    async def test_list_plan_assignments_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.list_plan_assignments("owner-2", patient.id)

    async def test_list_measurements_returns_the_patients_self_logged_entries(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.measurements[patient.id] = [
            {"weight_kg": 78.4, "attachment_url": "/uploads/measurements/u1/photo.jpg"},
        ]

        result = await service.list_measurements("owner-1", patient.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["attachment_url"], "/uploads/measurements/u1/photo.jpg")

    async def test_list_measurements_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.list_measurements("owner-2", patient.id)

    async def test_list_checkin_responses_returns_the_patients_submitted_responses(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.checkin_responses[patient.id] = [
            {"template_id": "t1", "answers": [{"field_id": "f1", "values": ["Bien"]}]},
        ]

        result = await service.list_checkin_responses("owner-1", patient.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["template_id"], "t1")

    async def test_list_checkin_responses_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.list_checkin_responses("owner-2", patient.id)

    async def test_list_workout_plan_assignments_returns_the_patients_history(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.workout_plan_assignments[patient.id] = [
            {"plan_id": "wp1", "plan_name": "Rutina", "assigned_at": "2026-08-10"},
        ]

        result = await service.list_workout_plan_assignments("owner-1", patient.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["plan_name"], "Rutina")

    async def test_list_workout_plan_assignments_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.list_workout_plan_assignments("owner-2", patient.id)

    async def test_list_workout_logs_returns_the_patients_adherence(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.workout_logs[patient.id] = [
            {"workout_plan_id": "wp1", "day_index": 0, "exercise_index": 0},
        ]

        result = await service.list_workout_logs("owner-1", patient.id)

        self.assertEqual(len(result), 1)

    async def test_get_dashboard_delegates_to_the_repository(self):
        repository = _FakePatientsRepository()
        repository.dashboard_data = {
            "total_patients": 5,
            "new_patients_this_month": 2,
            "upcoming_appointments_this_week": 3,
            "completed_appointments_this_month": 4,
            "active_patients": 4,
            "inactive_patients": [{"id": "p1", "name": "Juan"}],
        }
        service = PatientsService(repository)

        result = await service.get_dashboard("owner-1")

        self.assertEqual(result["total_patients"], 5)
        self.assertEqual(result["inactive_patients"], [{"id": "p1", "name": "Juan"}])

    async def test_create_invite_code_without_a_patient_id_delegates_directly(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)

        invite = await service.create_invite_code("owner-1")

        self.assertEqual(invite["code"], "CODE1")
        self.assertIsNone(repository.last_invite_patient_id)

    async def test_create_invite_code_for_an_existing_unlinked_patient_succeeds(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Juan"})

        invite = await service.create_invite_code("owner-1", patient_id=patient.id)

        self.assertEqual(invite["code"], "CODE1")
        self.assertEqual(repository.last_invite_patient_id, patient.id)

    async def test_create_invite_code_rejects_an_already_linked_patient(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner(
            "owner-1", {"name": "Juan", "user_id": "user-1"}
        )

        with self.assertRaises(ValueError):
            await service.create_invite_code("owner-1", patient_id=patient.id)

    async def test_create_invite_code_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Juan"})

        with self.assertRaises(LookupError):
            await service.create_invite_code("owner-2", patient_id=patient.id)

    async def test_claim_patient_links_the_owner_and_consumes_the_code(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_unclaimed("Sola Paciente", "SOLO2026")

        claimed = await service.claim_patient("owner-1", "SOLO2026")

        self.assertEqual(claimed.id, patient.id)
        self.assertEqual(claimed.owner_id, "owner-1")
        self.assertNotIn("SOLO2026", repository.connection_codes)

    async def test_claim_patient_rejects_an_unknown_code(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)

        with self.assertRaises(LookupError):
            await service.claim_patient("owner-1", "NOPE0000")

    async def test_claim_patient_rejects_a_code_already_claimed(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        await repository.create_unclaimed("Sola Paciente", "SOLO2026")
        await service.claim_patient("owner-1", "SOLO2026")

        with self.assertRaises(LookupError):
            await service.claim_patient("owner-2", "SOLO2026")

    async def test_create_patient_rejects_when_the_quota_checker_raises(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository, quota_checker=_FakeQuotaChecker(allow=False))

        with self.assertRaises(PermissionError):
            await service.create_patient("owner-1", {"name": "Nueva Paciente"})

        self.assertEqual(len(repository.patients), 0)

    async def test_create_patient_succeeds_when_the_quota_checker_allows(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository, quota_checker=_FakeQuotaChecker(allow=True))

        patient = await service.create_patient("owner-1", {"name": "Nueva Paciente"})

        self.assertEqual(patient.name, "Nueva Paciente")

    async def test_claim_patient_rejects_when_the_quota_checker_raises(self):
        repository = _FakePatientsRepository()
        await repository.create_unclaimed("Sola Paciente", "SOLO2026")
        service = PatientsService(repository, quota_checker=_FakeQuotaChecker(allow=False))

        with self.assertRaises(PermissionError):
            await service.claim_patient("owner-1", "SOLO2026")

        self.assertIn("SOLO2026", repository.connection_codes)

    async def test_create_patient_stores_email_and_phone(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)

        patient = await service.create_patient(
            "owner-1", {"name": "Maria", "email": "maria@example.com", "phone": "555-1234"}
        )

        self.assertEqual(patient.email, "maria@example.com")
        self.assertEqual(patient.phone, "555-1234")

    async def test_create_and_update_patient_round_trip_tags(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)

        patient = await service.create_patient(
            "owner-1", {"name": "Maria", "tags": ["VIP", "Grupo A"]}
        )
        self.assertEqual(patient.tags, ["VIP", "Grupo A"])

        updated = await service.update_patient("owner-1", patient.id, {"tags": ["VIP"]})
        self.assertEqual(updated.tags, ["VIP"])

    async def test_archive_patient_sets_archived_at_and_hides_from_default_list(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        archived = await service.archive_patient("owner-1", patient.id)
        self.assertIsNotNone(archived.archived_at)

        items, total = await service.list_patients("owner-1", page=1, limit=20)
        self.assertEqual(total, 0)

        items, total = await service.list_patients(
            "owner-1", page=1, limit=20, include_archived=True
        )
        self.assertEqual(total, 1)

    async def test_archive_patient_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.archive_patient("owner-2", patient.id)

    async def test_unarchive_patient_restores_default_visibility(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        await service.archive_patient("owner-1", patient.id)

        restored = await service.unarchive_patient("owner-1", patient.id)
        self.assertIsNone(restored.archived_at)

        items, total = await service.list_patients("owner-1", page=1, limit=20)
        self.assertEqual(total, 1)

    async def test_toggle_workout_log_marks_and_unmarks_an_exercise(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        payload = {"workout_plan_id": "wp1", "day_index": 0, "exercise_index": 1}

        first = await service.toggle_workout_log("owner-1", patient.id, payload)
        self.assertTrue(first["completed"])

        second = await service.toggle_workout_log("owner-1", patient.id, payload)
        self.assertFalse(second["completed"])

    async def test_toggle_workout_log_requires_day_and_exercise_index(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(ValueError):
            await service.toggle_workout_log(
                "owner-1", patient.id, {"workout_plan_id": "wp1"}
            )

    async def test_toggle_workout_log_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        payload = {"workout_plan_id": "wp1", "day_index": 0, "exercise_index": 0}

        with self.assertRaises(LookupError):
            await service.toggle_workout_log("owner-2", patient.id, payload)
