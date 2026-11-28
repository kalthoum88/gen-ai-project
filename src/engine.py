
from src.ticket import (
    Ticket,
    OrderItem,
    load_restaurants,
    calculate_order
)


class OrderEngine:
    """Manage a customer's pizza order."""

    def __init__(self, restaurant_id):
        self.restaurants = load_restaurants()

        if restaurant_id not in self.restaurants:
            raise ValueError("Restaurant does not exist.")

        self.restaurant_id = restaurant_id
        self.items = []

        self.delivery_zone = None
        self.address = None
        self.phone = None
        self.confirmed = False
  
    def add_item(self, name, size, quantity=1, remove_ingredients=None):
        """Add a pizza after checking it against the restaurant menu."""

        restaurant = self.restaurants[self.restaurant_id]

        pizza = next(
            (
                item for item in restaurant["items"]
                if item["name"].lower() == name.lower()
            ),
            None
        )

        if pizza is None:
            raise ValueError(f"{name} is not available.")

        if size not in pizza["sizes"]:
            raise ValueError(f"{size} is not available for {name}.")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        remove_ingredients = remove_ingredients or []

        available_ingredients = [
            ingredient.lower()
            for ingredient in pizza["ingredients"]
        ]

        for ingredient in remove_ingredients:
            if ingredient.lower() not in available_ingredients:
                raise ValueError(
                    f"{ingredient} is not an ingredient in {name}."
                )

        item = OrderItem(
            name=pizza["name"],
            size=size,
            quantity=quantity,
            remove_ingredients=remove_ingredients
        )

        self.confirmed = False
        self.items.append(item)

        return "Pizza added successfully."

    def remove_item(self, name, size):
        """Remove a pizza from the order."""

        for item in self.items:
            if (
                item.name.lower() == name.lower()
                and item.size == size
            ):
                self.confirmed = False
                self.items.remove(item)
                return "Pizza removed successfully."

        return "Pizza not found in the order."

    def update_quantity(self, name, size, new_quantity):
        """Change the quantity of an existing pizza."""

        if new_quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        for item in self.items:
            if (
                item.name.lower() == name.lower()
                and item.size == size
            ):
                self.confirmed = False
                item.quantity = new_quantity
                return "Quantity updated successfully."

        return "Pizza not found in the order."
    
    def update_size(self, name, old_size, new_size):
        """Change the size of an existing pizza."""

        restaurant = self.restaurants[self.restaurant_id]

        pizza = next(
            (
                item for item in restaurant["items"]
                if item["name"].lower() == name.lower()
            ),
            None
        )

        if pizza is None:
            raise ValueError(f"{name} is not available.")

        if new_size not in pizza["sizes"]:
            raise ValueError(
                f"{new_size} is not available for {name}."
            )

        for index, item in enumerate(self.items):
            if (
                item.name.lower() == name.lower()
                and item.size == old_size
            ):
                updated_item = OrderItem(
                    name=item.name,
                    size=new_size,
                    quantity=item.quantity,
                    remove_ingredients=item.remove_ingredients
                )

                self.confirmed = False
                self.items[index] = updated_item

                return "Pizza size updated successfully."

        return "Pizza not found in the order."

    def update_ingredients(self, name, size, remove_ingredients):
        """Update the ingredients the customer wants removed."""

        restaurant = self.restaurants[self.restaurant_id]

        pizza = next(
            (
                item for item in restaurant["items"]
                if item["name"].lower() == name.lower()
            ),
            None
        )

        if pizza is None:
            raise ValueError(f"{name} is not available.")

        if not isinstance(remove_ingredients, list):
            raise ValueError("Ingredient removals must be a list.")

        available_ingredients = {
            ingredient.lower()
            for ingredient in pizza["ingredients"]
        }

        for ingredient in remove_ingredients:
            if (
                not isinstance(ingredient, str)
                or ingredient.lower() not in available_ingredients
            ):
                raise ValueError(
                    f"{ingredient} is not an ingredient in {name}."
                )

        for index, item in enumerate(self.items):
            if (
                item.name.lower() == name.lower()
                and item.size == size
            ):
                updated_item = OrderItem(
                    name=item.name,
                    size=item.size,
                    quantity=item.quantity,
                    remove_ingredients=remove_ingredients
                )

                self.confirmed = False
                self.items[index] = updated_item

                return "Pizza ingredients updated successfully."

        return "Pizza not found in the order."

    def set_delivery_details(self, zone, address, phone):
        """Save delivery information."""
        self.confirmed = False
        self.delivery_zone = zone
        self.address = address
        self.phone = phone

        return "Delivery information saved."

    def calculate_total(self):
        """Calculate the current order total."""

        if not self.items:
            raise ValueError("Your basket is empty.")

        if not all([
            self.delivery_zone,
            self.address,
            self.phone
        ]):
            raise ValueError("Delivery information is incomplete.")

        ticket = Ticket(
            restaurant=self.restaurant_id,
            items=self.items,
            delivery_zone=self.delivery_zone,
            address=self.address,
            phone=self.phone
        )

        return calculate_order(ticket, self.restaurants)

    def get_basket(self):
        """Return the current basket."""

        return [
            {
                "name": item.name,
                "size": item.size,
                "quantity": item.quantity,
                "remove_ingredients": item.remove_ingredients
            }
            for item in self.items
        ]

    def build_recap(self):
        """Prepare an order summary for customer review."""

        result = self.calculate_total()

        return {
            "restaurant": self.restaurant_id,
            "items": self.get_basket(),
            "delivery_zone": self.delivery_zone,
            "address": self.address,
            "phone": self.phone,
            "subtotal": result.subtotal,
            "discount": result.discount,
            "delivery_fee": result.delivery_fee,
            "total": result.total,
            "promotion_reward": result.promotion_reward,
            "status": "awaiting_confirmation"
        }

    def confirm_order(self, confirmed):
        """Confirm or reject the customer's order."""

        if not isinstance(confirmed, bool):
            raise ValueError("Confirmation must be True or False.")

        self.confirmed = confirmed

        if confirmed:
            return "Order confirmed."

        return "Order not confirmed."

    def get_final_ticket(self):
        """Return the final ticket only after confirmation."""

        if not self.confirmed:
            raise ValueError(
                "The customer must confirm the order first."
            )

        recap = self.build_recap()

        ticket = Ticket(
            restaurant=self.restaurant_id,
            items=self.items,
            delivery_zone=self.delivery_zone,
            address=self.address,
            phone=self.phone
        )

        return {
            "ticket": ticket.model_dump(),
            "subtotal": recap["subtotal"],
            "discount": recap["discount"],
            "delivery_fee": recap["delivery_fee"],
            "total": recap["total"],
            "promotion_reward": recap["promotion_reward"],
            "status": "confirmed"
        }
