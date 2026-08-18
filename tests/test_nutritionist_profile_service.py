import unittest

from app.modules.nutritionist_profile.application.nutritionist_profile_service import (
    NutritionistProfileService,
)
from app.modules.nutritionist_profile.domain.entities import NutritionistProfile, SocialLink


class _FakeNutritionistProfileRepository:
    def __init__(self):
        self.profiles: dict[str, NutritionistProfile] = {}
        self.patient_counts: dict[str, int] = {}

    async def get_for_owner(self, owner_id):
        return self.profiles.get(owner_id)

    async def upsert_for_owner(self, owner_id, payload):
        current = self.profiles.get(owner_id) or NutritionistProfile(owner_id=owner_id)
        social_links = [
            SocialLink(platform=link["platform"], handle=link["handle"])
            for link in payload.get("social_links", [
                {"platform": l.platform, "handle": l.handle} for l in current.social_links
            ])
        ]
        updated = NutritionistProfile(
            owner_id=owner_id,
            role_label=payload.get("role_label", current.role_label),
            bio=payload.get("bio", current.bio),
            years_experience=payload.get("years_experience", current.years_experience),
            session_price=payload.get("session_price", current.session_price),
            session_price_currency=payload.get(
                "session_price_currency", current.session_price_currency
            ),
            social_links=social_links,
        )
        self.profiles[owner_id] = updated
        return updated

    async def count_patients_for_owner(self, owner_id):
        return self.patient_counts.get(owner_id, 0)


class NutritionistProfileServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_get_my_profile_returns_defaults_when_none_saved_yet(self):
        repository = _FakeNutritionistProfileRepository()
        repository.patient_counts["owner-1"] = 3
        service = NutritionistProfileService(repository)

        result = await service.get_my_profile("owner-1")

        self.assertIsNone(result["role_label"])
        self.assertEqual(result["session_price_currency"], "MXN")
        self.assertEqual(result["social_links"], [])
        self.assertEqual(result["patient_count"], 3)

    async def test_update_my_profile_saves_fields_and_reports_patient_count(self):
        repository = _FakeNutritionistProfileRepository()
        repository.patient_counts["owner-1"] = 5
        service = NutritionistProfileService(repository)

        result = await service.update_my_profile(
            "owner-1",
            {
                "role_label": "Nutrióloga clínica",
                "bio": "12 años ayudando a mis pacientes.",
                "years_experience": 12,
                "session_price": 650.0,
                "session_price_currency": "MXN",
                "social_links": [{"platform": "instagram", "handle": "@dra.ruiz"}],
            },
        )

        self.assertEqual(result["role_label"], "Nutrióloga clínica")
        self.assertEqual(result["years_experience"], 12)
        self.assertEqual(result["session_price"], 650.0)
        self.assertEqual(result["social_links"], [{"platform": "instagram", "handle": "@dra.ruiz"}])
        self.assertEqual(result["patient_count"], 5)

    async def test_update_my_profile_rejects_an_empty_payload(self):
        repository = _FakeNutritionistProfileRepository()
        service = NutritionistProfileService(repository)

        with self.assertRaises(ValueError):
            await service.update_my_profile("owner-1", {})

    async def test_get_profile_for_owner_returns_none_when_never_saved(self):
        repository = _FakeNutritionistProfileRepository()
        service = NutritionistProfileService(repository)

        result = await service.get_profile_for_owner("owner-1")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
