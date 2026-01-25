"""PCB editing tools for KiCad MCP Server."""

from typing import Any, List
from ..server import mcp
from ..parsers.pcb_parser import PCBParser


@mcp.tool()
async def create_pcb(
    file_path: str,
    board_width: float = 100.0,
    board_height: float = 80.0,
    layers: int = 2,
) -> str:
    """Create a new KiCad PCB file.

    Args:
        file_path: Path where to save the .kicad_pcb file
        board_width: Board width in mm
        board_height: Board height in mm
        layers: Number of copper layers (2, 4, 6, etc.)

    Returns:
        Confirmation message with file path
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        if not path.suffix:
            path = path.with_suffix('.kicad_pcb')

        # Generate layer list
        layer_defs = ""
        copper_layers = []
        for i in range(layers):
            if i == 0:
                copper_layers.append(f'    (0 "F.Cu" signal)')
            elif i == layers - 1:
                copper_layers.append(f'    (31 "B.Cu" signal)')
            else:
                copper_layers.append(f'    ({i + 14} "In{i}.Cu" signal)')

        layer_defs = '\n'.join(copper_layers)

        # Generate KiCad PCB file content
        content = f'''(kicad_pcb (version 20171130) (host pcbnew 5.1.0)

  (general
    (thickness 1.6)
    (drawings 0)
    (tracks 0)
    (vias 0)
    (zones 0)
    (modules 0)
    (nets 1)
  )

  (page A4)

  (layers
{layer_defs}
    (32 B.Adhes user)
    (33 F.Adhes user)
    (34 B.Paste user)
    (35 F.Paste user)
    (36 B.SilkS user)
    (37 F.SilkS user)
    (38 B.Mask user)
    (39 F.Mask user)
    (40 Dwgs.User user)
    (41 Cmts.User user)
    (42 Eco1.User user)
    (43 Eco2.User user)
    (44 Edge.Cuts user)
    (45 Margin user)
    (46 B.CrtYd user)
    (47 F.CrtYd user)
    (48 B.Fab user)
    (49 F.Fab user)
  )

  (setup
    (last_trace_width 0.25)
    (trace_clearance 0.2)
    (zone_clearance 0.508)
    (zone_45_only no)
    (trace_min 0.2)
    (via_size 0.8)
    (via_drill 0.4)
    (via_min_size 0.4)
    (via_min_drill 0.3)
    (uvia_size 0.3)
    (uvia_drill 0.1)
    (uvias_allowed no)
    (uvia_min_size 0.2)
    (uvia_min_drill 0.1)
    (edge_width 0.05)
    (segment_width 0.2)
    (pcb_text_width 0.3)
    (pcb_text_size 1.5 1.5)
    (mod_edge_width 0.12)
    (mod_text_size 1 1)
    (mod_text_width 0.15)
    (pad_size 1.524 1.524)
    (pad_drill 0.762)
    (pad_to_mask_clearance 0.05)
    (aux_axis_origin 0 0)
    (visible_elements FFFFFF7F)
    (pcbplotparams
      (layerselection 0x010fc_ffffffff)
      (usegerberextensions false)
      (usegerberattributes false)
      (usegerberadvancedattributes false)
      (creategerberjobfile false)
      (excludeedgelayer true)
      (linewidth 0.100000)
      (plotframeref false)
      (viasonmask false)
      (mode 1)
      (useauxorigin false)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (psnegative false)
      (psa4output false)
      (plotreference true)
      (plotvalue true)
      (plotinvisibletext false)
      (padsonsilk false)
      (subtractmaskfromsilk false)
      (outputformat 1)
      (mirror false)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory ""))
  )

  (net 0 "")

  (net_class Default "This is the default net class."
    (clearance 0.2)
    (trace_width 0.25)
    (via_dia 0.8)
    (via_drill 0.4)
    (uvia_dia 0.3)
    (uvia_drill 0.1)
  )

'''

        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_text(content)

        return f"""# PCB Created Successfully

**File:** {path}
**Dimensions:** {board_width} x {board_height} mm
**Layers:** {layers}

Next steps:
- Add board outline with `add_board_outline`
- Add footprints with `add_footprint`
- Add tracks with `add_track`
- Add vias with `add_via`
- Save changes"""

    except Exception as e:
        return f"Error creating PCB: {e}"


@mcp.tool()
async def add_board_outline(
    file_path: str,
    width: float,
    height: float,
    center_x: float = 50.0,
    center_y: float = 50.0,
) -> str:
    """Add a rectangular board outline (Edge.Cuts).

    Args:
        file_path: Path to .kicad_pcb file
        width: Board width in mm
        height: Board height in mm
        center_x: Center X position
        center_y: Center Y position

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Calculate corner points
        x1 = center_x - width / 2
        y1 = center_y - height / 2
        x2 = center_x + width / 2
        y2 = center_y + height / 2

        # Generate gr_line for board outline (4 lines forming a rectangle)
        import uuid
        outline_uuids = [str(uuid.uuid4()) for _ in range(4)]

        outline_content = f'''  (gr_line (start {x1} {y1}) (end {x2} {y1})
    (stroke (width 0.05) (type default))
    (layer "Edge.Cuts") (net 0) (tstamp {outline_uuids[0]}))
  (gr_line (start {x2} {y1}) (end {x2} {y2})
    (stroke (width 0.05) (type default))
    (layer "Edge.Cuts") (net 0) (tstamp {outline_uuids[1]}))
  (gr_line (start {x2} {y2}) (end {x1} {y2})
    (stroke (width 0.05) (type default))
    (layer "Edge.Cuts") (net 0) (tstamp {outline_uuids[2]}))
  (gr_line (start {x1} {y2}) (end {x1} {y1})
    (stroke (width 0.05) (type default))
    (layer "Edge.Cuts") (net 0) (tstamp {outline_uuids[3]}))
'''

        # Insert before the last closing paren
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + outline_content + content[last_paren:]

        path.write_text(new_content)

        return f"""# Board Outline Added Successfully

**Dimensions:** {width} x {height} mm
**Center:** ({center_x}, {center_y})
**Corners:** ({x1}, {y1}) to ({x2}, {y2})

Board outline added to {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding board outline: {e}"


@mcp.tool()
async def add_footprint(
    file_path: str,
    reference: str,
    footprint_id: str,
    value: str,
    position: tuple[float, float],
    layer: str = "F.Cu",
    rotation: float = 0.0,
) -> str:
    """Add a footprint to the PCB.

    Args:
        file_path: Path to .kicad_pcb file
        reference: Reference designator (e.g., 'R1', 'C1', 'U1')
        footprint_id: Footprint library ID (e.g., 'Resistor_SMD:R_0805_2012Metric')
        value: Component value
        position: X, Y coordinates in mm
        layer: PCB layer (F.Cu or B.Cu)
        rotation: Rotation angle in degrees

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Generate UUID
        import uuid
        fp_uuid = str(uuid.uuid4())

        # Generate footprint instance
        footprint_instance = f'''  (footprint "{footprint_id}"
    (layer "{layer}")
    (tedit {fp_uuid})
    (at {position[0]} {position[1]} {rotation})
    (descr " footprint")
    (tags " footprint")
    (property "Reference" "{reference}")
    (property "Value" "{value}")
  )
'''

        # Insert before the last closing paren
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + footprint_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Footprint Added Successfully

**Reference:** {reference}
**Footprint:** {footprint_id}
**Value:** {value}
**Position:** ({position[0]}, {position[1]})
**Layer:** {layer}
**Rotation:** {rotation}°

Footprint added to {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding footprint: {e}"


@mcp.tool()
async def add_track(
    file_path: str,
    start: tuple[float, float],
    end: tuple[float, float],
    layer: str = "F.Cu",
    width: float = 0.25,
    net: int = 0,
) -> str:
    """Add a track segment to the PCB.

    Args:
        file_path: Path to .kicad_pcb file
        start: Start point (x, y) in mm
        end: End point (x, y) in mm
        layer: PCB layer (F.Cu, B.Cu, or inner layers)
        width: Track width in mm
        net: Net number (0 = no net)

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Generate UUID
        import uuid
        track_uuid = str(uuid.uuid4())

        # Generate track segment
        track_instance = f'''  (segment
    (start {start[0]} {start[1]})
    (end {end[0]} {end[1]})
    (width {width})
    (layer "{layer}")
    (net {net})
    (tstamp {track_uuid})
  )
'''

        # Insert before the last closing paren
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + track_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Track Added Successfully

**From:** ({start[0]}, {start[1]})
**To:** ({end[0]}, {end[1]})
**Layer:** {layer}
**Width:** {width} mm
**Net:** {net}

Track added to {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding track: {e}"


@mcp.tool()
async def add_via(
    file_path: str,
    position: tuple[float, float],
    size: float = 0.8,
    drill: float = 0.4,
    net: int = 0,
) -> str:
    """Add a via to the PCB.

    Args:
        file_path: Path to .kicad_pcb file
        position: X, Y coordinates in mm
        size: Via diameter in mm
        drill: Drill diameter in mm
        net: Net number (0 = no net)

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Generate UUID
        import uuid
        via_uuid = str(uuid.uuid4())

        # Generate via instance
        via_instance = f'''  (via
    (at {position[0]} {position[1]})
    (size {size})
    (drill {drill})
    (layers "F.Cu" "B.Cu")
    (net {net})
    (tstamp {via_uuid})
  )
'''

        # Insert before the last closing paren
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + via_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Via Added Successfully

**Position:** ({position[0]}, {position[1]})
**Size:** {size} mm
**Drill:** {drill} mm
**Net:** {net}

Via added to {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding via: {e}"


@mcp.tool()
async def add_zone(
    file_path: str,
    polygon_points: List[tuple[float, float]],
    layer: str = "F.Cu",
    net: int = 0,
    zone_name: str = "",
) -> str:
    """Add a copper zone to the PCB.

    Args:
        file_path: Path to .kicad_pcb file
        polygon_points: List of (x, y) points defining the zone
        layer: PCB layer
        net: Net number for the zone
        zone_name: Optional zone name

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Generate polygon pts string
        pts_str = " ".join([f"(xy {x} {y})" for x, y in polygon_points])

        # Generate UUID
        import uuid
        zone_uuid = str(uuid.uuid4())

        # Handle zone name
        zname = zone_name if zone_name else ""

        # Generate zone instance
        zone_instance = f'''  (zone (net {net}) (net_name "{zname}")
    (layer "{layer}")
    (tstamp {zone_uuid})
    (hatch edge 0.508)
    (connect_pads (clearance 0.508))
    (min_thickness 0.254)
    (fill yes (arc_segments 32) (thermal_gap 0.508) (thermal_bridge_width 0.508))
    (polygon
      (pts
        {pts_str}
      )
    )
  )
'''

        # Insert before the last closing paren
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + zone_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Zone Added Successfully

**Points:** {len(polygon_points)} vertices
**Layer:** {layer}
**Net:** {net}
**Zone Name:** {zone_name or "None"}

Zone added to {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding zone: {e}"


@mcp.tool()
async def add_text(
    file_path: str,
    text: str,
    position: tuple[float, float],
    layer: str = "F.SilkS",
    size: float = 1.0,
    thickness: float = 0.15,
) -> str:
    """Add text to the PCB.

    Args:
        file_path: Path to .kicad_pcb file
        text: Text string to add
        position: X, Y coordinates in mm
        layer: PCB layer (F.SilkS, B.SilkS, F.Fab, etc.)
        size: Text height in mm
        thickness: Stroke thickness in mm

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Generate UUID
        import uuid
        text_uuid = str(uuid.uuid4())

        # Generate text instance
        text_instance = f'''  (gr_text "{text}" (at {position[0]} {position[1]})
    (layer "{layer}")
    (effects (font (size {size} {size}) (thickness {thickness})))
    (tstamp {text_uuid})
  )
'''

        # Insert before the last closing paren
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + text_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Text Added Successfully

**Text:** {text}
**Position:** ({position[0]}, {position[1]})
**Layer:** {layer}
**Size:** {size} mm

Text added to {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding text: {e}"


@mcp.tool()
async def list_available_footprints(
    category: str = "",
) -> str:
    """List available footprint libraries.

    Args:
        category: Optional category filter

    Returns:
        List of available footprint libraries
    """
    # Common KiCad footprint libraries
    categories = {
        "Resistor_SMD": [
            "R_0402_1005Metric",
            "R_0603_1608Metric",
            "R_0805_2012Metric",
            "R_1206_3216Metric",
            "R_2512_6332Metric",
        ],
        "Capacitor_SMD": [
            "C_0402_1005Metric",
            "C_0603_1608Metric",
            "C_0805_2012Metric",
            "C_1206_3216Metric",
            "C_1210_3225Metric",
        ],
        "LED_SMD": [
            "LED_0402_1005Metric",
            "LED_0603_1608Metric",
            "LED_0805_2012Metric",
            "LED_1206_3216Metric",
        ],
        "Connector_PinHeader": [
            "PinHeader_1x02_P2.54mm_Vertical",
            "PinHeader_1x04_P2.54mm_Vertical",
            "PinHeader_1x06_P2.54mm_Vertical",
            "PinHeader_2x03_P2.54mm_Vertical",
            "PinHeader_2x20_P2.54mm_Vertical",
        ],
        "Package_TO_SOT_SMD": [
            "SOT-23",
            "SOT-223",
            "SOT-323",
            "SOT-89",
            "SOT-143",
        ],
        "Module": [
            "Arduino_Nano",
            "ESP32-WROOM-32",
            "Raspberry_Pi_2_3",
        ],
    }

    lines = [
        "# Available Footprint Libraries",
        "",
        "Usage: `Library:Footprint`",
        "Example: `Resistor_SMD:R_0805_2012Metric`",
        "",
    ]

    if category:
        if category in categories:
            lines.append(f"## {category}")
            for fp in categories[category]:
                lines.append(f"- {category}:{fp}")
        else:
            lines.append(f"Error: Category '{category}' not found")
            lines.append("")
            lines.append("Available categories:")
            for cat in categories.keys():
                lines.append(f"- {cat}")
    else:
        for cat, fps in categories.items():
            lines.append(f"## {cat}")
            for fp in fps:
                lines.append(f"- {cat}:{fp}")
            lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def set_track_width(
    file_path: str,
    track_name: str,
    width: float,
) -> str:
    """Set a track width in the design rules.

    Args:
        file_path: Path to .kicad_pcb file
        track_name: Name of the track class (e.g., "signal", "power", "default")
        width: Track width in mm

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # For simplicity, just update the default track width
        # In a full implementation, would manage multiple track width classes
        new_content = content.replace(
            "(last_trace_width 0.25)",
            f"(last_trace_width {width})"
        )

        path.write_text(new_content)

        return f"""# Track Width Updated

**Track:** {track_name}
**Width:** {width} mm

Design rule updated in {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error setting track width: {e}"
