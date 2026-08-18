"""Seeds the SMAE (Sistema Mexicano de Alimentos Equivalentes) reference
catalog: 16 food-exchange groups plus a starter set of common foods per
group. Idempotent — re-running upserts groups and skips foods that already
exist by (group_id, name).
"""
import asyncio

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db

GROUPS = [
    {"_id": "cereales_sin_grasa", "name": "Cereales y tubérculos sin grasa",
     "kcal": 70, "carbs_g": 15, "protein_g": 2, "fat_g": 0},
    {"_id": "cereales_con_grasa", "name": "Cereales y tubérculos con grasa",
     "kcal": 115, "carbs_g": 15, "protein_g": 2, "fat_g": 5},
    {"_id": "leguminosas", "name": "Leguminosas",
     "kcal": 120, "carbs_g": 20, "protein_g": 8, "fat_g": 1},
    {"_id": "verduras", "name": "Verduras",
     "kcal": 25, "carbs_g": 4, "protein_g": 2, "fat_g": 0},
    {"_id": "frutas", "name": "Frutas",
     "kcal": 60, "carbs_g": 15, "protein_g": 0, "fat_g": 0},
    {"_id": "aoa_muy_bajo_grasa", "name": "Alimentos de origen animal muy bajos en grasa",
     "kcal": 40, "carbs_g": 0, "protein_g": 7, "fat_g": 1},
    {"_id": "aoa_bajo_grasa", "name": "Alimentos de origen animal bajos en grasa",
     "kcal": 55, "carbs_g": 0, "protein_g": 7, "fat_g": 3},
    {"_id": "aoa_moderado_grasa", "name": "Alimentos de origen animal con grasa moderada",
     "kcal": 75, "carbs_g": 0, "protein_g": 7, "fat_g": 5},
    {"_id": "aoa_alto_grasa", "name": "Alimentos de origen animal altos en grasa",
     "kcal": 100, "carbs_g": 0, "protein_g": 7, "fat_g": 8},
    {"_id": "leche_descremada", "name": "Leche descremada",
     "kcal": 95, "carbs_g": 12, "protein_g": 9, "fat_g": 2},
    {"_id": "leche_semidescremada", "name": "Leche semidescremada",
     "kcal": 110, "carbs_g": 12, "protein_g": 9, "fat_g": 4},
    {"_id": "leche_entera", "name": "Leche entera",
     "kcal": 150, "carbs_g": 12, "protein_g": 9, "fat_g": 8},
    {"_id": "aceites_sin_proteina", "name": "Aceites y grasas sin proteína",
     "kcal": 45, "carbs_g": 0, "protein_g": 0, "fat_g": 5},
    {"_id": "aceites_con_proteina", "name": "Aceites y grasas con proteína",
     "kcal": 70, "carbs_g": 0, "protein_g": 3, "fat_g": 5},
    {"_id": "azucares_sin_grasa", "name": "Azúcares sin grasa",
     "kcal": 40, "carbs_g": 10, "protein_g": 0, "fat_g": 0},
    {"_id": "azucares_con_grasa", "name": "Azúcares con grasa",
     "kcal": 85, "carbs_g": 10, "protein_g": 0, "fat_g": 5},
]

FOODS = {
    "cereales_sin_grasa": [
        ("Tortilla de maíz", "1 pieza (30 g)"),
        ("Pan de caja", "1 rebanada"),
        ("Arroz cocido", "½ taza"),
        ("Avena cocida", "½ taza"),
        ("Pasta cocida", "½ taza"),
        ("Bolillo sin migajón", "½ pieza"),
    ],
    "cereales_con_grasa": [
        ("Tortilla de harina", "1 pieza"),
        ("Pan dulce", "1 pieza chica"),
        ("Galletas María", "5 piezas"),
        ("Elote con mantequilla", "1 pieza mediana"),
    ],
    "leguminosas": [
        ("Frijoles cocidos", "½ taza"),
        ("Lentejas cocidas", "½ taza"),
        ("Garbanzos cocidos", "½ taza"),
        ("Habas cocidas", "½ taza"),
    ],
    "verduras": [
        ("Lechuga", "1 taza"),
        ("Jitomate", "1 pieza mediana"),
        ("Brócoli cocido", "½ taza"),
        ("Zanahoria cruda", "1 taza"),
        ("Espinaca cruda", "2 tazas"),
        ("Calabacita cocida", "½ taza"),
    ],
    "frutas": [
        ("Manzana", "1 pieza chica"),
        ("Plátano", "½ pieza"),
        ("Papaya", "1 taza"),
        ("Naranja", "1 pieza"),
        ("Fresas", "1 taza"),
        ("Melón", "1 taza"),
    ],
    "aoa_muy_bajo_grasa": [
        ("Claras de huevo", "3 piezas"),
        ("Pechuga de pollo sin piel", "30 g"),
        ("Atún en agua", "30 g"),
        ("Queso panela", "30 g"),
    ],
    "aoa_bajo_grasa": [
        ("Pescado blanco", "30 g"),
        ("Queso cottage", "¼ taza"),
        ("Pollo pierna sin piel", "30 g"),
    ],
    "aoa_moderado_grasa": [
        ("Huevo entero", "1 pieza"),
        ("Queso oaxaca", "30 g"),
        ("Carne molida de res", "30 g"),
    ],
    "aoa_alto_grasa": [
        ("Chorizo", "30 g"),
        ("Queso manchego", "30 g"),
        ("Salchicha", "1 pieza"),
    ],
    "leche_descremada": [
        ("Leche descremada", "1 taza"),
        ("Yogurt light natural", "1 taza"),
    ],
    "leche_semidescremada": [
        ("Leche semidescremada", "1 taza"),
        ("Yogurt natural", "1 taza"),
    ],
    "leche_entera": [
        ("Leche entera", "1 taza"),
        ("Yogurt natural entero", "1 taza"),
    ],
    "aceites_sin_proteina": [
        ("Aceite de oliva", "1 cdta"),
        ("Aguacate", "⅓ pieza"),
        ("Mayonesa", "1 cdta"),
    ],
    "aceites_con_proteina": [
        ("Cacahuates", "10 piezas"),
        ("Almendras", "6 piezas"),
        ("Nueces", "4 mitades"),
    ],
    "azucares_sin_grasa": [
        ("Azúcar", "1 cda"),
        ("Miel", "1 cda"),
        ("Mermelada", "1 cda"),
    ],
    "azucares_con_grasa": [
        ("Chocolate", "1 cuadrito"),
        ("Cajeta", "1 cda"),
        ("Nutella", "1 cdta"),
    ],
}


async def seed_groups() -> None:
    db = get_db()
    for group in GROUPS:
        await db.equivalency_groups.update_one(
            {"_id": group["_id"]}, {"$set": group}, upsert=True
        )
    print(f"Grupos: {len(GROUPS)} actualizados/creados.")


async def seed_foods() -> None:
    db = get_db()
    created = 0
    for group_id, foods in FOODS.items():
        for name, portion in foods:
            existing = await db.equivalency_foods.find_one(
                {"group_id": group_id, "name": name, "owner_id": None}
            )
            if existing:
                continue
            await db.equivalency_foods.insert_one({
                "group_id": group_id,
                "name": name,
                "portion_description": portion,
                "owner_id": None,
            })
            created += 1
    total = sum(len(v) for v in FOODS.values())
    print(f"Alimentos: {created} nuevos de {total} en el catálogo base.")


async def main() -> None:
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        await seed_groups()
        await seed_foods()
        print("=== Catálogo de equivalencias listo ===")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
