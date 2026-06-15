"""
Catalog page — searchable, filterable view of all loaded models.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CODE_DIR = Path(__file__).parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import streamlit as st

from utils.categories import CATEGORIES, CATEGORY_COLORS, CATEGORY_DISPLAY_NAMES
from utils.constants import (
    DATA_DIR,
    GRADE_OPTIONS,
    CONFIDENTIALITY_OPTIONS,
    SHARING_LAYER_OPTIONS,
    GRADE_COLORS,
    CONFIDENTIALITY_COLORS,
)
from utils.loader import load_all_models
from utils.styles import inject_css, badge as _badge, CSS_CARD

inject_css()

# ---------------------------------------------------------------------------
# Session state — initialise models if not already loaded
# ---------------------------------------------------------------------------

if "models" not in st.session_state:
    with st.spinner("Loading model database ..."):
        st.session_state["models"] = load_all_models(DATA_DIR)

if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = None

models: dict = st.session_state["models"]

# ---------------------------------------------------------------------------
# Helper: safe metadata accessor
# ---------------------------------------------------------------------------

def _meta(model, key: str, default: str = "") -> str:
    """Return metadata value as a stripped string, with a fallback."""
    val = model.metadata.get(key, default)
    return str(val).strip() if val is not None else default


def _meta_int(model, key: str, default: int | None = None) -> int | None:
    """Return metadata value coerced to int."""
    val = model.metadata.get(key)
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Collect unique software values across all models
# ---------------------------------------------------------------------------

all_software: list[str] = sorted(set(
    _meta(m, "SOFTWARE") for m in models.values()
    if _meta(m, "SOFTWARE")
))

# Collect categories actually present in the loaded models
present_category_slugs: list[str] = sorted(set(
    m.category for m in models.values() if m.category
))
present_categories = [
    c for c in CATEGORIES if c["slug"] in present_category_slugs
]

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Filters")

    search_query = st.text_input("Search by name or keyword", placeholder="e.g. cheese, cement ...")
    search_author = st.text_input("Search by author", placeholder="e.g. Smith, Florez ...")

    selected_grades = st.multiselect(
        "Grade",
        options=GRADE_OPTIONS,
        default=[],
    )

    selected_conf = st.multiselect(
        "Confidentiality",
        options=CONFIDENTIALITY_OPTIONS,
        default=[],
    )

    trl_range = st.slider(
        "TRL",
        min_value=1,
        max_value=9,
        value=(1, 9),
    )

    selected_software = st.multiselect(
        "Software",
        options=all_software,
        default=[],
    )

    selected_layers = st.multiselect(
        "Sharing Layer",
        options=SHARING_LAYER_OPTIONS,
        default=[],
    )

    selected_categories = st.multiselect(
        "Category",
        options=[c["slug"] for c in present_categories],
        format_func=lambda s: CATEGORY_DISPLAY_NAMES.get(s, s),
        default=[],
    )

    st.divider()
    if st.button("Clear all filters", use_container_width=True):
        st.rerun()

# ---------------------------------------------------------------------------
# Filtering logic
# ---------------------------------------------------------------------------

def _passes_filters(name: str, model) -> bool:
    """Return True if the model passes all active filters."""
    # Text search (name / keyword / description)
    if search_query.strip():
        q = search_query.strip().lower()
        haystack = (
            _meta(model, "MODEL NAME").lower()
            + " "
            + _meta(model, "KEYWORDS").lower()
            + " "
            + _meta(model, "DESCRIPTION").lower()
        )
        if q not in haystack:
            return False

    # Author search
    if search_author.strip():
        if search_author.strip().lower() not in _meta(model, "AUTHORS AND CONTRIBUTORS").lower():
            return False

    # Grade
    if selected_grades:
        grade = _meta(model, "GRADE").upper()
        if grade not in [g.upper() for g in selected_grades]:
            return False

    # Confidentiality
    if selected_conf:
        conf = _meta(model, "CONFIDENTIALITY")
        if conf not in selected_conf:
            return False

    # TRL range
    trl = _meta_int(model, "TRL")
    if trl is not None:
        if not (trl_range[0] <= trl <= trl_range[1]):
            return False

    # Software
    if selected_software:
        sw = _meta(model, "SOFTWARE")
        if sw not in selected_software:
            return False

    # Sharing layer
    if selected_layers:
        layer = _meta_int(model, "SHARING LAYER")
        if layer not in selected_layers:
            return False

    # Category
    if selected_categories:
        if model.category not in selected_categories:
            return False

    return True


filtered = {
    name: model
    for name, model in models.items()
    if _passes_filters(name, model)
}

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title("Model Catalog")
st.caption(f"Showing {len(filtered)} of {len(models)} model{'s' if len(models) != 1 else ''}")

if len(models) < 3:
    st.info(
        f"The database currently contains {len(models)} model(s). "
        "Filters are active but results will be limited until more models are added."
    )

if not filtered:
    st.warning("No models match the current filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

with st.expander("Table view", expanded=False):
    import pandas as pd
    table_rows = []
    for name, model in filtered.items():
        trl_val = _meta_int(model, "TRL")
        table_rows.append({
            "Model Name":       _meta(model, "MODEL NAME") or name,
            "Category":         CATEGORY_DISPLAY_NAMES.get(model.category, model.category),
            "Version":          _meta(model, "VERSION"),
            "Grade":            _meta(model, "GRADE"),
            "TRL":              trl_val if trl_val is not None else "",
            "Confidentiality":  _meta(model, "CONFIDENTIALITY"),
            "Sharing Layer":    _meta(model, "SHARING LAYER"),
            "Software":         _meta(model, "SOFTWARE"),
            "Keywords":         _meta(model, "KEYWORDS"),
        })

    st.dataframe(
        pd.DataFrame(table_rows),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Model cards
# ---------------------------------------------------------------------------

for name, model in filtered.items():
    with st.container(border=True):
        col_left, col_mid, col_img, col_right = st.columns([3, 4, 2, 1])

        with col_left:
            model_display_name = _meta(model, "MODEL NAME") or name
            st.subheader(model_display_name)
            uid = _meta(model, "MODEL UID")
            if uid:
                st.caption(f"UID: {uid}")

            # Category chip
            cat_slug = model.category
            if cat_slug:
                cat_color = CATEGORY_COLORS.get(cat_slug, "#888888")
                cat_label = CATEGORY_DISPLAY_NAMES.get(cat_slug, cat_slug)
                st.markdown(
                    f'<span style="background:{cat_color};color:#ffffff;padding:2px 10px;'
                    f'border-radius:10px;font-size:10px;font-weight:600;letter-spacing:0.03em;">'
                    f'{cat_label}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown("")

            # Badges row
            grade = _meta(model, "GRADE").upper()
            grade_color = GRADE_COLORS.get(grade, "#888888")

            conf = _meta(model, "CONFIDENTIALITY")
            conf_color = CONFIDENTIALITY_COLORS.get(conf, "#888888")

            trl_val = _meta_int(model, "TRL")
            trl_str = f"TRL {trl_val}" if trl_val is not None else "TRL ?"

            version = _meta(model, "VERSION")

            badges = []
            if grade:
                badges.append(_badge(grade, grade_color))
            if conf:
                badges.append(_badge(conf, conf_color))
            badges.append(_badge(trl_str, "#607D8B"))
            if version:
                badges.append(_badge(f"v{version}", "#607D8B"))

            software = _meta(model, "SOFTWARE")
            if software:
                badges.append(_badge(software, "#9C27B0"))

            st.markdown("&nbsp;".join(badges), unsafe_allow_html=True)

        with col_mid:
            desc = _meta(model, "DESCRIPTION")
            if desc:
                truncated = desc[:280] + "..." if len(desc) > 280 else desc
                st.markdown(
                    f'<p style="color:#334155;font-size:13px;margin:0;line-height:1.6;">{truncated}</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<p style="color:#94a3b8;font-size:13px;font-style:italic;">No description available.</p>',
                    unsafe_allow_html=True,
                )

            keywords = _meta(model, "KEYWORDS")
            if keywords:
                st.markdown(
                    f'<p style="color:#64748b;font-size:11px;margin-top:6px;">'
                    f'Keywords: {keywords}</p>',
                    unsafe_allow_html=True,
                )

        with col_img:
            # BFD thumbnail
            bfd_raw = _meta(model, "BLOCK FLOW DIAGRAM")
            bfd_path = Path(bfd_raw) if bfd_raw and bfd_raw not in ("N/A", "-", "") else None
            if bfd_path and bfd_path.exists():
                try:
                    st.image(str(bfd_path), use_container_width=True)
                except Exception:
                    pass
            else:
                st.markdown(
                    '<div style="border:1px dashed #cbd5e1;border-radius:6px;'
                    'padding:24px 8px;text-align:center;color:#94a3b8;font-size:11px;">'
                    'No BFD</div>',
                    unsafe_allow_html=True,
                )

        with col_right:
            layer = _meta(model, "SHARING LAYER")
            if layer:
                st.markdown(
                    f'<p style="color:#64748b;font-size:12px;text-align:center;margin-bottom:4px;">'
                    f'Sharing layer<br><strong style="font-size:20px;color:#0f172a;">{layer}</strong></p>',
                    unsafe_allow_html=True,
                )

            if st.button("View Details", key=f"btn_{name}", use_container_width=True):
                st.session_state["selected_model"] = name
                st.switch_page("pages/2_Model_Detail.py")
