# E-commerce Sales & Operations Analytics

A data analytics portfolio application combining **data profiling, reliable joins, metric definitions, SQL and interactive visualizations**.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_SQL-4169E1?logo=postgresql&logoColor=white)

**Source:** [Brazilian E-Commerce Public Dataset by Olist (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

**Status:** Implemented code and tests; public Olist files are **not** included in this repo. Without them, the app uses a prominently labelled **fictional demo**. A live cloud deployment has not been configured.

## Questions this dashboard helps answer

- How does delivered-order merchandise value change over purchase months?
- Which categories contribute most to selected item-level GMV?
- Where are delivered orders concentrated geographically?
- How often do eligible orders arrive by their estimated delivery date?
- What is the distribution of customer review scores?

## Key performance indicators

| KPI | Definition | Notes |
| --- | --- | --- |
| GMV (R$) | Sum of eligible delivered-order item `price` | Excludes freight and payments; gross merchandise value, **not** recognized accounting revenue |
| Delivered orders | Distinct `order_id` with eligible matching items | Uses **order grain**, not item grain |
| Average basket value | Filtered GMV / matching distinct delivered orders | Category selection may include only selected-category items while counting the containing order once |
| On-time delivery % | Delivered orders on/before estimate / orders with both dates | Missing dates excluded from denominator |
| Mean review score | Average per-order review score across reviewed selected orders | Multiple reviews are averaged once before the order-level join |

### Data quality safeguards

1. Enforces unique order, customer, product and item keys.
2. Groups multiple reviews to one order-level score **before joins**.
3. Reports orphan items, orphan customers, invalid item prices and missing dates.
4. Avoids inflation of GMV when orders have multiple items or reviews.
5. Preserves source classifications so fictional demonstrations are not mistaken for observed sales.

## Project layout

```text
ecommerce-analytics/
├── app.py                # Dashboard interface
├── src/
│   ├── pipeline.py       # Grain-safe data preparation and metrics
│   └── demo.py           # Deterministic fictional dataset
├── tests/test_pipeline.py
├── sql/analytics.sql     # PostgreSQL reference queries
├── data/raw/             # Olist data, excluded from version control
└── requirements.txt
```

## Run locally

Requires Python **3.10+**; tested in CI with Python 3.12.

```bash
git clone https://github.com/MNR05/Data-Analitycs.git
cd Data-Analitycs/projects/ecommerce-analytics
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The initial app works with **deterministic synthetic data**. To run it against Olist, download the dataset from Kaggle and copy the **six CSVs** listed in [data/raw/README.md](./data/raw/README.md) to `data/raw/`, then choose **Local Olist CSVs** in the sidebar. Alternatively select **Upload Olist CSVs** and upload all six files in the app.

> Do not upload raw customer datasets to a public GitHub repository, and respect the dataset's terms. Use the sample mode for public demonstrations if licensing or privacy is uncertain.

## Automated tests

```bash
python -m pytest tests -q
```

GitHub Actions runs these tests on each push and pull request. The test suite checks data-grain integrity, monetary aggregation, filters, duplicate reviews, invalid source keys and missing delivery dates.

## SQL

[`sql/analytics.sql`](./sql/analytics.sql) contains reference PostgreSQL queries for monthly GMV, delivery reliability and category performance. The dashboard runs on Pandas from CSV files; the SQL is a separate reference implementation and assumes you have loaded Olist CSVs into tables with original names.

## Deployment

1. Create a Streamlit Community Cloud app pointing to **this repository**.
2. Set its main file to `projects/ecommerce-analytics/app.py`.
3. Supply an appropriate requirements file / dependency configuration for the app root; the included `requirements.txt` lives beside the app.
4. Default to **Fictional demo** unless permitted public records are supplied.
5. Verify filters, denominators, source labelling and export after deploying.

No API credentials, tokens or institutional datasets are required.

## Limitations

- Historical sample covers a finite time window; this is **not** a live commerce system.
- GMV is based on listed item prices, not payment capture, refunds, recognition or net margin.
- On-time figures depend on recorded delivery dates and estimates.
- Customer *states* represent the delivery/customer table's geography, not a comprehensive behavioral segmentation.
- Selection of categories produces item-scoped GMV and order-scoped counts by design; this is disclosed in the interface.
- Correlation between low reviews and delivery lateness is not causal proof.

**Authorship:** Independent portfolio implementation created in 2026, without any historical date manipulation or private organizational information.
