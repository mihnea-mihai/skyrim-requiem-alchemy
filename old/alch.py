"""Build a JSON file with detailed information derived from the inputs."""

from __future__ import annotations

import csv

import json
import statistics
import logging


logging.basicConfig(filename="alchemy.log", level=logging.DEBUG)


class Alchemy:
    """Global data."""

    def __init__(self):
        pass

    with open("data/values.csv", "r", encoding="utf-8") as file:
        VALUES: list = list(csv.DictReader(file))

    @classmethod
    def to_json(self) -> dict:
        jdoc = {"ingredients": {}, "effects": {}}
        for ingredient in Ingredient.get_all():
            jdoc["ingredients"][ingredient.name] = ingredient.to_json()
        return jdoc


class Ingredient:
    def __init__(self, name: str):
        self.name: str = name

    def __repr__(self):
        return f"Ingredient({self.name})"

    @classmethod
    def get_all(cls):
        for name in sorted(set(row["ingredient"] for row in Alchemy.VALUES)):
            yield Ingredient(name)

    @property
    def effects(self):
        for row in Alchemy.VALUES:
            if row["ingredient"] == self.name:
                yield Effect(row["effect"])

    def magnitude(self, effect: Effect) -> Magnitude:
        return Magnitude(self, effect)

    def duration(self, effect: Effect) -> Duration:
        return Duration(self, effect)

    def to_json(self):
        jdoc = {"effects": {}}
        for effect in self.effects:
            jdoc["effects"][effect.name] = {
                "magnitude": {
                    "value": effect.magnitude(self).value,
                    "mult": effect.magnitude(self).mult,
                },
                "duration": {
                    "value": effect.duration(self).value,
                    "mult": effect.duration(self).mult,
                },
            }
        return jdoc


class Effect:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"Effect({self.name})"

    @classmethod
    def get_all(cls):
        for name in sorted(set(row["effect"] for row in Alchemy.VALUES)):
            yield Effect(name)

    @property
    def ingredients(self):
        for row in Alchemy.VALUES:
            if row["effect"] == self.name:
                yield Ingredient(row["ingredient"])

    @property
    def magnitudes(self):
        for ingredient in self.ingredients:
            yield Magnitude(ingredient, self)

    @property
    def median_magnitude(self):
        return statistics.median(mag.value for mag in self.magnitudes)

    def magnitude(self, ingredient: Ingredient) -> Magnitude:
        return Magnitude(ingredient, self)

    @property
    def durations(self):
        for ingredient in self.ingredients:
            yield Duration(ingredient, self)

    @property
    def median_duration(self):
        return statistics.median(dur.value for dur in self.durations)

    def duration(self, ingredient: Ingredient) -> Duration:
        return Duration(ingredient, self)
    
    def to_json(self):
        jdoc = {"ingredients": {}}
        for effect in self.get:
            jdoc["effects"][effect.name] = {
                "magnitude": {
                    "value": effect.magnitude(self).value,
                    "mult": effect.magnitude(self).mult,
                },
                "duration": {
                    "value": effect.duration(self).value,
                    "mult": effect.duration(self).mult,
                },
            }
        return jdoc


class Magnitude:
    def __init__(self, ingredient: Ingredient, effect: Effect):
        self.ingredient = ingredient
        self.effect = effect

    @property
    def value(self):
        """Magnitude value."""
        for row in Alchemy.VALUES:
            if (
                row["ingredient"] == self.ingredient.name
                and row["effect"] == self.effect.name
            ):
                return float(row["magnitude"])

    @property
    def mult(self):
        if median := self.effect.median_magnitude:
            return self.value / median


class Duration:
    def __init__(self, ingredient: Ingredient, effect: Effect):
        self.ingredient = ingredient
        self.effect = effect

    @property
    def value(self):
        for row in Alchemy.VALUES:
            if (
                row["ingredient"] == self.ingredient.name
                and row["effect"] == self.effect.name
            ):
                return float(row["duration"])

    @property
    def mult(self):
        if median := self.effect.median_duration:
            return self.value / median


# Save to file
with open("alchemy.json", "w", encoding="utf-8") as file:
    json.dump(Alchemy.to_json(), file, indent=4)
