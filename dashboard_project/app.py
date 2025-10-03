# app.py - Interactive dashboard using Dash + Plotly
# Place your cleaned dataset at data/cleaned_sales.csv (relative to this file).
# This app will fall back to the included sample data if your cleaned file is not present.

import os
import pandas as pd
import numpy as np
from datetime import datetime
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import dash_table
import plotly.express as px
import dash_bootstrap_components as dbc

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data", "cleaned_sales.csv")
SAMPLE_PATH = os.path.join(BASE_DIR, "data", "cleaned_sales_sample.csv")

def load_data():
    if os.path.exists(DATA_PATH):
        print(f"Loading dataset from {DATA_PATH}")
        df = pd.read_csv(DATA_PATH, parse_dates=["order_date"])
    elif os.path.exists(SAMPLE_PATH):
        print(f"No cleaned_sales.csv found. Using sample at {SAMPLE_PATH}")
        df = pd.read_csv(SAMPLE_PATH, parse_dates=["order_date"])
    else:
        raise FileNotFoundError("No dataset found. Put your cleaned CSV at data/cleaned_sales.csv")

    # Basic sanity & normalization (adapt these to your actual column names if needed)
    # Expected columns (case-insensitive): order_id, order_date, product_id, product_name, category,
    # country, quantity, price, revenue
    df.columns = [c.strip() for c in df.columns]
    if "revenue" not in df.columns and {"quantity", "price"}.issubset(df.columns):
        df["revenue"] = df["quantity"] * df["price"]

    # Ensure hour and weekday exist
    if "order_date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["order_date"]):
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["order_hour"] = df["order_date"].dt.hour.fillna(-1).astype(int)
    df["order_weekday"] = df["order_date"].dt.day_name()
    return df.dropna(subset=["order_date"])  # drop rows with missing date

df = load_data()

# Choose default filters
available_countries = sorted(df['country'].dropna().unique().tolist())
available_categories = sorted(df['category'].dropna().unique().tolist()) if "category" in df.columns else []

# Use a Bootstrap theme and the local assets/custom.css for styling
external_scripts = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
]
external_styles = [
    dbc.themes.FLATLY,
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap",
]
app = Dash(__name__, external_stylesheets=external_styles, external_scripts=external_scripts, suppress_callback_exceptions=True)
app.title = "Sales EDA — Advanced Dashboard"

# Header
# Simple, clear header (clean and accessible)
header = html.Div([
    html.H1("Sales EDA — Interactive Dashboard", style={"margin":"6px 0", "fontSize":"24px"}),
    html.Div("Filter and explore the cleaned sales dataset.", style={"color": "#6b7280", "marginBottom": "6px"})
], style={"padding":"12px 0"})

# Controls (sidebar)
controls = html.Div([
    html.H5("Filters"),
    html.Label("Country"),
    dcc.Dropdown(id="country-dropdown", options=[{"label": c, "value": c} for c in available_countries],
                 value=available_countries if len(available_countries) <= 3 else [available_countries[0]],
                 multi=True, placeholder="Select country..."),
    html.Br(),
    html.Label("Category"),
    dcc.Dropdown(id="category-dropdown", options=[{"label": c, "value": c} for c in available_categories],
                 value=[] if available_categories else None,
                 multi=True, placeholder="Select category..."),
    html.Br(),
    html.Label("Date range"),
    dcc.DatePickerRange(
        id="date-picker",
        start_date=df["order_date"].min().date(),
        end_date=df["order_date"].max().date(),
        display_format="YYYY-MM-DD",
    ),
    html.Hr(),
    dbc.Button("Reset Filters", id="reset-filters", color="secondary", size="sm", className="mb-2"),
    dbc.Button("Download CSV", id="export-btn", color="primary", size="sm", className="mb-2", style={"marginLeft":"8px"}),
    dcc.Download(id="download-data"),
    html.Div(className="footer-note", children=["Tip: Hover charts for details"])
], className="sidebar")

# Tooltips
tooltips = html.Div([
    dbc.Tooltip("Select one or more countries to filter the data.", target="country-dropdown", placement="right"),
    dbc.Tooltip("Filter by product category. Leave empty to include all.", target="category-dropdown", placement="right"),
    dbc.Tooltip("Pick a date range to zoom the time-series and heatmap.", target="date-picker", placement="right"),
    dbc.Tooltip("Number of orders/revenue within the selected filters.", target="kpi-revenue", placement="top"),
])

# KPI cards (simple aggregated metrics)
def make_kpi_card(id_val, label):
    # simple KPI card (no icons) for clarity
    return dbc.Card([
        dbc.CardBody([
            html.Div(id=id_val, className="kpi-number"),
            html.Div(label, className="kpi-label")
        ])
    ], className="kpi-card")

kpi_row = dbc.Row([
    dbc.Col(make_kpi_card("kpi-revenue", "Total Revenue"), width=3),
    dbc.Col(make_kpi_card("kpi-orders", "Total Orders"), width=3),
    dbc.Col(make_kpi_card("kpi-aov", "Avg Order Value"), width=3),
    dbc.Col(make_kpi_card("kpi-products", "Unique Products"), width=3),
], className="mb-3")

# Summary small cards (data scientist-friendly)
summary_row = dbc.Row([
    dbc.Col(dbc.Card(dbc.CardBody([html.Div(id="summary-rows", className="kpi-number"), html.Div("Rows", className="kpi-label")])), width=3),
    dbc.Col(dbc.Card(dbc.CardBody([html.Div(id="summary-start", className="kpi-number"), html.Div("Start Date", className="kpi-label")])), width=3),
    dbc.Col(dbc.Card(dbc.CardBody([html.Div(id="summary-end", className="kpi-number"), html.Div("End Date", className="kpi-label")])), width=3),
    dbc.Col(dbc.Card(dbc.CardBody([html.Div(id="summary-countries", className="kpi-number"), html.Div("Countries", className="kpi-label")])), width=3),
], className="mb-3")

# Graph columns
graphs = html.Div([
    dbc.Row([
        dbc.Col(dcc.Graph(id="top-products"), md=6),
        dbc.Col(dcc.Graph(id="sales-by-country"), md=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="revenue-time"), md=6),
        dbc.Col(dcc.Graph(id="hour-heatmap"), md=6),
    ], className="mt-3")
], style={"marginTop": "10px"})

# Data preview controls and table
preview_controls = html.Div([
    html.Div([html.Label("Preview rows"), dcc.Input(id="preview-rows", type="number", value=10, min=1, max=200, step=1, style={"width":"100%"})]),
], style={"marginTop": "12px", "marginBottom": "8px"})

data_table = dash_table.DataTable(
    id='preview-table',
    columns=[],
    data=[],
    page_size=10,
    style_table={'overflowX': 'auto'},
    style_cell={'textAlign': 'left', 'padding': '6px'},
    style_header={'backgroundColor': 'rgba(0,0,0,0.03)', 'fontWeight': '600'},
)

app.layout = dbc.Container([
    header,
    html.Br(),
    dbc.Row([
        dbc.Col(controls, md=3),
        dbc.Col([
            kpi_row,
            summary_row,
            graphs
            , preview_controls, data_table
        ], md=9)
    ], align="start", className="g-3")
    , tooltips
], fluid=True)


@app.callback(
    Output("top-products", "figure"),
    Output("sales-by-country", "figure"),
    Output("revenue-time", "figure"),
    Output("hour-heatmap", "figure"),
    Output("kpi-revenue", "children"),
    Output("kpi-orders", "children"),
    Output("kpi-aov", "children"),
    Output("kpi-products", "children"),
    Output('preview-table', 'columns'),
    Output('preview-table', 'data'),
    Output('summary-rows', 'children'),
    Output('summary-start', 'children'),
    Output('summary-end', 'children'),
    Output('summary-countries', 'children'),
    Input("country-dropdown", "value"),
    Input("category-dropdown", "value"),
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date"),
    State("preview-rows", "value"),
)
def update_charts(selected_countries, selected_categories, start_date, end_date, preview_rows):
    # Normalize inputs to lists
    dff = df.copy()
    if selected_countries:
        if not isinstance(selected_countries, list):
            selected_countries = [selected_countries]
        dff = dff[dff["country"].isin(selected_countries)]
    if selected_categories:
        if not isinstance(selected_categories, list):
            selected_categories = [selected_categories]
        dff = dff[dff["category"].isin(selected_categories)]
    if start_date:
        dff = dff[dff["order_date"] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff["order_date"] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)]

    # Top products by revenue
    top_products = (dff.groupby("product_name")["revenue"].sum().reset_index().sort_values("revenue", ascending=False).head(10))
    fig_top = px.bar(top_products, x="revenue", y="product_name", orientation="h", title="Top 10 Products by Revenue",
                     labels={"revenue": "Revenue", "product_name": "Product"})
    fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, margin={"l":200})

    # Sales by country
    sales_country = dff.groupby("country")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
    fig_country = px.bar(sales_country, x="country", y="revenue", title="Sales by Country",
                         labels={"revenue": "Revenue", "country": "Country"})

    # Revenue over time (monthly)
    time_series = dff.set_index("order_date").resample("M")["revenue"].sum().reset_index()
    if time_series.empty:
        fig_time = px.line(title="Revenue Over Time (monthly) — No data for selected filters")
    else:
        fig_time = px.line(time_series, x="order_date", y="revenue", title="Revenue Over Time (monthly)",
                           labels={"order_date": "Month", "revenue": "Revenue"})

    # Heatmap: hour vs weekday (counts)
    pivot = pd.pivot_table(dff, index="order_hour", columns="order_weekday", values="revenue", aggfunc="sum", fill_value=0)
    # Ensure weekday order
    weekdays = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    pivot = pivot.reindex(columns=[c for c in weekdays if c in pivot.columns])
    if pivot.empty:
        fig_heat = px.imshow([[0]], title="Hourly Heatmap — No data")
    else:
        fig_heat = px.imshow(pivot, labels={"x":"Weekday", "y":"Hour", "color":"Revenue"},
                             x=pivot.columns, y=pivot.index, title="Revenue heatmap: Hour vs Weekday")

    # KPIs
    total_revenue = dff["revenue"].sum()
    total_orders = dff["order_id"].nunique() if "order_id" in dff.columns else len(dff)
    aov = total_revenue / total_orders if total_orders else 0
    unique_products = dff["product_id"].nunique() if "product_id" in dff.columns else dff["product_name"].nunique()

    kpi_rev = f"${total_revenue:,.0f}"
    kpi_ord = f"{int(total_orders):,}"
    kpi_aov = f"${aov:,.2f}"
    kpi_prod = f"{int(unique_products):,}"

    # Wrap KPIs in spans with classes for colorized CSS
    rev_span = html.Span(kpi_rev, className=("kpi-number positive" if total_revenue >= 0 else "kpi-number negative"))
    ord_span = html.Span(kpi_ord, className="kpi-number")
    aov_span = html.Span(kpi_aov, className=("kpi-number positive" if aov >= 0 else "kpi-number negative"))
    prod_span = html.Span(kpi_prod, className="kpi-number")

    # Prepare preview table
    try:
        n_preview = int(preview_rows) if preview_rows else 10
    except Exception:
        n_preview = 10
    preview_df = dff.copy().head(n_preview)
    table_columns = [{'name': c, 'id': c} for c in preview_df.columns]
    table_data = preview_df.to_dict('records')

    # Summary values
    total_rows = len(dff)
    start_dt = dff["order_date"].min().date() if not dff.empty else "-"
    end_dt = dff["order_date"].max().date() if not dff.empty else "-"
    countries_count = dff["country"].nunique()

    return fig_top, fig_country, fig_time, fig_heat, rev_span, ord_span, aov_span, prod_span, table_columns, table_data, f"{total_rows}", str(start_dt), str(end_dt), f"{countries_count}"


# Reset filters
@app.callback(
    Output("country-dropdown", "value"),
    Output("category-dropdown", "value"),
    Output("date-picker", "start_date"),
    Output("date-picker", "end_date"),
    Input("reset-filters", "n_clicks"),
)
def reset_filters(n_clicks):
    # Return defaults when button clicked; if never clicked, do not change (Dash requires a return)
    if not n_clicks:
        # No-op: return current defaults matching initialization
        return (available_countries if len(available_countries) <= 3 else [available_countries[0]],
                [] if available_categories else None,
                df["order_date"].min().date(),
                df["order_date"].max().date())
    return (available_countries if len(available_countries) <= 3 else [available_countries[0]],
            [] if available_categories else None,
            df["order_date"].min().date(),
            df["order_date"].max().date())


# Export filtered data as CSV
@app.callback(
    Output("download-data", "data"),
    Input("export-btn", "n_clicks"),
    State("country-dropdown", "value"),
    State("category-dropdown", "value"),
    State("date-picker", "start_date"),
    State("date-picker", "end_date"),
    prevent_initial_call=True,
)
def export_csv(n_clicks, selected_countries, selected_categories, start_date, end_date):
    if not n_clicks:
        raise PreventUpdate
    dff = df.copy()
    if selected_countries:
        if not isinstance(selected_countries, list):
            selected_countries = [selected_countries]
        dff = dff[dff["country"].isin(selected_countries)]
    if selected_categories:
        if not isinstance(selected_categories, list):
            selected_categories = [selected_categories]
        dff = dff[dff["category"].isin(selected_categories)]
    if start_date:
        dff = dff[dff["order_date"] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff["order_date"] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)]

    return dcc.send_data_frame(dff.to_csv, "filtered_sales.csv", index=False)

if __name__ == "__main__":
    app.run(debug=True, port=8050)

