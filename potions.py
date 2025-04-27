from data import Data, Ingredient, Row, Effect
from dataclasses import dataclass
from pprint import pprint

Data.populate()


@dataclass(frozen=True)
class Potion:
    ing1: Ingredient
    ing2: Ingredient
    ing3: Ingredient | None = None

    @classmethod
    def ensure_purity(cls, effects: set[Effect]) -> bool:
        types = set()
        for effect in effects:
            types.add(effect.type_)
            if len(types) > 1:  # if both are found
                return False
        return True

    @classmethod
    def attempt(cls, ingr1: Ingredient, ingr2: Ingredient) -> bool:
        intersection = ingr1.effects & ingr2.effects
        if not intersection:
            return False
        if not cls.ensure_purity(intersection):
            return False
        return True

    @property
    def effects(self) -> frozenset[Row]:
        st = set()
        for effect in self.ing1.effects & self.ing2.effects:
            row1 = Data.rows_dict[ing1.name][effect.name]
            row2 = Data.rows_dict[ing2.name][effect.name]
            st.add(max([row1, row2]))
        return frozenset(st)


all_set = set()
compatible_set = set()
potion_types = set()
for ing1 in Data.ingredients:
    for ing2 in Data.ingredients:
        all_set.add(frozenset({ing1, ing2}))
        if Potion.attempt(ing1, ing2):
            compatible_set.add(frozenset({ing1, ing2}))
            potion_types.add(Potion(ing1, ing2).effects)

print(len(all_set))
print(len(compatible_set))
print(len(potion_types))

# pprint(potion_types)

for st in potion_types:
    if len(st) > 3:
        print(len(st))
        print(st)
