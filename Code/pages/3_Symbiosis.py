"""
Connector Symbiosis page — shows which models produce and consume each connector type.

This is a preliminary view. The analysis becomes meaningful once multiple models
are loaded in the database.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import pandas as pd
import streamlit as st

from utils.constants import DATA_DIR
from utils.loader import load_all_models

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Symbiosis — IETS Task XXIV",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state — initialise models if not already loaded
# ---------------------------------------------------------------------------

if "models" not in st.session_state:
    with st.spinner("Loading model database ..."):
        st.session_state["models"] = load_all_models(DATA_DIR)

models: dict = st.session_state["models"]

# ---------------------------------------------------------------------------
# Build connector matrix
# ---------------------------------------------------------------------------

def _build_connector_matrix(models: dict) -> dict[str, list[dict]]:
    """
    Build a connector compatibility matrix from all unit-level connectors.

    Returns a dict keyed by connector name with a list of
    {model, unit, direction, type, flow_value, flow_unit, T_value} dicts.
    """
    matrix: dict[str, list[dict]] = {}
    for model_name, model in models.items():
        for unit_name in model.unit_names:
            if unit_name not in model.units:
                continue
            unit = model.units[unit_name]
            if unit.connectors.empty:
                continue
            for _, row in unit.connectors.iterrows():
                direction = row.get("direction")
                if str(direction).strip().upper() not in ("IN", "OUT"):
                    continue
                conn_name = row.get("name") or row.get("NAME (ALIAS)", "")
                if not conn_name:
                    continue
                conn_name = str(conn_name).strip()
                if conn_name not in matrix:
                    matrix[conn_name] = []
                matrix[conn_name].append({
                    "model":      model_name,
                    "unit":       unit_name,
                    "direction":  str(direction).strip().upper(),
                    "type":       str(row.get("type") or "").strip(),
                    "flow_value": row.get("flow_value"),
                    "flow_unit":  str(row.get("flow_unit") or "").strip(),
                    "T_value":    row.get("T_value"),
                })
    return matrix


connector_matrix = _build_connector_matrix(models)

# ---------------------------------------------------------------------------
# Flatten to DataFrame
# ---------------------------------------------------------------------------

rows = []
for conn_name, entries in connector_matrix.items():
    for entry in entries:
        rows.append({"connector": conn_name, **entry})

matrix_df = pd.DataFrame(rows) if rows else pd.DataFrame(
    columns=["connector", "model", "unit", "direction", "type", "flow_value", "flow_unit", "T_value"]
)

# ---------------------------------------------------------------------------
# Page content
# ---------------------------------------------------------------------------

st.title("Connector Symbiosis")
st.caption("Compatibility analysis of material and energy connectors across models")

if len(models) < 2:
    st.info(
        "Connector Symbiosis analysis is preliminary. "
        "Full compatibility analysis requires multiple models to be loaded. "
        f"Currently {len(models)} model(s) in the database."
    )

st.markdown(
    """
Each row represents a connector endpoint (IN or OUT) on a specific unit.
Models that **produce** (OUT) and **consume** (IN) the same connector type
are potential symbiosis candidates.
    """
)

st.divider()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Filters")

    direction_filter = st.multiselect(
        "Direction",
        options=["IN", "OUT"],
        default=[],
    )

    conn_type_options = sorted(matrix_df["type"].dropna().unique().tolist()) if not matrix_df.empty else []
    type_filter = st.multiselect(
        "Connector type",
        options=conn_type_options,
        default=[],
    )

    conn_name_options = sorted(matrix_df["connector"].dropna().unique().tolist()) if not matrix_df.empty else []
    name_filter = st.multiselect(
        "Connector name",
        options=conn_name_options,
        default=[],
    )

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

filtered_df = matrix_df.copy()

if direction_filter:
    filtered_df = filtered_df[filtered_df["direction"].isin(direction_filter)]

if type_filter:
    filtered_df = filtered_df[filtered_df["type"].isin(type_filter)]

if name_filter:
    filtered_df = filtered_df[filtered_df["connector"].isin(name_filter)]

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total connector endpoints", len(matrix_df))
with col2:
    n_producers = len(matrix_df[matrix_df["direction"] == "OUT"]) if not matrix_df.empty else 0
    st.metric("Producers (OUT)", n_producers)
with col3:
    n_consumers = len(matrix_df[matrix_df["direction"] == "IN"]) if not matrix_df.empty else 0
    st.metric("Consumers (IN)", n_consumers)

st.divider()

# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------

st.subheader("Connector Matrix")
st.caption(f"Showing {len(filtered_df)} of {len(matrix_df)} connector endpoints")

if filtered_df.empty:
    st.info("No connectors match the current filters.")
else:
    def _style_direction(val: str) -> str:
        if str(val).upper() == "OUT":
            return "background-color: #FFF8E1; color: #5D4037;"
        if str(val).upper() == "IN":
            return "background-color: #E8F5E9; color: #1B5E20;"
        return ""

    display_df = filtered_df.reset_index(drop=True)
    st.dataframe(
        display_df.style.map(_style_direction, subset=["direction"]),
        use_container_width=True,
        hide_index=True,
    )

# ---------------------------------------------------------------------------
# Symbiosis candidates
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Potential Symbiosis Pairs")
st.caption(
    "Connector names that appear as both OUT (producer) and IN (consumer) across different models."
)

if not matrix_df.empty:
    producers = set(matrix_df[matrix_df["direction"] == "OUT"]["connector"].tolist())
    consumers = set(matrix_df[matrix_df["direction"] == "IN"]["connector"].tolist())
    candidates = sorted(producers & consumers)

    if candidates:
        for conn_name in candidates:
            with st.container(border=True):
                st.markdown(f"**{conn_name}**")
                prod_rows = matrix_df[
                    (matrix_df["connector"] == conn_name) & (matrix_df["direction"] == "OUT")
                ]
                cons_rows = matrix_df[
                    (matrix_df["connector"] == conn_name) & (matrix_df["direction"] == "IN")
                ]

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(
                        '<p style="color:#5D4037;font-weight:600;font-size:12px;">PRODUCERS (OUT)</p>',
                        unsafe_allow_html=True,
                    )
                    for _, r in prod_rows.iterrows():
                        st.markdown(
                            f'<p style="margin:2px 0;font-size:13px;">'
                            f'{r["model"]} / {r["unit"]}</p>',
                            unsafe_allow_html=True,
                        )
                with c2:
                    st.markdown(
                        '<p style="color:#1B5E20;font-weight:600;font-size:12px;">CONSUMERS (IN)</p>',
                        unsafe_allow_html=True,
                    )
                    for _, r in cons_rows.iterrows():
                        st.markdown(
                            f'<p style="margin:2px 0;font-size:13px;">'
                            f'{r["model"]} / {r["unit"]}</p>',
                            unsafe_allow_html=True,
                        )
    else:
        st.info(
            "No symbiosis candidates found. "
            "This is expected with a single model — add more models to discover matches."
        )
else:
    st.info("No connector data available.")
