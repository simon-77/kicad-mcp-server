"""Schematic summarization tools for KiCad MCP Server."""

from collections import Counter
from ..server import mcp
from ..parsers.schematic_parser import SchematicParser


@mcp.tool()
async def summarize_schematic(
    file_path: str,
    detail_level: str = "standard",
    include_nets: bool = True,
    include_power: bool = True,
) -> str:
    """Generate a comprehensive text summary of a KiCad schematic.

    Args:
        file_path: Path to .kicad_sch file
        detail_level: Level of detail ('brief', 'standard', 'detailed')
        include_nets: Whether to include net information
        include_power: Whether to include power supply analysis

    Returns:
        Human-readable markdown summary
    """
    try:
        parser = SchematicParser(file_path)
        title_block = parser.get_title_block()
        components = parser.get_components()
        nets = parser.get_nets()
        sheets = parser.get_sheets()

        # Group components by type
        component_groups = {}
        ics = []
        connectors = []
        power_components = []

        for comp in components:
            prefix = "".join(c for c in comp.reference if c.isalpha())
            if prefix not in component_groups:
                component_groups[prefix] = []
            component_groups[prefix].append(comp)

            # Identify key component types
            if prefix in ("U", "IC", "DD"):
                ics.append(comp)
            elif prefix in ("J", "P", "CONN"):
                connectors.append(comp)
            elif prefix in ("U_REG", "VR", "VRM"):
                power_components.append(comp)

        lines = []

        # Title section
        lines.append(f"# Schematic Summary: {file_path}")
        lines.append("")

        if title_block.get("title"):
            lines.append(f"**Project:** {title_block['title']}")
        if title_block.get("company"):
            lines.append(f"**Company:** {title_block['company']}")
        if title_block.get("date"):
            lines.append(f"**Date:** {title_block['date']}")

        lines.extend([
            "",
            "## Overview",
            f"- **Total Components:** {len(components)}",
            f"- **Total Nets:** {len(nets)}",
            f"- **Hierarchical Sheets:** {len(sheets)}",
            "",
        ])

        # Component summary
        lines.append("## Components by Type")
        for prefix in sorted(component_groups.keys()):
            count = len(component_groups[prefix])
            # Get example values
            examples = [c.value for c in component_groups[prefix][:3]]
            examples_str = ", ".join(examples)
            if len(component_groups[prefix]) > 3:
                examples_str += ", ..."
            lines.append(f"- **{prefix}**: {count} (e.g., {examples_str})")

        lines.append("")

        # Key components section
        if ics:
            lines.append("## Integrated Circuits")
            for ic in ics:
                lines.append(f"- **{ic.reference}**: {ic.value} ({ic.library_id})")
            lines.append("")

        if connectors:
            lines.append("## Connectors")
            for conn in connectors:
                lines.append(f"- **{conn.reference}**: {conn.value}")
            lines.append("")

        # Power analysis
        if include_power:
            lines.extend([
                "## Power Supply Analysis",
                "",
])

            # Identify power nets
            power_nets = [n for n in nets if any(
                kw in n.name.lower() for kw in ["gnd", "vcc", "vdd", "vss", "+", "-", "vbat"]
            )]

            if power_nets:
                lines.append("**Power Nets:**")
                for net in sorted(power_nets, key=lambda n: n.name):
                    lines.append(f"- {net.name}")
                lines.append("")

            if power_components:
                lines.append("**Power Components:**")
                for pc in power_components:
                    lines.append(f"- **{pc.reference}**: {pc.value}")
                lines.append("")

            # Add inference about power requirements
            vcc_nets = [n for n in power_nets if "vcc" in n.name.lower() or "vdd" in n.name.lower()]
            if vcc_nets:
                lines.append("**Voltage Rails Detected:**")
                for net in set(vcc_nets):
                    # Extract voltage if present in name
                    import re
                    voltage_match = re.search(r'(\d+\.?\d*)[Vv]?', net.name)
                    if voltage_match:
                        lines.append(f"- {voltage_match.group(0)}")
                    else:
                        lines.append(f"- {net.name}")
                lines.append("")

        # Net information
        if include_nets and detail_level != "brief":
            lines.extend([
                "## Net Summary",
                "",
])

            # Show power nets separately
            power_net_list = [n for n in nets if any(
                kw in n.name.lower() for kw in ["gnd", "vcc", "vdd", "vss", "+", "-"]
            )]

            signal_nets = [n for n in nets if n not in power_net_list]

            lines.append(f"- **Power Nets:** {len(power_net_list)}")
            lines.append(f"- **Signal Nets:** {len(signal_nets)}")

            if detail_level == "detailed":
                lines.extend([
                    "",
                    "**All Nets:**",
])
                for net in sorted(nets, key=lambda n: n.name):
                    lines.append(f"- {net.name}")

            lines.append("")

        # Functional blocks (heuristic-based)
        if detail_level in ("standard", "detailed"):
            lines.extend([
                "## Functional Block Analysis",
                "",
                "Based on component groupings, the following functional blocks are identified:",
                "",
])

            # Identify common functional patterns
            functional_blocks = []

            # Power supply block
            if any(n in ["VCC", "VDD", "+3V3", "+5V", "+12V"] for n in [n.name for n in nets]):
                functional_blocks.append("**Power Supply**: Voltage regulation and distribution")

            # MCU block
            mcu_components = [c for c in components if any(
                kw in c.value.lower() for kw in ["mcu", "micro", "atmega", "stm32", "esp", "pic"]
            )]
            if mcu_components:
                mcu_refs = ", ".join(c.reference for c in mcu_components)
                functional_blocks.append(f"**Microcontroller**: {mcu_refs}")

            # Communication interfaces
            uart_nets = [n for n in nets if "tx" in n.name.lower() or "rx" in n.name.lower()]
            i2c_nets = [n for n in nets if "sda" in n.name.lower() or "scl" in n.name.lower()]
            spi_nets = [n for n in nets if "mosi" in n.name.lower() or "miso" in n.name.lower()]

            if uart_nets:
                functional_blocks.append("**UART Interface**: Serial communication")
            if i2c_nets:
                functional_blocks.append("**I2C Interface**: I2C bus")
            if spi_nets:
                functional_blocks.append("**SPI Interface**: SPI bus")

            if functional_blocks:
                for block in functional_blocks:
                    lines.append(f"- {block}")
            else:
                lines.append("- *No clear functional blocks identified*")

            lines.append("")

        # Notes and warnings
        if detail_level == "detailed":
            lines.extend([
                "## Analysis Notes",
                "",
                "- This is an automated summary based on schematic structure",
                "- Manual review recommended for critical designs",
                "- Functional block detection is heuristic-based",
                "",
])

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error generating summary: {e}"


@mcp.tool()
async def analyze_functional_blocks(file_path: str) -> str:
    """Analyze and identify functional blocks in a schematic.

    Args:
        file_path: Path to .kicad_sch file

    Returns:
        Detailed functional block analysis
    """
    try:
        parser = SchematicParser(file_path)
        components = parser.get_components()
        nets = parser.get_nets()

        net_names = [n.name.lower() for n in nets]

        lines = [
            f"# Functional Block Analysis: {file_path}",
            "",
            "## Detected Functional Blocks",
            "",
        ]

        # Analyze different functional patterns
        blocks = {}

        # Power supply detection
        power_nets = [n for n in nets if any(
            kw in n.name for kw in ["GND", "VCC", "VDD", "+3V3", "+5V", "+12V", "Vbat"]
        )]
        if power_nets:
            blocks["Power Supply"] = {
                "description": "Power distribution and regulation",
                "nets": [n.name for n in power_nets],
                "components": [c.reference for c in components if any(
                    kw in c.value.lower() for kw in ["reg", "ldo", "buck", "boost"]
                )],
            }

        # Microcontroller detection
        mcu_comps = [c for c in components if any(
            kw in c.value.lower() for kw in [
                "atmega", "attiny", "stm32", "esp32", "esp8266", "pic",
                "mcu", "microcontroller", " cortex", "arm"
            ]
        )]
        if mcu_comps:
            blocks["Microcontroller"] = {
                "description": "Main processing unit",
                "components": [f"{c.reference} ({c.value})" for c in mcu_comps],
            }

        # Communication interfaces
        uart = any("tx" in n or "rx" in n for n in net_names)
        i2c = any("sda" in n or "scl" in n for n in net_names)
        spi = any("mosi" in n or "miso" in n or "sck" in n for n in net_names)
        can = any("can" in n for n in net_names)
        usb = any("usb" in n for n in net_names)

        interfaces = []
        if uart:
            interfaces.append("UART")
        if i2c:
            interfaces.append("I2C")
        if spi:
            interfaces.append("SPI")
        if can:
            interfaces.append("CAN")
        if usb:
            interfaces.append("USB")

        if interfaces:
            blocks["Communication Interfaces"] = {
                "description": "Data communication protocols",
                "protocols": interfaces,
            }

        # Memory
        memory_comps = [c for c in components if any(
            kw in c.value.lower() for kw in ["flash", "eeprom", "sdram", "sram", "nvram"]
        )]
        if memory_comps:
            blocks["Memory"] = {
                "description": "Data storage",
                "components": [f"{c.reference} ({c.value})" for c in memory_comps],
            }

        # Display
        display_comps = [c for c in components if any(
            kw in c.value.lower() for kw in ["lcd", "oled", "tft", "display"]
        )]
        if display_comps:
            blocks["Display/Interface"] = {
                "description": "Visual output",
                "components": [f"{c.reference} ({c.value})" for c in display_comps],
            }

        # Sensors
        sensor_comps = [c for c in components if any(
            kw in c.value.lower() for kw in [
                "sensor", "temp", "humidity", "pressure", "accel",
                "gyro", "magnet", "proximity", "light"
            ]
        )]
        if sensor_comps:
            blocks["Sensors"] = {
                "description": "Environmental and motion sensing",
                "components": [f"{c.reference} ({c.value})" for c in sensor_comps],
            }

        # Output results
        if blocks:
            for block_name, block_data in blocks.items():
                lines.append(f"### {block_name}")
                lines.append(f"*{block_data['description']}*")
                lines.append("")

                if "components" in block_data and block_data["components"]:
                    lines.append("**Components:**")
                    for comp in block_data["components"]:
                        lines.append(f"- {comp}")
                    lines.append("")

                if "nets" in block_data and block_data["nets"]:
                    lines.append("**Nets:**")
                    for net in block_data["nets"][:10]:
                        lines.append(f"- {net}")
                    lines.append("")

                if "protocols" in block_data:
                    lines.append("**Protocols:**")
                    for protocol in block_data["protocols"]:
                        lines.append(f"- {protocol}")
                    lines.append("")
        else:
            lines.append("*No distinct functional blocks identified*")
            lines.append("")

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error analyzing functional blocks: {e}"
