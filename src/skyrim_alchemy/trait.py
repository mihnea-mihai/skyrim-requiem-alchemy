from __future__ import annotations

from typing import TYPE_CHECKING

from skyrim_alchemy.data import Data
from skyrim_alchemy.potency import Potency
from skyrim_alchemy.effect import Effect
from skyrim_alchemy.ingredient import Ingredient
from skyrim_alchemy.logger import logger
from skyrim_alchemy.utils import read_csv

if TYPE_CHECKING:
    from skyrim_alchemy import Potion


class Trait:
    @staticmethod
    def read_all():
        for row in read_csv("data/traits.csv"):
            Trait.from_row(row)
        Data.effects = sorted(Data.effects)

    @staticmethod
    def from_row(row: dict) -> None:
        trait = Trait(row)
        Data.traits.append(trait)
        logger.debug("Trait list += %s", trait)

    def __init__(self, row: dict):
        self.ingredient: Ingredient = Ingredient.get(row["ingredient_name"])
        self.potency: Potency = Potency.from_data(
            Effect.get(row["effect_name"]),
            float(row["magnitude"]),
            int(row["duration"]),
        )
        self.order: int = int(row["order"])

    def __repr__(self):
        return f"Trait({self.ingredient.name}, {self.potency})"

    def __lt__(self, other: Trait) -> bool:
        return (self.potency, self.ingredient) < (other.potency, other.ingredient)
