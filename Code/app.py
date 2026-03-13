"""
IETS Task XXIV — Streamlit app entry point.

Loads all models once, stores them in st.session_state, injects global CSS,
and renders the home/landing page.

Run from the project root:
    streamlit run Code/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure Code/ is on the path so all package imports resolve
_CODE_DIR = Path(__file__).parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import streamlit as st

from utils.constants import DATA_DIR
from utils.loader import load_all_models

# ---------------------------------------------------------------------------
# Page configuration  (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="IETS Task XXIV — Process Model Database",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* ---- Base typography ---- */
    html, body, [class*="css"] {
        font-family: 'Arial', 'Helvetica Neue', sans-serif;
    }

    /* ---- Main container ---- */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background-color: #F8F9FB;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }

    /* ---- Metric tiles ---- */
    [data-testid="stMetric"] {
        background-color: #F5F7FA;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #E8EBF0;
    }
    [data-testid="stMetricLabel"] {
        font-size: 12px;
        color: #666666;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    [data-testid="stMetricValue"] {
        font-size: 20px;
        font-weight: 600;
        color: #1A1A1A;
    }

    /* ---- Tabs ---- */
    [data-testid="stTabs"] [role="tab"] {
        font-weight: 500;
        color: #555555;
        padding: 8px 18px;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #1A73E8;
        border-bottom: 2px solid #1A73E8;
    }

    /* ---- DataFrame ---- */
    [data-testid="stDataFrame"] {
        border-radius: 6px;
        overflow: hidden;
    }

    /* ---- Section headers ---- */
    h2 {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1A1A1A;
        margin-top: 1.5rem;
    }
    h3 {
        font-size: 1rem;
        font-weight: 600;
        color: #333333;
    }

    /* ---- Dividers ---- */
    hr {
        border: none;
        border-top: 1px solid #E8EBF0;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state — load models once
# ---------------------------------------------------------------------------

if "models" not in st.session_state:
    with st.spinner("Loading model database ..."):
        st.session_state["models"] = load_all_models(DATA_DIR)

if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = None

# ---------------------------------------------------------------------------
# Landing page content
# ---------------------------------------------------------------------------

models: dict = st.session_state["models"]
n_models = len(models)

st.title("IETS Task XXIV — Industrial Process Model Database")
st.caption("IEA Industrial Energy Technology and Systems — Subtask 1")

st.markdown(
    """
This tool provides access to a curated database of industrial process models
developed under IEA IETS Task XXIV. Each model documents the energy flows,
connectors, and equipment of an industrial site or process unit, structured
to support decarbonisation analysis and industrial symbiosis studies.

Use the sidebar navigation to explore the catalog, inspect individual models,
or analyse connector compatibility between processes.
    """
)

st.divider()

# Summary metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Models loaded", n_models)
with col2:
    grades = [m.metadata.get("GRADE", "") for m in models.values()]
    st.metric("White-box models", sum(1 for g in grades if str(g).upper() == "WHITE-BOX"))
with col3:
    open_models = [
        m for m in models.values()
        if str(m.metadata.get("CONFIDENTIALITY", "")).strip() == "Open"
    ]
    st.metric("Open access", len(open_models))
with col4:
    trls = []
    for m in models.values():
        try:
            trls.append(int(m.metadata.get("TRL", 0)))
        except (ValueError, TypeError):
            pass
    avg_trl = f"{sum(trls)/len(trls):.1f}" if trls else "N/A"
    st.metric("Average TRL", avg_trl)

st.divider()

# Data directory info
if n_models == 0:
    st.warning(
        f"No model files were found in {DATA_DIR}. "
        "Place IETS v6 Excel files (.xlsx) in that directory and restart the app."
    )
else:
    st.info(
        f"{n_models} model{'s' if n_models != 1 else ''} loaded from "
        f"{DATA_DIR}. Navigate to the Catalog page to browse them."
    )
