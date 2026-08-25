# app/db/init_indexes.py
from app.db.mongo import get_db

async def ensure_indexes() -> None:
    """
    Crea los índices necesarios para rendimiento e integridad.
    Se llama en startup, después de conectar a Mongo.
    """
    db = get_db()

    # ---------- USERS ----------
    # email único
    await db.users.create_index("email", unique=True)

    # ---------- PATIENTS ----------
    # Búsqueda por nombre y correo (ajusta campos que realmente guardes)
    await db.patients.create_index([("owner_id", 1), ("name", 1)])
    await db.patients.create_index("email")
    await db.patients.create_index("user_id")  # vínculo paciente-usuario

    # ---------- APPOINTMENTS ----------
    # Consultas comunes: por paciente, por estado y por fecha
    await db.appointments.create_index("patient_id")
    await db.appointments.create_index("status")
    await db.appointments.create_index("start")
    # Índice compuesto para listar por paciente ordenado por fecha
    await db.appointments.create_index([("patient_id", 1), ("start", -1)])
    await db.appointments.create_index([("owner_id", 1), ("start", 1)])

    # ---------- PLANS ----------
    await db.plans.create_index("name")
    await db.plans.create_index("goal")
    # Para búsqueda por ingrediente dentro de meals.items
    await db.plans.create_index([("meals.items.name", 1)])
    await db.plans.create_index([("owner_id", 1), ("updated_at", -1)])
    await db.plan_assignments.create_index([("owner_id", 1), ("patient_id", 1)])


    # ---------- PLAN ASSIGNMENTS ----------
    await db.plan_assignments.create_index("plan_id")
    await db.plan_assignments.create_index("patient_id")
    await db.plan_assignments.create_index([("patient_id", 1), ("plan_id", 1)], unique=False)

    # ---------- MEASUREMENTS (for progress) ----------
    await db.measurements.create_index([("patient_id", 1), ("at", 1)])

    # ---------- BODY COMPOSITIONS (InBody scans) ----------
    await db.body_compositions.create_index([("patient_id", 1), ("at", -1)])

    # ---------- RECIPE COLLECTIONS ----------
    await db.recipe_collections.create_index("owner_id")

    # ---------- NUTRITIONIST PROFILES ----------
    await db.nutritionist_profiles.create_index("owner_id", unique=True)

    # ---------- FOOD DIARY ENTRIES ----------
    await db.food_diary_entries.create_index([("patient_id", 1), ("at", -1)])

    # ---------- RECOMMENDATIONS (supplements/brands) ----------
    await db.recommendations.create_index([("owner_id", 1), ("kind", 1)])

    # ---------- INVITE CODES (self-registration) ----------
    await db.invite_codes.create_index("code", unique=True)
    await db.invite_codes.create_index("owner_id")

    # ---------- CONNECTION CODES (patient self-registration, no nutritionist yet) ----------
    # Sparse: most patients never have this field once claimed/never self-registered.
    await db.patients.create_index("connection_code", unique=True, sparse=True)

    # ---------- CONSULTATIONS ----------
    await db.consultations.create_index([("owner_id", 1), ("patient_id", 1), ("status", 1)])
    await db.consultations.create_index([("owner_id", 1), ("created_at", -1)])


    # ---------- NOTIFICATIONS----------

    await db.devices.create_index([("user_id", 1), ("token", 1)], unique=True)


    await db.google_tokens.create_index("user_id", unique=True)
    await db.google_tokens.create_index("provider", name="provider")  # opcional

    # ---------- RATE LIMITING ----------
    await db.rate_limit_events.create_index("key")
    # TTL: events expire on their own an hour after creation, matching the
    # longest throttle window in use — no manual cleanup job needed.
    await db.rate_limit_events.create_index("at", expireAfterSeconds=3600)

    # ---------- MESSAGING (patient <-> nutritionist chat) ----------
    await db.messages.create_index([("owner_id", 1), ("patient_id", 1), ("created_at", 1)])

    # ---------- WORKOUT PLANS ----------
    await db.workout_plans.create_index([("owner_id", 1), ("updated_at", -1)])
    await db.workout_plan_assignments.create_index([("owner_id", 1), ("patient_id", 1)])
    await db.workout_plan_assignments.create_index("plan_id")
    await db.workout_plan_assignments.create_index("patient_id")
    await db.workout_logs.create_index([("owner_id", 1), ("patient_id", 1)])
    await db.workout_logs.create_index([("patient_id", 1), ("workout_plan_id", 1)])
    await db.exercise_library.create_index([("owner_id", 1), ("name", 1)])
