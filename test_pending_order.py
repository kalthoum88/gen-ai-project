
from src.assistant import PizzaAssistant

assistant = PizzaAssistant("pizza_house")

# First message: size is missing.
result = assistant.process_order_message(
    "I want a Margherita."
)

print("First response:")
print(result)

# Second message: customer supplies the missing size.
result = assistant.process_order_message("Large")

print("\nSecond response:")
print(result)

print("\nFinal basket:")
print(assistant.show_basket())
