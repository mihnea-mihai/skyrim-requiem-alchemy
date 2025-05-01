from __future__ import annotations
import csv

from collections.abc import Generator
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal
from statistics import median


class Data:

    @classmethod
    def convert(cls, value: str) -> int | float | str | bool | None:
        if value == "yes":
            return True
        if value == "no":
            return False
        if value == "":
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    @classmethod
    def readcsv(cls, path: str) -> Generator[dict]:
        with open(f"data/{path}.csv", encoding="utf-8") as file_in:
            for row in csv.DictReader(file_in):
                yield {key: cls.convert(value) for key, value in row.items()}

    @classmethod
    def populate(cls):
        cls.effects = {row["name"]: Effect(**row) for row in cls.readcsv("effects")}
        cls.ingredients = {
            row["name"]: Ingredient(**row) for row in cls.readcsv("ingredients")
        }

        cls.traits = defaultdict(dict)
        for row in cls.readcsv("traits"):
            cls.traits[row["ingredient_name"]][row["effect_name"]] = Trait(**row)


@dataclass(frozen=True)
class Effect:
    name: str
    effect_type: Literal["beneficial", "harmful"]
    base_cost: float

    @property
    def median_magnitude(self) -> float:
        return median(t.magnitude for t in Trait.by_effect(self.name))

    @property
    def median_duration(self) -> float:
        return median(t.duration for t in Trait.by_effect(self.name))

    @property
    def median_price(self) -> float:
        median_magnitude_factor = 1
        median_duration_factor = 1
        if self.median_magnitude:
            median_magnitude_factor = self.median_magnitude
        if self.median_duration:
            median_duration_factor = self.median_duration / 10
        median_value = pow(median_magnitude_factor * median_duration_factor, 1.1)

        return median_value * self.base_cost


@dataclass(frozen=True)
class Ingredient:
    name: str
    value: int
    plantable: bool
    vendor_rarity: Literal["common", "uncommon", "rare", "limited"] | None
    unique_to: (
        Literal["ResourcePack", "Hearthfire", "Dawnguard", "Dragonborn", "Requiem"]
        | None
    )


@dataclass(frozen=True)
class Trait:
    ingredient_name: str
    effect_name: str
    magnitude: float
    duration: int

    @classmethod
    def by_effect(cls, effect: str) -> Generator[Trait]:
        for eff_obj in Data.traits.values():
            if effect in eff_obj:
                yield eff_obj[effect]


Data.populate()

for tr in Trait.by_effect(Data.effects["Waterbreathing"]):
    print(tr)
