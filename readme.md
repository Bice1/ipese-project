# IETS Task XXIV - Industrial Process Integration Platform

A Streamlit web application for browsing, analyzing, and integrating industrial process models oriented toward decarbonization. It implements thermodynamic pinch analysis, connector symbiosis detection, and multi-model heat integration on top of a filesystem-based model database using the IETS v6 data format.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Web framework | [Streamlit](https://streamlit.io) | ≥ 1.32.0 |
| Language | Python | 3.10+ (tested on 3.13) |
| Data processing | pandas | ≥ 2.0.0 |
| Numerical engine | NumPy | ≥ 1.26.0 |
| Excel parsing | openpyxl | ≥ 3.1.0 |
| Visualization | Plotly | ≥ 5.18.0 |
| Graph layout | NetworkX | ≥ 3.0 |
| Plot rendering | Matplotlib | ≥ 3.7.0 |
| Interactive graph | streamlit-flow-component | ≥ 1.5.0 |
| Database | None - JSON files on disk | |

---

## Prerequisites

- Python 3.10 or higher
- pip

---

## Installation

```bash
# 1. Clone or download the repository, then enter the app directory
cd IPESE-PROJECT/Code

# 2. (Recommended) Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running Locally

```bash
# From the Code/ directory
streamlit run app.py

or 

python -m streamlit run app.py
```


On first launch, Streamlit loads all JSON models from `Code/models/`, auto-generates any missing block flow diagram SVGs, and caches everything in session memory. Subsequent page navigations within the same session are fast.



## Environment Variables

No `.env` file is required. All paths are resolved relative to the source files:

| Internal constant | Default resolved path | Purpose |
|---|---|---|
| `DATA_DIR` | `Code/models/` | Root of the model filesystem database |
| `DEFAULT_CORE_SVG` | `Code/assets/default_core.svg` | Fallback SVG template for BFD generation |

Streamlit theme is set in `Code/.streamlit/config.toml` (no env vars needed).

---

## Folder Structure

```
IPESE-PROJECT/
├── Code/                         # All application code
│   ├── app.py                    # Entry point - registers Streamlit pages
│   ├── requirements.txt          # Python dependencies
│   ├── .streamlit/
│   │   └── config.toml           # Theme (colors, font)
│   ├── assets/
│   │   └── default_core.svg      # Default SVG template for BFD generation
│   ├── engine/
│   │   └── pinch.py              # Pinch analysis algorithm (composite curves, GCC)
│   ├── models/                   # Model database (one folder per model)
│   │   ├── air_separation/
│   │   ├── bio_and_waste/
│   │   ├── co2_capture/
│   │   ├── electrochemical/
│   │   ├── gas_upgrading_syngas/
│   │   ├── heat_recovery_upgrade/
│   │   ├── power_and_utilities/
│   │   ├── renewables/
│   │   ├── synthetic_fuels_biofuels/
│   │   └── thermal_conversion/
│   ├── pages/
│   │   ├── 1_Catalog.py          # Searchable model catalog
│   │   ├── 2_Model_Detail.py     # Detailed model analysis (6 tabs)
│   │   ├── 3_Symbiosis.py        # Cross-model connector compatibility
│   │   ├── 4_Multi_Integration.py# Multi-model heat integration
│   │   └── 5_Upload.py           # Import new models from Excel
│   ├── parser/
│   │   ├── parser.py             # IETS v6 Excel → ParsedModel dataclass
│   │   └── excel_parser.py       # Excel-to-JSON conversion utility (standalone)
│   └── utils/
│       ├── categories.py         # 18 category definitions and color map
│       ├── constants.py          # Global constants and color palette
│       ├── diagram.py            # SVG block flow diagram generator
│       ├── forum.py              # Forum post read/write (JSON persistence)
│       ├── loader.py             # Model loading and session-level caching
│       └── styles.py             # CSS injection and HTML helpers
documentation
├── README.md                     # This file
└── method.md                     # Exhaustive feature and architecture documentation
```

---

## Further Documentation

See [method.md](method.md) for an exhaustive description of every implemented feature, data models, the pinch analysis algorithm, layer communication, and known technical debt.
