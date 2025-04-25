from jinja2 import Environment, FileSystemLoader, select_autoescape
import pandas as pd

df = pd.read_csv("data/values.csv")


class Ingredient:
    def __init__(self, name: str):
        self.name: str = name
        self.slug = "ingredients/" + self.name.lower().replace(" ", "_").replace(
            "'", "_"
        )
        self.effects = df[df["ingredient"] == self.name][
            ["effect", "magnitude", "duration"]
        ]


ingredients_list = df["ingredient"].sort_values().unique()

ingredients = [Ingredient(ing) for ing in ingredients_list]

env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

tpl = env.get_template("default.html.jinja")

with open("index.html", "w", encoding="utf-8") as file_out:
    file_out.write(tpl.render(ingredients=ingredients))

tpl = env.get_template("ingredient.html.jinja")
for ingredient in ingredients:
    with open(f"{ingredient.slug}.html", "w", encoding="utf-8") as file_out:
        file_out.write(
            tpl.render(
                ingredient=ingredient, ingredients=ingredients, title=ingredient.name
            )
        )

print(Ingredient("Deathbell").effects)


for eff in Ingredient("Deathbell").effects['effect']:
    print(eff)
