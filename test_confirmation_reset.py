from src.engine import OrderEngine

engine = OrderEngine("pizza_house")

engine.add_item("Margherita", "Large", 2)
engine.set_delivery_details(
    "Batna Center",
    "Batna Center, Street 1",
    "0550000001"
)

engine.confirm_order(True)
print("Initially confirmed:", engine.confirmed)

# Change the order
engine.update_quantity("Margherita", "Large", 3)

print("After changing quantity:", engine.confirmed)

try:
    engine.get_final_ticket()
except ValueError as error:
    print("Correctly rejected:", error)