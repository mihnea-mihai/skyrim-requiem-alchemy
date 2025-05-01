from jinja2 import Environment, FileSystemLoader, select_autoescape

from data import Data

Data.populate()


# def format_mult(mult: float) -> int | float:
#     int_num = round(mult)
#     if int_num == mult:
#         return int_num
#     return round(mult, 1)


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


tpl = env.get_template("default.html.jinja")

with open("docs/index.html", "w", encoding="utf-8") as file_out:
    file_out.write(tpl.render(title=""))

tpl = env.get_template("effects.html.jinja")

with open("docs/effects.html", "w", encoding="utf-8") as file_out:
    file_out.write(tpl.render(title="Effects", effects=Data.effects.values()))

tpl = env.get_template("ingredients.html.jinja")

with open("docs/ingredients.html", "w", encoding="utf-8") as file_out:
    file_out.write(
        tpl.render(title="Ingredients", ingredients=Data.ingredients.values())
    )

# tpl = env.get_template("effect.html.jinja")

# with open("paralysis.html", "w", encoding="utf-8") as file_out:
#     file_out.write(
#         tpl.render(title="Paralysis", effect=Effect.get("Waterbreathing"), data=Data())
#     )
