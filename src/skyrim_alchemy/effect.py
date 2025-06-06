from __future__ import annotations

from functools import cache, cached_property
from statistics import median
from typing import TYPE_CHECKING

from skyrim_alchemy.data import Data
from skyrim_alchemy.utils import read_csv
from skyrim_alchemy.logger import logger

if TYPE_CHECKING:
    from skyrim_alchemy import Ingredient, Potency, Potion, Trait


class Effect:
    @staticmethod
    def read_all():
        for row in read_csv("data/effects.csv"):
            Effect.from_row(row)
        Data.effects = sorted(Data.effects)

    @staticmethod
    def from_row(row: dict) -> None:
        eff = Effect(row)
        Data.effects.append(eff)
        logger.debug("Effect list += %s", eff)

    def __init__(self, row: dict):
        self.name: str = row["name"]
        self.effect_type: str = row["effect_type"]
        self.base_cost: float = float(row["base_cost"])

    @cached_property
    def traits(self) -> list[Trait]:
        return [t for t in Data.traits if t.potency.effect == self]

    @cached_property
    def potencies(self) -> list[Potency]:
        return sorted({t.potency for t in self.traits})

    @cached_property
    def ingredients(self) -> list[Ingredient]:
        return sorted({t.ingredient for t in self.traits})

    # @cached_property
    # def potions(self) -> list[Potion]:
    #     return sorted(p for p in Data.potions if self in p.ingredients)

    @cached_property
    def median_magnitude(self) -> float:
        return median(t.potency.magnitude for t in self.traits)

    @cached_property
    def median_duration(self) -> float:
        return median(t.potency.duration for t in self.traits)

    @cached_property
    def median_price(self) -> float:
        return median(t.potency.price for t in self.traits)

    @cached_property
    def median_accessibility(self) -> float:
        return median(i.accessibility_factor for i in self.ingredients)

    def __repr__(self):
        return f"Effect({self.name})"

    def __lt__(self, other: Effect):
        return (self.base_cost, self.name) < (other.base_cost, other.name)

    @staticmethod
    @cache
    def get(name: str) -> Effect:
        for eff in Data.effects:
            if eff.name == name:
                return eff


if __name__ == "__main__":
    Effect.read_all()
    for effect in Data.effects:
        print(effect)
