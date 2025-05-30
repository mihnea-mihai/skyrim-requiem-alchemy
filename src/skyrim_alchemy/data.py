"""
Data model.
"""

from __future__ import annotations

import csv
from collections import defaultdict, namedtuple
from collections.abc import Generator
from dataclasses import dataclass
from functools import cache, cached_property
from statistics import mean, median
from typing import Literal, Optional

from skyrim_alchemy.logger import logger
from skyrim_alchemy.utils import value_formula


# class TraitSet(set):

#     @cached_property
#     def ingredients(self: set[Trait]) -> set[Ingredient]:
#         return {trait.ingredient for trait in self}

#     @cached_property
#     def potencies(self: set[Trait]) -> dict[Potency, Trait]:
#         res = defaultdict(set)
#         for trait in self:
#             res[trait.potency].add(trait)
#         return res

#     @cached_property
#     def effects(self: set[Trait]) -> set[Ingredient]:
#         return {trait.potency.effect for trait in self}


IngredientRow = namedtuple(
    "IngredientRow", "name,value,plantable,vendor_rarity,unique_to"
)


class Ingredient:
    """Alchemy ingredient.
    Only the `name` field is used for hash and equality."""

    def __init__(self, row: IngredientRow):
        self.name: str = row.name
        self.value = int(row.value)
        self.plantable = row.plantable == "True"
        self.vendor_rarity: Optional[
            Literal["common", "uncommon", "rare", "limited"]
        ] = row.vendor_rarity
        self.unique_to: Optional[
            Literal[
                "ResourcePack",
                "Dawnguard",
                "Dragonborn",
                "Fishing",
                "Hearthfire",
                "Requiem",
            ]
        ] = row.unique_to

    @cached_property
    def average_price(self) -> float:
        """The average price of this ingredient's potencies."""
        return mean({potency.price for potency in self.traits.potencies})

    @cached_property
    def traits(self) -> set[Trait]:
        """Subset of `Trait` entries pertaining to this ingredient."""
        return {trait for trait in Data.traits if trait.ingredient == self}

    @classmethod
    def create(cls, row: IngredientRow) -> Ingredient:
        """Create a new instance from a CSV row.
        No need for cache as this will only be called once per
        traversed CSV row.

        Also adds the entry to the `Data.ingredients` set.

        Parameters
        ----------
        row : dict
            CSV row as dictionary.

        Returns
        -------
        Ingredient
            Returned instance.
        """
        ingredient = Ingredient(row)
        logger.info("Created ingredient %s", ingredient)
        Data.ingredients.add(ingredient)
        return ingredient

    @classmethod
    @cache
    def get(cls, name: str) -> Ingredient:
        """Retrieve an existing `Ingredient` instance. Is cached so it
        only searches once for each ingredient.

        Parameters
        ----------
        name : str
            Name of the instance to return

        Returns
        -------
        Ingredient
            Retrieved instance.

        Raises
        ------
        KeyError
            If an `Ingredient` instance with this name is not found.
        """
        logger.info("Fetching ingredient %s", name)
        for ingredient in Data.ingredients:
            if ingredient.name == name:
                return ingredient
        raise KeyError(f"Ingredient {name} not found")

    def __repr__(self):
        return f"Ingredient({self.name})"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, ing: Ingredient):
        return self.name == ing.name


EffectRow = namedtuple("EffectRow", "name,effect_type,base_cost")


class Effect:
    """Alchemy effect.
    Only the `name` field is used for hash and equality."""

    def __init__(self, row: EffectRow):
        self.name: str = row.name
        self.effect_type: Literal["beneficial", "harmful"] = row.effect_type
        self.base_cost = float(row.base_cost)

    @cached_property
    def median_magnitude(self) -> float:
        """The median magnitude of this effect
        (median of all magnitudes of the effect's traits)."""
        return median(trait.potency.magnitude for trait in self.traits)

    @cached_property
    def median_duration(self) -> float:
        """The median duration of this effect
        (median of all durations of the effect's traits)."""
        return median(trait.potency.duration for trait in self.traits)

    @cached_property
    def median_price(self) -> float:
        """The median price of this effect
        (median of all prices of the effect's traits)."""
        return median(trait.potency.price for trait in self.traits)

    @cached_property
    def traits(self) -> set[Trait]:
        """Subset of `Trait` entries pertaining to this effect."""
        return {trait for trait in Data.traits if trait.potency.effect == self}

    @classmethod
    def create(cls, row: EffectRow) -> Effect:
        """Create a new instance from a CSV row.
        No need for cache as this will only be called once per
        traversed CSV row.

        Also adds the entry to the `Data.effects` set.

        Parameters
        ----------
        row : dict
            CSV row as dictionary.

        Returns
        -------
        Effect
            Returned instance.
        """
        effect = Effect(row)
        logger.info("Creating %s", effect)
        Data.effects.add(effect)
        return effect

    @classmethod
    @cache
    def get(cls, name: str) -> Effect:
        """Retrieve an existing `Effect` instance. Is cached so it
        only searches once for each effect.

        Parameters
        ----------
        name : str
            Name of the instance to return

        Returns
        -------
        Effect
            Retrieved instance.

        Raises
        ------
        KeyError
            If an `Effect` instance with this name is not found.
        """
        logger.info("Fetching effect %s", name)
        for effect in Data.effects:
            if effect.name == name:
                return effect
        raise KeyError(f"Effect {name} not found")

    def __repr__(self):
        return f"Effect({self.name})"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, eff: Effect):
        return self.name == eff.name


TraitRow = namedtuple(
    "TraitRow", "ingredient_name,effect_name,magnitude,duration,order"
)


class Trait:

    def __init__(self, row: TraitRow):
        self.ingredient = Ingredient.get(row.ingredient_name)
        self.potency = Potency.create(row)
        self.order = int(row.order)

    def __eq__(self, obj: Trait):
        return self.ingredient == obj.ingredient and self.potency == obj.potency

    def __hash__(self):
        return hash((self.ingredient, self.potency))

    def __repr__(self):
        return f"Trait({self.ingredient},{self.potency})"

    def __gt__(self, obj: Trait):
        return self.potency.price > obj.potency.price

    @classmethod
    def create(cls, row: TraitRow) -> Trait:
        trait = Trait(row)
        logger.info("Created %s", trait)
        Data.traits.add(trait)
        return trait

    # def match(
    #     self, obj: Ingredient | Effect | Potency
    # ) -> Ingredient | Effect | Potency:
    #     match str(type(obj)):
    #         case "Ingredient":
    #             return self.ingredient
    #         case "Effect":
    #             return self.potency.effect
    #         case "Potency":
    #             return self.potency

    # def match_in(self, cont: list[Ingredient | Effect | Potency]) -> bool:
    #     return self.match(cont[0]) in cont

    @classmethod
    @cache
    def get(cls, ingredient: Ingredient, effect: Effect) -> Trait:
        """Get a trait by Ingredient and Effect.

        Parameters
        ----------
        ingredient : Ingredient
            _description_
        effect : Effect
            _description_

        Returns
        -------
        Trait
            _description_
        """
        for trait in Data.traits:
            if trait.ingredient == ingredient and trait.potency.effect == effect:
                return trait


class Potency:
    """Alchemy potency. `effect`, `magnitude` and `duration` are all used
    for hash and equality."""

    def __init__(self, row: TraitRow):
        self.effect = Effect.get(row.effect_name)
        self.magnitude = float(row.magnitude)
        self.duration = int(row.duration)
        self.price = (
            value_formula(self.magnitude, self.duration) * self.effect.base_cost
        )

    def __repr__(self):
        return f"Potency({self.effect},{self.magnitude},{self.duration})"

    def __eq__(self, obj: Potency):
        return (
            self.effect == obj.effect
            and self.magnitude == obj.magnitude
            and self.duration == obj.duration
        )

    def __hash__(self):
        return hash((self.effect, self.magnitude, self.duration))

    def __gt__(self, obj: Potency):
        return self.price > obj.price

    @cached_property
    def traits(self) -> set[Trait]:
        """Subset of `Trait` entries pertaining to this potency."""
        return {trait for trait in self.effect.traits if trait.potency == self}

    @classmethod
    @cache  # this ensures no duplicates
    def create(cls, row: TraitRow) -> Potency:
        potency = Potency(row)
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
    def all_effects(self) -> dict[Effect, set[Trait]]:
        dct: dict[Effect, set[Trait]] = defaultdict(set)
        for trait in Data.traits:
            if trait.ingredient in self.ingredients:
                dct[trait.potency.effect].add(trait)
        return dct

    @cached_property
    def traits(self) -> set[Trait]:
        return {max(traits) for traits in self.all_effects.values() if len(traits) > 1}

    @cached_property
    def potencies(self) -> frozenset[Potency]:
        return frozenset({trait.potency for trait in self.traits})

    @cached_property
    def effects(self) -> set[Potency]:
        return {potency.effect for potency in self.potencies}

    @property
    def price(self) -> float:
        return sum(potency.price for potency in self.potencies)

    def adds_value(self, ingredient: Ingredient) -> bool:
        for potion_effect in self.all_effects:
            if potion_effect in ingredient.effects:
                if Trait.get(ingredient, potion_effect) > max(
                    self.all_effects[potion_effect]
                ):
                    return True
        return False

    @classmethod
    @cache
    def get_similar(cls, ingredients: set[Ingredient]) -> Potion:
        for potion in Data.potions:
            if len(ingredients.intersection(potion.ingredients)) > 1:
                return potion

    @classmethod
    @cache
    def create(cls, ingredients: frozenset[Ingredient]) -> Potion | None:
        potion = Potion(ingredients)
        # if len(potion.traits) == 0:
        #     return None
        # if len(ingredients) > 2:
        #     if len(potion.traits) == len(Potion.get_similar(ingredients).traits):
        #         return None
        #     return potion
        return potion


class Data:
    ingredients: set[Ingredient] = set()
    effects: set[Effect] = set()
    traits: set[Trait] = set()
    potencies: set[Potency] = set()
    potions: set[Potion] = set()
    grouped_potions: dict[frozenset[Potency], set[Potion]]

    @classmethod
    def csv_to_dict(cls, name: str) -> Generator[dict]:
        with open(f"data/{name}.csv", encoding="utf-8") as file_in:
            yield from csv.DictReader(file_in)

    @classmethod
    def read_csvs(cls):
        for row in cls.csv_to_dict("ingredients"):
            Ingredient.create(IngredientRow(**row))
        for row in cls.csv_to_dict("effects"):
            Effect.create(EffectRow(**row))
        for row in cls.csv_to_dict("traits"):
            Trait.create(TraitRow(**row))

    @classmethod
    def populate(cls):
        cls.read_csvs()
        cls.grouped_potions = defaultdict(dict)
        for ingredient1 in cls.ingredients:
            for ingredient2 in cls.ingredients:
                if ingredient2 in ingredient1.traits.ingredients:
                    potion = Potion.create(frozenset({ingredient1, ingredient2}))
                    cls.potions.add(potion)
                    cls.grouped_potions[frozenset(potion.potencies)] = potion
        # initial_potions = cls.potions.copy()
        # for potion in initial_potions:
        #     for ingredient in cls.ingredients:
        #         if ingredient in potion.ingredients:
        #             continue
        #         if potion.adds_value(ingredient):
        #             new_potion = Potion.create(
        #                 frozenset(potion.ingredients | {ingredient})
        #             )
        #             cls.potions.add(new_potion)
        #             cls.grouped_potions[frozenset(new_potion.potencies)] = new_potion


if __name__ == "__main__":
    Data.populate()
