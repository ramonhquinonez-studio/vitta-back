from typing import Protocol

from .entities import NearbyPlace


class PlacesRepository(Protocol):
    async def search_nearby(
        self, lat: float, lon: float, *, radius_m: int = 1500, limit: int = 20
    ) -> list[NearbyPlace]:
        ...
