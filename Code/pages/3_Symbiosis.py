"""
Connector Symbiosis page — scalable cross-model compatibility analysis.

Data source: model.external_connectors (top-level EXTERNAL CONNECTORS section)
cross-referenced with unit connector directions (IN/OUT).
Only external connectors participate in cross-model UID matching;
internal connectors are excluded.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import hashlib

import streamlit as st
from streamlit_flow import (
    StreamlitFlowEdge,
    StreamlitFlowNode,
    StreamlitFlowState,
    streamlit_flow,
)

_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from utils.categories import CATEGORIES
from utils.constants import DATA_DIR
from utils.loader import load_all_models
from utils.styles import inject_css

inject_css()

# ---------------------------------------------------------------------------
# Load models
# ---------------------------------------------------------------------------

if "models" not in st.session_state:
    with st.spinner("Loading model database ..."):
        st.session_state["models"] = load_all_models(DATA_DIR)

models: dict = st.session_state["models"]

# ---------------------------------------------------------------------------
# Color palettes
# ---------------------------------------------------------------------------

_CAT_PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a",
]
_UID_PALETTE = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
    "#a65628", "#f781bf", "#999999", "#66c2a5", "#fc8d62",
    "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3",
]
_CATEGORY_COLOR = {
    c["slug"]: _CAT_PALETTE[i % len(_CAT_PALETTE)]
    for i, c in enumerate(CATEGORIES)
}
_UID_NODE_COLOR = "#e8e8e8"
_DEFAULT_COLOR  = "#7f7f7f"


def _model_color(model_name: str) -> str:
    m = models.get(model_name)
    if m is None:
        return _DEFAULT_COLOR
    return _CATEGORY_COLOR.get(m.category, _DEFAULT_COLOR)


# ---------------------------------------------------------------------------
# Core data builder
# ---------------------------------------------------------------------------

def _uid_from_ext_row(row: pd.Series) -> str:
    return str(
        row.get("UID") or row.get("Unique Identifier Number, UID") or ""
    ).strip().upper()


def _build_symbiosis_data(
    models: dict,
    uid_filter: set[str] | None = None,
    cat_filter: set[str] | None = None,
) -> tuple[list[dict], dict[str, dict], list[tuple]]:
    """
    Returns:
      rows    — flat list[{Model, UID, Direction, Type, Category}]
      uid_map — {uid: {"out": [...], "in": [...]}}
      edges   — [(producer, consumer, uid), ...]
    """
    rows: list[dict] = []
    uid_map: dict[str, dict] = {}

    for model_name, model in models.items():
        if cat_filter and model.category not in cat_filter:
            continue
        ext = model.external_connectors
        if ext is None or ext.empty:
            continue

        name_to_uid: dict[str, str] = {}
        for _, erow in ext.iterrows():
            uid  = _uid_from_ext_row(erow)
            name = str(erow.get("NAME (ALIAS)") or "").strip()
            if uid and name:
                name_to_uid[name] = uid

        if not name_to_uid:
            continue

        seen: set[tuple[str, str]] = set()
        for unit_name in model.unit_names:
            unit = model.units.get(unit_name)
            if unit is None or unit.connectors is None or unit.connectors.empty:
                continue
            for _, crow in unit.connectors.iterrows():
                conn_name = str(crow.get("name") or "").strip()
                direction = str(crow.get("direction") or "").strip().upper()
                if direction not in ("IN", "OUT"):
                    continue
                uid = name_to_uid.get(conn_name)
                if not uid:
                    continue
                if uid_filter and uid not in uid_filter:
                    continue
                key = (uid, direction)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "Model":     model_name,
                    "UID":       uid,
                    "Direction": direction,
                    "Type":      str(crow.get("type") or "").strip(),
                    "Category":  model.category or "",
                })
                bucket  = uid_map.setdefault(uid, {"out": [], "in": []})
                dir_key = "out" if direction == "OUT" else "in"
                if model_name not in bucket[dir_key]:
                    bucket[dir_key].append(model_name)

    edges: list[tuple] = []
    for uid, bucket in uid_map.items():
        for producer in bucket["out"]:
            for consumer in bucket["in"]:
                if producer != consumer:
                    edges.append((producer, consumer, uid))

    return rows, uid_map, edges


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

_all_rows, _, _ = _build_symbiosis_data(models)
_all_uids        = sorted({r["UID"]      for r in _all_rows})
_all_cats        = sorted({r["Category"] for r in _all_rows if r["Category"]})
_all_model_names = sorted({r["Model"]    for r in _all_rows})
_cat_display     = {c["slug"]: c["name"] for c in CATEGORIES}

with st.sidebar:
    st.header("Symbiosis")

    layout_mode = st.radio(
        "Graph layout",
        options=["Model → Model", "UID hub-and-spoke"],
        index=0,
        help=(
            "Model → Model: directed edges between producer and consumer models.\n"
            "UID hub-and-spoke: UID resource nodes act as intermediaries."
        ),
    )

    uid_filter_sel = st.multiselect(
        "Filter by UID",
        options=_all_uids,
        default=[],
        help="Leave empty to show all UIDs.",
    )
    cat_filter_sel = st.multiselect(
        "Filter by category",
        options=_all_cats,
        format_func=lambda s: _cat_display.get(s, s),
        default=[],
        help="Leave empty to show all categories.",
    )

uid_filter = set(uid_filter_sel) if uid_filter_sel else None
cat_filter = set(cat_filter_sel) if cat_filter_sel else None

# ---------------------------------------------------------------------------
# Build data (with UID / category filters)
# ---------------------------------------------------------------------------

rows, uid_map, edges = _build_symbiosis_data(models, uid_filter, cat_filter)
flat_df = pd.DataFrame(rows) if rows else pd.DataFrame(
    columns=["Model", "UID", "Direction", "Type", "Category"]
)

# Global UID → color mapping (stable across modes; keyed on all possible UIDs)
_uid_keys = sorted({r["UID"] for r in rows})
uid_color  = {uid: _UID_PALETTE[i % len(_UID_PALETTE)] for i, uid in enumerate(_uid_keys)}

# ---------------------------------------------------------------------------
# Page header + metrics
# ---------------------------------------------------------------------------

st.title("Connector Symbiosis")
st.caption(
    "Cross-model compatibility via external connector UID matching. "
    "Arrows show resource flow: producer (OUT) → consumer (IN)."
)

n_models = len({r["Model"] for r in rows})
n_uids   = len(uid_map)
n_pairs  = len({(p, c) for p, c, _ in edges})

c1, c2, c3 = st.columns(3)
c1.metric("Models with external connectors", n_models)
c2.metric("Unique UIDs",                     n_uids)
c3.metric("Symbiosis pairs",                 n_pairs)

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_graph, tab_matrix, tab_table, tab_wip, tab_flow = st.tabs(
    ["Network Graph", "Symbiosis Matrix", "Connector Table", "Network Graph (WIP)", "ReactFlow (WIP)"]
)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Network Graph
# ═══════════════════════════════════════════════════════════════════════════

with tab_graph:
    # ── Checkbox filters (Excel-style: Select All / Clear All + per-item) ─
    _graph_model_options = sorted({r["Model"] for r in rows})
    _graph_uid_options   = sorted({r["UID"]   for r in rows})

    flt_col1, flt_col2 = st.columns(2)

    with flt_col1:
        with st.expander("**Models**", expanded=True):
            _mc1, _mc2 = st.columns(2)
            if _mc1.button("Select all", key="m_sel_all", use_container_width=True):
                for _m in _graph_model_options:
                    st.session_state[f"cb_m_{_m}"] = True
            if _mc2.button("Clear all", key="m_clr_all", use_container_width=True):
                for _m in _graph_model_options:
                    st.session_state[f"cb_m_{_m}"] = False
            selected_models = []
            for _m in _graph_model_options:
                if f"cb_m_{_m}" not in st.session_state:
                    st.session_state[f"cb_m_{_m}"] = True
                if st.checkbox(_m, key=f"cb_m_{_m}"):
                    selected_models.append(_m)

    with flt_col2:
        with st.expander("**UIDs**", expanded=True):
            _uc1, _uc2 = st.columns(2)
            if _uc1.button("Select all", key="u_sel_all", use_container_width=True):
                for _u in _graph_uid_options:
                    st.session_state[f"cb_u_{_u}"] = True
            if _uc2.button("Clear all", key="u_clr_all", use_container_width=True):
                for _u in _graph_uid_options:
                    st.session_state[f"cb_u_{_u}"] = False
            selected_uids = []
            for _u in _graph_uid_options:
                if f"cb_u_{_u}" not in st.session_state:
                    st.session_state[f"cb_u_{_u}"] = True
                if st.checkbox(_u, key=f"cb_u_{_u}"):
                    selected_uids.append(_u)

    _sel_model_set = set(selected_models)
    _sel_uid_set   = set(selected_uids)
    graph_rows  = [r for r in rows
                   if r["Model"] in _sel_model_set and r["UID"] in _sel_uid_set]
    graph_edges = [(p, c, uid) for p, c, uid in edges
                   if p in _sel_model_set and c in _sel_model_set and uid in _sel_uid_set]

    if not graph_rows:
        st.info("No connector data to display. Select at least one model and one UID.")
    else:
        # ── Build layout graph (undirected, just for positions) ──────────
        G_layout = nx.Graph()

        if layout_mode == "Model → Model":
            for r in graph_rows:
                G_layout.add_node(r["Model"])
            for p, c, _ in graph_edges:
                G_layout.add_edge(p, c)
        else:
            for r in graph_rows:
                G_layout.add_node(r["Model"])
                G_layout.add_node(r["UID"])
                G_layout.add_edge(r["Model"], r["UID"])

        k   = 3.5 / math.sqrt(max(len(G_layout.nodes()), 1))
        pos = nx.spring_layout(G_layout, seed=42, k=k)

        # ── Edge traces (one per UID, each with its own color) ───────────
        edge_traces: list[go.Scatter] = []
        arrow_anns: list[dict]        = []
        mid_x, mid_y, mid_text        = [], [], []

        if layout_mode == "Model → Model":
            uid_edge_groups: dict[str, list] = defaultdict(list)
            for p, c, uid in graph_edges:
                uid_edge_groups[uid].append((p, c))

            for uid, pairs in sorted(uid_edge_groups.items()):
                color = uid_color.get(uid, _DEFAULT_COLOR)
                ex, ey = [], []
                for p, c in pairs:
                    x0, y0 = pos[p]
                    x1, y1 = pos[c]
                    ex += [x0, x1, None]
                    ey += [y0, y1, None]
                    mid_x.append((x0 + x1) / 2)
                    mid_y.append((y0 + y1) / 2)
                    mid_text.append(f"<b>{uid}</b><br>{p} → {c}")
                    arrow_anns.append(dict(
                        x=x1, y=y1, ax=x0, ay=y0,
                        xref="x", yref="y", axref="x", ayref="y",
                        showarrow=True,
                        arrowhead=3, arrowsize=1.2, arrowwidth=2.0,
                        arrowcolor=color,
                        text="",
                    ))
                edge_traces.append(go.Scatter(
                    x=ex, y=ey,
                    mode="lines",
                    line=dict(width=2.5, color=color),
                    name=uid,
                    legendgroup=uid,
                    showlegend=True,
                    hoverinfo="none",
                ))

        else:  # hub-and-spoke
            hub_groups: dict[str, list] = defaultdict(list)
            for r in graph_rows:
                m, uid, direction = r["Model"], r["UID"], r["Direction"]
                src, tgt = (m, uid) if direction == "OUT" else (uid, m)
                hub_groups[uid].append((src, tgt))

            for uid, pairs in sorted(hub_groups.items()):
                color = uid_color.get(uid, _DEFAULT_COLOR)
                ex, ey = [], []
                for src, tgt in pairs:
                    x0, y0 = pos[src]
                    x1, y1 = pos[tgt]
                    ex += [x0, x1, None]
                    ey += [y0, y1, None]
                    mid_x.append((x0 + x1) / 2)
                    mid_y.append((y0 + y1) / 2)
                    direction_label = "OUT" if src in {r["Model"] for r in graph_rows} else "IN"
                    mid_text.append(f"<b>{uid}</b><br>{src} → {tgt}")
                    arrow_anns.append(dict(
                        x=x1, y=y1, ax=x0, ay=y0,
                        xref="x", yref="y", axref="x", ayref="y",
                        showarrow=True,
                        arrowhead=3, arrowsize=1.2, arrowwidth=2.0,
                        arrowcolor=color,
                        text="",
                    ))
                edge_traces.append(go.Scatter(
                    x=ex, y=ey,
                    mode="lines",
                    line=dict(width=2.5, color=color),
                    name=uid,
                    legendgroup=uid,
                    showlegend=True,
                    hoverinfo="none",
                ))

        # ── Invisible midpoint hover trace ───────────────────────────────
        mid_trace = go.Scatter(
            x=mid_x, y=mid_y,
            mode="markers",
            marker=dict(size=12, opacity=0),
            hoverinfo="text",
            hovertext=mid_text,
            showlegend=False,
        )

        # ── Node traces ──────────────────────────────────────────────────
        node_traces: list[go.Scatter] = []

        if layout_mode == "Model → Model":
            all_nodes = list(G_layout.nodes())
            node_traces.append(go.Scatter(
                x=[pos[n][0] for n in all_nodes],
                y=[pos[n][1] for n in all_nodes],
                mode="markers+text",
                text=[f"<b>{n}</b>" for n in all_nodes],
                textposition="top center",
                textfont=dict(size=12, color="#1a1a1a", family="Arial"),
                marker=dict(
                    size=40,
                    color=[_model_color(n) for n in all_nodes],
                    line=dict(width=3, color="#ffffff"),
                    opacity=0.92,
                ),
                hoverinfo="text",
                hovertext=[
                    f"<b>{n}</b><br>Category: {models[n].category if n in models else ''}"
                    for n in all_nodes
                ],
                showlegend=False,
            ))

        else:  # hub-and-spoke
            model_nodes = [n for n in G_layout.nodes()
                           if n in {r["Model"] for r in graph_rows}]
            uid_nodes   = [n for n in G_layout.nodes()
                           if n not in {r["Model"] for r in graph_rows}]

            node_traces.append(go.Scatter(
                x=[pos[n][0] for n in model_nodes],
                y=[pos[n][1] for n in model_nodes],
                mode="markers+text",
                text=[f"<b>{n}</b>" for n in model_nodes],
                textposition="top center",
                textfont=dict(size=12, color="#1a1a1a", family="Arial"),
                marker=dict(
                    size=40,
                    color=[_model_color(n) for n in model_nodes],
                    symbol="circle",
                    line=dict(width=3, color="#ffffff"),
                    opacity=0.92,
                ),
                hoverinfo="text",
                hovertext=[
                    f"<b>{n}</b><br>Category: {models[n].category if n in models else ''}"
                    for n in model_nodes
                ],
                name="Models",
                showlegend=False,
            ))
            node_traces.append(go.Scatter(
                x=[pos[n][0] for n in uid_nodes],
                y=[pos[n][1] for n in uid_nodes],
                mode="markers+text",
                text=[f"<b>{n}</b>" for n in uid_nodes],
                textposition="bottom center",
                textfont=dict(size=10, color="#444444", family="Arial"),
                marker=dict(
                    size=26,
                    color=[uid_color.get(n, _UID_NODE_COLOR) for n in uid_nodes],
                    symbol="diamond",
                    line=dict(width=2, color="#ffffff"),
                    opacity=0.85,
                ),
                hoverinfo="text",
                name="UIDs",
                showlegend=False,
            ))

        fig = go.Figure(
            data=edge_traces + [mid_trace] + node_traces,
            layout=go.Layout(
                height=660,
                showlegend=True,
                legend=dict(
                    title=dict(text="<b>UID</b>", font=dict(size=12, color="black")),
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#cccccc",
                    borderwidth=1,
                    font=dict(size=11, color="black"),
                    itemclick=False,
                    itemdoubleclick=False,
                ),
                hovermode="closest",
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                annotations=arrow_anns,
                paper_bgcolor="#f8f9fa",
                plot_bgcolor="#f8f9fa",
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

        if layout_mode == "Model → Model" and not graph_edges:
            st.info("No symbiosis edges to display — models share no OUT→IN UIDs.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Symbiosis Matrix
# ═══════════════════════════════════════════════════════════════════════════

with tab_matrix:
    if not edges:
        st.info("No symbiosis pairs found with the current filters.")
    else:
        pair_rows = [
            {"Producer (OUT)": p, "Consumer (IN)": c, "UID": uid}
            for p, c, uid in edges
        ]
        pair_df = pd.DataFrame(pair_rows)

        # ── Count pivot ───────────────────────────────────────────────────
        count_pivot = (
            pair_df.groupby(["Producer (OUT)", "Consumer (IN)"])["UID"]
            .count()
            .unstack(fill_value=0)
        )

        # ── UID name hover texts ──────────────────────────────────────────
        uid_name_pivot: dict[tuple, str] = {}
        for p, c, uid in edges:
            uid_name_pivot.setdefault((p, c), []).append(uid)

        hover_z = []
        for prod in count_pivot.index:
            row_hover = []
            for cons in count_pivot.columns:
                uids = uid_name_pivot.get((prod, cons), [])
                if uids:
                    row_hover.append(
                        f"<b>{prod}</b> → <b>{cons}</b><br>"
                        + "<br>".join(f"• {u}" for u in sorted(set(uids)))
                    )
                else:
                    row_hover.append("")
            hover_z.append(row_hover)

        fig_heat = go.Figure(go.Heatmap(
            z=count_pivot.values.tolist(),
            x=count_pivot.columns.tolist(),
            y=count_pivot.index.tolist(),
            colorscale="Blues",
            showscale=False,
            text=count_pivot.values.tolist(),
            texttemplate="%{text}",
            customdata=hover_z,
            hovertemplate="%{customdata}<extra></extra>",
        ))
        fig_heat.update_layout(
            height=max(320, 36 * len(count_pivot) + 180),
            xaxis_title="Consumer (IN)",
            yaxis_title="Producer (OUT)",
            xaxis=dict(tickangle=-35),
            margin=dict(l=20, r=20, t=30, b=100),
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        st.caption("Cell = number of shared UIDs — hover for details")
        st.plotly_chart(fig_heat, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Connector Table
# ═══════════════════════════════════════════════════════════════════════════

with tab_table:
    if flat_df.empty:
        st.info("No external connector data found with the current filters.")
    else:
        dir_sel = st.multiselect(
            "Direction",
            ["IN", "OUT"],
            default=[],
            key="tbl_dir_filter",
            help="Leave empty to show all.",
        )
        tbl_df = flat_df.copy()
        if dir_sel:
            tbl_df = tbl_df[tbl_df["Direction"].isin(dir_sel)]

        st.caption(
            f"Showing {len(tbl_df)} of {len(flat_df)} external connector endpoints "
            "(internal connectors excluded)"
        )

        def _style_dir(val: str) -> str:
            if val == "OUT":
                return "background-color:#FFF8E1;color:#5D4037"
            if val == "IN":
                return "background-color:#E8F5E9;color:#1B5E20"
            return ""

        st.dataframe(
            tbl_df[["Model", "UID", "Direction", "Type", "Category"]]
            .reset_index(drop=True)
            .style.map(_style_dir, subset=["Direction"]),
            use_container_width=True,
            hide_index=True,
        )

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — Network Graph (WIP)  [networkX MultiDiGraph + matplotlib]
# ═══════════════════════════════════════════════════════════════════════════


def _assign_rads(graph_edges: list[tuple]) -> dict[tuple, float]:
    pair_groups: dict[tuple, list] = defaultdict(list)
    for p, c, uid in graph_edges:
        pair_groups[(p, c)].append(uid)
    rad_map: dict[tuple, float] = {}
    for (u, v), uids in pair_groups.items():
        n = len(uids)
        if n == 1:
            rads = [0.15]
        elif n == 2:
            rads = [0.2, -0.2]
        elif n == 3:
            rads = [0.25, 0.0, -0.25]
        else:
            rads = [round(0.4 - i * 0.8 / (n - 1), 3) for i in range(n)]
        for i, uid in enumerate(uids):
            rad_map[(u, v, i)] = rads[i]
    return rad_map


with tab_wip:
    if not graph_rows:
        st.info("No connector data to display. Select at least one model and one UID.")
    else:
        G_wip = nx.MultiDiGraph()

        if layout_mode == "Model → Model":
            for r in graph_rows:
                G_wip.add_node(r["Model"])
            rad_map = _assign_rads(graph_edges)
            pair_counter: dict[tuple, int] = defaultdict(int)
            for p, c, uid in graph_edges:
                idx = pair_counter[(p, c)]
                G_wip.add_edge(
                    p, c, key=f"{uid}_{idx}",
                    uid=uid,
                    color=uid_color.get(uid, _DEFAULT_COLOR),
                    rad=rad_map[(p, c, idx)],
                )
                pair_counter[(p, c)] += 1
            model_nodes_wip = list(G_wip.nodes())
            uid_nodes_wip: list = []

        else:  # hub-and-spoke
            for r in graph_rows:
                G_wip.add_node(r["Model"])
                G_wip.add_node(r["UID"])
            for r in graph_rows:
                m, uid, direction = r["Model"], r["UID"], r["Direction"]
                color = uid_color.get(uid, _DEFAULT_COLOR)
                if direction == "OUT":
                    G_wip.add_edge(m, uid, key=f"{m}_OUT_{uid}", uid=uid, color=color, rad=0.15)
                else:
                    G_wip.add_edge(uid, m, key=f"{uid}_IN_{m}", uid=uid, color=color, rad=0.15)
            _model_set_wip = {r["Model"] for r in graph_rows}
            model_nodes_wip = [n for n in G_wip.nodes() if n in _model_set_wip]
            uid_nodes_wip   = [n for n in G_wip.nodes() if n not in _model_set_wip]

        n_wip   = max(len(G_wip.nodes()), 1)
        pos_wip = nx.spring_layout(G_wip, seed=42, k=3.5 / math.sqrt(n_wip))

        if layout_mode == "Model → Model" and G_wip.number_of_edges() == 0:
            st.info("No symbiosis edges — models share no OUT→IN UIDs. Isolated nodes shown.")

        fig_wip, ax_wip = plt.subplots(figsize=(14, 10))
        ax_wip.set_facecolor("#f8f9fa")
        fig_wip.patch.set_facecolor("#f8f9fa")
        ax_wip.axis("off")

        for u, v, k, data in G_wip.edges(keys=True, data=True):
            nx.draw_networkx_edges(
                G_wip, pos_wip, edgelist=[(u, v, k)], ax=ax_wip,
                edge_color=[data["color"]],
                connectionstyle=f"arc3,rad={data['rad']}",
                arrowsize=20, width=2.0, arrows=True,
                min_source_margin=15, min_target_margin=15,
            )

        nx.draw_networkx_nodes(
            G_wip, pos_wip, nodelist=model_nodes_wip, ax=ax_wip,
            node_color=[_model_color(n) for n in model_nodes_wip],
            node_size=1200, node_shape="o", linewidths=2, edgecolors="#ffffff",
        )
        nx.draw_networkx_labels(
            G_wip, pos_wip,
            labels={n: n for n in model_nodes_wip}, ax=ax_wip,
            font_size=9, font_weight="bold", font_color="#1a1a1a",
        )

        if uid_nodes_wip:
            nx.draw_networkx_nodes(
                G_wip, pos_wip, nodelist=uid_nodes_wip, ax=ax_wip,
                node_color=[uid_color.get(n, _UID_NODE_COLOR) for n in uid_nodes_wip],
                node_size=400, node_shape="D", linewidths=1.5, edgecolors="#ffffff",
            )
            nx.draw_networkx_labels(
                G_wip, pos_wip,
                labels={n: n for n in uid_nodes_wip}, ax=ax_wip,
                font_size=8, font_color="#444444",
            )

        visible_uids = sorted({data["uid"] for _, _, _, data in G_wip.edges(keys=True, data=True)})
        legend_handles = [
            mpatches.Patch(color=uid_color.get(uid, _DEFAULT_COLOR), label=uid)
            for uid in visible_uids
        ]
        if legend_handles:
            ax_wip.legend(
                handles=legend_handles, title="UID", loc="upper right",
                framealpha=0.9, edgecolor="#cccccc", fontsize=9, title_fontsize=10,
            )

        plt.tight_layout()
        st.pyplot(fig_wip, use_container_width=True)
        plt.close(fig_wip)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — ReactFlow (WIP)  [streamlit-flow-component / ReactFlow]
# ═══════════════════════════════════════════════════════════════════════════

with tab_flow:
    if not graph_rows:
        st.info("No connector data to display. Select at least one model and one UID.")
    else:
        _fp = hashlib.md5(
            (str(sorted((r["Model"], r["UID"], r["Direction"]) for r in graph_rows)) + layout_mode).encode()
        ).hexdigest()

        if st.session_state.get("_flow_fp") != _fp:
            G_rf = nx.MultiDiGraph()

            if layout_mode == "Model → Model":
                for r in graph_rows:
                    G_rf.add_node(r["Model"])
                for p, c, uid in graph_edges:
                    G_rf.add_edge(p, c, key=f"{uid}_{p}_{c}", uid=uid)
                _rf_model_nodes = list(G_rf.nodes())
                _rf_uid_nodes: list = []

            else:  # hub-and-spoke
                for r in graph_rows:
                    G_rf.add_node(r["Model"])
                    G_rf.add_node(r["UID"])
                for r in graph_rows:
                    m, uid, direction = r["Model"], r["UID"], r["Direction"]
                    if direction == "OUT":
                        G_rf.add_edge(m, uid, key=f"{m}_OUT_{uid}", uid=uid)
                    else:
                        G_rf.add_edge(uid, m, key=f"{uid}_IN_{m}", uid=uid)
                _model_set_rf = {r["Model"] for r in graph_rows}
                _rf_model_nodes = [n for n in G_rf.nodes() if n in _model_set_rf]
                _rf_uid_nodes   = [n for n in G_rf.nodes() if n not in _model_set_rf]

            n_rf   = max(len(G_rf.nodes()), 1)
            pos_rf = nx.spring_layout(G_rf, seed=42, k=3.5 / math.sqrt(n_rf))

            _SCALE, _OFFSET_X, _OFFSET_Y = 500, 600, 400

            sf_nodes: list[StreamlitFlowNode] = []
            for node_id in _rf_model_nodes:
                x, y = pos_rf[node_id]
                sf_nodes.append(StreamlitFlowNode(
                    id=str(node_id),
                    pos=(x * _SCALE + _OFFSET_X, y * _SCALE + _OFFSET_Y),
                    data={"label": node_id},
                    node_type="default",
                    style={
                        "background": _model_color(node_id),
                        "color": "#ffffff",
                        "borderRadius": "8px",
                        "fontWeight": "bold",
                        "fontSize": "12px",
                        "padding": "8px 12px",
                        "border": "2px solid rgba(255,255,255,0.4)",
                        "minWidth": "120px",
                        "textAlign": "center",
                    },
                ))
            for node_id in _rf_uid_nodes:
                x, y = pos_rf[node_id]
                sf_nodes.append(StreamlitFlowNode(
                    id=str(node_id),
                    pos=(x * _SCALE + _OFFSET_X, y * _SCALE + _OFFSET_Y),
                    data={"label": node_id},
                    node_type="default",
                    style={
                        "background": uid_color.get(node_id, _UID_NODE_COLOR),
                        "color": "#333333",
                        "borderRadius": "4px",
                        "fontSize": "11px",
                        "padding": "6px 10px",
                        "border": "1.5px solid #aaaaaa",
                        "minWidth": "80px",
                        "textAlign": "center",
                    },
                ))

            sf_edges: list[StreamlitFlowEdge] = []
            for src, tgt, key, data in G_rf.edges(keys=True, data=True):
                uid = data.get("uid", "")
                sf_edges.append(StreamlitFlowEdge(
                    id=key,
                    source=str(src),
                    target=str(tgt),
                    animated=True,
                    marker_end={"type": "arrowclosed"},
                    label=uid,
                    style={
                        "stroke": uid_color.get(uid, _DEFAULT_COLOR),
                        "strokeWidth": 2,
                    },
                ))

            st.session_state["_flow_fp"]    = _fp
            st.session_state["_flow_state"] = StreamlitFlowState(nodes=sf_nodes, edges=sf_edges)

        updated_state = streamlit_flow(
            "flow_wip",
            st.session_state["_flow_state"],
            height=620,
            fit_view=True,
            show_minimap=True,
            show_controls=True,
            animate_new_edges=True,
        )
        st.session_state["_flow_state"] = updated_state
