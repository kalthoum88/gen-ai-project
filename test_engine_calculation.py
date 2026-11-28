
from src.engine import OrderEngine

engine = OrderEngine("pizza_house")

engine.add_item("Margherita", "Large", 2)

# First test: incomplete delivery information
print("TEST 1: Missing delivery details")

try:
    engine.calculate_total()
except ValueError as error:
    print("Correctly rejected:", error)

# Add delivery information
engine.set_delivery_details(
    "Batna Center",
    "Batna Center, Street 1",
    "0550000001"
)

# Second test: calculate complete order
print("\nTEST 2: Complete order")

result = engine.calculate_total()

print("Subtotal:", result.subtotal, "DA")
print("Discount:", result.discount, "DA")
print("Delivery:", result.delivery_fee, "DA")
print("Total:", result.total, "DA")

print("\nBASKET:")
print(engine.get_basket())
def build_recap(self):
        """Prepare an order summary for customer review."""

        result = self.calculate_total()

        recap = {
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

        return recap

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

        if not getattr(self, "confirmed", False):
            raise ValueError("The customer must confirm the order first.")

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
