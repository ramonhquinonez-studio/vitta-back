from pydantic import BaseModel, Field
from typing import Generic, List, TypeVar

T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)

class Page(BaseModel, Generic[T]):
    items: List[T]
    page: int
    limit: int
    total: int
