from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from typing import Optional
from ..core.deps import get_current_user, get_db
from ..schemas.patients import PatientIn, PatientUpdate, PatientOut
from ..schemas.pagination import PaginationParams, Page

router = APIRouter(prefix="/patients", tags=["patients"])

def as_oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

def serialize(p: dict) -> PatientOut:
    return PatientOut(
        id=str(p["_id"]),
        name=p["name"],
        age=p.get("age"),
        sex=p.get("sex"),
        height_cm=p.get("height_cm"),
        allergies=p.get("allergies"),
        notes=p.get("notes"),
        owner_id=str(p["owner_id"]),
    )

@router.get("", response_model=Page[PatientOut])
async def list_patients(
    pagination: PaginationParams = Depends(),
    q: Optional[str] = Query(None, description="Búsqueda por nombre (regex, case-insensitive)"),
    current=Depends(get_current_user),
    db=Depends(get_db),
):
    owner_id = ObjectId(current["sub"])
    filters = {"owner_id": owner_id}

    if q:
        # Búsqueda simple por nombre (insensible a mayúsculas)
        filters["name"] = {"$regex": q, "$options": "i"}

    total = await db.patients.count_documents(filters)
    cursor = (
        db.patients
        .find(filters)
        .sort("name", 1)
        .skip((pagination.page - 1) * pagination.limit)
        .limit(pagination.limit)
    )
    items = [serialize(p) async for p in cursor]
    return Page(items=items, page=pagination.page, limit=pagination.limit, total=total)

@router.post("", response_model=PatientOut, status_code=201)
async def create_patient(payload: PatientIn, current=Depends(get_current_user), db=Depends(get_db)):
    doc = payload.dict()
    doc["owner_id"] = ObjectId(current["sub"])
    res = await db.patients.insert_one(doc)
    created = await db.patients.find_one({"_id": res.inserted_id})
    return serialize(created)

@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: str, current=Depends(get_current_user), db=Depends(get_db)):
    oid = as_oid(patient_id)
    p = await db.patients.find_one({"_id": oid, "owner_id": ObjectId(current["sub"])})
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return serialize(p)

@router.patch("/{patient_id}", response_model=PatientOut)
async def update_patient(patient_id: str, payload: PatientUpdate, current=Depends(get_current_user), db=Depends(get_db)):
    oid = as_oid(patient_id)
    update = {k: v for k, v in payload.dict().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db.patients.update_one(
        {"_id": oid, "owner_id": ObjectId(current["sub"])},
        {"$set": update}
    )
    p = await db.patients.find_one({"_id": oid, "owner_id": ObjectId(current["sub"])})
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return serialize(p)

@router.delete("/{patient_id}")
async def delete_patient(patient_id: str, current=Depends(get_current_user), db=Depends(get_db)):
    oid = as_oid(patient_id)
    res = await db.patients.delete_one({"_id": oid, "owner_id": ObjectId(current["sub"])})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"ok": True}
