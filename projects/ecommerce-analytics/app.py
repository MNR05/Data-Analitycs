"""Streamlit dashboard for the Olist public e-commerce dataset.

Data provenance is always shown. Fictional sample data is explicitly labelled.
Run: streamlit run app.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.demo import generate_demo
from src.pipeline import build_model, filter_facts, load_olist, load_uploaded, measures


st.set_page_config(
    page_title="E-commerce Analytics | Portfolio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
       background: rgba(60,100,150,0.08);
       border: 1px solid rgba(125,155,180,.20);
       border-radius: 14px;
       padding: 16px;
    }
    div.block-container { padding-top: 2.0rem; padding-bottom: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("E-commerce Sales & Operations")
st.caption("Explore revenue, order volumes, product categories and delivery reliability with reproducible Python analytics.")

SOURCE_URL = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
BASE = Path(__file__).resolve().parent
RAW_DIR = BASE / "data" / "raw"

with st.sidebar:
    st.header("Dataset")
    default_mode = "Local Olist CSVs" if all((RAW_DIR / f).is_file() for f in (
        "olist_orders_dataset.csv", "olist_order_items_dataset.csv",
        "olist_customers_dataset.csv", "olist_products_dataset.csv",
        "product_category_name_translation.csv", "olist_order_reviews_dataset.csv",
    )) else "Fictional demo"
    mode = st.radio("Data source", ["Fictional demo", "Local Olist CSVs", "Upload Olist CSVs"],
                    index=["Fictional demo", "Local Olist CSVs", "Upload Olist CSVs"].index(default_mode))
    uploads = []
    if mode == "Upload Olist CSVs":
        uploads = st.file_uploader("Upload all six required CSV files",
                                   type="csv", accept_multiple_files=True)
    st.divider()
    st.markdown("**Definitions**")
    st.caption("GMV = sum of item prices for delivered orders, **excluding freight**. "
               "AOV = GMV / distinct delivered orders within the selection. "
               "Delivery on-time % = orders with actual delivery on or before the estimate / "
               "delivered orders with both delivery timestamps.")
    st.caption("Category filters select orders containing matching items; order-level metrics are "
               "computed once per matching order. GMV includes only matching items. "
               "Category-selected AOV is therefore a category basket-value metric.")

if mode == "Fictional demo":
    st.warning("**FICTIONAL DEMO DATA** — Generated examples, not Olist observations or real business results. "
               "Switch to the public Olist CSVs to analyze actual historical records.")
else:
    st.info(f"**Public Olist dataset** — Historical Brazilian marketplace data. "
            f"[Download from Kaggle]({SOURCE_URL}). Metrics are descriptive, not live operations.")

@st.cache_data(show_spinner="Building validated data model…")
def build_from_directory(location: str):
    return build_model(load_olist(location))


@st.cache_data(show_spinner="Generating fictional demo…")
def build_demo():
    return build_model(generate_demo())


try:
    if mode == "Fictional demo":
        orders, items, quality = build_demo()
    elif mode == "Local Olist CSVs":
        orders, items, quality = build_from_directory(str(RAW_DIR))
    else:
        if not uploads:
            st.info("Upload all six Olist CSV files to start the analysis.")
            st.stop()
        orders, items, quality = build_model(load_uploaded(uploads))
except (ValueError, FileNotFoundError, KeyError, pd.errors.ParserError) as exc:
    st.error(f"Could not build the data model: {exc}")
    st.stop()

if items.empty:
    st.warning("No eligible delivered-order line items in the selected dataset.")
    st.stop()

first = items["order_purchase_timestamp"].min().date()
last = items["order_purchase_timestamp"].max().date()
with st.sidebar:
    st.header("Filters")
    chosen_dates = st.date_input("Purchase dates", (first, last), min_value=first, max_value=last)
    state_options = sorted(items["customer_state"].dropna().astype(str).unique().tolist())
    chosen_states = st.multiselect("Customer state", state_options, default=[])
    category_options = sorted(items["category"].dropna().astype(str).unique().tolist())
    chosen_categories = st.multiselect("Product category", category_options, default=[])

if not isinstance(chosen_dates, tuple) or len(chosen_dates) != 2:
    st.info("Select a start and end date.")
    st.stop()

selected_orders, selected_items = filter_facts(
    orders, items, chosen_dates, chosen_states, chosen_categories
)
kpis = measures(selected_orders, selected_items)

st.subheader("Performance overview")
a, b, c, d = st.columns(4)
a.metric("GMV excluding freight", f"R$ {kpis['gmv_brl']:,.0f}")
b.metric("Delivered orders", f"{kpis['orders']:,}")
c.metric("Basket value / order", f"R$ {kpis['aov_brl']:,.2f}")
d.metric("On-time deliveries", "N/A" if kpis["on_time_rate"] is None else f"{kpis['on_time_rate']:.1%}")
st.caption(f"On-time denominator: {kpis['on_time_denominator']:,} orders with known delivery and estimate. "
           f"Selected items: {len(selected_items):,}. Values reflect all active filters.")

left, right = st.columns([1.4, 1])
with left:
    st.subheader("GMV by purchase month")
    monthly = (selected_items.groupby("purchase_month", as_index=False)
               .agg(gmv_brl=("price", "sum"), items=("order_item_id", "size"))
               .sort_values("purchase_month"))
    if monthly.empty:
        st.info("No transactions match the selection.")
    else:
        fig = px.line(monthly, x="purchase_month", y="gmv_brl",
                      markers=True, labels={"purchase_month": "Month", "gmv_brl": "GMV (R$)"},
                      template="plotly_white")
        fig.update_layout(margin=dict(t=12, b=10, l=10, r=10), height=330,
                          yaxis_tickprefix="R$ ")
        st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Top categories by GMV")
    categories = (selected_items.groupby("category", as_index=False)
                  .agg(gmv_brl=("price", "sum")).sort_values("gmv_brl", ascending=False).head(10))
    if categories.empty:
        st.info("No categories match the selection.")
    else:
        fig = px.bar(categories.sort_values("gmv_brl"), x="gmv_brl", y="category",
                     orientation="h", labels={"gmv_brl": "GMV (R$)", "category": ""},
                     template="plotly_white")
        fig.update_layout(margin=dict(t=12, b=10, l=10, r=10), height=330)
        st.plotly_chart(fig, use_container_width=True)

left, right = st.columns([1, 1])
with left:
    st.subheader("Delivered orders by state")
    state_counts = (selected_orders.groupby("customer_state", as_index=False)
                    .agg(orders=("order_id", "nunique"))
                    .sort_values("orders", ascending=False).head(12))
    if not state_counts.empty:
        fig = px.bar(state_counts, x="customer_state", y="orders", template="plotly_white",
                     labels={"customer_state": "State", "orders": "Delivered orders"})
        fig.update_layout(margin=dict(t=12, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No selected orders.")
with right:
    st.subheader("Reviews and delivery")
    review_view = selected_orders.loc[selected_orders["review_score"].notna()].copy()
    if not review_view.empty:
        review_dist = (review_view.assign(stars=review_view["review_score"].round(0).astype(int))
                       .groupby("stars", as_index=False).agg(orders=("order_id", "nunique")))
        fig = px.bar(review_dist, x="stars", y="orders", template="plotly_white",
                     labels={"stars": "Mean review score, rounded", "orders": "Orders"})
        fig.update_layout(margin=dict(t=12, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No review scores in this selection.")
    score = "N/A" if kpis["avg_review"] is None else f"{kpis['avg_review']:.2f} / 5"
    st.caption(f"Mean per-order review score: {score} (n={kpis['review_denominator']:,}). "
               "Multiple reviews of the same order are averaged before joining.")

with st.expander("Data quality, definitions and provenance", expanded=False):
    st.write(f"Source: **{mode}**. Data is never uploaded to a server outside this Streamlit app "
             "by the included Python pipeline. If deployed, uploaded files are processed by the app host.")
    st.dataframe(pd.DataFrame(
        [{"Check": name.replace("_", " ").capitalize(), "Value": value}
         for name, value in quality.items()]),
        use_container_width=True, hide_index=True,
    )
    st.markdown(
        "**Methodology:** Orders are deduplicated/validated at order grain, reviews are aggregated "
        "to one record per order, and monetary values are computed from order-item prices after "
        "restricting the population to delivered orders. Payment totals are not used. "
        "Missing delivery timestamps are excluded only from the punctuality denominator. "
        "No causal conclusions are implied by comparisons."
    )

st.download_button(
    "Export filtered monthly metrics (CSV)",
    data=monthly.to_csv(index=False).encode("utf-8"),
    file_name="ecommerce_monthly_metrics.csv", mime="text/csv",
    disabled=monthly.empty,
)
st.caption("Portfolio implementation — source code and tests in this repository. "
           "Historical Olist data may include outliers, missing timestamps and known coverage limits.")
