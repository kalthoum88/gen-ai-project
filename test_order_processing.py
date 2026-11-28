
from src.assistant import PizzaAssistant

assistant = PizzaAssistant("pizza_house")

messages = [
    "I want one large Margherita.",
    "Give me two medium BBQ Chicken pizzas without onions.",
    "I'd like a small Pepperoni and a large Tuna, please."
]

for message in messages:
    print("\nCustomer:", message)

    result = assistant.process_order_message(message)

    print("Result:", result["status"])
    print("Basket:", result.get("basket", result.get("message")))
    print("-" * 60)
