
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
import json
from pathlib import Path

class OrderItem(BaseModel):
    """One pizza in the customer's order."""

    name: str
    size: Literal["Small", "Medium", "Large"]
    quantity: int = Field(gt=0)
    remove_ingredients: List[str] = Field(default_factory=list)


class Ticket(BaseModel):
    """The complete customer's delivery order."""

    restaurant: str
    items: List[OrderItem] = Field(min_length=1)
    delivery_zone: str
    address: str
    phone: str

    @field_validator("restaurant", "delivery_zone", "address")
    @classmethod
    def validate_not_empty(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        value = value.strip()

        if not value.isdigit() or len(value) != 10:
            raise ValueError(
                "Phone number must contain exactly 10 digits."
            )

        return value


class OrderResult(BaseModel):
    """Validated order with prices calculated by Python."""

    ticket: Ticket
    subtotal: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    delivery_fee: float = Field(ge=0)
    total: float = Field(ge=0)
    promotion_reward: str | None = None
def load_restaurants():
    """Load restaurant data from the JSON database."""

    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "restaurants.json"

    with open(data_path, "r", encoding="utf-8") as file:
        return json.load(file)
def validate_ticket_against_menu(ticket, restaurants):
    """Check that every order detail exists in the restaurant menu."""
    if ticket.restaurant not in restaurants:
        raise ValueError("Restaurant does not exist.")

    restaurant = restaurants[ticket.restaurant]

    menu = {
        item["name"].lower(): item
        for item in restaurant["items"]
    }

    for order_item in ticket.items:

        pizza = menu.get(order_item.name.lower())

        if pizza is None:
            raise ValueError(
                f"{order_item.name} is not available at this restaurant."
            )

        if order_item.size not in pizza["sizes"]:
            raise ValueError(
                f"{order_item.size} is unavailable for {order_item.name}."
            )

        available_ingredients = [
            ingredient.lower()
            for ingredient in pizza["ingredients"]
        ]

        for ingredient in order_item.remove_ingredients:
            if ingredient.lower() not in available_ingredients:
                raise ValueError(
                    f"{ingredient} is not an ingredient in {order_item.name}."
                )

    if ticket.delivery_zone not in restaurant["delivery_zones"]:
        raise ValueError("Delivery zone is not available.")

    return True

def calculate_order(ticket, restaurants):
    """Calculate subtotal, discount, delivery fee and final total."""

    validate_ticket_against_menu(ticket, restaurants)

    restaurant = restaurants[ticket.restaurant]

    subtotal = 0

    # Calculate pizza prices
    for order_item in ticket.items:
        pizza = next(
            item for item in restaurant["items"]
            if item["name"].lower() == order_item.name.lower()
        )

        price = pizza["sizes"][order_item.size]

        subtotal += price * order_item.quantity

    # Calculate promotion
    discount = 0
    promotion_reward = None

    promotion = restaurant["promotion"].lower()

    if ticket.restaurant == "pizza_house":
        if subtotal > 2000:
            discount = round(subtotal * 0.10, 2)

    elif ticket.restaurant == "italian_corner":
        if subtotal > 2500:
            promotion_reward = "Free drink"

    elif ticket.restaurant == "fast_pizza":
        large_pizzas = sum(
            item.quantity
            for item in ticket.items
            if item.size == "Large"
        )

        if large_pizzas >= 2:
            promotion_reward = "One free drink"

    # Delivery fee
    delivery_fee = restaurant["delivery_zones"][ticket.delivery_zone]

    # Final total
    total = subtotal - discount + delivery_fee

    return OrderResult(
        ticket=ticket,
        subtotal=subtotal,
        discount=discount,
        delivery_fee=delivery_fee,
        total=total,
        promotion_reward=promotion_reward
    )