"""
GCC/CC pinch engine — interval method.

Temperature shifting convention (CLAUDE.md):
    Hot streams : T_shifted = T - dTmin_contribution / 2
    Cold streams: T_shifted = T + dTmin_contribution / 2

Public API
----------
compute_pinch(streams, cascade_filter) -> PinchResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PinchResult:
    """Output of compute_pinch."""

    # Composite curves: list of (T_shifted [C], H_cumulative [kW])
    hot_cc:  list[tuple[float, float]] = field(default_factory=list)
    cold_cc: list[tuple[float, float]] = field(default_factory=list)

    # Grand Composite Curve: list of (T_shifted [C], residual_H [kW]),
    # sorted from highest T to lowest T
    gcc: list[tuple[float, float]] = field(default_factory=list)

    # Minimum utility targets
    q_hot_min:  float = 0.0  # kW — external hot utility required
    q_cold_min: float = 0.0  # kW — external cold utility required

    # Pinch temperatures (shifted scale)
    pinch_temperatures: list[float] = field(default_factory=list)

    # Distinct HEAT CASCADE labels present in the filtered data
    cascade_labels: list[str] = field(default_factory=list)

    # Non-fatal issues encountered during computation
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def compute_pinch(
    streams: pd.DataFrame,
    cascade_filter: str | None = None,
) -> PinchResult:
    """
    Compute composite curves and grand composite curve via the interval method.

    Parameters
    ----------
    streams:
        Merged heat-streams DataFrame from one or more unit sheets.
        Required columns: type, T_in, T_out, H_in, H_out, dtmin_contr, heat_cascade.
        The ``is_phase_change`` flag (added by the parser) is used for phase-change
        streams but is not strictly required.
    cascade_filter:
        If None or "ALL", all streams participate.
        If a named cascade label (e.g. "CHEESEPLANT"), only streams where
        heat_cascade equals that label OR equals "DEFAULT" are included.

    Returns
    -------
    PinchResult
    """
    result = PinchResult()

    if streams is None or streams.empty:
        result.warnings.append("No heat streams provided.")
        return result

    df = _filter_and_validate(streams, cascade_filter, result)

    if df.empty:
        result.warnings.append("No valid streams remain after filtering.")
        return result

    result.cascade_labels = sorted(
        str(v) for v in df["heat_cascade"].dropna().unique() if str(v).strip()
    )

    df = _apply_temperature_shift(df, result)

    breakpoints = _build_breakpoints(df)

    if len(breakpoints) < 2:
        result.warnings.append("Not enough temperature breakpoints to build curves.")
        return result

    hot_df  = df[df["type_norm"] == "Hot"].copy()
    cold_df = df[df["type_norm"] == "Cold"].copy()

    result.hot_cc  = _build_cc(hot_df,  breakpoints)
    result.cold_cc = _build_cc(cold_df, breakpoints)

    result.gcc, result.q_hot_min, result.q_cold_min, result.pinch_temperatures = (
        _build_gcc(hot_df, cold_df, breakpoints)
    )

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _filter_and_validate(
    streams: pd.DataFrame,
    cascade_filter: str | None,
    result: PinchResult,
) -> pd.DataFrame:
    """
    Keep only rows that are valid Hot or Cold streams.

    Removes:
    - Rows where ``type`` is not Hot/Cold  (parser description-row leak)
    - Rows where T_in or T_out is not numeric (SAT, N/A, …)
    - Rows where H_in or H_out is not numeric
    Applies cascade filter when requested.
    """
    df = streams.copy()

    # Normalise type to title case
    if "type" in df.columns:
        df["type_norm"] = df["type"].apply(
            lambda v: str(v).strip().title() if v is not None else ""
        )
    else:
        result.warnings.append("Column 'type' missing from streams DataFrame.")
        return pd.DataFrame()

    # Keep only Hot/Cold rows
    valid_types = df["type_norm"].isin(["Hot", "Cold"])
    skipped = (~valid_types).sum()
    if skipped:
        result.warnings.append(
            f"{skipped} stream row(s) skipped: type is not Hot or Cold."
        )
    df = df[valid_types].copy()

    # Check for SAT temperature values
    for col in ("T_in", "T_out"):
        if col not in df.columns:
            continue
        sat_mask = df[col].apply(
            lambda v: isinstance(v, str) and str(v).strip().upper() == "SAT"
        )
        if sat_mask.any():
            names = df.loc[sat_mask, "name"].tolist() if "name" in df.columns else []
            result.warnings.append(
                f"Stream(s) with SAT temperature in '{col}' excluded from pinch "
                f"analysis: {names}"
            )
        df = df[~sat_mask].copy()

    # Numeric coercion for temperature and enthalpy columns
    for col in ("T_in", "T_out", "H_in", "H_out"):
        if col not in df.columns:
            result.warnings.append(f"Column '{col}' missing — skipping affected rows.")
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["T_in", "T_out", "H_in", "H_out"])
    dropped = before - len(df)
    if dropped:
        result.warnings.append(
            f"{dropped} stream row(s) dropped: non-numeric T or H values."
        )

    # dtmin_contr — default 0 if missing or non-numeric
    if "dtmin_contr" not in df.columns:
        df["dtmin_contr"] = 0.0
    df["dtmin_contr"] = pd.to_numeric(df["dtmin_contr"], errors="coerce").fillna(0.0)

    # heat_cascade — default to "DEFAULT" if missing
    if "heat_cascade" not in df.columns:
        df["heat_cascade"] = "DEFAULT"
    df["heat_cascade"] = df["heat_cascade"].apply(
        lambda v: str(v).strip() if v is not None else "DEFAULT"
    )
    df.loc[df["heat_cascade"] == "", "heat_cascade"] = "DEFAULT"

    # Apply cascade filter
    if cascade_filter and cascade_filter.upper() != "ALL":
        mask = (df["heat_cascade"] == cascade_filter) | (df["heat_cascade"] == "DEFAULT")
        df = df[mask].copy()

    return df.reset_index(drop=True)


def _apply_temperature_shift(df: pd.DataFrame, result: PinchResult) -> pd.DataFrame:
    """
    Add shifted temperature columns and precomputed dH.

    T_in_s, T_out_s: shifted inlet/outlet temperatures
    T_lo, T_hi: min/max of shifted temperatures for each stream
    dH: absolute enthalpy change |H_out - H_in|
    """
    half_dt = df["dtmin_contr"] / 2.0

    hot_mask  = df["type_norm"] == "Hot"
    cold_mask = df["type_norm"] == "Cold"

    df["T_in_s"]  = np.where(hot_mask, df["T_in"]  - half_dt, df["T_in"]  + half_dt)
    df["T_out_s"] = np.where(hot_mask, df["T_out"] - half_dt, df["T_out"] + half_dt)

    df["T_lo"] = df[["T_in_s", "T_out_s"]].min(axis=1)
    df["T_hi"] = df[["T_in_s", "T_out_s"]].max(axis=1)
    df["dH"]   = (df["H_out"] - df["H_in"]).abs()

    return df


def _build_breakpoints(df: pd.DataFrame) -> list[float]:
    """Return sorted, deduplicated list of all shifted temperature breakpoints."""
    raw = np.concatenate([df["T_lo"].values, df["T_hi"].values])
    raw = raw[np.isfinite(raw)]
    raw = np.sort(raw)

    # Deduplicate within tolerance 1e-6 K
    if len(raw) == 0:
        return []
    deduped = [float(raw[0])]
    for val in raw[1:]:
        if abs(val - deduped[-1]) > 1e-6:
            deduped.append(float(val))
    return deduped


def _interval_contributions(
    streams_df: pd.DataFrame,
    t_lo: float,
    t_hi: float,
) -> float:
    """
    Compute total enthalpy contribution from streams_df to interval [t_lo, t_hi].

    For normal streams: contribution = dH * overlap / span
    For phase-change streams (span < 1e-6): full dH if their degenerate band
    falls inside the interval (their T_lo and T_hi are both within [t_lo, t_hi]).
    """
    if streams_df.empty:
        return 0.0

    total = 0.0
    for _, row in streams_df.iterrows():
        s_lo = row["T_lo"]
        s_hi = row["T_hi"]
        span = s_hi - s_lo

        # Stream must overlap the interval
        if s_hi <= t_lo or s_lo >= t_hi:
            continue

        if span < 1e-6:
            # Phase-change: assign full dH to the interval that contains it
            total += float(row["dH"])
        else:
            overlap = min(t_hi, s_hi) - max(t_lo, s_lo)
            if overlap > 0:
                total += float(row["dH"]) * overlap / span

    return total


def _build_cc(
    streams_df: pd.DataFrame,
    all_breakpoints: list[float],
) -> list[tuple[float, float]]:
    """
    Build a composite curve for the given set of streams (all Hot OR all Cold).

    Returns a list of (T_shifted, H_cumulative) pairs sorted by increasing T.
    H starts at 0 at the lowest temperature breakpoint of the group.
    """
    if streams_df.empty:
        return []

    # Use only the breakpoints spanned by this group's streams
    t_min = float(streams_df["T_lo"].min())
    t_max = float(streams_df["T_hi"].max())

    group_bps = [t for t in all_breakpoints if t_min - 1e-9 <= t <= t_max + 1e-9]
    if len(group_bps) < 2:
        return []

    cc: list[tuple[float, float]] = [(group_bps[0], 0.0)]
    H = 0.0
    for k in range(len(group_bps) - 1):
        t_lo = group_bps[k]
        t_hi = group_bps[k + 1]
        dH = _interval_contributions(streams_df, t_lo, t_hi)
        H += dH
        cc.append((t_hi, H))

    return cc


def _build_gcc(
    hot_df: pd.DataFrame,
    cold_df: pd.DataFrame,
    breakpoints: list[float],
) -> tuple[list[tuple[float, float]], float, float, list[float]]:
    """
    Build the grand composite curve via the heat cascade.

    Returns (gcc_points, q_hot_min, q_cold_min, pinch_temperatures).
    gcc_points are sorted from highest T to lowest T.
    """
    n = len(breakpoints)
    # Cascade residuals: R[i] is the residual at breakpoints[n-1-i] (top to bottom)
    # We process intervals from top to bottom.

    # Build net surplus per interval (top interval first)
    intervals_desc = list(zip(reversed(breakpoints[:-1]), reversed(breakpoints[1:])))
    # intervals_desc[i] = (T_lo, T_hi) from top to bottom

    net_surplus: list[float] = []
    for t_lo, t_hi in intervals_desc:
        hot_contrib  = _interval_contributions(hot_df,  t_lo, t_hi)
        cold_contrib = _interval_contributions(cold_df, t_lo, t_hi)
        net_surplus.append(hot_contrib - cold_contrib)

    # Cumulate residuals from top (R[0] = 0 at the highest T)
    residuals = [0.0]
    for surplus in net_surplus:
        residuals.append(residuals[-1] + surplus)

    # Shift so minimum residual = 0 (pinch adjustment)
    min_r = min(residuals)
    q_hot_min = -min_r if min_r < 0 else 0.0
    r_shifted = [r + q_hot_min for r in residuals]

    q_cold_min = r_shifted[-1]

    # Build GCC list (T, residual) from top to bottom
    # breakpoints are sorted low-to-high; reversed gives high-to-low
    t_desc = list(reversed(breakpoints))
    gcc = [(t_desc[i], r_shifted[i]) for i in range(len(t_desc))]

    # Pinch temperatures: where residual <= tolerance
    tol = max(1e-3 * max(r_shifted, default=1.0), 1e-3)
    pinch_temps = [t for t, r in gcc if r <= tol]

    return gcc, q_hot_min, q_cold_min, pinch_temps
