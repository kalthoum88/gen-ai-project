
from src.assistant import PizzaAssistant


assistant = PizzaAssistant("pizza_house")

test_messages = [
    "I want one large Margherita.",
    "Give me two medium BBQ Chicken pizzas without onions.",
    "I'd like a small Pepperoni and a large Tuna, please."
]

for message in test_messages:
    print("\nCustomer:", message)

    result = assistant.extract_order_message(message)

    print("Extracted information:")
    print(result)
    print("-" * 60)
