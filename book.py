from jinja2 import Environment, FileSystemLoader, select_autoescape

from skyrim_alchemy.data import Data
from skyrim_alchemy.logger import logger
from skyrim_alchemy.effect import Effect
from skyrim_alchemy.ingredient import Ingredient
from skyrim_alchemy.potency import Potency
from skyrim_alchemy.potion import Potion
from skyrim_alchemy.trait import Trait


Ingredient.read_all()
Effect.read_all()
Trait.read_all()


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
        # "potions",
    ]:
        with open(f"docs/{page}.html", "w", encoding="utf-8") as file_out:
            file_out.write(
                env.get_template(f"{page}.html.jinja").render(
                    title=page.capitalize(), data=Data
                )
            )

    # for ingredient in Data.ingredients:
    #     with open(
    #         f"docs/ingredients/{ingredient.name}.html", "w", encoding="utf-8"
    #     ) as file_out:
    #         file_out.write(
    #             env.get_template("ingredient.html.jinja").render(
    #                 ingredient=ingredient, data=Data
    #             )
    #         )
    # for effect in Data.effects:
    #     with open(
    #         f"docs/effects/{effect.name}.html", "w", encoding="utf-8"
    #     ) as file_out:
    #         file_out.write(
    #             env.get_template("effect.html.jinja").render(effect=effect, data=Data)
    #         )

    logger.info("ended Generation")
