from __future__ import annotations

from functools import cached_property
from itertools import chain, combinations, groupby, pairwise
from typing import TYPE_CHECKING

from skyrim_alchemy.data import Data
from skyrim_alchemy.logger import logger

if TYPE_CHECKING:
    from skyrim_alchemy import Effect, Ingredient, Potency, Trait


class Potion:
    @staticmethod
    def from_ingredients(ingredients: tuple[Ingredient]):
        new_ings = tuple(sorted(set(ingredients)))
        # for potion in Data.potions:
        #     if potion.ingredients == new_ings:
        #         return potion
        pot = Potion(new_ings)
        if pot.valid and pot.pure and pot.compatible_duration and pot.is_improvement:
            logger.debug("Potions += %s", str(pot))
            Data.potions.append(pot)
            # Data.ingredient_combinations.append(new_ings)
        return pot

    def __repr__(self) -> str:
        return f"Potion({', '.join(i.name for i in self.ingredients)})"

    @cached_property
    def candidate_ingredients(self) -> list[Ingredient]:
        if len(self.ingredients) > 2:
            raise ValueError
        return [
            comp_ing
            for ing in self.ingredients
            for comp_ing in ing.compatible_ingredients
            if comp_ing not in self.ingredients
        ]

    @cached_property
    def all_traits(self) -> list[Trait]:
        return list(chain.from_iterable(ing.traits for ing in self.ingredients))

    @cached_property
    def all_potencies_by_effect(self) -> list[tuple[Effect, list[Trait]]]:
        return [
            (effect, list(potencies))
            for effect, potencies in groupby(
                sorted([t.potency for t in self.all_traits], key=lambda p: p.effect),
                key=lambda p: p.effect,
            )
        ]

    @cached_property
    def potencies(self) -> tuple[Potency]:
        return tuple(
            sorted(
                max(sorted(potencies))
                for _, potencies in self.all_potencies_by_effect
                if len(potencies) > 1
            )
        )

    @cached_property
    def effects(self) -> tuple[Effect]:
        return tuple(sorted(potency.effect for potency in self.potencies))

    @cached_property
    def is_improvement(self) -> bool:
        if len(self.ingredients) == 2:
            return True
        for ing1, ing2 in combinations(self.ingredients, 2):
            pot = Potion(sorted((ing1, ing2)))
            if self.potencies == pot.potencies:
                return False
        return True

    @cached_property
    def valid(self) -> bool:
        return len(self.potencies) > 0

    @cached_property
    def pure(self) -> bool:
        # return True
        for pot1, pot2 in pairwise(self.potencies):
            if pot1.effect.effect_type != pot2.effect.effect_type:
                return False
        return True

    @cached_property
    def compatible_duration(self) -> bool:
        for pot1, pot2 in combinations(self.potencies, 2):
            if pot1.effect.permanent or pot2.effect.permanent:
                continue
            if pot1.duration != pot2.duration:
                return False
            if pot1.magnitude == 0 and pot2.magnitude != 0:
                return False
            if pot2.magnitude == 0 and pot1.magnitude != 0:
                return False
        return True

        # if pot1.duration == pot2.duration:
        #     if pot1.duration == 0:  # applies to both
        #         return True
        #     else:  # magnitude affects duration only for one
        #         return False
        # else:
        #     return False

        # if (
        #     pot1.duration != pot2.duration
        #     and not (pot1.effect.permanent or pot2.effect.permanent)
        #     and (pot1.magnitude != 0 and pot2.magnitude != 0)
        # ):
        #     return False
        # (
        #     pot1.magnitude == 0
        #     and pot2.magnitude != 0
        #     or pot1.magnitude != 0
        #     and pot2.magnitude == 0
        # )

    @cached_property
    def overpriced(self) -> bool:
        return any(potency.overpriced for potency in self.potencies)

    @cached_property
    def potencies_accessibility_sum(self) -> float:
        return sum(potency.min_potion_accessibility for potency in self.potencies)

    def __init__(self, ingredients: tuple[Ingredient]):
        self.ingredients = ingredients
        self.best_in_slot = False
        """Test"""

    @cached_property
    def accessibility(self) -> float:
        return sum(i.accessibility for i in self.ingredients)

    @cached_property
    def price(self) -> float:
        return sum(p.price for p in self.potencies)

    @cached_property
    def relative_value(self) -> float:
        return self.price / self.accessibility * 100

    def __lt__(self, other: Potion) -> bool:
        return (self.effects, self.potencies, self.accessibility) < (
            other.effects,
            other.potencies,
            other.accessibility,
        )
