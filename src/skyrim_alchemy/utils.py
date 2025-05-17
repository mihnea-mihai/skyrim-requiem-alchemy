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


def coerce(value, type_):
    match type_:
        case "float":
            return float(value)
        case "int":
            return int(value)
        case "bool":
            return value == "True"
    return value


def coerce_fields(obj: Any):
    for fld in fields(obj):
        val = getattr(obj, fld.name, None)
        if val and fld.type in ["float", "bool", "int"]:
            setattr(obj, fld.name, coerce(val, fld.type))
