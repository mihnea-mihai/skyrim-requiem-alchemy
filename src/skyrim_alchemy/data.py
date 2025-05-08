from __future__ import annotations

import csv
import logging
from collections.abc import Generator
from dataclasses import dataclass, field, fields
from functools import cache, cached_property
from typing import Any

with open("alchemy.log", "w", encoding="utf-8"):
    pass

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="alchemy.log",
    format="%(levelname)s\t%(asctime)s\t%(message)s",
    level=logging.INFO,
)


ignorable = {"repr": False, "compare": False}


def coerce(value, type_):
    match type_:
        case "float":
            return float(value)
        case "int":
            return int(value)
        case "bool":
            return int(value)
    return value


@dataclass(unsafe_hash=True)
class Ingredient:
    name: str
    value: int = field(**ignorable)
    plantable: bool = field(**ignorable)
    vendor_rarity: str = field(**ignorable)
    unique_to: str = field(**ignorable)

    def __str__(self):
        return f"Ingredient({self.name})"

    @classmethod
    def create(cls, row: dict) -> Ingredient:
        ingredient = Ingredient(**row)
        logger.info("Created %s", ingredient)
        Data.ingredients.add(ingredient)
        return ingredient

    @classmethod
    @cache
    def get(cls, name: str) -> Ingredient:
        logger.info("Fetching ingredient %s", name)
        for ingredient in Data.ingredients:
            if ingredient.name == name:
                return ingredient


@dataclass(unsafe_hash=True)
class Effect:
    name: str
    effect_type: str = field(**ignorable)
    base_cost: float = field(**ignorable)

    def __post_init__(self):
        for fld in fields(self):
            if fld.type in ["float", "bool", "int"]:
                setattr(self, fld.name, coerce(getattr(self, fld.name), fld.type))

    def __str__(self):
        return f"Effect({self.name})"

    @classmethod
    def create(cls, row: dict) -> Effect:
        effect = Effect(**row)
        logger.info("Creating %s", effect)
        Data.effects.add(effect)
        return effect

    @classmethod
    @cache
    def get(cls, name: str) -> Effect:
        logger.info("Fetching effect %s", name)
        for effect in Data.effects:
            if effect.name == name:
                return effect


@dataclass(unsafe_hash=True)
class Trait:
    ingredient: Ingredient
    potency: Potency

    def __str__(self):
        return f"Trait({self.ingredient},{self.potency})"

    @classmethod
    def create(cls, row: dict) -> Trait:
        trait = Trait(
            Ingredient.get(row["ingredient_name"]),
            Potency.create(row["effect_name"], row["magnitude"], row["duration"]),
        )
        logger.info("Created %s", trait)
        Data.traits.add(trait)
        return trait

    @classmethod
    @cache
    def get(cls, ingredient_name: str, effect_name: str) -> Trait:
        for trait in Data.traits:
            if (
                trait.ingredient_name == ingredient_name
                and trait.effect_name == effect_name
            ):
                return trait


@dataclass(frozen=True)
class Potency:
    effect: Effect
    magnitude: float
    duration: int

    def __str__(self):
        return f"Potency({self.effect},{self.magnitude},{self.duration})"

    @classmethod
    @cache  # this ensures no duplicates
    def create(cls, effect_name: str, magnitude: float, duration: int) -> Potency:
        potency = Potency(Effect.get(effect_name), magnitude, duration)
        logger.info("Created %s", potency)
        Data.potencies.add(potency)
        return potency


class Data:
    ingredients: set[Ingredient] = set()
    effects: set[Effect] = set()
    traits: set[Trait] = set()
    potencies: set[Potency] = set()

    @classmethod
    def csv_to_dict(cls, name: str) -> Generator[dict]:
        with open(f"data/{name}.csv", encoding="utf-8") as file_in:
            yield from csv.DictReader(file_in)

    @classmethod
    def read_csvs(cls):
        for row in cls.csv_to_dict("ingredients"):
            Ingredient.create(row)
        for row in cls.csv_to_dict("effects"):
            Effect.create(row)
        for row in cls.csv_to_dict("traits"):
            Trait.create(row)

    @classmethod
    @cache
    def ingredients_sorted(cls) -> list[Ingredient]:
        return sorted(cls.ingredients, key=lambda x: x.name)


if __name__ == "__main__":
    Data.read_csvs()
    eff = Effect.get("Fear")
    print(type(eff.base_cost))
