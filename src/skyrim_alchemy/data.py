"""
Data model.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Generator
from dataclasses import dataclass, field
from functools import cache, cached_property
from statistics import median, mean
from typing import NamedTuple
from skyrim_alchemy.logger import logger
from skyrim_alchemy.utils import value_formula

from types import MappingProxyType

# from pprint import pprint
from typing import Literal, Optional


@dataclass
class Ingredient:
    """Alchemy ingredient.
    Only the `name` field is used for hash and equality."""

    _row: dict

    @cached_property
    def name(self) -> str:
        """Ingredient name."""
        return self._row["name"]

    @cached_property
    def value(self) -> int:
        """Ingredient septim cost."""
        return int(self._row["value"])

    @cached_property
    def plantable(self) -> bool:
        """Whether or not the ingredient can be planted in Hearthfire."""
        return bool(self._row["plantable"])

    @cached_property
    def vendor_rarity(
        self,
    ) -> Optional[Literal["common", "uncommon", "rare", "limited"]]:
        """What is the possibility of finding/buying this ingredient.
        Missing value means it is unsold."""
        return self._row["vendor_rarity"]

    @cached_property
    def unique_to(
        self,
    ) -> Optional[
        Literal[
            "ResourcePack",
            "Dawnguard",
            "Dragonborn",
            "Fishing",
            "Hearthfire",
            "Requiem",
        ]
    ]:
        """The plugin that introduces this ingredient, if applicable."""
        return self._row["unique_to"]

    @cached_property
    def average_price(self) -> float:
        """The average price of this ingredient's potencies."""
        return mean({potency.price for potency in self.potencies})

    @cached_property
    def traits(self) -> set[Trait]:
        """Subset of `Trait` entries pertaining to this ingredient."""
        return {trait for trait in Data.traits if trait.ingredient == self}

    @cached_property
    def potencies(self) -> set[Potency]:
        """Subset of `Potency` entries pertaining to this ingredient."""
        return {trait.potency for trait in self.traits}

    @cached_property
    def effects(self) -> set[Effect]:
        """Subset of `Effect` entries pertaining to this ingredient."""
        return {potency.effect for potency in self.potencies}

    @cached_property
    def compatible_ingredients(self) -> set[Ingredient]:
        """Subset of other ingredients having at least a single effect in common
        with the current one."""
        return {
            ingredient
            for ingredient in Data.ingredients - {self}
            if ingredient.effects.intersection(self.effects)
        }

    @classmethod
    def create(cls, row: dict) -> Ingredient:
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


@dataclass
class Effect:
    """Alchemy effect.
    Only the `name` field is used for hash and equality."""

    _row: dict

    @cached_property
    def name(self) -> str:
        """Effect name."""
        return self._row["name"]

    @cached_property
    def effect_type(self) -> Literal["beneficial", "harmful"]:
        """Type of effect: positive (`beneficial`) or negative (`harmful`)."""
        return self._row["effect_type"]

    @cached_property
    def base_cost(self) -> float:
        """The base cost of this effect, which is later used in calculations
        for potion value."""
        return float(self._row["base_cost"])

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

    @cached_property
    def potencies(self) -> dict[Potency, set[Trait]]:
        """Dictionary of all `Potency` entries pertaining to this effect
        (acting as keys) and the subset of traits pertaining to that potency
        (acting as values). This basically groups effect traits by potencies.
        """
        res = defaultdict(set)
        for trait in self.traits:
            res[trait.potency].add(trait)
        return res

    @cached_property
    def ingredients(self) -> set[Ingredient]:
        """Subset of ingredients pertaining to this effect."""
        return {trait.ingredient for trait in self.traits}

    @classmethod
    def create(cls, row: dict) -> Effect:
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


class TraitRow(NamedTuple):
    ingredient_name: str
    effect_name: str
    magnitude: float
    duration: int
    order: int


@dataclass
class Trait:
    _row: TraitRow

    @cached_property
    def ingredient(self) -> Ingredient:
        return Ingredient.get(self._row.ingredient_name)

    @cached_property
    def potency(self) -> Potency:
        return Potency.create(self._row)

    @cached_property
    def order(self) -> int:
        return int(self._row.order)

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


@dataclass
class Potency:
    """Alchemy potency. `effect`, `magnitude` and `duration` are all used
    for hash and equality."""

    _row: TraitRow

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
    def effect(self) -> Effect:
        return Effect.get(self._row.effect_name)

    @cached_property
    def magnitude(self) -> float:
        return float(self._row.magnitude)

    @cached_property
    def duration(self) -> int:
        return int(self._row.duration)

    @cached_property
    def price(self) -> float:
        return value_formula(self.magnitude, self.duration) * self.effect.base_cost

    @cached_property
    def traits(self) -> set[Trait]:
        """Subset of `Trait` entries pertaining to this potency."""
        return {trait for trait in self.effect.traits if trait.potency == self}

    @cached_property
    def ingredients(self) -> set[Ingredient]:
        return {trait.ingredient for trait in self.traits}

    @classmethod
    @cache  # this ensures no duplicates
    def create(cls, row: MappingProxyType) -> Potency:
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
            Ingredient.create(row)
        for row in cls.csv_to_dict("effects"):
            Effect.create(row)
        for row in cls.csv_to_dict("traits"):
            Trait.create(TraitRow(**row))

    @classmethod
    def populate(cls):
        cls.read_csvs()
        cls.grouped_potions = defaultdict(dict)
        for ingredient1 in cls.ingredients:
            for ingredient2 in cls.ingredients:
                if ingredient2 in ingredient1.compatible_ingredients:
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
