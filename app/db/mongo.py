# app/db/mongo.py
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None

async def connect_to_mongo(uri: str, db_name: str) -> None:
    """Conecta y deja disponible get_db()."""
    global _client, _db
    _client = AsyncIOMotorClient(uri)
    _db = _client[db_name]

async def close_mongo_connection() -> None:
    """Cierra la conexión (para shutdown)."""
    global _client
    if _client:
        _client.close()
        _client = None

def get_db() -> AsyncIOMotorDatabase:
    """Obtén la DB actual (levanta si no está inicializada)."""
    if _db is None:
        raise RuntimeError("MongoDB is not initialized. Did startup run?")
    return _db
