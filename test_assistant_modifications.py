from src.assistant import PizzaAssistant

assistant = PizzaAssistant("pizza_house")

# Start with two pizzas
print("\nCUSTOMER: I want one large Margherita and one medium BBQ Chicken.")
result = assistant.process_order_message(
    "I want one large Margherita and one medium BBQ Chicken."
)
print("ASSISTANT:", result)
print("BASKET:", assistant.show_basket())

# Test 1: Change quantity
print("\nTEST 1: Change Margherita quantity")
result = assistant.process_order_message(
    "Actually, make my Margherita quantity two."
)
print("ASSISTANT:", result)
print("BASKET:", assistant.show_basket())

# Test 2: Change size
print("\nTEST 2: Change Margherita size")
result = assistant.process_order_message(
    "Change my Margherita to Medium."
)
print("ASSISTANT:", result)
print("BASKET:", assistant.show_basket())

# Test 3: Remove an ingredient
print("\nTEST 3: Remove onions")
result = assistant.process_order_message(
    "No onions on my BBQ Chicken."
)
print("ASSISTANT:", result)
print("BASKET:", assistant.show_basket())

# Test 4: Remove a pizza
print("\nTEST 4: Remove BBQ Chicken")
result = assistant.process_order_message(
    "Remove the BBQ Chicken."
)
print("ASSISTANT:", result)
print("FINAL BASKET:", assistant.show_basket())