from src.ticket import (
    Ticket,
    load_restaurants,
    calculate_order
)

restaurants = load_restaurants()

ticket = Ticket(
    restaurant="pizza_house",
    items=[
        {
            "name": "Margherita",
            "size": "Large",
            "quantity": 2,
            "remove_ingredients": []
        }
    ],
    delivery_zone="Batna Center",
    address="Batna Center, Street 1",
    phone="0550000001"
)

result = calculate_order(ticket, restaurants)

print("\nORDER CALCULATION")
print("----------------------")
print("Subtotal:", result.subtotal, "DA")
print("Discount:", result.discount, "DA")
print("Delivery:", result.delivery_fee, "DA")
print("Total:", result.total, "DA")
print("Promotion:", result.promotion_reward)