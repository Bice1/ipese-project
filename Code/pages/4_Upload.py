"""
Upload page — import a new IETS v6 Excel model into the database.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from parser.excel_parser import parse_excel_to_model_json
from utils.categories import CATEGORIES
from utils.constants import DATA_DIR
from utils.loader import load_all_models
from utils.styles import inject_css

inject_css()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_dir_name(name: str) -> str:
    """Convert a model name to a filesystem-safe directory/file stem."""
    name = name.strip()
    name = re.sub(r"[^\w\s\-]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name or "model"


def _parse_file(xlsx_bytes: bytes) -> dict[str, Any] | None:
    """Run excel_parser and return the JSON dict, or None on failure."""
    try:
        return parse_excel_to_model_json(xlsx_bytes)
    except Exception as exc:
        st.error(f"Could not parse file: {exc}")
        return None


def _meta(json_dict: dict, key: str, default: str = "") -> str:
    return str(json_dict.get("METADATA", {}).get(key, "") or default).strip()


# ---------------------------------------------------------------------------
# Page UI
# ---------------------------------------------------------------------------

st.title("Upload Model")
st.caption("Import an IETS v6 Excel template into the model database.")

st.divider()

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1 — Choose category")
    cat_display_list = [c["name"] for c in CATEGORIES]
    cat_slug_list    = [c["slug"] for c in CATEGORIES]
    chosen_display = st.selectbox(
        "Category",
        options=cat_display_list,
        label_visibility="collapsed",
    )
    chosen_slug = cat_slug_list[cat_display_list.index(chosen_display)]

    st.subheader("2 — Upload files")
    xlsx_file = st.file_uploader(
        "IETS v6 Excel template (.xlsx / .xlsm)",
        type=["xlsx", "xlsm"],
        help="The file must follow the IETS Task XXIV v6 template structure. Macro-enabled workbooks (.xlsm) are accepted.",
    )
    img_file = st.file_uploader(
        "Block Flow Diagram image (optional)",
        type=["png", "jpg", "jpeg", "svg"],
        help="Will be stored alongside the model and shown in the Overview tab.",
    )
    suppl_files = st.file_uploader(
        "Supplementary material (optional)",
        type=["pdf", "md"],
        accept_multiple_files=True,
        help="One or more PDF or Markdown files stored alongside the model.",
    )

# ---------------------------------------------------------------------------
# Parse the uploaded file (cached in session state to avoid re-parsing on
# every widget interaction)
# ---------------------------------------------------------------------------

json_dict: dict | None = None

if xlsx_file is not None:
    file_id = (xlsx_file.name, xlsx_file.size)
    if st.session_state.get("_upload_file_id") != file_id:
        with st.spinner("Parsing file …"):
            xlsx_file.seek(0)
            result = _parse_file(xlsx_file.read())
        st.session_state["_upload_json_dict"] = result
        st.session_state["_upload_file_id"] = file_id
    json_dict = st.session_state.get("_upload_json_dict")

with col_right:
    st.subheader("Preview")
    if json_dict is not None:
        model_name = _meta(json_dict, "Model Name") or Path(xlsx_file.name).stem

        if model_name:
            st.success(f"**{model_name}** — parsed successfully")
        else:
            st.warning("Model name not found in METADATA sheet.")

        info_rows = []
        for key in ["Model Name", "Model UID", "Authors and Contributors",
                    "Version", "TRL", "Grade", "Confidentiality"]:
            val = _meta(json_dict, key)
            if val:
                info_rows.append({"Field": key, "Value": val})

        info_rows.append({"Field": "Units",    "Value": str(len(json_dict.get("UNITS", {})))})
        info_rows.append({"Field": "Category", "Value": chosen_display})
        if img_file:
            info_rows.append({"Field": "BFD image", "Value": img_file.name})
        for sf in suppl_files:
            info_rows.append({"Field": "Supplementary", "Value": sf.name})

        st.dataframe(pd.DataFrame(info_rows), use_container_width=True, hide_index=True)

    elif xlsx_file is not None:
        st.error("Parsing failed — see error above.")
        model_name = None
    else:
        st.info("Upload an XLSX file to see a preview.")
        model_name = None

# ---------------------------------------------------------------------------
# Import button
# ---------------------------------------------------------------------------

st.divider()

can_import = json_dict is not None and bool(
    _meta(json_dict, "Model Name") or (xlsx_file is not None and xlsx_file.name)
)

import_btn = st.button("Import Model", type="primary", disabled=not can_import)

if import_btn and json_dict is not None:
    model_name = _meta(json_dict, "Model Name") or Path(xlsx_file.name).stem
    dir_name   = _safe_dir_name(model_name)
    model_dir  = DATA_DIR / chosen_slug / dir_name
    json_path  = model_dir / f"{dir_name}.json"
    xlsx_ext   = Path(xlsx_file.name).suffix  # preserve .xlsx or .xlsm
    xlsx_dest  = model_dir / f"{dir_name}{xlsx_ext}"

    if json_path.exists():
        st.warning(
            f"A model named **{model_name}** already exists in `{chosen_slug}`. "
            "Overwriting."
        )

    try:
        model_dir.mkdir(parents=True, exist_ok=True)

        # Patch BFD path in the JSON dict if an image was provided
        out_dict = dict(json_dict)
        out_dict["METADATA"] = dict(json_dict.get("METADATA", {}))

        if img_file is not None:
            img_ext  = Path(img_file.name).suffix
            bfd_dest = model_dir / f"{dir_name}_BFD{img_ext}"
            img_file.seek(0)
            bfd_dest.write_bytes(img_file.read())
            out_dict["METADATA"]["Block Flow Diagram"] = str(bfd_dest)

        if suppl_files:
            saved_paths = []
            seen: dict[str, int] = {}
            for sf in suppl_files:
                stem = Path(sf.name).stem
                ext  = Path(sf.name).suffix
                count = seen.get(sf.name, 0)
                seen[sf.name] = count + 1
                dest_name = sf.name if count == 0 else f"{stem}_{count}{ext}"
                dest = model_dir / dest_name
                sf.seek(0)
                dest.write_bytes(sf.read())
                saved_paths.append(str(dest))
            out_dict["METADATA"]["Supplementary Material"] = json.dumps(saved_paths)

        # Write JSON
        json_path.write_text(
            json.dumps(out_dict, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        # Copy xlsx
        xlsx_file.seek(0)
        xlsx_dest.write_bytes(xlsx_file.read())

        # Invalidate model cache
        load_all_models.clear()

        st.success(
            f"Model **{model_name}** imported to "
            f"`{model_dir.relative_to(DATA_DIR.parent)}`."
        )

        if st.button("Open in Model Detail →"):
            st.session_state["selected_model"] = model_name
            st.switch_page("pages/2_Model_Detail.py")

    except Exception as exc:
        st.error(f"Import failed: {exc}")
