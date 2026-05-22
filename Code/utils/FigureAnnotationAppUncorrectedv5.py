"""
CC/GCC Interactive Annotation Tool  (v3)
=========================================
- TRUE click-anywhere via JS handler on Plotly's drag overlay
- Annotations saved per data configuration (fingerprint hash)
- Free-text label entry

Usage:  python app.py  ->  http://127.0.0.1:8050
"""

import json
import hashlib
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from dash import (Dash, html, dcc, Input, Output, State,
                  callback_context, ALL, clientside_callback)
from dash.exceptions import PreventUpdate

# ---------------------------------------------------------------------------
# Annotation persistence  (keyed by data fingerprint)
# ---------------------------------------------------------------------------
ANNOTATIONS_DIR = Path("annotations")
ANNOTATIONS_DIR.mkdir(exist_ok=True)


def data_fingerprint(hot_streams, cold_streams):
    raw = json.dumps({"h": hot_streams, "c": cold_streams}, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def load_annotations(plot_type, fingerprint):
    p = ANNOTATIONS_DIR / f"{plot_type}_{fingerprint}.json"
    if p.exists():
        with open(p, "r") as f:
            return json.load(f).get("annotations", [])
    return []


def save_annotations(plot_type, fingerprint, annotations):
    p = ANNOTATIONS_DIR / f"{plot_type}_{fingerprint}.json"
    with open(p, "w") as f:
        json.dump({"plot": plot_type, "fingerprint": fingerprint,
                    "annotations": annotations}, f, indent=2)


def annotations_to_plotly(annotations):
    out = []
    for ann in annotations:
        out.append(dict(
            x=ann["x"], y=ann["y"], text=ann.get("text", ""),
            showarrow=ann.get("arrow", True),
            arrowhead=2, arrowsize=1.2, arrowwidth=1.5,
            arrowcolor="#c0392b",
            ax=ann.get("ax", 0), ay=ann.get("ay", -35),
            font=dict(size=12, color="#2C3E50",
                      family="JetBrains Mono, monospace"),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="#bdc3c7", borderwidth=1, borderpad=4,
        ))
    return out


# =====================================================================
#  PINCH ENGINE  (per-stream dTmin contributions)
# =====================================================================

PHASE_CHANGE_DT = 0.1


def compute_pinch(hot_streams, cold_streams):
    hot = []
    for s in hot_streams:
        Tin, Tout, Q, dt_c = s
        if abs(Tin - Tout) < 1e-6:
            Tin = Tin + PHASE_CHANGE_DT
        dT = abs(Tin - Tout)
        hot.append({'Tin': Tin, 'Tout': Tout, 'Q': Q, 'CP': Q / dT,
                     'dt_c': dt_c,
                     'Ts_min': min(Tin, Tout) - dt_c,
                     'Ts_max': max(Tin, Tout) - dt_c})
    cold = []
    for s in cold_streams:
        Tin, Tout, Q, dt_c = s
        if abs(Tin - Tout) < 1e-6:
            Tout = Tout + PHASE_CHANGE_DT
        dT = abs(Tin - Tout)
        cold.append({'Tin': Tin, 'Tout': Tout, 'Q': Q, 'CP': Q / dT,
                      'dt_c': dt_c,
                      'Ts_min': min(Tin, Tout) + dt_c,
                      'Ts_max': max(Tin, Tout) + dt_c})

    def build_composite(streams):
        temps = sorted({s['Ts_min'] for s in streams} |
                       {s['Ts_max'] for s in streams})
        T, H = [temps[0]], [0.0]
        for i in range(len(temps) - 1):
            T_lo, T_hi = temps[i], temps[i + 1]
            cp = sum(s['CP'] for s in streams
                     if s['Ts_min'] <= T_lo + 1e-9 and
                        s['Ts_max'] >= T_hi - 1e-9)
            T.append(T_hi)
            H.append(H[-1] + cp * (T_hi - T_lo))
        return np.array(H), np.array(T)

    hot_H, hot_T = build_composite(hot)
    cold_H, cold_T = build_composite(cold)
    total_hot, total_cold = hot_H[-1], cold_H[-1]

    min_offset = max(0.0, total_hot - total_cold)

    def min_vertical_gap(offset):
        cH = cold_H + offset
        H_lo, H_hi = max(hot_H[0], cH[0]), min(hot_H[-1], cH[-1])
        if H_lo >= H_hi:
            return 999.0
        grid = np.linspace(H_lo, H_hi, 5000)
        return np.min(np.interp(grid, hot_H, hot_T) -
                      np.interp(grid, cH, cold_T))

    gap = min_vertical_gap(min_offset)
    if gap > 1e-3:
        offset_final, is_threshold = min_offset, True
    elif gap < -1e-6:
        lo_s, hi_s = min_offset, min_offset + 5 * max(total_hot, total_cold)
        for _ in range(200):
            mid = (lo_s + hi_s) / 2
            if min_vertical_gap(mid) < 0:
                lo_s = mid
            else:
                hi_s = mid
        offset_final, is_threshold = (lo_s + hi_s) / 2, False
    else:
        offset_final, is_threshold = min_offset, False

    cold_H_final = cold_H + offset_final
    Qh = cold_H_final[-1] - hot_H[-1]
    Qc = cold_H_final[0] - hot_H[0]

    overlap_lo = max(hot_H[0], cold_H_final[0])
    overlap_hi = min(hot_H[-1], cold_H_final[-1])
    pinch_T_star = pinch_h = None
    pinch_gap = 999.0
    if overlap_lo < overlap_hi:
        grid = np.linspace(overlap_lo, overlap_hi, 5000)
        Th = np.interp(grid, hot_H, hot_T)
        Tc = np.interp(grid, cold_H_final, cold_T)
        gaps = Th - Tc
        idx = np.argmin(gaps)
        pinch_T_star = float(Th[idx])
        pinch_gap = float(gaps[idx])
        pinch_h = float(grid[idx])

    all_T_star = sorted(set(hot_T.tolist() + cold_T.tolist()), reverse=True)

    def interp_ext(Ts, cT, cH):
        if Ts < cT[0]: return float(cH[0])
        if Ts > cT[-1]: return float(cH[-1])
        return float(np.interp(Ts, cT, cH))

    gcc_cascade = [0.0]
    for i in range(len(all_T_star) - 1):
        Thi, Tlo = all_T_star[i], all_T_star[i + 1]
        dH_h = interp_ext(Thi, hot_T, hot_H) - interp_ext(Tlo, hot_T, hot_H)
        dH_c = interp_ext(Thi, cold_T, cold_H_final) - \
               interp_ext(Tlo, cold_T, cold_H_final)
        gcc_cascade.append(gcc_cascade[-1] + dH_h - dH_c)

    gcc_T = np.array(all_T_star)
    gcc_dQ = np.array(gcc_cascade) - min(gcc_cascade)

    return {
        'Qh': round(Qh, 4), 'Qc': round(Qc, 4),
        'pinch_T': round(pinch_T_star, 2) if pinch_T_star else None,
        'pinch_h': pinch_h, 'is_threshold': is_threshold,
        'pinch_gap': pinch_gap,
        'total_hot': total_hot, 'total_cold': total_cold,
        'gcc_T': gcc_T, 'gcc_dQ': gcc_dQ,
        'hot_H': hot_H, 'hot_T': hot_T,
        'cold_H': cold_H_final, 'cold_T': cold_T,
    }


# =====================================================================
#  PLOTLY FIGURE BUILDERS  (NO invisible grid — JS handles clicks)
# =====================================================================

PLOT_STYLE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#FAFBFC",
    font=dict(family="JetBrains Mono, Source Sans Pro, sans-serif",
              size=13, color="#2C3E50"),
    margin=dict(l=70, r=40, t=50, b=60),
    xaxis=dict(gridcolor="#E8ECF0", gridwidth=1, zeroline=False,
               title_font=dict(size=14), tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#E8ECF0", gridwidth=1, zeroline=False,
               title_font=dict(size=14), tickfont=dict(size=11)),
    legend=dict(bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#BDC3C7", borderwidth=1, font=dict(size=11)),
)


def build_cc_figure(res, user_annotations):
    hot_H, hot_T = res['hot_H'], res['hot_T']
    cold_H, cold_T = res['cold_H'], res['cold_T']
    Qh, Qc = res['Qh'], res['Qc']
    is_threshold = res['is_threshold']
    pinch_T_star, pinch_h = res['pinch_T'], res['pinch_h']

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hot_H.tolist(), y=hot_T.tolist(), mode="lines+markers",
        name="Hot Composite (shifted)",
        line=dict(color="#E74C3C", width=2.5),
        marker=dict(size=5, color="#E74C3C")))
    fig.add_trace(go.Scatter(
        x=cold_H.tolist(), y=cold_T.tolist(), mode="lines+markers",
        name="Cold Composite (shifted)",
        line=dict(color="#3498DB", width=2.5),
        marker=dict(size=5, color="#3498DB")))

    built_in = []
    T_range = max(hot_T[-1], cold_T[-1]) - min(hot_T[0], cold_T[0])
    if T_range < 1e-6:
        T_range = 1.0

    if Qh > 1e-3:
        y_top = max(hot_T[-1], cold_T[-1])
        fig.add_trace(go.Scatter(
            x=[float(hot_H[-1]), float(cold_H[-1])], y=[y_top, y_top],
            mode="lines", line=dict(color="#E74C3C", width=1.5, dash="dash"),
            showlegend=False, opacity=0.7))
        built_in.append(dict(
            x=(float(hot_H[-1]) + float(cold_H[-1])) / 2,
            y=y_top + T_range * 0.03,
            text=f"<b>Qh = {Qh:.0f} kW</b>", showarrow=False,
            font=dict(size=11, color="#E74C3C", family="JetBrains Mono")))

    if Qc > 1e-3:
        y_bot = min(hot_T[0], cold_T[0])
        fig.add_trace(go.Scatter(
            x=[float(hot_H[0]), float(cold_H[0])], y=[y_bot, y_bot],
            mode="lines", line=dict(color="#3498DB", width=1.5, dash="dash"),
            showlegend=False, opacity=0.7))
        built_in.append(dict(
            x=(float(hot_H[0]) + float(cold_H[0])) / 2,
            y=y_bot - T_range * 0.05,
            text=f"<b>Qc = {Qc:.0f} kW</b>", showarrow=False,
            font=dict(size=11, color="#3498DB", family="JetBrains Mono")))

    if (not is_threshold and pinch_T_star is not None and
            hot_T[0] <= pinch_T_star <= hot_T[-1] and pinch_h is not None):
        fig.add_trace(go.Scatter(
            x=[pinch_h], y=[pinch_T_star], mode="markers",
            marker=dict(size=14, color="black", symbol="star"),
            name=f"Pinch T*={pinch_T_star:.1f}", showlegend=True))
        built_in.append(dict(
            x=pinch_h, y=pinch_T_star,
            text=f"<b>Pinch T*={pinch_T_star:.1f}</b>",
            showarrow=True, arrowhead=2, arrowwidth=1.2,
            arrowcolor="#333", ax=40, ay=-30,
            font=dict(size=11, color="#333", family="JetBrains Mono")))

    all_anns = built_in + annotations_to_plotly(user_annotations or [])
    label = "THRESHOLD" if is_threshold else "PINCH"
    fig.update_layout(
        title=dict(text=f"Shifted Composite Curves - {label}",
                   font=dict(size=15)),
        xaxis_title="Enthalpy (kW)",
        yaxis_title="Shifted Temperature T* (C / K)",
        annotations=all_anns,
        dragmode=False,
        **PLOT_STYLE)
    return fig


def build_gcc_figure(res, user_annotations):
    gcc_T, gcc_dQ = res['gcc_T'], res['gcc_dQ']

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=gcc_dQ.tolist(), y=gcc_T.tolist(), mode="lines+markers",
        name="Grand Composite",
        line=dict(color="#37474f", width=2.5),
        marker=dict(size=5, color="#37474f")))
    fig.add_trace(go.Scatter(
        x=[0] * len(gcc_T), y=gcc_T.tolist(), mode="lines",
        line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(
        x=gcc_dQ.tolist(), y=gcc_T.tolist(), mode="lines",
        fill="tonextx", fillcolor="rgba(55,71,79,0.08)",
        line=dict(width=0), showlegend=False))
    fig.add_vline(x=0, line_width=0.8, line_color="gray")

    dQ_max = float(max(gcc_dQ)) if len(gcc_dQ) > 0 else 1
    built_in = []

    gcc_pinch_idx = int(np.argmin(gcc_dQ))
    if gcc_dQ[gcc_pinch_idx] < 1e-3:
        built_in.append(dict(
            x=0, y=float(gcc_T[gcc_pinch_idx]),
            text=f"<b>Pinch T*={gcc_T[gcc_pinch_idx]:.1f}</b>",
            showarrow=True, arrowhead=2, arrowwidth=1,
            arrowcolor="black", ax=50, ay=0,
            font=dict(size=11, color="black", family="JetBrains Mono")))

    built_in.append(dict(
        x=float(gcc_dQ[0]), y=float(gcc_T[0]),
        text=f"<b>Qh = {gcc_dQ[0]:.1f} kW</b>",
        showarrow=True, arrowhead=2, arrowwidth=1,
        arrowcolor="#E74C3C", ax=50, ay=-20,
        font=dict(size=11, color="#E74C3C", family="JetBrains Mono")))

    built_in.append(dict(
        x=float(gcc_dQ[-1]), y=float(gcc_T[-1]),
        text=f"<b>Qc = {gcc_dQ[-1]:.1f} kW</b>",
        showarrow=True, arrowhead=2, arrowwidth=1,
        arrowcolor="#3498DB", ax=50, ay=20,
        font=dict(size=11, color="#3498DB", family="JetBrains Mono")))

    all_anns = built_in + annotations_to_plotly(user_annotations or [])
    fig.update_layout(
        title=dict(text="Grand Composite Curve", font=dict(size=15)),
        xaxis_title="Cascaded Heat dQ (kW)",
        yaxis_title="Shifted Temperature T* (C / K)",
        xaxis_range=[-dQ_max * 0.08, dQ_max * 1.45],
        annotations=all_anns,
        dragmode=False,
        **PLOT_STYLE)
    return fig


# =====================================================================
#  EXAMPLES
# =====================================================================

EXAMPLES = {
    "Example 1: Threshold": {
        "hot":  [[180, 80, 1000, 5], [150, 50, 1000, 10]],
        "cold": [[20, 120, 800, 8], [80, 140, 1000, 6]],
    },
    "Example 2: Normal Pinch": {
        "hot":  [[200, 100, 1000, 5], [150, 80, 700, 3]],
        "cold": [[50, 300, 1500, 5], [80, 200, 1000, 8]],
    },
    "Example 3: Clear Threshold": {
        "hot":  [[300, 100, 2000, 5]],
        "cold": [[30, 80, 100, 3]],
    },
}

# =====================================================================
#  JAVASCRIPT: Click-anywhere handler
# =====================================================================

# This JS runs once per plot whenever the figure updates.
# It attaches a click handler to Plotly's .nsewdrag overlay
# (the transparent rect that covers the entire plot area).
# Pixel coords are converted to data coords via axis range + rect size.
# Result is pushed to a dcc.Store via dash_clientside.set_props.

CLICK_HANDLER_JS = """
function(figure, graphId, storeId) {
    /*
     * Robust click-anywhere handler for Plotly graphs in Dash.
     *
     * Why mousedown/mouseup instead of click:
     *   Plotly's drag overlay (.nsewdrag) consumes 'click' events for
     *   pan/zoom/select.  By tracking mousedown -> mouseup ourselves on
     *   the ENTIRE graph wrapper (capture phase), we can detect a
     *   stationary click (< 5px movement, < 500ms) that Plotly would
     *   otherwise swallow.
     *
     * Pixel -> data coordinate conversion uses Plotly's internal
     *   _fullLayout.xaxis/yaxis.range + the .nsewdrag bounding rect.
     */
    setTimeout(function() {
        var wrapper = document.getElementById(graphId);
        if (!wrapper) return;

        var gd = wrapper.querySelector('.js-plotly-plot') || wrapper;

        // Only attach once
        var key = '_annClick_' + storeId;
        if (gd[key]) return;
        gd[key] = true;

        var downX = 0, downY = 0, downTime = 0;

        // Capture phase: we see the event BEFORE Plotly's handlers
        gd.addEventListener('mousedown', function(e) {
            downX = e.clientX;
            downY = e.clientY;
            downTime = Date.now();
        }, true);

        gd.addEventListener('mouseup', function(e) {
            var dx = Math.abs(e.clientX - downX);
            var dy = Math.abs(e.clientY - downY);
            var dt = Date.now() - downTime;

            // Only treat as annotation click if barely moved and short press
            if (dx > 5 || dy > 5 || dt > 500) return;

            // Get the plot area rect from .nsewdrag (the drag overlay)
            var dragRect = gd.querySelector('.nsewdrag');
            if (!dragRect) return;
            var rect = dragRect.getBoundingClientRect();

            // Check click is inside the plot area
            if (e.clientX < rect.left || e.clientX > rect.right ||
                e.clientY < rect.top  || e.clientY > rect.bottom) return;

            var layout = gd._fullLayout;
            if (!layout || !layout.xaxis || !layout.yaxis) return;

            // Pixel fraction within plot area
            var fracX = (e.clientX - rect.left) / rect.width;
            var fracY = 1.0 - (e.clientY - rect.top) / rect.height;

            // Convert to data coordinates
            var xr = layout.xaxis.range;
            var yr = layout.yaxis.range;
            var dataX = xr[0] + fracX * (xr[1] - xr[0]);
            var dataY = yr[0] + fracY * (yr[1] - yr[0]);

            dataX = Math.round(dataX * 100) / 100;
            dataY = Math.round(dataY * 100) / 100;

            // Push to Dash Store via set_props (bypasses callback graph)
            if (window.dash_clientside && window.dash_clientside.set_props) {
                window.dash_clientside.set_props(storeId, {
                    data: {x: dataX, y: dataY, ts: Date.now()}
                });
            }
        }, true);

        // Set crosshair cursor on the drag overlay
        var dragEl = gd.querySelector('.nsewdrag');
        if (dragEl) dragEl.style.cursor = 'crosshair';

    }, 500);

    return window.dash_clientside.no_update;
}
"""


# =====================================================================
#  DASH APP
# =====================================================================

app = Dash(__name__)


def _btn(color, bg="none", border=True):
    return {"background": bg if bg != "none" else "none",
            "border": f"1px solid {color}" if border else "none",
            "color": color if bg == "none" else "white",
            "padding": "5px 14px", "borderRadius": "5px",
            "cursor": "pointer", "fontSize": "12px",
            "fontFamily": "JetBrains Mono"}


def serve_layout():
    return html.Div([
        html.Link(
            href="https://fonts.googleapis.com/css2?"
                 "family=JetBrains+Mono:wght@400;600"
                 "&family=Source+Sans+Pro:wght@400;600;700&display=swap",
            rel="stylesheet"),

        # Header
        html.Div([
            html.Div([
                html.Div("P", style={
                    "fontSize": "18px", "color": "white",
                    "marginRight": "12px", "fontWeight": "700",
                    "backgroundColor": "#c0392b", "width": "34px",
                    "height": "34px", "borderRadius": "8px",
                    "display": "flex", "alignItems": "center",
                    "justifyContent": "center",
                    "fontFamily": "JetBrains Mono"}),
                html.Div([
                    html.H1("Pinch Analysis - Annotation Tool", style={
                        "margin": "0", "fontSize": "20px",
                        "fontWeight": "700", "color": "#1A1A2E",
                        "letterSpacing": "-0.5px"}),
                    html.P("Click anywhere to annotate | "
                           "annotations saved per data config",
                           style={"margin": "2px 0 0 0", "fontSize": "11px",
                                  "color": "#95a5a6",
                                  "fontFamily": "JetBrains Mono, monospace"}),
                ]),
            ], style={"display": "flex", "alignItems": "center"}),
            html.Div([
                dcc.Dropdown(
                    id="example-dropdown",
                    options=[{"label": k, "value": k} for k in EXAMPLES],
                    value=list(EXAMPLES.keys())[0],
                    clearable=False,
                    style={"width": "280px", "fontSize": "12px",
                           "fontFamily": "JetBrains Mono"}),
            ]),
        ], style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "center", "padding": "16px 28px",
            "borderBottom": "1px solid #E8ECF0",
            "fontFamily": "Source Sans Pro, sans-serif",
            "backgroundColor": "white"}),

        # Stream table + results
        html.Div(id="stream-table", style={
            "padding": "10px 28px", "fontSize": "12px",
            "fontFamily": "JetBrains Mono, monospace",
            "backgroundColor": "#F8F9FA",
            "borderBottom": "1px solid #E8ECF0"}),
        html.Div(id="results-banner", style={
            "padding": "8px 28px", "fontSize": "13px",
            "fontFamily": "JetBrains Mono, monospace",
            "backgroundColor": "white",
            "borderBottom": "1px solid #E8ECF0"}),

        # Annotation label input
        html.Div([
            html.Span("Label:", style={
                "color": "#7f8c8d", "marginRight": "8px",
                "fontSize": "12px", "fontWeight": "600"}),
            dcc.Input(
                id="next-label-input", type="text",
                placeholder="Type label, then click anywhere on a plot...",
                debounce=False,
                style={"flex": "1", "padding": "7px 12px",
                       "border": "2px solid #3498db",
                       "borderRadius": "6px", "fontSize": "13px",
                       "fontFamily": "JetBrains Mono",
                       "maxWidth": "500px",
                       "outline": "none"}),
            html.Span("  (empty = show coordinates)",
                       style={"color": "#bdc3c7", "fontSize": "11px",
                              "marginLeft": "8px"}),
        ], style={
            "display": "flex", "alignItems": "center",
            "padding": "12px 28px",
            "fontFamily": "JetBrains Mono, monospace",
            "borderBottom": "1px solid #E8ECF0",
            "backgroundColor": "#f0f7ff"}),

        # Plots
        html.Div([
            html.Div([
                dcc.Graph(id="cc-plot",
                          config={"displayModeBar": True,
                                  "scrollZoom": True,
                                  "doubleClick": "reset"},
                          style={"height": "520px"}),
            ], style={"flex": "1", "minWidth": "0"}),
            html.Div([
                dcc.Graph(id="gcc-plot",
                          config={"displayModeBar": True,
                                  "scrollZoom": True,
                                  "doubleClick": "reset"},
                          style={"height": "520px"}),
            ], style={"flex": "1", "minWidth": "0"}),
        ], style={"display": "flex", "gap": "12px",
                  "padding": "16px 28px"}),

        # Annotation tables
        html.Div([
            # CC
            html.Div([
                html.Div([
                    html.H3("CC Annotations", style={
                        "margin": "0", "fontSize": "14px",
                        "fontWeight": "600", "color": "#2C3E50"}),
                    html.Div([
                        html.Button("Clear", id="cc-clear-btn",
                                    n_clicks=0, style=_btn("#c0392b")),
                        html.Button("Export JSON", id="cc-export-btn",
                                    n_clicks=0,
                                    style=_btn("white", bg="#2C3E50",
                                               border=False)),
                    ], style={"display": "flex", "gap": "6px"}),
                ], style={"display": "flex",
                           "justifyContent": "space-between",
                           "alignItems": "center", "marginBottom": "8px"}),
                html.Div(id="cc-annotations-table"),
                dcc.Download(id="cc-download"),
            ], style={"flex": "1"}),
            # GCC
            html.Div([
                html.Div([
                    html.H3("GCC Annotations", style={
                        "margin": "0", "fontSize": "14px",
                        "fontWeight": "600", "color": "#2C3E50"}),
                    html.Div([
                        html.Button("Clear", id="gcc-clear-btn",
                                    n_clicks=0, style=_btn("#8e44ad")),
                        html.Button("Export JSON", id="gcc-export-btn",
                                    n_clicks=0,
                                    style=_btn("white", bg="#2C3E50",
                                               border=False)),
                    ], style={"display": "flex", "gap": "6px"}),
                ], style={"display": "flex",
                           "justifyContent": "space-between",
                           "alignItems": "center", "marginBottom": "8px"}),
                html.Div(id="gcc-annotations-table"),
                dcc.Download(id="gcc-download"),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "28px",
                  "padding": "0 28px 20px 28px"}),

        # -- Manual coordinate input for precise placement --
        html.Div([
            html.Details([
                html.Summary("Manual coordinate entry", style={
                    "cursor": "pointer", "color": "#7f8c8d",
                    "fontSize": "12px", "fontWeight": "600"}),
                html.Div([
                    html.Div([
                        html.Label("x:", style={"marginRight": "4px",
                                                 "fontSize": "12px"}),
                        dcc.Input(id="manual-x", type="number",
                                  placeholder="x", style={
                                      "width": "100px", "padding": "4px 8px",
                                      "border": "1px solid #dcdde1",
                                      "borderRadius": "4px", "fontSize": "12px",
                                      "fontFamily": "JetBrains Mono"}),
                        html.Label("y:", style={"marginLeft": "12px",
                                                 "marginRight": "4px",
                                                 "fontSize": "12px"}),
                        dcc.Input(id="manual-y", type="number",
                                  placeholder="y", style={
                                      "width": "100px", "padding": "4px 8px",
                                      "border": "1px solid #dcdde1",
                                      "borderRadius": "4px", "fontSize": "12px",
                                      "fontFamily": "JetBrains Mono"}),
                        html.Button("Add to CC", id="manual-cc-btn",
                                    n_clicks=0,
                                    style={**_btn("#c0392b"),
                                           "marginLeft": "12px"}),
                        html.Button("Add to GCC", id="manual-gcc-btn",
                                    n_clicks=0,
                                    style={**_btn("#8e44ad"),
                                           "marginLeft": "6px"}),
                    ], style={"display": "flex", "alignItems": "center",
                              "marginTop": "8px"}),
                ]),
            ], open=False),
        ], style={"padding": "10px 28px 16px 28px",
                  "fontFamily": "JetBrains Mono, monospace"}),

        # Stores
        dcc.Store(id="cc-ann-store", data=[]),
        dcc.Store(id="gcc-ann-store", data=[]),
        dcc.Store(id="pinch-store", data={}),
        dcc.Store(id="fingerprint-store", data=""),
        # Click coordinate stores (written by JS, read by Python)
        dcc.Store(id="cc-click-store", data={"x": 0, "y": 0, "ts": 0}),
        dcc.Store(id="gcc-click-store", data={"x": 0, "y": 0, "ts": 0}),

    ], style={
        "fontFamily": "Source Sans Pro, sans-serif",
        "backgroundColor": "#F0F2F5", "minHeight": "100vh"})


app.layout = serve_layout


# =====================================================================
#  CLIENTSIDE CALLBACKS — attach JS click handlers
# =====================================================================

# For CC plot: attach click handler to .nsewdrag
app.clientside_callback(
    CLICK_HANDLER_JS,
    Output("cc-click-store", "data"),
    Input("cc-plot", "figure"),
    State("cc-plot", "id"),
    State("cc-click-store", "id"),
)

# For GCC plot: same handler, different IDs
app.clientside_callback(
    CLICK_HANDLER_JS,
    Output("gcc-click-store", "data"),
    Input("gcc-plot", "figure"),
    State("gcc-plot", "id"),
    State("gcc-click-store", "id"),
)


# =====================================================================
#  SERVER CALLBACKS
# =====================================================================

# -- Example change --

@app.callback(
    Output("pinch-store", "data"),
    Output("fingerprint-store", "data"),
    Output("cc-ann-store", "data"),
    Output("gcc-ann-store", "data"),
    Output("stream-table", "children"),
    Output("results-banner", "children"),
    Input("example-dropdown", "value"),
)
def on_example_change(name):
    ex = EXAMPLES.get(name, list(EXAMPLES.values())[0])
    fp = data_fingerprint(ex["hot"], ex["cold"])
    res = compute_pinch(ex["hot"], ex["cold"])

    store = {k: (v.tolist() if isinstance(v, np.ndarray) else v)
             for k, v in res.items()}

    cc_anns = load_annotations("cc", fp)
    gcc_anns = load_annotations("gcc", fp)

    h = {"padding": "4px 8px", "fontWeight": "600",
         "borderBottom": "2px solid #CCC", "fontSize": "10px",
         "color": "#7F8C8D", "textTransform": "uppercase"}
    c = {"padding": "4px 8px", "borderBottom": "1px solid #EEE",
         "fontSize": "12px"}
    rows = [html.Tr([html.Th(t, style=h) for t in
                      ["Stream", "Tin", "Tout", "Q (kW)", "dTmin/2"]])]
    for i, s in enumerate(ex["hot"]):
        rows.append(html.Tr([
            html.Td(f"H{i+1}", style={**c, "color": "#c0392b",
                                        "fontWeight": "600"}),
            *[html.Td(f"{v}", style=c) for v in s]]))
    for i, s in enumerate(ex["cold"]):
        rows.append(html.Tr([
            html.Td(f"C{i+1}", style={**c, "color": "#2980b9",
                                        "fontWeight": "600"}),
            *[html.Td(f"{v}", style=c) for v in s]]))
    tbl = html.Table(rows, style={
        "borderCollapse": "collapse", "backgroundColor": "white",
        "borderRadius": "5px", "overflow": "hidden"})

    pt = "THRESHOLD" if res['is_threshold'] else "PINCH"
    bc = "#e67e22" if pt == "THRESHOLD" else "#27ae60"
    parts = [
        html.Span(f" {pt} ", style={
            "backgroundColor": bc, "color": "white",
            "padding": "2px 8px", "borderRadius": "3px",
            "fontSize": "11px", "fontWeight": "600", "marginRight": "12px"}),
        html.Span(f"Qh={res['Qh']:.1f}", style={
            "color": "#c0392b", "fontWeight": "600", "marginRight": "14px"}),
        html.Span(f"Qc={res['Qc']:.1f}", style={
            "color": "#2980b9", "fontWeight": "600", "marginRight": "14px"}),
    ]
    if res['pinch_T'] and not res['is_threshold']:
        parts.append(html.Span(f"T*={res['pinch_T']:.1f}",
                                style={"fontWeight": "600",
                                       "marginRight": "14px"}))
    rec = min(res['total_hot'], res['total_cold']) - max(0, res['Qc'])
    parts.append(html.Span(f"Recovery={rec:.0f} kW",
                            style={"color": "#95a5a6"}))

    return store, fp, cc_anns, gcc_anns, tbl, html.Div(parts)


# -- Plot updates --

@app.callback(Output("cc-plot", "figure"),
              Input("cc-ann-store", "data"),
              Input("pinch-store", "data"))
def update_cc(anns, res):
    if not res:
        raise PreventUpdate
    for k in ('hot_H', 'hot_T', 'cold_H', 'cold_T', 'gcc_T', 'gcc_dQ'):
        if k in res:
            res[k] = np.array(res[k])
    return build_cc_figure(res, anns)


@app.callback(Output("gcc-plot", "figure"),
              Input("gcc-ann-store", "data"),
              Input("pinch-store", "data"))
def update_gcc(anns, res):
    if not res:
        raise PreventUpdate
    for k in ('hot_H', 'hot_T', 'cold_H', 'cold_T', 'gcc_T', 'gcc_dQ'):
        if k in res:
            res[k] = np.array(res[k])
    return build_gcc_figure(res, anns)


# -- JS click -> add annotation (CC) --

@app.callback(
    Output("cc-ann-store", "data", allow_duplicate=True),
    Input("cc-click-store", "data"),
    State("cc-ann-store", "data"),
    State("fingerprint-store", "data"),
    State("next-label-input", "value"),
    prevent_initial_call=True)
def on_cc_click(click, anns, fp, label):
    if not click or click.get("ts", 0) == 0:
        raise PreventUpdate
    text = (label or "").strip() or f"({click['x']:.1f}, {click['y']:.1f})"
    anns = (anns or []) + [{"x": click["x"], "y": click["y"],
                             "text": text, "arrow": True,
                             "ax": 0, "ay": -35}]
    save_annotations("cc", fp, anns)
    return anns


# -- JS click -> add annotation (GCC) --

@app.callback(
    Output("gcc-ann-store", "data", allow_duplicate=True),
    Input("gcc-click-store", "data"),
    State("gcc-ann-store", "data"),
    State("fingerprint-store", "data"),
    State("next-label-input", "value"),
    prevent_initial_call=True)
def on_gcc_click(click, anns, fp, label):
    if not click or click.get("ts", 0) == 0:
        raise PreventUpdate
    text = (label or "").strip() or f"({click['x']:.1f}, {click['y']:.1f})"
    anns = (anns or []) + [{"x": click["x"], "y": click["y"],
                             "text": text, "arrow": True,
                             "ax": 0, "ay": -35}]
    save_annotations("gcc", fp, anns)
    return anns


# -- Manual coordinate add --

@app.callback(
    Output("cc-ann-store", "data", allow_duplicate=True),
    Input("manual-cc-btn", "n_clicks"),
    State("manual-x", "value"),
    State("manual-y", "value"),
    State("next-label-input", "value"),
    State("cc-ann-store", "data"),
    State("fingerprint-store", "data"),
    prevent_initial_call=True)
def manual_add_cc(n, x, y, label, anns, fp):
    if x is None or y is None:
        raise PreventUpdate
    text = (label or "").strip() or f"({x:.1f}, {y:.1f})"
    anns = (anns or []) + [{"x": round(x, 2), "y": round(y, 2),
                             "text": text, "arrow": True,
                             "ax": 0, "ay": -35}]
    save_annotations("cc", fp, anns)
    return anns


@app.callback(
    Output("gcc-ann-store", "data", allow_duplicate=True),
    Input("manual-gcc-btn", "n_clicks"),
    State("manual-x", "value"),
    State("manual-y", "value"),
    State("next-label-input", "value"),
    State("gcc-ann-store", "data"),
    State("fingerprint-store", "data"),
    prevent_initial_call=True)
def manual_add_gcc(n, x, y, label, anns, fp):
    if x is None or y is None:
        raise PreventUpdate
    text = (label or "").strip() or f"({x:.1f}, {y:.1f})"
    anns = (anns or []) + [{"x": round(x, 2), "y": round(y, 2),
                             "text": text, "arrow": True,
                             "ax": 0, "ay": -35}]
    save_annotations("gcc", fp, anns)
    return anns


# -- Clear --

@app.callback(
    Output("cc-ann-store", "data", allow_duplicate=True),
    Input("cc-clear-btn", "n_clicks"),
    State("fingerprint-store", "data"),
    prevent_initial_call=True)
def clear_cc(n, fp):
    save_annotations("cc", fp, [])
    return []


@app.callback(
    Output("gcc-ann-store", "data", allow_duplicate=True),
    Input("gcc-clear-btn", "n_clicks"),
    State("fingerprint-store", "data"),
    prevent_initial_call=True)
def clear_gcc(n, fp):
    save_annotations("gcc", fp, [])
    return []


# -- Delete individual --

@app.callback(
    Output("cc-ann-store", "data", allow_duplicate=True),
    Input({"type": "cc-del", "index": ALL}, "n_clicks"),
    State("cc-ann-store", "data"),
    State("fingerprint-store", "data"),
    prevent_initial_call=True)
def del_cc(clicks, anns, fp):
    ctx = callback_context
    if not ctx.triggered or not any(clicks):
        raise PreventUpdate
    idx = json.loads(ctx.triggered[0]["prop_id"].rsplit(".", 1)[0])["index"]
    anns = [a for i, a in enumerate(anns) if i != idx]
    save_annotations("cc", fp, anns)
    return anns


@app.callback(
    Output("gcc-ann-store", "data", allow_duplicate=True),
    Input({"type": "gcc-del", "index": ALL}, "n_clicks"),
    State("gcc-ann-store", "data"),
    State("fingerprint-store", "data"),
    prevent_initial_call=True)
def del_gcc(clicks, anns, fp):
    ctx = callback_context
    if not ctx.triggered or not any(clicks):
        raise PreventUpdate
    idx = json.loads(ctx.triggered[0]["prop_id"].rsplit(".", 1)[0])["index"]
    anns = [a for i, a in enumerate(anns) if i != idx]
    save_annotations("gcc", fp, anns)
    return anns


# -- Inline text editing --

@app.callback(
    Output("cc-ann-store", "data", allow_duplicate=True),
    Input({"type": "cc-edit", "index": ALL}, "value"),
    State("cc-ann-store", "data"),
    State("fingerprint-store", "data"),
    prevent_initial_call=True)
def edit_cc(values, anns, fp):
    if not anns:
        raise PreventUpdate
    changed = False
    for i, v in enumerate(values):
        if i < len(anns) and v is not None and v != anns[i].get("text"):
            anns[i]["text"] = v
            changed = True
    if not changed:
        raise PreventUpdate
    save_annotations("cc", fp, anns)
    return anns


@app.callback(
    Output("gcc-ann-store", "data", allow_duplicate=True),
    Input({"type": "gcc-edit", "index": ALL}, "value"),
    State("gcc-ann-store", "data"),
    State("fingerprint-store", "data"),
    prevent_initial_call=True)
def edit_gcc(values, anns, fp):
    if not anns:
        raise PreventUpdate
    changed = False
    for i, v in enumerate(values):
        if i < len(anns) and v is not None and v != anns[i].get("text"):
            anns[i]["text"] = v
            changed = True
    if not changed:
        raise PreventUpdate
    save_annotations("gcc", fp, anns)
    return anns


# -- Render annotation tables --

def _ann_table(anns, prefix):
    if not anns:
        return html.Div("No annotations. Click anywhere on the plot "
                         "or use manual entry below.",
                         style={"color": "#bdc3c7", "fontSize": "12px",
                                "fontStyle": "italic",
                                "fontFamily": "JetBrains Mono",
                                "padding": "6px 0"})
    hd = {"padding": "5px 8px", "fontSize": "10px", "fontWeight": "600",
          "color": "#95a5a6", "textTransform": "uppercase",
          "fontFamily": "JetBrains Mono",
          "borderBottom": "2px solid #E8ECF0"}
    cl = {"padding": "5px 8px", "fontSize": "12px", "color": "#2C3E50",
          "fontFamily": "JetBrains Mono",
          "borderBottom": "1px solid #F0F2F5"}
    rows = [html.Tr([html.Th(c, style=hd)
                      for c in ["#", "x", "y", "Label", ""]])]
    for i, a in enumerate(anns):
        rows.append(html.Tr([
            html.Td(str(i + 1), style=cl),
            html.Td(f"{a['x']:.1f}", style=cl),
            html.Td(f"{a['y']:.1f}", style=cl),
            html.Td(dcc.Input(
                id={"type": f"{prefix}-edit", "index": i},
                value=a.get("text", ""), type="text", debounce=True,
                style={"border": "1px solid #E8ECF0", "borderRadius": "4px",
                       "padding": "3px 6px", "fontSize": "12px",
                       "width": "100%", "fontFamily": "JetBrains Mono",
                       "boxSizing": "border-box"}),
                     style={**cl, "minWidth": "160px"}),
            html.Td(html.Button(
                "x", id={"type": f"{prefix}-del", "index": i}, n_clicks=0,
                style={"background": "none", "border": "none",
                       "color": "#e74c3c", "cursor": "pointer",
                       "fontSize": "14px", "fontWeight": "700"}),
                     style=cl),
        ]))
    return html.Table(rows, style={
        "width": "100%", "borderCollapse": "collapse",
        "backgroundColor": "white", "borderRadius": "6px",
        "overflow": "hidden",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})


@app.callback(Output("cc-annotations-table", "children"),
              Input("cc-ann-store", "data"))
def tbl_cc(a): return _ann_table(a or [], "cc")


@app.callback(Output("gcc-annotations-table", "children"),
              Input("gcc-ann-store", "data"))
def tbl_gcc(a): return _ann_table(a or [], "gcc")


# -- Export --

@app.callback(Output("cc-download", "data"),
              Input("cc-export-btn", "n_clicks"),
              State("cc-ann-store", "data"),
              State("fingerprint-store", "data"),
              prevent_initial_call=True)
def exp_cc(n, anns, fp):
    return dcc.send_string(
        json.dumps({"plot": "cc", "fingerprint": fp,
                     "annotations": anns or []}, indent=2),
        filename=f"cc_annotations_{fp}.json")


@app.callback(Output("gcc-download", "data"),
              Input("gcc-export-btn", "n_clicks"),
              State("gcc-ann-store", "data"),
              State("fingerprint-store", "data"),
              prevent_initial_call=True)
def exp_gcc(n, anns, fp):
    return dcc.send_string(
        json.dumps({"plot": "gcc", "fingerprint": fp,
                     "annotations": anns or []}, indent=2),
        filename=f"gcc_annotations_{fp}.json")


# =====================================================================
if __name__ == "__main__":
    print("\n  Pinch Analysis Annotation Tool v3")
    print("  -----------------------------------")
    print("  * Click ANYWHERE on plots (JS handler)")
    print("  * Or use manual x,y coordinate entry")
    print("  * Annotations saved per data config")
    print("  * Open: http://127.0.0.1:8050\n")
    app.run(debug=True)
