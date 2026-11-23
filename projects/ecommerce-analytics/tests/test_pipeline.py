import pandas as pd
import pytest

from src.demo import generate_demo
from src.pipeline import build_model, filter_facts, measures


def test_demo_has_correct_grains_and_totals():
    orders, items, quality = build_model(generate_demo(seed=2, n_orders=40))
    assert len(orders) == 40
    assert orders["order_id"].is_unique
    assert not items.duplicated(["order_id", "order_item_id"]).any()
    result = measures(orders, items)
    assert result["orders"] == 40
    assert result["gmv_brl"] == pytest.approx(items["price"].sum())
    assert result["aov_brl"] == pytest.approx(result["gmv_brl"] / 40)
    assert result["on_time_denominator"] == 40
    assert 0 <= result["on_time_rate"] <= 1
    assert quality["source_orders"] == 40


def test_filter_preserves_unique_order_count_and_item_gmv():
    orders, items, _ = build_model(generate_demo(seed=4, n_orders=50))
    category = items["category"].iloc[0]
    d0 = items["order_purchase_timestamp"].min().date()
    d1 = items["order_purchase_timestamp"].max().date()
    chosen_orders, chosen_items = filter_facts(orders, items, (d0, d1), [], [category])
    assert len(chosen_items) > 0
    assert chosen_items["category"].eq(category).all()
    assert measures(chosen_orders, chosen_items)["orders"] == chosen_items["order_id"].nunique()
    assert measures(chosen_orders, chosen_items)["gmv_brl"] == pytest.approx(chosen_items["price"].sum())


def test_multiple_reviews_do_not_multiply_gmv():
    frames = generate_demo(seed=2, n_orders=3)
    first_id = frames["orders"]["order_id"].iloc[0]
    frames["reviews"] = pd.concat(
        [frames["reviews"], pd.DataFrame([{"order_id": first_id, "review_score": 1}])],
        ignore_index=True,
    )
    orders, items, quality = build_model(frames)
    assert len(orders) == 3
    assert len(items) == len(frames["items"])
    assert quality["duplicated_review_order_ids"] == 1


def test_reject_duplicate_order_key():
    frames = generate_demo(seed=2, n_orders=3)
    frames["orders"] = pd.concat([frames["orders"], frames["orders"].iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate key"):
        build_model(frames)


def test_missing_timestamp_is_not_counted_as_late():
    frames = generate_demo(seed=2, n_orders=3)
    frames["orders"].loc[0, "order_delivered_customer_date"] = None
    orders, items, quality = build_model(frames)
    kpis = measures(orders, items)
    assert kpis["on_time_denominator"] == 2
    assert quality["delivered_orders_missing_delivery_or_estimate"] == 1


def test_reject_orphan_customer_counts_quality():
    frames = generate_demo(seed=2, n_orders=3)
    frames["customers"] = frames["customers"].iloc[1:].copy()
    _, _, quality = build_model(frames)
    assert quality["orphan_customers"] == 1
