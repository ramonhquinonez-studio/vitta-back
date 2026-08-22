"""Seeds a starter set of supplements/brands into ONE nutritionist's own
"Suplementos y marcas" catalog (unlike seed_equivalencies.py, this is
per-owner, not global — every nutritionist curates their own list). Content
sourced from real references, not invented: generic supplement categories
are standard nutrition-practice terms, brands are Profeco's top-ranked
vitamin brands in Mexico plus the major direct-sales players confirmed to
operate there. Idempotent — skips any (owner, kind, title) that already
exists, safe to re-run.

Usage: PYTHONPATH=. .venv/bin/python app/scripts/seed_recommendations_starter.py <email>
"""
import asyncio
import sys

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db
from app.modules.recommendations.application.recommendations_service import (
    RecommendationsService,
)
from app.modules.recommendations.infrastructure.mongo_recommendations_repository import (
    MongoRecommendationsRepository,
)

SUPPLEMENTS = [
    "Proteína en polvo",
    "Multivitamínico",
    "Omega-3",
    "Vitamina D",
    "Vitamina C",
    "Complejo B",
    "Magnesio",
    "Colágeno hidrolizado",
    "Probióticos",
    "Creatina",
    "Hierro",
    "Zinc",
    "Calcio",
    "Fibra",
    "BCAA / Aminoácidos",
]

BRANDS = [
    "NOW Foods",
    "Nature Made",
    "Centrum",
    "Garden of Life",
    "Spring Valley",
    "GNC",
    "Solgar",
    "Nutrilite (Amway)",
    "Herbalife",
    "Omnilife",
]


async def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python app/scripts/seed_recommendations_starter.py <email>")
        sys.exit(1)
    email = sys.argv[1]

    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        db = get_db()
        user = await db.users.find_one({"email": email})
        if user is None:
            print(f"No user found with email {email!r}.")
            sys.exit(1)
        owner_id = str(user["_id"])

        service = RecommendationsService(MongoRecommendationsRepository(db))
        existing = await service.list_my_recommendations(owner_id)
        existing_keys = {(r.kind, r.title) for r in existing}

        to_create = [
            {"kind": "supplement", "title": title}
            for title in SUPPLEMENTS
            if ("supplement", title) not in existing_keys
        ] + [
            {"kind": "brand", "title": title}
            for title in BRANDS
            if ("brand", title) not in existing_keys
        ]

        if not to_create:
            print(f"{email}: catálogo ya tiene todos los elementos iniciales, nada que hacer.")
            return

        created = await service.create_bulk(owner_id, to_create)
        print(f"{email}: {len(created)} elementos agregados "
              f"({len(SUPPLEMENTS) + len(BRANDS) - len(created)} ya existían).")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
