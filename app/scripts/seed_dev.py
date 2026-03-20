import asyncio
from datetime import datetime, timedelta
import random
from bson import ObjectId

from app.core.config import settings
from app.core.security import hash_password
from app.db.mongo import connect_to_mongo, get_db, close_mongo_connection


async def upsert_user(email: str, password: str, role: str = "patient") -> ObjectId:
    db = get_db()
    u = await db.users.find_one({"email": email})
    if u:
        return u["_id"]
    now = datetime.utcnow()
    res = await db.users.insert_one({
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "created_at": now,
        "updated_at": now,
    })
    return res.inserted_id


async def ensure_patient_for_user(user_id: ObjectId, owner_id: ObjectId) -> ObjectId:
    db = get_db()
    p = await db.patients.find_one({"user_id": user_id})
    if p:
        return p["_id"]
    res = await db.patients.insert_one({
        "user_id": user_id,
        "owner_id": owner_id,
        "name": "Paciente Demo",
        "age": 30,
        "sex": "other",
        "height_cm": 170,
        "allergies": ["lactosa"],
        "created_at": datetime.utcnow(),
    })
    return res.inserted_id


async def ensure_plan(owner_id: ObjectId) -> ObjectId:
    db = get_db()
    p = await db.plans.find_one({"owner_id": owner_id, "name": "Plan Semanal Demo"})
    if p:
        return p["_id"]
    now = datetime.utcnow()
    res = await db.plans.insert_one({
        "owner_id": owner_id,
        "name": "Plan Semanal Demo",
        "goal": "maintenance",
        "duration_days": 7,
        "meals": [
            {
                "title": "Desayuno",
                "items": [
                    {"name": "Avenaa", "qty": 60, "unit": "g"},
                    {"name": "Plátano", "qty": 1, "unit": "pz"},
                ],
            },
            {
                "title": "Comida",
                "items": [
                    {"name": "Pechuga de pollo", "qty": 150, "unit": "g"},
                    {"name": "Arroz", "qty": 80, "unit": "g"},
                ],
            },
        ],
        "created_at": now,
        "updated_at": now,
    })
    return res.inserted_id


async def ensure_assignment(owner_id: ObjectId, patient_id: ObjectId, plan_id: ObjectId) -> None:
    db = get_db()
    existing = await db.plan_assignments.find_one({
        "owner_id": owner_id,
        "patient_id": patient_id,
        "plan_id": plan_id,
    })
    if existing:
        return
    await db.plan_assignments.insert_one({
        "owner_id": owner_id,
        "patient_id": patient_id,
        "plan_id": plan_id,
        "assigned_at": datetime.utcnow(),
    })


async def seed_appointments(owner_id: ObjectId, patient_id: ObjectId) -> None:
    db = get_db()
    now = datetime.utcnow()
    # Crea 3 citas próximas sin solape
    slots = [now + timedelta(days=i, hours=10) for i in range(1, 4)]
    for i, start in enumerate(slots):
        end = start + timedelta(minutes=45)
        exists = await db.appointments.find_one({"owner_id": owner_id, "patient_id": patient_id, "start": start})
        if exists:
            continue
        await db.appointments.insert_one({
            "owner_id": owner_id,
            "patient_id": patient_id,
            "start": start,
            "end": end,
            "mode": "online" if i % 2 == 0 else "onsite",
            "status": "confirmed" if i == 0 else "pending",
            "note": "Cita demo",
            "created_at": now,
            "updated_at": now,
        })


async def seed_measurements(owner_id: ObjectId, patient_id: ObjectId) -> None:
    db = get_db()
    now = datetime.utcnow()
    # Crea una serie de 10 mediciones diarias hacia atrás
    base_weight = 80.0
    base_fat = 28.0
    for i in range(10, -1, -1):
        at = now - timedelta(days=i)
        # Pequeñas variaciones
        weight = base_weight - (10 - i) * 0.3 + random.uniform(-0.2, 0.2)
        body_fat = base_fat - (10 - i) * 0.2 + random.uniform(-0.3, 0.3)
        exists = await db.measurements.find_one({"patient_id": patient_id, "at": {"$gte": at.replace(hour=0, minute=0), "$lte": at.replace(hour=23, minute=59)}})
        if exists:
            continue
        await db.measurements.insert_one({
            "owner_id": owner_id,
            "patient_id": patient_id,
            "at": at,
            "weight_kg": round(weight, 2),
            "body_fat_pct": round(body_fat, 2),
            "waist_cm": 90 + (10 - i) * -0.5 + random.uniform(-0.5, 0.5),
            "notes": "auto-seed",
            "created_at": now,
        })


async def seed_prescriptions(owner_id: ObjectId, patient_id: ObjectId) -> None:
    db = get_db()
    now = datetime.utcnow()
    exists = await db.prescriptions.find_one({"patient_id": patient_id})
    if exists:
        return
    await db.prescriptions.insert_one({
        "owner_id": owner_id,
        "patient_id": patient_id,
        "at": now - timedelta(days=2),
        "medications": [
            {"name": "Metformina", "dose": "850 mg", "frequency": "cada 12h", "duration": "30 días"},
            {"name": "Omega-3", "dose": "1 cápsula", "frequency": "con desayuno", "duration": "30 días"},
        ],
        "notes": "Beber 2L de agua al día. Vigilar glucemias.",
    })


async def seed_recipe_collections(owner_id: ObjectId) -> None:
    db = get_db()
    now = datetime.utcnow()
    exists = await db.recipe_collections.find_one({"owner_id": owner_id})
    if exists:
        return
    await db.recipe_collections.insert_one({
        "owner_id": owner_id,
        "title": "Recetario Ligero",
        "description": "Platillos sencillos y balanceados.",
        "recipes": [
            {
                "title": "Ensalada de quinua",
                "ingredients": [
                    {"name": "Quinua", "qty": 80, "unit": "g"},
                    {"name": "Tomate", "qty": 1, "unit": "pz"},
                    {"name": "Aguacate", "qty": 0.5, "unit": "pz"},
                ],
                "steps": ["Cocer la quinua", "Picar vegetales", "Mezclar y servir"],
            },
            {
                "title": "Wrap de pollo",
                "ingredients": [
                    {"name": "Tortilla integral", "qty": 1, "unit": "pz"},
                    {"name": "Pechuga de pollo", "qty": 120, "unit": "g"},
                ],
                "steps": ["Cocinar pollo", "Armar wrap"],
            },
        ],
        "updated_at": now,
    })


async def seed_education_videos(owner_id: ObjectId) -> None:
    db = get_db()
    now = datetime.utcnow()
    exists = await db.education_videos.find_one({"owner_id": owner_id})
    if exists:
        return
    await db.education_videos.insert_many([
        {
            "owner_id": owner_id,
            "title": "Cómo leer etiquetas nutrimentales",
            "description": "Guía rápida para elegir mejor en el súper.",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "thumbnail_url": None,
            "published_at": now - timedelta(days=5),
        },
        {
            "owner_id": owner_id,
            "title": "Porciones y plato del bien comer",
            "description": "Conceptos clave para balancear tus comidas.",
            "url": "https://www.youtube.com/watch?v=Zi_XLOBDo_Y",
            "thumbnail_url": None,
            "published_at": now - timedelta(days=1),
        },
    ])


async def seed_clinical_history(owner_id: ObjectId, patient_id: ObjectId) -> None:
    db = get_db()
    now = datetime.utcnow()
    notes_exists = await db.clinical_notes.find_one({"patient_id": patient_id})
    if not notes_exists:
        await db.clinical_notes.insert_many([
            {
                "owner_id": owner_id,
                "patient_id": patient_id,
                "at": now - timedelta(days=15),
                "author": "Lic. Nutrióloga Demo",
                "note": "Se observa buena adherencia. Ajustar colación vespertina.",
                "attachments": [],
            },
            {
                "owner_id": owner_id,
                "patient_id": patient_id,
                "at": now - timedelta(days=7),
                "author": "Lic. Nutrióloga Demo",
                "note": "Revisar tolerancia a lácteos. Sugerir alternativas sin lactosa.",
                "attachments": [],
            },
        ])

    comp_exists = await db.body_compositions.find_one({"patient_id": patient_id})
    if not comp_exists:
        await db.body_compositions.insert_one({
            "owner_id": owner_id,
            "patient_id": patient_id,
            "at": now - timedelta(days=10),
            "provider": "InBody",
            "metrics": {
                "weight_kg": 78.4,
                "body_fat_pct": 27.1,
                "skeletal_muscle_kg": 33.5,
                "visceral_fat_level": 9,
            },
            "attachment_url": None,
        })


async def main():
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        # Usuario pro (nutriólogo)
        pro_email = "pro_demo@nutri.app"
        pro_pwd = "123456"
        pro_id = await upsert_user(pro_email, pro_pwd, role="pro")

        # Usuario paciente
        patient_email = "patient_demo@nutri.app"
        patient_pwd = "123456"
        patient_user_id = await upsert_user(patient_email, patient_pwd, role="patient")

        # Paciente ligado a user y owner (pro)
        patient_id = await ensure_patient_for_user(patient_user_id, pro_id)

        # Plan básico del owner y asignación al paciente
        plan_id = await ensure_plan(pro_id)
        await ensure_assignment(pro_id, patient_id, plan_id)

        # Citas de ejemplo
        await seed_appointments(pro_id, patient_id)
        # Mediciones de ejemplo para el dashboard de progreso
        await seed_measurements(pro_id, patient_id)
        # Prescripción, recetarios, videos, e historial clínico de ejemplo
        await seed_prescriptions(pro_id, patient_id)
        await seed_recipe_collections(pro_id)
        await seed_education_videos(pro_id)
        await seed_clinical_history(pro_id, patient_id)

        print("=== Seed listo ===")
        print(f"PRO:    {pro_email} / {pro_pwd}")
        print(f"PATIENT:{patient_email} / {patient_pwd}")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
