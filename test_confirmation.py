
from src.engine import OrderEngine
import json

engine = OrderEngine("pizza_house")

engine.add_item("Margherita", "Large", 2)

engine.set_delivery_details(
    "Batna Center",
    "Batna Center, Street 1",
    "0550000001"
)

# Show recap
print("ORDER RECAP")
print(json.dumps(engine.build_recap(), indent=4))

# Try to obtain ticket before confirmation
print("\nTEST 1: Before confirmation")

try:
    engine.get_final_ticket()
except ValueError as error:
    print("Correctly rejected:", error)

# Customer confirms
print("\nTEST 2: Customer confirms")

print(engine.confirm_order(True))

# Generate final ticket
print("\nFINAL JSON TICKET")

final_ticket = engine.get_final_ticket()

print(json.dumps(final_ticket, indent=4))
