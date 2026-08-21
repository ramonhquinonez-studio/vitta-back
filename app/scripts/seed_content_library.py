"""Seeds the platform-curated nutrition education library: a fixed set of
articles (category/title/description/read_time/emoji/sections). This is the
same content that used to be hardcoded in nutri_app's
`nutrition_library_page.dart`, now given a real home. Idempotent — re-running
upserts every article by its stable string `_id`.
"""
import asyncio

from app.core.config import settings
from app.db.mongo import close_mongo_connection, connect_to_mongo, get_db

ARTICLES = [
    {
        "_id": "macronutrientes",
        "category": "Fundamentos",
        "title": "Macronutrientes: Proteínas, carbohidratos y grasas",
        "description": "Aprende sobre los tres macronutrientes esenciales y su importancia en tu alimentación...",
        "read_time": "8 min",
        "emoji": "🍽️",
        "order": 1,
        "sections": [
            {
                "title": "¿Qué son los macronutrientes?",
                "text": "Los macronutrientes son los nutrientes que el cuerpo necesita en grandes cantidades para funcionar correctamente. Incluyen proteínas, carbohidratos y grasas.",
            },
            {
                "title": "Proteínas",
                "text": "Las proteínas son fundamentales para la construcción y reparación de tejidos. Se recomienda consumir aproximadamente 0.8-1 g por kg de peso corporal al día.",
                "bullets": [
                    "Fuentes animales: pollo, pescado, huevos, lácteos",
                    "Fuentes vegetales: legumbres, tofu, quinoa, frutos secos",
                ],
            },
            {
                "title": "Carbohidratos",
                "text": "Principal fuente de energía del cuerpo. Prioriza carbohidratos complejos de granos enteros, frutas y verduras.",
            },
            {
                "title": "Grasas",
                "text": "Esenciales para la absorción de vitaminas y salud hormonal. Enfócate en grasas insaturadas como aguacate, aceite de oliva y frutos secos.",
            },
            {
                "title": "Recomendaciones prácticas",
                "text": "Combina los tres macronutrientes en cada comida para mejorar la saciedad y mantener niveles de energía estables.",
            },
            {
                "title": "Ejemplo de plato",
                "text": "Pollo a la plancha (proteína) + arroz integral (carbohidrato) + ensalada con aceite de oliva (grasas saludables).",
            },
        ],
    },
    {
        "_id": "hidratacion",
        "category": "Hidratación",
        "title": "Hidratación: ¿Cuánta agua necesitas realmente?",
        "description": "Descubre cuánta agua debes beber diariamente y cómo la hidratación afecta tu metabolismo.",
        "read_time": "5 min",
        "emoji": "💧",
        "order": 2,
        "sections": [
            {
                "title": "La importancia del agua",
                "text": "El agua participa en la regulación de la temperatura, transporte de nutrientes y eliminación de desechos.",
            },
            {
                "title": "¿Cuánta agua?",
                "text": "Una guía general es 30-35 ml por kg de peso, ajustando por actividad física y clima.",
            },
            {
                "title": "Señales de hidratación",
                "text": "Observa el color de la orina y la sensación de sed para ajustar tu consumo diario.",
            },
        ],
    },
    {
        "_id": "plato_saludable",
        "category": "Fundamentos",
        "title": "El plato saludable: Composición ideal de tus comidas",
        "description": "Aprende a balancear tus comidas usando el método del plato saludable.",
        "read_time": "6 min",
        "emoji": "🥗",
        "order": 3,
        "sections": [
            {
                "title": "Distribución del plato",
                "text": "Llena la mitad del plato con vegetales, un cuarto con proteína y un cuarto con carbohidratos integrales.",
            },
            {
                "title": "Balance diario",
                "text": "Combina colores y texturas para asegurar variedad de nutrientes.",
            },
        ],
    },
    {
        "_id": "metabolismo",
        "category": "Metabolismo",
        "title": "Metabolismo: Cómo funciona y cómo acelerarlo",
        "description": "Entiende qué es el metabolismo y estrategias basadas en evidencia para optimizarlo.",
        "read_time": "10 min",
        "emoji": "⚡",
        "order": 4,
        "sections": [
            {
                "title": "Metabolismo basal",
                "text": "Es la energía que tu cuerpo usa en reposo. Depende de masa muscular, edad y genética.",
            },
            {
                "title": "Estrategias",
                "text": "Prioriza fuerza, buen descanso y una ingesta adecuada de proteínas para apoyar tu metabolismo.",
            },
        ],
    },
    {
        "_id": "etiquetas_nutricionales",
        "category": "Educación",
        "title": "Interpretando etiquetas nutricionales",
        "description": "Aprende a leer etiquetas para elegir productos con mejores nutrientes.",
        "read_time": "7 min",
        "emoji": "🏷️",
        "order": 5,
        "sections": [
            {
                "title": "Porción y calorías",
                "text": "Revisa el tamaño de porción para interpretar correctamente calorías y nutrientes.",
            },
            {
                "title": "Azúcares y sodio",
                "text": "Busca opciones con menor azúcar añadida y sodio para cuidar tu salud.",
            },
        ],
    },
]


async def seed_articles() -> None:
    db = get_db()
    for article in ARTICLES:
        await db.content_articles.update_one(
            {"_id": article["_id"]}, {"$set": article}, upsert=True
        )
    print(f"Artículos: {len(ARTICLES)} actualizados/creados.")


async def main() -> None:
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    try:
        await seed_articles()
        print("=== Biblioteca nutricional lista ===")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
