"""Overview page - quick view built from only the highlighted columns in the source workbook."""

import plotly.express as px
import streamlit as st

from common import (
    BLUE,
    DATA_FILE,
    OVERVIEW_ALL_FILTERS,
    OVERVIEW_FILTER_GROUPS,
    OVERVIEW_HEADLINE,
    OVERVIEW_MEASURES,
    RED,
    SHEET_NAME,
    build_sidebar_filters,
    format_inr,
    inject_global_css,
    load_data,
    money_item,
    render_kpi_grid,
    style_fig,
)

inject_global_css()
df = load_data()

st.title("CPSW Sales Dashboard — Overview")
st.caption(f"Source: {DATA_FILE.name} | Sheet: {SHEET_NAME} | {len(df):,} transaction lines | highlighted columns only")

filtered, all_filters, current_selection = build_sidebar_filters(
    df, OVERVIEW_FILTER_GROUPS, key_prefix="ov"
)

if filtered.empty:
    st.warning("No rows match the current filters.")
    st.stop()

# --- KPI cards ---

headline_col = OVERVIEW_MEASURES[OVERVIEW_HEADLINE]

mrp_sum = filtered["MRP TOTAL"].sum()
weighted_disc = (
    (filtered["TRADE DISCOUNT %"] * filtered["MRP TOTAL"]).sum() / mrp_sum
    if mrp_sum
    else 0
)

# Gross/Net Value: COGS = Billing Quantity x Average cost (per-material weighted average cost,
# joined by Material Code; unmatched materials contribute COGS = 0)
basic_sum = filtered["BASIC VALUE"].sum()
taxable_sum = filtered["TAXABLE VALUE"].sum()
cogs_sum = filtered["COGS"].sum()

gross_value = basic_sum - cogs_sum
gross_pct = (gross_value / basic_sum * 100) if basic_sum else 0

net_value = taxable_sum - cogs_sum
net_pct = (net_value / taxable_sum * 100) if taxable_sum else 0

kpi_items = [
    money_item(OVERVIEW_HEADLINE, filtered[headline_col].sum(), headline=True),
    money_item("Gross Value", gross_value),
    {"label": "Gross %", "value": f"{gross_pct:,.1f}%", "negative": gross_pct < 0},
    money_item("Net Value", net_value),
    {"label": "Net %", "value": f"{net_pct:,.1f}%", "negative": net_pct < 0},
    money_item("Taxable Value", filtered[OVERVIEW_MEASURES["Taxable Value"]].sum()),
    money_item("Value Before Cash Discount", filtered[OVERVIEW_MEASURES["Value Before Cash Discount"]].sum()),
    money_item("MRP Total", filtered[OVERVIEW_MEASURES["MRP Total"]].sum()),
    money_item("Cash Discount", filtered[OVERVIEW_MEASURES["Cash Discount"]].sum()),
    money_item("Freight Charge", filtered[OVERVIEW_MEASURES["Freight Charge"]].sum()),
    money_item("Handling Charge", filtered[OVERVIEW_MEASURES["Handling Charge"]].sum()),
    money_item("Quantity Value Discount", filtered[OVERVIEW_MEASURES["Quantity Value Discount"]].sum()),
    {"label": "Billing Quantity", "value": f"{filtered[OVERVIEW_MEASURES['Billing Quantity']].sum():,.0f}", "negative": False},
    {"label": "Transaction Lines", "value": f"{len(filtered):,}", "negative": False},
    {"label": "Trade Discount % (value-weighted)", "value": f"{weighted_disc * 100:,.1f}%", "negative": weighted_disc < 0},
]
render_kpi_grid(kpi_items)

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
bar_colors = [RED if v < 0 else BLUE for v in chart_df[measure_col]]
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

st.dataframe(display_table, use_container_width=True, hide_index=True)
st.download_button(
    "Download this table as CSV",
    display_table.to_csv(index=False).encode("utf-8"),
    file_name=f"sales_by_{group_label.replace(' ', '_').lower()}.csv",
    mime="text/csv",
)
