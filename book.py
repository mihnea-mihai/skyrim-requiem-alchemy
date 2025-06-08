from jinja2 import Environment, FileSystemLoader, select_autoescape

from skyrim_alchemy.data import Data
from skyrim_alchemy.logger import logger
from skyrim_alchemy.effect import Effect
from skyrim_alchemy.ingredient import Ingredient
from skyrim_alchemy.potion import Potion

from itertools import combinations, groupby

# from skyrim_alchemy.potency import Potency
# from skyrim_alchemy.potion import Potion
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
    min(potion_list).recommended = True


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
env.tests["is_recommended_potion"] = lambda p: p.recommended
# ing = Ingredient.get("Canis Root")
with open("docs/index.html", "w", encoding="utf-8") as file_out:
    file_out.write(env.get_template("default.html.jinja").render(title=""))

# tpl = env.get_template("formatting/ingredient/plantable.html.jinja")

# print(tpl.render(ingredient=ing))

if __name__ == "__main__":

    for page in [
        "ingredients",
        "effects",
        "potencies",
        "traits",
        "potions",
    ]:
        with open(f"docs/{page}.html", "w", encoding="utf-8") as file_out:
            html = env.get_template(f"{page}.html.jinja").render(
                title=page.capitalize(), data=Data
            )
            file_out.write(html)

    for ingredient in Data.ingredients:
        with open(
            f"docs/ingredients/{ingredient.name}.html", "w", encoding="utf-8"
        ) as file_out:
            file_out.write(
                env.get_template("ingredient.html.jinja").render(
                    ingredient=ingredient, data=Data
                )
            )
    for effect in Data.effects:
        with open(
            f"docs/effects/{effect.name}.html", "w", encoding="utf-8"
        ) as file_out:
            file_out.write(
                env.get_template("effect.html.jinja").render(effect=effect, data=Data)
            )

    logger.info("ended Generation")
