from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from typing import Optional
from datetime import datetime
from ..core.deps import get_current_user, get_db
from ..schemas.appointments import AppointmentIn, AppointmentUpdate, AppointmentOut
from ..schemas.pagination import PaginationParams, Page

router = APIRouter(prefix="/appointments", tags=["appointments"])

def as_oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

def serialize(a: dict) -> AppointmentOut:
    return AppointmentOut(
        id=str(a["_id"]),
        patient_id=str(a["patient_id"]),
        start=a["start"],
        end=a["end"],
        mode=a["mode"],
        status=a["status"],
        payment_status=a.get("payment_status", "unpaid"),
        video_room_url=a.get("video_room_url"),
        notes=a.get("notes"),
        owner_id=str(a["owner_id"]),
    )

@router.get("", response_model=Page[AppointmentOut])
async def list_appointments(
    pagination: PaginationParams = Depends(),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current=Depends(get_current_user),
    db=Depends(get_db),
):
    filters = {"owner_id": ObjectId(current["sub"])}
    if date_from or date_to:
        filters["start"] = {}
        if date_from: filters["start"]["$gte"] = date_from
        if date_to:   filters["start"]["$lte"] = date_to
    if patient_id:
        filters["patient_id"] = as_oid(patient_id)
    if status:
        filters["status"] = status

    total = await db.appointments.count_documents(filters)
    cursor = (
        db.appointments
        .find(filters)
        .sort("start", 1)
        .skip((pagination.page - 1) * pagination.limit)
        .limit(pagination.limit)
    )
    items = [serialize(a) async for a in cursor]
    return Page(items=items, page=pagination.page, limit=pagination.limit, total=total)

@router.post("", response_model=AppointmentOut, status_code=201)
async def create_appointment(payload: AppointmentIn, current=Depends(get_current_user), db=Depends(get_db)):
    # Validar que el paciente exista y pertenezca a la nutrióloga
    p = await db.patients.find_one({"_id": as_oid(payload.patient_id), "owner_id": ObjectId(current["sub"])})
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    doc = payload.dict()
    doc["patient_id"] = as_oid(payload.patient_id)
    doc["owner_id"] = ObjectId(current["sub"])
    res = await db.appointments.insert_one(doc)
    created = await db.appointments.find_one({"_id": res.inserted_id})
    return serialize(created)

@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(appointment_id: str, current=Depends(get_current_user), db=Depends(get_db)):
    oid = as_oid(appointment_id)
    a = await db.appointments.find_one({"_id": oid, "owner_id": ObjectId(current["sub"])})
    if not a:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return serialize(a)

@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(appointment_id: str, payload: AppointmentUpdate, current=Depends(get_current_user), db=Depends(get_db)):
    oid = as_oid(appointment_id)
    update = {k: v for k, v in payload.dict().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Si viene patient_id en update (no está en schema), se puede añadir validación similar al create
    await db.appointments.update_one({"_id": oid, "owner_id": ObjectId(current["sub"])}, {"$set": update})
    a = await db.appointments.find_one({"_id": oid, "owner_id": ObjectId(current["sub"])})
    if not a:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return serialize(a)

@router.delete("/{appointment_id}")
async def delete_appointment(appointment_id: str, current=Depends(get_current_user), db=Depends(get_db)):
    oid = as_oid(appointment_id)
    res = await db.appointments.delete_one({"_id": oid, "owner_id": ObjectId(current["sub"])})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"ok": True}
