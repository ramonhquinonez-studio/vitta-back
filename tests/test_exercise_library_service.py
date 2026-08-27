import unittest
from unittest.mock import patch

from app.modules.exercise_library.application.exercise_library_service import ExerciseLibraryService


class _FakeExerciseLibraryRepository:
    def __init__(self):
        self.items: dict[str, dict] = {}
        self.sequence = 1

    async def list_for_owner(self, owner_id):
        return [i for i in self.items.values() if i["owner_id"] == owner_id]

    async def list_platform_items(self):
        return [i for i in self.items.values() if i["owner_id"] is None]

    async def get_platform_item(self, item_id):
        item = self.items.get(item_id)
        if item is None or item["owner_id"] is not None:
            return None
        return item

    async def update_platform_item_video_url(self, item_id, video_url):
        if item_id in self.items:
            self.items[item_id]["video_url"] = video_url

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

    async def test_list_platform_items_returns_only_ownerless_items(self):
        repo = _FakeExerciseLibraryRepository()
        service = ExerciseLibraryService(repo)
        await service.create_item("owner-1", {"name": "Sentadilla"})
        repo.items["platform-1"] = {
            "id": "platform-1",
            "owner_id": None,
            "name": "Press banca",
            "default_sets": None,
            "default_reps": None,
            "video_url": None,
        }

        result = await service.list_platform_items()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Press banca")

    async def test_list_platform_items_is_empty_before_any_sync(self):
        repo = _FakeExerciseLibraryRepository()
        service = ExerciseLibraryService(repo)

        self.assertEqual(await service.list_platform_items(), [])

    async def test_get_platform_video_url_caches_the_gif_on_first_call(self):
        repo = _FakeExerciseLibraryRepository()
        repo.items["workoutx-1"] = {
            "id": "workoutx-1",
            "owner_id": None,
            "name": "Press banca",
            "video_url": "https://api.workoutxapp.com/v1/gifs/0001.gif",
        }
        service = ExerciseLibraryService(repo)

        with patch(
            "app.modules.exercise_library.application.exercise_library_service.WorkoutXClient"
        ) as mock_client_cls, patch(
            "app.modules.exercise_library.application.exercise_library_service.save_bytes"
        ) as mock_save_bytes:
            mock_client_cls.return_value.fetch_gif_bytes.return_value = b"gif-bytes"
            mock_save_bytes.return_value = "/uploads/exercise_library/platform/workoutx-1.gif"

            url = await service.get_platform_video_url("workoutx-1")

        self.assertEqual(url, "/uploads/exercise_library/platform/workoutx-1.gif")
        mock_client_cls.return_value.fetch_gif_bytes.assert_called_once_with(
            "https://api.workoutxapp.com/v1/gifs/0001.gif"
        )
        # The repository's stored video_url is rewritten to the cached path.
        self.assertEqual(
            repo.items["workoutx-1"]["video_url"],
            "/uploads/exercise_library/platform/workoutx-1.gif",
        )

    async def test_get_platform_video_url_reuses_an_already_cached_gif(self):
        repo = _FakeExerciseLibraryRepository()
        repo.items["workoutx-1"] = {
            "id": "workoutx-1",
            "owner_id": None,
            "name": "Press banca",
            "video_url": "/uploads/exercise_library/platform/workoutx-1.gif",
        }
        service = ExerciseLibraryService(repo)

        with patch(
            "app.modules.exercise_library.application.exercise_library_service.WorkoutXClient"
        ) as mock_client_cls:
            url = await service.get_platform_video_url("workoutx-1")

        self.assertEqual(url, "/uploads/exercise_library/platform/workoutx-1.gif")
        mock_client_cls.return_value.fetch_gif_bytes.assert_not_called()

    async def test_get_platform_video_url_rejects_an_unknown_item(self):
        repo = _FakeExerciseLibraryRepository()
        service = ExerciseLibraryService(repo)

        with self.assertRaises(LookupError):
            await service.get_platform_video_url("workoutx-missing")

    async def test_delete_item_removes_it(self):
        repo = _FakeExerciseLibraryRepository()
        service = ExerciseLibraryService(repo)
        item = await service.create_item("owner-1", {"name": "Sentadilla"})

        await service.delete_item("owner-1", item["id"])

        self.assertEqual(await service.list_items("owner-1"), [])


if __name__ == "__main__":
    unittest.main()
