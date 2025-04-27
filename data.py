"""Data model."""

from __future__ import annotations
import csv
from dataclasses import dataclass
from typing import Literal, Generator
from pprint import pprint

from statistics import median


class Data:  # pylint: disable=too-few-public-methods
    """Wrapper for data."""

    rows: list[Row] = []
    """List of all `Row` instances."""
    ingredients: list[Ingredient] = []
    """List of all `Ingredient` instances."""
    effects: list[Effect] = []
    """List of all `Effect` instances."""
    rows_dict: dict[str : dict[str:Row]] = {}
    potions: set[Potion] = set()

    @classmethod
    def _infer_value(cls, value: "str") -> int | float | str:
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    @classmethod
    def _csvrows(cls, path: str) -> Generator[dict]:
        """Read a CSV.

        Parameters
        ----------
        path : str
            CSV file name. Path will be built as `data/{path}.csv`.

        Returns
        -------
        list[dict]
            Each CSV row is a dictionary in the list.
        """
        with open(f"data/{path}.csv", encoding="utf-8") as file_in:
            for row in csv.DictReader(file_in):
                yield {key: cls._infer_value(value) for key, value in row.items()}
            # return list(csv.DictReader(file_in))

    @classmethod
    def populate(cls) -> None:
        """Fill the lists from CSV files."""
        cls.rows = [Row(**line) for line in cls._csvrows("values")]
        cls.ingredients = [Ingredient(**line) for line in cls._csvrows("ingredients")]
        cls.effects = [Effect(**line) for line in cls._csvrows("effects")]
        for row in cls.rows:
            if row.ingredient_name not in cls.rows_dict:
                cls.rows_dict[row.ingredient_name] = {}
            cls.rows_dict[row.ingredient_name][row.effect_name] = row


@dataclass(frozen=True)
class Row:
    """Maps ingredients to effects and magnitudes/durations."""

    ingredient_name: str
    """Name of the ingredient."""
    effect_name: str
    """Name of the effect."""
    magnitude: float
    """Absolute value of the magnitude."""
    duration: float
    """Absolute value of the duration."""

    # def __post_init__(self):
    #     if not self.magnitude:
    #         self.magnitude = 1
    #     if not self.duration:
    #         self.duration = 10

    def __lt__(self, other: Row) -> bool:
        return self.value < other.value

    @property
    def ingredient(self) -> Ingredient:
        """Return the `Ingredient` instance applicable to the current `Row`."""
        return Ingredient.get(self.ingredient_name)

    @property
    def effect(self) -> Effect:
        """Return the `Effect` instance applicable to the current `Row`."""
        return Effect.get(self.effect_name)

    @property
    def magnitude_mult(self) -> float:
        """Compare the current effect potency to the median value of the effect.
        If median magnitude is 0 returns 1."""
        if not (med_mag := self.effect.median_magnitude):
            return 1
        return self.magnitude / med_mag

    @property
    def duration_mult(self) -> float:
        """Compare the current effect potency to the median value of the effect.
        If median duration is 0 returns 1."""
        if not (med_dur := self.effect.median_duration):
            return 1
        return self.duration / med_dur

    @property
    def value(self) -> float:
        """Value to be used in computing the price and the priority of effects."""
        mag = self.magnitude if self.magnitude else 1
        dur = self.duration if self.duration else 10
        return pow(mag * dur / 10, 1.1)

    @property
    def price(self) -> float:
        """Estimated price of the effect."""
        return self.value * self.effect.base_cost


@dataclass(frozen=True)
class Ingredient:
    """Ingredient data."""

    name: str
    """Ingredient name."""
    value: int
    """Ingredient price."""
    plantable: bool
    """Wether or not the ingredient is plantable in Hearthfire."""
    rarity: Literal["common", "uncommon", "rare", "unsold"]
    """Vendor rarity. Values are `common`, `uncommon`, `rare` and `unsold`."""

    @classmethod
    def get(cls, name: str) -> Ingredient:
        """Gets `Ingredient` instance by name.

        Parameters
        ----------
        name : str
            Name of ingredient to be matched to existing list.

        Returns
        -------
        Ingredient
            `Ingredient` instance with given name.
        """
        return [row for row in Data.ingredients if row.name == name][0]

    @property
    def rows(self) -> list[Row]:
        """Get rows for this entry.

        Returns
        -------
        list[Row]
            Subset of rows applicable to the current `Ingredient` instance.
        """
        return [row for row in Data.rows if row.ingredient_name == self.name]

    @property
    def effects(self) -> set[Effect]:
        """Effects of this ingredient."""
        return {Effect.get(row.effect_name) for row in self.rows}


@dataclass(frozen=True)
class Effect:
    """Effect data."""

    name: str
    """Effect name."""
    base_cost: float
    """Effect base price."""
    type_: Literal["pos", "neg"]
    """Whether the effect is positive (`pos`) or negative (`neg`)."""

    @classmethod
    def get(cls, name: str) -> Effect:
        """Gets `Effect` instance by name.

        Parameters
        ----------
        name : str
            Name of effect to be matched to existing list.

        Returns
        -------
        Effect
            `Effect` instance with given name.
        """
        return [row for row in Data.effects if row.name == name][0]

    @property
    def rows(self) -> list[Row]:
        """Get the subset of rows applicable to the current `Effect` instance."""
        return [row for row in Data.rows if row.effect_name == self.name]

    @property
    def median_magnitude(self) -> float:
        """Median magnitude based on all entries available as rows."""
        return median(row.magnitude for row in self.rows)

    @property
    def median_duration(self) -> float:
        """Median duration based on all entries available as rows."""
        return median(row.duration for row in self.rows)

    @property
    def grouped_rows(self) -> dict[tuple, list[Row]]:
        """Similar to `rows()`, but groups rows based on equal combinations of
        magnitude and durations, and returns a `dict` where the mag/dur tuple
        is the key and a list of the `Row` instances is the value.

        The list is ordered in descending order (larger values first)."""
        dct: dict[tuple, list[Row]] = {}
        for row in self.rows:
            key = (row.magnitude_mult, row.duration_mult)
            if key not in dct:
                dct[key] = []
            dct[key].append(row.ingredient_name)
        ordered_keys = sorted(dct.keys(), key=lambda x: x[0] * x[1], reverse=True)
        return {key: dct[key] for key in ordered_keys}

    @property
    def sorted_rows(self) -> dict[tuple, list[Row]]:
        """Similar to `rows()`, but also sorts in descending order of potency
        (magnitude x duration multipliers)."""
        return sorted(self.rows, key=lambda x: x.value, reverse=True)

    @property
    def ingredients(self) -> set[Ingredient]:
        """Ingredients having this effect."""
        return {Ingredient.get(row.ingredient_name) for row in self.rows}

    @property
    def effects_lvl2(self) -> set[Effect]:
        """2nd level effects (all effects of direct ingredients also having
        the current effect)."""
        effs = set()
        for ingredient in self.ingredients:
            effs |= {eff for eff in ingredient.effects if eff.type_ == self.type_}
        return effs

    @property
    def ingredients_lvl2(self) -> set[Ingredient]:
        """2nd level ingredients (compatible with direct ingredients of
        this effect). Excludes combined potions (harmful and beneficial effects)."""
        ings = set()
        for effect in self.effects_lvl2:
            ings |= effect.ingredients
        return ings


@dataclass(frozen=True)
class Potion:
    ingredients: frozenset[Ingredient]

    @classmethod
    def mix(cls, ing1: Ingredient, ing2: Ingredient) -> Potion | None:
        key = frozenset({ing1, ing2})

        common_effects = ing1.effects & ing2.effects
        if not common_effects:
            return
        effect_types = set()
        for effect in common_effects:
            effect_types.add(effect.type_)
            if len(effect_types) > 1:  # if both types
                return
        return Potion(key)

    @classmethod
    def _get_combined_effects(cls, ingredients: set[Ingredient]) -> frozenset[Row]:
        dct = {}
        for ingredient in ingredients:
            for effect in ingredient.effects:
                if effect not in dct:
                    dct[effect] = set()
                dct[effect].add(Data.rows_dict[ingredient.name][effect.name])
        return frozenset({max(value) for value in dct.values() if len(value) > 1})

    @classmethod
    def enrich(cls, potion: Potion, ingredient: Ingredient) -> Potion | None:
        if len(potion.ingredients) > 2:
            return
        new_ingredients = set(potion.ingredients) | {ingredient}
        new_effects = cls._get_combined_effects(new_ingredients)
        if new_effects == potion.effects:
            return
        effect_types = set()
        for row in new_effects:
            effect_types.add(row.effect.type_)
            if len(effect_types) > 1:  # if both types
                return
        return Potion(frozenset(new_ingredients))

    @property
    def effects(self) -> frozenset[Row]:
        return self._get_combined_effects(self.ingredients)

    # @property
    # def rows(self) -> set[Row]:
    #     common_effects = self.ing1.effects & self.ing2.effects


if __name__ == "__main__":
    Data.populate()

    for ing1 in Data.ingredients:
        for ing2 in Data.ingredients:
            Data.potions.add(Potion.mix(ing1, ing2))
    pots_2ing = Data.potions.copy()
    print(len(pots_2ing))
    for pot in pots_2ing:
        if not pot:
            continue
        for ing3 in Data.ingredients:
            Data.potions.add(Potion.enrich(pot, ing3))

    print(len(Data.potions))

    effect_dict = {}
    for pot in Data.potions:
        if not pot:
            continue
        if pot.effects not in effect_dict:
            effect_dict[pot.effects] = {}
        effect_dict[pot.effects] = pot
    print(len(effect_dict))
