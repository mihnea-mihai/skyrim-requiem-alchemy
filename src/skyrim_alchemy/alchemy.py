from __future__ import annotations

import csv
from skyrim_alchemy.logger import logger
from functools import cache, cached_property
from itertools import combinations, pairwise
from collections import defaultdict

from skyrim_alchemy.utils import value_formula

from statistics import mean, median


class Ingredient:
    def __init__(self, row: dict):
        self.name: str = row["name"]
        self.value: int = int(row["value"])
        self.plantable: bool = row["plantable"] == "True"
        self.vendor_rarity: str = row["vendor_rarity"]
        self.unique_to: str = row["unique_to"]
        self.traits: list[Trait] = []
        self.effects: list[Effect] = []
        self.potencies: list[Potency] = []
        self.traits_by_effects: dict[Effect, list[Trait]] = {}
        self.potions: list[Potion] = []
        self.average_potion_price: float = 0
        self.median_potion_price: float = 0

    def __repr__(self):
        return f"Ingredient({self.name})"

    def __lt__(self, other: Ingredient):
        return self.accessibility_factor < other.accessibility_factor

    @cached_property
    def accessibility_factor(self) -> int:
        res = 0
        if self.plantable:
            res += 2
        elif self.name in ["Daedra Heart", "Strange Remains"]:
            res += 9
        else:
            res += 5
        res *= 10

        if self.value < 50:
            res += 1
        elif self.value < 250:
            res += 3
        else:
            res += 9
        res *= 10
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
        res *= 10
        if self.unique_to in ["", "Requiem"]:
            res += 1
        elif self.unique_to == "Fishing":
            res += 9
        else:
            res += 4
        res *= 1000
        res += self.value
        res *= 100
        res += round(self.average_potency_price, 2)

        return res

    @cached_property
    def average_potency_price(self):
        return mean({potency.price for potency in self.potencies})

    @staticmethod
    def from_row(row: dict) -> None:
        ing = Ingredient(row)
        logger.info("Created ingredient %s", ing)
        Data.ingredients.append(ing)

    @staticmethod
    @cache
    def get(name: str) -> Ingredient:
        for ing in Data.ingredients:
            if ing.name == name:
                return ing

    @cached_property
    def compatible_ingredients(self) -> list[Ingredient]:
        res = [
            trait.ingredient
            for trait in Data.traits
            if trait.potency.effect in self.effects
        ]
        res.remove(self)
        return res


class Effect:
    def __init__(self, row: dict):
        self.name: str = row["name"]
        self.effect_type: str = row["effect_type"]
        self.base_cost: float = float(row["base_cost"])
        self.median_magnitude: float = 0
        self.median_duration: int = 0
        self.median_price: float = 0
        self.traits: list[Trait] = []
        self.potencies: list[Potency] = []
        self.ingredients: list[Ingredient] = []
        self.traits_by_potencies: dict[Potency, list[Trait]] = defaultdict(list)
        self.median_accessibility: float = 0

    def __repr__(self):
        return f"Effect({self.name})"

    @staticmethod
    def from_row(row: dict) -> None:
        eff = Effect(row)
        logger.info("Created effect %s", eff)
        Data.effects.append(eff)

    @staticmethod
    @cache
    def get(name: str) -> Effect:
        for eff in Data.effects:
            if eff.name == name:
                return eff


class Trait:

    def __init__(self, row: dict):
        self.ingredient: Ingredient = Ingredient.get(row["ingredient_name"])
        self.potency: Potency = Potency.create(
            Effect.get(row["effect_name"]),
            float(row["magnitude"]),
            int(row["duration"]),
        )
        self.order: int = int(row["order"])

    def __repr__(self):
        return f"Trait({self.ingredient.name}, {self.potency}, {self.order})"

    @staticmethod
    def from_row(row: dict) -> None:
        trait = Trait(row)
        logger.info("Created trait %s", trait)
        Data.traits.append(trait)
        ing = trait.ingredient
        eff = trait.potency.effect
        pot = trait.potency
        ing.traits.append(trait)
        ing.potencies.append(pot)
        ing.effects.append(eff)
        ing.traits_by_effects[eff] = {trait}
        eff.traits.append(trait)
        eff.potencies.append(pot)
        eff.ingredients.append(ing)
        eff.traits_by_potencies[pot].append(trait)


class Potency:

    def __init__(self, effect: Effect, magnitude: float, duration: int):
        self.effect: Effect = effect
        self.magnitude: float = magnitude
        self.duration: int = duration
        self.price: float = (
            value_formula(self.magnitude, self.duration) * self.effect.base_cost
        )

    @staticmethod
    @cache  # cache ensures no duplicates
    def create(effect: Effect, magnitude: float, duration: int) -> Potency:
        pot = Potency(effect, magnitude, duration)
        logger.info("Created potency %s", pot)
        Data.potencies.append(pot)
        return pot

    def __lt__(self, other: Potency):
        return self.price < other.price

    def __repr__(self):
        return f"Potency({self.effect.name}, {self.magnitude}, {self.duration})"


class Data:
    ingredients: list[Ingredient] = []
    effects: list[Effect] = []
    traits: list[Trait] = []
    potencies: list[Potency] = []
    potions: list[Potion] = []
    potions_by_potencies: dict[tuple[Potency], list[Potion]] = defaultdict(list)
    potions_by_effects: dict[tuple[Effect], list[Potion]] = defaultdict(list)


class Potion:
    def __init__(self, ingredients: tuple[Ingredient]):
        self.ingredients: tuple[Ingredient] = ingredients

    @cached_property
    def traits_by_effects(self) -> dict[Effect, set[Trait]]:
        res = defaultdict(set)
        for ing in self.ingredients:
            for effect, traits in ing.traits_by_effects.items():
                res[effect] |= traits
        return res

    @cached_property
    def potencies(self) -> tuple[Potency]:
        cmp = tuple(
            sorted(
                [
                    max({t.potency for t in traits}, key=lambda t: t.price)
                    for traits in self.traits_by_effects.values()
                    if len(traits) > 1
                ],
                key=lambda p: p.effect.name,
            )
        )

        for potencies in Data.potions_by_potencies:
            if potencies == cmp:
                return potencies
        return cmp

    @cached_property
    def effects(self) -> tuple[Effect]:
        cmp = tuple(
            sorted(
                [
                    effect
                    for effect, traits in self.traits_by_effects.items()
                    if len(traits) > 1
                ],
                key=lambda e: e.name,
            )
        )

        for effects in Data.potions_by_effects:
            if effects == cmp:
                return effects
        return cmp

    @cached_property
    def ingredients_flag(self) -> str:
        if all(ing.plantable for ing in self.ingredients):
            return "plantable"
        if all(ing.vendor_rarity == "common" for ing in self.ingredients):
            return "common"
        if all(ing.vendor_rarity in ["common", "uncommon"] for ing in self.ingredients):
            return "uncommon"
        if all(
            ing.vendor_rarity in ["common", "uncommon", "rare"]
            for ing in self.ingredients
        ):
            return "rare"
        return ""

    @cached_property
    def accessibility(self) -> float:
        return sum(ing.accessibility_factor for ing in self.ingredients)

    @cached_property
    def price(self) -> float:
        return sum(pot.price for pot in self.potencies)

    @cached_property
    def pure(self) -> bool:
        # return True
        for pot1, pot2 in pairwise(self.potencies):
            if pot1.effect.effect_type != pot2.effect.effect_type:
                return False
        return True

    @staticmethod
    def from_ingredients(ingredients: tuple[Ingredient]) -> None | Potion:
        if len(ingredients) > len(set(ingredients)):
            return
        potion = Potion(ingredients)
        if not potion.potencies:
            return
        if not potion.pure:
            return

        if len(potion.ingredients) == 3:
            for ing1, ing2 in combinations(potion.ingredients, 2):
                mini_potion = Potion((ing1, ing2))
                if not mini_potion:
                    continue
                if potion.potencies == mini_potion.potencies:
                    return

        logger.info("Created potion of %s : %s", len(potion.ingredients), potion)

        Data.potions.append(potion)
        Data.potions_by_potencies[potion.potencies].append(potion)
        Data.potions_by_effects[potion.effects].append(potion)
        for ing in ingredients:
            ing.potions.append(potion)
        return potion

    def __repr__(self):
        return f"Potion{str(self.ingredients)}"


def explore():
    print(f"Ingredients: {len(Data.ingredients)}")
    print(f"Effects: {len(Data.effects)}")
    print(f"Potencies: {len(Data.potencies)}")
    print(f"Traits: {len(Data.traits)}")
    print(f"Potions: {len(Data.potions)}")
    print(f"Potion potencies: {len(Data.potions_by_potencies)}")
    print(f"Potion effects: {len(Data.potions_by_effects)}")


def read():
    with open("data/ingredients.csv", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            Ingredient.from_row(row)
    with open("data/effects.csv", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            Effect.from_row(row)
    with open("data/traits.csv", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            Trait.from_row(row)

    for eff in Data.effects:
        eff.median_magnitude = median([trait.potency.magnitude for trait in eff.traits])
        eff.median_duration = median([trait.potency.duration for trait in eff.traits])
        eff.median_price = (
            value_formula(eff.median_magnitude, eff.median_duration) * eff.base_cost
        )
        eff.median_accessibility = median(
            ing.accessibility_factor for ing in eff.ingredients
        )

    for ing1, ing2 in combinations(Data.ingredients, 2):
        Potion.from_ingredients(tuple(sorted([ing1, ing2])))

    for ing1, ing2, ing3 in combinations(Data.ingredients, 3):
        Potion.from_ingredients(tuple(sorted([ing1, ing2, ing3])))

    for ing in Data.ingredients:
        ing.average_potion_price = mean(potion.price for potion in ing.potions)
        ing.median_potion_price = median(potion.price for potion in ing.potions)

    for potencies, potions in Data.potions_by_potencies.items():
        Data.potions_by_potencies[potencies] = sorted(
            potions, key=lambda p: p.ingredients
        )


if __name__ == "__main__":
    read()
    explore()
