from jinja2 import Environment, FileSystemLoader, select_autoescape

from data import Data

Data.populate()

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


with open("docs/index.html", "w", encoding="utf-8") as file_out:
    file_out.write(env.get_template("default.html.jinja").render(title=""))

for page in ["effects", "ingredients", "potencies", "traits"]:
    with open(f"docs/{page}.html", "w", encoding="utf-8") as file_out:
        file_out.write(
            env.get_template(f"{page}.html.jinja").render(
                title=page.capitalize(), data=Data
            )
        )

for ingredient in Data.ingredients:
    with open(
        f"docs/ingredients/{ingredient.name}.html", "w", encoding="utf-8"
    ) as file_out:
        file_out.write(
            env.get_template("ingredient.html.jinja").render(
                title=ingredient.name, data=Data, ingredient=ingredient
            )
        )

for effect in Data.effects:
    with open(f"docs/effects/{effect.name}.html", "w", encoding="utf-8") as file_out:
        file_out.write(
            env.get_template("effect.html.jinja").render(
                title=effect.name, data=Data, effect=effect
            )
        )
