# skyrim-requiem-alchemy

## Ingredients

### Fields

Name | Type | Description
---|---|---
name | str
value | int
plantable | bool
vendor_rarity | str
unique_to | str
average_price | float | average of all potency values

### Links

Name | Type | Description
---|---|---
traits | set[Traits]
compatible_ingredients | set[Ingredient] | ingredients with at least one common effect

### Methods

Name | Type | Description
---|---|---
compatible_with(Ingredient) | bool






### Computed fields

- average_price: float
- traits: set[Traits]


plantable




hardest




## Effects

Table:

- name
- effect type
- base cost
- median magnitude
- median duration
- median price
- ingredients
