from dataclasses import dataclass, field


@dataclass(frozen=True)
class Recipe:
    id: str
    title: str
    meal_type: str | None = None
    minutes: int | None = None
    portions: int | None = None
    kcal: int | None = None
    ingredients: list[dict] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    url: str | None = None


@dataclass(frozen=True)
class RecipeCollection:
    id: str
    owner_id: str
    title: str
    description: str | None = None
    recipes: list[Recipe] = field(default_factory=list)
