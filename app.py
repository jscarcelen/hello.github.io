import streamlit as st
import stripe
import json
import uuid
import pandas as pd

# Stripe configuration
stripe.api_key = "sk_test_YOUR_SECRET_KEY"  # Replace with your Stripe secret key
DOMAIN = "http://localhost:8501"  # Update this to your deployed domain

# Load products
@st.cache_data
def load_products():
    with open("products.json") as f:
        return json.load(f)

# Cart setup
if "cart" not in st.session_state:
    st.session_state.cart = {}

def add_to_cart(product_id):
    st.session_state.cart[product_id] = st.session_state.cart.get(product_id, 0) + 1

def remove_from_cart(product_id):
    if product_id in st.session_state.cart:
        st.session_state.cart[product_id] -= 1
        if st.session_state.cart[product_id] <= 0:
            del st.session_state.cart[product_id]

def get_cart_items():
    return [(prod, qty) for prod in products for pid, qty in st.session_state.cart.items() if prod["id"] == pid]

def calculate_total():
    return sum(prod["price"] * qty for prod, qty in get_cart_items())

def create_checkout_session():
    line_items = []
    for prod, qty in get_cart_items():
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": prod["price"],
                "product_data": {
                    "name": prod["name"],
                },
            },
            "quantity": qty,
        })

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=DOMAIN + "/?success=true",
            cancel_url=DOMAIN + "/?canceled=true",
        )
        return session.url
    except Exception as e:
        st.error(f"Error creating Stripe session: {e}")
        return None

# Load products
#products = load_products()
products = pd.read_json("products.json")

# Streamlit layout
st.set_page_config(page_title="Simple Shop", layout="wide")
st.title("🛍️ My E-Commerce Shop")
st.title(products)
for idx, product in enumerate(products):
    st.title(product["image"])
st.image("49.jpg", width=200)
st.image("images/49.jpg", width=200)
st.image(products["image"][0], width=200)


# Gallery view
cols = st.columns(3)
for idx, product in enumerate(products):
    with cols[idx % 3]:
        st.image(product["image"], width=200)
        st.markdown(f"**{product['name']}**")
        st.markdown(f"💵 ${product['price'] / 100:.2f}")
        st.button("Add to Cart", key=f"add_{product['id']}", on_click=add_to_cart, args=(product["id"],))

st.divider()

# Cart section
st.subheader("🛒 Your Cart")
cart_items = get_cart_items()
if not cart_items:
    st.info("Your cart is empty.")
else:
    for prod, qty in cart_items:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.markdown(f"{prod['name']} (x{qty}) - ${prod['price'] * qty / 100:.2f}")
        with col2:
            st.button("➕", key=f"plus_{prod['id']}", on_click=add_to_cart, args=(prod["id"],))
        with col3:
            st.button("➖", key=f"minus_{prod['id']}", on_click=remove_from_cart, args=(prod["id"],))

    st.markdown(f"### Total: ${calculate_total() / 100:.2f}")
    if st.button("💳 Checkout with Stripe"):
        checkout_url = create_checkout_session()
        if checkout_url:
            st.success("Redirecting to Stripe Checkout...")
            st.markdown(f"[Click here if not redirected]({checkout_url})", unsafe_allow_html=True)
            st.markdown(
                f"""<meta http-equiv="refresh" content="1;url={checkout_url}">""",
                unsafe_allow_html=True,
            )
