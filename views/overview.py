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

kpi_items = [
    money_item(OVERVIEW_HEADLINE, filtered[headline_col].sum(), headline=True),
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

st.subheader(f"{OVERVIEW_HEADLINE} by Month")
monthly = (
    filtered.groupby("Month", as_index=False)[headline_col]
    .sum()
    .sort_values("Month")
)
monthly["Month Label"] = monthly["Month"].dt.strftime("%b %Y")
fig_trend = px.bar(monthly, x="Month Label", y=headline_col, text_auto=".2s")
fig_trend.update_traces(marker_color=BLUE)
style_fig(fig_trend, xaxis_title="", yaxis_title=OVERVIEW_HEADLINE, showlegend=False)
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

summary = filtered.groupby(group_col, as_index=False)[list(OVERVIEW_MEASURES.values())].sum()
summary = summary.sort_values(measure_col, ascending=False)

chart_df = summary.head(int(top_n)).sort_values(measure_col)
bar_colors = [RED if v < 0 else BLUE for v in chart_df[measure_col]]
fig_bar = px.bar(chart_df, x=measure_col, y=group_col, orientation="h", text_auto=".2s")
fig_bar.update_traces(marker_color=bar_colors)
style_fig(fig_bar, yaxis_title="", xaxis_title=measure_label, height=max(350, 28 * len(chart_df)))
st.plotly_chart(fig_bar, use_container_width=True)

display_rename = {group_col: group_label, **{c: m for m, c in OVERVIEW_MEASURES.items()}}
display_table = summary.rename(columns=display_rename)

st.dataframe(display_table, use_container_width=True, hide_index=True)
st.download_button(
    "Download this table as CSV",
    display_table.to_csv(index=False).encode("utf-8"),
    file_name=f"sales_by_{group_label.replace(' ', '_').lower()}.csv",
    mime="text/csv",
)
