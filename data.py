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


@dataclass
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


@dataclass
class Ingredient:
    """Ingredient data."""

    name: str
    """Ingredient name."""
    value: int
    """Ingredient price."""
    plantable: bool
    """Wether or not the ingredient is plantable in Hearthfire."""
    rarity: Literal["common", "uncommon", "rare"]
    """Vendor rarity. Values are `common`, `uncommon`, `rare`."""

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


@dataclass
class Effect:
    """Effect data."""

    name: str
    """Effect name."""
    value: int
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
        return sorted(
            self.rows, key=lambda x: x.magnitude_mult * x.duration_mult, reverse=True
        )


if __name__ == "__main__":
    Data.populate()

    # ing = Ingredient.get("Canis Root")

    # print(ing.rows[0].effect.median_magnitude)

    eff = Effect.get("Restore Health").sorted_rows

    pprint(eff)
