"""Test code generation tools for KiCad MCP Server."""

from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, Template

from ..server import mcp
from ..parsers.schematic_parser import SchematicParser


def _get_test_pin_info(components: list, nets: list) -> list[dict[str, Any]]:
    """Extract test pin information from components and nets.

    Args:
        components: List of schematic components
        nets: List of schematic nets

    Returns:
        List of test pin dictionaries
    """
    test_pins = []

    # Find connectors and test points
    for comp in components:
        prefix = "".join(c for c in comp.reference if c.isalpha())
        if prefix in ("J", "P", "TP", "CONN"):
            # Extract pin information
            for i, pin in enumerate(comp.pins if hasattr(comp, 'pins') else []):
                test_pins.append({
                    "name": f"{comp.reference}_{pin.get('number', i)}",
                    "number": pin.get("number", i),
                    "node_label": comp.reference.lower(),
                })

    # Add default test pins if none found
    if not test_pins:
        # Create some default test points
        test_pins = [
            {"name": "LED1", "number": 2, "node_label": "gpio2"},
            {"name": "BUTTON1", "number": 0, "node_label": "gpio0"},
        ]

    return test_pins


def _get_template_data(
    parser: SchematicParser,
    test_type: str,
    target_mcu: str | None,
) -> dict[str, Any]:
    """Gather data for template rendering.

    Args:
        parser: Schematic parser instance
        test_type: Type of tests to generate
        target_mcu: Target MCU for embedded frameworks

    Returns:
        Dictionary with template variables
    """
    components = parser.get_components()
    nets = parser.get_nets()
    title_block = parser.get_title_block()

    # Build test pin information
    test_pins = _get_test_pin_info(components, nets)

    # Create test data
    tests = []
    for pin in test_pins[:10]:  # Limit to 10 test pins
        tests.append({
            "name": pin["name"],
            "pin": pin["number"],
            "is_input": True,
            "expected": "HIGH" if "button" in pin["name"].lower() else "LOW",
        })

    # Get analog pins (for functional tests)
    analog_pins = []
    for comp in components:
        if any(kw in comp.value.lower() for kw in ["sensor", "pot", "thermistor"]):
            analog_pins.append(comp.reference)

    # Prepare template data
    data = {
        "project_name": title_block.get("title", "Project"),
        "schematic_path": str(parser.file_path),
        "components": [
            {
                "reference": c.reference,
                "value": c.value,
                "footprint": c.footprint,
            }
            for c in components
        ],
        "nets": [
            {
                "name": n.name,
                "code": n.code,
                "pins": [],  # Simplified - would need full parsing
            }
            for n in nets[:50]  # Limit to 50 nets
        ],
        "test_type": test_type,
        "target_mcu": target_mcu,
        "test_pins": test_pins,
        "tests": tests,
        "analog_pins": analog_pins,
    }

    return data


def _load_template(framework: str, test_type: str) -> Template:
    """Load Jinja2 template for specified framework.

    Args:
        framework: Framework identifier (pytest, unittest, arduino, etc.)
        test_type: Type of tests (connectivity, functional, production)

    Returns:
        Jinja2 Template object
    """
    # Get template directory
    template_dir = Path(__file__).parent.parent / "templates"
    framework_dir = template_dir / framework

    # Check if framework directory exists
    if not framework_dir.exists():
        raise ValueError(f"Unknown framework: {framework}")

    # Create Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Determine template file
    template_files = {
        "pytest": "pytest/test_connectivity.py.j2",
        "unittest": "unittest/test_schematic.py.j2",
        "arduino": "arduino/connectivity_test.cpp.j2",
        "zephyr": "zephyr/test_main.c.j2",
        "st_hal": "st_hal/hal_test.c.j2",
        "esp_idf": "esp_idf/test_suite.c.j2",
    }

    template_name = template_files.get(framework)
    if not template_name:
        raise ValueError(f"No template available for framework: {framework}")

    return env.get_template(template_name)


@mcp.tool()
async def generate_test_code(
    schematic_path: str,
    test_framework: str = "pytest",
    test_type: str = "connectivity",
    target_mcu: str | None = None,
) -> str:
    """Generate test code based on schematic connectivity.

    Args:
        schematic_path: Path to .kicad_sch file
        test_framework: Target test framework
            - pytest: Python pytest framework
            - unittest: Python unittest framework
            - arduino: Arduino/C++ framework
            - zephyr: Zephyr RTOS testing
            - st_hal: STM32 HAL library
            - esp_idf: ESP-IDF framework
        test_type: Type of tests to generate
            - connectivity: Continuity and connection tests
            - functional: Functional verification tests
            - docs: Test documentation and checklists
            - production: Manufacturing test procedures
        target_mcu: Target MCU for embedded frameworks
            (e.g., "stm32f103", "esp32", "atmega328p")

    Returns:
        Generated test code with:
        - Test fixtures for connectivity verification
        - Test point descriptions
        - Expected values for key nets
        - Component presence checks
        - Framework-specific initialization code
    """
    try:
        # Parse schematic
        parser = SchematicParser(schematic_path)

        # Validate framework
        valid_frameworks = ["pytest", "unittest", "arduino", "zephyr", "st_hal", "esp_idf"]
        if test_framework not in valid_frameworks:
            return f"Error: Unknown framework '{test_framework}'. Valid options: {', '.join(valid_frameworks)}"

        # Validate test_type
        valid_test_types = ["connectivity", "functional", "docs", "production"]
        if test_type not in valid_test_types:
            return f"Error: Unknown test_type '{test_type}'. Valid options: {', '.join(valid_test_types)}"

        # Generate docs instead of code if requested
        if test_type == "docs":
            return await _generate_test_documentation(parser, test_framework, target_mcu)

        # Load template
        template = _load_template(test_framework, test_type)

        # Prepare template data
        data = _get_template_data(parser, test_type, target_mcu)

        # Render template
        generated_code = template.render(**data)

        # Add header comment
        framework_names = {
            "pytest": "Python pytest",
            "unittest": "Python unittest",
            "arduino": "Arduino",
            "zephyr": "Zephyr RTOS",
            "st_hal": "STM32 HAL",
            "esp_idf": "ESP-IDF",
        }

        header = f"""{'#' if test_framework in ['pytest', 'unittest'] else '//'}
 * {'=' * 60}
 * {framework_names.get(test_framework, test_framework)} Test Code
 * Generated from: {schematic_path}
 * Test Type: {test_type}
"""

        return header + "\n" + generated_code

    except FileNotFoundError as e:
        return f"Error: {e}"
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error generating test code: {e}"


async def _generate_test_documentation(
    parser: SchematicParser,
    test_framework: str,
    target_mcu: str | None,
) -> str:
    """Generate test documentation instead of code.

    Args:
        parser: Schematic parser instance
        test_framework: Target framework
        target_mcu: Target MCU

    Returns:
        Markdown documentation
    """
    components = parser.get_components()
    nets = parser.get_nets()
    title_block = parser.get_title_block()

    lines = [
        f"# Test Documentation: {title_block.get('title', 'Project')}",
        "",
        f"**Schematic:** {parser.file_path.name}",
        f"**Target Framework:** {test_framework}",
        f"**Target MCU:** {target_mcu or 'N/A'}",
        "",
        "## Overview",
        "",
        "This document outlines the test procedures for verifying the",
        "schematic design and PCB assembly.",
        "",
        "## Test Requirements",
        "",
        f"- **Total Components:** {len(components)}",
        f"- **Total Nets:** {len(nets)}",
        "",
        "## Test Points",
        "",
        "### Connectors",
        "",
    ]

    # List connectors
    connectors = [c for c in components if c.reference.startswith(("J", "P", "CONN"))]
    if connectors:
        for conn in connectors:
            lines.append(f"- **{conn.reference}**: {conn.value}")
    else:
        lines.append("*No connectors found*")

    lines.extend([
        "",
        "## Test Procedures",
        "",
        "### Power-Up Test",
        "",
        "1. Verify power supply voltages",
        "2. Check for shorts on power rails",
        "3. Measure current consumption",
        "",
        "### Connectivity Test",
        "",
        "1. Verify all ground connections",
        "2. Check power supply distribution",
        "3. Test signal continuity",
        "",
        "### Functional Test",
        "",
        "1. Configure I/O pins",
        "2. Run communication interface tests",
        "3. Verify peripheral responses",
        "",
        "## Expected Results",
        "",
        "- All power rails within tolerance",
        "- No shorts or open circuits",
        "- All interfaces responsive",
        "",
])

    return "\n".join(lines)


@mcp.tool()
async def list_test_frameworks() -> str:
    """List available test frameworks for code generation.

    Returns:
        List of supported frameworks with descriptions
    """
    frameworks = {
        "pytest": {
            "description": "Python pytest framework - Feature-rich testing framework",
            "language": "Python",
            "use_case": "Connectivity verification, automated testing",
        },
        "unittest": {
            "description": "Python unittest - Standard library testing framework",
            "language": "Python",
            "use_case": "Basic connectivity tests, production verification",
        },
        "arduino": {
            "description": "Arduino/C++ framework - For Arduino boards",
            "language": "C++",
            "use_case": "Arduino-based hardware testing",
        },
        "zephyr": {
            "description": "Zephyr RTOS testing - For embedded systems",
            "language": "C",
            "use_case": "Production testing on Zephyr-powered devices",
        },
        "st_hal": {
            "description": "STM32 HAL library - For STM32 microcontrollers",
            "language": "C",
            "use_case": "STM32-based production testing",
        },
        "esp_idf": {
            "description": "ESP-IDF framework - For ESP32/ESP8266 chips",
            "language": "C",
            "use_case": "Espressif microcontroller testing",
        },
    }

    lines = [
        "# Available Test Frameworks",
        "",
        "The following frameworks are supported for test code generation:",
        "",
    ]

    for name, info in frameworks.items():
        lines.extend([
            f"## {name}",
            f"- **Language:** {info['language']}",
            f"- **Description:** {info['description']}",
            f"- **Use Case:** {info['use_case']}",
            "",
])

    lines.extend([
        "## Usage Examples",
        "",
        "```python",
        '# Generate pytest tests',
        'await generate_test_code("schematic.kicad_sch", "pytest")',
        '',
        '# Generate Arduino tests',
        'await generate_test_code("schematic.kicad_sch", "arduino", target_mcu="atmega328p")',
        '',
        '# Generate Zephyr tests',
        'await generate_test_code("schematic.kicad_sch", "zephyr", target_mcu="esp32")',
        "```",
        "",
])

    return "\n".join(lines)
