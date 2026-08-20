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
GREEN = "#1E8A4C"
ORANGE = "#E8830C"
YELLOW = "#F4C430"
CHART_SEQUENCE = [BLUE, GREEN, ORANGE, RED, NAVY, YELLOW, "#5A85BE", "#7A8DA6"]

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


def money_item(label: str, raw_value: float, headline: bool = False, sentiment: bool = False, category: str | None = None) -> dict:
    """sentiment=True colors positive values green (profit/margin-type metrics only —
    plain revenue/volume figures should stay neutral, not turn green just for being positive)."""
    return {
        "label": label,
        "value": format_inr(raw_value),
        "headline": headline,
        "negative": raw_value < 0,
        "positive": sentiment and raw_value > 0,
        "category": category,
    }


def _lerp_hex(c1: str, c2: str, t: float) -> str:
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02X}{g:02X}{b:02X}"


def rank_gradient(n: int, dark: str = NAVY, light: str = "#8FB4DE") -> list[str]:
    """n colors from dark (rank 1 / highest) to light (lowest), for leaderboard-style bar charts."""
    if n <= 1:
        return [dark]
    return [_lerp_hex(dark, light, i / (n - 1)) for i in range(n)]


def render_header(title: str) -> None:
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {NAVY}, {BLUE});
            border-bottom: 4px solid {RED};
            border-radius: 10px;
            padding: 18px 24px;
            margin-bottom: 18px;
        ">
            <span style="color: #FFFFFF; font-size: 1.8rem; font-weight: 700;">{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---- top-N customer quick filter --------------------------------------------

def make_top_n_customer_widget(df: pd.DataFrame, all_filters: dict, key_prefix: str, value_col: str,
                                value_label: str, customer_col: str = "SOLD TO PARTY NAME", n: int = 10):
    """Returns (render_fn, session_state_key). render_fn is a zero-arg function (for
    build_sidebar_filters' extra_widgets) that shows a multiselect populated with the actual
    top-N customer names by value_col — recomputed from whatever the OTHER active filters
    currently narrow the data down to. Selecting any of them filters down to just those;
    selecting none leaves the data unrestricted."""
    key = f"{key_prefix}_top_n_customers"

    def render():
        d = df
        for label, col in all_filters.items():
            sel = st.session_state.get(f"{key_prefix}_{label}", [])
            if sel:
                d = d[d[col].isin(sel)]
        top_names = d.groupby(customer_col)[value_col].sum().nlargest(n).index.tolist()
        if key in st.session_state:
            st.session_state[key] = [v for v in st.session_state[key] if v in top_names]
        st.multiselect(f"Top {n} Customers (by {value_label})", top_names, key=key)

    return render, key


# ---- sidebar cross-filtering -------------------------------------------------

def build_sidebar_filters(df: pd.DataFrame, filter_groups: dict, key_prefix: str,
                           default_expanded=("Time", "Transaction"), help_text: dict | None = None,
                           extra_widgets: dict | None = None):
    """Render grouped, cross-filtering multiselects in the sidebar and return the filtered df.

    Each widget's options reflect all OTHER currently active filters (not itself), so choices
    keep narrowing consistently as the user filters. key_prefix keeps this page's widget state
    isolated from other pages sharing the same sidebar.

    extra_widgets: optional {group_name: callable} — the callable is invoked inside that group's
    expander (after its normal filter widgets) to render something extra, e.g. a "Top 10 only" toggle.
    """
    help_text = help_text or {}
    extra_widgets = extra_widgets or {}
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

                if group_name in extra_widgets:
                    extra_widgets[group_name]()

    filtered = df
    for label, col in all_filters.items():
        sel = current_selection(label)
        if sel:
            filtered = filtered[filtered[col].isin(sel)]

    return filtered, all_filters, current_selection


# ---- KPI card grid ------------------------------------------------------------

_KPI_CARD_CSS = f"""
<style>
.kpi-grid {{
    display: grid;
    gap: 16px;
    margin-bottom: 16px;
}}
.kpi-card {{
    position: relative;
    border: 1px solid rgba(4, 21, 98, 0.08);
    border-top: 3px solid {BLUE};
    background: #FFFFFF;
    border-radius: 12px;
    padding: 16px 20px;
    min-width: 0;
    box-shadow: 0 1px 3px rgba(4, 21, 98, 0.07), 0 4px 10px rgba(4, 21, 98, 0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.kpi-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(4, 21, 98, 0.10), 0 8px 20px rgba(4, 21, 98, 0.08);
}}
.kpi-card.headline {{
    grid-column: span 2;
    background: linear-gradient(135deg, {NAVY}, {BLUE});
    border-top: 3px solid {RED};
    box-shadow: 0 4px 14px rgba(4, 21, 98, 0.25);
}}
.kpi-card.headline .kpi-label,
.kpi-card.headline .kpi-value {{
    color: #FFFFFF;
}}
.kpi-card.cat-margin {{
    background: linear-gradient(180deg, rgba(30, 138, 76, 0.07), #FFFFFF 55%);
    border-top: 3px solid {NAVY};
}}
.kpi-card.cat-charge {{
    background: linear-gradient(180deg, rgba(218, 18, 18, 0.05), #FFFFFF 55%);
    border-top: 3px solid {RED};
}}
.kpi-card.cat-warning {{
    background: linear-gradient(180deg, rgba(232, 131, 12, 0.07), #FFFFFF 55%);
    border-top: 3px solid {ORANGE};
}}
.kpi-label {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    color: {BLUE};
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.kpi-label::before {{
    content: "";
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.55;
    flex: none;
}}
.kpi-card.headline .kpi-label::before {{
    background: {RED};
    opacity: 1;
}}
.kpi-value {{
    font-size: 1.6rem;
    font-weight: 700;
    margin-top: 6px;
    line-height: 1.2;
    color: {NAVY};
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.kpi-value.negative {{
    color: {RED};
}}
.kpi-value.positive {{
    color: {GREEN};
}}
.kpi-value.warning {{
    color: {ORANGE};
}}
.kpi-card.headline .kpi-value {{
    font-size: 2.2rem;
}}
@media (max-width: 900px) {{
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr) !important; }}
    .kpi-card.headline {{ grid-column: span 2; }}
}}
</style>
"""


def _kpi_cards_html(items: list[dict]) -> str:
    html_parts = []
    for item in items:
        card_classes = "kpi-card"
        if item.get("headline"):
            card_classes += " headline"
        elif item.get("category"):
            card_classes += f" cat-{item['category']}"

        value_class = ""
        if not item.get("headline"):
            if item.get("negative"):
                value_class = " negative"
            elif item.get("warning"):
                value_class = " warning"
            elif item.get("positive"):
                value_class = " positive"

        html_parts.append(
            f'<div class="{card_classes}">'
            f'<div class="kpi-label">{item["label"]}</div>'
            f'<div class="kpi-value{value_class}">{item["value"]}</div>'
            f'</div>'
        )
    return "".join(html_parts)


def render_kpi_grid(items: list[dict], columns: int = 4) -> None:
    """Auto-flowing grid: items wrap after `columns` per row (a 'headline' item spans 2)."""
    grid = f'<div class="kpi-grid" style="grid-template-columns: repeat({columns}, 1fr);">{_kpi_cards_html(items)}</div>'
    st.markdown(_KPI_CARD_CSS + grid, unsafe_allow_html=True)


def render_kpi_rows(rows: list[list[dict]]) -> None:
    """Explicit row-by-row layout: each row is its own grid, split evenly across its own items."""
    grids = "".join(
        f'<div class="kpi-grid" style="grid-template-columns: repeat({len(row)}, 1fr);">{_kpi_cards_html(row)}</div>'
        for row in rows
    )
    st.markdown(_KPI_CARD_CSS + grids, unsafe_allow_html=True)


def inject_global_css() -> None:
    """Site-wide styling: tooltip contrast, smoother/card-styled sidebar filters, chart cards
    (border + shadow), and colored/carded data tables (the grid reads its own header/cell
    colors from CSS custom properties on .stDataFrameGlideDataEditor, which this overrides)."""
    st.markdown(
        f"""
        <style>
        /* ---- tooltips ---- */
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

        /* ---- smooth transitions everywhere ---- */
        button, [data-baseweb="select"] > div, [data-testid="stExpander"] summary,
        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {{
            transition: all 0.16s ease;
        }}

        /* ---- sidebar filter panel ---- */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF, {GREY});
        }}
        [data-testid="stSidebar"] [data-testid="stExpander"] {{
            background: #FFFFFF;
            border: 1px solid rgba(4, 21, 98, 0.10);
            border-radius: 12px;
            box-shadow: 0 1px 4px rgba(4, 21, 98, 0.06);
            margin-bottom: 10px;
            overflow: hidden;
        }}
        [data-testid="stSidebar"] [data-testid="stExpander"] summary {{
            border-radius: 10px;
        }}
        [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {{
            background: rgba(17, 70, 143, 0.07);
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            border-radius: 8px !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within {{
            border-color: {BLUE} !important;
            box-shadow: 0 0 0 2px rgba(17, 70, 143, 0.15) !important;
        }}

        /* ---- buttons ---- */
        .stButton button, .stDownloadButton button, [data-testid="stSidebar"] button {{
            border-radius: 10px !important;
        }}
        .stButton button:hover, .stDownloadButton button:hover, [data-testid="stSidebar"] button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 3px 10px rgba(4, 21, 98, 0.15);
        }}

        /* ---- charts as cards: border + light shadow ---- */
        [data-testid="stPlotlyChart"] {{
            background: #FFFFFF;
            border: 1px solid rgba(4, 21, 98, 0.10);
            border-radius: 14px;
            box-shadow: 0 2px 6px rgba(4, 21, 98, 0.06), 0 6px 16px rgba(4, 21, 98, 0.05);
            padding: 14px;
            margin-bottom: 8px;
        }}
        [data-testid="stPlotlyChart"]:hover {{
            box-shadow: 0 4px 10px rgba(4, 21, 98, 0.09), 0 10px 22px rgba(4, 21, 98, 0.07);
        }}

        /* ---- tables as cards, with a colored header row ---- */
        [data-testid="stDataFrame"] {{
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 2px 6px rgba(4, 21, 98, 0.06), 0 6px 16px rgba(4, 21, 98, 0.05);
            margin-bottom: 8px;
        }}
        [data-testid="stDataFrameResizable"] {{
            border-radius: 14px !important;
            border: 1px solid rgba(4, 21, 98, 0.10) !important;
        }}
        .stDataFrameGlideDataEditor {{
            --gdg-bg-header: {NAVY} !important;
            --gdg-text-header: #FFFFFF !important;
            --gdg-bg-icon-header: #FFFFFF !important;
            --gdg-fg-icon-header: {NAVY} !important;
            --gdg-bg-header-has-focus: {BLUE} !important;
            --gdg-bg-header-hovered: {BLUE} !important;
            --gdg-accent-color: {BLUE} !important;
            --gdg-accent-fg: #FFFFFF !important;
            --gdg-accent-light: rgba(17, 70, 143, 0.12) !important;
            --gdg-border-color: rgba(4, 21, 98, 0.12) !important;
            --gdg-horizontal-border-color: rgba(4, 21, 98, 0.08) !important;
        }}

        /* ---- custom HTML summary tables (real colored header, unlike st.dataframe's canvas grid) ---- */
        .cpsw-table-wrap {{
            overflow: auto;
            border: 1px solid rgba(4, 21, 98, 0.10);
            border-radius: 14px;
            box-shadow: 0 2px 6px rgba(4, 21, 98, 0.06), 0 6px 16px rgba(4, 21, 98, 0.05);
            margin-bottom: 8px;
        }}
        .cpsw-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
        }}
        .cpsw-table thead th {{
            position: sticky;
            top: 0;
            background: {NAVY};
            color: #FFFFFF;
            text-align: left;
            padding: 10px 14px;
            font-weight: 600;
            white-space: nowrap;
            z-index: 1;
        }}
        .cpsw-table tbody td {{
            padding: 8px 14px;
            color: {NAVY};
            border-bottom: 1px solid rgba(4, 21, 98, 0.06);
            white-space: nowrap;
        }}
        .cpsw-table tbody tr:nth-child(even) {{
            background: rgba(17, 70, 143, 0.03);
        }}
        .cpsw-table tbody tr:hover {{
            background: rgba(17, 70, 143, 0.09);
        }}
        .cpsw-table tbody tr.hl {{
            background: {YELLOW}40 !important;
        }}
        .cpsw-table tbody tr.hl:hover {{
            background: {YELLOW}66 !important;
        }}
        .cpsw-table td.num {{
            text-align: right;
            font-variant-numeric: tabular-nums;
        }}
        .cpsw-table td.neg {{
            color: {RED};
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_table_cell(col: str, v) -> str:
    if isinstance(v, str):
        return v
    if pd.isna(v):
        return ""
    if "%" in col:
        return f"{v:,.1f}%"
    if "(₹ Cr)" in col:
        return f"{v:,.2f}"
    if float(v).is_integer():
        return f"{v:,.0f}"
    return f"{v:,.2f}"


def render_html_table(df: pd.DataFrame, highlight_col: str | None = None, top_n: int = 1, max_height: int = 420) -> None:
    """Fully custom HTML table: real navy header (not fakeable on st.dataframe — its grid is
    canvas-rendered and reads its theme from a JS prop, not CSS, despite exposing CSS variables),
    zebra rows, hover highlight, and the top row(s) by highlight_col tinted yellow.

    Use for small/medium (summary) tables. st.dataframe is still better for very large ones
    (thousands of rows) since this has no virtualization.
    """
    top_idx = set(df[highlight_col].nlargest(top_n).index) if highlight_col and highlight_col in df.columns and len(df) else set()
    numeric_cols = set(df.select_dtypes("number").columns)

    header_html = "".join(f"<th>{c}</th>" for c in df.columns)
    rows_html = []
    for idx, row in df.iterrows():
        cells = []
        for col in df.columns:
            v = row[col]
            classes = []
            if col in numeric_cols:
                classes.append("num")
                if pd.notna(v) and v < 0:
                    classes.append("neg")
            cells.append(f'<td class="{" ".join(classes)}">{_format_table_cell(col, v)}</td>')
        rows_html.append(f'<tr class="{"hl" if idx in top_idx else ""}">{"".join(cells)}</tr>')

    st.markdown(
        f"""
        <div class="cpsw-table-wrap" style="max-height:{max_height}px;">
          <table class="cpsw-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{"".join(rows_html)}</tbody>
          </table>
        </div>
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
