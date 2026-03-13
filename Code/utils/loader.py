"""
Model loader — scans DATA_DIR for *.xlsx files and parses them with IETSParser.
Cached with st.cache_resource so parsing runs only once per Streamlit session.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

import streamlit as st

# Ensure Code/ is on the path so sibling packages resolve correctly
_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from parser.parser import IETSParser, ParsedModel


@st.cache_resource(show_spinner=False)
def load_all_models(data_dir: Path | str) -> dict[str, ParsedModel]:
    """
    Parse every *.xlsx file in data_dir and return a dict keyed by model name.

    Uses MODEL NAME from METADATA as the key; falls back to the filename stem
    if the field is missing or blank.  Files that fail to parse are skipped with
    a st.warning notification.
    """
    data_dir = Path(data_dir)
    models: dict[str, ParsedModel] = {}

    if not data_dir.exists():
        st.warning(f"Data directory not found: {data_dir}")
        return models

    xlsx_files = sorted(data_dir.glob("*.xlsx"))

    if not xlsx_files:
        st.warning(f"No .xlsx files found in {data_dir}")
        return models

    for filepath in xlsx_files:
        try:
            parser = IETSParser(str(filepath))
            model = parser.parse()
            key = str(model.metadata.get("MODEL NAME") or "").strip()
            if not key:
                key = filepath.stem
            models[key] = model
        except Exception as exc:
            st.warning(f"Could not parse {filepath.name}: {exc}")

    return models
