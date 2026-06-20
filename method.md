# Method - Feature Reference & Architecture

This document describes every feature implemented in the IETS Task XXIV web application, how each feature is triggered, which files are involved, and how the layers communicate. It is derived entirely from the source code.

---

## Table of Contents

1. [Overall Architecture](#1-overall-architecture)
2. [Data Models & Schemas](#2-data-models--schemas)
3. [Model Loading Pipeline](#3-model-loading-pipeline)
4. [Page 1 - Catalog](#4-page-1--catalog)
5. [Page 2 - Model Detail](#5-page-2--model-detail)
6. [Page 3 - Symbiosis](#6-page-3--symbiosis)
7. [Page 4 - Multi-Model Integration](#7-page-4--multi-model-integration)
8. [Page 5 - Upload](#8-page-5--upload)
9. [Pinch Analysis Engine](#9-pinch-analysis-engine)
10. [Parser - IETS v6 Excel](#10-parser--iets-v6-excel)
11. [SVG Block Flow Diagram Generator](#11-svg-block-flow-diagram-generator)
12. [Forum Backend](#12-forum-backend)
13. [Shared Utilities](#13-shared-utilities)
14. [Key User Journeys](#14-key-user-journeys)
15. [Known Technical Debt & Incomplete Features](#15-known-technical-debt--incomplete-features)

---

## 1. Overall Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  BROWSER  -  Streamlit multipage UI (5 pages)                    │
│                                                                  │
│  pages/1_Catalog.py          pages/2_Model_Detail.py            │
│  pages/3_Symbiosis.py        pages/4_Multi_Integration.py        │
│  pages/5_Upload.py                                               │
└─────────────────────┬────────────────────────────────────────────┘
                      │ st.session_state  (selected model key,
                      │                    username, filter state)
┌─────────────────────▼────────────────────────────────────────────┐
│  IN-MEMORY LAYER  -  utils/loader.py                             │
│                                                                  │
│  load_all_models(DATA_DIR)                                       │
│   └─ scan models/<category>/<model>/*.json                       │
│   └─ parse each JSON → ParsedModel dataclass                     │
│   └─ generate missing BFD SVGs (diagram.py)                      │
│   └─ cache with @st.cache_resource (once per session)            │
│                                                                  │
│  Result: dict[str, ParsedModel]  (key = model folder name)       │
└─────────────────────┬────────────────────────────────────────────┘
                      │ reads / writes JSON files
┌─────────────────────▼────────────────────────────────────────────┐
│  FILESYSTEM  -  Code/models/<category>/<model>/                  │
│                                                                  │
│  <model>.json              parsed model (source of truth)        │
│  <model>_v6.xlsx           original Excel (kept for reference)   │
│  <model>_BFD.svg           block flow diagram image              │
│  <supplementary>.pdf/.md   attached documents                    │
│  posts.json                expert forum threads                  │
└──────────────────────────────────────────────────────────────────┘
```

**Provisionnal architectural decisions to be updated for deployement:**

- **No database server.** All persistent state is JSON files on disk. This simplifies deployment (no connection string, no migrations) at the cost of no concurrent write safety.
- **No REST API.** Streamlit widgets drive reruns directly; inter-page state is passed through `st.session_state`.
- **Single process.** The app is single-threaded per user session; `@st.cache_resource` is shared across sessions.

---

## 2. Data Models & Schemas

### 2.1 ParsedModel

Defined in `Code/parser/parser.py`. All pages consume this dataclass.

```python
@dataclass
class ParsedModel:
    filepath: str                           # Absolute path to .json file
    metadata: dict[str, Any]                # 23 METADATA sheet fields
    unit_names: list[str]                   # Ordered list of unit sheet names
    units: dict[str, UnitData]              # {unit_name: UnitData}
    external_connectors: pd.DataFrame       # Global scope connectors
    internal_connectors: pd.DataFrame       # Cross-unit connectors
    global_uid_registry: list[str]          # All unique connector UIDs
    variables: pd.DataFrame                 # VARIABLES sheet
    calculations: pd.DataFrame | None       # CALCULATIONS sheet (optional)
    warnings: list[str]                     # Non-fatal parser warnings
    category: str                           # Category slug (from folder path)
```

### 2.2 UnitData

```python
@dataclass
class UnitData:
    name: str
    fmin: float | None                      # Minimum capacity multiplier
    fmax: float | None                      # Maximum capacity multiplier
    connectors: pd.DataFrame                # Unit-level connectors
    heat_streams: pd.DataFrame              # HEAT STREAMS sheet rows
    equipments: list[dict]                  # Equipment list
    description: str = ""
```

### 2.3 METADATA fields (23)

`MODEL UID`, `MODEL NAME`, `AUTHORS AND CONTRIBUTORS`, `CONTACT INFO`, `CREATION DATE`, `LAST UPDATED`, `MODEL STATUS`, `VERSION`, `CONFIDENTIALITY`, `SHARING LAYER`, `GRADE`, `REFERENCE CAPACITY`, `TRL`, `KEYWORDS`, `DESCRIPTION`, `DOI`, `MAIN RELATED PUBLICATION`, `REFERENCES`, `SOFTWARE`, `SOFTWARE FILE`, `BLOCK FLOW DIAGRAM`, `URL`, `SUPPLEMENTARY MATERIAL`

### 2.4 HEAT STREAMS DataFrame columns

| Column | Description |
|---|---|
| `name` | Stream identifier |
| `type` | `"Hot"` or `"Cold"` |
| `T_in`, `T_out` | Inlet/outlet temperature [°C] |
| `H_in`, `H_out` | Inlet/outlet enthalpy flow [kW] |
| `cp` | Specific heat capacity |
| `mdot` | Mass flow rate |
| `dtmin_contr` | dTmin contribution [°C] - used for temperature shifting |
| `heat_cascade` | Cascade label (e.g., `"DEFAULT"`, `"CHEESEPLANT"`) |
| `is_phase_change` | `True` when `T_in ≈ T_out` |

### 2.5 CONNECTORS DataFrame columns

`name`, `type`, `direction` (`IN`/`OUT`), `flow_value`, `flow_unit`, `T_value`, `T_unit`, `P_value`, `P_unit`, `vapor_fraction`, `phase`, `composition`, `reference_stream`, `description`

### 2.6 Equipment structure (list of dicts)

```json
{
  "name": "Pump A",
  "type": "Pump",
  "subtype": "Centrifugal",
  "params": [
    {"param": "Efficiency", "value": 0.75, "unit": "%"}
  ]
}
```

### 2.7 Forum posts (posts.json)

```json
[{
  "id": "<uuid4>",
  "username": "Alice",
  "timestamp": "2026-05-21T14:32:00",
  "title": "Post title",
  "text": "Post body",
  "comments": [{
    "id": "<uuid4>",
    "username": "Bob",
    "timestamp": "...",
    "text": "Comment text",
    "replies": [{
      "id": "<uuid4>",
      "username": "Charlie",
      "timestamp": "...",
      "text": "Reply text"
    }]
  }]
}]
```

### 2.8 PinchResult

Returned by `engine/pinch.py::compute_pinch()`.

```python
@dataclass
class PinchResult:
    hot_cc: list[tuple[float, float]]       # [(T_shifted, H_cumulative), ...]
    cold_cc: list[tuple[float, float]]
    gcc: list[tuple[float, float]]          # [(T, residual), ...]
    q_hot_min: float                        # Minimum hot utility [kW]
    q_cold_min: float                       # Minimum cold utility [kW]
    pinch_temperatures: list[float]         # [°C], may be multiple
    cascade_labels: list[str]
    warnings: list[str]
```

---

## 3. Model Loading Pipeline

**Files:** `utils/loader.py`, `utils/diagram.py`, `parser/parser.py`

**Trigger:** First access to `load_all_models()` within a Streamlit session (cached with `@st.cache_resource`).

**Steps:**

1. Walk `Code/models/<category>/<model>/` recursively.
2. For each directory containing a `*.json` file, read the JSON.
3. Call `_json_to_parsed_model(data, filepath)` → reconstruct `ParsedModel` with DataFrames from dict lists.
4. Call `_ensure_bfd(model, model_dir)`:
   - If no BFD path or file missing → call `diagram.generate_bfd_svg()` → save to `<model>_BFD.svg`.
5. Store in `dict[str, ParsedModel]` keyed by model folder name.
6. Return the complete dict.

**Cache invalidation:** Explicitly cleared by calling `load_all_models.clear()` after a successful upload (page 5).

---

## 4. Page 1 - Catalog

**File:** `Code/pages/1_Catalog.py`

### Features

#### Sidebar filters
- **Text search** - matches against `MODEL NAME`, `KEYWORDS`, `DESCRIPTION`, author names (case-insensitive substring).
- **Author search** - dedicated field for `AUTHORS AND CONTRIBUTORS`.
- **Grade** - checkbox group: `WHITE-BOX`, `GRAY-BOX`, `BLACK-BOX`.
- **Confidentiality** - checkbox group: `Open`, `Restricted`, `Confidential`.
- **TRL range** - double-ended slider (1–9).
- **Software** - free-text field.
- **Sharing Layer** - double-ended slider (0–6).
- **Category** - multiselect, populated from loaded models (not hardcoded).
- **Clear all filters** button - resets session state and triggers `st.rerun()`.

#### Model cards (default view)
One card per filtered model, displaying:
- Model name and color-coded category chip.
- Badges: Grade, Confidentiality, TRL, Version, Software.
- Truncated description (280 characters).
- Keywords.
- Block flow diagram thumbnail (SVG or PNG).
- Sharing layer number.
- **"View Details"** button → sets `st.session_state["selected_model"]` and calls `st.switch_page("pages/2_Model_Detail.py")`.

#### Table view (expandable)
Summary table with one row per model, key metadata columns.

#### Model count
Header shows `N of M models` based on active filters.

---

## 5. Page 2 - Model Detail

**File:** `Code/pages/2_Model_Detail.py`

### Sidebar
- Category dropdown → filters the model list below it.
- Model selector → loads the selected `ParsedModel`.
- **"Back to Catalog"** button.
- Username input (persisted in `st.session_state["username"]`, used for forum posts).

### Tab 1 - Overview

- Description rendered in a styled HTML card.
- Full metadata table (all 23 fields except `DESCRIPTION` and `BLOCK FLOW DIAGRAM`).
- Block Flow Diagram image (auto-generated SVG or user-uploaded image).
- Metric tiles: TRL, Grade, Sharing Layer, Confidentiality, Software, Model Status.
- Unit summary cards: capacity range (Fmin–Fmax), stream count, connector count, equipment count per unit.
- Supplementary material section:
  - PDF → rendered inline via base64 iframe + download button.
  - Markdown → rendered with `st.markdown()` + download button.

### Tab 2 - Heat Analysis

**Trigger:** Selecting this tab with a model that has heat streams defined.

- **Cascade label filter** - select a named cascade or "All".
- **Unit filter** - select a single unit or "All units".
- **Chart type selector** - `CC` (composite curves), `GCC` (grand composite curve), `Carnot GCC`, or `Both` (CC + GCC side by side).
- **Metrics row:** Qc,min [kW], Qh,min [kW], pinch temperature(s) [°C].
- **Plotly charts** with:
  - Hot/cold composite curves with dashed-line annotations for pinch and utility gaps.
  - GCC with shaded utility regions.
  - Carnot GCC: y-axis is Carnot efficiency `η = 1 - T₀/(T+273.15)`.
- **Heat streams data table** (expandable) showing all streams used in the computation.
- Calls `engine/pinch.py::compute_pinch()` with the filtered DataFrame.

### Tab 3 - Connectors

- **External connectors table** - global scope connectors (model boundary).
- **Internal connectors table** - cross-unit connectors.
- **Per-unit connectors** - one expander per unit, each with a connector table.

### Tab 4 - Equipment

- Per-unit equipment list rendered as a table.
- Columns: equipment name, type, subtype, parameter name, value, unit.
- Capacity multiplier info (Fmin, Fmax, scalable vs fixed).

### Tab 5 - Variables

- Full variable table from the VARIABLES sheet.
- Filterable by `TYPE` and `USER GRADE` columns via selectbox widgets.

### Tab 6 - Forum

**Trigger:** Selecting this tab. Posts are read from `posts.json` on each render.

- Posts displayed newest-first.
- Each post shows: username badge (color-coded), timestamp, title, body.
- **Comment threads** (2 levels: comments + replies).
  - Comments displayed in an expander per post.
  - Replies displayed in a nested expander per comment.
  - Reply form (text area + submit button) at the bottom of each comment.
- **New post form:** title field + body text area + submit button. Requires `username` to be set in sidebar.
- Persistence: `forum.py::save_posts()` writes the updated list back to `posts.json`.

---

## 6. Page 3 - Symbiosis

**File:** `Code/pages/3_Symbiosis.py`

Identifies which models can exchange streams based on matching connector UIDs.

### Sidebar
- **Layout mode** - `"Model → Model"` (direct edges) vs `"UID hub-and-spoke"` (UID as intermediate node).
- **UID filter** - multiselect of all UIDs present in external connectors.
- **Category filter** - multiselect.

### Metrics row
- Models with at least one external connector.
- Unique UIDs across all models.
- Total symbiosis pairs (pairs of models sharing ≥1 UID).

### Tab 1 - Network Graph (Plotly)

- Dual filter UI: "Select all / Clear all" per model list and per UID list.
- Graph computed with NetworkX spring layout.
- **Nodes:** models (circles, colored by category). In hub mode, UIDs are additional diamond-shaped nodes.
- **Edges:** producer→consumer connection per shared UID, colored by UID.
- **Hover tooltips** on edge midpoints show UID, producer, consumer.
- Arrow annotations drawn along edges to indicate direction.
- Legend listing UIDs and their colors.

### Tab 2 - Symbiosis Matrix (Heatmap)

- Producer (rows) × Consumer (columns) heatmap.
- Cell value = count of shared UIDs between that pair.
- Hover tooltip shows list of shared UIDs.
- Plotly `go.Heatmap` with annotated text.

### Tab 3 - Connector Table

- Flat table of all external connectors across all models.
- Columns: Model, UID, Direction (IN/OUT), Type, Category.
- Direction filter (IN/OUT/All) via radio button.
- Rows styled by direction color.

### Tab 4 - Network Graph (WIP, Matplotlib)

- Alternative visualization using Matplotlib + NetworkX.
- Curved edges with separate arc radii for multi-UID pairs.
- Legend with UID colors.
- Rendered as a static PNG image.

### Tab 5 - Network Graph (WIP, ReactFlow)

- Uses `streamlit-flow-component` to render an interactive ReactFlow graph.
- Nodes are draggable; edges are animated.
- Minimap and zoom controls enabled.
- Experimental - may have rendering instability.

---

## 7. Page 4 - Multi-Model Integration

**File:** `Code/pages/4_Multi_Integration.py`

Combines heat streams from N selected models and performs joint pinch analysis to quantify heat recovery potential.

### Sidebar
- **Model multiselect** - requires ≥2 models.
- **Per-model capacity factor slider** - range derived from `UnitData.fmin`/`fmax` (defaults to 0.1–3.0 if not set). Scales all heat stream enthalpy values by the factor before merging.

### Tab 1 - Combined Heat Analysis

- Merges all heat streams from selected models (scaled by capacity factor).
- Calls `compute_pinch()` on the merged DataFrame.
- Plots:
  - **Composite Curves** (hot + cold, shifted temperatures) with Plotly.
  - **Grand Composite Curve** with shaded utility regions.
  - Pinch temperatures marked with dashed lines.
  - Qc,min and Qh,min gaps annotated.
- Utility metrics: Qc,min, Qh,min, pinch temperature.
- Expandable merged streams table.

### Tab 2 - Recovery Potential

- Comparison table: each model individually + arithmetic sum + combined (joint pinch) + recovered heat.
- Columns: Model, Qh,min, Qc,min, Pinch T.
- **Recovered heat** = sum(Qh,min individual) − Qh,min(combined).
- **CO₂ avoidance estimate** - natural gas assumption: 0.2 kgCO₂/kWh.
- Interpretation callout:
  - Recovered > 1 kW → success.
  - 0–1 kW → marginal.
  - < 0 → no synergy.

### Tab 3 - Stream Candidates

- Cross-model hot↔cold pairing: hot stream from model A paired with cold stream from model B.
- **Temperature overlap** computed per pair (overlap in shifted temperature intervals).
- **Q_candidate** = min(ΔH_hot, ΔH_cold) weighted by temperature overlap fraction.
- Results ranked by Q_candidate descending.
- Top candidate highlighted in a callout.
- **CSV export button** - downloads the full candidate table.

---

## 8. Page 5 - Upload

**File:** `Code/pages/5_Upload.py`

### Left panel - File input
- **Category selector** - dropdown from 18 categories.
- **XLSX/XLSM file uploader** - triggers `IETSParser(file).parse()` on change, result cached in `st.session_state`.
- **Optional BFD image** - PNG, JPG, or SVG.
- **Optional supplementary files** - PDF or Markdown, multiple allowed.

### Right panel - Preview
- Shown after successful parse.
- Metadata preview table: Model Name, UID, Authors, Version, TRL, Grade, Confidentiality.
- File info: unit count, category, BFD file name, supplementary file names.
- Parse warnings shown as `st.warning()` blocks.

### Import action

Triggered by **"Import Model"** button:

1. Creates `Code/models/<category>/<safe_model_name>/`.
2. Generates a filesystem-safe directory name (lowercase, spaces → underscores, special chars stripped).
3. Writes `<model_name>.json` (serialized `ParsedModel`).
4. Copies `.xlsx` source file.
5. Saves BFD image if provided.
6. Saves supplementary files (deduplicates by filename).
7. Updates `BLOCK FLOW DIAGRAM` and `SUPPLEMENTARY MATERIAL` metadata fields with absolute paths.
8. Calls `load_all_models.clear()` to invalidate cache.
9. Shows success message with saved path.
10. Renders **"Open in Model Detail"** button → navigates directly to the uploaded model.

---

## 9. Pinch Analysis Engine

**File:** `Code/engine/pinch.py`  
**Entry point:** `compute_pinch(heat_streams: pd.DataFrame, dTmin: float = 10.0) → PinchResult`

### Temperature shifting convention

```
Hot streams:   T_shifted = T - dtmin_contr / 2
Cold streams:  T_shifted = T + dtmin_contr / 2
```

`dtmin_contr` is read per-stream from the heat streams table (defaults to `dTmin` argument if missing).

### Algorithm (interval method)

1. **Validate and filter streams:**
   - Keep rows where `type` is `"Hot"` or `"Cold"`.
   - Coerce `T_in`, `T_out`, `H_in`, `H_out` to numeric; drop non-numeric rows.
   - Drop rows with `"SAT"` temperature values (emit warning).
   - Apply cascade label filter.

2. **Build breakpoints:**
   - Collect all shifted `T_lo` and `T_hi` values from all streams.
   - Sort descending, deduplicate within `1e-6 K` tolerance.

3. **Composite curves:**
   - For each temperature interval `[T_lo, T_hi]`, sum enthalpy contributions from all streams whose shifted range overlaps the interval.
   - Phase-change streams (`T_in ≈ T_out`): assign full `ΔH` to the degenerate band they fall into.
   - Build cumulative enthalpy arrays for hot and cold separately.

4. **Grand Composite Curve (GCC):**
   - Compute net surplus per interval: `surplus = ΔH_cold − ΔH_hot` (per interval, top-down).
   - Cascade residuals: `R[i] = R[i-1] + surplus[i]`.
   - Shift so `min(R) = 0`.
   - `Qh,min = −min_residual_before_shift`, `Qc,min = R[-1]`.
   - Pinch temperatures = intervals where `R ≤ 1e-6`.

5. **Edge cases handled:**
   - Multiple named cascades (filter by `heat_cascade` column).
   - `DEFAULT` cascade as fallback.
   - Phase-change streams.
   - Empty stream sets → return empty `PinchResult` with warnings.

---

## 10. Parser - IETS v6 Excel

**File:** `Code/parser/parser.py`  
**Class:** `IETSParser`

### Input

IETS v6 `.xlsx` / `.xlsm` workbook with sheets:
- `METADATA` - key-value pairs (23 fields).
- `CONNECTORS` - global external connectors.
- `INTERNAL_CONNECTORS` - cross-unit connectors.
- `VARIABLES` - model variables.
- `CALCULATIONS` - (optional) formula sheet.
- One sheet per unit (named by unit), each containing sub-tables:
  - `UNIT INFO` - `FMIN`, `FMAX`, unit description.
  - `HEAT STREAMS` - stream rows.
  - `CONNECTORS` - unit-level connectors.
  - `EQUIPMENTS` - equipment definitions.

### Output

`ParsedModel` dataclass (see §2.1).

### Key behaviors

- Sub-tables within unit sheets are located by scanning for header keywords (not fixed row offsets), making the parser robust to variable template layouts.
- Numeric coercion is applied to all quantitative fields.
- Warnings accumulated for missing sections or unparseable values; parser does not raise exceptions on partial data.

### excel_parser.py (standalone utility)

`Code/parser/excel_parser.py` - converts a v6 Excel file to a standalone JSON file without the Streamlit layer. Partially implements a `FormulaEvaluator` for basic arithmetic cell references; not used by the main app at runtime.

---

## 11. SVG Block Flow Diagram Generator

**File:** `Code/utils/diagram.py`

- Called by `loader.py` when a model has no BFD or the BFD file is missing.
- Loads `Code/assets/default_core.svg` as a template.
- Attempts to lay out unit blocks and connector arrows from model data.
- Current state: generates a minimal/generic SVG; full layout algorithm is partially implemented.
- Output saved to `<model_dir>/<model_name>_BFD.svg`.

---

## 12. Forum Backend

**File:** `Code/utils/forum.py`

Functions:
- `load_posts(model_dir: Path) → list[dict]` - reads `posts.json`; returns `[]` if missing.
- `save_posts(model_dir: Path, posts: list[dict])` - serializes posts list to `posts.json`.
- `new_post(username, title, text) → dict` - builds a post dict with `uuid4` ID and ISO timestamp.
- `new_comment(username, text) → dict` - builds a comment dict.
- `new_reply(username, text) → dict` - builds a reply dict.

No authentication or access control is implemented. Any username string is accepted.

---

## 13. Shared Utilities

### utils/categories.py
- Defines 18 category slugs and their display names.
- `CATEGORY_COLORS: dict[str, str]` - hex color per category, used for card chips and graph nodes.
- `get_category_from_path(path: str) → str` - infers category from model directory path.

### utils/constants.py
- Global constants: `DTMIN_DEFAULT`, `CO2_INTENSITY_NATGAS`, temperature tolerance values.
- `GRADE_COLORS`, `CONFIDENTIALITY_COLORS` - badge color maps.

### utils/styles.py
- `inject_css()` - injects custom CSS via `st.markdown()` for card layout, badge styling, metric tiles.
- `html_card(...)` - returns an HTML string for model overview cards.
- `badge(label, color)` - returns a small HTML badge span.

### utils/loader.py
- `load_all_models(data_dir: Path) → dict[str, ParsedModel]` - `@st.cache_resource` decorated.
- `_json_to_parsed_model(data: dict, filepath: str) → ParsedModel` - reconstructs DataFrames from JSON lists.
- `_ensure_bfd(model: ParsedModel, model_dir: Path)` - generates BFD if missing.

---

## 14. Key User Journeys

### A. Browse and inspect a model

```
User opens app → Catalog page loads (load_all_models cached)
→ User types in search bar or sets filters
→ Filtered model cards render
→ User clicks "View Details"
→ session_state["selected_model"] = key
→ st.switch_page → Model Detail page
→ Sidebar auto-selects the model
→ Overview tab renders with metadata, BFD, unit summary
→ User clicks "Heat Analysis" tab
→ compute_pinch() runs on unit heat streams
→ CC and GCC charts render with Plotly
```

### B. Explore connector compatibility

```
User opens Symbiosis page
→ load_all_models() (already cached)
→ All external connectors aggregated across models
→ Symbiosis pairs computed (shared UID, one IN + one OUT)
→ Network graph tab: spring layout computed via NetworkX
→ User filters by UID → graph updates
→ User switches to Matrix tab → heatmap shows pair counts
```

### C. Analyze multi-model heat integration

```
User opens Integration page
→ Multiselect: picks 2+ models
→ Adjusts capacity sliders
→ All heat streams merged, scaled by factor
→ compute_pinch() on merged streams
→ CC + GCC plotted for combined system
→ Recovery Potential tab: per-model vs. combined Qh,min compared
→ CO2 savings estimated
→ Stream Candidates tab: cross-model stream pairs ranked
→ User exports candidates as CSV
```

### D. Add a new model

```
User opens Upload page
→ Selects category
→ Uploads v6 Excel file
→ IETSParser.parse() runs → ParsedModel in session_state
→ Preview renders (metadata, unit count, warnings)
→ User uploads BFD image and supplementary PDF
→ Clicks "Import Model"
→ Folder created at models/<category>/<name>/
→ JSON + XLSX + BFD + PDF written to disk
→ load_all_models.clear() called
→ Success message shown
→ User clicks "Open in Model Detail" → navigates to new model
```

---

## 15. Known Technical Debt & Incomplete Features

### Incomplete / WIP

| Item | Location | Status |
|---|---|---|
| BFD auto-layout | `utils/diagram.py` | Generates minimal SVG; full block placement not implemented |
| Excel formula evaluator | `parser/excel_parser.py` | Stub - only basic arithmetic; cell references partial |
| ReactFlow graph (Tab 5) | `pages/3_Symbiosis.py` | Experimental; may have rendering issues in some browsers |
| Matplotlib graph (Tab 4) | `pages/3_Symbiosis.py` | Works but low interactivity compared to Plotly tab |
| Multi-model integration edge cases | `pages/4_Multi_Integration.py` | Core works; untested under extreme scale differences |

### Dead code

| File | Issue |
|---|---|
| `utils/FigureAnnotationAppUncorrectedv5.py` | Not imported anywhere; appears to be an abandoned standalone script |
| `parser/v6_json/` | Pre-converted JSON files kept for reference; not loaded at runtime |
| `parser/v6_excel/` | Template Excel files; not used at runtime |

### Missing validation

- **Upload page** - no schema validation beyond what the parser tolerates; a malformed Excel can silently produce a partially populated model.
- **Upload page** - no duplicate detection; importing a model with the same name and category overwrites the existing folder with a warning but no confirmation prompt.
- **Forum** - no authentication; any string is accepted as username.

### Hardcoded assumptions

- CO₂ intensity of natural gas: `0.2 kgCO₂/kWh` (hardcoded in `constants.py`, used in Tab 2 of Multi-Integration for CO₂ savings estimate).
- Reference temperature for Carnot GCC: `T₀ = 25 °C` (hardcoded in `pages/2_Model_Detail.py`).
- Default `dTmin = 10 °C` if not specified per stream.

### No concurrent write safety

Multiple simultaneous sessions writing `posts.json` or uploading models to the same path will silently overwrite each other. Acceptable for single-user or small-team use; would require a proper database or file locking for broader deployment.
