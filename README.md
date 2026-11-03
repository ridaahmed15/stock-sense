# StockSense AI — Predictive Inventory Intelligence

A modular Streamlit SaaS-style inventory analytics prototype for small and medium-sized businesses. It includes a local SQLite data store, sales forecasting, replenishment planning, stock risk signals, slow/dead-stock analysis, product profitability, and downloadable PDF/CSV reports.

## Features

- Executive dashboard with inventory, sales, capital-at-risk, and stock-risk KPIs.
- CSV/Excel upload with required-column validation and SQLite persistence.
- Random Forest demand forecasting using 1/7/14-day sales lags and calendar features.
- Reorder recommendations using average demand, supplier lead time, target coverage, and safety stock.
- Low-stock / stockout risk flags based on on-hand quantity, reorder point, days of cover, and lead time.
- Slow-moving and dead-stock classification.
- **Cash trapped in inventory** estimate with SKU-level supporting calculations.
- Product revenue, gross profit, and margin estimates.
- Interactive Plotly charts, filters, sliders, CSS motion effects, and a dark premium visual theme.
- Downloadable PDF management report and CSV exports.
- Realistic sample datasets included in `data/`.

## Quick start

Recommended: Python 3.10–3.12.

```bash
# 1. Extract the ZIP and open a terminal in the StockSense_AI folder
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens in your browser (usually `http://localhost:8501`). No API key is required; all analytics run locally. `.env.example` is included for a future optional LLM integration, but no external AI service is called by this version.

## Project structure

```text
StockSense_AI/
├── app.py                 # Streamlit UI and navigation
├── analytics.py           # Validation, metrics, forecasting, reorder logic
├── database.py            # SQLite persistence and seeding
├── reports.py             # PDF report generation
├── requirements.txt
├── .env.example
├── README.md
├── data/
│   ├── products.csv
│   ├── sales.csv
│   ├── inventory.csv
│   └── suppliers.csv
└── assets/
    └── stocksense-mark.svg
```

## Upload formats and required columns

- **sales**: `date`, `product_id`, `units_sold`; optional `revenue`.
- **products**: `product_id`, `product_name`, `category`, `supplier`, `selling_price`, `unit_cost`, `reorder_point`, `lead_time_days`.
- **inventory**: `product_id`, `on_hand`; optional `last_restock_date`, `inventory_value`.
- **suppliers** (optional): `supplier`, `avg_lead_time_days`, `on_time_rate`, `contact`.

CSV and `.xlsx` are supported. Dates must be parseable. Product IDs should match across datasets.

## Calculation notes

- **Average daily demand** = units sold in trailing 90 days ÷ 90.
- **Days of cover** = current on-hand units ÷ average daily demand.
- **Reorder quantity** = `max(0, avg_daily_demand × (target coverage days + safety buffer days + lead time days) − on_hand)`.
- **Cash trapped** = `on_hand × unit_cost` for products with average demand below 0.75 units/day or no recorded sales in the available history.
- **Gross profit estimate** = recorded revenue − units sold × current unit cost.

These are operational estimates, not guaranteed outcomes. Cost changes, returns, stockouts, promotions, and future disruptions are not inferred unless represented in uploaded data. The forecast error band is indicative and is not a formal confidence interval.

## Testing checklist

1. Start the app and confirm the overview loads with sample data.
2. Change category/supplier filters and analysis-window slider.
3. Select a SKU on Demand Forecast and download the forecast CSV.
4. Change reorder coverage/safety sliders and download the purchase plan.
5. Inspect Cash Trapped product-level values and export CSV.
6. Upload a valid CSV/XLSX dataset through Data Studio.
7. Download the PDF report from Reports.

## Important

This is a functional local prototype, not a hosted multi-tenant production SaaS. Before commercial deployment, add authentication/roles, tenant isolation, audit logs, automated backups, secure secret management, migrations, tests, and deployment hardening.
"# stock-sense" 
"# stock-sense" 
