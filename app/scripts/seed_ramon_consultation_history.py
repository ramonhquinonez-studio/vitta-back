"""One-off data-seeding script: creates a real consultation history for
rhq.castro@gmail.com (Ramon Quinonez) — past appointments, each linked via
the new Appointment.plan_id / Appointment.body_composition_id fields to a
real plan and a real InBody-style body_composition record, so the
"Historial de consultas" screen can render real data instead of mocks.

Run with: PYTHONPATH=. .venv/bin/python -m app.scripts.seed_ramon_consultation_history
"""
import asyncio
from datetime import datetime, timedelta

from bson import ObjectId

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db

OWNER_ID = ObjectId("6a7d77ed114c9a911c281647")  # pro_demo@nutri.app
PATIENT_ID = ObjectId("6a7d79ea71f440e8e09421d6")  # Ramon Quinonez
PLAN_ID = ObjectId("6a7d77ee114c9a911c28164b")

# (days_ago, mode, status, note, weight_kg, body_fat_pct, skeletal_muscle_kg, bmi, link_plan)
CONSULTATIONS = [
    (
        58,
        "onsite",
        "confirmed",
        "Primera consulta. Se evalua composicion corporal y se establece "
        "plan alimenticio inicial orientado a perdida de grasa y "
        "mantenimiento de masa muscular.",
        75.0,
        24.5,
        31.2,
        26.1,
        False,
    ),
    (
        44,
        "online",
        "confirmed",
        "Control quincenal. Buena adherencia al plan. Se mantienen las "
        "indicaciones actuales y se refuerza la hidratacion diaria.",
        72.8,
        23.1,
        31.5,
        25.3,
        True,
    ),
    (
        30,
        "onsite",
        "confirmed",
        "Ajuste de plan. Se incrementa la ingesta de proteina "
        "post-entrenamiento y se agregan mas vegetales de hoja verde en "
        "almuerzo y cena.",
        70.5,
        21.8,
        31.9,
        24.5,
        True,
    ),
    (
        3,
        "online",
        "confirmed",
        "Seguimiento mensual. Progreso satisfactorio: perdida de peso "
        "gradual y sostenible con mejora en la composicion corporal y "
        "aumento de masa muscular.",
        68.0,
        20.4,
        32.3,
        23.7,
        True,
    ),
]


async def main() -> None:
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        db = get_db()
        now = datetime.utcnow()

        plan = await db.plans.find_one({"_id": PLAN_ID})
        if plan is None:
            raise RuntimeError(f"Plan {PLAN_ID} not found - run seed_ramon_real_plan first")

        existing = await db.appointments.count_documents({"patient_id": PATIENT_ID})
        if existing:
            print(f"Ramon already has {existing} appointment(s) - skipping (not idempotent, run manually cleaned if needed).")
            return

        created = 0
        for days_ago, mode, status, note, weight, fat_pct, muscle_kg, bmi, link_plan in CONSULTATIONS:
            at = now - timedelta(days=days_ago)

            scan_doc = {
                "owner_id": OWNER_ID,
                "patient_id": PATIENT_ID,
                "at": at,
                "provider": "InBody 270",
                "metrics": {
                    "weight_kg": weight,
                    "body_fat_pct": fat_pct,
                    "skeletal_muscle_kg": muscle_kg,
                    "bmi": bmi,
                },
                "attachment_url": None,
                "attachment_type": None,
                "created_at": now,
            }
            scan_result = await db.body_compositions.insert_one(scan_doc)

            appointment_doc = {
                "owner_id": OWNER_ID,
                "patient_id": PATIENT_ID,
                "start": at,
                "end": at + timedelta(minutes=45),
                "mode": mode,
                "status": status,
                "note": note,
                "plan_id": PLAN_ID if link_plan else None,
                "body_composition_id": scan_result.inserted_id,
                "no_sync": True,
                "created_at": now,
                "updated_at": now,
            }
            await db.appointments.insert_one(appointment_doc)
            created += 1

        print(f"Seeded {created} consultations (appointments + linked body_compositions) for Ramon.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
