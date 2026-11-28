from src.ticket import (
    Ticket,
    load_restaurants,
    calculate_order
)

restaurants = load_restaurants()


def test_order(restaurant, pizza, size, quantity, zone):
    ticket = Ticket(
        restaurant=restaurant,
        items=[
            {
                "name": pizza,
                "size": size,
                "quantity": quantity,
                "remove_ingredients": []
            }
        ],
        delivery_zone=zone,
        address="Batna Center, Street 1",
        phone="0550000001"
    )

    result = calculate_order(ticket, restaurants)

    print(f"\n{restaurant}")
    print("Subtotal:", result.subtotal, "DA")
    print("Discount:", result.discount, "DA")
    print("Delivery:", result.delivery_fee, "DA")
    print("Total:", result.total, "DA")
    print("Reward:", result.promotion_reward)


# Test 1: Pizza House 10% discount
test_order(
    "pizza_house",
    "Margherita",
    "Large",
    3,
    "Batna Center"
)

# Test 2: Italian Corner free drink
test_order(
    "italian_corner",
    "Classic Margherita",
    "Large",
    3,
    "Batna Center"
)

# Test 3: Fast Pizza free drink
test_order(
    "fast_pizza",
    "Mini Margherita",
    "Large",
    2,
    "Batna Center"
)