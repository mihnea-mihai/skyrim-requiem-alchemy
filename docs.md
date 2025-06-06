```mermaid
flowchart
data
effect
ingredient
potency
potion
trait

data --> effect
data --> ingredient
data & effect --> potency
data & potency & ingredient & effect --> trait
```