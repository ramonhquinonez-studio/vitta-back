import unittest

from app.modules.recommendations.application.recommendations_service import (
    RecommendationsService,
)
from app.modules.recommendations.domain.entities import Recommendation


class _FakeRecommendationsRepository:
    def __init__(self):
        self.items: dict[str, list[Recommendation]] = {}
        self.sequence = 1
        self.assignments: dict[tuple[str, str], set[str]] = {}

    async def list_for_owner(self, owner_id, *, kind=None):
        items = self.items.get(owner_id, [])
        if kind:
            items = [r for r in items if r.kind == kind]
        return items

    async def list_platform_recommendations(self, *, kind=None):
        items = self.items.get(None, [])
        if kind:
            items = [r for r in items if r.kind == kind]
        return items

    def _owns(self, owner_id, rec_id):
        return self._find(owner_id, rec_id) is not None

    async def assign_to_patients(self, owner_id, recommendation_id, patient_ids):
        if not self._owns(owner_id, recommendation_id):
            return 0
        key = (owner_id, recommendation_id)
        assigned = self.assignments.setdefault(key, set())
        assigned.update(patient_ids)
        return len(patient_ids)

    async def unassign_from_patient(self, owner_id, recommendation_id, patient_id):
        key = (owner_id, recommendation_id)
        assigned = self.assignments.get(key, set())
        if patient_id not in assigned:
            return False
        assigned.discard(patient_id)
        return True

    async def list_assigned_patient_ids(self, owner_id, recommendation_id):
        return sorted(self.assignments.get((owner_id, recommendation_id), set()))

    async def create_for_owner(self, owner_id, payload):
        rec = Recommendation(
            id=f"rec-{self.sequence}",
            owner_id=owner_id,
            kind=payload["kind"],
            title=payload["title"],
            equivalency_group_id=payload.get("equivalency_group_id"),
        )
        self.sequence += 1
        self.items.setdefault(owner_id, []).append(rec)
        return rec

    def _find(self, owner_id, rec_id):
        for rec in self.items.get(owner_id, []):
            if rec.id == rec_id:
                return rec
        return None

    async def update_for_owner(self, owner_id, recommendation_id, payload):
        current = self._find(owner_id, recommendation_id)
        if current is None:
            return None
        updated = Recommendation(
            id=current.id,
            owner_id=current.owner_id,
            kind=current.kind,
            title=payload.get("title", current.title),
            price=payload.get("price", current.price),
        )
        self.items[owner_id] = [
            updated if r.id == recommendation_id else r for r in self.items[owner_id]
        ]
        return updated

    async def delete_for_owner(self, owner_id, recommendation_id):
        current = self._find(owner_id, recommendation_id)
        if current is None:
            return False
        self.items[owner_id] = [r for r in self.items[owner_id] if r.id != recommendation_id]
        return True


class RecommendationsServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_recommendation_requires_a_title(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)

        with self.assertRaises(ValueError):
            await service.create_recommendation("owner-1", {"kind": "supplement"})

    async def test_create_recommendation_rejects_an_invalid_kind(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)

        with self.assertRaises(ValueError):
            await service.create_recommendation(
                "owner-1", {"kind": "invalid", "title": "Omega 3"}
            )

    async def test_create_brand_recommendation_persists_the_equivalency_group(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)

        created = await service.create_recommendation(
            "owner-1",
            {"kind": "brand", "title": "Nutrioli", "equivalency_group_id": "aceites_sin_proteina"},
        )

        self.assertEqual(created.equivalency_group_id, "aceites_sin_proteina")

    async def test_create_then_list_filters_by_kind(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)
        await service.create_recommendation("owner-1", {"kind": "supplement", "title": "Omega 3"})
        await service.create_recommendation(
            "owner-1", {"kind": "brand", "title": "Proteína Gold Standard"}
        )

        supplements = await service.list_my_recommendations("owner-1", kind="supplement")
        brands = await service.list_my_recommendations("owner-1", kind="brand")

        self.assertEqual(len(supplements), 1)
        self.assertEqual(supplements[0].title, "Omega 3")
        self.assertEqual(len(brands), 1)
        self.assertEqual(brands[0].title, "Proteína Gold Standard")

    async def test_update_then_delete_recommendation(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)
        created = await service.create_recommendation(
            "owner-1", {"kind": "supplement", "title": "Omega 3"}
        )

        updated = await service.update_recommendation("owner-1", created.id, {"price": "$250"})
        self.assertEqual(updated.price, "$250")

        await service.delete_recommendation("owner-1", created.id)
        self.assertEqual(await service.list_my_recommendations("owner-1"), [])

    async def test_create_bulk_creates_every_item(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)

        created = await service.create_bulk(
            "owner-1",
            [
                {"kind": "supplement", "title": "Omega 3"},
                {"kind": "brand", "title": "NOW Foods"},
            ],
        )

        self.assertEqual(len(created), 2)
        self.assertEqual(await service.list_my_recommendations("owner-1"), created)

    async def test_create_bulk_rejects_the_whole_batch_if_one_item_is_invalid(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)

        with self.assertRaises(ValueError):
            await service.create_bulk(
                "owner-1",
                [
                    {"kind": "supplement", "title": "Omega 3"},
                    {"kind": "supplement"},  # missing title
                ],
            )

        self.assertEqual(await service.list_my_recommendations("owner-1"), [])

    async def test_update_rejects_a_recommendation_not_owned(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)
        created = await service.create_recommendation(
            "owner-1", {"kind": "supplement", "title": "Omega 3"}
        )

        with self.assertRaises(LookupError):
            await service.update_recommendation("owner-2", created.id, {"price": "$1"})

    async def test_list_platform_recommendations_returns_owner_less_items(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)
        await service.create_recommendation(None, {"kind": "supplement", "title": "Vitamina D"})
        await service.create_recommendation("owner-1", {"kind": "supplement", "title": "Omega 3"})

        platform = await service.list_platform_recommendations()

        self.assertEqual(len(platform), 1)
        self.assertEqual(platform[0].title, "Vitamina D")

    async def test_assign_then_list_then_unassign(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)
        created = await service.create_recommendation(
            "owner-1", {"kind": "supplement", "title": "Omega 3"}
        )

        count = await service.assign_to_patients("owner-1", created.id, ["patient-1", "patient-2"])
        self.assertEqual(count, 2)

        assigned = await service.list_assignments("owner-1", created.id)
        self.assertCountEqual(assigned, ["patient-1", "patient-2"])

        await service.unassign_from_patient("owner-1", created.id, "patient-1")
        assigned = await service.list_assignments("owner-1", created.id)
        self.assertEqual(assigned, ["patient-2"])

    async def test_assign_requires_at_least_one_patient(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)
        created = await service.create_recommendation(
            "owner-1", {"kind": "supplement", "title": "Omega 3"}
        )

        with self.assertRaises(ValueError):
            await service.assign_to_patients("owner-1", created.id, [])

    async def test_assign_rejects_a_recommendation_not_owned(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)
        created = await service.create_recommendation(
            "owner-1", {"kind": "supplement", "title": "Omega 3"}
        )

        with self.assertRaises(LookupError):
            await service.assign_to_patients("owner-2", created.id, ["patient-1"])

    async def test_unassign_rejects_a_nonexistent_assignment(self):
        repository = _FakeRecommendationsRepository()
        service = RecommendationsService(repository)
        created = await service.create_recommendation(
            "owner-1", {"kind": "supplement", "title": "Omega 3"}
        )

        with self.assertRaises(LookupError):
            await service.unassign_from_patient("owner-1", created.id, "patient-1")


if __name__ == "__main__":
    unittest.main()
