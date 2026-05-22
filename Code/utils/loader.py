"""
Model loader — recursively scans DATA_DIR for *.json files under
  models/<category>/<model_name>/<model_name>.json
and converts them to ParsedModel dataclasses.

Category is inferred from the grandparent folder name.
BFD images are auto-generated on first load if absent.
Cached with st.cache_resource so loading runs only once per session.
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
from utils.categories import MODEL_CATEGORY_MAP, CATEGORY_SLUGS


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


def _json_to_parsed_model(data: dict, filepath: str, category: str = "") -> ParsedModel:
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
            description=str(unit_data.get("Unit Description", "") or "").strip(),
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
        category=category,
    )


# ---------------------------------------------------------------------------
# BFD generation helper
# ---------------------------------------------------------------------------

def _ensure_bfd(json_path: Path, data: dict) -> Path | None:
    """
    Generate a BFD SVG alongside the JSON if one does not already exist.
    Returns the path to the BFD file, or None if generation failed.
    """
    model_stem = json_path.stem.replace("_v6", "")
    bfd_path = json_path.parent / f"{model_stem}_BFD.svg"

    if bfd_path.exists():
        return bfd_path

    try:
        from utils.diagram import generate_block_flow_svg
        from utils.constants import DEFAULT_CORE_SVG

        svg_content = generate_block_flow_svg(data, str(DEFAULT_CORE_SVG))
        bfd_path.write_text(svg_content, encoding="utf-8")
        return bfd_path
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Category extraction
# ---------------------------------------------------------------------------

def _infer_category(filepath: Path) -> str:
    """
    Infer category slug from the folder hierarchy:
      models/<category>/<model_name>/<file>.json → filepath.parent.parent.name
    Falls back to MODEL_CATEGORY_MAP keyed by JSON stem.
    """
    grandparent = filepath.parent.parent.name
    if grandparent in CATEGORY_SLUGS:
        return grandparent
    return MODEL_CATEGORY_MAP.get(filepath.stem, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def load_all_models(data_dir: Path | str) -> dict[str, ParsedModel]:
    """
    Load every *.json file found recursively under data_dir.

    Expected structure: data_dir/<category>/<model_name>/<model_name>.json
    Category is inferred from the grandparent folder name.
    BFD images are auto-generated on first load if absent.
    Returns a dict keyed by model name (from METADATA, else filename stem).
    """
    data_dir = Path(data_dir)
    models: dict[str, ParsedModel] = {}

    if not data_dir.exists():
        st.warning(f"Data directory not found: {data_dir}")
        return models

    _SKIP_NAMES = {"comments.json", "posts.json"}
    json_files = sorted(f for f in data_dir.rglob("*.json") if f.name not in _SKIP_NAMES)

    if not json_files:
        st.warning(f"No .json files found under {data_dir}")
        return models

    for filepath in json_files:
        try:
            with open(filepath, encoding="utf-8") as fh:
                data = json.load(fh)

            category = _infer_category(filepath)

            # Ensure BFD exists; patch its absolute path into metadata
            bfd_path = _ensure_bfd(filepath, data)
            if bfd_path and bfd_path.exists():
                metadata = data.setdefault("METADATA", {})
                existing = str(metadata.get("Block Flow Diagram", "")).strip()
                if not existing or existing in ("-", "N/A"):
                    metadata["Block Flow Diagram"] = str(bfd_path)

            model = _json_to_parsed_model(data, str(filepath), category=category)

            key = str(data.get("METADATA", {}).get("Model Name") or "").strip()
            if not key:
                key = filepath.stem

            models[key] = model

        except Exception as exc:
            st.warning(f"Could not load {filepath.name}: {exc}")

    return models
