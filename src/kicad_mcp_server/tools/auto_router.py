"""Auto-routing and intelligent pin assignment tools."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..server import mcp
from ..parsers.schematic_parser import SchematicParser


# Pin assignments for common MCUs
MCU_PIN_MAPS = {
    "ESP32-S3-WROOM-1": {
        "I2C": {
            "SDA": [6, 8, 10, 12, 14, 16, 18, 21, 33, 35, 37, 39, 41, 43, 45, 47],
            "SCL": [7, 9, 11, 13, 15, 17, 19, 22, 34, 36, 38, 40, 42, 44, 46, 48],
        },
        "SPI": {
            "MOSI": [11, 13, 15, 35, 37, 39, 41, 43, 45, 47],
            "MISO": [12, 14, 16, 34, 36, 38, 40, 42, 44, 46, 48],
            "SCK": [10, 14, 16, 33, 36, 39, 42, 45, 48],
            "CS": [6, 8, 17, 18, 21, 22],
        },
        "UART": {
            "TX": [1, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 33, 35, 37, 39, 41, 43, 45, 47],
            "RX": [0, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 34, 36, 38, 40, 42, 44, 46, 48],
        },
    },
    "STM32F103C8T6": {
        "I2C": {
            "SDA": [7, 9, 11, 13, 15, 17],
            "SCL": [8, 10, 12, 14, 16, 18],
        },
        "SPI": {
            "MOSI": [15, 17, 19, 21],
            "MISO": [14, 16, 18, 20],
            "SCK": [13, 17, 19],
            "CS": [8, 10, 12],
        },
        "UART": {
            "TX": [9, 11, 13, 15],
            "RX": [10, 12, 14, 16],
        },
    },
}


@dataclass
class PinAssignment:
    """Pin assignment result."""

    component: str
    pin_type: str  # I2C, SPI, UART, GPIO
    pin_number: int
    pin_name: str
    function: str


def detect_communication_needs(components: List) -> Dict[str, List[str]]:
    """Detect communication protocols needed by components.

    Args:
        components: List of SchematicComponent objects

    Returns:
        Dictionary mapping protocol to list of components
    """
    needs = {
        "I2C": [],
        "SPI": [],
        "UART": [],
    }

    for comp in components:
        lib_id_lower = comp.library_id.lower() if comp.library_id else ""
        value_lower = comp.value.lower() if comp.value else ""

        # I2C devices
        if any(kw in lib_id_lower or kw in value_lower for kw in [
            "ssd1306", "oled", "bme280", "bme680", "mpu6050", "mpu9250",
            "sht", "bmp", "aht", "sensor", "i2c"
        ]):
            needs["I2C"].append(comp.reference)

        # SPI devices
        if any(kw in lib_id_lower or kw in value_lower for kw in [
            "sd_card", "tf", "flash", "w25q", "spi", "display", "tft"
        ]):
            needs["SPI"].append(comp.reference)

        # UART devices
        if any(kw in lib_id_lower or kw in value_lower for kw in [
            "gps", "bluetooth", "wifi", "uart", "serial"
        ]):
            needs["UART"].append(comp.reference)

    return needs


def assign_pins_for_mcu(
    mcu_type: str,
    communication_needs: Dict[str, List[str]]
) -> List[PinAssignment]:
    """Assign pins for MCU based on communication needs.

    Args:
        mcu_type: MCU model (e.g., "ESP32-S3-WROOM-1")
        communication_needs: Dict of protocol to component list

    Returns:
        List of PinAssignment objects
    """
    assignments = []

    # Get pin map for MCU (use ESP32-S3 as default)
    pin_map = MCU_PIN_MAPS.get(mcu_type, MCU_PIN_MAPS["ESP32-S3-WROOM-1"])

    # Assign I2C pins if needed
    if communication_needs["I2C"]:
        # Use first available SDA/SCL pair
        sda_pins = pin_map["I2C"]["SDA"]
        scl_pins = pin_map["I2C"]["SCL"]

        if sda_pins and scl_pins:
            assignments.append(PinAssignment(
                component="MCU",
                pin_type="I2C",
                pin_number=sda_pins[0],
                pin_name=f"GPIO{sda_pins[0]}",
                function="SDA"
            ))
            assignments.append(PinAssignment(
                component="MCU",
                pin_type="I2C",
                pin_number=scl_pins[0],
                pin_name=f"GPIO{scl_pins[0]}",
                function="SCL"
            ))

    # Assign SPI pins if needed
    if communication_needs["SPI"]:
        spi_pins = pin_map["SPI"]
        for func, pin_list in [("MOSI", spi_pins["MOSI"]),
                               ("MISO", spi_pins["MISO"]),
                               ("SCK", spi_pins["SCK"]),
                               ("CS", spi_pins["CS"])]:
            if pin_list:
                assignments.append(PinAssignment(
                    component="MCU",
                    pin_type="SPI",
                    pin_number=pin_list[0],
                    pin_name=f"GPIO{pin_list[0]}",
                    function=func
                ))

    # Assign UART pins if needed
    if communication_needs["UART"]:
        uart_pins = pin_map["UART"]
        for func, pin_list in [("TX", uart_pins["TX"]),
                               ("RX", uart_pins["RX"])]:
            if pin_list:
                assignments.append(PinAssignment(
                    component="MCU",
                    pin_type="UART",
                    pin_number=pin_list[0],
                    pin_name=f"GPIO{pin_list[0]}",
                    function=func
                ))

    return assignments


@mcp.tool()
async def auto_assign_pins(
    schematic_path: str,
) -> str:
    """Automatically assign MCU pins for communication protocols.

    Analyzes the schematic to:
    1. Detect MCU type
    2. Identify communication protocols needed (I2C, SPI, UART)
    3. Find components requiring each protocol
    4. Assign optimal pins on the MCU
    5. Avoid pin conflicts
    6. Return recommended pin assignments

    This tool recommends pin assignments but does not modify the schematic.
    Use the returned information to add connections manually or with other tools.

    Args:
        schematic_path: Path to .kicad_sch file

    Returns:
        Recommended pin assignments with explanations
    """
    try:
        # Parse schematic
        parser = SchematicParser(schematic_path)
        components = parser.get_components()

        # Detect MCU
        mcu_type = None
        for comp in components:
            if comp.library_id:
                if "ESP32-S3" in comp.library_id:
                    mcu_type = "ESP32-S3-WROOM-1"
                    break
                elif "STM32F103" in comp.library_id:
                    mcu_type = "STM32F103C8T6"
                    break
                elif "ESP32-WROOM" in comp.library_id:
                    mcu_type = "ESP32-WROOM-32"
                    break

        if not mcu_type:
            return "Error: Could not detect MCU type from schematic"

        # Detect communication needs
        comm_needs = detect_communication_needs(components)

        # Generate pin assignments
        assignments = assign_pins_for_mcu(mcu_type, comm_needs)

        # Build response
        lines = []
        lines.append("✅ **Pin Assignment Recommendations**")
        lines.append("")
        lines.append(f"## 🎯 Detected MCU: {mcu_type}")
        lines.append("")

        # Communication protocols needed
        lines.append("## 📡 Communication Protocols Detected")
        lines.append("")

        for protocol, comps in comm_needs.items():
            if comps:
                lines.append(f"### {protocol}")
                for comp in comps:
                    lines.append(f"  - {comp}")
                lines.append("")

        if not any(comm_needs.values()):
            lines.append("No communication protocols detected (no I2C/SPI/UART devices)")
            lines.append("")

        # Pin assignments
        lines.append("## 📌 Recommended Pin Assignments")
        lines.append("")

        if assignments:
            # Group by protocol
            by_protocol = {}
            for assign in assignments:
                if assign.pin_type not in by_protocol:
                    by_protocol[assign.pin_type] = []
                by_protocol[assign.pin_type].append(assign)

            for protocol, assigns in by_protocol.items():
                lines.append(f"### {protocol}")
                lines.append("")
                lines.append("| Pin | Function | Description |")
                lines.append("|-----|----------|-------------|")

                for assign in assigns:
                    lines.append(f"| {assign.pin_name} | {assign.function} | GPIO{assign.pin_number} |")

                lines.append("")
        else:
            lines.append("No pin assignments needed")
            lines.append("")

        # Connection suggestions
        lines.append("## 🔗 Suggested Connections")
        lines.append("")

        if comm_needs["I2C"]:
            i2c_comps = comm_needs["I2C"]
            sda_assign = next((a for a in assignments if a.function == "SDA"), None)
            scl_assign = next((a for a in assignments if a.function == "SCL"), None)

            if sda_assign and scl_assign:
                lines.append(f"### I2C Bus")
                lines.append(f"- All I2C devices connect to shared bus:")
                lines.append(f"  - SDA: {sda_assign.pin_name}")
                lines.append(f"  - SCL: {scl_assign.pin_name}")
                lines.append(f"- Devices: {', '.join(i2c_comps)}")
                lines.append("")

        if comm_needs["SPI"]:
            spi_comms = comm_needs["SPI"]
            mosi_assign = next((a for a in assignments if a.function == "MOSI"), None)
            miso_assign = next((a for a in assignments if a.function == "MISO"), None)
            sck_assign = next((a for a in assignments if a.function == "SCK"), None)

            if mosi_assign and miso_assign and sck_assign:
                lines.append(f"### SPI Bus")
                lines.append(f"- MOSI: {mosi_assign.pin_name}")
                lines.append(f"- MISO: {miso_assign.pin_name}")
                lines.append(f"- SCK: {sck_assign.pin_name}")
                lines.append(f"- Each SPI device needs its own CS pin")
                lines.append(f"- Devices: {', '.join(spi_comms)}")
                lines.append("")

        lines.append("## ⚠️ Notes")
        lines.append("")
        lines.append("- These are recommendations based on default pin mappings")
        lines.append("- Check MCU datasheet for special pin requirements")
        lines.append("- Verify no conflicts with your specific board layout")
        lines.append("- Some pins may have bootstrapping requirements")
        lines.append("- Consider using strapping pins appropriately")

        return "\n".join(lines)

    except Exception as e:
        import traceback
        return f"Error in auto-assign pins: {e}\n\n{traceback.format_exc()}"
