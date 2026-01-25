"""Advanced schematic editing tools for KiCad 9.0+ MCP Server."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from ..server import mcp


def _get_date_string() -> str:
    """Get current date in ISO format."""
    return datetime.now().strftime("%Y-%m-%d")


@mcp.tool()
async def add_wire(
    file_path: str,
    points: List[Tuple[float, float]],
) -> str:
    """Add a wire (connection line) to the schematic.

    Args:
        file_path: Path to the .kicad_sch file
        points: List of (x, y) coordinates for wire points

    Returns:
        Confirmation message with wire details
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File {file_path} does not exist"

        # Read existing schematic
        content = path.read_text()

        # Format the points
        pts_str = " ".join([f"(xy {x} {y})" for x, y in points])

        # Create wire entry
        wire_uuid = str(uuid.uuid4())
        wire_entry = f'''  (wire (pts {pts_str})
  )'''

        # Insert wire before the closing parenthesis
        if content.rstrip().endswith(')'):
            # Find the last closing paren and insert before it
            content = content.rstrip()
            if content.endswith(')'):
                content = content[:-1] + wire_entry + "\n)\n"
            else:
                content = content + "\n" + wire_entry + "\n)"
        else:
            content = content + "\n" + wire_entry + "\n)"

        # Write back
        path.write_text(content)

        return f"""✅ Wire added successfully!

**File:** {file_path}
**Points:** {points}
**UUID:** {wire_uuid}

Wire connects {len(points)} points:
{chr(10).join([f"  - ({x}, {y})" for x, y in points])}
"""

    except Exception as e:
        import traceback
        return f"Error adding wire: {e}\n\n{traceback.format_exc()}"


@mcp.tool()
async def add_label(
    file_path: str,
    text: str,
    x: float,
    y: float,
    orientation: float = 0,
    effect_justify: str = "left",
) -> str:
    """Add a local label (text label) to the schematic.

    Args:
        file_path: Path to the .kicad_sch file
        text: Label text
        x: X coordinate
        y: Y coordinate
        orientation: Rotation angle (0, 90, 180, 270)
        effect_justify: Text justification (left, right, center)

    Returns:
        Confirmation message
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File {file_path} does not exist"

        # Read existing schematic
        content = path.read_text()

        # Create label entry
        label_uuid = str(uuid.uuid4())
        label_entry = f'''  (label "{text}" (at {x} {y} {orientation})
    (effects (font (size 1.27 1.27)) (justify {effect_justify}))
    (uuid {label_uuid})
  )'''

        # Insert label before the closing parenthesis
        if content.rstrip().endswith(')'):
            content = content.rstrip()
            if content.endswith(')'):
                content = content[:-1] + label_entry + "\n)\n"
            else:
                content = content + "\n" + label_entry + "\n)"
        else:
            content = content + "\n" + label_entry + "\n)"

        # Write back
        path.write_text(content)

        return f"""✅ Label added successfully!

**File:** {file_path}
**Text:** {text}
**Position:** ({x}, {y})
**Orientation:** {orientation}°
**UUID:** {label_uuid}
"""

    except Exception as e:
        import traceback
        return f"Error adding label: {e}\n\n{traceback.format_exc()}"


@mcp.tool()
async def add_global_label(
    file_path: str,
    text: str,
    x: float,
    y: float,
    orientation: float = 0,
    shape: str = "input",
    effect_justify: str = "right",
) -> str:
    """Add a global label (for signals, I2C, SPI, etc.) to the schematic.

    Args:
        file_path: Path to the .kicad_sch file
        text: Label text (e.g., "SDA", "SCL", "GPIO2")
        x: X coordinate
        y: Y coordinate
        orientation: Rotation angle (0, 90, 180, 270)
        shape: Label shape (input, output, bidirectional, tri_state, passive)
        effect_justify: Text justification (left, right, center)

    Returns:
        Confirmation message
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File {file_path} does not exist"

        # Read existing schematic
        content = path.read_text()

        # Create global label entry
        label_uuid = str(uuid.uuid4())
        label_entry = f'''  (global_label "{text}" (shape {shape}) (at {x} {y} {orientation}) (fields_autoplaced)
    (effects (font (size 1.27 1.27)) (justify {effect_justify}))
    (uuid {label_uuid})
  )'''

        # Insert label before the closing parenthesis
        if content.rstrip().endswith(')'):
            content = content.rstrip()
            if content.endswith(')'):
                content = content[:-1] + label_entry + "\n)\n"
            else:
                content = content + "\n" + label_entry + "\n)"
        else:
            content = content + "\n" + label_entry + "\n)"

        # Write back
        path.write_text(content)

        return f"""✅ Global label added successfully!

**File:** {file_path}
**Text:** {text}
**Position:** ({x}, {y})
**Orientation:** {orientation}°
**Shape:** {shape}
**UUID:** {label_uuid}

Global labels can be used to connect signals across pages or for important signals like I2C (SDA, SCL).
"""

    except Exception as e:
        import traceback
        return f"Error adding global label: {e}\n\n{traceback.format_exc()}"


@mcp.tool()
async def add_component_from_library(
    file_path: str,
    library_name: str,
    symbol_name: str,
    reference: str,
    value: str,
    x: float,
    y: float,
    unit: int = 1,
) -> str:
    """Add a component from KiCad's built-in library to the schematic.

    Args:
        file_path: Path to the .kicad_sch file
        library_name: Library name (e.g., "Device", "MCU_ESP32", "Display")
        symbol_name: Symbol name (e.g., "R", "LED", "ESP32S3-WROOM")
        reference: Component reference (e.g., "R1", "U1", "D1")
        value: Component value (e.g., "1k", "ESP32S3", "SSD1306")
        x: X coordinate
        y: Y coordinate
        unit: Unit number for multi-unit symbols

    Returns:
        Confirmation message
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File {file_path} does not exist"

        # Read existing schematic
        content = path.read_text()

        # Generate UUID
        comp_uuid = str(uuid.uuid4())

        # Create component instance - just reference the library, don't define the symbol
        # KiCad will find the symbol in its built-in libraries
        lib_id = f"{library_name}:{symbol_name}"
        component_entry = f'''  (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit {unit}) (in_bom yes) (on_board yes) (dnp no)
    (uuid {comp_uuid})
    (property "Reference" "{reference}" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "{value}" (at {x} {y + 2.54} 0)
      (effects (font (size 1.27 1.27)))
    )
  )'''

        # Insert component before the closing parenthesis
        if content.rstrip().endswith(')'):
            content = content.rstrip()
            if content.endswith(')'):
                content = content[:-1] + component_entry + "\n)\n"
            else:
                content = content + "\n" + component_entry + "\n)"
        else:
            content = content + "\n" + component_entry + "\n)"

        # Write back
        path.write_text(content)

        return f"""✅ Component added successfully!

**File:** {file_path}
**Library:** {library_name}
**Symbol:** {symbol_name}
**Reference:** {reference}
**Value:** {value}
**Position:** ({x}, {y})
**Lib ID:** {lib_id}
**UUID:** {comp_uuid}

The component references the KiCad built-in library symbol. When you open this in KiCad, it will load the symbol definition from the {library_name} library.

**Common libraries:**
- Device: R, C, LED, Crystal
- MCU_Microchip: ATmega328P
- MCU_ESP32: ESP32S3-WROOM
- Display: SSD1306
- Switch: SW_Push
- Connector: USB_C_Plug
"""

    except Exception as e:
        import traceback
        return f"Error adding component: {e}\n\n{traceback.format_exc()}"

