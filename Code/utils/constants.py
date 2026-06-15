"""
Shared constants for the IETS Task XXIV Streamlit app.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Resolve to Code/models/ — organised by category/<model>/ subfolders
DATA_DIR: Path = Path(__file__).parent.parent / "models"

# Path to the default core SVG used when no specific unit SVG exists
DEFAULT_CORE_SVG: Path = Path(__file__).parent.parent / "assets" / "default_core.svg"

# ---------------------------------------------------------------------------
# Excel sheet names
# ---------------------------------------------------------------------------

FIXED_SHEET_NAMES: frozenset[str] = frozenset([
    "README", "METADATA", "CONNECTORS", "VARIABLES",
    "CALCULATIONS", "CHANGELOG", "SUPPL MATERIAL",
])

# ---------------------------------------------------------------------------
# METADATA display order (23 fields, exactly as they appear in the Excel)
# ---------------------------------------------------------------------------

METADATA_DISPLAY_KEYS: list[str] = [
    "MODEL UID",
    "MODEL NAME",
    "AUTHORS AND CONTRIBUTORS",
    "CONTACT INFO",
    "CREATION DATE",
    "LAST UPDATED",
    "MODEL STATUS",
    "VERSION",
    "CONFIDENTIALITY",
    "SHARING LAYER",
    "GRADE",
    "REFERENCE CAPACITY",
    "TRL",
    "KEYWORDS",
    "DESCRIPTION",
    "DOI",
    "MAIN RELATED PUBLICATION",
    "REFERENCES",
    "SOFTWARE",
    "SOFTWARE FILE",
    "BLOCK FLOW DIAGRAM",
    "URL",
    "SUPPLEMENTARY MATERIAL",
]

# Keys shown as metric tiles in the detail page (subset of METADATA_DISPLAY_KEYS)
METADATA_TILE_KEYS: list[str] = [
    "TRL",
    "GRADE",
    "SHARING LAYER",
    "CONFIDENTIALITY",
    "SOFTWARE",
    "MODEL STATUS",
]

# Keys excluded from the metadata table (shown elsewhere in the UI)
METADATA_TABLE_EXCLUDE: set[str] = {
    "DESCRIPTION",
    "BLOCK FLOW DIAGRAM",
}

# ---------------------------------------------------------------------------
# Catalog filter options
# ---------------------------------------------------------------------------

GRADE_OPTIONS: list[str] = ["WHITE-BOX", "GRAY-BOX", "BLACK-BOX"]
CONFIDENTIALITY_OPTIONS: list[str] = ["Open", "Restricted", "Confidential"]
SHARING_LAYER_OPTIONS: list[int] = [0, 1, 2, 3, 4, 5, 6]

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

COLOR_HOT: str = "#D94F3D"
COLOR_COLD: str = "#3A7FC1"
COLOR_GCC: str = "#5A8A5E"
COLOR_PINCH: str = "#888888"

# Grade badge colours
GRADE_COLORS: dict[str, str] = {
    "WHITE-BOX": "#2196F3",
    "GRAY-BOX":  "#FF9800",
    "BLACK-BOX": "#424242",
}

# Confidentiality badge colours
CONFIDENTIALITY_COLORS: dict[str, str] = {
    "Open":         "#4CAF50",
    "Restricted":   "#FF9800",
    "Confidential": "#F44336",
}

# ---------------------------------------------------------------------------
# Plotly base layout (applied to all figures)
# ---------------------------------------------------------------------------

PLOTLY_LAYOUT_BASE: dict = {
    "plot_bgcolor":  "white",
    "paper_bgcolor": "white",
    "font": {
        "family": "Inter, system-ui, Arial, sans-serif",
        "size": 13,
        "color": "#0f172a",
    },
    "xaxis": {
        "showgrid":      True,
        "gridcolor":     "#f1f5f9",
        "linecolor":     "#cbd5e1",
        "linewidth":     1,
        "showline":      True,
        "zeroline":      True,
        "zerolinecolor": "#cbd5e1",
        "zerolinewidth": 1,
    },
    "yaxis": {
        "showgrid":      True,
        "gridcolor":     "#f1f5f9",
        "linecolor":     "#cbd5e1",
        "linewidth":     1,
        "showline":      True,
        "zeroline":      False,
    },
    "legend": {
        "bgcolor":      "rgba(255,255,255,0.90)",
        "bordercolor":  "#e2e8f0",
        "borderwidth":  1,
    },
    "margin": {"l": 60, "r": 40, "t": 60, "b": 60},
}
