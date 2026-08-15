"""One-off data-seeding script: replaces the synthetic 2-meal demo plan
assigned to rhq.castro@gmail.com with the patient's real 7-day meal plan
(transcribed from the nutritionist-issued PDF), and adds every dish/snack
as a recipe in a new "Plan semanal de Ramón" cookbook collection so each
meal links to a real cookbook entry.

Run with: PYTHONPATH=. .venv/bin/python -m app.scripts.seed_ramon_real_plan
"""
import asyncio
import uuid
from datetime import datetime

from bson import ObjectId

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db

OWNER_ID = ObjectId("6a7d77ed114c9a911c281647")  # pro_demo@nutri.app
PATIENT_ID = ObjectId("6a7d79ea71f440e8e09421d6")  # Ramon Quinonez
PLAN_ID = ObjectId("6a7d77ee114c9a911c28164b")

BEBIDA_DESAYUNO = "Agua natural, café o té endulzado con Stevia."
BEBIDA_COMIDA = (
    "Agua natural o agua de fruta sin azúcar o con Stevia "
    "(Jamaica, limón, pepino, naranja, etc)."
)
BEBIDA_CENA = "Agua natural."

# key -> recipe definition. These become entries in a new cookbook collection.
RECIPES: dict[str, dict] = {
    "sopitas_huevo": {
        "title": "Sopitas con huevo",
        "meal_type": "Desayuno",
        "ingredients": [
            "2 pzas de huevo",
            "2 cucharadas de frijol molido",
            "1 cucharada de aceite",
            "Salsa al gusto, tomate cherry al gusto, cebolla",
            "½ tza de frijol molido",
            "2 pzas de tortilla de maíz",
        ],
        "steps": [
            "Calienta el aceite y cocina el huevo al gusto.",
            "Calienta el frijol molido y sirve sobre las tortillas.",
            "Corona con el huevo y la salsa al gusto.",
        ],
    },
    "avocado_toast": {
        "title": "Avocado toast",
        "meal_type": "Desayuno",
        "ingredients": [
            "2 pzas de huevo",
            "2 pzas de pan bimbo 00, pan masa madre o pan integral verde Panamá",
            "1 pza de aguacate",
        ],
        "steps": [
            "Tuesta el pan y machaca el aguacate encima.",
            "Cocina el huevo al gusto y sírvelo sobre el pan.",
        ],
    },
    "omelette": {
        "title": "Omelette",
        "meal_type": "Desayuno",
        "ingredients": [
            "2 pzas de huevo",
            "1 cucharada de aceite",
            "40 grs de queso oaxaca o de queso de cabra",
            "Ensalada: espinaca, tomate cherry, pimientos",
        ],
        "steps": [
            "Bate el huevo y cocina en el aceite a fuego medio.",
            "Agrega el queso, dobla el omelette y sirve con la ensalada.",
        ],
    },
    "huevos_montados": {
        "title": "Huevos montados",
        "meal_type": "Desayuno",
        "ingredients": [
            "2 pzas de tostadas de nopal",
            "½ tza de frijol molido",
            "2 pzas de huevo estrellado",
            "1/2 pza de aguacate",
        ],
        "steps": [
            "Unta el frijol molido sobre las tostadas de nopal.",
            "Corona con el huevo estrellado y el aguacate.",
        ],
    },
    "chilaquiles_huevo": {
        "title": "Chilaquiles con huevo",
        "meal_type": "Desayuno",
        "ingredients": [
            "1 pza de huevo",
            "15 pzas de totopos de nopal",
            "½ pza de aguacate",
            "Salsa verde o roja",
            "1 cucharada de crema",
            "Verdura al gusto",
        ],
        "steps": [
            "Calienta la salsa y sumerge los totopos hasta suavizar ligeramente.",
            "Sirve con el huevo al gusto, crema, aguacate y verdura.",
        ],
    },
    "colache": {
        "title": "Colache",
        "meal_type": "Desayuno",
        "ingredients": [
            "1 pza de calabacita en cubos, cebolla, tomate, granos de elote",
            "40 grs de queso oaxaca",
            "2 pzas de tortilla de maíz",
        ],
        "steps": [
            "Saltea la calabacita, cebolla, tomate y elote hasta cocinar.",
            "Agrega el queso al final y sirve con las tortillas.",
        ],
    },
    "pollo_limon": {
        "title": "Pechuga de pollo al limón",
        "meal_type": "Comida",
        "ingredients": [
            "150 grs de pechuga de pollo a la plancha",
            "1 cucharada de aceite",
            "Limón y/o mostaza al gusto para sazonar",
            "Verdura al gusto",
            "1 tza de arroz cocido",
            "½ pza de aguacate",
        ],
        "steps": [
            "Sazona la pechuga con limón y/o mostaza y cocina a la plancha.",
            "Sirve con arroz cocido, verdura al gusto y aguacate.",
        ],
    },
    "tacos_carne": {
        "title": "Tacos de carne",
        "meal_type": "Comida",
        "ingredients": [
            "180 grs de carne asada",
            "4 pzas de tortilla de maíz pequeñas",
            "1/3 de aguacate",
            "Salsa pico de gallo al gusto",
            "½ tza de frijol por un lado",
        ],
        "steps": [
            "Asa la carne y córtala en trozos pequeños.",
            "Sirve en tortillas con aguacate, pico de gallo y frijol.",
        ],
    },
    "pescado_empapelado": {
        "title": "Pescado empapelado",
        "meal_type": "Comida",
        "ingredients": [
            "160 grs de filete de pescado",
            "1 tza de arroz cocido",
            "1 cucharadita de mantequilla",
            "½ aguacate",
            "1 tza de garbanzo cocido",
            "Verdura al gusto (brócoli, cebolla, zanahoria)",
        ],
        "steps": [
            "Envuelve el pescado en papel aluminio con mantequilla y verdura.",
            "Hornea hasta cocinar y sirve con arroz, garbanzo y aguacate.",
        ],
    },
    "fajitas_pollo": {
        "title": "Fajitas de pollo",
        "meal_type": "Comida",
        "ingredients": [
            "150 grs de pollo",
            "3 pzas de tortilla de maíz",
            "1/3 de aguacate",
            "Chile morrón rojo y amarillo con cebolla al gusto, chile, tomate",
        ],
        "steps": [
            "Saltea el pollo en tiras con el chile morrón y la cebolla.",
            "Sirve en tortillas con aguacate.",
        ],
    },
    "pollo_crema_chipotle": {
        "title": "Pollo en crema chipotle",
        "meal_type": "Comida",
        "ingredients": [
            "150 grs de pechuga de pollo",
            "Crema al gusto",
            "Chile chipotle",
            "Sazonar al gusto",
            "Ensalada: espinaca, tomate cherry, queso de cabra, 5 mitades de nuez",
        ],
        "steps": [
            "Cocina la pechuga y agrega la crema con chipotle al final.",
            "Sirve con la ensalada de espinaca, queso de cabra y nuez.",
        ],
    },
    "medallon_atun": {
        "title": "Medallón de atún",
        "meal_type": "Comida",
        "ingredients": [
            "150 grs de medallón de atún",
            "4 pzas de tostadas de nopal",
            "Verdura al gusto (cebolla morada, pepino, tomate, limón)",
            "1/2 aguacate",
        ],
        "steps": [
            "Sella el medallón de atún al gusto.",
            "Sirve sobre las tostadas de nopal con verdura y aguacate.",
        ],
    },
    "quesadillas_salsa": {
        "title": "Quesadillas con salsa",
        "meal_type": "Cena",
        "ingredients": [
            "2 pzas de tortilla de maíz",
            "40 grs de queso panela u oaxaca",
            "Salsa pico de gallo al gusto",
            "½ pza de aguacate",
        ],
        "steps": [
            "Calienta las tortillas con el queso hasta derretir.",
            "Sirve con pico de gallo y aguacate.",
        ],
    },
    "yoghur_griego_fruta_nuez": {
        "title": "Yoghur griego con fruta y nuez",
        "meal_type": "Cena",
        "ingredients": [
            "1 tza de yoghur griego sin azúcar sabor a elegir",
            "2 porciones de fruta",
            "3 cucharadas de granola",
            "5 mitades de nuez",
        ],
        "steps": ["Combina todos los ingredientes en un tazón y sirve."],
    },
    "sandwich_pavo_aguacate": {
        "title": "Sandwich de pavo y aguacate",
        "meal_type": "Cena",
        "ingredients": [
            "2 pzas de pan integral (bimbo 00, masa madre o panamá integral verde)",
            "2 pzas de jamón de pavo",
            "½ aguacate",
            "1 cucharada de mayonesa",
        ],
        "steps": ["Arma el sandwich con todos los ingredientes y sirve."],
    },
    "pizza_pan_pita": {
        "title": "Pizza de pan pita",
        "meal_type": "Cena",
        "ingredients": [
            "1 pza de pan pita",
            "2 pzas de jamón de pavo",
            "1 cucharada de preggo o salsa de tomate",
            "40 grs de queso oaxaca",
            "30 grs de queso de cabra",
            "Verdura al gusto",
        ],
        "steps": [
            "Unta la salsa sobre el pan pita y agrega el resto de los ingredientes.",
            "Hornea u hornea en sartén tapado hasta derretir el queso.",
        ],
    },
    "sandwich_atun": {
        "title": "Sandwich de atún",
        "meal_type": "Cena",
        "ingredients": [
            "2 pzas de pan (bimbo 00, masa madre o panamá integral verde)",
            "1 lata de atún en agua",
            "1 cucharada de mayonesa",
            "½ pza de aguacate",
            "Verdura (lechuga, tomate, cebolla)",
        ],
        "steps": [
            "Mezcla el atún con la mayonesa.",
            "Arma el sandwich con el resto de los ingredientes y sirve.",
        ],
    },
    "vampiro_res": {
        "title": "Vampiro de res",
        "meal_type": "Cena",
        "ingredients": [
            "2 pzas de tortilla de maíz",
            "120 grs de carne asada",
            "1/2 aguacate",
            "40 grs de queso oaxaca",
            "Salsa pico de gallo",
        ],
        "steps": [
            "Asa la carne y córtala en trozos pequeños.",
            "Sirve en tortillas con queso, aguacate y salsa.",
        ],
    },
    "snack_a": {
        "title": "Snack de almendras, fruta y yoghur natural",
        "meal_type": "Snack",
        "ingredients": [
            "10 almendras",
            "1 porción de fruta",
            "1 yoghur chobani individual",
        ],
        "steps": ["Combina los ingredientes y sirve."],
    },
    "snack_b": {
        "title": "Snack de almendras y fruta",
        "meal_type": "Snack",
        "ingredients": ["10 almendras", "1 porción de fruta"],
        "steps": ["Combina los ingredientes y sirve."],
    },
    "snack_c": {
        "title": "Snack de almendras, fruta y yoghur de proteína",
        "meal_type": "Snack",
        "ingredients": [
            "10 almendras",
            "1 porción de fruta",
            "1 yoghur proteína chobani individual",
        ],
        "steps": ["Combina los ingredientes y sirve."],
    },
    "snack_d": {
        "title": "Snack de almendras",
        "meal_type": "Snack",
        "ingredients": ["10 almendras"],
        "steps": ["Sirve las almendras solas como snack."],
    },
    "snack_e": {
        "title": "Snack de cacahuates con manzana o uvas",
        "meal_type": "Snack",
        "ingredients": [
            "15 cacahuates",
            "1 manzana o 18 uvas verdes",
        ],
        "steps": ["Combina los ingredientes y sirve."],
    },
    "snack_f": {
        "title": "Snack de cacahuates o almendras",
        "meal_type": "Snack",
        "ingredients": ["15 cacahuates o almendras"],
        "steps": ["Sirve los cacahuates o almendras solos como snack."],
    },
    "snack_h": {
        "title": "Snack de cacahuates con uvas verdes",
        "meal_type": "Snack",
        "ingredients": ["15 cacahuates", "18 uvas verdes"],
        "steps": ["Combina los ingredientes y sirve."],
    },
}

# Per-day meal plan: (title, time, recipe_key | None, [item display lines], notes)
DAYS: list[dict] = [
    {
        "label": "Día 1",
        "meals": [
            ("Desayuno", "08:00", "sopitas_huevo", [
                "2 pzas de huevo", "2 cucharadas de frijol molido",
                "1 cucharada de aceite",
                "Salsa al gusto, tomate cherry al gusto, cebolla",
                "½ tza de frijol molido", "2 pzas de tortilla de maíz",
            ], BEBIDA_DESAYUNO),
            ("Snack", "10:30", "snack_a", [
                "10 almendras", "1 porción de fruta", "1 yoghur chobani individual",
            ], None),
            ("Comida", "13:30", "pollo_limon", [
                "150 grs de pechuga de pollo a la plancha", "1 cucharada de aceite",
                "Limón y/o mostaza al gusto para sazonar", "Verdura al gusto",
                "1 tza de arroz cocido", "½ pza de aguacate",
            ], BEBIDA_COMIDA),
            ("Snack", "17:00", "snack_e", [
                "15 pzas de cacahuates con 1 pza de manzana o 18 pzas de uvas verdes",
            ], None),
            ("Cena", "20:00", "quesadillas_salsa", [
                "2 pzas de tortilla de maíz", "40 grs de queso panela u oaxaca",
                "Salsa pico de gallo al gusto", "½ pza de aguacate",
            ], BEBIDA_CENA),
        ],
    },
    {
        "label": "Día 2",
        "meals": [
            ("Desayuno", "08:00", "avocado_toast", [
                "2 pzas de huevo",
                "2 pzas de pan bimbo 00, pan masa madre o pan integral verde Panamá",
                "1 pza de aguacate",
            ], BEBIDA_DESAYUNO),
            ("Snack", "10:30", "snack_b", ["10 almendras", "1 porción de fruta"], None),
            ("Comida", "13:30", "tacos_carne", [
                "180 grs de carne asada", "4 pzas de tortilla de maíz pequeñas",
                "1/3 de aguacate", "Salsa pico de gallo al gusto",
                "½ tza de frijol por un lado",
            ], BEBIDA_COMIDA),
            ("Snack", "17:00", "snack_f", ["15 pzas de cacahuates o almendras"], None),
            ("Cena", "20:00", "yoghur_griego_fruta_nuez", [
                "1 tza de yoghur griego sin azúcar sabor a elegir",
                "2 porciones de fruta", "3 cucharadas de granola", "5 mitades de nuez",
            ], BEBIDA_CENA),
        ],
    },
    {
        "label": "Día 3",
        "meals": [
            ("Desayuno", "08:00", "omelette", [
                "2 pzas de huevo", "1 cucharada de aceite",
                "40 grs de queso oaxaca o de queso de cabra",
                "Ensalada: espinaca, tomate cherry, pimientos",
            ], BEBIDA_DESAYUNO),
            ("Snack", "10:30", "snack_b", ["10 almendras", "1 porción de fruta"], None),
            ("Comida", "13:30", "pescado_empapelado", [
                "160 grs de filete de pescado", "1 tza de arroz cocido",
                "1 cucharadita de mantequilla", "½ aguacate",
                "1 tza de garbanzo cocido",
                "Verdura al gusto (brócoli, cebolla, zanahoria)",
            ], BEBIDA_COMIDA),
            ("Snack", "17:00", "snack_e", [
                "15 pzas de cacahuates con 1 pza de manzana roja o 18 pzas de uvas verdes",
            ], None),
            ("Cena", "20:00", "sandwich_pavo_aguacate", [
                "2 pzas de pan integral (bimbo 00, masa madre o panamá integral verde)",
                "2 pzas de jamón de pavo", "½ aguacate", "1 cucharada de mayonesa",
            ], BEBIDA_CENA),
        ],
    },
    {
        "label": "Día 4",
        "meals": [
            ("Desayuno", "08:00", "huevos_montados", [
                "2 pzas de tostadas de nopal", "½ tza de frijol molido",
                "2 pzas de huevo estrellado", "1/2 pza de aguacate",
            ], BEBIDA_DESAYUNO),
            ("Snack", "10:30", "snack_c", [
                "10 almendras", "1 porción de fruta",
                "1 yoghur proteína chobani individual",
            ], None),
            ("Comida", "13:30", "fajitas_pollo", [
                "150 grs de pollo", "3 pzas de tortilla de maíz", "1/3 de aguacate",
                "Chile morrón rojo y amarillo con cebolla al gusto, chile, tomate",
            ], BEBIDA_COMIDA),
            ("Snack", "17:00", "snack_h", [
                "15 pzas de cacahuates con 18 pzas de uvas verdes",
            ], None),
            ("Cena", "20:00", "pizza_pan_pita", [
                "1 pza de pan pita", "2 pzas de jamón de pavo",
                "1 cucharada de preggo o salsa de tomate", "40 grs de queso oaxaca",
                "30 grs de queso de cabra", "Verdura al gusto",
            ], BEBIDA_CENA),
        ],
    },
    {
        "label": "Día 5",
        "meals": [
            ("Desayuno", "08:00", "sopitas_huevo", [
                "2 pzas de huevo", "2 cucharadas de frijol molido",
                "1 cucharada de aceite",
                "Salsa al gusto, tomate cherry al gusto, cebolla",
                "½ tza de frijol molido", "2 pzas de tortilla de maíz",
            ], BEBIDA_DESAYUNO),
            ("Snack", "10:30", "snack_b", ["10 almendras", "1 porción de fruta"], None),
            ("Comida", "13:30", "pollo_crema_chipotle", [
                "150 grs de pechuga de pollo", "Crema al gusto", "Chile chipotle",
                "Sazonar al gusto",
                "Ensalada: espinaca, tomate cherry, queso de cabra, 5 mitades de nuez",
            ], BEBIDA_COMIDA),
            ("Snack", "17:00", "snack_c", [
                "10 almendras", "1 porción de fruta",
                "1 yoghur proteína chobani individual",
            ], None),
            ("Cena", "20:00", "sandwich_atun", [
                "2 pzas de pan (bimbo 00, masa madre o panamá integral verde)",
                "1 lata de atún en agua", "1 cucharada de mayonesa",
                "½ pza de aguacate", "Verdura (lechuga, tomate, cebolla)",
            ], BEBIDA_CENA),
        ],
    },
    {
        "label": "Día 6",
        "meals": [
            ("Desayuno", "08:00", "chilaquiles_huevo", [
                "1 pza de huevo", "15 pzas de totopos de nopal", "½ pza de aguacate",
                "Salsa verde o roja", "1 cucharada de crema", "Verdura al gusto",
            ], BEBIDA_DESAYUNO),
            ("Snack", "10:30", "snack_c", [
                "10 almendras", "1 porción de fruta",
                "1 yoghur proteína chobani individual",
            ], None),
            ("Comida", "13:30", "medallon_atun", [
                "150 grs de medallón de atún", "4 pzas de tostadas de nopal",
                "Verdura al gusto (cebolla morada, pepino, tomate, limón)",
                "1/2 aguacate",
            ], BEBIDA_COMIDA),
            ("Snack", "17:00", "snack_f", ["15 pzas de cacahuates o almendras"], None),
            ("Cena", "20:00", "vampiro_res", [
                "2 pzas de tortilla de maíz", "120 grs de carne asada",
                "1/2 aguacate", "40 grs de queso oaxaca", "Salsa pico de gallo",
            ], BEBIDA_CENA),
        ],
    },
    {
        "label": "Día 7",
        "meals": [
            ("Desayuno", "08:00", "colache", [
                "1 pza de calabacita en cubos, cebolla, tomate, granos de elote",
                "40 grs de queso oaxaca", "2 pzas de tortilla de maíz",
            ], BEBIDA_DESAYUNO),
            ("Snack", "10:30", "snack_d", ["10 almendras"], None),
            ("Comida", "13:30", None, [], "Comida libre con moderación."),
            ("Snack", "17:00", "snack_d", ["10 almendras"], None),
            ("Cena", "20:00", None, [], "Elige una opción de la semana."),
        ],
    },
]


async def main() -> None:
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        db = get_db()
        now = datetime.utcnow()

        recipe_ids: dict[str, str] = {}
        recipe_docs = []
        for key, recipe in RECIPES.items():
            recipe_id = uuid.uuid4().hex
            recipe_ids[key] = recipe_id
            recipe_docs.append({
                "id": recipe_id,
                "title": recipe["title"],
                "meal_type": recipe["meal_type"],
                "ingredients": [
                    {"name": line} for line in recipe["ingredients"]
                ],
                "steps": recipe["steps"],
            })

        collection_filter = {"owner_id": OWNER_ID, "title": "Plan semanal de Ramón"}
        await db.recipe_collections.update_one(
            collection_filter,
            {
                "$set": {
                    "owner_id": OWNER_ID,
                    "title": "Plan semanal de Ramón",
                    "description": "Recetas de tu plan de alimentación actual.",
                    "recipes": recipe_docs,
                    "updated_at": now,
                }
            },
            upsert=True,
        )

        plan_days = []
        for day in DAYS:
            meals = []
            for title, time, recipe_key, item_lines, notes in day["meals"]:
                recipe_id = recipe_ids.get(recipe_key) if recipe_key else None
                dish_name = RECIPES[recipe_key]["title"] if recipe_key else None
                items = [
                    {"name": line, "recipe_id": recipe_id} for line in item_lines
                ]
                meals.append({
                    "title": title,
                    "dish_name": dish_name,
                    "time": time,
                    "items": items,
                    "notes": notes,
                })
            plan_days.append({"label": day["label"], "meals": meals})

        await db.plans.update_one(
            {"_id": PLAN_ID},
            {"$set": {"days": plan_days, "updated_at": now}},
        )

        print(f"Recipes seeded: {len(recipe_docs)}")
        print(f"Plan {PLAN_ID} updated with {len(plan_days)} real days.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
