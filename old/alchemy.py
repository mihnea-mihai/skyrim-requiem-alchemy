from __future__ import annotations
import json
import csv
import pandas as pd

# with open("data/values.csv", encoding="utf-8") as file_in:
#     data = list(csv.DictReader(file_in))

df = pd.read_csv("data/values.csv")


class Ingredient:
    # _dict: dict[str, Ingredient] = {}

    # def __init__(self, ingredient_name: str):
    #     self.name: str = ingredient_name
    #     """Name of the ingredient."""
    #     self.effects: list[Effect] = []
    #     """All effects of the ingredient."""
    #     self.immediate_candidates: set = set()
    #     """Set of ingredients that will successfully
    #     combine with the current one."""

    #     for name in df[df["ingredient"] == self.name]["effect"]:
    #         self.effects.append(Effect.get(name))

    #     for effect in self.effects:
    #         for ingredient in effect.ingredients:
    #             self.immediate_candidates.add(ingredient)

    # @classmethod
    # def get(cls, name: str) -> Ingredient:
    #     if name not in cls._dict:
    #         cls._dict[name] = Ingredient(name)
    #     return cls._dict[name]

    def __init__(self, name):
        self.name = name
        


class Effect:
    _dict: dict[str, Effect] = {}

    @classmethod
    def get(cls, name: str) -> Effect:
        if name not in cls._dict:
            cls._dict[name] = Effect(name)
        return cls._dict[name]

    def __init__(self, effect_name: str):
        self.name: str = effect_name
        """Name of the effect."""
        self.ingredients = []
        """All ingredients of the effect."""
        for name in df[df["effect"] == self.name]["ingredient"]:
            self.ingredients.append(Ingredient.get(name))

    def __repr__(self):
        return f"Effect({self.name})"


def read(path: str) -> dict:
    ingredients = {}
    effects = {}
    with open(path, encoding="utf-8") as file_in:
        for line in csv.DictReader(file_in):
            ingredient = line["ingredient"]
            effect = line["effect"]
            if ingredient not in ingredients:
                ingredients[ingredient] = {"effects": {}}
            ingredients[ingredient]["effects"][effect] = {
                "magnitude": float(line["magnitude"]),
                "duration": float(line["duration"]),
            }
            if effect not in effects:
                effects[effect] = {"variants": {}}
            key = str(tuple([line["magnitude"], line["duration"]]))
            if key not in effects[effect]["variants"]:
                effects[effect]["variants"][key] = []
            effects[effect]["variants"][key].append(ingredient)

            # effects[effect]["ingredients"].append(line["ingredient"])
    return {"ingredients": ingredients, "effects": effects}


# data = read("data/values.csv")
# with open("data/values.json", "w", encoding="utf-8") as file_out:
#     json.dump(data, file_out, indent=4)

ing = Ingredient.get("Salt")

print(ing.name)

print(ing.effects)

ing2 = Ingredient.get("Deathbell")

ing3 = Ingredient.get("Salt")


print(len(Ingredient._dict))
print(len(Effect._dict))
