"""Shared config, data loading, and UI helpers for the CPSW Sales Dashboard pages."""

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_FILE = Path(__file__).parent / "Ankith - Sales - Copy.xlsx"
SHEET_NAME = "Base - DS"
COST_SHEET_NAME = "Weighted average cost"

# ---- brand palette ----------------------------------------------------------

NAVY = "#041562"
BLUE = "#11468F"
RED = "#DA1212"
GREY = "#EEEEEE"
CHART_SEQUENCE = [BLUE, NAVY, RED, "#5A85BE", "#8C1F1F", "#7A8DA6"]

# ---- Overview page: highlighted columns only (per source workbook) ----------

OVERVIEW_FILTER_GROUPS = {
    "Time": {"Month": "Month"},
    "Transaction": {
        "Transaction Type": "FLAG",
        "MIS Category": "MIS Category",
    },
    "Geography": {
        "State": "STATE DESCRIPTION",
        "Branch": "BRANCH DESCRIPTION",
        "City": "CITY DESCRIPTION",
        "Cluster": "CLUSTER DESCRIPTION",
        "Zone": "ZONE DESCRIPTION",
        "Territory": "TERRITORY DESCRIPTION",
    },
    "Customer": {
        "Customer": "SOLD TO PARTY NAME",
        "Customer Group": "CUSTOMER GROUP DESCRIPTION",
        "CG1 (Dev Status)": "CG1 DESCRIPTION",
        "Distribution Channel": "DISTRIBUTION CHANNEL DESCRIPTION",
    },
    "Product": {
        "Material": "MATERIAL DESCRIPTION",
        "Material Group": "MATERIAL GROUP DESCRIPTION",
        "MG1": "MG1 DESCRIPTION",
        "MG2": "MG2 DESCRIPTION",
        "MG3": "MG3 DESCRIPTION",
        "MG4": "MG4 DESCRIPTION",
    },
}
OVERVIEW_ALL_FILTERS = {label: col for group in OVERVIEW_FILTER_GROUPS.values() for label, col in group.items()}

OVERVIEW_MEASURES = {
    "Basic Value": "BASIC VALUE",
    "Taxable Value": "TAXABLE VALUE",
    "Value Before Cash Discount": "VALUE B4 CD",
    "MRP Total": "MRP TOTAL",
    "Cash Discount": "CASH DISCOUNT",
    "Freight Charge": "FREIGHT CHARGE",
    "Handling Charge": "HANDLING CHARGE",
    "Quantity Value Discount": "QUANTITY VALUE DISC",
    "Billing Quantity": "BILLING QUANTITY",
}
OVERVIEW_HEADLINE = "Basic Value"

# ---- 360 Sales Dashboard page: full column set -------------------------------

DASH360_FILTER_GROUPS = {
    "Time": {"Month": "Month"},
    "Transaction": {
        "Transaction Type": "FLAG",
        "MIS Category": "MIS Category",
    },
    "Geography": {
        "State": "STATE DESCRIPTION",
        "Branch": "BRANCH DESCRIPTION",
        "City": "CITY DESCRIPTION",
        "Cluster": "CLUSTER DESCRIPTION",
        "Zone": "ZONE DESCRIPTION",
        "Territory": "TERRITORY DESCRIPTION",
    },
    "Customer": {
        "Customer": "SOLD TO PARTY NAME",
        "Customer Group": "CUSTOMER GROUP DESCRIPTION",
        "Customer Type": "Customer Type",
        "Market": "Market",
        "CG1 (Dev Status)": "CG1 DESCRIPTION",
        "Distribution Channel": "DISTRIBUTION CHANNEL DESCRIPTION",
    },
    "Product": {
        "Material": "MATERIAL DESCRIPTION",
        "Material Group": "MATERIAL GROUP DESCRIPTION",
        "MG1": "MG1 DESCRIPTION",
        "MG2": "MG2 DESCRIPTION",
        "MG3": "MG3 DESCRIPTION",
        "MG4": "MG4 DESCRIPTION",
    },
}
DASH360_ALL_FILTERS = {label: col for group in DASH360_FILTER_GROUPS.values() for label, col in group.items()}

DASH360_FILTER_HELP = {
    "Customer Type": "Source data mixes 'DB'/'DD' abbreviations with 'DISTRIBUTOR'/'DIRECT DEALER' labels "
    "inconsistently — shown as-is, cross-check against Customer Group if precision matters.",
}

DASH360_MEASURES = {
    "Net Sales (Invoice Value)": "INVOICE VALUE",
    "Taxable Value": "TAXABLE VALUE",
    "Basic Value": "BASIC VALUE",
    "MRP Total": "MRP TOTAL",
    "Cash Discount": "CASH DISCOUNT",
    "Freight Charge": "FREIGHT CHARGE",
    "Handling Charge": "HANDLING CHARGE",
    "Billing Quantity": "BILLING QUANTITY",
}
DASH360_HEADLINE = "Net Sales (Invoice Value)"

FULL_COLUMNS = [
    "Month", "FLAG", "MIS Category",
    "SALES ORDER NO",
    "SOLD TO PARTY", "SOLD TO PARTY NAME",
    "TERRITORY DESCRIPTION", "ZONE DESCRIPTION", "CLUSTER DESCRIPTION",
    "CITY DESCRIPTION", "BRANCH DESCRIPTION", "STATE DESCRIPTION",
    "CUSTOMER GROUP DESCRIPTION", "CG1 DESCRIPTION", "DISTRIBUTION CHANNEL DESCRIPTION",
    "Customer Type", "Market",
    "MATERIAL CODE", "MATERIAL DESCRIPTION", "MATERIAL GROUP DESCRIPTION",
    "MG1 DESCRIPTION", "MG2 DESCRIPTION", "MG3 DESCRIPTION", "MG4 DESCRIPTION",
    "BILLING QUANTITY", "MRP TOTAL", "TRADE DISCOUNT %", "TRADE DISCOUNT", "BASIC VALUE",
    "FOC DISCOUNT VALUE", "NET OF FOC", "QUANTITY VALUE DISC", "PIPES AND FITTING DISC",
    "VALUE B4 CD", "CASH DISCOUNT", "FREIGHT CHARGE", "HANDLING CHARGE", "TAXABLE VALUE",
    "CGST", "SGST", "IGST", "ROUNDING OFF", "INVOICE VALUE",
]

_NUMERIC_COLS = [
    "BILLING QUANTITY", "MRP TOTAL", "TRADE DISCOUNT", "BASIC VALUE",
    "FOC DISCOUNT VALUE", "NET OF FOC", "QUANTITY VALUE DISC", "PIPES AND FITTING DISC",
    "VALUE B4 CD", "CASH DISCOUNT", "FREIGHT CHARGE", "HANDLING CHARGE", "TAXABLE VALUE",
    "CGST", "SGST", "IGST", "ROUNDING OFF", "INVOICE VALUE",
]


# ---- data loading -----------------------------------------------------------

@st.cache_data(show_spinner="Loading sales data...")
def load_data() -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME, usecols=FULL_COLUMNS)

    df["Month"] = pd.to_datetime(df["Month"])

    # both have inconsistent casing in the source, e.g. "Chrome Plated" vs "CHROME PLATED"
    df["MIS Category"] = df["MIS Category"].astype(str).str.strip().str.title()
    df["Market"] = df["Market"].astype(str).str.strip().str.title()

    for col in df.columns:
        if col != "Month" and df[col].dtype == object:
            df[col] = df[col].fillna("(Blank)")

    for col in _NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # some rows store this as text, e.g. "-45.00%", instead of a numeric fraction like -0.45
    trade_disc = df["TRADE DISCOUNT %"].astype(str).str.rstrip("%")
    trade_disc = pd.to_numeric(trade_disc, errors="coerce")
    is_percent_string = df["TRADE DISCOUNT %"].astype(str).str.contains("%")
    trade_disc = trade_disc.where(~is_percent_string, trade_disc / 100)
    df["TRADE DISCOUNT %"] = trade_disc.fillna(0)

    # weighted-average cost per material, for COGS / Gross & Net Value
    cost = pd.read_excel(DATA_FILE, sheet_name=COST_SHEET_NAME, usecols=["Material code", "Average cost"])
    cost = cost.dropna(subset=["Material code"]).drop_duplicates(subset=["Material code"], keep="last")
    df = df.merge(cost, left_on="MATERIAL CODE", right_on="Material code", how="left")
    df["Average cost"] = pd.to_numeric(df["Average cost"], errors="coerce").fillna(0)
    # unmatched material codes (no row in the cost sheet) get COGS = 0, per business decision
    df["COGS"] = df["BILLING QUANTITY"] * df["Average cost"]

    return df


def format_inr(value: float) -> str:
    """Format a number in Crore, always — e.g. -₹0.0032 Cr rather than switching units for small values."""
    sign = "-" if value < 0 else ""
    cr = abs(value) / 1e7
    if 0 < cr < 1:
        return f"{sign}₹{cr:,.4f} Cr"
    return f"{sign}₹{cr:,.2f} Cr"


def money_item(label: str, raw_value: float, headline: bool = False) -> dict:
    return {"label": label, "value": format_inr(raw_value), "headline": headline, "negative": raw_value < 0}


# ---- sidebar cross-filtering -------------------------------------------------

def build_sidebar_filters(df: pd.DataFrame, filter_groups: dict, key_prefix: str,
                           default_expanded=("Time", "Transaction"), help_text: dict | None = None):
    """Render grouped, cross-filtering multiselects in the sidebar and return the filtered df.

    Each widget's options reflect all OTHER currently active filters (not itself), so choices
    keep narrowing consistently as the user filters. key_prefix keeps this page's widget state
    isolated from other pages sharing the same sidebar.
    """
    help_text = help_text or {}
    all_filters = {label: col for group in filter_groups.values() for label, col in group.items()}

    def key_for(label: str) -> str:
        return f"{key_prefix}_{label}"

    def current_selection(label: str):
        return st.session_state.get(key_for(label), [])

    def filtered_except(label: str) -> pd.DataFrame:
        d = df
        for lbl, col in all_filters.items():
            if lbl == label:
                continue
            sel = current_selection(lbl)
            if sel:
                d = d[d[col].isin(sel)]
        return d

    with st.sidebar:
        st.header("Filters")

        if st.button("Reset all filters", use_container_width=True, key=f"{key_prefix}_reset"):
            for label in all_filters:
                st.session_state.pop(key_for(label), None)
            st.rerun()

        for group_name, group in filter_groups.items():
            with st.expander(group_name, expanded=(group_name in default_expanded)):
                for label, col in group.items():
                    key = key_for(label)
                    options = sorted(filtered_except(label)[col].dropna().unique().tolist())
                    # prune stale selections before instantiating the widget, so a narrowed
                    # option list never conflicts with a previously chosen value
                    if key in st.session_state:
                        st.session_state[key] = [v for v in st.session_state[key] if v in options]
                    widget_kwargs = {"key": key}
                    if label in help_text:
                        widget_kwargs["help"] = help_text[label]
                    if label == "Month":
                        st.multiselect(label, options, format_func=lambda d: d.strftime("%b %Y"), **widget_kwargs)
                    else:
                        st.multiselect(label, options, **widget_kwargs)

    filtered = df
    for label, col in all_filters.items():
        sel = current_selection(label)
        if sel:
            filtered = filtered[filtered[col].isin(sel)]

    return filtered, all_filters, current_selection


# ---- KPI card grid ------------------------------------------------------------

def render_kpi_grid(items: list[dict], columns: int = 4) -> None:
    css = f"""
    <style>
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat({columns}, 1fr);
        gap: 14px;
        margin-bottom: 8px;
    }}
    .kpi-card {{
        border: 1px solid rgba(4, 21, 98, 0.14);
        border-top: 3px solid {BLUE};
        background: {GREY};
        border-radius: 10px;
        padding: 14px 18px;
        min-width: 0;
    }}
    .kpi-card.headline {{
        grid-column: span 2;
        background: linear-gradient(135deg, {NAVY}, {BLUE});
        border-top: 3px solid {RED};
    }}
    .kpi-card.headline .kpi-label,
    .kpi-card.headline .kpi-value {{
        color: #FFFFFF;
    }}
    .kpi-label {{
        font-size: 0.78rem;
        color: {BLUE};
        opacity: 0.85;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .kpi-value {{
        font-size: 1.55rem;
        font-weight: 700;
        margin-top: 4px;
        line-height: 1.2;
        color: {NAVY};
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .kpi-value.negative {{
        color: {RED};
    }}
    .kpi-card.headline .kpi-value {{
        font-size: 2.1rem;
    }}
    @media (max-width: 900px) {{
        .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
        .kpi-card.headline {{ grid-column: span 2; }}
    }}
    </style>
    """
    cards_html = "".join(
        f'<div class="kpi-card{" headline" if item.get("headline") else ""}">'
        f'<div class="kpi-label">{item["label"]}</div>'
        f'<div class="kpi-value{" negative" if item.get("negative") and not item.get("headline") else ""}">{item["value"]}</div>'
        f'</div>'
        for item in items
    )
    st.markdown(css + f'<div class="kpi-grid">{cards_html}</div>', unsafe_allow_html=True)


def inject_global_css() -> None:
    """High-contrast styling for Streamlit's native help (?) tooltips, which otherwise render
    with a transparent background and are hard to read against whatever sits behind them."""
    st.markdown(
        f"""
        <style>
        div[data-baseweb="tooltip"] [data-testid="stTooltipContent"] {{
            background: {NAVY} !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            box-shadow: 0 4px 14px rgba(4, 21, 98, 0.35) !important;
        }}
        div[data-baseweb="tooltip"] [data-testid="stTooltipContent"] * {{
            color: #FFFFFF !important;
        }}
        [data-testid="stTooltipIcon"] svg {{
            stroke: {BLUE} !important;
            stroke-opacity: 1 !important;
            opacity: 1 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_fig(fig, **layout_kwargs):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color=NAVY,
        hoverlabel=dict(bgcolor=NAVY, font_color="#FFFFFF", font_size=13, bordercolor=BLUE),
        **layout_kwargs,
    )
    return fig
