"""
Diagram generation service.

Provides helpers to generate a block flow diagram SVG from model JSON plus a core SVG.
Includes optional CLI helpers for local/testing usage.
"""

# ============================================================================
# CONFIGURATION PARAMETERS - Edit these to set default files (otherwise only passing the FOLDER_PATH is enough to run the code.)
# ============================================================================
FOLDER_PATH = "BeerProcessing"              # Folder containing JSON and SVG files
JSON_FILE = "BeerProcessing.json"           # Input JSON file with unit data (optional if folder is specified)
CORE_SVG_FILE = "furnace_generic.svg"  # Core SVG component to embed (optional if folder is specified)
OUTPUT_FILE = "output_diagram.svg"     # Output SVG diagram file
# ============================================================================

import glob
import io
import json
import os
import re
import sys
from xml.etree import ElementTree as ET

def load_json(json_path):
    """Load and parse the JSON configuration file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def load_core_svg(svg_path):
    """Load the core SVG component."""
    tree = ET.parse(svg_path)
    return tree.getroot()


def _value_only(value):
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def _first_value(item, keys, default=""):
    normalized = {}
    normalized_compact = {}
    for k in item.keys():
        raw = str(k).replace("\u00a0", " ")
        nk = " ".join(raw.strip().lower().split())
        normalized.setdefault(nk, k)
        normalized_compact.setdefault(nk.replace(" ", "").replace("/", ""), k)
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
        nk = " ".join(str(key).replace("\u00a0", " ").strip().lower().split())
        if nk in normalized:
            value = item.get(normalized[nk])
            if value not in (None, ""):
                return value
        compact = nk.replace(" ", "").replace("/", "")
        if compact in normalized_compact:
            value = item.get(normalized_compact[compact])
            if value not in (None, ""):
                return value
        for cand_compact, orig_key in normalized_compact.items():
            if compact and compact in cand_compact:
                value = item.get(orig_key)
                if value not in (None, ""):
                    return value
    return default


def _iter_units(data):
    units = data.get("UNITS", {})
    if isinstance(units, dict):
        for unit_name, unit_data in units.items():
            yield unit_name, unit_data
    elif isinstance(units, list):
        for unit_data in units:
            unit_name = (
                unit_data.get("Unit Info", {}).get("Unit name")
                or unit_data.get("Unit name")
                or unit_data.get("Name")
                or "Unit"
            )
            yield unit_name, unit_data


def extract_connectors(data):
    """Extract all connectors from all units in the JSON data."""
    connectors = []

    for unit_name, unit_data in _iter_units(data):
        for connector in unit_data.get("Connectors", []) or []:
            direction_raw = _first_value(
                connector,
                ["DIRECTION", "Direction", "FLOW DIRECTION", "Flow Direction", "IN/OUT", "In/Out"],
                ""
            )
            direction = str(direction_raw).strip().upper()
            if direction.startswith("IN"):
                direction = "IN"
            elif direction.startswith("OUT"):
                direction = "OUT"
            connector_info = {
                "unit": unit_name,
                "name": _first_value(connector, ["NAME (ALIAS)", "Alias", "NAME", "Name", "UID"], ""),
                "type": _first_value(connector, ["TYPE", "Type"], ""),
                "direction": direction,
                "value": _first_value(connector, ["VALUE", "Value", "FLOW VALUE", "FLOW VALUE/UNIT"], {}),
                "physical_unit": _first_value(connector, ["PHYSICAL UNIT", "Physical Unit", "FLOW UNIT"], ""),
                "temperature": _first_value(
                    connector,
                    ["TEMPERATURE", "Temperature", "TEMPERATURE VALUE", "TEMPERATURE VALUE/UNIT"],
                    ""
                ),
            }
            connectors.append(connector_info)

    return connectors


def extract_heat_streams(data):
    """Extract all heat streams from all units in the JSON data."""
    heat_streams = []

    for unit_name, unit_data in _iter_units(data):
        for stream in unit_data.get("Heat Streams", []) or []:
            stream_info = {
                "unit": unit_name,
                "name": _first_value(stream, ["NAME", "Name", "name"], ""),
                "type": _first_value(stream, ["TYPE", "Type", "type"], ""),
                "inlet_temp": _first_value(
                    stream,
                    [
                        "INLET TEMPERATURE VALUE",
                        "INLET TEMPERATURE VALUE/UNIT",
                        "Inlet Temperature [C]",
                        "Inlet Temperature",
                        "Tin"
                    ],
                    {}
                ),
                "outlet_temp": _first_value(
                    stream,
                    [
                        "OUTLET TEMPERATURE VALUE",
                        "OUTLET TEMPERATURE VALUE/UNIT",
                        "Outlet Temperature [C]",
                        "Outlet Temperature",
                        "Tout"
                    ],
                    {}
                ),
                "inlet_enthalpy": _first_value(
                    stream,
                    [
                        "INLET ENTHALPY FLOW VALUE",
                        "INLET ENTHALPY VALUE",
                        "INLET ENTHALPY VALUE/UNIT",
                        "Inlet Enthalpy Flow  [kW]",
                        "Inlet Enthalpy Flow [kW]",
                        "Hin"
                    ],
                    {}
                ),
                "outlet_enthalpy": _first_value(
                    stream,
                    [
                        "OUTLET ENTHALPY FLOW VALUE",
                        "OUTLET ENTHALPY VALUE",
                        "OUTLET ENTHALPY VALUE/UNIT",
                        "Outlet Enthalpy Flow [kW]",
                        "Outlet Enthalpy Flow  [kW]",
                        "Hout"
                    ],
                    {}
                ),
            }
            heat_streams.append(stream_info)

    return heat_streams


def format_value(value):
    """Format the value, handling both direct values and formula objects."""
    if isinstance(value, dict):
        if 'value' in value:
            val = value['value']
            if isinstance(val, (int, float)):
                return f"{val:,.2f}"
            return str(val)
    elif isinstance(value, (int, float)):
        return f"{value:,.2f}"
    return str(value)


def get_numeric_value(value):
    """Extract numeric value from value or dict."""
    if isinstance(value, dict):
        return float(value.get('value', 0))
    return float(value) if value else 0


def get_bfd_output_path(base_folder, filename):
    """Return the output path inside a BFDs subfolder, creating it when needed."""
    bfd_folder = os.path.join(base_folder, "BFDs")
    os.makedirs(bfd_folder, exist_ok=True)
    return os.path.join(bfd_folder, filename)


def create_arrow_marker(svg_ns):
    """Create arrow marker definition for SVG."""
    defs = ET.Element(f'{{{svg_ns}}}defs')

    # Arrow marker for inputs (pointing right)
    marker_in = ET.SubElement(defs, f'{{{svg_ns}}}marker', {
        'id': 'arrowIn',
        'markerWidth': '10',
        'markerHeight': '10',
        'refX': '9',
        'refY': '3',
        'orient': 'auto',
        'markerUnits': 'strokeWidth'
    })
    ET.SubElement(marker_in, f'{{{svg_ns}}}path', {
        'd': 'M0,0 L0,6 L9,3 z',
        'fill': '#000'
    })

    # Arrow marker for outputs (pointing right)
    marker_out = ET.SubElement(defs, f'{{{svg_ns}}}marker', {
        'id': 'arrowOut',
        'markerWidth': '10',
        'markerHeight': '10',
        'refX': '9',
        'refY': '3',
        'orient': 'auto',
        'markerUnits': 'strokeWidth'
    })
    ET.SubElement(marker_out, f'{{{svg_ns}}}path', {
        'd': 'M0,0 L0,6 L9,3 z',
        'fill': '#000'
    })

    return defs


def draw_heat_streams_table(root, svg_ns, heat_streams, diagram_start_y, diagram_width):
    """Draw separate tables for hot and cold heat streams side by side below the main block diagram."""
    if not heat_streams:
        return diagram_start_y  # No heat streams, return same Y position

    # Separate hot and cold streams (case-insensitive)
    hot_streams = [s for s in heat_streams if str(s.get("type", "")).upper() == "HOT"]
    cold_streams = [s for s in heat_streams if str(s.get("type", "")).upper() == "COLD"]

    # If only one type exists, use single centered table
    if not hot_streams or not cold_streams:
        all_streams = hot_streams if hot_streams else cold_streams
        title_text = "Hot Streams" if hot_streams else "Cold Streams"
        title_color = '#dc2626' if hot_streams else '#2563eb'
        row_fill = '#fee2e2' if hot_streams else '#dbeafe'

        current_y = diagram_start_y + 60
        row_height = 30
        header_height = 35
        col_widths = [200, 150, 150, 150, 150]
        total_width = sum(col_widths)
        table_x = (diagram_width - total_width) / 2

        return draw_single_centered_table(root, svg_ns, all_streams, title_text, title_color,
                                          row_fill, current_y, table_x, col_widths,
                                          row_height, header_height)

    # Both hot and cold streams exist - draw side by side
    current_y = diagram_start_y + 60
    row_height = 30
    header_height = 35

    # Calculate table width to fit side by side with spacing
    table_gap = 40  # Gap between two tables
    available_width = diagram_width - 100  # Leave 50px padding on each side
    single_table_width = (available_width - table_gap) / 2

    # Adjust column widths proportionally to fit
    col_widths = [single_table_width * 0.25, single_table_width * 0.1875,
                  single_table_width * 0.1875, single_table_width * 0.1875,
                  single_table_width * 0.1875]

    # Position tables
    left_table_x = 50
    right_table_x = 50 + single_table_width + table_gap

    # Determine which table has more rows to calculate the height needed
    max_rows = max(len(hot_streams), len(cold_streams))

    # Draw hot streams table (left)
    hot_bottom_y = draw_side_by_side_table(root, svg_ns, hot_streams, "Hot Streams",
                                           '#dc2626', '#fee2e2', current_y, left_table_x,
                                           col_widths, row_height, header_height, single_table_width)

    # Draw cold streams table (right) - starts at same Y position
    cold_bottom_y = draw_side_by_side_table(root, svg_ns, cold_streams, "Cold Streams",
                                            '#2563eb', '#dbeafe', current_y, right_table_x,
                                            col_widths, row_height, header_height, single_table_width)

    # Return the maximum bottom Y position
    return max(hot_bottom_y, cold_bottom_y)


def draw_single_centered_table(root, svg_ns, streams, title_text, title_color, row_fill,
                                start_y, table_x, col_widths, row_height, header_height):
    """Draw a single centered table (used when only hot or cold streams exist)."""
    total_width = sum(col_widths)

    # Draw title
    title = ET.SubElement(root, f'{{{svg_ns}}}text', {
        'x': str(table_x + total_width / 2),
        'y': str(start_y - 20),
        'text-anchor': 'middle',
        'font-size': '16',
        'font-weight': 'bold',
        'fill': title_color
    })
    title.text = title_text

    # Draw header row background
    ET.SubElement(root, f'{{{svg_ns}}}rect', {
        'x': str(table_x),
        'y': str(start_y),
        'width': str(total_width),
        'height': str(header_height),
        'fill': '#e5e7eb',
        'stroke': '#333',
        'stroke-width': '1'
    })

    # Draw header text
    headers = ['Name', 'T inlet [°C]', 'T outlet [°C]', 'H inlet [kW]', 'H outlet [kW]']
    x_pos = table_x
    for i, header in enumerate(headers):
        if i > 0:
            ET.SubElement(root, f'{{{svg_ns}}}line', {
                'x1': str(x_pos),
                'y1': str(start_y),
                'x2': str(x_pos),
                'y2': str(start_y + header_height),
                'stroke': '#333',
                'stroke-width': '1'
            })

        header_text = ET.SubElement(root, f'{{{svg_ns}}}text', {
            'x': str(x_pos + col_widths[i] / 2),
            'y': str(start_y + header_height / 2 + 5),
            'text-anchor': 'middle',
            'font-size': '12',
            'font-weight': 'bold',
            'fill': '#333'
        })
        header_text.text = header
        x_pos += col_widths[i]

    # Draw data rows
    table_y = start_y + header_height
    for stream in streams:
        name = stream['name']
        inlet_temp = format_value(stream['inlet_temp'])
        outlet_temp = format_value(stream['outlet_temp'])
        inlet_enth = format_value(stream['inlet_enthalpy'])
        outlet_enth = format_value(stream['outlet_enthalpy'])

        ET.SubElement(root, f'{{{svg_ns}}}rect', {
            'x': str(table_x),
            'y': str(table_y),
            'width': str(total_width),
            'height': str(row_height),
            'fill': row_fill,
            'stroke': '#333',
            'stroke-width': '1'
        })

        row_data = [name, inlet_temp, outlet_temp, inlet_enth, outlet_enth]
        x_pos = table_x
        for i, data in enumerate(row_data):
            if i > 0:
                ET.SubElement(root, f'{{{svg_ns}}}line', {
                    'x1': str(x_pos),
                    'y1': str(table_y),
                    'x2': str(x_pos),
                    'y2': str(table_y + row_height),
                    'stroke': '#333',
                    'stroke-width': '1'
                })

            cell_text = ET.SubElement(root, f'{{{svg_ns}}}text', {
                'x': str(x_pos + col_widths[i] / 2),
                'y': str(table_y + row_height / 2 + 5),
                'text-anchor': 'middle',
                'font-size': '11',
                'font-weight': 'normal',
                'fill': '#333'
            })
            cell_text.text = str(data)
            x_pos += col_widths[i]

        table_y += row_height

    return table_y + 40


def draw_side_by_side_table(root, svg_ns, streams, title_text, title_color, row_fill,
                             start_y, table_x, col_widths, row_height, header_height, table_width):
    """Draw a table for side-by-side layout."""
    if not streams:
        return start_y

    # Draw title
    title = ET.SubElement(root, f'{{{svg_ns}}}text', {
        'x': str(table_x + table_width / 2),
        'y': str(start_y - 20),
        'text-anchor': 'middle',
        'font-size': '16',
        'font-weight': 'bold',
        'fill': title_color
    })
    title.text = title_text

    # Draw header row background
    ET.SubElement(root, f'{{{svg_ns}}}rect', {
        'x': str(table_x),
        'y': str(start_y),
        'width': str(table_width),
        'height': str(header_height),
        'fill': '#e5e7eb',
        'stroke': '#333',
        'stroke-width': '1'
    })

    # Draw header text
    headers = ['Name', 'T in [°C]', 'T out [°C]', 'H in [kW]', 'H out [kW]']
    x_pos = table_x
    for i, header in enumerate(headers):
        if i > 0:
            ET.SubElement(root, f'{{{svg_ns}}}line', {
                'x1': str(x_pos),
                'y1': str(start_y),
                'x2': str(x_pos),
                'y2': str(start_y + header_height),
                'stroke': '#333',
                'stroke-width': '1'
            })

        header_text = ET.SubElement(root, f'{{{svg_ns}}}text', {
            'x': str(x_pos + col_widths[i] / 2),
            'y': str(start_y + header_height / 2 + 5),
            'text-anchor': 'middle',
            'font-size': '14',
            'font-weight': 'bold',
            'fill': '#333'
        })
        header_text.text = header
        x_pos += col_widths[i]

    # Draw data rows
    table_y = start_y + header_height
    for stream in streams:
        name = stream['name']
        inlet_temp = format_value(stream['inlet_temp'])
        outlet_temp = format_value(stream['outlet_temp'])
        inlet_enth = format_value(stream['inlet_enthalpy'])
        outlet_enth = format_value(stream['outlet_enthalpy'])

        ET.SubElement(root, f'{{{svg_ns}}}rect', {
            'x': str(table_x),
            'y': str(table_y),
            'width': str(table_width),
            'height': str(row_height),
            'fill': row_fill,
            'stroke': '#333',
            'stroke-width': '1'
        })

        row_data = [name, inlet_temp, outlet_temp, inlet_enth, outlet_enth]
        x_pos = table_x
        for i, data in enumerate(row_data):
            if i > 0:
                ET.SubElement(root, f'{{{svg_ns}}}line', {
                    'x1': str(x_pos),
                    'y1': str(table_y),
                    'x2': str(x_pos),
                    'y2': str(table_y + row_height),
                    'stroke': '#333',
                    'stroke-width': '1'
                })

            cell_text = ET.SubElement(root, f'{{{svg_ns}}}text', {
                'x': str(x_pos + col_widths[i] / 2),
                'y': str(table_y + row_height / 2 + 5),
                'text-anchor': 'middle',
                'font-size': '13',
                'font-weight': 'normal',
                'fill': '#333'
            })
            cell_text.text = str(data)
            x_pos += col_widths[i]

        table_y += row_height

    return table_y + 40


def get_unit_name(data):
    """Extract the unit name from JSON data."""
    units = data.get("UNITS") or {}
    if isinstance(units, dict) and units:
        unit_name = next(iter(units.keys()))
        unit_data = units.get(unit_name, {})
        return unit_data.get("Unit Info", {}).get("Unit name") or unit_name
    if isinstance(units, list) and units:
        unit_data = units[0]
        return (
            unit_data.get("Unit Info", {}).get("Unit name")
            or unit_data.get("Unit name")
            or unit_data.get("Name")
            or "Diagram"
        )
    return "Diagram"


def build_svg_content(data, core_svg_path, unit_name=None):
    """Build SVG content for the block diagram."""
    # If unit_name is specified, filter to only that unit
    if unit_name:
        units = data.get("UNITS") or {}
        if isinstance(units, dict) and unit_name in units:
            filtered_data = {
                "METADATA": data.get("METADATA", {}),
                "UNITS": {unit_name: units[unit_name]}
            }
            data = filtered_data
        elif isinstance(units, list):
            matched = None
            for unit_data in units:
                candidate = (
                    unit_data.get("Unit Info", {}).get("Unit name")
                    or unit_data.get("Unit name")
                    or unit_data.get("Name")
                )
                if candidate == unit_name:
                    matched = unit_data
                    break
            if matched:
                data = {"METADATA": data.get("METADATA", {}), "UNITS": [matched]}
            else:
                raise ValueError(f"Unit '{unit_name}' not found in JSON")
        else:
            raise ValueError(f"Unit '{unit_name}' not found in JSON")

    core_svg = load_core_svg(core_svg_path)
    unit_name_for_title = unit_name or get_unit_name(data)
    replace_default_core_label = os.path.basename(str(core_svg_path)) == "default_core.svg"

    # Extract connectors and heat streams
    connectors = extract_connectors(data)
    heat_streams = extract_heat_streams(data)

    # Get SVG namespace
    svg_ns = 'http://www.w3.org/2000/svg'

    # Create new SVG root
    # Calculate dimensions based on number of connectors
    num_inputs = sum(1 for c in connectors if c['direction'] == 'IN')
    num_outputs = sum(1 for c in connectors if c['direction'] == 'OUT')
    max_connectors = max(num_inputs, num_outputs, 1)

    # Larger canvas to accommodate everything
    diagram_width = 2000
    diagram_height = max(1200, 400 + max_connectors * 180)

    root = ET.Element(f'{{{svg_ns}}}svg', {
        'xmlns': svg_ns,
        'width': str(diagram_width),
        'height': str(diagram_height),
        'viewBox': f'0 0 {diagram_width} {diagram_height}'
    })

    # Add arrow markers
    defs = create_arrow_marker(svg_ns)
    root.append(defs)

    # Position connectors (calculate before title for width adjustment)
    center_x = 1000  # Center of wider canvas

    # Calculate center_y based on number of connectors to ensure proper spacing
    num_inputs_initial = sum(1 for c in connectors if c['direction'] == 'IN')
    num_outputs_initial = sum(1 for c in connectors if c['direction'] == 'OUT')
    max_connectors_initial = max(num_inputs_initial, num_outputs_initial, 1)

    # Center Y should accommodate all connectors with 100px spacing
    # Start from a reasonable top position and calculate based on connectors
    # Add extra space for title above the block
    top_margin = 150  # Increased to accommodate title above block
    center_y = top_margin + (max_connectors_initial - 1) * 50

    # Get original SVG dimensions
    core_width = float(core_svg.get('width', '426').replace('px', ''))
    core_height = float(core_svg.get('height', '237').replace('px', ''))

    # STEP 1: Determine block size based on number of flows
    # Arrows are spaced 100px apart vertically
    arrow_span = (max_connectors_initial - 1) * 100 if max_connectors_initial > 1 else 100

    # Block height: based on connectors + padding
    vertical_padding = 25  # Padding above first and below last arrow
    calculated_height = arrow_span + (2 * vertical_padding)

    # Apply minimum block dimensions to ensure core SVG is visible
    min_block_width = 500
    min_block_height = 400
    BLOCK_HEIGHT = max(min_block_height, calculated_height)

    # STEP 2: Calculate dynamic block width based on core SVG aspect ratio
    # Start with a width that maintains the core SVG aspect ratio relative to block height
    margin = 10  # Margin inside the block

    # Calculate what width we need to maintain core SVG aspect ratio
    # given the available height
    available_height = BLOCK_HEIGHT - (2 * margin)
    aspect_ratio = core_width / core_height

    # Calculate width needed to fit core SVG at its aspect ratio
    needed_width_for_height = available_height * aspect_ratio + (2 * margin)

    # Apply min and max constraints
    max_block_width = 900
    BLOCK_WIDTH = max(min_block_width, min(max_block_width, needed_width_for_height))

    # STEP 3: Scale the core SVG to fit inside the block
    available_width = BLOCK_WIDTH - (2 * margin)
    available_height = BLOCK_HEIGHT - (2 * margin)

    # Calculate scale to fit core SVG inside available space
    scale_x = available_width / core_width
    scale_y = available_height / core_height
    scale = min(scale_x, scale_y)  # Use smaller scale to fit both dimensions

    # Calculate position to center the scaled SVG
    translate_x = center_x - (core_width * scale / 2)
    translate_y = center_y - (core_height * scale / 2)

    # Separate inputs and outputs early to calculate dimensions
    inputs = [c for c in connectors if c['direction'] == 'IN']
    outputs = [c for c in connectors if c['direction'] == 'OUT']

    # Use the predetermined block dimensions
    block_width = BLOCK_WIDTH
    block_height = BLOCK_HEIGHT
    block_x = center_x - (block_width / 2)
    block_y = center_y - (block_height / 2)

    # Calculate the actual width needed based on connectors
    min_x = 50 if inputs else block_x - 10  # Left edge: start of input arrows or block edge
    max_x = diagram_width - 45 if outputs else block_x + block_width + 10  # Right edge: end of output labels or block edge
    actual_width = max_x - min_x + 100  # Add padding

    # Adjust all x-coordinates if we're trimming left whitespace
    x_offset = -min_x + 50 if not inputs else 0

    # Apply x_offset for positioning when trimming whitespace
    translate_x_adjusted = translate_x + x_offset
    block_x_adjusted = block_x + x_offset

    # Embed core SVG in the center
    core_group = ET.SubElement(root, f'{{{svg_ns}}}g', {
        'transform': f'translate({translate_x_adjusted}, {translate_y}) scale({scale})'
    })

    # Copy all elements from core SVG to the group, preserving structure
    def clean_element(elem, parent_is_foreign=False):
        """Recursively copy element preserving namespaces where needed."""
        tag = elem.tag

        # Check if this element is foreignObject or inside one
        is_foreign_or_child = 'foreignObject' in str(tag) or parent_is_foreign or 'xhtml' in str(tag)

        if is_foreign_or_child:
            # Preserve full tag and ALL attributes for foreignObject and HTML content
            new_elem = ET.Element(tag)
            for key, value in elem.attrib.items():
                new_elem.set(key, value)
        else:
            # For SVG elements, clean the tag and skip xmlns
            clean_tag = tag.split('}')[-1] if '}' in tag else tag
            new_elem = ET.Element(clean_tag)
            for key, value in elem.attrib.items():
                if 'xmlns' not in key.lower():
                    new_elem.set(key, value)

        # Copy text and tail
        new_elem.text = elem.text
        if replace_default_core_label and isinstance(new_elem.text, str):
            if new_elem.text.strip() == "Core SVG":
                new_elem.text = unit_name_for_title
        new_elem.tail = elem.tail

        # Recursively copy children, passing foreign context
        for child in elem:
            new_elem.append(clean_element(child, is_foreign_or_child))

        return new_elem

    for child in core_svg:
        core_group.append(clean_element(child))

    # Draw a background rectangle for the block with more padding
    ET.SubElement(root, f'{{{svg_ns}}}rect', {
        'x': str(block_x_adjusted - 20),
        'y': str(block_y - 20),
        'width': str(block_width + 40),
        'height': str(block_height + 40),
        'fill': 'none',
        'stroke': '#666',
        'stroke-width': '2',
        'stroke-dasharray': '5,5',
        'rx': '10'
    })

    # Calculate the actual bounding box of all elements
    # Title is at block_y - 40, need to ensure it's visible
    title_position_y = block_y - 40

    # Calculate max Y from all elements
    max_y_input = max([center_y - (len(inputs) - 1) * 50 + i * 100 + 25 for i in range(len(inputs))], default=0)
    max_y_output = max([center_y - (len(outputs) - 1) * 50 + i * 100 + 25 for i in range(len(outputs))], default=0)
    max_y_block = block_y + block_height + 20  # Block + padding for dashed border
    actual_max_y = max(max_y_input, max_y_output, max_y_block)

    # Calculate actual canvas dimensions needed
    # Height needs to accommodate from title (with padding) to bottom element (with padding)
    top_padding = 30  # Padding above title
    bottom_padding = 30  # Padding below bottom element
    min_y = title_position_y - top_padding
    actual_canvas_height = actual_max_y - min_y + bottom_padding

    # Update SVG dimensions to fit all content
    root.set('height', str(int(actual_canvas_height)))
    root.set('width', str(int(actual_width)))
    root.set('viewBox', f'0 {int(min_y)} {int(actual_width)} {int(actual_canvas_height)}')

    # Add white background that covers the entire viewBox
    background = ET.Element(f'{{{svg_ns}}}rect', {
        'x': '0',
        'y': str(int(min_y)),
        'width': str(int(actual_width)),
        'height': str(int(actual_canvas_height)),
        'fill': 'white'
    })
    # Insert background as first element after defs
    root.insert(1, background)

    # Add title above the main block
    title_x = actual_width / 2
    title_y = block_y - 40  # Position 40px above the block
    title_text = ET.SubElement(root, f'{{{svg_ns}}}text', {
        'x': str(title_x),
        'y': str(title_y),
        'text-anchor': 'middle',
        'font-size': '24',
        'font-weight': 'bold',
        'fill': '#333'
    })
    # Use unit name for title instead of model name
    title_text.text = f"{unit_name_for_title} - Block Flow Diagram"

    # Draw input arrows (coming from left)
    for i, connector in enumerate(inputs):
        y_pos = center_y - (len(inputs) - 1) * 50 + i * 100

        # Label box
        label_text = f"{connector['name']}"
        value_text = f"{format_value(connector['value'])} {connector['physical_unit']}"

        label_bg = ET.SubElement(root, f'{{{svg_ns}}}rect', {
            'x': '55',
            'y': str(y_pos - 25),
            'width': '200',
            'height': '50',
            'fill': 'white',
            'stroke': '#2563eb',
            'stroke-width': '1',
            'rx': '5'
        })

        label = ET.SubElement(root, f'{{{svg_ns}}}text', {
            'x': '155',
            'y': str(y_pos - 5),
            'text-anchor': 'middle',
            'font-size': '14',
            'font-weight': 'bold',
            'fill': '#2563eb'
        })
        label.text = label_text

        value = ET.SubElement(root, f'{{{svg_ns}}}text', {
            'x': '155',
            'y': str(y_pos + 12),
            'text-anchor': 'middle',
            'font-size': '12',
            'fill': '#555'
        })
        value.text = value_text

        # Arrow line starting from right edge of label box
        arrow_gap = 20  # Fixed distance from arrow to block
        arrow_start_x = 255  # Right edge of label box (55 + 200)
        arrow_end_x = block_x_adjusted - arrow_gap
        ET.SubElement(root, f'{{{svg_ns}}}line', {
            'x1': str(arrow_start_x),
            'y1': str(y_pos),
            'x2': str(arrow_end_x),
            'y2': str(y_pos),
            'stroke': '#2563eb',
            'stroke-width': '2',
            'marker-end': 'url(#arrowIn)'
        })

    # Draw output arrows (going to right)
    for i, connector in enumerate(outputs):
        y_pos = center_y - (len(outputs) - 1) * 50 + i * 100

        # Calculate output arrow end position with fixed spacing
        arrow_gap = 20  # Fixed distance from block to arrow
        arrow_start_x = block_x_adjusted + block_width + arrow_gap
        arrow_end_x = actual_width - 250 if outputs else arrow_start_x + 100

        # Arrow line
        ET.SubElement(root, f'{{{svg_ns}}}line', {
            'x1': str(arrow_start_x),
            'y1': str(y_pos),
            'x2': str(arrow_end_x),
            'y2': str(y_pos),
            'stroke': '#dc2626',
            'stroke-width': '2',
            'marker-end': 'url(#arrowOut)'
        })

        # Label
        label_text = f"{connector['name']}"
        value_text = f"{format_value(connector['value'])} {connector['physical_unit']}"

        label_x = arrow_end_x + 5
        label_bg = ET.SubElement(root, f'{{{svg_ns}}}rect', {
            'x': str(label_x),
            'y': str(y_pos - 25),
            'width': '200',
            'height': '50',
            'fill': 'white',
            'stroke': '#dc2626',
            'stroke-width': '1',
            'rx': '5'
        })

        label = ET.SubElement(root, f'{{{svg_ns}}}text', {
            'x': str(label_x + 100),
            'y': str(y_pos - 5),
            'text-anchor': 'middle',
            'font-size': '14',
            'font-weight': 'bold',
            'fill': '#dc2626'
        })
        label.text = label_text

        value = ET.SubElement(root, f'{{{svg_ns}}}text', {
            'x': str(label_x + 100),
            'y': str(y_pos + 12),
            'text-anchor': 'middle',
            'font-size': '12',
            'fill': '#555'
        })
        value.text = value_text

    # Draw heat streams table if they exist
    table_bottom_y = draw_heat_streams_table(root, svg_ns, heat_streams, actual_max_y, actual_width)

    # Update canvas height to include heat streams table
    if heat_streams:
        actual_canvas_height = table_bottom_y - min_y + bottom_padding
        root.set('height', str(int(actual_canvas_height)))
        root.set('viewBox', f'0 {int(min_y)} {int(actual_width)} {int(actual_canvas_height)}')
        # Update background height
        background.set('height', str(int(actual_canvas_height)))

    # Build output content
    tree = ET.ElementTree(root)
    ET.register_namespace('', svg_ns)

    # Write to a temporary string first to clean up duplicate xmlns
    temp_output = io.BytesIO()
    tree.write(temp_output, encoding='utf-8', xml_declaration=True)

    # Read back and fix duplicate xmlns declarations
    svg_content = temp_output.getvalue().decode('utf-8')

    # Remove duplicate xmlns declarations (keep only the first one)
    # This regex finds duplicate xmlns="..." after the first one in the svg tag
    svg_content = re.sub(
        r'(<svg[^>]*xmlns="http://www\.w3\.org/2000/svg"[^>]*)\s+xmlns="http://www\.w3\.org/2000/svg"',
        r'\1',
        svg_content
    )

    return svg_content


def generate_block_flow_svg(model_data, core_svg_path, unit_name=None):
    """Public service API for block flow diagram generation."""
    return build_svg_content(model_data, core_svg_path, unit_name=unit_name)


def generate_diagram(json_path, core_svg_path, output_path, unit_name=None):
    """Generate the complete block diagram and write it to a file."""
    data = load_json(json_path)
    svg_content = build_svg_content(data, core_svg_path, unit_name=unit_name)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    print(f"Diagram generated successfully: {output_path}")
    print(f"![Test]({output_path}) ")


def find_svg_in_folder(folder_path):
    """Find SVG files in the specified folder."""
    # Find all SVG files
    svg_files = glob.glob(os.path.join(folder_path, "*.svg"))
    # Exclude generated diagram files from the list
    svg_files = [f for f in svg_files if not (f.endswith('output_diagram.svg') or f.endswith('_BFD.svg'))]

    if not svg_files:
        print(f"Error: No SVG files found in {folder_path}")
        return None

    # Use the first SVG file found
    core_svg_path = svg_files[0]

    if len(svg_files) > 1:
        print(f"Warning: Multiple SVG files found. Using: {os.path.basename(core_svg_path)}")

    return core_svg_path


def find_files_in_folder(folder_path):
    """Find JSON and SVG files in the specified folder."""
    # Find all JSON files
    json_files = glob.glob(os.path.join(folder_path, "*.json"))

    # Find all SVG files
    core_svg_path = find_svg_in_folder(folder_path)

    if not json_files:
        print(f"Error: No JSON files found in {folder_path}")
        return None, None

    if core_svg_path is None:
        return None, None

    # Use the first JSON file found
    json_path = json_files[0]

    if len(json_files) > 1:
        print(f"Warning: Multiple JSON files found. Using: {os.path.basename(json_path)}")

    return json_path, core_svg_path


def process_json_with_multiple_units(json_path, folder_path):
    """Process a JSON file that may contain multiple units."""
    data = load_json(json_path)

    # Check if there are multiple units
    if 'UNITS' not in data or not data['UNITS']:
        print("Error: No UNITS found in JSON")
        return False

    unit_names = [unit_name for unit_name, _ in _iter_units(data)]

    if len(unit_names) == 1:
        # Single unit - use original logic
        return None  # Signal to use original single-unit logic

    # Multiple units - generate a diagram for each
    print(f"Found {len(unit_names)} units in JSON: {', '.join(unit_names)}")
    print()

    success_count = 0
    for unit_name in unit_names:
        # Look for corresponding SVG file for this unit
        svg_path = os.path.join(folder_path, f"{unit_name}.svg")

        if not os.path.exists(svg_path):
            print(f"Warning: SVG file not found for unit '{unit_name}': {svg_path}")
            print(f"  Skipping this unit.")
            print()
            continue

        # Generate output filename
        output_filename = f"{unit_name}_BFD.svg"
        output_path = get_bfd_output_path(folder_path, output_filename)

        print(f"Processing unit: {unit_name}")
        print(f"  Core SVG: {os.path.basename(svg_path)}")
        print(f"  Output: {os.path.join('BFDs', output_filename)}")

        # Generate diagram for this specific unit
        generate_diagram(json_path, svg_path, output_path, unit_name=unit_name)
        success_count += 1
        print()

    print(f"Successfully generated {success_count} out of {len(unit_names)} diagrams")
    return True


def main():
    # Use command-line arguments if provided, otherwise use defaults from top of file
    if len(sys.argv) >= 4:
        # Three arguments: json_file, core_svg_file, output_svg
        json_path = sys.argv[1]
        core_svg_path = sys.argv[2]
        output_path = sys.argv[3]
        print(f"Using provided files:")
        print(f"  JSON file: {json_path}")
        print(f"  Core SVG: {core_svg_path}")
        print(f"  Output: {output_path}")
        print()
    elif len(sys.argv) == 2:
        arg = sys.argv[1]

        # Check if argument is a folder or a JSON file
        if os.path.isdir(arg):
            # It's a folder - auto-detect both JSON and SVG
            folder_path = arg
            json_path, core_svg_path = find_files_in_folder(folder_path)
            if json_path is None or core_svg_path is None:
                sys.exit(1)

            print(f"Processing folder: {folder_path}")
            print(f"  JSON file: {os.path.basename(json_path)}")
            print()

            # Check if JSON has multiple units
            result = process_json_with_multiple_units(json_path, folder_path)
            if result is True:
                # Successfully processed multiple units
                sys.exit(0)
            # If result is None, continue with single-unit logic below

            # Single unit logic
            data = load_json(json_path)
            unit_name = get_unit_name(data)
            output_filename = f"{unit_name}_BFD.svg"
            output_path = get_bfd_output_path(folder_path, output_filename)

            print(f"  Core SVG: {os.path.basename(core_svg_path)}")
            print(f"  Output: {os.path.join('BFDs', output_filename)}")
            print()
        elif os.path.isfile(arg) and arg.endswith('.json'):
            # It's a JSON file - auto-detect SVG in same folder
            json_path = arg
            folder_path = os.path.dirname(json_path) or '.'

            print(f"Processing JSON file: {json_path}")
            print()

            # Check if JSON has multiple units
            result = process_json_with_multiple_units(json_path, folder_path)
            if result is True:
                # Successfully processed multiple units
                sys.exit(0)
            # If result is None, continue with single-unit logic below

            core_svg_path = find_svg_in_folder(folder_path)
            if core_svg_path is None:
                sys.exit(1)

            # Single unit logic
            data = load_json(json_path)
            unit_name = get_unit_name(data)
            output_filename = f"{unit_name}_BFD.svg"
            output_path = get_bfd_output_path(folder_path, output_filename)

            print(f"  Core SVG (auto-detected): {os.path.basename(core_svg_path)}")
            print(f"  Output: {os.path.join('BFDs', output_filename)}")
            print()
        else:
            print(f"Error: '{arg}' is not a valid directory or JSON file")
            sys.exit(1)
    elif len(sys.argv) == 1:
        # No arguments provided, use configuration parameters at top of file
        folder_path = FOLDER_PATH

        # Check if we should auto-find files or use specified ones
        if folder_path != "." and os.path.isdir(folder_path):
            json_path, core_svg_path = find_files_in_folder(folder_path)
            if json_path is None or core_svg_path is None:
                sys.exit(1)

            print(f"Using default configuration:")
            print(f"  Folder: {folder_path}")
            print(f"  JSON file: {os.path.basename(json_path)}")
            print()

            # Check if JSON has multiple units
            result = process_json_with_multiple_units(json_path, folder_path)
            if result is True:
                # Successfully processed multiple units
                sys.exit(0)
            # If result is None, continue with single-unit logic below

            # Single unit logic
            data = load_json(json_path)
            unit_name = get_unit_name(data)
            output_filename = f"{unit_name}_BFD.svg"
            output_path = get_bfd_output_path(folder_path, output_filename)

            print(f"  Core SVG: {os.path.basename(core_svg_path)}")
            print(f"  Output: {os.path.join('BFDs', output_filename)}")
            print()
        else:
            json_path = JSON_FILE
            core_svg_path = CORE_SVG_FILE
            output_dir = "BFDs"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, OUTPUT_FILE)

            print(f"Using default configuration:")
            print(f"  JSON file: {json_path}")
            print(f"  Core SVG: {core_svg_path}")
            print(f"  Output: {os.path.join('BFDs', OUTPUT_FILE)}")
            print()
    else:
        print("Usage: python generate_diagram.py [path]")
        print("   OR: python generate_diagram.py [json_file] [core_svg_file] [output_svg]")
        print()
        print("Arguments:")
        print("  path          - Path to folder OR JSON file")
        print("                  If folder: auto-detects JSON and SVG files")
        print("                  If JSON file: auto-detects SVG in same folder")
        print()
        print("  json_file     - Specific JSON file path")
        print("  core_svg_file - Specific core SVG file path")
        print("  output_svg    - Output SVG file path")
        print()
        print("If no arguments provided, uses configuration parameters at top of script")
        print()
        print("Examples:")
        print("  python generate_diagram.py ./models/furnace/")
        print("  python generate_diagram.py ./models/furnace/NGFurnace.json")
        print("  python generate_diagram.py NGFurnace.json furnace_generic.svg output.svg")
        sys.exit(1)

    generate_diagram(json_path, core_svg_path, output_path)


if __name__ == '__main__':
    main()
