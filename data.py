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

        tried_mixtures = set()
        cls.potions: set[Potion] = set()
        for ing1 in Data.ingredients.values():
            for ing2 in Data.ingredients.values():
                key = frozenset({ing1, ing2})
                if key in tried_mixtures:
                    continue
                tried_mixtures.add(key)
                p = Potion(key)
                if p.pure:
                    cls.potions.add(p)
                    for ing3 in Data.ingredients.values():
                        key2 = frozenset({ing1, ing2, ing3})
                        if key2 in tried_mixtures:
                            continue
                        tried_mixtures.add(key2)
                        p2 = Potion(key2)
                        if p2.pure and len(p2.effects) > len(p.effects):
                            cls.potions.add(p2)


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

    @property
    def traits(self) -> Generator[Trait]:
        return Trait.by_effect(self.name)


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

    @property
    def traits(self) -> Generator[Trait]:
        return Trait.by_ingredient(self.name)


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

    @classmethod
    def by_ingredient(cls, ingredient: str) -> Generator[Trait]:
        yield from Data.traits[ingredient].values()

    @property
    def effect(self) -> Effect:
        return Data.effects[self.effect_name]

    @property
    def ingredient(self) -> Ingredient:
        return Data.ingredients[self.ingredient_name]

    @property
    def magnitude_mult(self) -> float:
        mag = self.magnitude
        med_mag = self.effect.median_magnitude
        if mag == med_mag:
            return 1
        if med_mag == 0:
            return mag
        return mag / med_mag

    @property
    def duration_mult(self) -> float:
        dur = self.duration
        med_dur = self.effect.median_duration
        if dur == med_dur:
            return 1
        if med_dur == 0:
            return dur
        return dur / med_dur

    @property
    def median_price(self) -> float:
        return self.effect.pr

    @property
    def price(self) -> float:
        magnitude_factor = 1
        duration_factor = 1
        if self.magnitude:
            magnitude_factor = self.magnitude
        if self.duration:
            duration_factor = self.duration / 10
        value = pow(magnitude_factor * duration_factor, 1.1)

        return value * self.effect.base_cost

    @property
    def price_mult(self) -> float:
        price = self.price
        median_price = self.effect.median_price
        if price == median_price:
            return 1
        return price / median_price


@dataclass(frozen=True)
class Potion:
    ingredients: frozenset[Ingredient]

    @property
    def effects(self) -> frozenset[Effect]:
        combined_effects = [tr.effect for ing in self.ingredients for tr in ing.traits]
        valid_effects = [
            effect for effect in combined_effects if combined_effects.count(effect) > 1
        ]
        return frozenset(valid_effects)

    @property
    def pure(self) -> bool:
        effects = self.effects
        if not effects:
            return False
        first = list(effects)[0].effect_type
        for effect in effects:
            if effect.effect_type != first:
                return False
        return True


if __name__ == "__main__":
    Data.populate()


