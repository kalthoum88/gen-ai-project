from src.ticket import (
    Ticket,
    load_restaurants,
    validate_ticket_against_menu
)

restaurants = load_restaurants()

ticket = Ticket(
    restaurant="pizza_house",
    items=[
        {
            "name": "Margherita",
            "size": "Large",
            "quantity": 2,
            "remove_ingredients": ["basil"]
        }
    ],
    delivery_zone="Batna Center",
    address="Batna Center, Street 1",
    phone="0550000001"
)

result = validate_ticket_against_menu(ticket, restaurants)

print("Ticket validation:", result)