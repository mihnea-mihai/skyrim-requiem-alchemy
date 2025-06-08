from __future__ import annotations

import csv
import inspect
from dataclasses import fields
import itertools
from functools import cached_property
from inspect import isfunction, signature
from typing import Any


def groupby(in_list: list, key) -> list:
    return [(k, list(v)) for k, v in itertools.groupby(sorted(in_list, key=key))]


def cache_self_methods(cls: object):
    for method_name, method in cls.__dict__.items():
        if isfunction(method) and "__" not in method_name:
            params = list(signature(method).parameters.values())
            if len(params) == 1 and params[0].name == "self":
                setattr(cls, method_name, cached_property(method))
    return cls


def value_formula(magnitude: float, duration: int) -> float:
    magnitude_factor = 1
    duration_factor = 1
    if magnitude:
        magnitude_factor = magnitude
    if duration:
        duration_factor = duration / 10
    return pow(magnitude_factor * duration_factor, 1.1)


def read_csv(path: str):
    with open(path, encoding="utf-8") as file:
        yield from csv.DictReader(file)
