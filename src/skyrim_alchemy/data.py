from __future__ import annotations

import csv
import logging
from collections.abc import Generator
from dataclasses import dataclass, field, fields
from functools import cache, cached_property
from typing import Any

from statistics import median

from skyrim_alchemy.utils import value_formula

with open("alchemy.log", "w", encoding="utf-8"):
    pass

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="alchemy.log",
    format="%(levelname)s\t%(asctime)s\t%(message)s",
    level=logging.INFO,
)


def IGNORABLE():
    # pylint: disable=invalid-field-call
    return field(repr=False, compare=False)


def COMPUTED():
    # pylint: disable=invalid-field-call
    return field(repr=False, compare=False, init=False)


def coerce(value, type_):
    match type_:
        case "float":
            return float(value)
        case "int":
            return int(value)
        case "bool":
            return value == "True"
    return value


def coerce_fields(obj: Any):
    for fld in fields(obj):
        val = getattr(obj, fld.name, None)
        if val and fld.type in ["float", "bool", "int"]:
            setattr(obj, fld.name, coerce(val, fld.type))


@dataclass(unsafe_hash=True)
class Ingredient:
    name: str = field(compare=True)
    value: int = IGNORABLE()
    plantable: bool = IGNORABLE()
    vendor_rarity: str = IGNORABLE()
    unique_to: str = IGNORABLE()

    @cached_property
    def traits(self) -> set[Trait]:
        return {trait for trait in Data.traits if trait.ingredient == self}

    @cached_property
    def potencies(self) -> set[Potency]:
        return {trait.potency for trait in self.traits}

    @cached_property
    def effects(self) -> set[Effect]:
        return {potency.effect for potency in self.potencies}

    def __str__(self):
        return f"Ingredient({self.name})"

    def __post_init__(self):
        coerce_fields(self)

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
    effect_type: str = IGNORABLE()
    base_cost: float = IGNORABLE()

    @cached_property
    def traits(self) -> set[Trait]:
        return {trait for trait in Data.traits if trait.potency.effect == self}

    @cached_property
    def potencies(self) -> set[Potency]:
        return {trait.potency for trait in self.traits}

    @cached_property
    def median_magnitude(self) -> float:
        return median(trait.potency.magnitude for trait in self.traits)

    @cached_property
    def median_duration(self) -> float:
        return median(trait.potency.duration for trait in self.traits)

    @cached_property
    def median_price(self) -> float:
        return median(trait.potency.price for trait in self.traits)

    def __post_init__(self):
        coerce_fields(self)

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
    order: int

    def __str__(self):
        return f"Trait({self.ingredient},{self.potency})"

    @classmethod
    def create(cls, row: dict) -> Trait:
        trait = Trait(
            Ingredient.get(row["ingredient_name"]),
            Potency.create(row["effect_name"], row["magnitude"], row["duration"]),
            row["order"],
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


@dataclass(unsafe_hash=True)
class Potency:
    effect: Effect
    magnitude: float
    duration: int
    price: float = COMPUTED()

    @cached_property
    def ingredients(self) -> set[Ingredient]:
        return {
            trait.ingredient for trait in self.effect.traits if trait.potency == self
        }

    def __str__(self):
        return f"Potency({self.effect},{self.magnitude},{self.duration})"

    def __post_init__(self):
        coerce_fields(self)
        self.price = (
            value_formula(self.magnitude, self.duration) * self.effect.base_cost
        )

    @classmethod
    @cache  # this ensures no duplicates
    def create(cls, effect_name: str, magnitude: float, duration: int) -> Potency:
        potency = Potency(Effect.get(effect_name), magnitude, duration)
        logger.info("Created %s", potency)
        Data.potencies.add(potency)
        return potency

    @classmethod
    @cache
    def get(cls, ingredient: Ingredient, effect: Effect) -> Potency:
        for potency in effect.potencies:
            if ingredient in potency.ingredients:
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
    for ing in Data.ingredients:
        print(ing.plantable)
    # print(Ingredient.__init__.__code__.co_varnames)
