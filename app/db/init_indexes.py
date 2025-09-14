from . import mongo

async def ensure_indexes():
    if mongo.db is None:
        await mongo.connect_to_mongo()

    # users
    await mongo.db.users.create_index("email", unique=True)

    # patients: owner_id + name (búsquedas rápidas por nombre dentro de la nutrióloga)
    await mongo.db.patients.create_index([("owner_id", 1), ("name", 1)])

    # appointments: owner_id + start (para queries por rango de fechas)
    await mongo.db.appointments.create_index([("owner_id", 1), ("start", 1)])
    # y filtro por patient_id frecuente
    await mongo.db.appointments.create_index([("owner_id", 1), ("patient_id", 1), ("start", 1)])
