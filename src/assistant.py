
import json
import re

from src.rag import (
    ask_restaurant_assistant,
    generate_text,
    load_restaurants
)
from src.engine import OrderEngine


class PizzaAssistant:
    """Connect natural-language messages to the validated order engine."""

    def __init__(self, restaurant_id):
        self.engine = OrderEngine(restaurant_id)
        self.restaurant_id = restaurant_id
        self.restaurants = load_restaurants()

        # Unfinished pizza information.
        self.pending_items = []

        # Delivery information collected across messages.
        self.pending_delivery = {
            "delivery_zone": None,
            "address": None,
            "phone": None
        }

    # ---------------------------------------------------------
    # 1. NATURAL-LANGUAGE INFORMATION EXTRACTION
    # ---------------------------------------------------------

    def extract_order_message(self, message, pending_items=None):
        """Extract order, modification and delivery information."""

        restaurant = self.restaurants[self.restaurant_id]

        menu = [
            {
                "name": item["name"],
                "sizes": list(item["sizes"].keys()),
                "ingredients": item["ingredients"]
            }
            for item in restaurant["items"]
        ]

        pending_context = json.dumps(
            pending_items or [],
            ensure_ascii=False,
            indent=2
        )

        delivery_context = json.dumps(
            self.pending_delivery,
            ensure_ascii=False,
            indent=2
        )

        basket_context = json.dumps(
            self.engine.get_basket(),
            ensure_ascii=False,
            indent=2
        )

        prompt = f"""
You are an information extraction assistant for a pizza ordering system.

Restaurant: {restaurant["name"]}

Available menu:
{json.dumps(menu, ensure_ascii=False, indent=2)}

Current customer basket:
{basket_context}

Previous unfinished pizza information:
{pending_context}

Previously collected delivery information:
{delivery_context}

New customer message:
{message}

Return ONLY one valid JSON object with this structure:

{{
    "intent": "add_item",
    "action": "add_item",
    "target_name": null,
    "current_size": null,
    "new_size": null,
    "quantity": null,
    "remove_ingredients": [],
    "items": [
        {{
            "name": "exact menu name",
            "size": "Small, Medium, Large, or null",
            "quantity": 1,
            "remove_ingredients": []
        }}
    ],
    "delivery_zone": null,
    "address": null,
    "phone": null
}}

RULES:

1. MENU
- Use exact pizza names from the available menu.
- Never invent a pizza or ingredient.
- If the pizza name is unclear, use null.

2. SIZE
- Available sizes: Small, Medium, Large.
- If missing, use null.
- If the customer gives a size that completes a pending order,
  apply it to the appropriate pizza.

3. QUANTITY
- If missing, use 1 for new pizzas.
- Preserve previous quantities when completing pending orders.
- For modifications, quantity means the new total quantity,
  not the number to add.

4. INGREDIENT MODIFICATIONS
- Only include explicitly requested ingredient removals.
- Only use ingredients belonging to that pizza.
- For an ingredient modification, preserve existing removals
  unless the customer explicitly asks to restore an ingredient.

5. PENDING ORDERS
- Use previous unfinished order information.
- Preserve previously extracted information.
- Do not create duplicate pizzas.
- If the customer says only "Large", apply it to the pizza
  waiting for a size.
- If the customer clearly starts a new order, do not mix it
  with the previous unfinished order.

6. DELIVERY
- Extract delivery_zone, address and phone if provided.
- Preserve previously collected information.
- Return null for information not supplied in this message.
- Never invent delivery information.

7. INTENT
Use these intent values:

- "add_item": Customer orders a new pizza.
- "provide_details": Customer supplies delivery information.
- "modify_order": Customer changes an existing basket item.
- "other": Message is unrelated to ordering.

8. ORDER MODIFICATIONS

Use these action values:

- "add_item": Add a new pizza.
- "remove_item": Remove a pizza from the basket.
- "update_quantity": Change the quantity of a pizza.
- "change_size": Change the size of an existing pizza.
- "update_ingredients": Change ingredients to remove.

For modifications:

- Set intent to "modify_order".
- Use target_name with the exact menu name.
- Use current_size when the customer identifies the existing size.
- Use new_size for a requested size change.
- Use quantity for the new total quantity.
- Use remove_ingredients for requested ingredient removals.
- Do not invent items, sizes or ingredients.
- Do not add a new pizza when the customer is modifying an
  existing one.
- Use the current basket to identify the pizza being modified.
- If the customer says "remove the BBQ Chicken", identify it
  as remove_item.
- If the customer says "make it two", identify it as
  update_quantity when the basket makes the target clear.

EXAMPLES:

"Actually, make my Margherita quantity two"
=> intent: modify_order
=> action: update_quantity
=> target_name: Margherita
=> quantity: 2

"Change my Margherita to Medium"
=> intent: modify_order
=> action: change_size
=> target_name: Margherita
=> new_size: Medium

"Remove the BBQ Chicken"
=> intent: modify_order
=> action: remove_item
=> target_name: BBQ Chicken

"No onions on my BBQ Chicken"
=> intent: modify_order
=> action: update_ingredients
=> target_name: BBQ Chicken
=> remove_ingredients: ["onions"]

"Give me another large Margherita"
=> intent: add_item
=> action: add_item

Return JSON only. No Markdown or explanations.
"""

        response = generate_text(prompt).strip()

        # Remove Markdown code fences if Gemini adds them.
        if response.startswith("```"):
            response = response.replace("```json", "", 1)
            response = response.replace("```", "").strip()

        try:
            result = json.loads(response)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Could not read the assistant's JSON response: {response}"
            ) from error

        if not isinstance(result, dict):
            raise ValueError(
                "The extracted response must be a JSON object."
            )

        if not isinstance(result.get("items", []), list):
            raise ValueError("Extracted items must be a list.")

        result.setdefault("intent", "other")
        result.setdefault("action", "add_item")
        result.setdefault("target_name", None)
        result.setdefault("current_size", None)
        result.setdefault("new_size", None)
        result.setdefault("quantity", None)
        result.setdefault("remove_ingredients", [])
        result.setdefault("items", [])
        result.setdefault("delivery_zone", None)
        result.setdefault("address", None)
        result.setdefault("phone", None)

        return result

    # ---------------------------------------------------------
    # 2. DELIVERY INFORMATION
    # ---------------------------------------------------------

    def _update_delivery_information(self, extracted):
        """Save and validate delivery information."""

        for field in ("delivery_zone", "address", "phone"):
            value = extracted.get(field)

            if isinstance(value, str) and value.strip():
                self.pending_delivery[field] = value.strip()

        restaurant = self.restaurants[self.restaurant_id]

        available_zones = restaurant["delivery_zones"]

        zone = self.pending_delivery["delivery_zone"]

        # Match delivery zones without case sensitivity.
        if zone:
            matching_zone = next(
                (
                    available
                    for available in available_zones
                    if available.casefold() == zone.casefold()
                ),
                None
            )

            if matching_zone is None:
                return {
                    "status": "invalid_delivery_zone",
                    "message": (
                        f"We don't deliver to {zone}. "
                        f"Available zones: {', '.join(available_zones)}."
                    )
                }

            self.pending_delivery["delivery_zone"] = matching_zone

        phone = self.pending_delivery["phone"]

        if phone:
            cleaned_phone = re.sub(r"\s+", "", phone)

            if not re.fullmatch(r"\d{10}", cleaned_phone):
                return {
                    "status": "invalid_phone",
                    "message": (
                        "Please provide a valid 10-digit phone number."
                    )
                }

            self.pending_delivery["phone"] = cleaned_phone

        missing = [
            field
            for field, value in self.pending_delivery.items()
            if not value
        ]

        if missing:
            questions = {
                "delivery_zone": (
                    "Which delivery zone are you in? "
                    f"Available zones: {', '.join(available_zones)}."
                ),
                "address": "What is your delivery address?",
                "phone": "What is your 10-digit telephone number?"
            }

            return {
                "status": "needs_delivery_information",
                "missing": missing,
                "message": questions[missing[0]]
            }

        self.engine.set_delivery_details(
            zone=self.pending_delivery["delivery_zone"],
            address=self.pending_delivery["address"],
            phone=self.pending_delivery["phone"]
        )

        return {
            "status": "delivery_details_complete",
            "delivery_details": self.pending_delivery.copy()
        }

    def _process_delivery_message(self, message):
        """Recognize clear delivery answers without calling Gemini."""

        restaurant = self.restaurants[self.restaurant_id]
        available_zones = restaurant["delivery_zones"]

        cleaned_message = message.strip()

        # Recognize a delivery zone.
        for zone in available_zones:
            if cleaned_message.casefold() == zone.casefold():
                self.pending_delivery["delivery_zone"] = zone

                return self._update_delivery_information({})

        # Recognize a 10-digit phone number.
        cleaned_phone = re.sub(r"\s+", "", cleaned_message)

        if re.fullmatch(r"\d{10}", cleaned_phone):
            self.pending_delivery["phone"] = cleaned_phone

            return self._update_delivery_information({})

        # Recognize an address when the zone is already known.
        address_keywords = (
            "street", "st.", "rue", "avenue", "avenue",
            "road", "road", "حي", "شارع", "طريق",
            "near", "nearby", "building", "apartment"
        )

        looks_like_address = (
            bool(re.search(r"\d", cleaned_message))
            or any(
                keyword in cleaned_message.casefold()
                for keyword in address_keywords
            )
        )

        if (
            self.pending_delivery["delivery_zone"]
            and not self.pending_delivery["address"]
            and looks_like_address
        ):
            self.pending_delivery["address"] = cleaned_message

            return self._update_delivery_information({})

        return None

    # ---------------------------------------------------------
    # 3. ORDER MODIFICATIONS
    # ---------------------------------------------------------

    def _process_modification(self, extracted):
        """Apply a customer's requested basket modification."""

        action = extracted.get("action")
        name = extracted.get("target_name")
        size = extracted.get("current_size")

        if not name:
            return {
                "status": "needs_clarification",
                "message": "Which pizza would you like to modify?"
            }

        basket = self.engine.get_basket()

        matching_items = [
            item for item in basket
            if item["name"].casefold() == name.casefold()
            and (not size or item["size"] == size)
        ]

        if not matching_items:
            return {
                "status": "item_not_found",
                "message": f"{name} was not found in your basket."
            }

        # Remove a pizza.
        if action == "remove_item":

            if not size and len(matching_items) > 1:
                return {
                    "status": "needs_clarification",
                    "message": (
                        f"Which size of {name} should I remove?"
                    )
                }

            selected = matching_items[0]

            result = self.engine.remove_item(
                selected["name"],
                selected["size"]
            )

        # Change quantity.
        elif action == "update_quantity":

            quantity = extracted.get("quantity")

            if (
                not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity < 1
            ):
                return {
                    "status": "invalid_quantity",
                    "message": "Please provide a valid quantity."
                }

            if len(matching_items) > 1:
                return {
                    "status": "needs_clarification",
                    "message": (
                        f"Which size of {name} should I update?"
                    )
                }

            selected = matching_items[0]

            result = self.engine.update_quantity(
                selected["name"],
                selected["size"],
                quantity
            )

        # Change pizza size.
        elif action == "change_size":

            new_size = extracted.get("new_size")

            if not new_size:
                return {
                    "status": "needs_clarification",
                    "message": "What size would you like instead?"
                }

            if len(matching_items) > 1:
                return {
                    "status": "needs_clarification",
                    "message": (
                        "Please specify which pizza size to change."
                    )
                }

            selected = matching_items[0]

            result = self.engine.update_size(
                selected["name"],
                selected["size"],
                new_size
            )

        # Change ingredient removals.
        elif action == "update_ingredients":

            removals = extracted.get("remove_ingredients", [])

            if not isinstance(removals, list):
                return {
                    "status": "invalid_modifications",
                    "message": "The ingredient modifications are invalid."
                }

            if len(matching_items) > 1:
                return {
                    "status": "needs_clarification",
                    "message": (
                        "Please specify which pizza size to modify."
                    )
                }

            selected = matching_items[0]

            existing = selected["remove_ingredients"]

            combined_removals = list(dict.fromkeys(
                existing + removals
            ))

            result = self.engine.update_ingredients(
                selected["name"],
                selected["size"],
                combined_removals
            )

        else:
            return {
                "status": "unsupported_modification",
                "message": "I couldn't understand that modification."
            }

        return {
            "status": "order_modified",
            "message": result,
            "basket": self.engine.get_basket()
        }

    # ---------------------------------------------------------
    # 4. MAIN CONVERSATION PROCESSING
    # ---------------------------------------------------------

    def process_order_message(self, message):
        """Process a customer's order, modification or delivery message."""

        if not isinstance(message, str) or not message.strip():
            return {
                "status": "invalid_message",
                "message": "Please enter a message."
            }

        # First, recognize clear delivery answers using Python.
        if self.engine.get_basket() and not self.pending_items:
            delivery_response = self._process_delivery_message(message)

            if delivery_response is not None:
                return delivery_response

        # Use Gemini for natural-language interpretation.
        extracted = self.extract_order_message(
            message,
            self.pending_items
        )

        intent = extracted.get("intent")

        # Handle basket modifications.
        if intent == "modify_order":
            return self._process_modification(extracted)

        if intent not in ("add_item", "provide_details"):
            return {
                "status": "not_an_order",
                "extracted": extracted
            }

        # Save any delivery information extracted from the message.
        delivery_result = self._update_delivery_information(extracted)

        if delivery_result["status"] in (
            "invalid_delivery_zone",
            "invalid_phone"
        ):
            return delivery_result

        requested_items = extracted.get("items", [])

        # Handle messages containing delivery details only.
        if not requested_items and not self.pending_items:

            if intent == "provide_details":
                return delivery_result

            if any(self.pending_delivery.values()):
                return delivery_result

            return {
                "status": "needs_clarification",
                "message": "Which pizza would you like?"
            }

        restaurant = self.restaurants[self.restaurant_id]

        menu = {
            item["name"]: item
            for item in restaurant["items"]
        }

        # Validate every requested pizza before changing the basket.
        for item in requested_items:

            if not isinstance(item, dict):
                return {
                    "status": "invalid_order",
                    "message": "One of the requested items is invalid."
                }

            name = item.get("name")
            size = item.get("size")
            quantity = item.get("quantity", 1)
            removals = item.get("remove_ingredients", [])

            if not name or name not in menu:
                self.pending_items = requested_items

                return {
                    "status": "needs_clarification",
                    "message": (
                        f"I couldn't identify '{name}'. "
                        "Please choose a pizza from the menu."
                    )
                }

            if not size:
                self.pending_items = requested_items

                return {
                    "status": "needs_information",
                    "message": f"What size would you like for {name}?"
                }

            if size not in menu[name]["sizes"]:
                return {
                    "status": "invalid_size",
                    "message": f"{size} is not available for {name}."
                }

            if (
                not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity < 1
            ):
                return {
                    "status": "invalid_quantity",
                    "message": (
                        f"Please provide a valid quantity for {name}."
                    )
                }

            if not isinstance(removals, list):
                return {
                    "status": "invalid_modifications",
                    "message": f"Modifications for {name} are invalid."
                }

            available_ingredients = {
                ingredient.lower()
                for ingredient in menu[name]["ingredients"]
            }

            for ingredient in removals:
                if (
                    not isinstance(ingredient, str)
                    or ingredient.lower() not in available_ingredients
                ):
                    return {
                        "status": "invalid_modifications",
                        "message": (
                            f"{ingredient} is not an ingredient in {name}."
                        )
                    }

        # All requested pizzas are valid. Add them to the basket.
        for item in requested_items:
            self.engine.add_item(
                name=item["name"],
                size=item["size"],
                quantity=item.get("quantity", 1),
                remove_ingredients=item.get("remove_ingredients", [])
            )

        # Clear unfinished order information after successful addition.
        self.pending_items = []

        result = {
            "status": "items_added",
            "basket": self.engine.get_basket()
        }

        if delivery_result["status"] == "needs_delivery_information":
            result["next_message"] = delivery_result["message"]
            result["missing_delivery_information"] = (
                delivery_result["missing"]
            )

        return result

    # ---------------------------------------------------------
    # 5. PUBLIC METHODS FOR THE INTERFACE
    # ---------------------------------------------------------

    def ask(self, question):
        """Ask a restaurant menu question using RAG."""

        return ask_restaurant_assistant(
            question,
            self.restaurant_id
        )

    def add_item(self, name, size, quantity=1, remove_ingredients=None):
        return self.engine.add_item(
            name,
            size,
            quantity,
            remove_ingredients
        )

    def remove_item(self, name, size):
        return self.engine.remove_item(name, size)

    def update_quantity(self, name, size, quantity):
        return self.engine.update_quantity(
            name,
            size,
            quantity
        )

    def update_size(self, name, old_size, new_size):
        return self.engine.update_size(
            name,
            old_size,
            new_size
        )

    def update_ingredients(self, name, size, remove_ingredients):
        return self.engine.update_ingredients(
            name,
            size,
            remove_ingredients
        )

    def set_delivery_details(self, zone, address, phone):
        return self._update_delivery_information({
            "delivery_zone": zone,
            "address": address,
            "phone": phone
        })

    def show_basket(self):
        return self.engine.get_basket()

    def show_recap(self):
        return self.engine.build_recap()

    def confirm(self, confirmed):
        return self.engine.confirm_order(confirmed)

    def get_ticket(self):
        return self.engine.get_final_ticket()
