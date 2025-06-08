from __future__ import annotations

from functools import cache, cached_property
from itertools import groupby
from statistics import mean, median
from typing import TYPE_CHECKING

from skyrim_alchemy.data import Data
from skyrim_alchemy.logger import logger
from skyrim_alchemy.utils import read_csv

if TYPE_CHECKING:
    from skyrim_alchemy import Effect, Potency, Potion, Trait


class Ingredient:
    @staticmethod
    def read_all():
        for row in read_csv("data/ingredients.csv"):
            Ingredient.from_row(row)
        # Data.ingredients.sort()

    @staticmethod
    def from_row(row: dict) -> None:
        ing = Ingredient(row)
        Data.ingredients.append(ing)
        logger.debug("Ingredient list += %s", ing)

    def __init__(self, row: dict):
        self.name: str = row["name"]
        self.value: int = int(row["value"])
        self.plantable: bool = row["plantable"] == "True"
        self.vendor_rarity: str = row["vendor_rarity"]
        self.unique_to: str = row["unique_to"]

    @cached_property
    def traits(self) -> list[Trait]:
        return [t for t in Data.traits if t.ingredient == self]

    @cached_property
    def potencies(self) -> list[Potency]:
        return [t.potency for t in self.traits]

    @cached_property
    def effects(self) -> list[Effect]:
        return sorted(p.effect for p in self.potencies)

    @cached_property
    def potions(self) -> list[Potion]:
        return sorted(p for p in Data.potions if self in p.ingredients)
        # return [p for p in Data.potions if self in p.ingredients]

    @cached_property
    def grouped_potions(self) -> list[tuple[Potency, list[Potion]]]:
        return [
            (potency, list(potions))
            for potency, potions in groupby(
                sorted(
                    sorted(self.potions, key=lambda p: p.potencies, reverse=True),
                    key=lambda p: p.effects,
                ),
                key=lambda p: p.potencies,
            )
        ]

    @cached_property
    def average_potency_price(self) -> float:
        return mean(p.price for p in self.potencies)

    @cached_property
    def average_potion_price(self) -> float:
        return mean(p.price for p in self.potions)

    @cached_property
    def median_potion_price(self) -> float:
        return median(p.price for p in self.potions)

    @cached_property
    def compatible_ingredients(self) -> list[Ingredient]:
        return sorted(
            i
            for i in Data.ingredients
            if set(i.effects) & set(self.effects) and i != self
        )

    def __repr__(self):
        return f"Ingredient({self.name})"

    def __lt__(self, other: Ingredient):
        if self.accessibility_factor < other.accessibility_factor:
            return True
        if self.accessibility_factor > other.accessibility_factor:
            return False
        return NotImplemented

    @staticmethod
    @cache
    def get(name: str) -> Ingredient:
        for ing in Data.ingredients:
            if ing.name == name:
                return ing

    @cached_property
    def accessibility_factor(self) -> float:
        res: float = 0.0
        if self.plantable:
            res += 1
        elif self.name in ["Daedra Heart", "Strange Remains"]:
            res += 9
        else:
            res += 2
        res *= 2

        if self.value < 50:
            res += 1
        elif self.value < 250:
            res += 3
        elif self.value < 750:
            res += 5
        else:
            res += 9
        res *= 2
        match self.vendor_rarity:
            case "common":
                res += 1
            case "uncommon":
                res += 2
            case "rare":
                res += 4
            case "limited":
                res += 7
            case _:
                res += 9
        res *= 2
        if self.unique_to in ["", "Requiem"]:
            res += 1
        elif self.unique_to == "Fishing":
            res += 9
        else:
            res += 4
        res *= 10
        res += self.value
        res *= 2
        res += round(self.average_potency_price, 2)

        return res


if __name__ == "__main__":
    Ingredient.read_all()
    for ingredient in Data.ingredients:
        print(ingredient)
