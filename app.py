"""
CPSW Sales Dashboard
Run with:  streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="CPSW Sales Dashboard", layout="wide")

overview_page = st.Page("views/overview.py", title="Overview", icon="📌", default=True)
dashboard_360_page = st.Page("views/dashboard_360.py", title="360 Sales Dashboard", icon="🧭")

nav = st.navigation([overview_page, dashboard_360_page], position="sidebar")
nav.run()
