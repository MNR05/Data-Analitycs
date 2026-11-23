"""Olist CSV ingestion, quality checks, and safe fact-grain joins.

Grains:
- orders: one row / delivered order
- items: one row / order item
Never join payments/reviews directly to order_items without aggregation.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "translations": "product_category_name_translation.csv",
    "reviews": "olist_order_reviews_dataset.csv",
}
REQUIRED = {
    "orders": {"order_id", "customer_id", "order_status", "order_purchase_timestamp",
               "order_delivered_customer_date", "order_estimated_delivery_date"},
    "items": {"order_id", "order_item_id", "product_id", "price", "freight_value"},
    "customers": {"customer_id", "customer_state"},
    "products": {"product_id", "product_category_name"},
    "translations": {"product_category_name", "product_category_name_english"},
    "reviews": {"order_id", "review_score"},
}


def load_olist(raw_dir: str | Path) -> dict[str, pd.DataFrame]:
    folder = Path(raw_dir)
    missing = [file for file in FILES.values() if not (folder / file).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Olist CSVs in {folder}: {', '.join(missing)}")
    return {key: pd.read_csv(folder / filename, low_memory=False)
            for key, filename in FILES.items()}


def load_uploaded(files) -> dict[str, pd.DataFrame]:
    uploads = {file.name: file for file in files}
    missing = [name for name in FILES.values() if name not in uploads]
    if missing:
        raise ValueError("Upload all six files: " + ", ".join(missing))
    for file in uploads.values():
        file.seek(0)
    return {key: pd.read_csv(uploads[filename], low_memory=False)
            for key, filename in FILES.items()}


def _require_columns(frames: dict[str, pd.DataFrame]) -> None:
    for name, columns in REQUIRED.items():
        if name not in frames:
            raise ValueError(f"Missing table: {name}")
        missing = columns - set(frames[name].columns)
        if missing:
            raise ValueError(f"{name}: missing columns {sorted(missing)}")


def _unique(df: pd.DataFrame, columns: list[str], name: str) -> None:
    if df.duplicated(columns).any():
        raise ValueError(f"{name}: duplicate key {columns}; resolve before joining")


def build_model(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Create delivered-order and line-item facts without multiplying revenue."""
    _require_columns(frames)
    orders = frames["orders"].copy()
    items = frames["items"].copy()
    customers = frames["customers"].copy()
    products = frames["products"].copy()
    translation = frames["translations"].copy()
    reviews = frames["reviews"].copy()

    for name, df, cols in [
        ("orders", orders, ["order_id"]),
        ("items", items, ["order_id", "order_item_id"]),
        ("customers", customers, ["customer_id"]),
        ("products", products, ["product_id"]),
        ("translations", translation, ["product_category_name"]),
    ]:
        _unique(df, cols, name)

    quality = {
        "source_orders": int(len(orders)),
        "source_items": int(len(items)),
        "source_reviews": int(len(reviews)),
        "non_delivered_orders_excluded": int((orders["order_status"] != "delivered").sum()),
        "orphan_items": int((~items["order_id"].isin(orders["order_id"])).sum()),
        "orphan_customers": int((~orders["customer_id"].isin(customers["customer_id"])).sum()),
        "missing_item_prices": int(pd.to_numeric(items["price"], errors="coerce").isna().sum()),
        "duplicated_review_order_ids": int(reviews["order_id"].duplicated().sum()),
    }

    # Reviews can have >1 row per order: aggregate before joining to order grain.
    reviews["review_score"] = pd.to_numeric(reviews["review_score"], errors="coerce")
    reviews_one = (reviews.groupby("order_id", as_index=False)["review_score"]
                   .mean())

    for column in ("order_purchase_timestamp", "order_delivered_customer_date",
                   "order_estimated_delivery_date"):
        orders[column] = pd.to_datetime(orders[column], errors="coerce")

    orders = orders.loc[orders["order_status"] == "delivered"].copy()
    orders = orders.dropna(subset=["order_purchase_timestamp"])
    orders = orders.merge(customers[["customer_id", "customer_state"]],
                          on="customer_id", how="left", validate="many_to_one")
    orders = orders.merge(reviews_one, on="order_id", how="left", validate="one_to_one")
    orders["customer_state"] = orders["customer_state"].fillna("UNKNOWN")
    orders["on_time"] = (
        orders["order_delivered_customer_date"].le(orders["order_estimated_delivery_date"])
        .where(orders["order_delivered_customer_date"].notna()
               & orders["order_estimated_delivery_date"].notna())
    )
    orders["delay_days"] = (
        orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"]
    ).dt.total_seconds().div(86400).clip(lower=0)
    quality["delivered_orders_valid_purchase_date"] = int(len(orders))
    quality["delivered_orders_missing_delivery_or_estimate"] = int(orders["on_time"].isna().sum())

    items["price"] = pd.to_numeric(items["price"], errors="coerce")
    items["freight_value"] = pd.to_numeric(items["freight_value"], errors="coerce")
    quality["invalid_item_prices_excluded"] = int((items["price"].isna() | (items["price"] < 0)).sum())
    items = items.loc[items["price"].notna() & (items["price"] >= 0)].copy()

    order_fields = ["order_id", "order_purchase_timestamp", "customer_state", "on_time",
                    "review_score", "delay_days"]
    items = items.merge(orders[order_fields], on="order_id", how="inner", validate="many_to_one")
    items = items.merge(products[["product_id", "product_category_name"]],
                        on="product_id", how="left", validate="many_to_one")
    items = items.merge(translation, on="product_category_name",
                        how="left", validate="many_to_one")
    items["category"] = (items["product_category_name_english"]
                          .fillna(items["product_category_name"])
                          .fillna("Uncategorized"))
    items["purchase_month"] = items["order_purchase_timestamp"].dt.to_period("M").astype(str)
    quality["eligible_order_items"] = int(len(items))
    quality["eligible_gmv_brl"] = float(items["price"].sum())
    return orders, items, quality


def filter_facts(
    orders: pd.DataFrame, items: pd.DataFrame,
    date_range: tuple, states: list[str], categories: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter item grain first; select unique matching orders for order-grain metrics."""
    start, end = [pd.Timestamp(value) for value in date_range]
    mask = items["order_purchase_timestamp"].dt.normalize().between(start, end)
    if states:
        mask &= items["customer_state"].isin(states)
    if categories:
        mask &= items["category"].isin(categories)
    selected_items = items.loc[mask].copy()
    selected_orders = orders.loc[
        orders["order_id"].isin(selected_items["order_id"])
    ].copy()
    return selected_orders, selected_items


def measures(orders: pd.DataFrame, items: pd.DataFrame) -> dict:
    """All KPI denominators and revenue use the same selection."""
    order_count = int(orders["order_id"].nunique())
    gmv = float(items["price"].sum())
    eligible_delivery = orders["on_time"].dropna()
    reviews = orders["review_score"].dropna()
    return {
        "gmv_brl": gmv,
        "orders": order_count,
        "aov_brl": gmv / order_count if order_count else 0.0,
        "on_time_rate": float(eligible_delivery.astype(bool).mean()) if len(eligible_delivery) else None,
        "on_time_denominator": int(len(eligible_delivery)),
        "avg_review": float(reviews.mean()) if len(reviews) else None,
        "review_denominator": int(len(reviews)),
        "late_orders": int((eligible_delivery == False).sum()),  # noqa: E712
    }
