import jinja2
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

with open("data/alchemy.json", "r", encoding="utf-8") as file_in:
    data = json.load(file_in)

eff1 = ["Fortify Lockpicking"]


def get_effects(ingredients: list[str]) -> list[str]:
    effects = set()
    for ingredient in ingredients:
        for effect in data[ingredient]:
            effects.add(effect)
    return sorted(effects)


def get_ingredients(effects: list[str]) -> list[str]:
    ingredients = set()
    for ingredient in data:
        for effect in effects:
            if effect in data[ingredient]:
                ingredients.add(ingredient)
    return sorted(ingredients)


# eff2 = get_effects(ing1)
ing2 = get_ingredients(eff1)
eff2 = get_effects(ing2)
ing3 = get_ingredients(eff2)

env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

tpl = env.get_template("table.html")

with open("table.html", "w", encoding="utf-8") as file_out:
    file_out.write(
        tpl.render(
            ingredients=ing3,
            effects=eff2,
            data=data,
        )
    )
