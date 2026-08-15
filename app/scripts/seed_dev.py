import asyncio
import uuid
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


async def ensure_plan(owner_id: ObjectId, recipe_ids: dict[str, str]) -> ObjectId:
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
                "time": "08:00",
                "items": [
                    {
                        "name": "Avena",
                        "qty": 60,
                        "unit": "g",
                        "recipe_id": recipe_ids.get("Avena con plátano"),
                    },
                    {
                        "name": "Plátano",
                        "qty": 1,
                        "unit": "pz",
                        "recipe_id": recipe_ids.get("Avena con plátano"),
                    },
                ],
            },
            {
                "title": "Comida",
                "time": "13:30",
                "items": [
                    {
                        "name": "Pechuga de pollo",
                        "qty": 150,
                        "unit": "g",
                        "recipe_id": recipe_ids.get("Pollo con arroz al horno"),
                    },
                    {
                        "name": "Arroz",
                        "qty": 80,
                        "unit": "g",
                        "recipe_id": recipe_ids.get("Pollo con arroz al horno"),
                    },
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


async def ensure_demo_invite_code(owner_id: ObjectId) -> None:
    db = get_db()
    code = "DEMO2026"
    existing = await db.invite_codes.find_one({"code": code})
    if existing:
        return
    await db.invite_codes.insert_one({
        "code": code,
        "owner_id": owner_id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=365),
        "used_at": None,
        "used_by_user_id": None,
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


async def seed_recipe_collections(owner_id: ObjectId) -> dict[str, str]:
    db = get_db()
    now = datetime.utcnow()
    existing = await db.recipe_collections.find_one({"owner_id": owner_id})
    if existing:
        return {
            recipe.get("title"): recipe.get("id")
            for recipe in existing.get("recipes", [])
        }

    recipes = [
        {
            "id": uuid.uuid4().hex,
            "title": "Avena con plátano",
            "meal_type": "Desayuno",
            "minutes": 10,
            "portions": 1,
            "kcal": 320,
            "ingredients": [
                {"name": "Avena", "qty": 60, "unit": "g"},
                {"name": "Plátano", "qty": 1, "unit": "pz"},
                {"name": "Leche o agua", "qty": 200, "unit": "ml"},
            ],
            "steps": [
                "Hervir la leche o el agua.",
                "Agregar la avena y cocinar 3-5 minutos.",
                "Servir con el plátano rebanado.",
            ],
        },
        {
            "id": uuid.uuid4().hex,
            "title": "Pollo con arroz al horno",
            "meal_type": "Comida",
            "minutes": 35,
            "portions": 2,
            "kcal": 480,
            "ingredients": [
                {"name": "Pechuga de pollo", "qty": 150, "unit": "g"},
                {"name": "Arroz", "qty": 80, "unit": "g"},
                {"name": "Caldo de verduras", "qty": 200, "unit": "ml"},
            ],
            "steps": [
                "Sellar la pechuga de pollo en un sartén.",
                "Colocar el pollo y el arroz en un refractario con el caldo.",
                "Hornear a 200°C durante 25 minutos.",
            ],
        },
        {
            "id": uuid.uuid4().hex,
            "title": "Ensalada de quinua",
            "meal_type": "Comida",
            "minutes": 20,
            "portions": 2,
            "kcal": 410,
            "ingredients": [
                {"name": "Quinua", "qty": 80, "unit": "g"},
                {"name": "Tomate", "qty": 1, "unit": "pz"},
                {"name": "Aguacate", "qty": 0.5, "unit": "pz"},
            ],
            "steps": ["Cocer la quinua", "Picar vegetales", "Mezclar y servir"],
        },
        {
            "id": uuid.uuid4().hex,
            "title": "Wrap de pollo",
            "meal_type": "Cena",
            "minutes": 15,
            "portions": 1,
            "kcal": 390,
            "ingredients": [
                {"name": "Tortilla integral", "qty": 1, "unit": "pz"},
                {"name": "Pechuga de pollo", "qty": 120, "unit": "g"},
            ],
            "steps": ["Cocinar pollo", "Armar wrap"],
        },
    ]

    await db.recipe_collections.insert_one({
        "owner_id": owner_id,
        "title": "Recetario Ligero",
        "description": "Platillos sencillos y balanceados.",
        "recipes": recipes,
        "updated_at": now,
    })
    return {recipe["title"]: recipe["id"] for recipe in recipes}


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

async def seed_body_compositions(owner_id: ObjectId, patient_id: ObjectId) -> None:
    db = get_db()
    now = datetime.utcnow()
    exists = await db.body_compositions.find_one({"patient_id": patient_id})
    if exists:
        return

    # Historial de 4 escaneos InBody, del más antiguo al más reciente.
    scans = [
        {
            "days_ago": 60,
            "weight_kg": 78.4,
            "body_fat_pct": 27.1,
            "skeletal_muscle_kg": 32.8,
            "body_fat_mass_kg": 21.2,
            "total_body_water_l": 42.9,
            "protein_kg": 11.6,
            "minerals_kg": 3.9,
            "bmi": 25.6,
            "visceral_fat_level": 11,
            "bmr_kcal": 1610,
            "waist_hip_ratio": 0.97,
            "obesity_degree_pct": 116,
            "inbody_score": 74,
            "ideal_weight_kg": 71.7,
            "weight_control_kg": -6.7,
            "fat_control_kg": -6.7,
            "muscle_control_kg": 0.0,
            "grip_strength_left_kg": 28.5,
            "grip_strength_right_kg": 30.0,
        },
        {
            "days_ago": 40,
            "weight_kg": 76.9,
            "body_fat_pct": 25.8,
            "skeletal_muscle_kg": 33.4,
            "body_fat_mass_kg": 19.8,
            "total_body_water_l": 43.6,
            "protein_kg": 11.9,
            "minerals_kg": 4.0,
            "bmi": 25.1,
            "visceral_fat_level": 10,
            "bmr_kcal": 1635,
            "waist_hip_ratio": 0.96,
            "obesity_degree_pct": 114,
            "inbody_score": 77,
            "ideal_weight_kg": 71.7,
            "weight_control_kg": -5.2,
            "fat_control_kg": -5.2,
            "muscle_control_kg": 0.0,
            "grip_strength_left_kg": 29.5,
            "grip_strength_right_kg": 31.0,
        },
        {
            "days_ago": 20,
            "weight_kg": 74.9,
            "body_fat_pct": 24.0,
            "skeletal_muscle_kg": 34.2,
            "body_fat_mass_kg": 18.0,
            "total_body_water_l": 44.3,
            "protein_kg": 12.1,
            "minerals_kg": 4.05,
            "bmi": 24.4,
            "visceral_fat_level": 8,
            "bmr_kcal": 1660,
            "waist_hip_ratio": 0.95,
            "obesity_degree_pct": 111,
            "inbody_score": 80,
            "ideal_weight_kg": 71.7,
            "weight_control_kg": -3.2,
            "fat_control_kg": -3.2,
            "muscle_control_kg": 0.0,
            "grip_strength_left_kg": 31.0,
            "grip_strength_right_kg": 32.5,
        },
        {
            "days_ago": 0,
            "weight_kg": 73.2,
            "body_fat_pct": 16.8,
            "skeletal_muscle_kg": 35.1,
            "body_fat_mass_kg": 12.3,
            "total_body_water_l": 44.6,
            "protein_kg": 12.3,
            "minerals_kg": 4.10,
            "bmi": 23.9,
            "visceral_fat_level": 5,
            "bmr_kcal": 1686,
            "waist_hip_ratio": 0.95,
            "obesity_degree_pct": 109,
            "inbody_score": 82,
            "ideal_weight_kg": 71.7,
            "weight_control_kg": -1.5,
            "fat_control_kg": -1.5,
            "muscle_control_kg": 0.0,
            "grip_strength_left_kg": 32.5,
            "grip_strength_right_kg": 34.0,
        },
    ]

    documents = []
    for scan in scans:
        days_ago = scan.pop("days_ago")
        documents.append({
            "owner_id": owner_id,
            "patient_id": patient_id,
            "at": now - timedelta(days=days_ago),
            "provider": "InBody",
            "metrics": scan,
            "attachment_url": None,
            "attachment_type": None,
        })
    await db.body_compositions.insert_many(documents)


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

        # Recetario primero, para poder ligar cada comida del plan a su receta
        recipe_ids = await seed_recipe_collections(pro_id)

        # Plan básico del owner y asignación al paciente
        plan_id = await ensure_plan(pro_id, recipe_ids)
        await ensure_assignment(pro_id, patient_id, plan_id)

        # Citas de ejemplo
        await seed_appointments(pro_id, patient_id)
        # Mediciones de ejemplo para el dashboard de progreso
        await seed_measurements(pro_id, patient_id)
        # Prescripción, videos, e historial clínico de ejemplo
        await seed_prescriptions(pro_id, patient_id)
        await seed_education_videos(pro_id)
        await seed_clinical_history(pro_id, patient_id)
        # Historial de escaneos InBody
        await seed_body_compositions(pro_id, patient_id)
        # Código de invitación demo para probar el registro de pacientes
        await ensure_demo_invite_code(pro_id)

        print("=== Seed listo ===")
        print(f"PRO:    {pro_email} / {pro_pwd}")
        print(f"PATIENT:{patient_email} / {patient_pwd}")
        print("INVITE: DEMO2026 (para probar /auth/register)")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
