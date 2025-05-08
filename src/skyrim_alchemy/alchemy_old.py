from __future__ import annotations

import csv
from collections.abc import Generator
from statistics import median
from typing import Any, Literal, Optional


class Trait:
    pass


class Effect:
    def __init__(self, row: dict[str, Any]):
        self.name: str
        self.effect_type: str
        self.base_cost: float
        self.traits: set[Trait]
        self.ingredients: set[Ingredient]
        self.potencies: set[Potency]
        self.median_magnitude: float
        self.median_duration: float
        self.median_price: float

        for key, value in row.items():
            self.__setattr__(key, value)

    @classmethod
    def get(cls, name: str) -> Effect:
        for effect in Data.effects:
            if effect.name == name:
                return effect

    # def update(self):
    #     self.traits = [trait for trait in Data.traits if trait.potency.effect == self]
    #     self.ingredients = [trait.ingredient for trait in self.traits]
    #     self.potencies = sorted(
    #         {trait.potency for trait in self.traits}, key=lambda x: x.price
    #     )
    #     self.median_magnitude = median(trait.potency.magnitude for trait in self.traits)
    #     self.median_duration = median(trait.potency.duration for trait in self.traits)
    #     self.median_price = (
    #         Data.compute_base_value(self.median_magnitude, self.median_duration)
    #         * self.base_cost
    #     )

    def __repr__(self):
        return f"Effect({self.name})"

    def __eq__(self, value: Effect):
        return self.name == value.name

    def __hash__(self):
        return hash(self.name)


class Potency:
    def __init__(self, row: dict[str, Any]):
        self.effect: Effect = Effect.get(row["effect_name"])
        self.magnitude: float = row["magnitude"]
        self.duration: int = row["duration"]
        self.magnitude_mult: float
        self.duration_mult: float
        self.price: float
        self.price_mult: float
        self.traits: list[Trait]
        self.ingredients: list[Ingredient]

        self.price = (
            Data.compute_base_value(self.magnitude, self.duration)
            * self.effect.base_cost
        )

        for key, value in row.items():
            self.__setattr__(key, value)

    def __repr__(self):
        return f"Potency({self.effect}, {self.price_mult:.1f})"

    @classmethod
    def get(cls, row: dict[str, Any]) -> Potency:
        for potency in Data.potencies:
            if (
                potency.effect == Effect.get(row["effect_name"])
                and potency.magnitude == row["magnitude"]
                and potency.duration == row["duration"]
            ):
                return potency
        pot = Potency(row)
        Data.potencies.append(pot)
        return pot

    def update(self):
        self.magnitude_mult = Data.compute_multiplier(
            self.magnitude, self.effect.median_magnitude
        )
        self.duration_mult = Data.compute_multiplier(
            self.duration, self.effect.median_duration
        )
        self.price_mult = Data.compute_multiplier(self.price, self.effect.median_price)
        self.traits = [trait for trait in Data.traits if trait.potency == self]
        self.ingredients = [trait.ingredient for trait in self.traits]


class Potion:
    pass


class Ingredient:
    def __init__(self, row: dict[str, Any]):

        self.name: str
        self.value: int
        self.plantable: bool
        self.vendor_rarity: str
        self.unique_to: str
        self.traits: set[Trait]
        self.effects: set["Effect"]

        for key, value in row.items():
            self.__setattr__(key, value)

    def __repr__(self):
        return f"Ingredient({self.name})"

    def effects_by_ingredient(self, ingredient: Ingredient) -> set[Effect]:
        return set(self.effects).intersection(ingredient.effects)

    def get_trait_by_effects(self, effect: Effect) -> Trait:
        for trait in self.traits:
            if trait.effect == effect:
                return trait

    @classmethod
    def get(cls, name: str) -> Ingredient:
        for ingredient in Data.ingredients:
            if ingredient.name == name:
                return ingredient

    # def update1(self):
    #     self.traits = [trait for trait in Data.traits if trait.ingredient == self]
    #     self.effects = [trait.potency.effect for trait in self.traits]

    # def update2(self):
    #     self.compatible_ingredients = [
    #         ingredient
    #         for ingredient in Data.ingredients
    #         if set(ingredient.effects).intersection(self.effects) and self != ingredient
    #     ]

    #     self.compatibilities = {
    #         ingredient: effects
    #         for ingredient in Data.ingredients
    #         if (effects := set(ingredient.effects).intersection(self.effects))
    #         and self != ingredient
    #     }


class Data:
    """Wrapper for all data."""

    ingredients: set[Ingredient]
    """Set of all available ingredients."""

    effects: set[Effect]
    potencies: set[Potency]
    traits: set[Trait]
    potions: set[Potion]

    @classmethod
    def compute_base_value(cls, magnitude: float, duration: int) -> float:
        magnitude_factor = 1
        duration_factor = 1
        if magnitude:
            magnitude_factor = magnitude
        if duration:
            duration_factor = duration / 10
        return pow(magnitude_factor * duration_factor, 1.1)

    @classmethod
    def compute_multiplier(cls, value, median_value) -> float:
        if value == median_value:
            return 1
        if median_value == 0:
            return value
        return value / median_value

    @classmethod
    def _convert(cls, value: str) -> int | float | str | bool | None:
        if value == "yes":
            return True
        if value == "no":
            return False
        # if value == "":
        #     return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    @classmethod
    def _readcsv(cls, path: str) -> Generator[dict]:
        with open(f"data/{path}.csv", encoding="utf-8") as file_in:
            for row in csv.DictReader(file_in):
                yield {key: cls._convert(value) for key, value in row.items()}

    @classmethod
    def populate(cls):
        # cls.effects = {Effect(row) for row in cls._readcsv("effects")}
        cls.ingredients = {Ingredient(row) for row in cls._readcsv("ingredients")}
        # cls.traits = [Trait(row) for row in cls._readcsv("traits")]
        # for effect in cls.effects:
        #     effect.update()
        # for ingredient in cls.ingredients:
        #     ingredient.update1()
        # for potency in cls.potencies:
        #     potency.update()
        # for ingredient in cls.ingredients:
        #     ingredient.update2()
        # tried_mixtures = set()
        # cls.potions: set[Potion] = set()
        # for ing1 in Data.ingredients.values():
        #     for ing2 in Data.ingredients.values():
        #         key = frozenset({ing1, ing2})
        #         if key in tried_mixtures:
        #             continue
        #         tried_mixtures.add(key)
        #         p = Potion(key)
        #         if p.pure:
        #             cls.potions.add(p)
        #             for ing3 in Data.ingredients.values():
        #                 key2 = frozenset({ing1, ing2, ing3})
        #                 if key2 in tried_mixtures:
        #                     continue
        #                 tried_mixtures.add(key2)
        #                 p2 = Potion(key2)
        #                 if p2.pure and len(p2.effects) > len(p.effects):
        #                     cls.potions.add(p2)


if __name__ == "__main__":
    Data.populate()
    # for ing in Data.ingredients:
    #     print(ing)
    # ing = Ingredient.get("Nirnroot")
    # print(ing.__dict__)
