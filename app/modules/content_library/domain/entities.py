from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleSection:
    title: str
    text: str
    bullets: list[str] | None = None


@dataclass(frozen=True)
class Article:
    id: str
    category: str
    title: str
    description: str
    read_time: str
    emoji: str
    order: int
    sections: list[ArticleSection]
