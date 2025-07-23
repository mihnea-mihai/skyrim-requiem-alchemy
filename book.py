from itertools import combinations, groupby

from jinja2 import Environment, FileSystemLoader, select_autoescape

from skyrim_alchemy.data import Data
from skyrim_alchemy.effect import Effect
from skyrim_alchemy.ingredient import Ingredient
from skyrim_alchemy.logger import logger
from skyrim_alchemy.potion import Potion
from skyrim_alchemy.trait import Trait

Ingredient.read_all()
Effect.read_all()
Trait.read_all()
Data.ingredients.sort()
Data.effects.sort()
Data.traits.sort()
Data.potencies.sort()

for ing1, ing2 in combinations(Data.ingredients, 2):
    Potion.from_ingredients(tuple(sorted((ing1, ing2))))

print(len(Data.potions))

for ing1, ing2, ing3 in combinations(Data.ingredients, 3):
    Potion.from_ingredients(tuple(sorted((ing1, ing2, ing3))))


print(len(Data.potions))

for potencies, potions in groupby(
    sorted(Data.potions, key=lambda p: p.potencies, reverse=True),
    key=lambda p: p.potencies,
):
    potion_list = list(potions)
    min(potion_list).best_in_slot = True
    Data.potency_combinations.append(potencies)

Data.effect_combinations = sorted(
    effects
    for effects, _ in groupby(
        sorted(Data.potency_combinations), key=lambda ps: sorted(p.effect for p in ps)
    )
)

for potion in Data.potions:
    if (
        potion.best_in_slot
        and potion.pure
        and potion.compatible_duration
        and not potion.overpriced
        and potion.potencies_accessibility_sum > potion.accessibility / 10
    ):
        Data.useful_potions.append(potion)

print(len(Data.useful_potions))


# Data.valuable_potions = sor

logger.info("Started generating")

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.debug"],
)


def crop_number(val):
    if int(val) == val:
        return int(val)
    return round(val, 1)


env.filters["crop_number"] = crop_number
env.tests["is_recommended_potion"] = lambda p: p.best_in_slot


def template_to_file(template: str, filename: str, **kwargs):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(env.get_template(template).render(data=Data, **kwargs))


template_to_file("index.html.jinja", "docs/index.html")

for page in [
    "ingredients",
    "effects",
    "potencies",
    "traits",
    "potions",
]:
    template_to_file(f"{page}.html.jinja", f"docs/{page}.html")

for ingredient in Data.ingredients:
    template_to_file(
        "ingredient.html.jinja",
        f"docs/ingredients/{ingredient.name}.html",
        ingredient=ingredient,
    )

for effect in Data.effects:
    template_to_file(
        "effect.html.jinja",
        f"docs/effects/{effect.name}.html",
        effect=effect,
    )

for potency in Data.potencies:
    template_to_file(
        "potency.html.jinja",
        f"docs/potencies/{potency.effect.name}+{potency.magnitude}+{potency.duration}.html",
        potency=potency,
    )
