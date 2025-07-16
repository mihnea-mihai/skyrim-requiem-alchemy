from __future__ import annotations

from functools import cache, cached_property
from itertools import groupby
from statistics import mean, median
from typing import TYPE_CHECKING

from skyrim_alchemy.data import Data
from skyrim_alchemy.logger import logger
from skyrim_alchemy.utils import read_csv

import math

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
    def compatible_ingredients(self) -> list[Ingredient]:
        return sorted(
            i
            for i in Data.ingredients
            if set(i.effects) & set(self.effects) and i != self
        )

    def __repr__(self):
        return f"Ingredient({self.name})"

    def __lt__(self, other: Ingredient):
        if self.accessibility < other.accessibility:
            return True
        if self.accessibility > other.accessibility:
            return False
        return self.name < other.name

    @staticmethod
    @cache
    def get(name: str) -> Ingredient:
        for ing in Data.ingredients:
            if ing.name == name:
                return ing

    @cached_property
    def accessibility(self) -> float:
        # res: float = pow(int(math.sqrt(self.value)), 2)
        # res: float = 1.0

        res = (self.value // 25 + 1) * 100
        # res = self.value * 1000
        match self.vendor_rarity:
            case "common":
                res *= 1
            case "uncommon":
                res *= 2
            case "rare":
                res *= 5
            case "limited":
                res *= 20
            case _:
                res *= 30

        if self.plantable:
            # res = math.log(res + 1)
            res = math.sqrt(res)
        # else:
        #     res *= 30

        # return res

        # res += (self.value // 50 + 1) * 50 + self.value

        # res += self.value
        # # res += math.sqrt(self.value)
        # # if not self.plantable:
        # #     res *= 2
        # # else:
        # #     res *= 0.1

        # match self.vendor_rarity:
        #     case "common":
        #         res = 1 * (self.value // 5 + 1)
        #     case "uncommon":
        #         res = 2 * (self.value // 5 + 1)
        #     case "rare":
        #         res = 4 * (self.value // 5 + 1)
        #     case "limited":
        #         res = 7 * (self.value // 5 + 1)
        #     case _:
        #         res = ((self.value - 10) // 10 + 2) * 100
        match self.unique_to:
            case "Requiem":
                res *= 1
            case "":
                res *= 1
            case "Fishing":
                res *= 2
            case _:
                res *= 1.5

        # if self.plantable:
        #     res = math.sqrt(res)
        # print(self.name, res)
        # # res += self.value
        res += self.average_potency_price + self.value
        return res

    @cached_property
    def valuable_potions(self) -> list[Potion]:
        return sorted(self.potions, key=lambda p: p.relative_value, reverse=True)[:10]


if __name__ == "__main__":
    Ingredient.read_all()
    for ingredient in Data.ingredients:
        print(ingredient)
