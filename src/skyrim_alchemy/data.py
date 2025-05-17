from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Generator
from dataclasses import dataclass, field
from functools import cache, cached_property
from statistics import median
from pprint import pprint
from skyrim_alchemy.utils import coerce_fields, value_formula
from skyrim_alchemy.logger import logger
from itertools import chain


@dataclass(unsafe_hash=True)
class Ingredient:
    name: str = field(compare=True)
    value: int = field(repr=False, compare=False)
    plantable: bool = field(repr=False, compare=False)
    vendor_rarity: str = field(repr=False, compare=False)
    unique_to: str = field(repr=False, compare=False)

    def __post_init__(self):
        coerce_fields(self)

    def __str__(self):
        return f"Ingredient({self.name})"

    @cached_property
    def traits(self) -> set[Trait]:
        return {trait for trait in Data.traits if trait.ingredient == self}

    @cached_property
    def potencies(self) -> set[Potency]:
        return {trait.potency for trait in self.traits}

    @cached_property
    def effects(self) -> set[Effect]:
        return {potency.effect for potency in self.potencies}

    @cached_property
    def ingredients(self) -> set[Ingredient]:
        return {
            trait.ingredient
            for trait in Data.traits
            if trait.potency.effect in self.effects
        }

    @classmethod
    def create(cls, row: dict) -> Ingredient:
        ingredient = Ingredient(**row)
        logger.info("Created ingredient %s", ingredient)
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
    effect_type: str = field(repr=False, compare=False)
    base_cost: float = field(repr=False, compare=False)

    def __post_init__(self):
        coerce_fields(self)

    def __str__(self):
        return f"Effect({self.name})"

    @cached_property
    def traits(self) -> set[Trait]:
        return {trait for trait in Data.traits if trait.potency.effect == self}

    @cached_property
    def potencies(self) -> set[Potency]:
        grouped_potencies = defaultdict(set)
        for trait in self.traits:
            grouped_potencies[trait.potency].add(trait)
        return grouped_potencies

    @cached_property
    def ingredients(self) -> set[Ingredient]:
        return {trait.ingredient for trait in self.traits}

    @cached_property
    def median_magnitude(self) -> float:
        return median(trait.potency.magnitude for trait in self.traits)

    @cached_property
    def median_duration(self) -> float:
        return median(trait.potency.duration for trait in self.traits)

    @cached_property
    def median_price(self) -> float:
        return median(trait.potency.price for trait in self.traits)

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
    order: int = field(repr=False, compare=False)

    def __str__(self):
        return f"Trait({self.ingredient},{self.potency})"

    def __gt__(self, obj: Trait):
        return self.potency.price > obj.potency.price

    @classmethod
    def create(cls, row: dict) -> Trait:
        trait = Trait(
            Ingredient.get(row["ingredient_name"]),
            Potency.create(
                row["effect_name"], float(row["magnitude"]), int(row["duration"])
            ),
            int(row["order"]),
        )
        logger.info("Created %s", trait)
        Data.traits.add(trait)
        return trait

    def match(
        self, obj: Ingredient | Effect | Potency
    ) -> Ingredient | Effect | Potency:
        match str(type(obj)):
            case "Ingredient":
                return self.ingredient
            case "Effect":
                return self.potency.effect
            case "Potency":
                return self.potency

    def match_in(self, cont: list[Ingredient | Effect | Potency]) -> bool:
        return self.match(cont[0]) in cont

    @classmethod
    @cache
    def get(cls, ingredient: Ingredient, effect: Effect) -> Trait:
        for trait in Data.traits:
            if trait.ingredient == ingredient and trait.potency.effect == effect:
                return trait


@dataclass(unsafe_hash=True)
class Potency:
    effect: Effect
    magnitude: float
    duration: int

    def __str__(self):
        return f"Potency({self.effect},{self.magnitude},{self.duration})"

    def __gt__(self, obj: Potency):
        return self.price > obj.price

    @cached_property
    def price(self) -> float:
        return value_formula(self.magnitude, self.duration) * self.effect.base_cost

    @cached_property
    def ingredients(self) -> set[Ingredient]:
        return {
            trait.ingredient for trait in self.effect.traits if trait.potency == self
        }

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
        return Trait.get(ingredient, effect).potency


@dataclass(unsafe_hash=True)
class Potion:
    ingredients: set[Ingredient]

    @cached_property
    def traits(self) -> set[Trait]:
        all_effects: dict[Effect, set[Trait]] = defaultdict(set)
        for trait in Data.traits:
            if trait.ingredient in self.ingredients:
                all_effects[trait.potency.effect].add(trait)

        return {max(traits) for traits in all_effects.values() if len(traits) > 1}

    @cached_property
    def potencies(self) -> set[Potency]:
        return {trait.potency for trait in self.traits}

    @cached_property
    def effects(self) -> set[Potency]:
        return {potency.effect for potency in self.potencies}

    @property
    def price(self) -> float:
        return sum(potency.price for potency in self.potencies)

    @classmethod
    @cache
    def create(cls, ingredients: frozenset[Ingredient]) -> Potion | None:
        potion = Potion(ingredients)
        if not len(potion.traits):
            return None
        return potion


class Data:
    ingredients: set[Ingredient] = set()
    effects: set[Effect] = set()
    traits: set[Trait] = set()
    potencies: set[Potency] = set()
    potions: set[Potion] = set()

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
    def populate(cls):
        cls.read_csvs()
        for ingredient1 in cls.ingredients:
            for ingredient2 in cls.ingredients:
                potion = Potion.create(frozenset({ingredient1, ingredient2}))
                if not potion:
                    continue
                Data.potions.add(potion)


if __name__ == "__main__":
    Data.read_csvs()
    # ingset = IngredientSet({Ingredient.get("Deathbell"), Ingredient.get("Canis Root")})
    # print(ingset.filter(Effect.get("Tardiness")))
    # for ing1 in Data.ingredients:
    #     for ing2 in Data.ingredients:
    #         p = Potion({ing1, ing2})
    #         if p.potencies:
    #             print(ing1, ing2, p.potencies)
    # if p.effects:
    #     print(ing1, ing2, p.effects)
    # print(Ingredient.__init__.__code__.co_varnames)
    # p = Potion({Ingredient.get("Deathbell"), Ingredient.get("Salt")})
    # print(p.potencies)
    # print(p.potencies)
    # p = Potion({Ingredient.get("Horker Fat"), Ingredient.get("Troll Fat")})
    # for eff in p.effects:
    #     print(eff)
    # filter(Ingredient.testname(2), Data.ingredients)
    eff = Effect.get("Damage Health")
    # pprint(eff.potencies)
    ing1 = Ingredient.get("Salt")
    ing2 = Ingredient.get("Deathbell")
    p = Potion({ing1, ing2})
    pprint(p.potencies)
