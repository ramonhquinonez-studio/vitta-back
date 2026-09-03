from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_user, require_role
from app.schemas.places_lookup import NearbyPlaceOut

from ..application.places_lookup_service import PlacesLookupService
from ..infrastructure.overpass_places_repository import OverpassPlacesRepository

router = APIRouter(
    prefix="/places",
    tags=["places_lookup"],
    dependencies=[Depends(require_role("nutritionist"))],
)


def get_places_lookup_service() -> PlacesLookupService:
    return PlacesLookupService(OverpassPlacesRepository())


@router.get("/nearby", response_model=list[NearbyPlaceOut])
async def search_nearby_places(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_m: int = Query(1500, ge=100, le=20000),
    current=Depends(get_current_user),
    service: PlacesLookupService = Depends(get_places_lookup_service),
):
    try:
        places = await service.search_nearby(lat, lon, radius_m=radius_m)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [
        NearbyPlaceOut(
            name=p.name,
            address=p.address,
            cuisine=p.cuisine,
            lat=p.lat,
            lon=p.lon,
            distance_m=p.distance_m,
        )
        for p in places
    ]
