from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from src.assistant import PizzaAssistant


# ============================================================
# PAGE + PROJECT CONFIGURATION
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_ROOT / "data" / "restaurants.json"
CSS_PATH = PROJECT_ROOT / "styles.css"

st.set_page_config(
    page_title="Pizza AI | Smart Ordering",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_restaurants() -> dict[str, Any]:
    with DATABASE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_css() -> None:
    if CSS_PATH.exists():
        st.markdown(
            f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )
    else:
        st.warning("styles.css was not found beside app.py.")


restaurants = load_restaurants()
load_css()


# ============================================================
# SESSION STATE
# Keep one assistant object per restaurant across reruns.
# ============================================================
def initialize_state() -> None:
    defaults = {
        "active_page": "AI Assistant",
        "selected_restaurant": next(iter(restaurants)),
        "assistants": {},
        "chat_by_restaurant": {},
        "confirmed_tickets": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    for restaurant_id in restaurants:
        st.session_state.chat_by_restaurant.setdefault(
            restaurant_id,
            [
                {
                    "role": "assistant",
                    "content": (
                        "Welcome to Pizza AI! 🍕\n\n"
                        "I can answer questions about this restaurant's menu, "
                        "ingredients, allergens, prices and delivery information. "
                        "I can also take your order and help you modify it."
                    ),
                }
            ],
        )


initialize_state()


def get_assistant(restaurant_id: str) -> PizzaAssistant:
    """Return the persistent assistant for the selected restaurant."""
    if restaurant_id not in st.session_state.assistants:
        st.session_state.assistants[restaurant_id] = PizzaAssistant(restaurant_id)
    return st.session_state.assistants[restaurant_id]


# ============================================================
# HELPERS
# ============================================================
def money(value: Any) -> str:
    try:
        return f"{float(value):,.0f} DA"
    except (TypeError, ValueError):
        return "—"


def restaurant_display_name(restaurant_id: str) -> str:
    return restaurants[restaurant_id].get(
        "name", restaurant_id.replace("_", " ").title()
    )


def find_menu_item(restaurant_id: str, name: str) -> dict[str, Any] | None:
    for item in restaurants[restaurant_id].get("items", []):
        if item.get("name", "").casefold() == name.casefold():
            return item
    return None


def get_size_price(restaurant_id: str, name: str, size: str) -> int:
    menu_item = find_menu_item(restaurant_id, name)
    if not menu_item:
        return 0

    sizes = menu_item.get("sizes", {})
    try:
        return int(sizes.get(size, 0))
    except (TypeError, ValueError):
        return 0


def get_basket(assistant: PizzaAssistant) -> list[dict[str, Any]]:
    basket = assistant.show_basket()
    return basket if isinstance(basket, list) else []


def basket_subtotal(restaurant_id: str, basket: list[dict[str, Any]]) -> int:
    total = 0
    for item in basket:
        price = get_size_price(
            restaurant_id,
            item.get("name", ""),
            item.get("size", ""),
        )
        total += price * int(item.get("quantity", 1))
    return total


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def format_order_result(result: Any, assistant: PizzaAssistant) -> str:
    """Turn backend results into a readable chat response."""
    if isinstance(result, str):
        return result

    if not isinstance(result, dict):
        return safe_text(result) or "Your message has been processed."

    next_message = result.get("next_message")
    if next_message:
        return safe_text(next_message)

    status = result.get("status", "")

    if status == "items_added":
        return "I've added those items to your order. What else would you like?"

    if status == "order_modified":
        return "Your order has been updated. Would you like to make another change?"

    if status == "needs_delivery_information":
        return (
            result.get("message")
            or "Your items are in the basket. I still need your delivery details."
        )

    if status == "delivery_details_complete":
        return "Thank you! Your delivery details are complete. You can review your order."

    if status:
        message = result.get("message")
        return safe_text(message) if message else f"Order update: {status.replace('_', ' ')}."

    return safe_text(result)


def page_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="page-heading">
            <div class="eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-lockup">
                <div class="brand-mark">✦</div>
                <div>
                    <div class="brand-name">PIZZA <span>AI</span></div>
                    <div class="brand-caption">INTELLIGENT ORDERING</div>
                </div>
            </div>
            <div class="sidebar-label">WORKSPACE</div>
            """,
            unsafe_allow_html=True,
        )

        pages = [
            ("AI Assistant", "✦"),
            ("Menu & Restaurants", "▦"),
            ("Current Order", "🛍"),
            ("Order History", "▤"),
            ("Project Insights", "◫"),
        ]

        for page_name, symbol in pages:
            selected = st.session_state.active_page == page_name
            if st.button(
                f"{symbol}   {page_name}",
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.active_page = page_name
                st.rerun()

        st.markdown(
            """
            <div class="sidebar-status">
                <span class="status-dot"></span>
                <span>AI BACKEND INTEGRATION</span>
            </div>
            <div class="sidebar-footer">Python · Streamlit · Gemini · RAG</div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# LIVE BASKET + RECAP + CONFIRMATION
# ============================================================
def render_cart(
    restaurant_id: str,
    assistant: PizzaAssistant,
) -> None:
    st.markdown(
        """
        <div class="cart-heading">
            <div>
                <div class="eyebrow">YOUR SELECTION</div>
                <h2>Current order</h2>
            </div>
            <span class="cart-count">LIVE BASKET</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    basket = get_basket(assistant)

    if not basket:
        st.markdown(
            """
            <div class="empty-cart">
                <div class="empty-cart-icon">🛒</div>
                <h3>Your basket is waiting</h3>
                <p>Ask the AI assistant to add something or browse the menu.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for index, item in enumerate(basket):
        name = item.get("name", "Pizza")
        size = item.get("size", "")
        quantity = int(item.get("quantity", 1))
        unit_price = get_size_price(restaurant_id, name, size)
        removed = item.get("remove_ingredients", [])

        st.markdown(
            f"""
            <div class="cart-item">
                <div class="cart-item-icon">🍕</div>
                <div class="cart-item-info">
                    <div class="cart-item-name">{name}</div>
                    <div class="cart-item-meta">{size} · Qty {quantity}</div>
                    <div class="cart-item-meta">
                        {("No " + ", ".join(removed)) if removed else ""}
                    </div>
                </div>
                <div class="cart-item-price">{money(unit_price * quantity)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        controls = st.columns([1, 1, 1, 2])
        with controls[0]:
            if st.button("−", key=f"cart_minus_{restaurant_id}_{index}"):
                if quantity <= 1:
                    assistant.remove_item(name, size)
                else:
                    assistant.update_quantity(name, size, quantity - 1)
                st.session_state.confirmed_tickets.pop(restaurant_id, None)
                st.rerun()
        with controls[1]:
            st.markdown(
                f'<div class="quantity-value">{quantity}</div>',
                unsafe_allow_html=True,
            )
        with controls[2]:
            if st.button("+", key=f"cart_plus_{restaurant_id}_{index}"):
                assistant.update_quantity(name, size, quantity + 1)
                st.session_state.confirmed_tickets.pop(restaurant_id, None)
                st.rerun()
        with controls[3]:
            if st.button("Remove", key=f"cart_remove_{restaurant_id}_{index}"):
                assistant.remove_item(name, size)
                st.session_state.confirmed_tickets.pop(restaurant_id, None)
                st.rerun()

    st.markdown('<div class="cart-divider"></div>', unsafe_allow_html=True)

    subtotal = basket_subtotal(restaurant_id, basket)
    st.markdown(
        f"""
        <div class="grand-total">
            <span>Items subtotal</span>
            <strong>{money(subtotal)}</strong>
        </div>
        <div class="preview-note">
            This is the menu-price subtotal. The order engine calculates the
            final discount, delivery fee and total after delivery details are supplied.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Review order recap", expanded=False):
        try:
            recap = assistant.show_recap()
            st.write(f"**Restaurant:** {recap.get('restaurant', restaurant_display_name(restaurant_id))}")
            for item in recap.get("items", []):
                st.write(
                    f"• {item.get('quantity', 1)} × {item.get('size', '')} "
                    f"{item.get('name', '')}"
                )
            st.write(f"**Subtotal:** {money(recap.get('subtotal'))}")
            st.write(f"**Discount:** {money(recap.get('discount'))}")
            st.write(f"**Delivery:** {money(recap.get('delivery_fee'))}")
            st.markdown(f"### Total: {money(recap.get('total'))}")
            if recap.get("promotion_reward"):
                st.success(str(recap["promotion_reward"]))

            st.write("**Delivery zone:**", recap.get("delivery_zone") or "Not provided")
            st.write("**Address:**", recap.get("address") or "Not provided")
            st.write("**Phone:**", recap.get("phone") or "Not provided")

            if st.button(
                "Confirm this order",
                key=f"confirm_{restaurant_id}",
                type="primary",
                use_container_width=True,
            ):
                confirmation = assistant.confirm(True)
                ticket = assistant.get_ticket()
                st.session_state.confirmed_tickets[restaurant_id] = ticket
                st.success(safe_text(confirmation) or "Order confirmed.")
                st.rerun()

        except Exception:
            st.info(
                "The recap becomes available when the basket and all delivery "
                "details (zone, address and phone number) are complete. "
                "Provide any missing details in the AI chat."
            )

    confirmed_ticket = st.session_state.confirmed_tickets.get(restaurant_id)
    if confirmed_ticket:
        st.success("Order confirmed!")
        with st.expander("View validated JSON ticket", expanded=True):
            st.json(confirmed_ticket)
            st.download_button(
                "Download JSON ticket",
                data=json.dumps(confirmed_ticket, ensure_ascii=False, indent=2),
                file_name=f"{restaurant_id}_order_ticket.json",
                mime="application/json",
                key=f"download_ticket_{restaurant_id}",
                use_container_width=True,
            )


# ============================================================
# APP HEADER
# ============================================================
render_sidebar()

restaurant_options = list(restaurants.keys())
restaurant_names = {
    key: restaurant_display_name(key) for key in restaurant_options
}

top_left, top_right = st.columns([3, 1])
with top_left:
    st.markdown(
        """
        <div class="topbar-welcome">
            <div class="eyebrow">GOOD FOOD. SMARTER ORDERS.</div>
            <div class="topbar-title">Welcome to <span>Pizza AI</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_right:
    selected_id = st.selectbox(
        "Restaurant",
        options=restaurant_options,
        format_func=lambda key: restaurant_names[key],
        index=restaurant_options.index(st.session_state.selected_restaurant),
        key="restaurant_picker",
        label_visibility="collapsed",
    )
    if selected_id != st.session_state.selected_restaurant:
        st.session_state.selected_restaurant = selected_id
        st.rerun()


# Resolve the active restaurant and its persistent assistant.
restaurant_id = st.session_state.selected_restaurant
restaurant = restaurants[restaurant_id]
assistant = get_assistant(restaurant_id)
chat_messages = st.session_state.chat_by_restaurant[restaurant_id]


# ============================================================
# MAIN LAYOUT
# ============================================================
main_col, cart_col = st.columns([1.85, 1], gap="large")

with main_col:
    active_page = st.session_state.active_page

    # --------------------------------------------------------
    # AI ASSISTANT
    # --------------------------------------------------------
    if active_page == "AI Assistant":
        page_header(
            "YOUR PERSONAL ORDERING COMPANION",
            "Talk to your <span class='gold-text'>pizza assistant.</span>",
            "Ask menu questions or place and modify an order using natural language.",
        )

        st.markdown(
            """
            <div class="assistant-banner">
                <div class="assistant-avatar">✦</div>
                <div class="assistant-banner-copy">
                    <strong>Pizza AI Assistant</strong>
                    <span>Gemini · RAG menu knowledge · Conversational ordering</span>
                </div>
                <div class="assistant-online"><span></span> READY</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        interaction_mode = st.radio(
            "What would you like to do?",
            ["Ask a menu question", "Place / modify an order"],
            horizontal=True,
            key=f"interaction_mode_{restaurant_id}",
        )

        chat_box = st.container(height=440, border=False)
        with chat_box:
            for message in chat_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        prompt = st.chat_input(
            (
                "Ask about ingredients, prices, allergens or delivery..."
                if interaction_mode == "Ask a menu question"
                else "Example: Two large Margheritas, please..."
            ),
            key=f"chat_input_{restaurant_id}",
        )

        if prompt:
            chat_messages.append({"role": "user", "content": prompt})
            st.session_state.confirmed_tickets.pop(restaurant_id, None)

            with st.spinner("Pizza AI is thinking..."):
                try:
                    if interaction_mode == "Ask a menu question":
                        response = assistant.ask(prompt)
                        assistant_message = safe_text(response)
                    else:
                        result = assistant.process_order_message(prompt)
                        assistant_message = format_order_result(result, assistant)

                    if not assistant_message.strip():
                        assistant_message = "I processed that message. What would you like to do next?"

                except Exception as error:
                    assistant_message = (
                        "I couldn't process that message. "
                        "Please check the API key and backend dependencies, "
                        "then try again.\n\n"
                        f"**Technical detail:** `{type(error).__name__}: {error}`"
                    )

            chat_messages.append(
                {"role": "assistant", "content": assistant_message}
            )
            st.rerun()

        st.markdown(
            """
            <div class="language-strip">
                <span>CONVERSATION LANGUAGES</span>
                <b>English</b><i>·</i><b>Français</b><i>·</i><b>Algerian Darja</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # MENU
    # --------------------------------------------------------
    elif active_page == "Menu & Restaurants":
        page_header(
            "EXPLORE THE MENU",
            f"Discover <span class='gold-text'>{restaurant_names[restaurant_id]}.</span>",
            "Choose a pizza, select its size and add it to the real order engine.",
        )

        search = st.text_input(
            "Search menu",
            placeholder="Search pizza by name or ingredient...",
            key=f"menu_search_{restaurant_id}",
        ).strip().casefold()

        menu_items = restaurant.get("items", [])
        filtered_items = [
            item
            for item in menu_items
            if search in item["name"].casefold()
            or any(
                search in ingredient.casefold()
                for ingredient in item.get("ingredients", [])
            )
        ]

        st.markdown(
            f'<div class="menu-result-count">{len(filtered_items)} PIZZAS AVAILABLE</div>',
            unsafe_allow_html=True,
        )

        if not filtered_items:
            st.info("No pizzas match your search.")
        else:
            product_columns = st.columns(2, gap="medium")
            for index, item in enumerate(filtered_items):
                with product_columns[index % 2]:
                    with st.container(border=True):
                        st.markdown(
                            f"""
                            <div class="product-art">
                                <div class="product-art-glow"></div>
                                <div class="product-emoji">🍕</div>
                                <div class="product-art-label">FRESHLY PREPARED</div>
                            </div>
                            <div class="product-name">{item['name']}</div>
                            <div class="product-description">
                                {", ".join(item.get("ingredients", []))}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        sizes = list(item.get("sizes", {}).keys())
                        if not sizes:
                            st.warning("No sizes are configured for this item.")
                            continue

                        size = st.selectbox(
                            "Choose size",
                            sizes,
                            key=f"menu_size_{restaurant_id}_{index}",
                        )
                        price = get_size_price(restaurant_id, item["name"], size)

                        price_col, button_col = st.columns([1, 1])
                        with price_col:
                            st.markdown(
                                f'<div class="product-price">{money(price)}</div>',
                                unsafe_allow_html=True,
                            )
                        with button_col:
                            if st.button(
                                "＋ Add to order",
                                key=f"menu_add_{restaurant_id}_{index}",
                                use_container_width=True,
                                type="primary",
                            ):
                                try:
                                    assistant.add_item(item["name"], size, 1)
                                    st.session_state.confirmed_tickets.pop(
                                        restaurant_id, None
                                    )
                                    st.toast(f"{item['name']} added to your order.")
                                    st.rerun()
                                except Exception as error:
                                    st.error(f"Could not add item: {error}")

                        with st.expander("Ingredients & allergens"):
                            st.write(
                                "**Ingredients:**",
                                ", ".join(item.get("ingredients", [])),
                            )
                            st.write(
                                "**Allergens:**",
                                ", ".join(item.get("allergens", [])) or "Not specified",
                            )

    # --------------------------------------------------------
    # CURRENT ORDER
    # --------------------------------------------------------
    elif active_page == "Current Order":
        page_header(
            "YOUR BASKET",
            "Review your <span class='gold-text'>current order.</span>",
            "Your basket is connected to the Python order engine.",
        )
        st.info("Use the live order panel on the right to review and confirm.")
        if st.button("Open AI Assistant", type="primary"):
            st.session_state.active_page = "AI Assistant"
            st.rerun()
        if st.button("Browse menu"):
            st.session_state.active_page = "Menu & Restaurants"
            st.rerun()

    # --------------------------------------------------------
    # ORDER HISTORY
    # --------------------------------------------------------
    elif active_page == "Order History":
        page_header(
            "ORDER ACTIVITY",
            "Your <span class='gold-text'>order history.</span>",
            "Confirmed ticket for the current restaurant.",
        )
        ticket = st.session_state.confirmed_tickets.get(restaurant_id)
        if ticket:
            st.success("A confirmed order is available.")
            st.json(ticket)
        else:
            st.markdown(
                """
                <div class="empty-state-card">
                    <div class="empty-cart-icon">🧾</div>
                    <h3>No confirmed order yet</h3>
                    <p>Once an order is confirmed, its ticket will appear here.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # PROJECT INSIGHTS
    # --------------------------------------------------------
    elif active_page == "Project Insights":
        page_header(
            "SYSTEM OVERVIEW",
            "A smarter way to <span class='gold-text'>order pizza.</span>",
            "The main capabilities demonstrated by this project.",
        )
        metric_cols = st.columns(3)
        for column, (value, label) in zip(
            metric_cols,
            [("3", "RESTAURANTS"), ("45", "MENU ITEMS"), ("3", "LANGUAGE MODES")],
        ):
            with column:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-value">{value}</div>
                        <div class="metric-label">{label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown(
            """
            <div class="feature-list">
                <div><span>✦</span><b>Retrieval-Augmented Generation</b><small>Grounded menu questions and restaurant information.</small></div>
                <div><span>✦</span><b>Conversational ordering</b><small>Natural-language item selection and order modifications.</small></div>
                <div><span>✦</span><b>Validated order tickets</b><small>Python validation and deterministic price calculation.</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# RIGHT-HAND LIVE ORDER PANEL
# ============================================================
with cart_col:
    with st.container(border=True):
        render_cart(restaurant_id, assistant)


st.markdown(
    """
    <div class="app-footer">
        PIZZA AI <span>·</span> SMART RESTAURANT ORDERING <span>·</span> GEMINI + PYTHON
    </div>
    """,
    unsafe_allow_html=True,
)
