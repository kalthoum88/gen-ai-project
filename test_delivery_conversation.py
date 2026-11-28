
from src.assistant import PizzaAssistant


assistant = PizzaAssistant("pizza_house")

messages = [
    "I want one large Margherita.",
    "Batna Center",
    "12 Rue de la Liberté, Batna",
    "0551234567"
]

for message in messages:
    print("\nCustomer:", message)

    result = assistant.process_order_message(message)

    print("Assistant:", result)

print("\nFinal recap:")

try:
    print(assistant.show_recap())
except Exception as error:
    print("Recap not ready:", error)
