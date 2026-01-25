"""Advanced schematic editing tools for KiCad 9.0+ MCP Server."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from ..server import mcp


def _get_date_string() -> str:
    """Get current date in ISO format."""
    return datetime.now().strftime("%Y-%m-%d")


# Pin definitions for common symbols
SYMBOL_PINS = {
    "Device:R": [
        (1, "passive", ""),
        (2, "passive", "")
    ],
    "Device:LED": [
        (1, "passive", "K"),
        (2, "passive", "A")
    ],
    "Device:C": [
        (1, "passive", ""),
        (2, "passive", "")
    ],
    "Device:R_POT": [
        (1, "passive", ""),
        (2, "passive", ""),
        (3, "passive", "")
    ],
    "Switch:SW_Push": [
        (1, "passive", ""),
        (2, "passive", "")
    ],
    "MCU_ESP32_S3:ESP32-S3-WROOM-1": [
        (1, "input", "GPIO0"),
        (2, "input", "GPIO1"),
        (3, "input", "GPIO2"),
        (4, "input", "GPIO3"),
        (5, "input", "GPIO4"),
        (6, "input", "GPIO5"),
        (6, "input", "GPIO6"),
        (7, "input", "GPIO7"),
        (8, "input", "GPIO8"),
        (9, "input", "GPIO9"),
        (10, "input", "GPIO10"),
        # ... more pins
    ],
    "Display:SSD1306": [
        (1, "input", "GND"),
        (2, "input", "SCL"),
        (3, "input", "SDA"),
        (4, "input", "VCC"),
        # ... more pins
    ],
}


def get_pins_for_symbol(library_name: str, symbol_name: str) -> List[Tuple[int, str, str]]:
    """Get pin definitions for a symbol.

    Args:
        library_name: Library name (e.g., "Device", "MCU_ESP32_S3")
        symbol_name: Symbol name (e.g., "R", "LED", "ESP32-S3-WROOM-1")

    Returns:
        List of (pin_number, pin_type, pin_name) tuples
    """
    lib_id = f"{library_name}:{symbol_name}"

    # Check if we have a predefined pin mapping
    if lib_id in SYMBOL_PINS:
        return SYMBOL_PINS[lib_id]

    # Generic fallback for 2-pin devices
    # This works for resistors, capacitors, LEDs, etc.
    return [
        (1, "passive", ""),
        (2, "passive", "")
    ]


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
    footprint: str = "",
    x: float = 100,
    y: float = 100,
    unit: int = 1,
) -> str:
    """Add a component from KiCad's built-in library to the schematic with footprint.

    Args:
        file_path: Path to the .kicad_sch file
        library_name: Library name (e.g., "Device", "MCU_ESP32", "Display")
        symbol_name: Symbol name (e.g., "R", "LED", "ESP32S3-WROOM")
        reference: Component reference (e.g., "R1", "U1", "D1")
        value: Component value (e.g., "1k", "ESP32S3", "SSD1306")
        footprint: Footprint name (e.g., "Resistor_SMD:R_0805_2012Metric")
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

        # Create component instance with footprint
        lib_id = f"{library_name}:{symbol_name}"

        # Get pins for this symbol
        pins = get_pins_for_symbol(library_name, symbol_name)

        # Generate pin entries
        pin_entries = []
        for pin_num, pin_type, pin_name in pins:
            pin_uuid = str(uuid.uuid4())
            pin_entries.append(f'    (pin "{pin_num}" (uuid {pin_uuid}))')

        pins_str = "\n".join(pin_entries) if pin_entries else ""

        # Create component entry with all required fields
        component_entry = f'''  (symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit {unit})
  (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
  (uuid {comp_uuid})
  (property "Reference" "{reference}" (at {x} {y - 5} 0)
    (effects (font (size 1.27 1.27)))
  )
  (property "Value" "{value}" (at {x} {y + 2.54} 0)
    (effects (font (size 1.27 1.27)))
  )
  (property "Footprint" "{footprint}" (at {x} {y + 5.08} 0)
    (effects (font (size 1.27 1.27)) hide)
  )
{pins_str}
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

        footprint_info = f"\n**Footprint:** {footprint}" if footprint else "\n**Footprint:** Not specified"

        return f"""✅ Component added successfully!

**File:** {file_path}
**Library:** {library_name}
**Symbol:** {symbol_name}
**Reference:** {reference}
**Value:** {value}
**Position:** ({x}, {y})
**Lib ID:** {lib_id}
**UUID:** {comp_uuid}{footprint_info}

The component references the KiCad built-in library symbol with specified footprint.

**Common Component Footprints (LCSC compatible):**

**Resistors (0805 SMD):**
- Resistor_SMD:R_0805_2012Metric

**LEDs:**
- LED_SMD:LED_0805_2012Metric
- LED_SMD:LED_0603_1608Metric

**ESP32 Modules:**
- Module:ESP32-WROOM-32
- Module:ESP32-WROOM-32-N16R8

**OLED Displays:**
- Display:OLED-0.91-128x32
- Display:OLED-0.96-128x64

**Buttons:**
- Button_Switch_SMD:SW_Push_1P1T_NO_6x6mm_H9.5mm

**Connectors:**
- Connector_USB:USB_C_Plug_USB2.0-16Pin
"""

    except Exception as e:
        import traceback
        return f"Error adding component: {e}\n\n{traceback.format_exc()}"

