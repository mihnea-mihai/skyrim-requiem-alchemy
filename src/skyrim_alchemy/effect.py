from __future__ import annotations

from functools import cache, cached_property
from itertools import groupby
from statistics import median
from typing import TYPE_CHECKING

from skyrim_alchemy.data import Data
from skyrim_alchemy.logger import logger
from skyrim_alchemy.utils import read_csv

if TYPE_CHECKING:
    from skyrim_alchemy import Ingredient, Potency, Potion, Trait


class Effect:
    @staticmethod
    def read_all():
        for row in read_csv("data/effects.csv"):
            Effect.from_row(row)
        # Data.effects.sort()

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

    @cached_property
    def ingredients_by_potencies(self) -> list[tuple[Potency, list[Ingredient]]]:
        return [
            (p, sorted(trait.ingredient for trait in traits))
            for p, traits in groupby(
                sorted(self.traits, key=lambda t: t.potency, reverse=True),
                key=lambda t: t.potency,
            )
        ]

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
        return median(i.accessibility for i in self.ingredients)

    @cached_property
    def potions(self) -> list[Potion]:
        return sorted(p for p in Data.potions if self in p.effects)

    @cached_property
    def grouped_potions(self) -> list[tuple[Potency, list[Potion]]]:
        return sorted(
            [
                (potencies, list(potions))
                for potencies, potions in groupby(
                    sorted(
                        sorted(self.potions, key=lambda p: p.potencies, reverse=True),
                        key=lambda p: p.effects,
                    ),
                    key=lambda p: p.potencies,
                )
            ],
            key=lambda g: len(g[0]),
        )

    def __repr__(self):
        return f"Effect({self.name})"

    def __lt__(self, other: Effect):
        if self.median_price < other.median_price:
            return True
        if self.median_price > other.median_price:
            return False
        if self.median_accessibility < other.median_accessibility:
            return True
        if self.median_accessibility > other.median_accessibility:
            return False
        return False

    def __le__(self, other: Effect):
        try:
            return self < other
        except NotImplementedError:
            return True

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
