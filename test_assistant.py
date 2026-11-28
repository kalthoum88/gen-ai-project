
from src.assistant import PizzaAssistant

assistant = PizzaAssistant("pizza_house")

# 1. Ask a restaurant question
answer = assistant.ask(
    "How much is a Large Margherita?"
)

print("\nRAG ANSWER")
print(answer)

# 2. Add an item
assistant.add_item("Margherita", "Large", 2)

# 3. Set delivery details
assistant.set_delivery_details(
    "Batna Center",
    "Batna Center, Street 1",
    "0550000001"
)

# 4. Display the recap
print("\nORDER RECAP")
print(assistant.show_recap())

# 5. Confirm and generate the ticket
assistant.confirm(True)

print("\nFINAL TICKET")
print(assistant.get_ticket())
