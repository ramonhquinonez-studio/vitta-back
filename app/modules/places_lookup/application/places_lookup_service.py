from ..domain.entities import NearbyPlace
from ..domain.repositories import PlacesRepository


class PlacesLookupService:
    def __init__(self, repository: PlacesRepository):
        self._repository = repository

    async def search_nearby(
        self, lat: float, lon: float, *, radius_m: int = 1500
    ) -> list[NearbyPlace]:
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid coordinates")
        if not (100 <= radius_m <= 20000):
            raise ValueError("radius_m must be between 100 and 20000")
        return await self._repository.search_nearby(lat, lon, radius_m=radius_m)
