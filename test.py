from skyrim_alchemy.effect import Effect

Effect.read_all()

e1 = Effect.get("Paralysis")
e2 = Effect.get("Paralysis")

print(e1)

print(e2)

print(e1 == e2)
