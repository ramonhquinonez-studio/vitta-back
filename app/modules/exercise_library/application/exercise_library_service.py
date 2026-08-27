from app.core.storage import save_bytes

from ..domain.repositories import ExerciseLibraryRepository
from ..infrastructure.workoutx_client import WorkoutXClient


class ExerciseLibraryService:
    def __init__(self, repository: ExerciseLibraryRepository):
        self._repository = repository

    async def list_items(self, owner_id: str) -> list[dict]:
        return await self._repository.list_for_owner(owner_id)

    async def list_platform_items(self) -> list[dict]:
        return await self._repository.list_platform_items()

    async def get_platform_video_url(self, item_id: str) -> str:
        """Returns a relative `/uploads/...` URL for the item's GIF, caching
        it locally from WorkoutX on first request. WorkoutX's own GIF URLs
        require our permanent API key on every fetch (no short-lived-token
        option like MuscleWiki), and the free tier is capped at 500 calls a
        month — caching means we ever spend at most one call per exercise,
        not one per view."""
        item = await self._repository.get_platform_item(item_id)
        if item is None or not item.get("video_url"):
            raise LookupError("Exercise not found")
        video_url = item["video_url"]
        if video_url.startswith("/uploads/"):
            return video_url  # already cached from a prior call
        cached_url = self._cache_platform_gif(item_id, video_url)
        await self._repository.update_platform_item_video_url(item_id, cached_url)
        return cached_url

    def _cache_platform_gif(self, item_id: str, workoutx_gif_url: str) -> str:
        gif_bytes = WorkoutXClient().fetch_gif_bytes(workoutx_gif_url)
        return save_bytes(
            gif_bytes,
            subfolder="exercise_library/platform",
            filename=f"{item_id}.gif",
        )

    async def create_item(self, owner_id: str, payload: dict) -> dict:
        if not payload.get("name"):
            raise ValueError("name is required")
        return await self._repository.create_for_owner(owner_id, payload)

    async def delete_item(self, owner_id: str, item_id: str) -> None:
        deleted = await self._repository.delete_for_owner(owner_id, item_id)
        if not deleted:
            raise LookupError("Exercise not found")
