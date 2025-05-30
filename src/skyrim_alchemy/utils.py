from __future__ import annotations

from dataclasses import fields
from typing import Any


def value_formula(magnitude: float, duration: int) -> float:
    magnitude_factor = 1
    duration_factor = 1
    if magnitude:
        magnitude_factor = magnitude
    if duration:
        duration_factor = duration / 10
    return pow(magnitude_factor * duration_factor, 1.1)
