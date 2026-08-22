from typing import Optional

from pydantic import BaseModel, Field


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
    owner_id: Optional[str] = None
    video_url: Optional[str] = None


class ArticleSectionIn(BaseModel):
    title: str = ""
    text: str = Field(..., min_length=1)
    bullets: Optional[list[str]] = None


class ArticleIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    category: Optional[str] = Field(None, max_length=60)
    description: Optional[str] = Field(None, max_length=500)
    read_time: Optional[str] = Field(None, max_length=20)
    emoji: Optional[str] = Field(None, max_length=8)
    video_url: Optional[str] = None
    sections: list[ArticleSectionIn] = []


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    category: Optional[str] = Field(None, max_length=60)
    description: Optional[str] = Field(None, max_length=500)
    read_time: Optional[str] = Field(None, max_length=20)
    emoji: Optional[str] = Field(None, max_length=8)
    video_url: Optional[str] = None
    sections: Optional[list[ArticleSectionIn]] = None
