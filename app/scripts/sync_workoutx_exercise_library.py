"""Syncs the platform-curated ("Biblioteca pública") exercise library from
WorkoutX's API into the `exercise_library` collection, upserted with
`owner_id: None` — the same marker `content_articles` uses for platform
content (see `seed_content_library.py`). Idempotent: re-running upserts
every exercise by a stable `_id` derived from WorkoutX's own exercise id, so
it never creates duplicates.

Unlike MuscleWiki, WorkoutX's `GET /v1/exercises` returns full exercise data
(name, gifUrl, bodyPart, equipment, instructions) in one call — no separate
per-exercise detail call needed. A full library (~1,327 exercises) costs
only ~14 list calls at 100/page, comfortably inside the free tier's
500-calls/month quota. `--limit` still exists to cap it further if wanted.

`video_url` is stored as WorkoutX's raw `gifUrl` (e.g.
"https://api.workoutxapp.com/v1/gifs/0001.gif") — NOT directly loadable by a
client, since it 401s without our API key. It gets lazily cached into our
own `/uploads` storage (and rewritten in Mongo) the first time
`GET /exercise-library/platform/{item_id}/video-url` is called for that
item — see `ExerciseLibraryService.get_platform_video_url`.

Free tier note: WorkoutX's own FAQ states the free plan is for "evaluation
and small projects" — commercial production use needs a paid plan. Revisit
before relying on this at real scale.

Requires `WORKOUTX_API_KEY` in `.env`. Not run automatically — invoke
manually:
    python -m app.scripts.sync_workoutx_exercise_library --limit 20
"""
import argparse
import asyncio

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db
from app.modules.exercise_library.infrastructure.workoutx_client import WorkoutXClient

_PAGE_SIZE = 100


def _to_exercise_library_doc(raw: dict) -> dict:
    notes_parts = []
    if raw.get("bodyPart"):
        notes_parts.append(f"Zona: {raw['bodyPart']}")
    if raw.get("target"):
        notes_parts.append(f"Músculo objetivo: {raw['target']}")
    if raw.get("equipment"):
        notes_parts.append(f"Equipo: {raw['equipment']}")
    instructions = raw.get("instructions") or []
    if instructions:
        notes_parts.append(" ".join(str(step) for step in instructions))
    return {
        "_id": f"workoutx-{raw['id']}",
        "owner_id": None,
        "name": (raw.get("name") or "").strip(),
        "default_sets": None,
        "default_reps": None,
        "default_weight_kg": None,
        "default_duration_seconds": None,
        "default_rest_seconds": None,
        "video_url": raw.get("gifUrl"),
        "notes": " · ".join(notes_parts) if notes_parts else None,
    }


async def sync(limit: int | None) -> int:
    client = WorkoutXClient()
    db = get_db()
    synced = 0
    offset = 0
    while True:
        page = client.list_exercises(limit=_PAGE_SIZE, offset=offset)
        results = page.get("data", [])
        if not results:
            break
        for raw in results:
            if limit is not None and synced >= limit:
                return synced
            doc = _to_exercise_library_doc(raw)
            if not doc["name"]:
                continue
            await db.exercise_library.update_one(
                {"_id": doc["_id"]}, {"$set": doc}, upsert=True
            )
            synced += 1
        offset += _PAGE_SIZE
        if offset >= page.get("total", 0):
            break
    return synced


async def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max exercises to sync. Omit for a full sync (~14 calls, well inside the free quota).",
    )
    args = parser.parse_args()

    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        synced = await sync(args.limit)
        print(f"Synced {synced} platform exercises from WorkoutX.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
