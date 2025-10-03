
# Sales EDA Interactive Dashboard (Dash + Plotly)

This project contains a ready-to-run interactive dashboard (Dash) to visualize key findings from an Exploratory Data Analysis (EDA).

## Project structure (paths)

```
dashboard_project/
├── app.py                    # Main Dash app
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── data/
    ├── cleaned_sales.csv     # (expected) Put your cleaned dataset here
    └── cleaned_sales_sample.csv  # Sample data included
```

Absolute example paths:
- Linux/macOS: `/home/<you>/dashboard_project/app.py`
- Windows: `C:\Users\<you>\dashboard_project\app.py`

## Step-by-step

1. Clone or copy this folder to your machine, e.g.:
   ```
   mkdir ~/dashboard_project
   cp -r /path/to/dashboard_project/* ~/dashboard_project/
   cd ~/dashboard_project
   ```
2. (Optional but recommended) Create and activate a virtual environment:
   - macOS / Linux:
     ```
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Windows (PowerShell):
     ```
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   Note: the UI uses Bootstrap via `dash-bootstrap-components` for an enhanced layout and styling.
4. Place your cleaned dataset at `data/cleaned_sales.csv`.
   - Expected columns (adapt in code if yours differ): `order_id, order_date, product_id, product_name, category, country, quantity, price, revenue`
   - `order_date` should be parseable by `pandas.to_datetime`.
   - If `revenue` is missing, the app will compute it as `quantity * price`.
   - If you don't have a cleaned CSV, the app will use the included sample `data/cleaned_sales_sample.csv`.
5. Start the dashboard:
   ```
   python app.py
   ```
   Open your browser at `http://127.0.0.1:8050`

UI improvements in this version
- Modern header with gradient and subtitle
- Sidebar with filters and a Reset button
- KPI cards (Total Revenue, Orders, AOV, Unique Products)
- Bootstrap-based responsive layout and custom CSS in `assets/custom.css`

## What this dashboard includes (3-4 key metrics)
- Top 10 products by revenue (bar chart)
- Sales by country (bar chart)
- Revenue over time (monthly time series)
- Hour vs weekday revenue heatmap (to find peak shopping hours)

## How to produce a screencast (optional)
- Use OBS Studio, or Windows Game Bar (Win+G), or macOS QuickTime to record the browser while interacting with the dashboard.

## Next steps / deployment
- Deploy to Render, Heroku, or a VPS by creating a `Procfile` and pushing to the provider.
- Add authentication, caching, and a daily data-refresh pipeline for production use.

## Troubleshooting
- If charts show "No data", adjust the date range or filters.
- If your column names are different, edit `app.py` to match your dataset.

