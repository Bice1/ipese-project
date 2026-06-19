"""
Multi-Model Heat Integration page.

Combines heat streams from N selected models (each scaled by a capacity factor f),
runs the pinch engine on the merged set, and reports:
  Tab 1 - Combined CC / GCC charts (colour-coded by source model)
  Tab 2 - Recovery Potential: individual vs combined Qh/Qc
  Tab 3 - Stream Candidates: hot→cold pairs across models ranked by heat potential
"""

from __future__ import annotations

import sys
from itertools import product as _product
from pathlib import Path

_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine.pinch import compute_pinch, PinchResult
from parser.parser import ParsedModel
from utils.categories import CATEGORY_DISPLAY_NAMES, CATEGORY_COLORS
from utils.constants import (
    COLOR_COLD, COLOR_GCC, COLOR_HOT, COLOR_PINCH,
    DATA_DIR, PLOTLY_LAYOUT_BASE,
)
from utils.loader import load_all_models
from utils.styles import inject_css

inject_css()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "models" not in st.session_state:
    with st.spinner("Loading model database ..."):
        st.session_state["models"] = load_all_models(DATA_DIR)

models: dict[str, ParsedModel] = st.session_state["models"]

# Colour palette - one colour per model (up to 12, then cycling)
_MODEL_PALETTE = [
    "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
    "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#7f7f7f",
    "#aec7e8", "#f7b6d2",
]


def _model_color(name: str, name_list: list[str]) -> str:
    idx = name_list.index(name) if name in name_list else 0
    return _MODEL_PALETTE[idx % len(_MODEL_PALETTE)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _model_f_range(model: ParsedModel) -> tuple[float, float]:
    """Aggregate fmin/fmax over all units; fall back to [0.1, 3.0]."""
    fmins = [u.fmin for u in model.units.values() if u.fmin is not None]
    fmaxs = [u.fmax for u in model.units.values() if u.fmax is not None]
    lo = min(fmins) if fmins else 0.1
    hi = max(fmaxs) if fmaxs else 3.0
    lo = max(lo, 0.1)
    hi = max(hi, lo + 0.1)
    return lo, hi


def _collect_scaled_streams(model: ParsedModel, f: float, model_name: str) -> pd.DataFrame:
    """Merge all unit heat_streams, tag with _model/_unit, scale H by f."""
    frames = []
    for unit_name, unit in model.units.items():
        if unit.heat_streams is None or unit.heat_streams.empty:
            continue
        df = unit.heat_streams.copy()
        df["_model"] = model_name
        df["_unit"] = unit_name
        if f != 1.0:
            df["H_in"] = pd.to_numeric(df["H_in"], errors="coerce") * f
            df["H_out"] = pd.to_numeric(df["H_out"], errors="coerce") * f
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _build_cross_model_candidates(
    selected_items: list[tuple[str, ParsedModel, float]],
) -> pd.DataFrame:
    """
    Cross-join hot streams from model A with cold streams from model B (A≠B).
    Keep pairs where temperature ranges overlap and hot is hotter than cold.
    Rank by estimated heat potential Q_candidate [kW].
    """
    # Collect numeric streams per model
    model_streams: dict[str, pd.DataFrame] = {}
    for name, mdl, f in selected_items:
        df = _collect_scaled_streams(mdl, f, name)
        if df.empty:
            continue
        for col in ("T_in", "T_out", "H_in", "H_out"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["T_in", "T_out", "H_in", "H_out"])
        df["dH"] = (df["H_out"] - df["H_in"]).abs()
        model_streams[name] = df

    rows = []
    model_names = list(model_streams.keys())
    for name_a, name_b in _product(model_names, model_names):
        if name_a == name_b:
            continue
        df_a = model_streams[name_a]
        df_b = model_streams[name_b]

        hot_a = df_a[df_a["type"].apply(lambda v: str(v).strip().lower()) == "hot"]
        cold_b = df_b[df_b["type"].apply(lambda v: str(v).strip().lower()) == "cold"]

        for _, hot in hot_a.iterrows():
            t_hot_hi = max(float(hot["T_in"]), float(hot["T_out"]))
            t_hot_lo = min(float(hot["T_in"]), float(hot["T_out"]))
            dh_hot = float(hot["dH"])

            for _, cold in cold_b.iterrows():
                t_cold_hi = max(float(cold["T_in"]), float(cold["T_out"]))
                t_cold_lo = min(float(cold["T_in"]), float(cold["T_out"]))
                dh_cold = float(cold["dH"])

                # Hot stream must be globally hotter than the cold stream
                if t_hot_hi <= t_cold_lo:
                    continue

                # Compute temperature overlap
                overlap_lo = max(t_hot_lo, t_cold_lo)
                overlap_hi = min(t_hot_hi, t_cold_hi)
                if overlap_hi <= overlap_lo:
                    continue

                hot_span = t_hot_hi - t_hot_lo if (t_hot_hi - t_hot_lo) > 1e-6 else 1.0
                overlap_frac = (overlap_hi - overlap_lo) / hot_span
                q_candidate = min(dh_hot, dh_cold) * overlap_frac

                rows.append({
                    "Source model": name_a,
                    "Hot stream": str(hot.get("name", "-")),
                    "T_hot_in [°C]": round(t_hot_hi, 1),
                    "T_hot_out [°C]": round(t_hot_lo, 1),
                    "Target model": name_b,
                    "Cold stream": str(cold.get("name", "-")),
                    "T_cold_in [°C]": round(t_cold_lo, 1),
                    "T_cold_out [°C]": round(t_cold_hi, 1),
                    "T overlap [°C]": f"{overlap_lo:.1f} to {overlap_hi:.1f}",
                    "Q candidate [kW]": round(q_candidate, 2),
                })

    if not rows:
        return pd.DataFrame()
    df_out = pd.DataFrame(rows).sort_values("Q candidate [kW]", ascending=False)
    return df_out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Multi-Model Integration")

    all_model_names = sorted(models.keys())
    selected_names: list[str] = st.multiselect(
        "Select models (≥ 2)",
        options=all_model_names,
        default=[],
        help="Choose two or more industrial models to integrate thermally.",
    )

    f_values: dict[str, float] = {}
    if selected_names:
        st.divider()
        st.subheader("Capacity factors")
        for name in selected_names:
            mdl = models[name]
            lo, hi = _model_f_range(mdl)
            cat = CATEGORY_DISPLAY_NAMES.get(mdl.category, mdl.category or "")
            st.caption(f"**{name}**" + (f"  |  {cat}" if cat else ""))
            f_values[name] = st.slider(
                f"f - {name}",
                min_value=lo,
                max_value=hi,
                value=1.0,
                step=0.05,
                label_visibility="collapsed",
                help=(
                    "f = 1: reference capacity as modelled.  "
                    "f = 2: two identical plants in parallel.  "
                    f"Range from model fmin/fmax ({lo:.2f} to {hi:.2f})."
                ),
            )

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title("Multi-Model Heat Integration")
st.warning("Work in progress (WIP) - results are indicative only.")
st.caption(
    "Select 2 or more models in the sidebar and adjust their capacity factors. "
    "The pinch engine merges all heat streams and computes the combined CC/GCC "
    "and the thermal synergy potential."
)

if len(selected_names) < 2:
    st.info("Select at least **2 models** in the sidebar to run the integration analysis.")
    st.stop()

# ---------------------------------------------------------------------------
# Build merged stream table and individual results
# ---------------------------------------------------------------------------

selected_items: list[tuple[str, ParsedModel, float]] = [
    (name, models[name], f_values[name]) for name in selected_names
]

merged_frames: list[pd.DataFrame] = []
individual_results: dict[str, PinchResult] = {}
models_with_no_streams: list[str] = []

for name, mdl, f in selected_items:
    df = _collect_scaled_streams(mdl, f, name)
    if df.empty:
        models_with_no_streams.append(name)
        continue
    ind_result = compute_pinch(df)
    individual_results[name] = ind_result
    merged_frames.append(df)

if models_with_no_streams:
    st.warning(
        f"These models have no heat stream data and are excluded from the analysis: "
        + ", ".join(models_with_no_streams)
    )

if not merged_frames:
    st.error("None of the selected models contain heat stream data.")
    st.stop()

merged_streams = pd.concat(merged_frames, ignore_index=True)
combined_result = compute_pinch(merged_streams)

if combined_result.warnings:
    with st.expander("Computation warnings", expanded=False):
        for w in combined_result.warnings:
            st.warning(w)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_heat, tab_recovery, tab_candidates = st.tabs(
    ["Combined Heat Analysis", "Recovery Potential", "Stream Candidates"]
)

# ===========================================================================
# Tab 1 - Combined Heat Analysis
# ===========================================================================

with tab_heat:
    # Metrics row
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Combined Qc,min", f"{combined_result.q_cold_min:.2f} kW")
    with m2:
        st.metric("Combined Qh,min", f"{combined_result.q_hot_min:.2f} kW")
    with m3:
        pinch_str = (
            ", ".join(f"{t:.1f} °C" for t in combined_result.pinch_temperatures)
            if combined_result.pinch_temperatures else "N/A"
        )
        st.metric("Pinch temperature(s)", pinch_str)

    st.divider()

    # ── Composite Curves ────────────────────────────────────────────────────
    if combined_result.hot_cc or combined_result.cold_cc:
        fig_cc = go.Figure()

        if combined_result.hot_cc:
            H_hot = [h for (_, h) in combined_result.hot_cc]
            T_hot = [t for (t, _) in combined_result.hot_cc]
            fig_cc.add_trace(go.Scatter(
                x=H_hot, y=T_hot, mode="lines+markers",
                name="Hot Composite (combined)",
                line=dict(color=COLOR_HOT, width=2.5),
                marker=dict(size=5, color=COLOR_HOT),
            ))

        if combined_result.cold_cc:
            H_cold = [h + combined_result.q_cold_min for (_, h) in combined_result.cold_cc]
            T_cold = [t for (t, _) in combined_result.cold_cc]
            fig_cc.add_trace(go.Scatter(
                x=H_cold, y=T_cold, mode="lines+markers",
                name="Cold Composite (combined)",
                line=dict(color=COLOR_COLD, width=2.5),
                marker=dict(size=5, color=COLOR_COLD),
            ))

        if combined_result.cold_cc and combined_result.q_cold_min > 0.01:
            fig_cc.add_shape(type="line",
                x0=0, x1=combined_result.q_cold_min,
                y0=T_cold[0], y1=T_cold[0],
                line=dict(color=COLOR_COLD, width=1.5, dash="dash"),
            )
            fig_cc.add_annotation(
                x=combined_result.q_cold_min / 2, y=T_cold[0],
                text=f"Q_CU = {combined_result.q_cold_min:.1f} kW",
                showarrow=False, yshift=10,
                font=dict(size=11, color=COLOR_COLD),
            )

        if combined_result.hot_cc and combined_result.cold_cc and combined_result.q_hot_min > 0.01:
            fig_cc.add_shape(type="line",
                x0=H_hot[-1], x1=H_cold[-1],
                y0=T_hot[-1], y1=T_hot[-1],
                line=dict(color=COLOR_HOT, width=1.5, dash="dash"),
            )
            fig_cc.add_annotation(
                x=(H_hot[-1] + H_cold[-1]) / 2, y=T_hot[-1],
                text=f"Q_HU = {combined_result.q_hot_min:.1f} kW",
                showarrow=False, yshift=10,
                font=dict(size=11, color=COLOR_HOT),
            )

        for t_pinch in combined_result.pinch_temperatures:
            fig_cc.add_hline(
                y=t_pinch, line_dash="dash",
                line_color=COLOR_PINCH, line_width=1.5,
                annotation_text=f"Pinch: {t_pinch:.1f} °C",
                annotation_font_size=11, annotation_font_color=COLOR_PINCH,
            )

        fig_cc.update_layout(**{
            **PLOTLY_LAYOUT_BASE,
            "title": {"text": "Composite Curves - combined models", "x": 0.04, "font": {"size": 15}},
            "xaxis": {**PLOTLY_LAYOUT_BASE["xaxis"], "title": "Enthalpy [kW]"},
            "yaxis": {**PLOTLY_LAYOUT_BASE["yaxis"], "title": "Temperature [°C]  (shifted)"},
            "legend": {**PLOTLY_LAYOUT_BASE["legend"], "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
            "height": 460,
        })
        st.plotly_chart(fig_cc, use_container_width=True)

    # ── Grand Composite Curve ────────────────────────────────────────────────
    if combined_result.gcc:
        T_gcc = [t for (t, _) in combined_result.gcc]
        H_gcc = [h for (_, h) in combined_result.gcc]
        x_max = max(H_gcc)

        fig_gcc = go.Figure()
        fig_gcc.add_trace(go.Scatter(
            x=H_gcc, y=T_gcc, mode="lines+markers",
            name="Grand Composite Curve",
            line=dict(color=COLOR_GCC, width=2.5),
            marker=dict(size=5, color=COLOR_GCC),
        ))
        fig_gcc.add_trace(go.Scatter(
            x=[x_max] * len(T_gcc), y=T_gcc,
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        fig_gcc.add_trace(go.Scatter(
            x=H_gcc, y=T_gcc, mode="lines",
            fill="tonextx", fillcolor="rgba(90, 138, 94, 0.12)",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig_gcc.add_vline(x=0, line_color="#cbd5e1", line_width=1.5)

        if T_gcc:
            fig_gcc.add_annotation(
                x=combined_result.q_hot_min, y=T_gcc[0],
                text=f"Qh,min = {combined_result.q_hot_min:.1f} kW",
                showarrow=True, arrowhead=2, ax=40, ay=-20,
                font=dict(size=11, color=COLOR_HOT), arrowcolor=COLOR_HOT,
            )
            if combined_result.q_cold_min > 1e-3:
                fig_gcc.add_annotation(
                    x=combined_result.q_cold_min, y=T_gcc[-1],
                    text=f"Qc,min = {combined_result.q_cold_min:.1f} kW",
                    showarrow=True, arrowhead=2, ax=40, ay=20,
                    font=dict(size=11, color=COLOR_COLD), arrowcolor=COLOR_COLD,
                )

        for t_pinch in combined_result.pinch_temperatures:
            fig_gcc.add_hline(
                y=t_pinch, line_dash="dash",
                line_color=COLOR_PINCH, line_width=1.5,
                annotation_text=f"Pinch: {t_pinch:.1f} °C",
                annotation_font_size=11, annotation_font_color=COLOR_PINCH,
            )

        fig_gcc.update_layout(**{
            **PLOTLY_LAYOUT_BASE,
            "title": {"text": "Grand Composite Curve - combined models", "x": 0.04, "font": {"size": 15}},
            "xaxis": {**PLOTLY_LAYOUT_BASE["xaxis"], "title": "Net Heat Flow [kW]", "zeroline": True, "zerolinewidth": 2, "zerolinecolor": "#cbd5e1"},
            "yaxis": {**PLOTLY_LAYOUT_BASE["yaxis"], "title": "Temperature [°C]  (shifted)"},
            "height": 460,
        })
        st.plotly_chart(fig_gcc, use_container_width=True)

    # ── Merged stream table ─────────────────────────────────────────────────
    with st.expander("Merged heat streams", expanded=False):
        display_cols = [c for c in [
            "_model", "_unit", "name", "type", "T_in", "T_out", "H_in", "H_out", "heat_cascade",
        ] if c in merged_streams.columns]
        st.dataframe(
            merged_streams[display_cols],
            use_container_width=True,
            hide_index=True,
        )


# ===========================================================================
# Tab 2 - Recovery Potential
# ===========================================================================

with tab_recovery:
    sum_qh = sum(r.q_hot_min for r in individual_results.values())
    sum_qc = sum(r.q_cold_min for r in individual_results.values())
    recovery_qh = sum_qh - combined_result.q_hot_min
    recovery_qc = sum_qc - combined_result.q_cold_min

    # ── Comparison table ────────────────────────────────────────────────────
    table_rows = []
    for name in selected_names:
        if name not in individual_results:
            continue
        res = individual_results[name]
        pinch_str = (
            ", ".join(f"{t:.1f}" for t in res.pinch_temperatures)
            if res.pinch_temperatures else "N/A"
        )
        f_used = f_values.get(name, 1.0)
        table_rows.append({
            "Model": name,
            "f": f_used,
            "Qh,min [kW]": round(res.q_hot_min, 2),
            "Qc,min [kW]": round(res.q_cold_min, 2),
            "Pinch [°C]": pinch_str,
        })

    # Sum row
    table_rows.append({
        "Model": "Σ individual (no integration)",
        "f": "",
        "Qh,min [kW]": round(sum_qh, 2),
        "Qc,min [kW]": round(sum_qc, 2),
        "Pinch [°C]": "",
    })
    # Combined row
    combined_pinch_str = (
        ", ".join(f"{t:.1f}" for t in combined_result.pinch_temperatures)
        if combined_result.pinch_temperatures else "N/A"
    )
    table_rows.append({
        "Model": "Combined (with integration)",
        "f": "",
        "Qh,min [kW]": round(combined_result.q_hot_min, 2),
        "Qc,min [kW]": round(combined_result.q_cold_min, 2),
        "Pinch [°C]": combined_pinch_str,
    })
    # Savings row
    table_rows.append({
        "Model": "♻ Recovered",
        "f": "",
        "Qh,min [kW]": round(recovery_qh, 2),
        "Qc,min [kW]": round(recovery_qc, 2),
        "Pinch [°C]": "",
    })

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    st.divider()

    # ── Synergy metrics ─────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Hot utility recovered", f"{recovery_qh:.2f} kW")
    with c2:
        co2_tpy = recovery_qh * 0.2 * 8760 / 1e6 * 1e3  # t CO2/year
        st.metric("CO2 avoided (est.)", f"{co2_tpy:.1f} t/year",
                  help="Estimate assuming natural gas hot utility at 0.2 kgCO2/kWh, 8 760 h/year full load.")

    # ── Interpretation ──────────────────────────────────────────────────────
    st.divider()
    if recovery_qh > 1.0:
        st.success(
            f"**Integration recovers {recovery_qh:.1f} kW of hot utility.** "
            f"Waste heat from one or more processes can substitute external heating in others. "
            f"See the Stream Candidates tab for specific heat exchanger opportunities."
        )
    elif recovery_qh > 0:
        st.info(
            f"Marginal thermal recovery ({recovery_qh:.2f} kW). "
            "The process temperature levels may not overlap sufficiently at the selected scales. "
            "Try adjusting the capacity factors or adding more models."
        )
    else:
        st.warning(
            "No thermal synergy detected at the selected capacity factors. "
            "The hot and cold streams of these models do not overlap in temperature, "
            "or operate on different sides of the pinch. "
            "Combining them does not reduce external utility requirements."
        )


# ===========================================================================
# Tab 3 - Stream Candidates
# ===========================================================================

with tab_candidates:
    st.caption(
        "Feasible hot→cold stream pairs across models, ranked by estimated heat potential. "
        "Temperature overlap is computed on actual (unshifted) temperatures. "
        "This is a shortlist for HEN design - dTmin feasibility must be verified separately."
    )

    candidates_df = _build_cross_model_candidates(selected_items)

    if candidates_df.empty:
        st.info(
            "No cross-model stream pairing feasible at these temperature levels. "
            "The hot streams of each model do not overlap with the cold streams of the others."
        )
    else:
        # Source-model colour column (HTML badges)
        from utils.styles import badge as _badge

        def _model_badge(name: str) -> str:
            color = _model_color(name, selected_names)
            return _badge(name, color)

        # Display with colour styling
        st.caption(f"{len(candidates_df)} candidate pair(s) found")

        # Style: highlight rows by source model colour (light tint)
        def _row_color(row: pd.Series) -> list[str]:
            color = _model_color(str(row.get("Source model", "")), selected_names)
            # Convert hex to rgba with low opacity
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            bg = f"background-color: rgba({r},{g},{b},0.10)"
            return [bg] * len(row)

        st.dataframe(
            candidates_df.style.apply(_row_color, axis=1),
            use_container_width=True,
            hide_index=True,
        )

        # CSV export
        csv_bytes = candidates_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Export candidates as CSV",
            data=csv_bytes,
            file_name="stream_candidates.csv",
            mime="text/csv",
        )

        # Top candidate callout
        top = candidates_df.iloc[0]
        st.info(
            f"**Top candidate:** "
            f"*{top['Hot stream']}* ({top['Source model']}) → "
            f"*{top['Cold stream']}* ({top['Target model']})  |  "
            f"T overlap: {top['T overlap [°C]']} °C  |  "
            f"Q candidate: **{top['Q candidate [kW]']:.1f} kW**"
        )
