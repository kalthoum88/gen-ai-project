
from src.engine import OrderEngine

engine = OrderEngine("pizza_house")

# Test 1: Valid pizza
print("\nTEST 1: Valid pizza")

print(
    engine.add_item(
        "Margherita",
        "Large",
        2,
        ["basil"]
    )
)

# Test 2: Nonexistent pizza
print("\nTEST 2: Invalid pizza")

try:
    engine.add_item("Sushi", "Large")
except ValueError as error:
    print("Rejected:", error)

# Test 3: Invalid size
print("\nTEST 3: Invalid size")

try:
    engine.add_item("Margherita", "Extra Large")
except ValueError as error:
    print("Rejected:", error)

# Test 4: Invalid ingredient removal
print("\nTEST 4: Invalid ingredient")

try:
    engine.add_item("Margherita", "Large", 1, ["chicken"])
except ValueError as error:
    print("Rejected:", error)

# Display basket
print("\nFINAL BASKET")

for item in engine.items:
    print(item.name, item.size, item.quantity, item.remove_ingredients)
