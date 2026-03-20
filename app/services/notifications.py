from typing import Dict, Any, List, Optional
from bson import ObjectId
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.notify import send_push_to_tokens

async def notify_appointment_event(
    db: AsyncIOMotorDatabase,
    *,
    owner_id: ObjectId,
    appt: Dict[str, Any],
    event_type: str,   # "appointment_created" | "appointment_updated" | "appointment_reminder"...
) -> None:
    """Envía una push al owner por un evento de cita."""
    # tokens del owner
    tokens: List[str] = [
        d["token"] async for d in db.devices.find({"user_id": owner_id}, {"token": 1, "_id": 0})
    ]
    if not tokens:
        return

    # obtener paciente (si es ObjectId)
    patient = None
    pid = appt.get("patient_id")
    if isinstance(pid, ObjectId):
        patient = await db.patients.find_one({"_id": pid}, {"name": 1, "email": 1})

    # título/cuerpo
    title = "Cita"  # default
    if event_type == "appointment_created":
        title = "Nueva cita creada"
    elif event_type == "appointment_updated":
        title = "Cita actualizada"

    start: Optional[datetime] = appt.get("start")
    start_txt = start.isoformat() if isinstance(start, datetime) else ""

    body = f"Paciente: {patient.get('name') if patient else ''} • {start_txt}"

    # data para navegación en la app
    data = {
        "type": event_type,
        "appointmentId": str(appt.get("_id")),
        "patientId": str(pid) if isinstance(pid, ObjectId) else (pid or ""),
    }

    # dispara push
    send_push_to_tokens(tokens, title, body, data)
