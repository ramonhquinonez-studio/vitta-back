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


class _FakeOwnerScopedRepository:
    def __init__(self):
        self.mine: dict[str, list[Article]] = {}
        self.platform: list[Article] = []
        self.sequence = 1

    async def list_articles(self):
        return []

    async def list_for_owner(self, owner_id):
        return self.mine.get(owner_id, [])

    async def list_platform_articles(self):
        return self.platform

    def _find(self, owner_id, article_id):
        for article in self.mine.get(owner_id, []):
            if article.id == article_id:
                return article
        return None

    async def create_for_owner(self, owner_id, payload):
        article = Article(
            id=f"art-{self.sequence}",
            category=payload.get("category") or "",
            title=payload["title"],
            description=payload.get("description") or "",
            read_time=payload.get("read_time") or "",
            emoji=payload.get("emoji") or "📖",
            order=0,
            sections=[
                ArticleSection(title=s.get("title", ""), text=s["text"], bullets=s.get("bullets"))
                for s in payload.get("sections") or []
            ],
            owner_id=owner_id,
            video_url=payload.get("video_url"),
        )
        self.sequence += 1
        self.mine.setdefault(owner_id, []).append(article)
        return article

    async def update_for_owner(self, owner_id, article_id, payload):
        current = self._find(owner_id, article_id)
        if current is None:
            return None
        updated = Article(
            id=current.id,
            category=payload.get("category", current.category),
            title=payload.get("title", current.title),
            description=payload.get("description", current.description),
            read_time=payload.get("read_time", current.read_time),
            emoji=payload.get("emoji", current.emoji),
            order=current.order,
            sections=current.sections,
            owner_id=current.owner_id,
            video_url=payload.get("video_url", current.video_url),
        )
        self.mine[owner_id] = [updated if a.id == article_id else a for a in self.mine[owner_id]]
        return updated

    async def delete_for_owner(self, owner_id, article_id):
        current = self._find(owner_id, article_id)
        if current is None:
            return False
        self.mine[owner_id] = [a for a in self.mine[owner_id] if a.id != article_id]
        return True


class ContentLibraryServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_list_articles_returns_the_full_catalog(self):
        repository = _FakeContentLibraryRepository()
        service = ContentLibraryService(repository)

        articles = await service.list_articles()

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].id, "macronutrientes")
        self.assertEqual(articles[0].sections[1].bullets, ["Fuentes animales", "Fuentes vegetales"])
        self.assertIsNone(articles[1].sections[0].bullets)

    async def test_create_requires_a_title(self):
        repository = _FakeOwnerScopedRepository()
        service = ContentLibraryService(repository)

        with self.assertRaises(ValueError):
            await service.create("owner-1", {"sections": [{"text": "cuerpo"}]})

    async def test_create_requires_body_text_or_a_video_url(self):
        repository = _FakeOwnerScopedRepository()
        service = ContentLibraryService(repository)

        with self.assertRaises(ValueError):
            await service.create("owner-1", {"title": "Solo título"})

    async def test_create_with_a_video_url_and_no_body_text_is_allowed(self):
        repository = _FakeOwnerScopedRepository()
        service = ContentLibraryService(repository)

        article = await service.create(
            "owner-1", {"title": "Video de estiramientos", "video_url": "https://youtu.be/x"}
        )

        self.assertEqual(article.video_url, "https://youtu.be/x")
        self.assertEqual(article.owner_id, "owner-1")

    async def test_create_then_update_then_delete_round_trips(self):
        repository = _FakeOwnerScopedRepository()
        service = ContentLibraryService(repository)
        created = await service.create(
            "owner-1", {"title": "Mi artículo", "sections": [{"text": "cuerpo"}]}
        )

        updated = await service.update("owner-1", created.id, {"title": "Mi artículo editado"})
        self.assertEqual(updated.title, "Mi artículo editado")

        await service.delete("owner-1", created.id)
        self.assertEqual(await service.list_my_articles("owner-1"), [])

    async def test_list_platform_articles_returns_only_platform_content(self):
        repository = _FakeOwnerScopedRepository()
        repository.platform = [
            Article(
                id="medlineplus-nutrition",
                category="Alimentos y nutrición",
                title="Nutrición",
                description="...",
                read_time="3 min",
                emoji="🥗",
                order=100,
                sections=[ArticleSection(title="", text="cuerpo")],
            )
        ]
        await repository.create_for_owner("owner-1", {"title": "Mi propio artículo"})
        service = ContentLibraryService(repository)

        platform_articles = await service.list_platform_articles()

        self.assertEqual(len(platform_articles), 1)
        self.assertEqual(platform_articles[0].id, "medlineplus-nutrition")

    async def test_update_rejects_an_article_not_owned(self):
        repository = _FakeOwnerScopedRepository()
        service = ContentLibraryService(repository)
        created = await service.create(
            "owner-1", {"title": "Mi artículo", "sections": [{"text": "cuerpo"}]}
        )

        with self.assertRaises(LookupError):
            await service.update("owner-2", created.id, {"title": "x"})


if __name__ == "__main__":
    unittest.main()
