import math

import requests

from ..domain.entities import NearbyPlace

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_AMENITIES = "restaurant|fast_food|cafe"
# Overpass's Apache front-end returns a bare 406 for the default
# `python-requests` User-Agent (no error body explaining why) — confirmed
# live. Their usage policy asks for an identifiable UA anyway.
_HEADERS = {"User-Agent": "VittaNutriApp/1.0 (nutri_back places_lookup)"}


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class OverpassPlacesRepository:
    """Looks up real nearby restaurants/fast-food/cafés from OpenStreetMap's
    free, keyless Overpass API — no API key, no billing, community-sourced
    data. `fast_food` is included alongside `restaurant` because many
    everyday Mexican eating-out spots (taquerías, loncherías) are tagged
    that way in OSM, not `restaurant`.
    """

    async def search_nearby(
        self, lat: float, lon: float, *, radius_m: int = 1500, limit: int = 20
    ) -> list[NearbyPlace]:
        query = (
            f'[out:json][timeout:25];'
            f'(node["amenity"~"^({_AMENITIES})$"](around:{radius_m},{lat},{lon});'
            f'way["amenity"~"^({_AMENITIES})$"](around:{radius_m},{lat},{lon}););'
            f"out center {limit * 3};"
        )
        try:
            response = requests.post(
                _OVERPASS_URL, data={"data": query}, headers=_HEADERS, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Overpass API request failed: {exc}") from exc

        places: list[NearbyPlace] = []
        for element in response.json().get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name")
            if not name:
                continue
            place_lat = element.get("lat") or element.get("center", {}).get("lat")
            place_lon = element.get("lon") or element.get("center", {}).get("lon")
            if place_lat is None or place_lon is None:
                continue
            address = None
            street = tags.get("addr:street")
            number = tags.get("addr:housenumber")
            if street:
                address = f"{street} {number}".strip() if number else street
            places.append(
                NearbyPlace(
                    name=name,
                    address=address,
                    cuisine=tags.get("cuisine"),
                    lat=place_lat,
                    lon=place_lon,
                    distance_m=_haversine_m(lat, lon, place_lat, place_lon),
                )
            )

        places.sort(key=lambda p: p.distance_m or 0)
        return places[:limit]
