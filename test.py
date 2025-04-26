import pandas as pd
from collections import namedtuple
import csv

df = pd.read_csv("data/values.csv")

dbell = df[df["ingredient"] == "Deathbell"]

Value = namedtuple("Value", ["ingredient", "effect", "magnitude", "duration"])

# with open('data/values.csv', encoding='utf-8') as file_in:
#     csv.reader

v1 = Value(1, 2, 3, 4)

print(v1)

v2 = Value(1, 2, 3, 4)

print(v1 == v2)

tst = set()
tst.add(v1)
tst.add(v2)

print(tst)

testdict = {v1: "test", v2: "test3"}

print(testdict)

from dataclasses import dataclass


@dataclass
class Row:
    ingredient_name: str
    effect_name: str
    magnitude: float
    duration: float


r1 = Row("test", "test2", 2.5, 5.2)
r2 = Row("test", "test2", 2.5, 5.2)

print(r1 == r2)
