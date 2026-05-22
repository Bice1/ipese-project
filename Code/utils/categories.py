"""
Category definitions for IETS Task XXIV models.

All 18 categories from Lit Review/categories.txt with slugs, display names,
and hex colours.  MODEL_CATEGORY_MAP assigns the 11 existing models to their
respective category slugs.
"""

from __future__ import annotations

CATEGORIES: list[dict] = [
    {"slug": "heavy_industry",                   "name": "Heavy industry",                       "color": "#1B2A4A"},
    {"slug": "petrochemical",                    "name": "Petrochemical",                        "color": "#6B21A8"},
    {"slug": "nitrogen_chemistry",               "name": "Nitrogen chemistry",                   "color": "#9B1C1C"},
    {"slug": "precision_industries",             "name": "Precision industries",                 "color": "#0D9488"},
    {"slug": "urban_and_digital",                "name": "Urban & digital",                      "color": "#1D4ED8"},
    {"slug": "oxygenates_commodity_chemicals",   "name": "Oxygenates & commodity chemicals",     "color": "#06B6D4"},
    {"slug": "synthetic_fuels_biofuels",         "name": "Synthetic fuels & biofuels",           "color": "#166534"},
    {"slug": "food_and_beverage",                "name": "Food & beverage",                      "color": "#EA580C"},
    {"slug": "bio_and_waste",                    "name": "Bio & waste",                          "color": "#65A30D"},
    {"slug": "thermal_conversion",               "name": "Thermal conversion",                   "color": "#DC2626"},
    {"slug": "electrochemical",                  "name": "Electrochemical",                      "color": "#A855F7"},
    {"slug": "gas_upgrading_syngas",             "name": "Gas upgrading & syngas",               "color": "#CA8A04"},
    {"slug": "heat_recovery_upgrade",            "name": "Heat recovery & upgrade",              "color": "#14B8A6"},
    {"slug": "mass_energy_storage",              "name": "Mass & energy storage",                "color": "#EC4899"},
    {"slug": "power_and_utilities",              "name": "Power & utilities",                    "color": "#C2410C"},
    {"slug": "air_separation",                   "name": "Air separation",                       "color": "#2563EB"},
    {"slug": "renewables",                       "name": "Renewables",                           "color": "#4ADE80"},
    {"slug": "co2_capture",                      "name": "CO₂ capture, use & sequestration",     "color": "#6B7280"},
]

# Lookup helpers
CATEGORY_COLORS: dict[str, str] = {c["slug"]: c["color"] for c in CATEGORIES}
CATEGORY_DISPLAY_NAMES: dict[str, str] = {c["slug"]: c["name"] for c in CATEGORIES}
CATEGORY_SLUGS: list[str] = [c["slug"] for c in CATEGORIES]

# Model filename stem → category slug (for the 11 existing models).
# Key = exact stem of the JSON file (without extension), case-sensitive.
MODEL_CATEGORY_MAP: dict[str, str] = {
    "CCSAdsorption_v6":     "co2_capture",
    "CCSamines_v6":         "co2_capture",
    "CCSMembranes_v6":      "co2_capture",
    "cryoASU_v6":           "air_separation",
    "dualbedgasifFT_v6":    "synthetic_fuels_biofuels",
    "ElectroAlka_v6":       "electrochemical",
    "Heatpump_v6":          "heat_recovery_upgrade",
    "Methanator_v6":        "gas_upgrading_syngas",
    "PVpanel_v6":           "renewables",
    "Refrigerator_v6":      "power_and_utilities",
    "SOEC_Electrolyser_v6": "electrochemical",
}
