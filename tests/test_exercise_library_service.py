import unittest

from app.modules.exercise_library.application.exercise_library_service import ExerciseLibraryService


class _FakeExerciseLibraryRepository:
    def __init__(self):
        self.items: dict[str, dict] = {}
        self.sequence = 1

    async def list_for_owner(self, owner_id):
        return [i for i in self.items.values() if i["owner_id"] == owner_id]

    async def create_for_owner(self, owner_id, payload):
        item = {
            "id": str(self.sequence),
            "owner_id": owner_id,
            "name": payload["name"],
            "default_sets": payload.get("default_sets"),
            "default_reps": payload.get("default_reps"),
            "video_url": payload.get("video_url"),
        }
        self.sequence += 1
        self.items[item["id"]] = item
        return item

    async def delete_for_owner(self, owner_id, item_id):
        item = self.items.get(item_id)
        if item is None or item["owner_id"] != owner_id:
            return False
        del self.items[item_id]
        return True


class ExerciseLibraryServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_item_persists_defaults(self):
        repo = _FakeExerciseLibraryRepository()
        service = ExerciseLibraryService(repo)

        item = await service.create_item(
            "owner-1", {"name": "Sentadilla", "default_sets": 4, "default_reps": 10}
        )

        self.assertEqual(item["name"], "Sentadilla")
        self.assertEqual(item["default_sets"], 4)

    async def test_create_item_rejects_a_blank_name(self):
        repo = _FakeExerciseLibraryRepository()
        service = ExerciseLibraryService(repo)

        with self.assertRaises(ValueError):
            await service.create_item("owner-1", {"name": ""})

    async def test_list_items_scopes_by_owner(self):
        repo = _FakeExerciseLibraryRepository()
        service = ExerciseLibraryService(repo)
        await service.create_item("owner-1", {"name": "Sentadilla"})
        await service.create_item("owner-2", {"name": "Plancha"})

        result = await service.list_items("owner-1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Sentadilla")

    async def test_delete_item_rejects_an_item_not_owned(self):
        repo = _FakeExerciseLibraryRepository()
        service = ExerciseLibraryService(repo)
        item = await service.create_item("owner-1", {"name": "Sentadilla"})

        with self.assertRaises(LookupError):
            await service.delete_item("owner-2", item["id"])

    async def test_delete_item_removes_it(self):
        repo = _FakeExerciseLibraryRepository()
        service = ExerciseLibraryService(repo)
        item = await service.create_item("owner-1", {"name": "Sentadilla"})

        await service.delete_item("owner-1", item["id"])

        self.assertEqual(await service.list_items("owner-1"), [])


if __name__ == "__main__":
    unittest.main()
