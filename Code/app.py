"""
IETS Task XXIV — Streamlit entry point.

Run from the project root:
    streamlit run Code/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_CODE_DIR = Path(__file__).parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import streamlit as st
from utils.styles import inject_css

st.set_page_config(
    page_title="IETS Task XXIV — Process Model Database",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

pg = st.navigation([
    st.Page("pages/1_Catalog.py",            title="Catalog",      icon=":material/grid_view:"),
    st.Page("pages/2_Model_Detail.py",       title="Model Detail", icon=":material/description:"),
    st.Page("pages/3_Symbiosis.py",          title="Symbiosis",    icon=":material/hub:"),
    st.Page("pages/4_Multi_Integration.py",  title="Integration",  icon=":material/heat:"),
    st.Page("pages/5_Upload.py",             title="Upload",       icon=":material/upload_file:"),
])
pg.run()
