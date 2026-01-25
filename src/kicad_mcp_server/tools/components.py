"""Component management tools for KiCad MCP Server."""

from collections import defaultdict
from pathlib import Path
from typing import Any

from ..server import mcp
from ..parsers.schematic_parser import SchematicParser


@mcp.tool()
async def generate_bom(
    file_path: str,
    group_by_value: bool = True,
    include_footprints: bool = True,
) -> str:
    """Generate a Bill of Materials from a schematic.

    Args:
        file_path: Path to .kicad_sch file
        group_by_value: Group identical components together
        include_footprints: Include footprint information

    Returns:
        Formatted BOM table
    """
    try:
        parser = SchematicParser(file_path)
        components = parser.get_components()

        if group_by_value:
            # Group components by value and footprint
            groups = defaultdict(list)
            for comp in components:
                key = (comp.value, comp.footprint or "")
                groups[key].append(comp.reference)

            # Format grouped BOM
            lines = [
                f"# Bill of Materials: {file_path}",
                "",
                "| Designator | Value | Footprint | Quantity |",
                "|-------------|-------|-----------|----------|",
            ]

            for (value, footprint), refs in sorted(groups.items()):
                fp = footprint or "-"
                refs_sorted = sorted(refs)
                designators = ", ".join(refs_sorted)
                lines.append(f"| {designators} | {value} | {fp} | {len(refs)} |")

        else:
            # List all components individually
            lines = [
                f"# Bill of Materials: {file_path}",
                "",
                "| Designator | Value | Footprint |",
                "|-------------|-------|-----------|",
            ]

            for comp in sorted(components, key=lambda c: c.reference):
                fp = comp.footprint or "-"
                lines.append(f"| {comp.reference} | {comp.value} | {fp} |")

        # Add summary
        lines.extend([
            "",
            f"**Total Components:** {len(components)}",
            "",
])

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error generating BOM: {e}"


@mcp.tool()
async def list_component_types(file_path: str) -> str:
    """List all component types found in schematic.

    Args:
        file_path: Path to .kicad_sch file

    Returns:
        List of component types with counts
    """
    try:
        parser = SchematicParser(file_path)
        components = parser.get_components()

        # Group by component prefix
        type_counts = defaultdict(list)
        for comp in components:
            prefix = "".join(c for c in comp.reference if c.isalpha())
            type_counts[prefix].append(comp.reference)

        # Format output
        lines = [
            f"# Component Types: {file_path}",
            "",
            f"**Total Unique Types:** {len(type_counts)}",
            "",
            "| Type | Count | Designators |",
            "|------|-------|-------------|",
        ]

        for prefix in sorted(type_counts.keys()):
            refs = sorted(type_counts[prefix])
            count = len(refs)
            designators = ", ".join(refs[:10])
            if count > 10:
                designators += f" ... ({count - 10} more)"
            lines.append(f"| {prefix} | {count} | {designators} |")

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing component types: {e}"


@mcp.tool()
async def find_component_by_value(
    file_path: str,
    value_pattern: str,
) -> str:
    """Find components by value pattern.

    Args:
        file_path: Path to .kicad_sch file
        value_pattern: Value pattern to search for (supports regex)

    Returns:
        List of matching components
    """
    try:
        parser = SchematicParser(file_path)
        components = parser.search_components(value_pattern)

        if not components:
            return f"No components found matching value pattern: {value_pattern}"

        lines = [
            f"# Search Results: '{value_pattern}'",
            f"Found {len(components)} matching component(s)",
            "",
            "| Reference | Value | Footprint | Library |",
            "|-----------|-------|-----------|---------|",
        ]

        for comp in components:
            footprint = comp.footprint or "-"
            library = comp.library_id.split(":")[-1] if ":" in comp.library_id else comp.library_id
            lines.append(f"| {comp.reference} | {comp.value} | {footprint} | {library} |")

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error finding components: {e}"


@mcp.tool()
async def export_component_list(
    file_path: str,
    output_format: str = "csv",
) -> str:
    """Export component list for external tools.

    Args:
        file_path: Path to .kicad_sch file
        output_format: Output format ('csv', 'json', 'tsv')

    Returns:
        Exported component list
    """
    try:
        parser = SchematicParser(file_path)
        components = parser.get_components()

        if output_format == "csv":
            lines = ["Reference,Value,Footprint,Library"]
            for comp in sorted(components, key=lambda c: c.reference):
                fp = comp.footprint or ""
                lib = comp.library_id.replace(",", "_")
                lines.append(f"{comp.reference},{comp.value},{fp},{lib}")
            return "\n".join(lines)

        elif output_format == "tsv":
            lines = ["Reference\tValue\tFootprint\tLibrary"]
            for comp in sorted(components, key=lambda c: c.reference):
                fp = comp.footprint or ""
                lib = comp.library_id.replace("\t", " ")
                lines.append(f"{comp.reference}\t{comp.value}\t{fp}\t{lib}")
            return "\n".join(lines)

        elif output_format == "json":
            import json
            data = [
                {
                    "reference": c.reference,
                    "value": c.value,
                    "footprint": c.footprint,
                    "library": c.library_id,
                    "properties": c.properties,
                }
                for c in sorted(components, key=lambda c: c.reference)
            ]
            return json.dumps(data, indent=2)

        else:
            return f"Error: Unknown format '{output_format}'. Use 'csv', 'tsv', or 'json'."

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error exporting components: {e}"


@mcp.tool()
async def analyze_component_usage(
    file_path: str,
) -> str:
    """Analyze component usage patterns in schematic.

    Args:
        file_path: Path to .kicad_sch file

    Returns:
        Component usage analysis
    """
    try:
        parser = SchematicParser(file_path)
        components = parser.get_components()

        # Analyze by type
        type_counts = defaultdict(int)
        for comp in components:
            prefix = "".join(c for c in comp.reference if c.isalpha())
            type_counts[prefix] += 1

        # Identify ICs
        ics = [c for c in components if any(
            p in c.reference for p in ["U", "IC", "DD"]
        )]

        # Identify connectors
        connectors = [c for c in components if any(
            p in c.reference for p in ["J", "P", "CONN"]
        )]

        # Identify passives
        resistors = [c for c in components if c.reference.startswith("R")]
        capacitors = [c for c in components if c.reference.startswith("C")]
        inductors = [c for c in components if c.reference.startswith("L")]

        # Format analysis
        lines = [
            f"# Component Usage Analysis: {file_path}",
            "",
            "## Summary",
            f"- **Total Components:** {len(components)}",
            f"- **Unique Types:** {len(type_counts)}",
            "",
            "## Component Distribution",
            f"- **Resistors:** {len(resistors)}",
            f"- **Capacitors:** {len(capacitors)}",
            f"- **Inductors:** {len(inductors)}",
            f"- **ICs:** {len(ics)}",
            f"- **Connectors:** {len(connectors)}",
            "",
        ]

        # Common resistor values
        if resistors:
            r_values = defaultdict(int)
            for r in resistors:
                r_values[r.value] += 1

            lines.extend([
                "## Top Resistor Values",
])
            for value, count in sorted(r_values.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {value}: {count}")
            lines.append("")

        # Common capacitor values
        if capacitors:
            c_values = defaultdict(int)
            for c in capacitors:
                c_values[c.value] += 1

            lines.extend([
                "## Top Capacitor Values",
])
            for value, count in sorted(c_values.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {value}: {count}")
            lines.append("")

        # IC types
        if ics:
            lines.extend([
                "## Integrated Circuits",
])
            for ic in ics[:10]:
                lines.append(f"- {ic.reference}: {ic.value}")
            if len(ics) > 10:
                lines.append(f"- ... and {len(ics) - 10} more")
            lines.append("")

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error analyzing components: {e}"
