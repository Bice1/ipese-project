"""
Model Detail page — metadata, heat analysis (CC/GCC/Carnot), connectors, equipment, variables.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path

_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine.pinch import compute_pinch, PinchResult
from utils.categories import CATEGORY_DISPLAY_NAMES, CATEGORY_COLORS
from utils.loader import load_all_models
from utils.forum import load_posts, save_posts
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
    PLOTLY_LAYOUT_BASE,
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
    selected_name = next(iter(models))

model = models[selected_name]

# ---------------------------------------------------------------------------
# Sidebar — category-based model selector
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Model")

    # Step 1: category picker
    cats_present = sorted({m.category for m in models.values() if m.category})
    cat_display_options = ["All categories"] + [
        CATEGORY_DISPLAY_NAMES.get(s, s) for s in cats_present
    ]
    sel_cat_display = st.selectbox(
        "Category",
        options=cat_display_options,
        index=0,
        label_visibility="collapsed",
        key="sidebar_cat",
    )

    # Step 2: model picker (filtered by category)
    if sel_cat_display == "All categories":
        cat_models = list(models.keys())
    else:
        # Reverse-map display name → slug
        slug_for_display = {CATEGORY_DISPLAY_NAMES.get(s, s): s for s in cats_present}
        chosen_slug = slug_for_display.get(sel_cat_display, "")
        cat_models = [n for n, m in models.items() if m.category == chosen_slug]

    if not cat_models:
        cat_models = list(models.keys())

    default_idx = cat_models.index(selected_name) if selected_name in cat_models else 0
    new_selection = st.selectbox(
        "Model",
        options=cat_models,
        index=default_idx,
        label_visibility="collapsed",
        key="sidebar_model",
    )
    if new_selection != selected_name:
        st.session_state["selected_model"] = new_selection
        st.rerun()

    if st.button("Back to Catalog", use_container_width=True):
        st.switch_page("pages/1_Catalog.py")

    st.divider()
    st.subheader("Identity")
    _sidebar_username = st.text_input(
        "Your display name",
        value=st.session_state.get("username", ""),
        placeholder="Enter your name to comment",
        key="sidebar_username",
    )
    st.session_state["username"] = _sidebar_username.strip()

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
version = _meta("VERSION", "")
if version and version != "N/A":
    badges.append(_badge_html(f"v{version}", "#607D8B"))
sw = _meta("SOFTWARE", "")
if sw and sw != "N/A":
    badges.append(_badge_html(sw, "#9C27B0"))
if model.category:
    cat_color = CATEGORY_COLORS.get(model.category, "#888888")
    cat_label = CATEGORY_DISPLAY_NAMES.get(model.category, model.category)
    badges.append(_badge_html(cat_label, cat_color))

if badges:
    st.markdown("&nbsp;&nbsp;".join(badges), unsafe_allow_html=True)
    st.markdown("")  # spacer

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_heat, tab_connectors, tab_equipment, tab_variables, tab_forum = st.tabs(
    ["Overview", "Heat Analysis", "Connectors", "Equipment", "Variables", "Forum"]
)

# ===========================================================================
# Tab 1 — Overview
# ===========================================================================

with tab_overview:
    col_main, col_side = st.columns([2, 1])

    with col_main:
        desc = _meta("DESCRIPTION", "")
        if desc and desc != "N/A":
            st.subheader("Description")
            with st.container(border=True):
                st.markdown(
                    f'<p style="color:#333333;line-height:1.6;">{desc}</p>',
                    unsafe_allow_html=True,
                )

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

        # --- Supplementary material (PDF / MD) — supports one or many files ---
        suppl_raw = _meta("SUPPLEMENTARY MATERIAL", "")
        suppl_paths: list[Path] = []
        if suppl_raw and suppl_raw not in ("N/A", "-", ""):
            import json as _json
            try:
                suppl_paths = [Path(p) for p in _json.loads(suppl_raw)]
            except Exception:
                suppl_paths = [Path(suppl_raw)]
            suppl_paths = [p for p in suppl_paths if p.exists()]

        if suppl_paths:
            st.subheader("Supplementary Material")
            for suppl_path in suppl_paths:
                suppl_ext   = suppl_path.suffix.lower()
                suppl_bytes = suppl_path.read_bytes()
                st.caption(suppl_path.name)

                if suppl_ext == ".pdf":
                    st.download_button(
                        "Download PDF",
                        data=suppl_bytes,
                        file_name=suppl_path.name,
                        mime="application/pdf",
                        key=f"dl_pdf_{suppl_path.name}",
                    )

                elif suppl_ext == ".md":
                    suppl_text = suppl_bytes.decode("utf-8", errors="replace")
                    st.download_button(
                        "Download Markdown",
                        data=suppl_bytes,
                        file_name=suppl_path.name,
                        mime="text/markdown",
                        key=f"dl_md_{suppl_path.name}",
                    )
                    with st.expander("View content"):
                        st.markdown(suppl_text)

    with col_side:
        # BFD image
        bfd_path_str = _meta("BLOCK FLOW DIAGRAM", "")
        bfd_resolved = None
        if bfd_path_str and bfd_path_str not in ("N/A", "-", ""):
            candidates = [Path(bfd_path_str), DATA_DIR / bfd_path_str]
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
                    border: 2px dashed #CCCCCC; border-radius: 8px;
                    padding: 48px 24px; text-align: center;
                    color: #AAAAAA; font-size: 13px; background: #FAFAFA;
                ">Block Flow Diagram not available</div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        tile_defs = [("TRL", "TRL"), ("GRADE", "GRADE"), ("SHARING LAYER", "SHARING LAYER"), ("CONFIDENTIALITY", "CONFIDENTIALITY")]
        col_t1, col_t2 = st.columns(2)
        for i, (label, key) in enumerate(tile_defs):
            with (col_t1 if i % 2 == 0 else col_t2):
                st.metric(label, _meta(key))

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Software", _meta("SOFTWARE"))
        with col_s2:
            st.metric("Status", _meta("MODEL STATUS"))

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
        # Controls row
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 2, 3, 1])

        with ctrl_col1:
            cascade_options = ["ALL (combined)"] + cascade_labels
            selected_cascade_display = st.selectbox(
                "Cascade view",
                options=cascade_options,
                index=0,
            )
            cascade_filter = (
                None if selected_cascade_display == "ALL (combined)" else selected_cascade_display
            )

        with ctrl_col2:
            unit_options = ["All units"] + model.unit_names
            selected_unit = st.selectbox("Unit", options=unit_options)

        with ctrl_col3:
            chart_type = st.radio(
                "Chart type",
                options=["Composite Curves", "Grand Composite Curve", "Carnot GCC", "Both CC+GCC"],
                index=3,
                horizontal=True,
            )

        # Filter streams by unit if requested
        if selected_unit != "All units":
            streams_for_pinch = all_streams[all_streams["_unit"] == selected_unit].copy()
        else:
            streams_for_pinch = all_streams

        # Compute pinch
        result: PinchResult = compute_pinch(streams_for_pinch, cascade_filter=cascade_filter)

        if result.warnings:
            for w in result.warnings:
                st.warning(w)

        # Utility metrics
        if result.hot_cc or result.gcc:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Min hot utility Qh,min", f"{result.q_hot_min:.2f} kW")
            with m2:
                st.metric("Min cold utility Qc,min", f"{result.q_cold_min:.2f} kW")
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
                    "dtmin_contr", "heat_cascade",
                ]
                if c in streams_for_pinch.columns
            ]
            streams_display = streams_for_pinch[display_cols].copy()

            def _row_style(row):
                t = str(row.get("type", "")).strip().lower()
                if t == "hot":
                    return ["background-color: #FFF0EE"] * len(row)
                if t == "cold":
                    return ["background-color: #EEF4FF"] * len(row)
                return [""] * len(row)

            st.dataframe(
                streams_display.style.apply(_row_style, axis=1),
                use_container_width=True,
                hide_index=True,
            )

        cascade_label_display = selected_cascade_display.replace("ALL (combined)", "All cascades")

        # --- Composite Curves ---
        if chart_type in ("Composite Curves", "Both CC+GCC") and (result.hot_cc or result.cold_cc):
            fig_cc = go.Figure()

            if result.hot_cc:
                H_hot = [h for (_, h) in result.hot_cc]
                T_hot = [t for (t, _) in result.hot_cc]
                fig_cc.add_trace(go.Scatter(
                    x=H_hot, y=T_hot, mode="lines+markers",
                    name="Hot Composite Curve",
                    line=dict(color=COLOR_HOT, width=2.5),
                    marker=dict(size=5, color=COLOR_HOT),
                ))

            if result.cold_cc:
                H_cold = [h + result.q_hot_min for (_, h) in result.cold_cc]
                T_cold = [t for (t, _) in result.cold_cc]
                fig_cc.add_trace(go.Scatter(
                    x=H_cold, y=T_cold, mode="lines+markers",
                    name="Cold Composite Curve",
                    line=dict(color=COLOR_COLD, width=2.5),
                    marker=dict(size=5, color=COLOR_COLD),
                ))

            for t_pinch in result.pinch_temperatures:
                fig_cc.add_hline(
                    y=t_pinch, line_dash="dash",
                    line_color=COLOR_PINCH, line_width=1.5,
                    annotation_text=f"Pinch: {t_pinch:.1f} C",
                    annotation_font_size=11, annotation_font_color=COLOR_PINCH,
                )

            fig_cc.update_layout(**{
                **PLOTLY_LAYOUT_BASE,
                "title": {"text": f"Composite Curves  —  {cascade_label_display}", "x": 0.04, "font": {"size": 15}},
                "xaxis": {**PLOTLY_LAYOUT_BASE["xaxis"], "title": "Enthalpy [kW]"},
                "yaxis": {**PLOTLY_LAYOUT_BASE["yaxis"], "title": "Temperature [°C]  (shifted)"},
                "legend": {**PLOTLY_LAYOUT_BASE["legend"], "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
                "height": 480,
            })
            st.plotly_chart(fig_cc, use_container_width=True)

        # --- Grand Composite Curve ---
        if chart_type in ("Grand Composite Curve", "Both CC+GCC") and result.gcc:
            T_gcc = [t for (t, _) in result.gcc]
            H_gcc = [h for (_, h) in result.gcc]

            fig_gcc = go.Figure()
            fig_gcc.add_trace(go.Scatter(
                x=H_gcc, y=T_gcc, mode="lines+markers",
                name="Grand Composite Curve",
                line=dict(color=COLOR_GCC, width=2.5),
                marker=dict(size=5, color=COLOR_GCC),
                fill="tozerox", fillcolor="rgba(90, 138, 94, 0.08)",
            ))
            fig_gcc.add_vline(x=0, line_color="#CCCCCC", line_width=1.5)

            if T_gcc:
                fig_gcc.add_annotation(
                    x=result.q_hot_min, y=T_gcc[0],
                    text=f"Qh,min = {result.q_hot_min:.1f} kW",
                    showarrow=True, arrowhead=2, ax=40, ay=-20,
                    font=dict(size=11, color=COLOR_HOT), arrowcolor=COLOR_HOT,
                )
                if result.q_cold_min > 1e-3:
                    fig_gcc.add_annotation(
                        x=result.q_cold_min, y=T_gcc[-1],
                        text=f"Qc,min = {result.q_cold_min:.1f} kW",
                        showarrow=True, arrowhead=2, ax=40, ay=20,
                        font=dict(size=11, color=COLOR_COLD), arrowcolor=COLOR_COLD,
                    )

            for t_pinch in result.pinch_temperatures:
                fig_gcc.add_hline(
                    y=t_pinch, line_dash="dash",
                    line_color=COLOR_PINCH, line_width=1.5,
                    annotation_text=f"Pinch: {t_pinch:.1f} C",
                    annotation_font_size=11, annotation_font_color=COLOR_PINCH,
                )

            fig_gcc.update_layout(**{
                **PLOTLY_LAYOUT_BASE,
                "title": {"text": f"Grand Composite Curve  —  {cascade_label_display}", "x": 0.04, "font": {"size": 15}},
                "xaxis": {**PLOTLY_LAYOUT_BASE["xaxis"], "title": "Net Heat Flow [kW]", "zeroline": True, "zerolinewidth": 2, "zerolinecolor": "#CCCCCC"},
                "yaxis": {**PLOTLY_LAYOUT_BASE["yaxis"], "title": "Temperature [°C]  (shifted)"},
                "height": 480,
            })
            st.plotly_chart(fig_gcc, use_container_width=True)

        # --- Carnot-Factor GCC ---
        if chart_type == "Carnot GCC" and result.gcc:
            t_ref_c = 25.0   # ambient temperature reference
            T_REF_K = 298.15

            T_gcc_c = [t for (t, _) in result.gcc]
            H_gcc   = [h for (_, h) in result.gcc]

            # Carnot factor η = 1 − T_ref / T   (T in Kelvin)
            carnot_y = [
                1.0 - T_REF_K / (t + 273.15) if (t + 273.15) != 0 else 0.0
                for t in T_gcc_c
            ]

            fig_carnot = go.Figure()
            # Shaded area between curve and η=0 axis
            fig_carnot.add_trace(go.Scatter(
                x=[0] * len(carnot_y), y=carnot_y,
                mode="lines", line=dict(width=0), showlegend=False,
            ))
            fig_carnot.add_trace(go.Scatter(
                x=H_gcc, y=carnot_y, mode="lines+markers",
                name="Carnot GCC",
                line=dict(color=COLOR_GCC, width=2.5),
                marker=dict(size=5, color=COLOR_GCC),
                fill="tonextx", fillcolor="rgba(90, 138, 94, 0.1)",
            ))
            # η=0 reference line (pinch level)
            fig_carnot.add_hline(
                y=0, line_dash="dash", line_color=COLOR_PINCH, line_width=1.5,
                annotation_text=f"η=0  (T_ref = {t_ref_c:.1f} °C ambient)",
                annotation_font_size=11, annotation_font_color=COLOR_PINCH,
            )
            fig_carnot.add_vline(x=0, line_color="#CCCCCC", line_width=1.5)

            # Annotate Qh and Qc on the Carnot scale
            if carnot_y:
                fig_carnot.add_annotation(
                    x=result.q_hot_min, y=carnot_y[0],
                    text=f"Qh,min = {result.q_hot_min:.1f} kW",
                    showarrow=True, arrowhead=2, ax=40, ay=-20,
                    font=dict(size=11, color=COLOR_HOT), arrowcolor=COLOR_HOT,
                )
                if result.q_cold_min > 1e-3:
                    fig_carnot.add_annotation(
                        x=result.q_cold_min, y=carnot_y[-1],
                        text=f"Qc,min = {result.q_cold_min:.1f} kW",
                        showarrow=True, arrowhead=2, ax=40, ay=20,
                        font=dict(size=11, color=COLOR_COLD), arrowcolor=COLOR_COLD,
                    )

            fig_carnot.update_layout(**{
                **PLOTLY_LAYOUT_BASE,
                "title": {
                    "text": f"Carnot-Factor GCC  —  T_ref = {t_ref_c:.1f} °C (ambient)  —  {cascade_label_display}",
                    "x": 0.04, "font": {"size": 15},
                },
                "xaxis": {**PLOTLY_LAYOUT_BASE["xaxis"], "title": "Net Heat Flow [kW]"},
                "yaxis": {**PLOTLY_LAYOUT_BASE["yaxis"], "title": "Carnot factor  η = 1 − T_ref / T"},
                "height": 480,
            })
            st.plotly_chart(fig_carnot, use_container_width=True)

        if not result.hot_cc and not result.cold_cc and not result.gcc:
            st.info("No composite curve data could be computed for this selection.")

        if model.warnings:
            with st.expander("Parser warnings", expanded=False):
                for w in model.warnings:
                    st.text(w)


# ===========================================================================
# Tab 3 — Connectors
# ===========================================================================

with tab_connectors:
    st.subheader("External Connectors")
    ext = model.external_connectors
    if ext is not None and not ext.empty:
        st.dataframe(ext[[c for c in ext.columns if c is not None]], use_container_width=True, hide_index=True)
    else:
        st.info("No external connectors found.")

    int_conn = model.internal_connectors
    if int_conn is not None and not int_conn.empty:
        st.subheader("Internal Connectors")
        st.dataframe(int_conn[[c for c in int_conn.columns if c is not None]], use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Unit-level Connectors")
    for unit_name, unit in model.units.items():
        with st.expander(unit_name, expanded=True):
            if unit.description:
                st.caption(unit.description)
            if unit.connectors.empty:
                st.info("No connectors in this unit.")
            else:
                df_conn = unit.connectors.copy()
                # Reorder so description appears early (after name/type/direction)
                priority = ["name", "type", "direction", "description"]
                rest = [c for c in df_conn.columns if c not in priority and c is not None]
                ordered = [c for c in priority if c in df_conn.columns] + rest
                st.dataframe(df_conn[ordered], use_container_width=True, hide_index=True)


# ===========================================================================
# Tab 4 — Equipment
# ===========================================================================

with tab_equipment:
    for unit_name, unit in model.units.items():
        st.subheader(unit_name)

        if unit.fmin is not None and unit.fmax is not None:
            if unit.fmin == unit.fmax:
                st.caption(f"Fixed capacity (F = {unit.fmin})")
            else:
                st.caption(f"Scalable capacity: Fmin = {unit.fmin} — Fmax = {unit.fmax}")

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
                        st.dataframe(
                            params_df[[c for c in params_df.columns if c is not None]],
                            use_container_width=True,
                            hide_index=True,
                        )

        st.markdown("")


# ===========================================================================
# Tab 5 — Variables
# ===========================================================================

with tab_variables:
    if model.variables is None or model.variables.empty:
        st.info("No variables found for this model.")
    else:
        df_vars = model.variables.copy()

        # Filter controls
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            type_opts = sorted(df_vars["TYPE"].dropna().unique()) if "TYPE" in df_vars.columns else []
            type_filter = st.multiselect("Type", options=type_opts)
        with col_f2:
            grade_opts = sorted(df_vars["USER GRADE"].dropna().unique()) if "USER GRADE" in df_vars.columns else []
            grade_filter = st.multiselect("User grade", options=grade_opts)

        if type_filter and "TYPE" in df_vars.columns:
            df_vars = df_vars[df_vars["TYPE"].isin(type_filter)]
        if grade_filter and "USER GRADE" in df_vars.columns:
            df_vars = df_vars[df_vars["USER GRADE"].isin(grade_filter)]

        st.caption(f"{len(df_vars)} variable(s) shown")
        st.dataframe(df_vars, use_container_width=True, hide_index=True)


# ===========================================================================
# Tab 6 — Forum of Experts
# ===========================================================================

def _user_badge(username: str, size: int = 12) -> str:
    return (
        f'<span style="background:#1f77b4;color:white;padding:2px 8px;'
        f'border-radius:4px;font-size:{size}px;font-weight:600;">{username}</span>'
    )


def _render_comments(post: dict, posts: list[dict], username: str) -> None:
    """Render the comment thread for a single post (including nested replies)."""
    comments = post.get("comments", [])
    if comments:
        st.caption(f"{len(comments)} comment(s)")
    for comment in comments:
        with st.container(border=True):
            st.markdown(
                f'{_user_badge(comment["username"], 11)}'
                f'&nbsp;<span style="font-size:11px;color:#888;">'
                f'{comment["timestamp"].replace("T", " ")}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(comment["text"])

            # Nested replies
            for reply in comment.get("replies", []):
                st.markdown(
                    f'<div style="margin-left:24px;padding:6px 10px;'
                    f'border-left:3px solid #ddd;margin-top:6px;">'
                    f'{_user_badge(reply["username"], 10)}'
                    f'&nbsp;<span style="font-size:10px;color:#aaa;">'
                    f'{reply["timestamp"].replace("T", " ")}</span><br>'
                    f'{reply["text"]}</div>',
                    unsafe_allow_html=True,
                )

            # Reply-on-comment form
            if username:
                with st.expander("Reply to this comment"):
                    reply_text = st.text_area(
                        "Reply",
                        key=f"reply_{comment['id']}",
                        label_visibility="collapsed",
                        placeholder="Write a reply…",
                    )
                    if st.button("Post reply", key=f"btn_reply_{comment['id']}"):
                        if reply_text.strip():
                            comment.setdefault("replies", []).append(
                                {
                                    "id": str(uuid.uuid4()),
                                    "username": username,
                                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                                    "text": reply_text.strip(),
                                }
                            )
                            save_posts(model.filepath, posts)
                            st.rerun()

    # Add-comment form
    if username:
        with st.expander("Add a comment"):
            cmt_text = st.text_area(
                "Comment",
                key=f"cmt_{post['id']}",
                label_visibility="collapsed",
                placeholder="Write a comment on this post…",
            )
            if st.button("Post comment", key=f"btn_cmt_{post['id']}"):
                if cmt_text.strip():
                    post.setdefault("comments", []).append(
                        {
                            "id": str(uuid.uuid4()),
                            "username": username,
                            "timestamp": datetime.now().isoformat(timespec="seconds"),
                            "text": cmt_text.strip(),
                            "replies": [],
                        }
                    )
                    save_posts(model.filepath, posts)
                    st.rerun()


with tab_forum:
    username: str = st.session_state.get("username", "")
    posts = load_posts(model.filepath)

    if not username:
        st.info("Enter your display name in the sidebar to post or comment.")

    # --- New post form ---
    if username:
        with st.expander("New post", expanded=not posts):
            post_title = st.text_input(
                "Title",
                key="forum_new_title",
                placeholder="Give your post a short, descriptive title",
            )
            post_text = st.text_area(
                "Body",
                key="forum_new_text",
                placeholder="Share your expertise, findings, or questions about this model…",
                height=120,
            )
            if st.button("Submit post", type="primary"):
                if post_title.strip():
                    posts.append(
                        {
                            "id": str(uuid.uuid4()),
                            "username": username,
                            "timestamp": datetime.now().isoformat(timespec="seconds"),
                            "title": post_title.strip(),
                            "text": post_text.strip(),
                            "comments": [],
                        }
                    )
                    save_posts(model.filepath, posts)
                    st.rerun()
                else:
                    st.warning("A title is required.")

    st.divider()

    # --- Post list (newest first) ---
    if not posts:
        st.caption("No posts yet. Be the first to open a discussion!")
    else:
        st.caption(f"{len(posts)} post(s)")
        for post in reversed(posts):
            with st.container(border=True):
                st.markdown(
                    f'### {post["title"]}\n'
                    f'{_user_badge(post["username"])}'
                    f'&nbsp;<span style="font-size:11px;color:#888;">'
                    f'{post["timestamp"].replace("T", " ")}</span>',
                    unsafe_allow_html=True,
                )
                if post.get("text"):
                    st.markdown(post["text"])
                st.markdown("")
                _render_comments(post, posts, username)
