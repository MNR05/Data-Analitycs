"""Deterministic, fully fictional demo. Never label these rows as Olist data."""
from __future__ import annotations
from datetime import datetime, timedelta
from random import Random
import pandas as pd


def generate_demo(seed: int = 42, n_orders: int = 900) -> dict[str, pd.DataFrame]:
    r = Random(seed)
    states = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE"]
    categories = [
        ("eletronicos", "electronics"),
        ("casa", "home_goods"),
        ("beleza", "health_beauty"),
        ("esporte", "sports_leisure"),
        ("livros", "books"),
        ("moda", "fashion"),
    ]
    customers, products, orders, items, reviews = [], [], [], [], []
    for i, (pt, en) in enumerate(categories):
        products.append({"product_id": f"demo-product-{i}", "product_category_name": pt})
    first_day = datetime(2017, 1, 1)
    for i in range(n_orders):
        cid, oid = f"demo-customer-{i}", f"demo-order-{i}"
        state = r.choice(states)
        purchased = first_day + timedelta(days=r.randint(0, 650), hours=r.randint(0, 23))
        estimated = purchased + timedelta(days=r.randint(10, 23))
        delivered = estimated + timedelta(days=r.randint(-12, 7))
        customers.append({"customer_id": cid, "customer_state": state})
        orders.append({
            "order_id": oid, "customer_id": cid, "order_status": "delivered",
            "order_purchase_timestamp": purchased.isoformat(),
            "order_delivered_customer_date": delivered.isoformat(),
            "order_estimated_delivery_date": estimated.isoformat(),
        })
        for j in range(1, r.randint(1, 3) + 1):
            items.append({
                "order_id": oid, "order_item_id": j,
                "product_id": r.choice(products)["product_id"],
                "price": round(r.uniform(18, 450), 2),
                "freight_value": round(r.uniform(5, 32), 2),
            })
        review_score = r.choice([1, 2, 3]) if delivered > estimated else r.choice([3, 4, 4, 5, 5])
        reviews.append({"order_id": oid, "review_score": review_score})
    return {
        "orders": pd.DataFrame(orders),
        "items": pd.DataFrame(items),
        "customers": pd.DataFrame(customers),
        "products": pd.DataFrame(products),
        "translations": pd.DataFrame(
            [{"product_category_name": pt, "product_category_name_english": en}
             for pt, en in categories]
        ),
        "reviews": pd.DataFrame(reviews),
    }
