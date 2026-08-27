"""Thin client for WorkoutX's exercise API (workoutxapp.com) — the free-tier
alternative to MuscleWiki (500 requests/month, no credit card to sign up).
Their own FAQ states the free tier is for "evaluation and small projects";
commercial production use needs a paid plan.

Auth: an `X-WorkoutX-Key` header. Unlike MuscleWiki, `GET /v1/exercises`
appears to return full exercise data (name, gifUrl, bodyPart, equipment,
instructions) in one call — no separate per-exercise detail call needed,
which matters a lot for staying inside a 500-call/month free quota.

NOT YET CONFIRMED: whether the `gifUrl` values returned by the API are
directly loadable with no auth (like their public marketing-site GIFs,
confirmed publicly loadable at workoutxapp.com/gifs/{id}.gif) or require the
same API key / a minted token to fetch, the way MuscleWiki's `/stream/`
video paths do. Needs a real API key to test — do that before assuming
`gif_url` can be stored and used as-is.
"""
import requests

from app.core.config import settings

_BASE_URL = "https://api.workoutxapp.com"


class WorkoutXClient:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.WORKOUTX_API_KEY
        if not self._api_key:
            raise RuntimeError(
                "WORKOUTX_API_KEY is not set — add it to .env before using this client."
            )

    def _headers(self) -> dict:
        return {"X-WorkoutX-Key": self._api_key}

    def list_exercises(self, *, limit: int = 100, offset: int = 0) -> dict:
        response = requests.get(
            f"{_BASE_URL}/v1/exercises",
            headers=self._headers(),
            params={"limit": limit, "offset": offset},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def fetch_gif_bytes(self, gif_url: str) -> bytes:
        """Fetches the raw GIF bytes for a `gifUrl` value returned by
        `list_exercises` — those URLs 401 without our key attached."""
        response = requests.get(gif_url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.content
