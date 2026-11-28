
from src.engine import OrderEngine

engine = OrderEngine("pizza_house")

# Add two pizzas
print(engine.add_item("Margherita", "Large", 2))

# Add another pizza
print(engine.add_item("BBQ Chicken", "Medium", 1))

# Change Margherita quantity
print(engine.update_quantity("Margherita", "Large", 3))

# Remove BBQ Chicken
print(engine.remove_item("BBQ Chicken", "Medium"))

# Display current basket
print("\nCURRENT BASKET")

for item in engine.items:
    print(
        item.name,
        "| Size:", item.size,
        "| Quantity:", item.quantity
    )
