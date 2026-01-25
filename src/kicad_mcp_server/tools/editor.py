"""Schematic editing tools for KiCad MCP Server."""

from typing import Any
from ..server import mcp
from ..parsers.schematic_parser import SchematicParser


@mcp.tool()
async def create_schematic(
    file_path: str,
    title: str = "Untitled",
    company: str = "",
    revision: str = "1.0",
) -> str:
    """Create a new KiCad schematic file.

    Args:
        file_path: Path where to save the .kicad_sch file
        title: Project title
        company: Company name
        revision: Revision string

    Returns:
        Confirmation message with file path
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        if not path.suffix:
            path = path.with_suffix('.kicad_sch')

        # Generate KiCad schematic file content (S-expression format)
        content = f'''(kicad_sch (version 20211123) (generator eeschema)

  (paper "A4")

  (title_block
    (title "{title}")
    (company "{company}")
    (date "{_get_date_string()}")
    (rev "{revision}")
  )

  (lib_symbols
  )

'''

        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_text(content)

        return f"""# Schematic Created Successfully

**File:** {path}
**Title:** {title}
**Company:** {company}
**Revision:** {revision}

Next steps:
- Add components with `add_component`
- Connect pins with `connect_pins`
- Add net labels with `add_net_label`
- Save changes"""

    except Exception as e:
        return f"Error creating schematic: {e}"


@mcp.tool()
async def add_component(
    file_path: str,
    reference: str,
    value: str,
    library_id: str,
    position: tuple[float, float],
    unit: int = 1,
    footprint: str = "",
    properties: dict[str, str] | None = None,
) -> str:
    """Add a component to the schematic.

    Args:
        file_path: Path to .kicad_sch file
        reference: Component reference (e.g., 'R1', 'C1', 'U1')
        value: Component value (e.g., '10k', '100nF', 'ATmega328P')
        library_id: Symbol library ID (e.g., 'Device:R', 'Device:C', 'MCU_Module:ESP32_WROOM')
        position: X, Y coordinates in schematic
        unit: Unit number for multi-unit symbols (default: 1)
        footprint: Optional footprint assignment
        properties: Optional additional properties

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path
        import re

        path = Path(file_path)
        content = path.read_text()

        # Generate UUID for the component
        import uuid
        component_uuid = str(uuid.uuid4())

        # Build properties string
        props_str = ""
        if properties:
            for key, prop_value in properties.items():
                props_str += f'    (property "{key}" "{prop_value}" (at 0 0 0)\n'
                props_str += '      (effects (font (size 1.27 1.27)))\n'
                props_str += '    )\n'

        # Build footprint property if provided
        if footprint:
            props_str += f'    (property "Footprint" "{footprint}" (at 0 0 0)\n'
            props_str += '      (effects (font (size 1.27 1.27)) hide)\n'
            props_str += '    )\n'

        # Generate symbol instance
        symbol_instance = f'''  (symbol (lib_id "{library_id}") (at {position[0]} {position[1]} {unit}) (unit {unit})
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
    (uuid {component_uuid})
    (property "Reference" "{reference}" (at 0 -5.08 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "{value}" (at 0 3.81 0)
      (effects (font (size 1.27 1.27)))
    )
{props_str}  )
'''

        # Insert before the closing parenthesis
        # Find the last closing paren
        last_paren = content.rfind(')')
        if last_paren == -1:
            return "Error: Invalid schematic file format"

        new_content = content[:last_paren] + symbol_instance + content[last_paren:]

        # Write back
        path.write_text(new_content)

        return f"""# Component Added Successfully

**Reference:** {reference}
**Value:** {value}
**Library:** {library_id}
**Position:** ({position[0]}, {position[1]})

Component added to schematic at {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding component: {e}"


@mcp.tool()
async def add_wire(
    file_path: str,
    start: tuple[float, float],
    end: tuple[float, float],
) -> str:
    """Add a wire (polyline) to the schematic.

    Args:
        file_path: Path to .kicad_sch file
        start: Start point (x, y)
        end: End point (x, y)

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Generate wire instance
        import uuid
        wire_uuid = str(uuid.uuid4())

        wire_instance = f'''  (polyline (pts (xy {start[0]} {start[1]}) (xy {end[0]} {end[1]}))
    (stroke (width 0) (type default) (color 0 0 0 0))
    (fill (type none))
    (uuid {wire_uuid})
  )
'''

        # Insert before the closing parenthesis
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + wire_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Wire Added Successfully

**From:** ({start[0]}, {start[1]})
**To:** ({end[0]}, {end[1]})

Wire added to schematic at {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding wire: {e}"


@mcp.tool()
async def create_net(
    file_path: str,
    net_name: str,
    code: int | None = None,
) -> str:
    """Create a net in the schematic.

    Args:
        file_path: Path to .kicad_sch file
        net_name: Name of the net (e.g., 'GND', 'VCC', 'Net-(R1-Pad1)')
        code: Optional net code (auto-assigned if not provided)

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Auto-assign net code if not provided
        if code is None:
            import re
            # Find existing net codes
            existing_codes = re.findall(r'\(net\s+\(code\s+(\d+)\)', content)
            code = max([int(c) for c in existing_codes] + [0]) + 1

        # Generate net instance
        net_instance = f'  (net (code {code}) (name "{net_name}")\n  )\n'

        # Insert before the closing parenthesis
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + net_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Net Created Successfully

**Net Name:** {net_name}
**Net Code:** {code}

Net created in schematic at {file_path}

Use `connect_pin_to_net` to connect pins to this net."""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error creating net: {e}"


@mcp.tool()
async def add_net_label(
    file_path: str,
    net_name: str,
    position: tuple[float, float],
    label_type: str = "hierarchical",
) -> str:
    """Add a net label to the schematic.

    Args:
        file_path: Path to .kicad_sch file
        net_name: Name of the net
        position: X, Y coordinates for the label
        label_type: Type of label ('hierarchical', 'global', 'net')

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Generate UUID
        import uuid
        label_uuid = str(uuid.uuid4())

        # Generate label instance based on type
        if label_type == "hierarchical":
            label_instance = f'''  (label "{net_name}" (at {position[0]} {position[1]} 0)
    (effects (font (size 1.27 1.27)) (justify left bottom))
    (uuid {label_uuid})
  )
'''
        elif label_type == "global":
            label_instance = f'''  (global_label "{net_name}" (at {position[0]} {position[1]} 0)
    (effects (font (size 1.27 1.27)) (justify left bottom))
    (uuid {label_uuid})
  )
'''
        else:  # net label
            label_instance = f'''  (text_label "{net_name}" (at {position[0]} {position[1]} 0)
    (effects (font (size 1.27 1.27)))
    (uuid {label_uuid})
  )
'''

        # Insert before the closing parenthesis
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + label_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Net Label Added Successfully

**Net Name:** {net_name}
**Position:** ({position[0]}, {position[1]})
**Type:** {label_type}

Label added to schematic at {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding net label: {e}"


@mcp.tool()
async def add_junction(
    file_path: str,
    position: tuple[float, float],
) -> str:
    """Add a junction dot to connect crossing wires.

    Args:
        file_path: Path to .kicad_sch file
        position: X, Y coordinates for the junction

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Generate UUID
        import uuid
        junction_uuid = str(uuid.uuid4())

        # Generate junction instance
        junction_instance = f'''  (junction (at {position[0]} {position[1]} 0)
    (diameter 0) (color 0 0 0 0)
    (uuid {junction_uuid})
  )
'''

        # Insert before the closing parenthesis
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + junction_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Junction Added Successfully

**Position:** ({position[0]}, {position[1]})

Junction added to schematic at {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding junction: {e}"


@mcp.tool()
async def add_power_symbol(
    file_path: str,
    power_type: str,  # e.g., "+3V3", "+5V", "GND", "VCC"
    position: tuple[float, float],
) -> str:
    """Add a power symbol to the schematic.

    Args:
        file_path: Path to .kicad_sch file
        power_type: Type of power symbol ("+3V3", "+5V", "GND", "VCC", etc.)
        position: X, Y coordinates

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        path = Path(file_path)
        content = path.read_text()

        # Generate UUID
        import uuid
        power_uuid = str(uuid.uuid4())

        # Map power types to library IDs
        power_libs = {
            "+3V3": "power:+3V3",
            "+5V": "power:+5V",
            "+12V": "power:+12V",
            "GND": "power:GND",
            "VCC": "power:VCC",
            "VDD": "power:VDD",
            "VSS": "power:VSS",
        }

        lib_id = power_libs.get(power_type, f"power:{power_type}")

        # Generate power symbol instance
        power_instance = f'''  (symbol (lib_id "{lib_id}") (at {position[0]} {position[1]} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
    (uuid {power_uuid})
  )
'''

        # Insert before the closing parenthesis
        last_paren = content.rfind(')')
        new_content = content[:last_paren] + power_instance + content[last_paren:]

        path.write_text(new_content)

        return f"""# Power Symbol Added Successfully

**Type:** {power_type}
**Position:** ({position[0]}, {position[1]})

Power symbol added to schematic at {file_path}"""

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error adding power symbol: {e}"


@mcp.tool()
async def delete_component(
    file_path: str,
    reference: str,
) -> str:
    """Delete a component from the schematic.

    Args:
        file_path: Path to .kicad_sch file
        reference: Component reference to delete (e.g., 'R1', 'C1')

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path
        import re

        path = Path(file_path)
        content = path.read_text()

        # Find and remove the component symbol
        # Pattern to match symbol with the given reference
        pattern = rf'  \(symbol[^)]*\(property "Reference" "{reference}"[^)]*\)([^)]*\)){{2,}}'

        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, '', content, flags=re.DOTALL)
            path.write_text(new_content)

            return f"""# Component Deleted Successfully

**Reference:** {reference}

Component removed from schematic at {file_path}"""
        else:
            return f"Error: Component '{reference}' not found in schematic"

    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error deleting component: {e}"


@mcp.tool()
async def list_available_components(
    category: str = "",
) -> str:
    """List available component symbols by category.

    Args:
        category: Optional category filter (e.g., 'Device', 'MCU_Module', 'Connector')

    Returns:
        List of available component libraries and common symbols
    """
    # Common KiCad component libraries
    categories = {
        "Device": [
            "R - Resistor",
            "R_Pack - Resistor Pack",
            "C - Capacitor",
            "CP - Polarized Capacitor",
            "L - Inductor",
            "D - Diode",
            "LED - LED",
            "Q - Transistor",
            "Q_NMOS - N-MOSFET",
            "Q_PMOS - P-MOSFET",
        ],
        "MCU_Module": [
            "ESP32_WROOM - ESP32 WROOM module",
            "Arduino_Nano - Arduino Nano",
            "Raspberry_Pi_2_3 - Raspberry Pi connector",
        ],
        "Connector": [
            "Conn_01x01_Pin - 1-pin connector",
            "Conn_01x02_Pin - 2-pin connector",
            "Conn_01x04_Pin - 4-pin connector",
            "Conn_01x06_Pin - 6-pin connector",
            "USB_C_Plug - USB-C connector",
        ],
        "Mechanical": [
            "MountingHole - Mounting hole",
            "MountingHole_Pad - Mounting hole with pad",
        ],
        "Oscillator": [
            "Crystal - Crystal oscillator",
        ],
        "Power_Symbol": [
            "+3V3 - 3.3V power",
            "+5V - 5V power",
            "+12V - 12V power",
            "GND - Ground",
            "VCC - VCC power",
            "VDD - VDD power",
        ],
    }

    lines = [
        "# Available Component Libraries",
        "",
    ]

    if category:
        if category in categories:
            lines.append(f"## {category}")
            for comp in categories[category]:
                lines.append(f"- {comp}")
        else:
            lines.append(f"Error: Category '{category}' not found")
            lines.append("")
            lines.append("Available categories:")
            for cat in categories.keys():
                lines.append(f"- {cat}")
    else:
        for cat, comps in categories.items():
            lines.append(f"## {cat}")
            for comp in comps:
                lines.append(f"- {comp}")
            lines.append("")

    return "\n".join(lines)


def _get_date_string() -> str:
    """Get current date as YYYY-MM-DD."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")
