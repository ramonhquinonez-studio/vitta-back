from pydantic import BaseModel
from typing import Optional


class NearbyPlaceOut(BaseModel):
    name: str
    address: Optional[str] = None
    cuisine: Optional[str] = None
    lat: float
    lon: float
    distance_m: Optional[float] = None
