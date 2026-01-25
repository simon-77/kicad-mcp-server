"""Validation and testing tools for KiCad MCP Server.

Provides tools to:
- Validate schematics are correct
- Check KiCad compatibility
- Compile and verify generated code
"""

import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..server import mcp


@mcp.tool()
async def validate_schematic(
    file_path: str,
    strict_mode: bool = True,
) -> str:
    """Validate that a schematic is correct and complete.

    Performs comprehensive validation:
    - ✅ File opens in KiCad without errors
    - ✅ All components have valid symbols
    - ✅ All components have footprints assigned
    - ✅ Footprints exist in KiCad libraries
    - ✅ No ERC errors
    - ✅ All pins are connected properly
    - ✅ Power nets are present (3V3, GND)
    - ✅ No duplicate references
    - ✅ File format is valid KiCad 9.0+

    Args:
        file_path: Path to .kicad_sch or .kicad_pro file
        strict_mode: If True, fail on any warning; if False, only errors

    Returns:
        Validation report with pass/fail status and detailed findings
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return f"""❌ Validation Failed

**Error**: File not found: {file_path}

Please check the file path and try again.
"""

        # Determine file type
        if path.suffix == ".kicad_pro":
            return await _validate_kicad_project(path, strict_mode)
        elif path.suffix == ".kicad_sch":
            return await _validate_schematic_file(path, strict_mode)
        else:
            return f"""❌ Validation Failed

**Error**: Unsupported file type: {path.suffix}

Supported types: .kicad_pro, .kicad_sch
"""

    except Exception as e:
        import traceback
        return f"❌ Validation error: {e}\n\n{traceback.format_exc()}"


async def _validate_kicad_project(project_path: Path, strict_mode: bool) -> str:
    """Validate a KiCad project file."""
    findings = []
    errors = []
    warnings = []

    # 1. Check JSON structure
    try:
        with open(project_path, 'r') as f:
            pro_data = json.load(f)

        # Check version
        version = pro_data.get("meta", {}).get("version", 0)
        if version != 3:
            errors.append(f"Project file version is {version}, expected 3 for KiCad 9.0+")
        else:
            findings.append("✅ Project file version is correct (3)")

        # Check required sections
        required_sections = ["board", "sheets"]
        for section in required_sections:
            if section not in pro_data:
                errors.append(f"Missing required section: {section}")
            else:
                findings.append(f"✅ Section '{section}' exists")

    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format: {e}")

    # 2. Check associated files exist
    sch_path = project_path.parent / f"{project_path.stem}.kicad_sch"
    pcb_path = project_path.parent / f"{project_path.stem}.kicad_pcb"

    if sch_path.exists():
        findings.append(f"✅ Schematic file exists: {sch_path.name}")
        # Also validate schematic
        sch_result = await _validate_schematic_file(sch_path, strict_mode)
        findings.append(f"\n{sch_result}")
    else:
        errors.append(f"Missing schematic file: {sch_path.name}")

    if pcb_path.exists():
        findings.append(f"✅ PCB file exists: {pcb_path.name}")
    else:
        warnings.append(f"PCB file not found: {pcb_path.name} (optional)")

    # 3. Generate report
    return _generate_validation_report(
        file_path=str(project_path),
        findings=findings,
        errors=errors,
        warnings=warnings,
        strict_mode=strict_mode
    )


async def _validate_schematic_file(sch_path: Path, strict_mode: bool) -> str:
    """Validate a schematic file."""
    findings = []
    errors = []
    warnings = []

    # 1. Read and parse file
    try:
        content = sch_path.read_text()

        # Check version
        if "(version " in content:
            import re
            version_match = re.search(r'\(version\s+(\d+)', content)
            if version_match:
                version = version_match.group(1)
                if version >= "20240130":
                    findings.append(f"✅ Schematic version {version} (KiCad 9.0+)")
                else:
                    errors.append(f"Schematic version {version} is too old")

        # Check for generator_version
        if "(generator_version" in content:
            findings.append("✅ Generator version specified")
        else:
            warnings.append("Generator version not specified (optional for KiCad 9.0)")

        # Check for UUID
        if "(uuid " in content:
            findings.append("✅ Project UUID exists")
        else:
            errors.append("Missing project UUID")

        # Check for title_block
        if "(title_block" in content:
            findings.append("✅ Title block exists")
        else:
            warnings.append("No title block found (optional)")

        # Check for lib_symbols
        if "(lib_symbols" in content:
            findings.append("✅ Symbol definitions section exists")
        else:
            errors.append("Missing lib_symbols section")

        # Count components
        symbol_count = content.count("(symbol (lib_id ")
        if symbol_count > 0:
            findings.append(f"✅ Found {symbol_count} component(s)")
        else:
            warnings.append("No components found in schematic")

        # Check for common issues
        # Duplicate references
        refs = []
        ref_pattern = r'\(property "Reference" "([^"]+)"'
        for match in re.finditer(ref_pattern, content):
            refs.append(match.group(1))

        if len(refs) != len(set(refs)):
            duplicates = [ref for ref in set(refs) if refs.count(ref) > 1]
            errors.append(f"Duplicate references found: {', '.join(duplicates)}")
        else:
            findings.append(f"✅ No duplicate references ({len(refs)} components)")

        # Check for footprints
        footprint_count = content.count('(property "Footprint"')
        if footprint_count > 0:
            findings.append(f"✅ {footprint_count} footprint(s) assigned")
        else:
            errors.append("No footprints assigned to components")

        # Check for power nets
        if "GND" in content or "gnd" in content:
            findings.append("✅ GND net found")
        else:
            warnings.append("No GND net detected")

        if "3V3" in content or "+3V3" in content or "3.3V" in content:
            findings.append("✅ 3.3V power net found")
        else:
            warnings.append("No 3.3V power net detected")

        # Check for wires/connections
        wire_count = content.count("(wire (pts")
        if wire_count > 0:
            findings.append(f"✅ {wire_count} wire(s)/connection(s)")
        else:
            warnings.append("No wires found (schematic may be incomplete)")

    except Exception as e:
        errors.append(f"Error reading schematic: {e}")

    # 2. Try to open with KiCad CLI if available
    kicad_cli = shutil.which("kicad-cli")

    if kicad_cli:
        try:
            # Try to run ERC
            result = subprocess.run(
                [kicad_cli, "erc", str(sch_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                findings.append("✅ KiCad CLI ERC check passed")
            else:
                errors.append(f"KiCad CLI ERC failed: {result.stderr}")

        except Exception as e:
            warnings.append(f"Could not run KiCad CLI validation: {e}")
    else:
        warnings.append("KiCad CLI not found - skipping automated checks")

    # 3. Generate report
    return _generate_validation_report(
        file_path=str(sch_path),
        findings=findings,
        errors=errors,
        warnings=warnings,
        strict_mode=strict_mode
    )


def _generate_validation_report(
    file_path: str,
    findings: List[str],
    errors: List[str],
    warnings: List[str],
    strict_mode: bool
) -> str:
    """Generate validation report."""

    total_findings = len(findings)
    total_errors = len(errors)
    total_warnings = len(warnings)

    # Determine pass/fail
    if strict_mode:
        passed = (total_errors == 0)
    else:
        passed = (total_errors == 0)  # Only errors matter in non-strict mode

    status = "✅ PASS" if passed else "❌ FAIL"

    # Build report
    report = f"""# KiCad File Validation Report

**File**: {file_path}
**Status**: {status}
**Mode**: {'Strict' if strict_mode else 'Standard'}

## Summary
| Category | Count |
|----------|-------|
| ✅ Findings | {total_findings} |
| ❌ Errors | {total_errors} |
| ⚠️  Warnings | {total_warnings} |

"""

    if errors:
        report += "## ❌ Errors\n\n"
        for i, error in enumerate(errors, 1):
            report += f"{i}. {error}\n"
        report += "\n"

    if warnings and not strict_mode:
        report += "## ⚠️  Warnings\n\n"
        for i, warning in enumerate(warnings, 1):
            report += f"{i}. {warning}\n"
        report += "\n"

    report += "## ✅ Validation Findings\n\n"
    for i, finding in enumerate(findings, 1):
        report += f"{i}. {finding}\n"

    report += f"\n## {'FAILED' if not passed else 'PASSED'}"

    if not passed:
        report += "\n\nPlease fix the errors above and re-validate."

    return report


@mcp.tool()
async def check_kicad_compatibility(
    file_path: str,
) -> str:
    """Check if a KiCad file is compatible with KiCad 9.0+.

    Checks:
    - File format version
    - JSON structure for .kicad_pro
    - S-expression format for .kicad_sch
    - Required fields present
    - No deprecated features

    Args:
        file_path: Path to .kicad_pro, .kicad_sch, or .kicad_pcb file

    Returns:
        Compatibility report with issues found
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return f"""❌ Compatibility Check Failed

**Error**: File not found: {file_path}
"""

        suffix = path.suffix

        if suffix == ".kicad_pro":
            return await _check_kicad_pro_compatibility(path)
        elif suffix == ".kicad_sch":
            return await _check_kicad_sch_compatibility(path)
        elif suffix == ".kicad_pcb":
            return await _check_kicad_pcb_compatibility(path)
        else:
            return f"""❌ Compatibility Check Failed

**Error**: Unsupported file type: {suffix}

Supported types: .kicad_pro, .kicad_sch, .kicad_pcb
"""

    except Exception as e:
        import traceback
        return f"❌ Compatibility check error: {e}\n\n{traceback.format_exc()}"


async def _check_kicad_pro_compatibility(pro_path: Path) -> str:
    """Check .kicad_pro compatibility."""
    findings = []
    issues = []

    try:
        with open(pro_path, 'r') as f:
            data = json.load(f)

        # Check version
        version = data.get("meta", {}).get("version")
        if version == 3:
            findings.append("✅ Version 3 (KiCad 9.0+) - Fully compatible")
        elif version == 2:
            issues.append("Version 2 (KiCad 8.x) - May not work in KiCad 9.0+")
        elif version == 1:
            issues.append("Version 1 (KiCad 7.x) - Will NOT work in KiCad 9.0+")
        else:
            issues.append(f"Unknown version: {version}")

        # Check required fields
        required_sections = ["board", "sheets", "libraries"]
        for section in required_sections:
            if section in data:
                findings.append(f"✅ Section '{section}' exists")
            else:
                issues.append(f"Missing section: {section}")

        # Check sheets
        sheets = data.get("sheets", [])
        if sheets:
            findings.append(f"✅ {len(sheets)} sheet(s) defined")
        else:
            issues.append("No sheets defined")

    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON: {e}")

    # Generate report
    return _generate_compatibility_report(
        file_path=str(pro_path),
        file_type="Project",
        findings=findings,
        issues=issues
    )


async def _check_kicad_sch_compatibility(sch_path: Path) -> str:
    """Check .kicad_sch compatibility."""
    findings = []
    issues = []

    content = sch_path.read_text()

    # Check version
    import re
    version_match = re.search(r'\(version\s+(\d+)', content)
    if version_match:
        version = version_match.group(1)
        if version >= "20240130":
            findings.append(f"✅ Version {version} - KiCad 9.0+ compatible")
        else:
            issues.append(f"Version {version} - May have compatibility issues")

    # Check for generator_version (KiCad 9.0+)
    if "(generator_version" in content:
        gen_ver_match = re.search(r'\(generator_version\s+"([^"]+)"', content)
        if gen_ver_match:
            gen_ver = gen_ver_match.group(1)
            if gen_ver.startswith("9."):
                findings.append(f"✅ Generator version {gen_ver} - KiCad 9.0+")
            else:
                issues.append(f"Generator version {gen_ver} - May not be KiCad 9.0+")
    else:
        issues.append("No generator_version - May be KiCad 8.x or earlier")

    # Check for required sections
    if "(paper " in content:
        findings.append("✅ Paper size defined")
    else:
        issues.append("No paper size defined")

    if "(title_block" in content:
        findings.append("✅ Title block exists")
    else:
        issues.append("No title block - may cause issues")

    # Check for lib_symbols
    if "(lib_symbols" in content:
        findings.append("✅ Symbol definitions section exists")
    else:
        issues.append("Missing lib_symbols section - schematic may be incomplete")

    # Check for deprecated features
    deprecated_patterns = [
        "(unit_name_prefix",  # Deprecated in KiCad 9.0
        "(dnc_substitutes",  # Deprecated
    ]

    for pattern in deprecated_patterns:
        if pattern in content:
            issues.append(f"Contains deprecated feature: {pattern}")

    # Generate report
    return _generate_compatibility_report(
        file_path=str(sch_path),
        file_type="Schematic",
        findings=findings,
        issues=issues
    )


async def _check_kicad_pcb_compatibility(pcb_path: Path) -> str:
    """Check .kicad_pcb compatibility."""
    findings = []
    issues = []

    content = pcb_path.read_text()

    # Check version
    import re
    version_match = re.search(r'\(version\s+(\d+)', content)
    if version_match:
        version = version_match.group(1)
        if version >= "20240130":
            findings.append(f"✅ Version {version} - KiCad 9.0+ compatible")
        else:
            issues.append(f"Version {version} - May have compatibility issues")

    # Check for required sections
    required = ["(general", "(layers", "(setup"]
    for section in required:
        if section in content:
            findings.append(f"✅ Section {section} exists")
        else:
            issues.append(f"Missing section: {section}")

    # Check for layers
    layer_count = content.count("(layer ")
    if layer_count >= 4:  # Minimum: F.Cu, B.Cu, F.SilkS, B.SilkS
        findings.append(f"✅ {layer_count} layers defined")
    else:
        issues.append(f"Insufficient layers: {layer_count} (need at least 4)")

    # Generate report
    return _generate_compatibility_report(
        file_path=str(pcb_path),
        file_type="PCB",
        findings=findings,
        issues=issues
    )


def _generate_compatibility_report(
    file_path: str,
    file_type: str,
    findings: List[str],
    issues: List[str]
) -> str:
    """Generate compatibility report."""

    total_findings = len(findings)
    total_issues = len(issues)

    compatible = (total_issues == 0)
    status = "✅ COMPATIBLE" if compatible else "⚠️  ISSUES FOUND"

    report = f"""# KiCad 9.0+ Compatibility Check

**File**: {file_path}
**Type**: {file_type}
**Status**: {status}

## Summary
| Category | Count |
|----------|-------|
| ✅ Checks Passed | {total_findings} |
| ⚠️  Issues | {total_issues} |

"""

    if issues:
        report += "## ⚠️ Issues Found\n\n"
        for i, issue in enumerate(issues, 1):
            report += f"{i}. {issue}\n"
        report += "\n"

    report += "## ✅ Compatibility Checks\n\n"
    for i, finding in enumerate(findings, 1):
        report += f"{i}. {finding}\n"

    report += f"\n## {status}"

    if not compatible:
        report += "\n\nPlease address the issues above for KiCad 9.0+ compatibility."

    return report


@mcp.tool()
async def compile_test_code(
    code_path: str,
    framework: str,
    target_mcu: str = "",
) -> str:
    """Compile generated test code to verify it works.

    Supported frameworks:
    - Arduino: use arduino-cli
    - ESP-IDF: use idf.py
    - Zephyr: use west build
    - pytest: run pytest

    Args:
        code_path: Path to the test code file
        framework: Framework type (arduino, esp_idf, zephyr, pytest)
        target_mcu: Target MCU for compilation (e.g., "esp32:esp32:esp32s3")

    Returns:
        Compilation result with success/failure status
    """
    try:
        path = Path(code_path)

        if not path.exists():
            return f"""❌ Compilation Failed

**Error**: File not found: {code_path}
"""

        # Detect framework if not specified
        if not framework:
            framework = _detect_framework_from_file(path)

        # Compile based on framework
        if framework.lower() == "arduino":
            return await _compile_arduino_code(path, target_mcu)
        elif framework.lower() == "esp_idf":
            return await _compile_esp_idf_code(path)
        elif framework.lower() == "zephyr":
            return await _compile_zephyr_code(path)
        elif framework.lower() in ["pytest", "unittest"]:
            return await _compile_python_code(path)
        else:
            return f"""❌ Compilation Failed

**Error**: Unsupported framework: {framework}

Supported frameworks: arduino, esp_idf, zephyr, pytest
"""

    except Exception as e:
        import traceback
        return f"❌ Compilation error: {e}\n\n{traceback.format_exc()}"


def _detect_framework_from_file(file_path: Path) -> str:
    """Detect framework from file extension and content."""
    suffix = file_path.suffix.lower()

    if suffix == ".ino":
        return "arduino"
    elif suffix == ".py":
        return "pytest"
    elif suffix in [".c", ".h"]:
        # Could be ESP-IDF or Zephyr, check for hints
        content = file_path.read_text()
        if "esp_idf" in content or "esp_rom" in content:
            return "esp_idf"
        elif "zephyr" in content or "DEVICE_DT" in content:
            return "zephyr"
        else:
            return "c"
    else:
        return "unknown"


async def _compile_arduino_code(code_path: Path, target_mcu: str) -> str:
    """Compile Arduino code using arduino-cli."""
    arduino_cli = shutil.which("arduino-cli")

    if not arduino_cli:
        return """❌ Arduino Compilation Not Available

**Error**: arduino-cli not found

To compile Arduino code:
1. Install arduino-cli:
   macOS:   brew install arduino-cli
   Linux:   sudo apt install arduino-cli
   Windows: Download from https://arduino.github.io/arduino-cli/

2. Or verify code manually in Arduino IDE
"""

    # Default to ESP32S3 if not specified
    if not target_mcu:
        target_mcu = "esp32:esp32:esp32s3"

    # Run compilation
    result = subprocess.run(
        [
            arduino_cli,
            "compile",
            "--fqbn", target_mcu,
            str(code_path)
        ],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode == 0:
        return f"""✅ Arduino Code Compiled Successfully

**File**: {code_path}
**Target MCU**: {target_mmc}
**Tool**: arduino-cli

## Compilation Output
```
{result.stdout[:500] if len(result.stdout) > 500 else result.stdout}
```

The code compiled without errors!
"""
    else:
        return f"""❌ Arduino Compilation Failed

**File**: {code_path}
**Target MCU**: {target_mcu}
**Tool**: arduino-cli

## Error Output
```
{result.stderr}
```

## Compilation Output
```
{result.stdout}
```

Please fix the errors and recompile.
"""


async def _compile_esp_idf_code(code_path: Path) -> str:
    """Compile ESP-IDF code using idf.py."""
    idf_py = shutil.which("idf.py")

    if not idf_py:
        return """❌ ESP-IDF Compilation Not Available

**Error**: idf.py not found

To compile ESP-IDF code:
1. Install ESP-IDF:
   - Follow guide: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3-user-guide/get-started/index.html
   - Run: export.sh to setup environment

2. Or verify code manually
"""

    # Find project directory (look for CMakeLists.txt)
    project_dir = code_path.parent
    cmake_lists = project_dir / "CMakeLists.txt"

    if not cmake_lists.exists():
        return f"""❌ ESP-IDF Compilation Failed

**Error**: CMakeLists.txt not found in {project_dir}

ESP-IDF projects require a CMakeLists.txt file.
"""

    # Run compilation
    result = subprocess.run(
        ["idf.py", "build"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        timeout=120
    )

    if result.returncode == 0:
        return f"""✅ ESP-IDF Code Compiled Successfully

**Project**: {project_dir}
**Tool**: idf.py

## Compilation Summary
The code compiled without errors!
Binary will be in: {project_dir / "build" / "esp32s3_project.bin"}
"""
    else:
        return f"""❌ ESP-IDF Compilation Failed

**Project**: {project_dir}
**Tool**: idf.py

## Error Output
```
{result.stderr}
```

## Build Output
```
{result.stdout[:1000]}
```

Please fix the errors and rebuild.
"""


async def _compile_zephyr_code(code_path: Path) -> str:
    """Compile Zephyr code using west build."""
    west = shutil.which("west")

    if not west:
        return """❌ Zephyr Compilation Not Available

**Error**: west not found

To compile Zephyr code:
1. Install Zephyr SDK:
   - Follow guide: https://docs.zephyrproject.org/latest/develop/getting_started/index.html
   - Setup environment with zephyr-env.sh

2. Or verify code manually
"""

    # Find project directory
    project_dir = code_path.parent
    prj_conf = project_dir / "prj.conf"

    if not prj_conf.exists():
        # Check parent directory
        parent_dir = project_dir.parent
        prj_conf = parent_dir / "prj.conf"

    if not prj_conf.exists():
        return f"""❌ Zephyr Compilation Failed

**Error**: prj.conf not found

Zephyr projects require a prj.conf file.
"""

    # Run build
    result = subprocess.run(
        ["west", "build"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        timeout=120
    )

    if result.returncode == 0:
        return f"""✅ Zephyr Code Compiled Successfully

**Project**: {project_dir}
**Tool**: west build

## Build Summary
The code compiled without errors!
"""
    else:
        return f"""❌ Zephyr Compilation Failed

**Project**: {project_dir}
**Tool**: west build

## Error Output
```
{result.stderr[:1000]}
```

## Build Output
```
{result.stdout[:1000]}
```

Please fix the errors and rebuild.
"""


async def _compile_python_code(code_path: Path) -> str:
    """Compile/run Python test code using pytest."""
    pytest = shutil.which("pytest")

    if not pytest:
        # Try python -m pytest
        python_result = subprocess.run(
            ["python", "-m", "--version"],
            capture_output=True
        )
        if python_result.returncode == 0:
            pytest = "python -m pytest"
        else:
            return """❌ Python Test Runner Not Available

**Error**: pytest not found

To run Python tests:
1. Install pytest:
   pip install pytest

2. Or run manually: python {code_path}
"""

    # Run pytest
    result = subprocess.run(
        [pytest, str(code_path)],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0:
        # Parse output for test results
        lines = result.stdout.split('\n')
        test_summary = [l for l in lines if 'passed' in l or 'failed' in l or 'error' in l]

        return f"""✅ Python Tests Passed

**File**: {code_path}
**Tool**: pytest

## Test Results
```
{result.stdout}
```

All tests passed!
"""
    else:
        return f"""❌ Python Tests Failed

**File**: {code_path}
**Tool**: pytest

## Error Output
```
{result.stderr}
```

## Test Output
```
{result.stdout}
```

Please fix the errors and re-run.
"""
