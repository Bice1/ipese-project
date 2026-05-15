"""
IETS Task XXIV — Streamlit entry point.

Redirects immediately to the Catalog page.

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

st.set_page_config(
    page_title="IETS Task XXIV — Process Model Database",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.switch_page("pages/1_Catalog.py")
