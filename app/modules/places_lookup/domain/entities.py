from dataclasses import dataclass


@dataclass(frozen=True)
class NearbyPlace:
    name: str
    address: str | None
    cuisine: str | None
    lat: float
    lon: float
    distance_m: float | None
