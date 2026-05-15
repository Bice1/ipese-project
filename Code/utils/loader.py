"""
Model loader — scans DATA_DIR for *.json files produced by excel_parser.py
and converts them to ParsedModel dataclasses.
Cached with st.cache_resource so loading runs only once per Streamlit session.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from parser.parser import (
    CONNECTOR_COL_MAP,
    HEAT_STREAM_COL_MAP,
    ParsedModel,
    UnitData,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _scalar(val: Any) -> Any:
    """Return the numeric value from a formula-dict, or the value as-is."""
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val


def _connectors_df(raw: list[dict]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame(columns=list(CONNECTOR_COL_MAP.values()))
    df = pd.DataFrame(raw)
    df = df.map(_scalar)
    present = {k: v for k, v in CONNECTOR_COL_MAP.items() if k in df.columns}
    df = df.rename(columns=present)
    keep = [v for k, v in CONNECTOR_COL_MAP.items() if k in present]
    extra = [c for c in df.columns if c not in CONNECTOR_COL_MAP and c not in keep]
    return df[[c for c in keep + extra if c in df.columns]]


def _heat_streams_df(raw: list[dict]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame(columns=list(HEAT_STREAM_COL_MAP.values()))
    df = pd.DataFrame(raw)
    df = df.map(_scalar)
    present = {k: v for k, v in HEAT_STREAM_COL_MAP.items() if k in df.columns}
    df = df.rename(columns=present)
    keep = [v for k, v in HEAT_STREAM_COL_MAP.items() if k in present]
    extra = [c for c in df.columns if c not in HEAT_STREAM_COL_MAP and c not in keep]
    return df[[c for c in keep + extra if c in df.columns]]


def _equipments_list(raw: dict) -> list[dict]:
    result = []
    for eq_name, eq_data in (raw or {}).items():
        params = []
        for p in eq_data.get("Parameters", []):
            params.append({
                "Parameter": p.get("Parameter", ""),
                "Value": _scalar(p.get("Value")),
                "Unit": p.get("Unit", ""),
            })
        result.append({
            "name":    eq_name,
            "type":    eq_data.get("Type", ""),
            "subtype": eq_data.get("Subtype", ""),
            "params":  params,
        })
    return result


def _json_to_parsed_model(data: dict, filepath: str) -> ParsedModel:
    metadata = {str(k).upper(): v for k, v in data.get("METADATA", {}).items()}

    connectors_section = data.get("CONNECTORS", {})
    ext_raw = connectors_section.get("EXTERNAL CONNECTORS", [])
    int_raw = connectors_section.get("INTERNAL CONNECTORS", [])
    external_connectors = pd.DataFrame(ext_raw) if ext_raw else pd.DataFrame()
    internal_connectors = pd.DataFrame(int_raw) if int_raw else pd.DataFrame()

    global_uid_registry = [
        row.get("UID", "") for row in ext_raw if row.get("UID")
    ]

    variables_raw = data.get("VARIABLES", [])
    if variables_raw:
        vars_df = pd.DataFrame(variables_raw)
        if "DEFAULT VALUE" in vars_df.columns:
            vars_df["DEFAULT VALUE"] = vars_df["DEFAULT VALUE"].map(_scalar)
    else:
        vars_df = pd.DataFrame()

    units: dict[str, UnitData] = {}
    unit_names: list[str] = []
    for unit_name, unit_data in data.get("UNITS", {}).items():
        unit_names.append(unit_name)
        info = unit_data.get("Unit Info", {})
        units[unit_name] = UnitData(
            name=unit_name,
            fmin=_scalar(info.get("Minimum capacity multiplier")),
            fmax=_scalar(info.get("Maximum capacity multiplier")),
            connectors=_connectors_df(unit_data.get("Connectors", [])),
            heat_streams=_heat_streams_df(unit_data.get("Heat Streams", [])),
            equipments=_equipments_list(unit_data.get("Equipments", {})),
        )

    return ParsedModel(
        filepath=filepath,
        metadata=metadata,
        unit_names=unit_names,
        units=units,
        external_connectors=external_connectors,
        internal_connectors=internal_connectors,
        global_uid_registry=global_uid_registry,
        variables=vars_df,
        calculations=None,
        warnings=[],
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def load_all_models(data_dir: Path | str) -> dict[str, ParsedModel]:
    """
    Load every *.json file in data_dir and return a dict keyed by model name.

    Uses "Model Name" from METADATA as the key; falls back to the filename stem
    if the field is missing or blank.  Files that fail to load are skipped with
    a st.warning notification.
    """
    data_dir = Path(data_dir)
    models: dict[str, ParsedModel] = {}

    if not data_dir.exists():
        st.warning(f"Data directory not found: {data_dir}")
        return models

    json_files = sorted(data_dir.glob("*.json"))

    if not json_files:
        st.warning(f"No .json files found in {data_dir}")
        return models

    for filepath in json_files:
        try:
            with open(filepath, encoding="utf-8") as fh:
                data = json.load(fh)
            model = _json_to_parsed_model(data, str(filepath))
            key = str(data.get("METADATA", {}).get("Model Name") or "").strip()
            if not key:
                key = filepath.stem
            models[key] = model
        except Exception as exc:
            st.warning(f"Could not load {filepath.name}: {exc}")

    return models
