from pydantic import BaseModel, Field
from typing import List, Optional


class RecommendationOut(BaseModel):
    id: str
    owner_id: Optional[str] = None
    kind: str
    title: str
    subtitle: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    benefits: List[str] = []
    usage: Optional[str] = None
    notes: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[float] = None
    emoji: Optional[str] = None
    equivalency_group_id: Optional[str] = None


class RecommendationCreate(BaseModel):
    kind: str = Field(..., pattern="^(supplement|brand)$")
    title: str = Field(..., min_length=1, max_length=120)
    subtitle: Optional[str] = Field(None, max_length=120)
    category: Optional[str] = Field(None, max_length=60)
    brand: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    benefits: List[str] = []
    usage: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)
    price: Optional[str] = Field(None, max_length=40)
    rating: Optional[float] = Field(None, ge=0, le=5)
    emoji: Optional[str] = Field(None, max_length=8)
    # Only meaningful for kind="brand" — see Recommendation.equivalency_group_id.
    equivalency_group_id: Optional[str] = Field(None, max_length=60)


class RecommendationAssignRequest(BaseModel):
    patient_ids: List[str] = Field(..., min_length=1, max_length=200)


class RecommendationAssignmentsOut(BaseModel):
    patient_ids: List[str] = []


class RecommendationBulkCreate(BaseModel):
    items: List[RecommendationCreate] = Field(..., min_length=1, max_length=200)


class RecommendationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    subtitle: Optional[str] = Field(None, max_length=120)
    category: Optional[str] = Field(None, max_length=60)
    brand: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    benefits: Optional[List[str]] = None
    usage: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)
    price: Optional[str] = Field(None, max_length=40)
    rating: Optional[float] = Field(None, ge=0, le=5)
    emoji: Optional[str] = Field(None, max_length=8)
    equivalency_group_id: Optional[str] = Field(None, max_length=60)
