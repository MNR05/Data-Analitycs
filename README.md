# Data Analytics Portfolio

Hands-on analytics projects with **Python, SQL and interactive dashboards**, focused on business questions, transparent metric definitions and reproducible code.

## Featured project

### 📊 [E-commerce Sales & Operations Analytics](./projects/ecommerce-analytics/)

**Stack:** Python · Pandas · PostgreSQL SQL · Plotly · Streamlit · pytest

A full analytics starter built around the public **Brazilian E-Commerce Dataset by Olist**. It explores delivered-order GMV, order volumes, basket value, product categories, customer states, reviews and delivery performance. Core calculations are tested and the dashboard supports filtering and CSV export.

**[→ Run the dashboard locally](./projects/ecommerce-analytics/README.md)** | **[→ Open source app](./projects/ecommerce-analytics/app.py)** | **[→ Read SQL queries](./projects/ecommerce-analytics/sql/analytics.sql)**

> **Data provenance:** The dashboard starts with clearly marked fictional demonstration records if the Olist CSVs have not been supplied. The screenshots and sample charts, if any are added later, must identify their source. **No actual Olist metric results are claimed here.**

## Planned projects

| Project | Analytical focus | Status |
| --- | --- | --- |
| **Event Attendance Analytics** | Registrations, check-ins, conversion and activity demand using *fictional* event data | Planned |
| **Soil Moisture Analytics** | Time-series exploration and robust 24-hour forecasting using a suitable open dataset | Planned |

## Engineering standards

- Document metrics and denominators before visualizing.
- Validate data keys, referential integrity, missingness and join grain.
- Recompute filtered rates instead of averaging summary percentages.
- Use parameterized or safe SQL and never commit secrets or private data.
- Include automated tests and repeatable execution instructions.

Developed as a public engineering portfolio in 2026. No historical authorship or employment affiliation is claimed by the code.
