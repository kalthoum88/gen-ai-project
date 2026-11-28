
from src.engine import OrderEngine


engine = OrderEngine("pizza_house")

# Add two pizzas.
print(engine.add_item("Margherita", "Large", 1))
print(engine.add_item("BBQ Chicken", "Medium", 2))

print("\nINITIAL BASKET")
print(engine.get_basket())

# Change Margherita from Large to Medium.
print("\nTEST 1: Change pizza size")
print(engine.update_size("Margherita", "Large", "Medium"))

# Change BBQ Chicken ingredient removals.
print("\nTEST 2: Remove onions")
print(
    engine.update_ingredients(
        "BBQ Chicken",
        "Medium",
        ["onions"]
    )
)

print("\nUPDATED BASKET")
print(engine.get_basket())

# Try an invalid ingredient.
print("\nTEST 3: Invalid ingredient")
try:
    engine.update_ingredients(
        "Margherita",
        "Medium",
        ["chicken"]
    )
except ValueError as error:
    print("Correctly rejected:", error)

# Try an invalid size.
print("\nTEST 4: Invalid size")
try:
    engine.update_size(
        "Margherita",
        "Medium",
        "Extra Large"
    )
except ValueError as error:
    print("Correctly rejected:", error)
