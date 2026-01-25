"""Design Rule Checking tools for KiCad MCP Server."""

from collections import defaultdict
from typing import Any

from ..server import mcp
from ..parsers.schematic_parser import SchematicParser
from ..parsers.pcb_parser import PCBParser
from ..models.types import ERCError, DRCError


@mcp.tool()
async def run_basic_erc(file_path: str) -> str:
    """Run basic Electrical Rules Check on a schematic.

    Args:
        file_path: Path to .kicad_sch file

    Returns:
        ERC report with errors and warnings
    """
    try:
        parser = SchematicParser(file_path)
        components = parser.get_components()
        nets = parser.get_nets()

        errors = []
        warnings = []

        # Check 1: Unconnected pins (simplified check)
        # In a full implementation, this would check each pin's connection status
        power_component_refs = {c.reference for c in components if any(
            kw in c.value.lower() for kw in ["reg", "ldo", "buck", "boost"]
        )}

        # Check 2: Power flag verification
        power_nets = {n.name for n in nets if any(
            kw in n.name.lower() for kw in ["vcc", "vdd", "+5v", "+3v3", "+12v"]
        )}
        gnd_nets = {n.name for n in nets if "gnd" in n.name.lower()}

        if not power_nets:
            errors.append(ERCError(
                severity="error",
                type="NO_POWER",
                description="No power nets found (VCC, VDD, +5V, etc.)",
                components=[],
            ))

        if not gnd_nets:
            errors.append(ERCError(
                severity="error",
                type="NO_GROUND",
                description="No ground net found",
                components=[],
            ))

        # Check 3: Duplicate component references
        refs = [c.reference for c in components]
        ref_counts = defaultdict(int)
        for ref in refs:
            ref_counts[ref] += 1

        duplicates = {ref: count for ref, count in ref_counts.items() if count > 1}
        if duplicates:
            for ref, count in duplicates.items():
                errors.append(ERCError(
                    severity="error",
                    type="DUPLICATE_REFERENCE",
                    description=f"Duplicate reference {ref} found {count} times",
                    components=[ref],
                ))

        # Check 4: Missing component values
        missing_values = [c for c in components if not c.value or c.value in ["", "?"]]
        if missing_values:
            for comp in missing_values:
                warnings.append(ERCError(
                    severity="warning",
                    type="MISSING_VALUE",
                    description=f"Component {comp.reference} has no value specified",
                    components=[comp.reference],
                ))

        # Check 5: Unassigned footprints
        no_footprint = [c for c in components if not c.footprint]
        if no_footprint:
            for comp in no_footprint:
                warnings.append(ERCError(
                    severity="warning",
                    type="NO_FOOTPRINT",
                    description=f"Component {comp.reference} has no footprint assigned",
                    components=[comp.reference],
                ))

        # Check 6: Power input without power flag
        # This is a simplified check - real ERC would check pin types
        for comp in components:
            prefix = "".join(c for c in comp.reference if c.isalpha())
            if prefix in ("U", "IC", "DD"):
                # Check if IC might be unpowered
                # This is heuristic-based
                if any(pw in comp.value.lower() for pw in ["mcu", "micro", "controller"]):
                    # Assume MCUs need power
                    pass

        # Format output
        lines = [
            f"# ERC Report: {file_path}",
            "",
            f"**Components Checked:** {len(components)}",
            f"**Nets Checked:** {len(nets)}",
            "",
        ]

        if errors:
            lines.extend([
                f"## Errors ({len(errors)})",
                "",
])
            for err in errors:
                comp_str = ", ".join(err.components) if err.components else "None"
                lines.extend([
                    f"### {err.type}",
                    f"- **Severity:** {err.severity}",
                    f"- **Description:** {err.description}",
                    f"- **Components:** {comp_str}",
                    "",
])

        if warnings:
            lines.extend([
                f"## Warnings ({len(warnings)})",
                "",
])
            for warn in warnings:
                comp_str = ", ".join(warn.components) if warn.components else "None"
                lines.extend([
                    f"### {warn.type}",
                    f"- **Severity:** {warn.severity}",
                    f"- **Description:** {warn.description}",
                    f"- **Components:** {comp_str}",
                    "",
])

        if not errors and not warnings:
            lines.extend([
                "## Result",
                "",
                "**No errors or warnings found!**",
                "",
])
        else:
            lines.extend([
                "## Summary",
                "",
                f"- **Errors:** {len(errors)}",
                f"- **Warnings:** {len(warnings)}",
                "",
])

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error running ERC: {e}"


@mcp.tool()
async def run_basic_drc(file_path: str) -> str:
    """Run basic Design Rules Check on a PCB.

    Args:
        file_path: Path to .kicad_pcb file

    Returns:
        DRC report with errors and warnings
    """
    try:
        parser = PCBParser(file_path)
        footprints = parser.get_footprints()
        stats = parser.get_statistics()

        errors = []
        warnings = []

        # Check 1: Board dimensions
        if stats["board_width"] < 5 or stats["board_height"] < 5:
            warnings.append({
                "type": "SMALL_BOARD",
                "description": f"Board seems very small: {stats['board_width']:.1f} x {stats['board_height']:.1f} mm",
            })

        # Check 2: Components without footprints
        # (Already handled in footprint parsing)

        # Check 3: Track width recommendations
        if stats["total_tracks"] > 0:
            # This is simplified - real DRC would check each track
            pass

        # Check 4: Via count
        if stats["total_vias"] == 0 and stats["layers"] > 2:
            warnings.append({
                "type": "NO_VIAS",
                "description": "Multi-layer board but no vias found",
            })

        # Check 5: Unconnected pads (simplified)
        # Real DRC would check net connectivity

        # Format output
        lines = [
            f"# DRC Report: {file_path}",
            "",
            f"**Footprints Checked:** {len(footprints)}",
            f"**Track Segments:** {stats['total_tracks']}",
            f"**Vias:** {stats['total_vias']}",
            "",
        ]

        if errors:
            lines.extend([
                f"## Errors ({len(errors)})",
                "",
])
            for err in errors:
                lines.extend([
                    f"### {err['type']}",
                    f"- **Description:** {err['description']}",
                    "",
])

        if warnings:
            lines.extend([
                f"## Warnings ({len(warnings)})",
                "",
])
            for warn in warnings:
                lines.extend([
                    f"### {warn['type']}",
                    f"- **Description:** {warn['description']}",
                    "",
])

        if not errors and not warnings:
            lines.extend([
                "## Result",
                "",
                "**No errors or warnings found!**",
                "",
])
        else:
            lines.extend([
                "## Summary",
                "",
                f"- **Errors:** {len(errors)}",
                f"- **Warnings:** {len(warnings)}",
                "",
])

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error running DRC: {e}"


@mcp.tool()
async def check_schematic_pcb_consistency(
    schematic_path: str,
    pcb_path: str,
) -> str:
    """Check consistency between schematic and PCB.

    Args:
        schematic_path: Path to .kicad_sch file
        pcb_path: Path to .kicad_pcb file

    Returns:
        Consistency report
    """
    try:
        # Parse both files
        sch_parser = SchematicParser(schematic_path)
        pcb_parser = PCBParser(pcb_path)

        sch_components = sch_parser.get_components()
        pcb_footprints = pcb_parser.get_footprints()

        errors = []
        warnings = []

        # Extract references from both
        sch_refs = {c.reference for c in sch_components}
        pcb_refs = {f.reference for f in pcb_footprints}

        # Check 1: Components in schematic but not in PCB
        missing_in_pcb = sch_refs - pcb_refs
        if missing_in_pcb:
            errors.append({
                "type": "MISSING_IN_PCB",
                "description": f"Components in schematic but not in PCB: {', '.join(sorted(missing_in_pcb))}",
                "count": len(missing_in_pcb),
            })

        # Check 2: Footprints in PCB but not in schematic
        extra_in_pcb = pcb_refs - sch_refs
        if extra_in_pcb:
            errors.append({
                "type": "EXTRA_IN_PCB",
                "description": f"Footprints in PCB but not in schematic: {', '.join(sorted(extra_in_pcb))}",
                "count": len(extra_in_pcb),
            })

        # Check 3: Value consistency
        sch_values = {c.reference: c.value for c in sch_components}
        pcb_values = {f.reference: f.value for f in pcb_footprints}

        mismatched_values = []
        for ref in sch_refs & pcb_refs:
            if sch_values[ref] != pcb_values[ref]:
                mismatched_values.append(f"{ref}: Schematic={sch_values[ref]}, PCB={pcb_values[ref]}")

        if mismatched_values:
            warnings.append({
                "type": "VALUE_MISMATCH",
                "description": f"Value mismatches: {'; '.join(mismatched_values)}",
                "count": len(mismatched_values),
            })

        # Check 4: Footprint assignment
        unassigned = [c for c in sch_components if not c.footprint]
        if unassigned:
            warnings.append({
                "type": "UNASSIGNED_FOOTPRINTS",
                "description": f"Components without footprints: {', '.join(c.reference for c in unassigned)}",
                "count": len(unassigned),
            })

        # Format output
        lines = [
            f"# Schematic-PCB Consistency Report",
            "",
            f"**Schematic:** {schematic_path}",
            f"**PCB:** {pcb_path}",
            "",
            f"**Schematic Components:** {len(sch_components)}",
            f"**PCB Footprints:** {len(pcb_footprints)}",
            "",
        ]

        if errors:
            lines.extend([
                f"## Errors ({len(errors)})",
                "",
])
            for err in errors:
                lines.extend([
                    f"### {err['type']}",
                    f"- **Description:** {err['description']}",
                    f"- **Count:** {err['count']}",
                    "",
])

        if warnings:
            lines.extend([
                f"## Warnings ({len(warnings)})",
                "",
])
            for warn in warnings:
                lines.extend([
                    f"### {warn['type']}",
                    f"- **Description:** {warn['description']}",
                    f"- **Count:** {warn.get('count', 0)}",
                    "",
])

        if not errors and not warnings:
            lines.extend([
                "## Result",
                "",
                "**Schematic and PCB are consistent!**",
                "",
])
        else:
            lines.extend([
                "## Summary",
                "",
                f"- **Errors:** {len(errors)}",
                f"- **Warnings:** {len(warnings)}",
                "",
])

        return "\n".join(lines)

    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error checking consistency: {e}"


@mcp.tool()
async def list_erc_errors() -> str:
    """List common ERC error types and their descriptions.

    Returns:
        List of ERC error types with explanations
    """
    error_types = {
        "NO_POWER": "No power nets found in schematic",
        "NO_GROUND": "No ground net found in schematic",
        "DUPLICATE_REFERENCE": "Multiple components share the same reference designator",
        "MISSING_VALUE": "Component has no value specified",
        "NO_FOOTPRINT": "Component has no footprint assigned",
        "UNCONNECTED_PIN": "Pin is not connected to any net",
        "POWER_INPUT_FLAG": "Power input pin lacks power flag",
        "POWER_CONFLICT": "Conflicting power connections on same net",
        "DRIVER_CONFLICT": "Multiple outputs driving the same net",
        "FLOATING_INPUT": "Input pin is left unconnected",
    }

    lines = [
        "# Common ERC Error Types",
        "",
        "This tool describes common Electrical Rules Check errors:",
        "",
    ]

    for err_type, description in sorted(error_types.items()):
        lines.extend([
            f"## {err_type}",
            description,
            "",
])

    return "\n".join(lines)


@mcp.tool()
async def list_drc_errors() -> str:
    """List common DRC error types and their descriptions.

    Returns:
        List of DRC error types with explanations
    """
    error_types = {
        "CLEARANCE": "Insufficient clearance between copper features",
        "TRACK_WIDTH": "Track width below minimum requirement",
        "VIA_SIZE": "Via diameter or drill size below minimum",
        "PAD_SIZE": "Pad size insufficient for reliable soldering",
        "HOLE_SIZE": "Hole size too small or too large",
        "COPPER_SLIVER": "Narrow copper feature that may break",
        "MASK_ALIGNMENT": "Solder mask alignment issue",
        "EDGE_CLEARANCE": "Feature too close to board edge",
        "COURTYARD_OVERLAP": "Component courtyards overlap",
        "ZONE_OUTSIDE": "Copper zone extends outside board boundary",
        "MISSING_CONNECTION": "Net connection incomplete",
        "UNUSED_PAD": "Pad not connected to any net",
    }

    lines = [
        "# Common DRC Error Types",
        "",
        "This tool describes common Design Rules Check errors:",
        "",
    ]

    for err_type, description in sorted(error_types.items()):
        lines.extend([
            f"## {err_type}",
            description,
            "",
])

    return "\n".join(lines)
