
from src.ticket import Ticket

order = {
    "restaurant": "pizza_house",
    "items": [
        {
            "name": "Margherita",
           "size": "Large",
           "quantity": 2,
            "remove_ingredients": ["basil"]
        }
    ],
    "delivery_zone": "Batna Center",
    "address": "Batna Center, Street 1",
    "phone": "0550000001"
}

ticket = Ticket.model_validate(order)

print("Order validated successfully!")
print(ticket.model_dump_json(indent=4))
