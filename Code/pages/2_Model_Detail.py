"""
Model Detail page — full metadata panel, connectors, equipment.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import pandas as pd
import streamlit as st

from utils.loader import load_all_models
from utils.constants import (
    CONFIDENTIALITY_COLORS,
    DATA_DIR,
    GRADE_COLORS,
    METADATA_DISPLAY_KEYS,
    METADATA_TABLE_EXCLUDE,
    METADATA_TILE_KEYS,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Model Detail — IETS Task XXIV",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Session state — initialise models if not already loaded
# ---------------------------------------------------------------------------

if "models" not in st.session_state:
    with st.spinner("Loading model database ..."):
        st.session_state["models"] = load_all_models(DATA_DIR)

if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = None

models: dict = st.session_state["models"]

selected_name = st.session_state.get("selected_model")
if not selected_name or selected_name not in models:
    # Fallback: first available model
    selected_name = next(iter(models))

model = models[selected_name]

# ---------------------------------------------------------------------------
# Sidebar — model selector
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Model")
    new_selection = st.selectbox(
        "Select model",
        options=list(models.keys()),
        index=list(models.keys()).index(selected_name),
        label_visibility="collapsed",
    )
    if new_selection != selected_name:
        st.session_state["selected_model"] = new_selection
        st.rerun()

    if st.button("Back to Catalog", use_container_width=True):
        st.switch_page("pages/1_Catalog.py")

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _meta(key: str, default: str = "N/A") -> str:
    """Return metadata value as a clean string."""
    val = model.metadata.get(key)
    return str(val).strip() if val is not None and str(val).strip() else default


def _badge_html(text: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:white;padding:3px 10px;'
        f'border-radius:4px;font-size:11px;font-weight:600;">{text}</span>'
    )


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

model_name_display = _meta("MODEL NAME", selected_name)
st.title(model_name_display)

uid = _meta("MODEL UID")
authors = _meta("AUTHORS AND CONTRIBUTORS")
header_parts = []
if uid != "N/A":
    header_parts.append(f"UID: {uid}")
if authors != "N/A":
    header_parts.append(f"Authors: {authors}")
if header_parts:
    st.caption("  |  ".join(header_parts))

# Grade + confidentiality badges inline
grade = _meta("GRADE", "").upper()
grade_color = GRADE_COLORS.get(grade, "#888888")
conf = _meta("CONFIDENTIALITY", "")
conf_color = CONFIDENTIALITY_COLORS.get(conf, "#888888")

badges = []
if grade:
    badges.append(_badge_html(grade, grade_color))
if conf:
    badges.append(_badge_html(conf, conf_color))
trl_val = _meta("TRL")
if trl_val != "N/A":
    badges.append(_badge_html(f"TRL {trl_val}", "#607D8B"))
sw = _meta("SOFTWARE", "")
if sw and sw != "N/A":
    badges.append(_badge_html(sw, "#9C27B0"))

if badges:
    st.markdown("&nbsp;&nbsp;".join(badges), unsafe_allow_html=True)
    st.markdown("")  # spacer

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_heat, tab_connectors, tab_equipment = st.tabs(
    ["Overview", "Heat Analysis", "Connectors", "Equipment"]
)


# ===========================================================================
# Tab 1 — Overview
# ===========================================================================

with tab_overview:
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # Description
        desc = _meta("DESCRIPTION", "")
        if desc and desc != "N/A":
            st.subheader("Description")
            with st.container(border=True):
                st.markdown(
                    f'<p style="color:#333333;line-height:1.6;">{desc}</p>',
                    unsafe_allow_html=True,
                )

        # Metadata table
        st.subheader("Metadata")
        meta_rows = []
        for key in METADATA_DISPLAY_KEYS:
            if key in METADATA_TABLE_EXCLUDE:
                continue
            val = model.metadata.get(key)
            display_val = str(val).strip() if val is not None else ""
            if display_val:
                meta_rows.append({"Field": key, "Value": display_val})

        if meta_rows:
            meta_df = pd.DataFrame(meta_rows)
            st.dataframe(
                meta_df,
                use_container_width=True,
                hide_index=True,
                height=min(35 * len(meta_rows) + 38, 600),
            )

    with col_side:
        # BFD image
        bfd_key = "BLOCK FLOW DIAGRAM ( .png or .svg)"
        bfd_path_str = _meta(bfd_key, "")
        bfd_resolved = None

        if bfd_path_str and bfd_path_str != "N/A":
            # Try relative to DATA_DIR and absolute
            candidates = [
                DATA_DIR / bfd_path_str,
                Path(bfd_path_str),
            ]
            for candidate in candidates:
                if candidate.exists():
                    bfd_resolved = candidate
                    break

        if bfd_resolved:
            st.image(str(bfd_resolved), caption="Block Flow Diagram", use_container_width=True)
        else:
            st.markdown(
                """
                <div style="
                    border: 2px dashed #CCCCCC;
                    border-radius: 8px;
                    padding: 48px 24px;
                    text-align: center;
                    color: #AAAAAA;
                    font-size: 13px;
                    background: #FAFAFA;
                ">
                    Block Flow Diagram not available
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Key metric tiles
        tile_defs = [
            ("TRL", "TRL"),
            ("GRADE", "GRADE"),
            ("SHARING LAYER", "SHARING LAYER"),
            ("CONFIDENTIALITY", "CONFIDENTIALITY"),
        ]
        col_t1, col_t2 = st.columns(2)
        for i, (label, key) in enumerate(tile_defs):
            target_col = col_t1 if i % 2 == 0 else col_t2
            with target_col:
                st.metric(label, _meta(key))

        # Software + status
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Software", _meta("SOFTWARE"))
        with col_s2:
            st.metric("Status", _meta("MODEL STATUS"))

        # Units summary
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Units")
        for unit_name, unit in model.units.items():
            n_streams = len(unit.heat_streams) if not unit.heat_streams.empty else 0
            n_conn = len(unit.connectors) if not unit.connectors.empty else 0
            n_eq = len(unit.equipments)
            with st.container(border=True):
                st.markdown(
                    f"**{unit_name}**  \n"
                    f"Capacity: {unit.fmin} — {unit.fmax}  \n"
                    f"{n_streams} heat streams  |  {n_conn} connectors  |  {n_eq} equipment items",
                )


# ===========================================================================
# Tab 2 — Heat Analysis
# ===========================================================================

with tab_heat:
    st.info("🚧 Work In Progress")


# ===========================================================================
# Tab 3 — Connectors
# ===========================================================================

with tab_connectors:
    # External connectors
    st.subheader("External Connectors")
    ext = model.external_connectors
    if ext is not None and not ext.empty:
        display_ext = ext[[c for c in ext.columns if c is not None]].copy()
        st.dataframe(display_ext, use_container_width=True, hide_index=True)
    else:
        st.info("No external connectors found.")

    # Internal connectors
    int_conn = model.internal_connectors
    if int_conn is not None and not int_conn.empty:
        st.subheader("Internal Connectors")
        display_int = int_conn[[c for c in int_conn.columns if c is not None]].copy()
        st.dataframe(display_int, use_container_width=True, hide_index=True)

    st.divider()

    # Per-unit connectors
    st.subheader("Unit-level Connectors")
    for unit_name, unit in model.units.items():
        with st.expander(unit_name, expanded=True):
            if unit.connectors.empty:
                st.info("No connectors in this unit.")
            else:
                df_conn = unit.connectors.copy()
                valid_cols = [c for c in df_conn.columns if c is not None]
                st.dataframe(
                    df_conn[valid_cols],
                    use_container_width=True,
                    hide_index=True,
                )


# ===========================================================================
# Tab 4 — Equipment
# ===========================================================================

with tab_equipment:
    for unit_name, unit in model.units.items():
        st.subheader(unit_name)

        capacity_str = ""
        if unit.fmin is not None and unit.fmax is not None:
            if unit.fmin == unit.fmax:
                capacity_str = f"Fixed capacity (F = {unit.fmin})"
            else:
                capacity_str = f"Scalable capacity: Fmin = {unit.fmin} — Fmax = {unit.fmax}"
        if capacity_str:
            st.caption(capacity_str)

        if not unit.equipments:
            st.info("No equipment data for this unit.")
        else:
            for eq in unit.equipments:
                with st.container(border=True):
                    eq_name = eq.get("name", "Unknown")
                    eq_type = eq.get("type") or ""
                    eq_sub = eq.get("subtype") or ""

                    label_parts = [f"**{eq_name}**"]
                    type_str = "  |  ".join(p for p in [eq_type, eq_sub] if p)
                    if type_str:
                        label_parts.append(f"*{type_str}*")
                    st.markdown("  —  ".join(label_parts))

                    params = eq.get("params", [])
                    if params:
                        params_df = pd.DataFrame(params)
                        valid_cols = [c for c in params_df.columns if c is not None]
                        st.dataframe(
                            params_df[valid_cols],
                            use_container_width=True,
                            hide_index=True,
                        )

        st.markdown("")  # spacer between units
