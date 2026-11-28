from src.assistant import PizzaAssistant
import json

assistant = PizzaAssistant("pizza_house")

# 1. Place an order
print("\n1. CUSTOMER PLACES ORDER")
result = assistant.process_order_message(
    "I want two large Margherita pizzas."
)
print(result)

# 2. Provide delivery zone
print("\n2. CUSTOMER PROVIDES DELIVERY ZONE")
result = assistant.process_order_message("Batna Center")
print(result)

# 3. Provide address
print("\n3. CUSTOMER PROVIDES ADDRESS")
result = assistant.process_order_message(
    "12 Rue de la Liberté, Batna"
)
print(result)

# 4. Provide phone
print("\n4. CUSTOMER PROVIDES PHONE")
result = assistant.process_order_message("0551234567")
print(result)

# 5. Display recap
print("\n5. ORDER RECAP")
recap = assistant.show_recap()
print(json.dumps(recap, indent=4, ensure_ascii=False))

# 6. Confirm order
print("\n6. CUSTOMER CONFIRMS")
result = assistant.confirm(True)
print(result)

# 7. Generate final ticket
print("\n7. FINAL JSON TICKET")
ticket = assistant.get_ticket()
print(json.dumps(ticket, indent=4, ensure_ascii=False))

# 8. Modify after confirmation
print("\n8. CUSTOMER MODIFIES CONFIRMED ORDER")
result = assistant.process_order_message(
    "Make my Margherita quantity three."
)
print(result)

print("\n9. CHECK CONFIRMATION RESET")
try:
    assistant.get_ticket()
except ValueError as error:
    print("Correctly rejected:", error)