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
    # An eating-out alternative for this recipe's meal slot — a plain
    # {restaurant, dish, kcal, protein, carbs, fat} dict, copied verbatim
    # into a PlanMeal's eating_out_options when the recipe is used in a
    # plan. Kept loose here (not its own dataclass), matching this
    # entity's existing `ingredients: list[dict]` looseness.
    eating_out_option: dict | None = None


@dataclass(frozen=True)
class RecipeCollection:
    id: str
    owner_id: str
    title: str
    description: str | None = None
    recipes: list[Recipe] = field(default_factory=list)
