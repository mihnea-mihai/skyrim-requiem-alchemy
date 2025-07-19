from __future__ import annotations

from skyrim_alchemy.data import Data
from skyrim_alchemy.effect import Effect
from skyrim_alchemy.logger import logger
from skyrim_alchemy.utils import value_formula
from functools import cached_property

# from skyrim_alchemy.potion import Potion
from typing import TYPE_CHECKING

from statistics import mean

if TYPE_CHECKING:
    from skyrim_alchemy import Potion


class Potency:

    def __init__(self, effect: Effect, magnitude: float, duration: int):
        self.effect: Effect = effect
        self.magnitude: float = magnitude
        self.duration: int = duration
        self.price: float = (
            value_formula(self.magnitude, self.duration) * self.effect.base_cost
        )

    @staticmethod
    def from_data(effect: Effect, magnitude: float, duration: int) -> Potency:
        for pot in Data.potencies:
            if (
                pot.effect.name == effect.name
                and pot.magnitude == magnitude
                and pot.duration == duration
            ):
                return pot
        pot = Potency(effect, magnitude, duration)
        Data.potencies.append(pot)
        logger.debug("Potency list += %s", pot)
        return pot

    def __lt__(self, other: Potency):
        return (self.price, self.effect, id(self)) < (
            other.price,
            other.effect,
            id(other),
        )

    @cached_property
    def potions(self) -> list[Potion]:
        lst = []
        for potion in Data.potions:
            if self in potion.potencies:
                lst.append(potion)
        return lst

    @cached_property
    def min_potion_accessibility(self) -> float:
        if self.potions:
            return min(potion.accessibility for potion in self.potions)
        return -1

    @cached_property
    def average_potion_accessibility(self) -> float:
        if self.potions:
            return mean(potion.accessibility for potion in self.potions)
        return -1

    @cached_property
    def overpriced(self) -> bool:
        for potency in self.effect.potencies:
            if potency.price > self.price:
                if (
                    potency.min_potion_accessibility < self.min_potion_accessibility
                    and potency.magnitude >= self.magnitude
                    and potency.duration >= self.duration
                ):
                    return True
        return False

    @cached_property
    def useful_potions(self) -> list[Potion]:
        return [potion for potion in Data.useful_potions if self in potion.potencies]

    def __repr__(self):
        return f"Potency({self.effect.name}, {self.magnitude}, {self.duration})"
