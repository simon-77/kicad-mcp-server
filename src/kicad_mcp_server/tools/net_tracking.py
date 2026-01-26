"""Network and connection tracking tools for KiCad MCP Server."""

from ..server import mcp
from ..parsers.schematic_parser import SchematicParser


@mcp.tool()
async def trace_component_connections(
    file_path: str,
    reference: str,
) -> str:
    """Trace all network connections for a component in the schematic.

    Args:
        file_path: Path to .kicad_sch file
        reference: Component reference designator (e.g., 'R16', 'U1')

    Returns:
        Detailed connection information including wire-traced networks and labels
    """
    try:
        parser = SchematicParser(file_path)
        result = parser.trace_wire_network(reference)

        if "error" in result and result.get("error"):
            return f"❌ {result['error']}"

        # Get component details
        comp = parser.get_component_by_reference(reference)

        # Format output
        lines = [
            f"## Component Wire Network Trace: {reference}",
            "",
            f"**Value:** {comp.value if comp else 'N/A'}",
            f"**Position:** ({result['position'][0]:.2f}, {result['position'][1]:.2f})",
            f"**Trace Points:** {len(result['trace_path'])}",
            "",
        ]

        # Connected labels (wire-traced)
        if result['connected_labels']:
            lines.append("### Connected Labels (Wire-Traced)")
            lines.append("")
            lines.append("| Label | Distance | Position |")
            lines.append("|-------|----------|----------|")
            for label in sorted(result['connected_labels'], key=lambda x: x['distance']):
                conn_type = "Direct" if label['distance'] < 0.1 else "Connected"
                lines.append(f"| {label['name']} | {label['distance']:.2f}mm ({conn_type}) | ({label['position'][0]:.1f}, {label['position'][1]:.1f}) |")
        else:
            lines.append("### Connected Labels")
            lines.append("")
            lines.append("No labels found connected via wire network.")

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"❌ File not found: {e}"
    except Exception as e:
        return f"❌ Error tracing connections: {e}"


@mcp.tool()
async def trace_signal_path(
    file_path: str,
    start_reference: str,
    max_depth: int = 3,
) -> str:
    """Trace signal path starting from a component through the schematic.

    Args:
        file_path: Path to .kicad_sch file
        start_reference: Starting component reference
        max_depth: Maximum trace depth (default: 3)

    Returns:
        Signal path trace information
    """
    try:
        parser = SchematicParser(file_path)
        start_comp = parser.get_component_by_reference(start_reference)

        if not start_comp:
            return f"❌ Component '{start_reference}' not found"

        lines = [
            f"## Signal Path Trace: {start_reference}",
            "",
            f"**Component:** {start_comp.reference}",
            f"**Value:** {start_comp.value}",
            f"**Position:** ({start_comp.position[0]:.2f}, {start_comp.position[1]:.2f})",
            "",
            "### Tracing connections...",
            "",
        ]

        # Get connections for this component
        connections = parser.get_component_connections(start_reference)

        if "error" in connections:
            return f"❌ {connections['error']}"

        # Trace hierarchical labels first
        h_labels = [l for l in connections['nearby_labels'] if 'hierarchical_label' in str(l.get('name', ''))]

        if h_labels:
            lines.append("### Hierarchical Labels Found")
            lines.append("")
            for label in h_labels[:5]:
                lines.append(f"→ {label['name']} at {label['position']}")

        # Then nearby components
        if connections['nearby_components']:
            lines.append("")
            lines.append("### Connected Components")
            lines.append("")
            for comp in connections['nearby_components'][:5]:
                lines.append(f"→ {comp['reference']}: {comp['value']}")

        lines.extend([
            "",
            "### Note",
            "This shows spatial proximity. For complete net tracing,",
            "the parser would need to process wire segments and junctions.",
            "",
            "💡 Tip: Use hierarchical_labels in KiCad to document signal names.",
        ])

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"❌ File not found: {e}"
    except Exception as e:
        return f"❌ Error tracing signal: {e}"


@mcp.tool()
async def analyze_nets_by_area(
    file_path: str,
    center_x: float,
    center_y: float,
    radius: float = 20,
) -> str:
    """Analyze all nets and components within a specific area.

    Args:
        file_path: Path to .kicad_sch file
        center_x: Center X coordinate (mm)
        center_y: Center Y coordinate (mm)
        radius: Search radius in mm (default: 20)

    Returns:
        Analysis of nets and components in the specified area
    """
    try:
        parser = SchematicParser(file_path)
        components = parser.get_components()

        # Find components within the area
        area_components = []
        for comp in components:
            cx, cy = comp.position
            dist = ((cx - center_x)**2 + (cy - center_y)**2)**0.5
            if dist <= radius:
                area_components.append({
                    "reference": comp.reference,
                    "value": comp.value,
                    "position": comp.position,
                    "distance": dist,
                })

        lines = [
            f"## Area Analysis",
            f"Center: ({center_x:.2f}, {center_y:.2f}), Radius: {radius}mm",
            f"Components found: {len(area_components)}",
            "",
        ]

        if area_components:
            lines.append("### Components in Area")
            lines.append("")
            lines.append("| Reference | Value | Distance | Position |")
            lines.append("|-----------|-------|----------|----------|")
            for comp in sorted(area_components, key=lambda x: x['distance']):
                lines.append(f"| {comp['reference']} | {comp['value']} | {comp['distance']:.2f}mm | ({comp['position'][0]:.1f}, {comp['position'][1]:.1f}) |")
            lines.append("")

        # Find labels in the area
        content = parser.file_path.read_text()
        import re

        area_labels = []
        for label_match in re.finditer(
            r'\((?:global_)?label\s+"([^"]+)"[\s\S]*?\(at\s+([\d.]+)\s+([\d.]+)',
            content
        ):
            lx, ly = float(label_match.group(2)), float(label_match.group(3))
            dist = ((lx - center_x)**2 + (ly - center_y)**2)**0.5
            if dist <= radius:
                area_labels.append({
                    "name": label_match.group(1),
                    "position": (lx, ly),
                    "distance": dist,
                })

        if area_labels:
            lines.append("### Labels in Area")
            lines.append("")
            lines.append("| Label | Distance | Position |")
            lines.append("|-------|----------|----------|")
            for label in sorted(area_labels, key=lambda x: x['distance'])[:10]:
                lines.append(f"| {label['name']} | {label['distance']:.2f}mm | ({label['position'][0]:.1f}, {label['position'][1]:.1f}) |")

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"❌ File not found: {e}"
    except Exception as e:
        return f"❌ Error analyzing area: {e}"
