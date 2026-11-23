-- PostgreSQL reference queries for the public Olist CSV schema.
-- The tables below are assumed to have been loaded with their original CSV column names.
-- Not executed automatically by the Streamlit application.

-- 1) Monthly GMV excluding freight, delivered orders only.
-- Note: order_items has one row per order item; count distinct orders.
SELECT DATE_TRUNC('month', o.order_purchase_timestamp::timestamp)::date AS purchase_month,
       COUNT(DISTINCT o.order_id) AS delivered_orders,
       ROUND(SUM(oi.price::numeric), 2) AS gmv_excluding_freight_brl,
       ROUND(SUM(oi.price::numeric) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2)
         AS avg_order_value_brl
FROM olist_orders_dataset o
JOIN olist_order_items_dataset oi ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1 ORDER BY 1;

-- 2) On-time rate at distinct-order grain, not at item grain.
SELECT COUNT(*) FILTER (WHERE o.order_delivered_customer_date IS NOT NULL
                          AND o.order_estimated_delivery_date IS NOT NULL) AS eligible_orders,
       COUNT(*) FILTER (
         WHERE o.order_delivered_customer_date IS NOT NULL
           AND o.order_estimated_delivery_date IS NOT NULL
           AND o.order_delivered_customer_date::timestamp <= o.order_estimated_delivery_date::timestamp
       ) AS on_time_orders
FROM olist_orders_dataset o
WHERE o.order_status = 'delivered';

-- 3) Top categories by delivered-order item GMV.
SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'Uncategorized') AS category,
       COUNT(*) AS line_items,
       ROUND(SUM(oi.price::numeric), 2) AS gmv_excluding_freight_brl
FROM olist_order_items_dataset oi
JOIN olist_orders_dataset o ON o.order_id = oi.order_id
LEFT JOIN olist_products_dataset p ON p.product_id = oi.product_id
LEFT JOIN product_category_name_translation t ON t.product_category_name = p.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY 1 ORDER BY 3 DESC LIMIT 10;
