"""
Model Detail page — full metadata panel, heat analysis (GCC/CC), connectors, equipment.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine.pinch import compute_pinch, PinchResult
from utils.loader import load_all_models
from utils.constants import (
    COLOR_COLD,
    COLOR_GCC,
    COLOR_HOT,
    COLOR_PINCH,
    CONFIDENTIALITY_COLORS,
    DATA_DIR,
    GRADE_COLORS,
    METADATA_DISPLAY_KEYS,
    METADATA_TABLE_EXCLUDE,
    METADATA_TILE_KEYS,
    PLOTLY_LAYOUT_BASE,
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
# Collect all heat streams across all units
# ---------------------------------------------------------------------------

def _collect_all_streams() -> pd.DataFrame:
    """Merge heat_streams from every unit into a single DataFrame."""
    frames = []
    for unit_name, unit in model.units.items():
        if unit.heat_streams.empty:
            continue
        df = unit.heat_streams.copy()
        df["_unit"] = unit_name
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _get_cascade_labels(streams_df: pd.DataFrame) -> list[str]:
    """Return sorted list of distinct, non-empty cascade labels."""
    if streams_df.empty or "heat_cascade" not in streams_df.columns:
        return []
    labels = set()
    for val in streams_df["heat_cascade"].dropna():
        s = str(val).strip()
        if s and s.upper() != "DEFAULT":
            labels.add(s)
    return sorted(labels)


all_streams = _collect_all_streams()
cascade_labels = _get_cascade_labels(all_streams)

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
        bfd_key = "BLOCK FLOW DIAGRAM"
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
    if all_streams.empty:
        st.info("No heat streams found in this model.")
    else:
        # Controls bar
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 3, 1])

        with ctrl_col1:
            cascade_options = ["ALL (combined)"] + cascade_labels
            selected_cascade_display = st.selectbox(
                "Cascade view",
                options=cascade_options,
                index=0,
            )
            cascade_filter = (
                None
                if selected_cascade_display == "ALL (combined)"
                else selected_cascade_display
            )

        with ctrl_col2:
            chart_type = st.radio(
                "Chart type",
                options=["Composite Curves", "Grand Composite Curve", "Both"],
                index=2,
                horizontal=True,
            )

        # Compute pinch
        result: PinchResult = compute_pinch(all_streams, cascade_filter=cascade_filter)

        # Warnings from engine
        if result.warnings:
            for w in result.warnings:
                st.warning(w)

        # Utility metrics
        if result.hot_cc or result.gcc:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(
                    "Min hot utility Qh,min",
                    f"{result.q_hot_min:.2f} kW",
                )
            with m2:
                st.metric(
                    "Min cold utility Qc,min",
                    f"{result.q_cold_min:.2f} kW",
                )
            with m3:
                pinch_str = (
                    ", ".join(f"{t:.1f} C" for t in result.pinch_temperatures)
                    if result.pinch_temperatures
                    else "N/A"
                )
                st.metric("Pinch temperature(s)", pinch_str)

        st.divider()

        # Heat streams table
        with st.expander("Heat streams data", expanded=False):
            display_cols = [
                c for c in [
                    "_unit", "name", "type", "T_in", "T_in_unit",
                    "T_out", "T_out_unit", "H_in", "H_out", "H_in_unit",
                    "dtmin_contr", "heat_cascade", "is_phase_change",
                ]
                if c in all_streams.columns
            ]
            streams_display = all_streams[display_cols].copy()

            # Highlight Hot / Cold rows
            def _row_style(row):
                t = str(row.get("type", "")).strip().lower()
                if t == "hot":
                    return [f"background-color: #FFF0EE"] * len(row)
                if t == "cold":
                    return [f"background-color: #EEF4FF"] * len(row)
                return [""] * len(row)

            st.dataframe(
                streams_display.style.apply(_row_style, axis=1),
                use_container_width=True,
                hide_index=True,
            )

        # --------------- Charts ---------------

        cascade_label_display = (
            selected_cascade_display.replace("ALL (combined)", "All cascades")
        )

        # --- Composite Curves ---
        if chart_type in ("Composite Curves", "Both") and (result.hot_cc or result.cold_cc):
            fig_cc = go.Figure()

            if result.hot_cc:
                H_hot = [h for (_, h) in result.hot_cc]
                T_hot = [t for (t, _) in result.hot_cc]
                fig_cc.add_trace(go.Scatter(
                    x=H_hot,
                    y=T_hot,
                    mode="lines+markers",
                    name="Hot Composite Curve",
                    line=dict(color=COLOR_HOT, width=2.5),
                    marker=dict(size=5, color=COLOR_HOT),
                ))

            if result.cold_cc:
                # Offset cold CC by q_hot_min so curves touch at pinch
                H_cold = [h + result.q_hot_min for (_, h) in result.cold_cc]
                T_cold = [t for (t, _) in result.cold_cc]
                fig_cc.add_trace(go.Scatter(
                    x=H_cold,
                    y=T_cold,
                    mode="lines+markers",
                    name="Cold Composite Curve",
                    line=dict(color=COLOR_COLD, width=2.5),
                    marker=dict(size=5, color=COLOR_COLD),
                ))

            # Pinch horizontal lines
            for t_pinch in result.pinch_temperatures:
                fig_cc.add_hline(
                    y=t_pinch,
                    line_dash="dash",
                    line_color=COLOR_PINCH,
                    line_width=1.5,
                    annotation_text=f"Pinch: {t_pinch:.1f} C",
                    annotation_font_size=11,
                    annotation_font_color=COLOR_PINCH,
                )

            layout_cc = {
                **PLOTLY_LAYOUT_BASE,
                "title": {
                    "text": f"Composite Curves  —  {cascade_label_display}",
                    "x": 0.04,
                    "font": {"size": 15},
                },
                "xaxis": {
                    **PLOTLY_LAYOUT_BASE["xaxis"],
                    "title": "Enthalpy [kW]",
                },
                "yaxis": {
                    **PLOTLY_LAYOUT_BASE["yaxis"],
                    "title": "Temperature [C]  (shifted)",
                },
                "legend": {
                    **PLOTLY_LAYOUT_BASE["legend"],
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1,
                },
                "height": 480,
            }
            fig_cc.update_layout(**layout_cc)
            st.plotly_chart(fig_cc, use_container_width=True)

        # --- Grand Composite Curve ---
        if chart_type in ("Grand Composite Curve", "Both") and result.gcc:
            T_gcc = [t for (t, _) in result.gcc]
            H_gcc = [h for (_, h) in result.gcc]

            fig_gcc = go.Figure()

            fig_gcc.add_trace(go.Scatter(
                x=H_gcc,
                y=T_gcc,
                mode="lines+markers",
                name="Grand Composite Curve",
                line=dict(color=COLOR_GCC, width=2.5),
                marker=dict(size=5, color=COLOR_GCC),
                fill="tozerox",
                fillcolor="rgba(90, 138, 94, 0.08)",
            ))

            # Vertical axis at x=0 (pinch reference)
            fig_gcc.add_vline(
                x=0,
                line_color="#CCCCCC",
                line_width=1.5,
            )

            # Annotations for utilities
            if T_gcc:
                t_top = T_gcc[0]
                t_bot = T_gcc[-1]
                fig_gcc.add_annotation(
                    x=result.q_hot_min,
                    y=t_top,
                    text=f"Qh,min = {result.q_hot_min:.1f} kW",
                    showarrow=True,
                    arrowhead=2,
                    ax=40,
                    ay=-20,
                    font=dict(size=11, color=COLOR_HOT),
                    arrowcolor=COLOR_HOT,
                )
                if result.q_cold_min > 1e-3:
                    fig_gcc.add_annotation(
                        x=result.q_cold_min,
                        y=t_bot,
                        text=f"Qc,min = {result.q_cold_min:.1f} kW",
                        showarrow=True,
                        arrowhead=2,
                        ax=40,
                        ay=20,
                        font=dict(size=11, color=COLOR_COLD),
                        arrowcolor=COLOR_COLD,
                    )

            # Pinch horizontal lines
            for t_pinch in result.pinch_temperatures:
                fig_gcc.add_hline(
                    y=t_pinch,
                    line_dash="dash",
                    line_color=COLOR_PINCH,
                    line_width=1.5,
                    annotation_text=f"Pinch: {t_pinch:.1f} C",
                    annotation_font_size=11,
                    annotation_font_color=COLOR_PINCH,
                )

            layout_gcc = {
                **PLOTLY_LAYOUT_BASE,
                "title": {
                    "text": f"Grand Composite Curve  —  {cascade_label_display}",
                    "x": 0.04,
                    "font": {"size": 15},
                },
                "xaxis": {
                    **PLOTLY_LAYOUT_BASE["xaxis"],
                    "title": "Net Heat Flow [kW]",
                    "zeroline": True,
                    "zerolinewidth": 2,
                    "zerolinecolor": "#CCCCCC",
                },
                "yaxis": {
                    **PLOTLY_LAYOUT_BASE["yaxis"],
                    "title": "Temperature [C]  (shifted)",
                },
                "height": 480,
            }
            fig_gcc.update_layout(**layout_gcc)
            st.plotly_chart(fig_gcc, use_container_width=True)

        if not result.hot_cc and not result.cold_cc and not result.gcc:
            st.info("No composite curve data could be computed for this selection.")

        # Parser warnings
        if model.warnings:
            with st.expander("Parser warnings", expanded=False):
                for w in model.warnings:
                    st.text(w)


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
