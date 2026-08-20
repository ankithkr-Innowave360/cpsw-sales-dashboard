"""Overview page - quick view built from only the highlighted columns in the source workbook."""

import plotly.express as px
import streamlit as st

from common import (
    BLUE,
    OVERVIEW_ALL_FILTERS,
    OVERVIEW_FILTER_GROUPS,
    OVERVIEW_HEADLINE,
    OVERVIEW_MEASURES,
    RED,
    build_sidebar_filters,
    inject_global_css,
    load_data,
    make_top_n_customer_widget,
    money_item,
    rank_gradient,
    render_header,
    render_html_table,
    render_kpi_rows,
    style_fig,
)

inject_global_css()
df = load_data()

render_header("CPSW Dashboard")

top10_widget, TOP10_KEY = make_top_n_customer_widget(
    df, OVERVIEW_ALL_FILTERS, key_prefix="ov", value_col="BASIC VALUE", value_label="Basic Value"
)

filtered, all_filters, current_selection = build_sidebar_filters(
    df, OVERVIEW_FILTER_GROUPS, key_prefix="ov", extra_widgets={"Customer": top10_widget}
)

top10_selection = st.session_state.get(TOP10_KEY, [])
if top10_selection:
    filtered = filtered[filtered["SOLD TO PARTY NAME"].isin(top10_selection)]

if filtered.empty:
    st.warning("No rows match the current filters.")
    st.stop()

# --- KPI cards: P&L waterfall (MRP -> Gross Sales -> Net Sales -> Gross Profit -> Net Realised) ---

headline_col = OVERVIEW_MEASURES[OVERVIEW_HEADLINE]

mrp_sum = filtered["MRP TOTAL"].sum()
weighted_disc = (
    (filtered["TRADE DISCOUNT %"] * filtered["MRP TOTAL"]).sum() / mrp_sum
    if mrp_sum
    else 0
)

# Gross Sales = Basic Value (MRP net of Trade Discount)
gross_sales = filtered["BASIC VALUE"].sum()
volume_disc = filtered["QUANTITY VALUE DISC"].sum()
cash_disc = filtered["CASH DISCOUNT"].sum()

# Net Sales = Gross Sales - Volume Discount - Cash Discount
# (no separate "TO discount" column exists in this data — per business call, treated as already
# captured in Trade Discount, not a distinct deduction)
net_sales = gross_sales + volume_disc + cash_disc

# COGS = Billing Quantity x Average cost (per-material weighted average cost, joined by Material
# Code; unmatched materials contribute COGS = 0)
cogs_sum = filtered["COGS"].sum()
gross_profit = net_sales - cogs_sum
gross_profit_pct = (gross_profit / net_sales * 100) if net_sales else 0

handling = filtered["HANDLING CHARGE"].sum()
freight = filtered["FREIGHT CHARGE"].sum()
net_realised = gross_profit - handling - freight
net_realised_pct = (net_realised / net_sales * 100) if net_sales else 0

unique_skus = filtered["MATERIAL CODE"].nunique()


def _margin_flags(pct: float) -> dict:
    """Traffic-light tiers for a margin %: healthy above 25%, worth watching 10-25%, thin below 10%."""
    if pct < 10:
        return {"negative": True, "category": "charge"}
    if pct < 25:
        return {"warning": True, "category": "warning"}
    return {"positive": True, "category": "margin"}


gross_profit_flags = _margin_flags(gross_profit_pct)
net_realised_flags = _margin_flags(net_realised_pct)

kpi_rows = [
    [
        money_item("MRP Total", mrp_sum),
        {"label": "Trade Discount %", "value": f"{weighted_disc * 100:,.1f}%", "negative": weighted_disc < 0},
        money_item("Gross Sales", gross_sales),
        {"label": "Unique SKUs Sold", "value": f"{unique_skus:,}", "negative": False},
    ],
    [
        money_item("Gross Sales", gross_sales),
        money_item("Volume Discount", volume_disc, category="charge"),
        money_item("Cash Discount", cash_disc, category="charge"),
        money_item("Net Sales", net_sales),
    ],
    [
        money_item("Net Sales", net_sales),
        money_item("COGS", cogs_sum, category="charge"),
        money_item("Gross Profit", gross_profit, sentiment=True, category="margin"),
        {"label": "Gross Profit %", "value": f"{gross_profit_pct:,.1f}%", **gross_profit_flags},
    ],
    [
        money_item("Gross Profit", gross_profit, sentiment=True, category="margin"),
        money_item("Handling Charge", handling, category="charge"),
        money_item("Freight Charge", freight, category="charge"),
        money_item("Net Realised Amount", net_realised, sentiment=True, category="margin"),
        {"label": "NR %", "value": f"{net_realised_pct:,.1f}%", **net_realised_flags},
    ],
]
render_kpi_rows(kpi_rows)

st.divider()

# --- monthly trend ---

st.subheader(f"{OVERVIEW_HEADLINE} by Month (₹ Cr)")
monthly = (
    filtered.groupby("Month", as_index=False)[headline_col]
    .sum()
    .sort_values("Month")
)
monthly["Month Label"] = monthly["Month"].dt.strftime("%b %Y")
monthly[headline_col] = monthly[headline_col] / 1e7
fig_trend = px.bar(monthly, x="Month Label", y=headline_col, text_auto=".2f")
fig_trend.update_traces(marker_color=BLUE)
style_fig(fig_trend, xaxis_title="", yaxis_title=f"{OVERVIEW_HEADLINE} (₹ Cr)", showlegend=False)
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# --- explore by dimension ---

st.subheader("Explore by dimension")
c1, c2, c3 = st.columns([2, 2, 1])
groupable_labels = [l for l in OVERVIEW_ALL_FILTERS if l != "Month"]
default_group_idx = groupable_labels.index("State") if "State" in groupable_labels else 0
group_label = c1.selectbox("Group by", groupable_labels, index=default_group_idx)
measure_label = c2.selectbox("Measure", list(OVERVIEW_MEASURES.keys()), index=0)
top_n = c3.number_input("Top N", min_value=5, max_value=100, value=15, step=5)

group_col = OVERVIEW_ALL_FILTERS[group_label]
measure_col = OVERVIEW_MEASURES[measure_label]
is_money = measure_label != "Billing Quantity"

summary = filtered.groupby(group_col, as_index=False)[list(OVERVIEW_MEASURES.values())].sum()
summary = summary.sort_values(measure_col, ascending=False)

axis_label = f"{measure_label} (₹ Cr)" if is_money else measure_label
chart_df = summary.head(int(top_n)).sort_values(measure_col).copy()
if is_money:
    chart_df[measure_col] = chart_df[measure_col] / 1e7
gradient = list(reversed(rank_gradient(len(chart_df))))  # chart_df is ascending, so lowest gets the lightest shade
bar_colors = [RED if v < 0 else gradient[i] for i, v in enumerate(chart_df[measure_col])]
fig_bar = px.bar(chart_df, x=measure_col, y=group_col, orientation="h", text_auto=".2f" if is_money else ".2s")
fig_bar.update_traces(marker_color=bar_colors)
style_fig(fig_bar, yaxis_title="", xaxis_title=axis_label, height=max(350, 28 * len(chart_df)))
st.plotly_chart(fig_bar, use_container_width=True)

cr_table = summary.copy()
rename_map = {group_col: group_label}
for label, col in OVERVIEW_MEASURES.items():
    if label == "Billing Quantity":
        rename_map[col] = label
    else:
        cr_table[col] = (cr_table[col] / 1e7).round(4)
        rename_map[col] = f"{label} (₹ Cr)"
display_table = cr_table.rename(columns=rename_map)

render_html_table(display_table)
st.download_button(
    "Download this table as CSV",
    display_table.to_csv(index=False).encode("utf-8"),
    file_name=f"sales_by_{group_label.replace(' ', '_').lower()}.csv",
    mime="text/csv",
)
