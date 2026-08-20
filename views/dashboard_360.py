"""360 Sales Dashboard - comprehensive view built from the full column set."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import (
    BLUE,
    CHART_SEQUENCE,
    DASH360_ALL_FILTERS,
    DASH360_FILTER_GROUPS,
    DASH360_FILTER_HELP,
    DASH360_HEADLINE,
    DASH360_MEASURES,
    NAVY,
    RED,
    build_sidebar_filters,
    format_inr,
    inject_global_css,
    load_data,
    make_top_n_customer_widget,
    money_item,
    rank_gradient,
    render_header,
    render_html_table,
    render_kpi_grid,
    style_fig,
)

inject_global_css()
df = load_data()

render_header("CPSW Dashboard")

top10_widget, TOP10_KEY = make_top_n_customer_widget(
    df, DASH360_ALL_FILTERS, key_prefix="d360", value_col="INVOICE VALUE", value_label="Net Sales"
)

filtered, all_filters, current_selection = build_sidebar_filters(
    df, DASH360_FILTER_GROUPS, key_prefix="d360", help_text=DASH360_FILTER_HELP,
    extra_widgets={"Customer": top10_widget},
)

top10_selection = st.session_state.get(TOP10_KEY, [])
if top10_selection:
    filtered = filtered[filtered["SOLD TO PARTY NAME"].isin(top10_selection)]

if filtered.empty:
    st.warning("No rows match the current filters.")
    st.stop()

# --- KPI cards ---

net_sales = filtered["INVOICE VALUE"].sum()
taxable = filtered["TAXABLE VALUE"].sum()
basic = filtered["BASIC VALUE"].sum()
qty = filtered["BILLING QUANTITY"].sum()
orders = filtered["SALES ORDER NO"].nunique()
customers = filtered["SOLD TO PARTY"].nunique()
avg_invoice = net_sales / orders if orders else 0

gross_invoice = filtered.loc[filtered["FLAG"] == "Invoice", "INVOICE VALUE"].sum()
returns_value = filtered.loc[filtered["FLAG"] == "Credit Memo for Returns", "INVOICE VALUE"].sum()
return_rate = (abs(returns_value) / gross_invoice * 100) if gross_invoice else 0

mrp_sum = filtered["MRP TOTAL"].sum()
weighted_disc = (
    (filtered["TRADE DISCOUNT %"] * filtered["MRP TOTAL"]).sum() / mrp_sum if mrp_sum else 0
)

monthly_net = filtered.groupby("Month")["INVOICE VALUE"].sum().sort_index()
mom_growth = None
if len(monthly_net) >= 2 and monthly_net.iloc[-2] != 0:
    mom_growth = (monthly_net.iloc[-1] - monthly_net.iloc[-2]) / abs(monthly_net.iloc[-2]) * 100

state_sales = filtered.groupby("STATE DESCRIPTION")["INVOICE VALUE"].sum()
top_state_name = state_sales.idxmax() if len(state_sales) else "-"
top_state_share = (state_sales.max() / net_sales * 100) if net_sales and len(state_sales) else 0

# Return Rate %: traffic-light tiers — under 10% is healthy, 10-20% is worth watching, above 20% is a problem
if return_rate > 20:
    return_rate_flags = {"negative": True, "category": "charge"}
elif return_rate >= 10:
    return_rate_flags = {"warning": True, "category": "warning"}
else:
    return_rate_flags = {"positive": True, "category": "margin"}

# MoM Growth %: growing is good, a small dip is a caution, a real decline is bad
if mom_growth is None:
    mom_flags = {}
elif mom_growth < -5:
    mom_flags = {"negative": True, "category": "charge"}
elif mom_growth < 0:
    mom_flags = {"warning": True, "category": "warning"}
else:
    mom_flags = {"positive": True, "category": "margin"}

kpi_items = [
    money_item(DASH360_HEADLINE, net_sales, headline=True),
    money_item("Taxable Value", taxable),
    money_item("Basic Value", basic),
    {"label": "Billing Quantity", "value": f"{qty:,.0f}", "negative": False},
    {"label": "Distinct Orders", "value": f"{orders:,}", "negative": False},
    {"label": "Active Customers", "value": f"{customers:,}", "negative": False},
    money_item("Avg Invoice Value", avg_invoice),
    {"label": "Return Rate %", "value": f"{return_rate:,.1f}%", **return_rate_flags},
    {"label": "Trade Discount % (value-weighted)", "value": f"{weighted_disc * 100:,.1f}%", "negative": weighted_disc < 0},
    {
        "label": "MoM Growth %",
        "value": f"{mom_growth:,.1f}%" if mom_growth is not None else "N/A",
        **mom_flags,
    },
    {"label": f"Top State Share ({top_state_name})", "value": f"{top_state_share:,.1f}%", "negative": False},
]
render_kpi_grid(kpi_items)

st.divider()

# --- monthly trend: gross invoices vs returns ---

st.subheader("Monthly Trend — Gross Invoices vs Returns (₹ Cr)")
gross_by_month = (
    filtered[filtered["FLAG"] == "Invoice"].groupby("Month")["INVOICE VALUE"].sum().sort_index()
)
returns_by_month = (
    filtered[filtered["FLAG"] == "Credit Memo for Returns"].groupby("Month")["INVOICE VALUE"].sum().sort_index()
)
all_months = sorted(set(gross_by_month.index) | set(returns_by_month.index))
month_labels = [m.strftime("%b %Y") for m in all_months]

fig_trend = go.Figure()
fig_trend.add_bar(
    x=month_labels, y=[gross_by_month.get(m, 0) / 1e7 for m in all_months], name="Gross Invoices", marker_color=BLUE
)
fig_trend.add_bar(
    x=month_labels, y=[returns_by_month.get(m, 0) / 1e7 for m in all_months], name="Returns", marker_color=RED
)
style_fig(fig_trend, barmode="group", xaxis_title="", yaxis_title="Invoice Value (₹ Cr)", legend_title_text="")
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# --- geography ---

st.subheader("Sales by Geography")
geo_c1, geo_c2 = st.columns(2)

for col_widget, dim_col, title in [
    (geo_c1, "STATE DESCRIPTION", "Top States"),
    (geo_c2, "BRANCH DESCRIPTION", "Top Branches"),
]:
    g = filtered.groupby(dim_col, as_index=False)["INVOICE VALUE"].sum().sort_values("INVOICE VALUE").tail(15)
    g["INVOICE VALUE"] = g["INVOICE VALUE"] / 1e7
    gradient = list(reversed(rank_gradient(len(g))))
    colors = [RED if v < 0 else gradient[i] for i, v in enumerate(g["INVOICE VALUE"])]
    fig = px.bar(g, x="INVOICE VALUE", y=dim_col, orientation="h", text_auto=".2f")
    fig.update_traces(marker_color=colors)
    style_fig(fig, yaxis_title="", xaxis_title="Net Sales (₹ Cr)", height=max(320, 26 * len(g)), title=title)
    col_widget.plotly_chart(fig, use_container_width=True)

st.divider()

# --- customers & materials ---

st.subheader("Top Customers & Materials")
top_c1, top_c2 = st.columns(2)

top_customers = (
    filtered.groupby("SOLD TO PARTY NAME", as_index=False)["INVOICE VALUE"].sum()
    .sort_values("INVOICE VALUE").tail(10)
)
top_customers["INVOICE VALUE"] = top_customers["INVOICE VALUE"] / 1e7
fig_cust = px.bar(top_customers, x="INVOICE VALUE", y="SOLD TO PARTY NAME", orientation="h", text_auto=".2f")
fig_cust.update_traces(marker_color=list(reversed(rank_gradient(len(top_customers)))))
style_fig(fig_cust, yaxis_title="", xaxis_title="Net Sales (₹ Cr)", height=380, title="Top 10 Customers")
top_c1.plotly_chart(fig_cust, use_container_width=True)

top_materials = (
    filtered.groupby("MATERIAL DESCRIPTION", as_index=False)["INVOICE VALUE"].sum()
    .sort_values("INVOICE VALUE").tail(10)
)
top_materials["INVOICE VALUE"] = top_materials["INVOICE VALUE"] / 1e7
fig_mat = px.bar(top_materials, x="INVOICE VALUE", y="MATERIAL DESCRIPTION", orientation="h", text_auto=".2f")
fig_mat.update_traces(marker_color=list(reversed(rank_gradient(len(top_materials)))))
style_fig(fig_mat, yaxis_title="", xaxis_title="Net Sales (₹ Cr)", height=380, title="Top 10 Materials")
top_c2.plotly_chart(fig_mat, use_container_width=True)

st.divider()

# --- product mix & customer mix ---

st.subheader("Product & Customer Mix")
mix_c1, mix_c2, mix_c3 = st.columns([1.4, 1, 1])

MIX_CHART_HEIGHT = 460

mg_tree = (
    filtered.groupby(["MATERIAL GROUP DESCRIPTION", "MG1 DESCRIPTION"], as_index=False)["INVOICE VALUE"].sum()
)
mg_tree = mg_tree[mg_tree["INVOICE VALUE"] > 0]
mg_tree["INVOICE VALUE"] = mg_tree["INVOICE VALUE"] / 1e7
fig_tree = px.treemap(
    mg_tree, path=["MATERIAL GROUP DESCRIPTION", "MG1 DESCRIPTION"], values="INVOICE VALUE",
    color="MATERIAL GROUP DESCRIPTION", color_discrete_sequence=CHART_SEQUENCE,
)
fig_tree.update_traces(texttemplate="%{label}<br>₹%{value:.2f} Cr")
style_fig(fig_tree, title="Sales by Material Group", height=MIX_CHART_HEIGHT, margin=dict(t=50, l=4, r=4, b=4))
mix_c1.plotly_chart(fig_tree, use_container_width=True)

cg_mix = filtered.groupby("CUSTOMER GROUP DESCRIPTION", as_index=False)["INVOICE VALUE"].sum()
cg_mix = cg_mix[cg_mix["INVOICE VALUE"] > 0]
cg_mix["INVOICE VALUE"] = cg_mix["INVOICE VALUE"] / 1e7
fig_cg = px.pie(cg_mix, names="CUSTOMER GROUP DESCRIPTION", values="INVOICE VALUE", hole=0.55, color_discrete_sequence=CHART_SEQUENCE)
fig_cg.update_traces(hovertemplate="%{label}<br>₹%{value:.2f} Cr<br>%{percent}", textposition="inside")
style_fig(
    fig_cg, title="Customer Group Mix", height=MIX_CHART_HEIGHT, margin=dict(t=50, l=20, r=20, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
)
mix_c2.plotly_chart(fig_cg, use_container_width=True)

mkt_mix = filtered.groupby("Market", as_index=False)["INVOICE VALUE"].sum()
mkt_mix = mkt_mix[mkt_mix["INVOICE VALUE"] > 0]
mkt_mix["INVOICE VALUE"] = mkt_mix["INVOICE VALUE"] / 1e7
fig_mkt = px.pie(mkt_mix, names="Market", values="INVOICE VALUE", hole=0.55, color_discrete_sequence=CHART_SEQUENCE)
fig_mkt.update_traces(hovertemplate="%{label}<br>₹%{value:.2f} Cr<br>%{percent}", textposition="inside")
style_fig(
    fig_mkt, title="Market Mix (Developed / Developing)", height=MIX_CHART_HEIGHT, margin=dict(t=50, l=20, r=20, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
)
mix_c3.plotly_chart(fig_mkt, use_container_width=True)

st.divider()

# --- discount waterfall ---

st.subheader("Basic Value → Invoice Value Waterfall")
st.caption(
    "Starts at Basic Value rather than MRP Total: MRP Total stays positive even on returns/cancellations "
    "in the source data while Basic Value nets correctly, so an MRP-based waterfall would show a misleading gap."
)

wf_basic = filtered["BASIC VALUE"].sum()
wf_foc = filtered["FOC DISCOUNT VALUE"].sum()
wf_netfoc = filtered["NET OF FOC"].sum()
wf_qtypf = filtered["QUANTITY VALUE DISC"].sum() + filtered["PIPES AND FITTING DISC"].sum()
wf_b4cd = filtered["VALUE B4 CD"].sum()
wf_cd = filtered["CASH DISCOUNT"].sum()
wf_fr = filtered["FREIGHT CHARGE"].sum()
wf_hc = filtered["HANDLING CHARGE"].sum()
wf_tax = filtered["TAXABLE VALUE"].sum()
wf_cgst = filtered["CGST"].sum()
wf_sgst = filtered["SGST"].sum()
wf_igst = filtered["IGST"].sum()
wf_ro = filtered["ROUNDING OFF"].sum()
wf_inv = filtered["INVOICE VALUE"].sum()

wf_x = [
    "Basic Value", "FOC Discount", "Net of FOC", "Qty + P&F Discount", "Value B4 Cash Disc.",
    "Cash Discount", "Freight Charge", "Handling Charge", "Taxable Value",
    "CGST", "SGST", "IGST", "Rounding Off", "Invoice Value",
]
wf_measure = [
    "absolute", "relative", "total", "relative", "total",
    "relative", "relative", "relative", "total",
    "relative", "relative", "relative", "relative", "total",
]
wf_y_raw = [wf_basic, wf_foc, wf_netfoc, wf_qtypf, wf_b4cd, wf_cd, wf_fr, wf_hc, wf_tax, wf_cgst, wf_sgst, wf_igst, wf_ro, wf_inv]
wf_y = [v / 1e7 for v in wf_y_raw]

fig_wf = go.Figure(
    go.Waterfall(
        x=wf_x,
        measure=wf_measure,
        y=wf_y,
        text=[format_inr(v) for v in wf_y_raw],
        textposition="outside",
        increasing={"marker": {"color": BLUE}},
        decreasing={"marker": {"color": RED}},
        totals={"marker": {"color": NAVY}},
        connector={"line": {"color": "rgba(4,21,98,0.3)"}},
    )
)
style_fig(fig_wf, showlegend=False, margin=dict(t=10), yaxis_title="₹ Cr")
st.plotly_chart(fig_wf, use_container_width=True)

st.divider()

# --- detail tables ---

st.subheader("Detail Tables")
tab_cust, tab_geo, tab_mat, tab_raw = st.tabs(["Customer Summary", "Branch / State Summary", "Material Summary", "Raw Data"])

def weighted_discount(group):
    m = group["MRP TOTAL"].sum()
    return (group["TRADE DISCOUNT %"] * group["MRP TOTAL"]).sum() / m if m else 0

with tab_cust:
    cust_summary = filtered.groupby("SOLD TO PARTY NAME").agg(
        **{
            "Net Sales": ("INVOICE VALUE", "sum"),
            "Taxable Value": ("TAXABLE VALUE", "sum"),
            "Billing Quantity": ("BILLING QUANTITY", "sum"),
            "Orders": ("SALES ORDER NO", "nunique"),
        }
    ).reset_index()
    cust_summary["Avg Discount %"] = (
        filtered.groupby("SOLD TO PARTY NAME").apply(weighted_discount, include_groups=False).values * 100
    )
    cust_summary = cust_summary.sort_values("Net Sales", ascending=False)
    cust_summary["Net Sales"] = (cust_summary["Net Sales"] / 1e7).round(4)
    cust_summary["Taxable Value"] = (cust_summary["Taxable Value"] / 1e7).round(4)
    cust_summary = cust_summary.rename(columns={"Net Sales": "Net Sales (₹ Cr)", "Taxable Value": "Taxable Value (₹ Cr)"})
    render_html_table(cust_summary)
    st.download_button(
        "Download customer summary as CSV", cust_summary.to_csv(index=False).encode("utf-8"),
        file_name="customer_summary.csv", mime="text/csv", key="dl_cust",
    )

with tab_geo:
    geo_summary = filtered.groupby(["STATE DESCRIPTION", "BRANCH DESCRIPTION"]).agg(
        **{
            "Net Sales": ("INVOICE VALUE", "sum"),
            "Taxable Value": ("TAXABLE VALUE", "sum"),
            "Billing Quantity": ("BILLING QUANTITY", "sum"),
            "Customers": ("SOLD TO PARTY", "nunique"),
            "Orders": ("SALES ORDER NO", "nunique"),
        }
    ).reset_index().sort_values("Net Sales", ascending=False)
    geo_summary["Net Sales"] = (geo_summary["Net Sales"] / 1e7).round(4)
    geo_summary["Taxable Value"] = (geo_summary["Taxable Value"] / 1e7).round(4)
    geo_summary = geo_summary.rename(columns={"Net Sales": "Net Sales (₹ Cr)", "Taxable Value": "Taxable Value (₹ Cr)"})
    render_html_table(geo_summary)
    st.download_button(
        "Download branch/state summary as CSV", geo_summary.to_csv(index=False).encode("utf-8"),
        file_name="branch_state_summary.csv", mime="text/csv", key="dl_geo",
    )

with tab_mat:
    mat_summary = filtered.groupby("MATERIAL DESCRIPTION").agg(
        **{
            "Net Sales": ("INVOICE VALUE", "sum"),
            "Billing Quantity": ("BILLING QUANTITY", "sum"),
            "MRP Total": ("MRP TOTAL", "sum"),
        }
    ).reset_index()
    mat_summary["Avg Discount %"] = (
        filtered.groupby("MATERIAL DESCRIPTION").apply(weighted_discount, include_groups=False).values * 100
    )
    mat_summary = mat_summary.sort_values("Net Sales", ascending=False)
    mat_summary["Net Sales"] = (mat_summary["Net Sales"] / 1e7).round(4)
    mat_summary["MRP Total"] = (mat_summary["MRP Total"] / 1e7).round(4)
    mat_summary = mat_summary.rename(columns={"Net Sales": "Net Sales (₹ Cr)", "MRP Total": "MRP Total (₹ Cr)"})
    render_html_table(mat_summary, max_height=500)
    st.download_button(
        "Download material summary as CSV", mat_summary.to_csv(index=False).encode("utf-8"),
        file_name="material_summary.csv", mime="text/csv", key="dl_mat",
    )

with tab_raw:
    raw_cols = [
        "Month", "FLAG", "SOLD TO PARTY NAME", "STATE DESCRIPTION", "BRANCH DESCRIPTION",
        "MATERIAL DESCRIPTION", "MATERIAL GROUP DESCRIPTION", "BILLING QUANTITY",
        "BASIC VALUE", "TAXABLE VALUE", "INVOICE VALUE",
    ]
    raw_view = filtered[raw_cols].sort_values("Month").copy()
    for money_col in ["BASIC VALUE", "TAXABLE VALUE", "INVOICE VALUE"]:
        raw_view[money_col] = (raw_view[money_col] / 1e7).round(4)
    raw_view = raw_view.rename(columns={
        "BASIC VALUE": "BASIC VALUE (₹ Cr)", "TAXABLE VALUE": "TAXABLE VALUE (₹ Cr)", "INVOICE VALUE": "INVOICE VALUE (₹ Cr)",
    })
    st.dataframe(raw_view, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered raw data as CSV", raw_view.to_csv(index=False).encode("utf-8"),
        file_name="filtered_raw_data.csv", mime="text/csv", key="dl_raw",
    )
