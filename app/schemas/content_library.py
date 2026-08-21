from typing import Optional

from pydantic import BaseModel


class ArticleSectionOut(BaseModel):
    title: str
    text: str
    bullets: Optional[list[str]] = None


class ArticleOut(BaseModel):
    id: str
    category: str
    title: str
    description: str
    read_time: str
    emoji: str
    order: int
    sections: list[ArticleSectionOut]
