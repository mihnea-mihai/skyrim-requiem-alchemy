from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skyrim_alchemy import Effect, Ingredient, Potency, Potion, Trait


class Data:
    ingredients: list[Ingredient] = []
    effects: list[Effect] = []
    traits: list[Trait] = []
    potencies: list[Potency] = []
    potions: list[Potion] = []
    ingredient_combinations: list[tuple[Ingredient]] = []
    potency_combinations: list[tuple[Potency]] = []
    effect_combinations: list[tuple[Effect]] = []
    potions_by_potencies: dict[tuple[Potency], list[Potion]] = defaultdict(list)
    potions_by_effects: dict[tuple[Effect], list[Potion]] = defaultdict(list)
    valuable_potions: list[Potion] = []
