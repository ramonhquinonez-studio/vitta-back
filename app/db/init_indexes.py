# app/db/init_indexes.py
from . import mongo

async def ensure_indexes():
    # Por si alguien llama ensure_indexes sin haber conectado
    if mongo.db is None:
        await mongo.connect_to_mongo()

    await mongo.db.users.create_index("email", unique=True)