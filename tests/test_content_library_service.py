import unittest

from app.modules.content_library.application.content_library_service import (
    ContentLibraryService,
)
from app.modules.content_library.domain.entities import Article, ArticleSection


class _FakeContentLibraryRepository:
    def __init__(self):
        self.articles = [
            Article(
                id="macronutrientes",
                category="Fundamentos",
                title="Macronutrientes: Proteínas, carbohidratos y grasas",
                description="Aprende sobre los tres macronutrientes esenciales...",
                read_time="8 min",
                emoji="🍽️",
                order=1,
                sections=[
                    ArticleSection(
                        title="¿Qué son los macronutrientes?",
                        text="Los macronutrientes son los nutrientes que el cuerpo necesita.",
                    ),
                    ArticleSection(
                        title="Proteínas",
                        text="Fundamentales para tejidos.",
                        bullets=["Fuentes animales", "Fuentes vegetales"],
                    ),
                ],
            ),
            Article(
                id="hidratacion",
                category="Hidratación",
                title="Hidratación: ¿Cuánta agua necesitas realmente?",
                description="Descubre cuánta agua debes beber diariamente.",
                read_time="5 min",
                emoji="💧",
                order=2,
                sections=[
                    ArticleSection(
                        title="La importancia del agua",
                        text="El agua participa en la regulación de la temperatura.",
                    ),
                ],
            ),
        ]

    async def list_articles(self):
        return self.articles


class ContentLibraryServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_list_articles_returns_the_full_catalog(self):
        repository = _FakeContentLibraryRepository()
        service = ContentLibraryService(repository)

        articles = await service.list_articles()

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].id, "macronutrientes")
        self.assertEqual(articles[0].sections[1].bullets, ["Fuentes animales", "Fuentes vegetales"])
        self.assertIsNone(articles[1].sections[0].bullets)


if __name__ == "__main__":
    unittest.main()
