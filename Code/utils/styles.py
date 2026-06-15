"""
Shared CSS injection and HTML helpers for the IETS Task XXIV Streamlit app.

Color/font theming is handled by ../.streamlit/config.toml.
This module only injects structural CSS that config.toml cannot express:
  - component shape (border-radius, box-shadow)
  - tab underline indicator
  - metric tile border
  - footer visibility
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Reusable inline style for white card divs (used in st.markdown HTML blocks)
# ---------------------------------------------------------------------------

CSS_CARD = (
    "background:#ffffff;"
    "border:1px solid #e2e8f0;"
    "border-radius:8px;"
    "box-shadow:0 1px 4px rgba(0,0,0,0.06);"
    "padding:16px 20px;"
    "margin-bottom:12px;"
)

# ---------------------------------------------------------------------------
# Structural CSS — no color overrides (those live in config.toml)
# ---------------------------------------------------------------------------

_GLOBAL_CSS = """
<style>
/* ── Sidebar right-border accent ────────────────────────────────────────── */
[data-testid="stSidebar"] {
    border-right: 1px solid #e2e8f0;
}

/* ── Top bar bottom-border ──────────────────────────────────────────────── */
[data-testid="stHeader"] {
    border-bottom: 1px solid #e2e8f0;
}

/* ── Buttons — rounded shape ────────────────────────────────────────────── */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
    font-size: 13px;
    padding: 6px 16px;
    transition: opacity 0.15s ease;
}
[data-testid="stDownloadButton"] > button {
    border-radius: 6px;
    font-weight: 500;
    font-size: 13px;
}

/* ── Tabs — underline indicator ─────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 0;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-weight: 500;
    font-size: 13px;
    padding: 8px 18px;
}

/* ── Expanders — rounded border ─────────────────────────────────────────── */
[data-testid="stExpander"] {
    border-radius: 8px;
    box-shadow: none;
}

/* ── Metrics — tile border ──────────────────────────────────────────────── */
[data-testid="stMetric"] {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stMetricLabel"] {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Dataframe — rounded border ─────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
}

/* ── Selectbox / multiselect — rounded ──────────────────────────────────── */
[data-baseweb="select"] {
    border-radius: 6px;
}

/* ── Bordered containers (model cards) — shadow ─────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

/* ── Divider ────────────────────────────────────────────────────────────── */
hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 16px 0;
}

/* ── Hide Streamlit footer ──────────────────────────────────────────────── */
footer { visibility: hidden; }
</style>
"""


def inject_css() -> None:
    """Inject structural CSS into the current page."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# HTML badge helper
# ---------------------------------------------------------------------------

def badge(text: str, color: str) -> str:
    """Return an inline HTML badge span."""
    return (
        f'<span style="'
        f'background:{color};'
        f'color:#ffffff;'
        f'padding:3px 10px;'
        f'border-radius:4px;'
        f'font-size:11px;'
        f'font-weight:600;'
        f'letter-spacing:0.04em;'
        f'display:inline-block;'
        f'">{text}</span>'
    )
