import unittest

from app.modules.places_lookup.application.places_lookup_service import PlacesLookupService
from app.modules.places_lookup.domain.entities import NearbyPlace


class _FakePlacesRepository:
    def __init__(self):
        self.last_call = None

    async def search_nearby(self, lat, lon, *, radius_m=1500, limit=20):
        self.last_call = {"lat": lat, "lon": lon, "radius_m": radius_m}
        return [
            NearbyPlace(
                name="La Casa del Pavo",
                address="Eje Central 46",
                cuisine="mexican",
                lat=lat,
                lon=lon,
                distance_m=120.0,
            )
        ]


class PlacesLookupServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_search_nearby_delegates_to_the_repository(self):
        repository = _FakePlacesRepository()
        service = PlacesLookupService(repository)

        result = await service.search_nearby(19.4326, -99.1332, radius_m=800)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "La Casa del Pavo")
        self.assertEqual(repository.last_call, {"lat": 19.4326, "lon": -99.1332, "radius_m": 800})

    async def test_search_nearby_rejects_invalid_latitude(self):
        repository = _FakePlacesRepository()
        service = PlacesLookupService(repository)

        with self.assertRaises(ValueError):
            await service.search_nearby(120.0, -99.1332)

    async def test_search_nearby_rejects_invalid_longitude(self):
        repository = _FakePlacesRepository()
        service = PlacesLookupService(repository)

        with self.assertRaises(ValueError):
            await service.search_nearby(19.4326, -200.0)

    async def test_search_nearby_rejects_radius_out_of_bounds(self):
        repository = _FakePlacesRepository()
        service = PlacesLookupService(repository)

        with self.assertRaises(ValueError):
            await service.search_nearby(19.4326, -99.1332, radius_m=50)

        with self.assertRaises(ValueError):
            await service.search_nearby(19.4326, -99.1332, radius_m=30000)


if __name__ == "__main__":
    unittest.main()
