from datetime import datetime, timedelta, timezone
from app.db.mongo import get_db
from app.core.notify import send_push_to_tokens
from app.core.config import settings
from bson import ObjectId

async def run_reminders():
    db = get_db()
    now = datetime.now(timezone.utc)
    target_from = now + timedelta(minutes=settings.NOTIFY_BEFORE_MINUTES)
    target_to   = target_from + timedelta(minutes=1)

    # Marca simple para no duplicar: field 'reminder_sent': True
    cursor = db.appointments.find({
        "start": {"$gte": target_from, "$lt": target_to},
        "status": {"$in": ["pending","confirmed"]},
        "reminder_sent": {"$ne": True},
    })

    async for appt in cursor:
        owner_id = appt.get("owner_id")
        tokens = [d["token"] async for d in db.devices.find({"user_id": owner_id}, {"token":1, "_id":0})]
        if tokens:
            patient = None
            pid = appt.get("patient_id")
            if isinstance(pid, ObjectId):
                patient = await db.patients.find_one({"_id": pid}, {"name":1})
            title = "Recordatorio de cita"
            body = f"{patient.get('name') if patient else 'Paciente'} en ~{settings.NOTIFY_BEFORE_MINUTES} min"
            send_push_to_tokens(tokens, title, body, {"type":"appointment_reminder", "appointmentId": str(appt["_id"])})

        await db.appointments.update_one({"_id": appt["_id"]}, {"$set": {"reminder_sent": True}})
