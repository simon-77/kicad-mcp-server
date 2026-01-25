# KiCad MCP Server Implementation Plan

## Project Overview
Create a Model Context Protocol (MCP) server for KiCad using Python, providing capabilities for:
- **Natural language-driven design** - Create schematics and PCBs through natural language
- **Schematic analysis** (.kicad_sch files)
- **PCB analysis** (.kicad_pcb files)
- **Design rule checking** (ERC/DRC)
- **Component management** - LCSC integration
- **Schematic summarization** - Generate human-readable summaries
- **Test code generation** - Generate and compile test code
- **Complete testing** - Verify schematics and code work correctly

## Technology Stack
- **Language**: Python 3.10+
- **MCP SDK**: FastMCP
- **KiCad Integration**:
  - Template-based project creation (KiCad 9.0+)
  - KiCad Python API (pcbnew) when available
- **File Parsing**: kicad-skip + regex
- **Data Validation**: Pydantic
- **Templates**: Jinja2
- **Testing**: pytest, arduino-cli, esp-idf compiler

## Core Design Principles

### 1. Use KiCad Python API
- Prefer pcbnew API over manual file generation
- Ensures 100% file format compatibility
- Fallback: Template-based project creation

### 2. KiCad 9.0 Compatibility
- `.kicad_pro` (JSON, version=3)
- `.kicad_sch` (version 20240130)
- `.kicad_pcb` (version 20240130)

### 3. Natural Language Interaction
- Support Chinese and English
- Design intent: "Use ESP32S3, add OLED and IMU, layout on 30x30mm PCB"

### 4. LCSC Integration
- Component database with LCSC SKUs
- Footprint matching
- BOM generation with pricing

### 5. End-to-End Testing
- Verify schematics are correct
- Compile generated code
- Test on real hardware

## Implementation Status

### Phase 1: Foundation ✅ COMPLETE
- [x] Project structure setup
- [x] FastMCP server initialization
- [x] Basic schematic parser
- [x] Basic PCB parser
- [x] Configuration management

### Phase 2: Analysis Tools ✅ COMPLETE
- [x] Schematic analysis tools (`tools/schematic.py`)
- [x] PCB analysis tools (`tools/pcb.py`)
- [x] Component management (`tools/components.py`)
- [x] BOM generation
- [x] Project summarization (`tools/summary.py`)

### Phase 3: Design Tools ✅ COMPLETE
- [x] Project creation from templates (`tools/project.py`)
- [x] Schematic editing (`tools/schematic_editor.py`)
- [x] Wire and label tools
- [x] Footprint library management (`tools/footprint_library.py`)
- [x] ERC/DRC basic checks (`tools/drc.py`)

### Phase 4: Test Code Generation ✅ COMPLETE
- [x] Multi-framework support (`tools/testgen.py`)
  - pytest, unittest
  - Arduino, ESP-IDF
  - Zephyr, STM32 HAL
- [x] Jinja2 templates
- [x] Context data extraction

### Phase 5: 🎯 COMPLETE TESTING & VALIDATION (CURRENT)
- [ ] End-to-end testing pipeline
- [ ] Schematic validation
- [ ] Code compilation verification
- [ ] Hardware testing

## Testing & Quality Assurance

### Self-Validation Strategy 🔄 CRITICAL

**Core Concept**: Use our own tools to validate each other in a closed loop through **bidirectional validation (双向验证)**.

```
Create → Analyze → Validate → Compare → Report
   ↓         ↓          ↓          ↓         ↓
[Project Creation Tools]
         ↓
[Analysis Tools]
         ↓
[Validation Tools]
         ↓
[Comparison: Created vs Analyzed]
         ↓
[Pass/Fail Report]
```

#### Why Round-Trip Validation? (为什么需要双向验证)

**Problem**: External testing requires KiCad installation, toolchains, and hardware - not always available.

**Solution**: Use our own tools to validate each other in a closed loop:

1. **Create** a KiCad project using our creation tools
2. **Analyze** that same project using our analysis tools
3. **Verify** the analysis correctly identifies what was created
4. **Validate** the schematic passes all checks
5. **Compare** design spec vs actual result

This validates:
- ✅ Creation tools generate valid KiCad files
- ✅ Analysis tools correctly parse KiCad files
- ✅ Round-trip consistency (what we create = what we analyze)
- ✅ Validation tools catch real issues

**No external dependencies needed** - pure Python validation!

#### Self-Validation Workflow

```python
@mcp.tool()
async def self_validate_design_creation(
    design_spec: str,
    test_path: str
) -> str:
    """Complete self-validation of design creation workflow.

    Process:
    1. CREATE: Use create_kicad_project to make a project
    2. MODIFY: Use schematic_editor to add components
    3. ANALYZE: Use summarize_schematic to analyze what we created
    4. VALIDATE: Use validate_schematic to check correctness
    5. COMPARE: Verify analysis matches design spec
    6. REPORT: Generate comprehensive report

    Example:
        design_spec = "ESP32S3 + OLED (I2C) + IMU (I2C)"

    Creates:
    - Project with ESP32S3
    - SSD1306 OLED connected via I2C
    - MPU6050 IMU connected via I2C

    Analyzes:
    - Lists all components
    - Checks I2C connections
    - Verifies power nets

    Validates:
    - File format is KiCad 9.0+
    - All components have footprints
    - No ERC errors

    Compares:
    - Design spec vs analysis
    - Expected vs actual components
    - Expected vs actual connections

    Returns:
        Complete validation report with:
        - ✅ What was created
        - ✅ What was analyzed
        - ✅ Validation results
        - ✅ Comparison results
        - ✅ Pass/Fail status
    """
```

#### Example Self-Validation Test

```python
# Test: Create ESP32S3 + OLED design
design_spec = """
Main controller: ESP32-S3-WROOM-1
Peripherals:
  - SSD1306 OLED (I2C, GPIO6=SDA, GPIO7=SCL)
  - MPU6050 IMU (I2C, GPIO6=SDA, GPIO7=SCL)
Power: 3.3V, GND
"""

# Step 1: Create project
project_result = await create_kicad_project(
    project_path="/tmp/self_test_esp32s3",
    project_name="esp32s3_self_test"
)

# Step 2: Add components
await add_component_from_library(
    file_path="/tmp/self_test_esp32s3/esp32s3_self_test.kicad_sch",
    component_name="ESP32-S3-WROOM-1",
    reference="U1",
    position=(100, 100)
)

await add_component_from_library(
    file_path="/tmp/self_test_esp32s3/esp32s3_self_test.kicad_sch",
    component_name="SSD1306",
    reference="U2",
    position=(150, 100)
)

# Step 3: Analyze
analysis = await summarize_schematic(
    file_path="/tmp/self_test_esp32s3/esp32s3_self_test.kicad_sch"
)

# Step 4: Validate
validation = await validate_schematic(
    file_path="/tmp/self_test_esp32s3/esp32s3_self_test.kicad_sch",
    strict_mode=True
)

# Step 5: Compare
# - Check if ESP32S3 is in analysis
# - Check if OLED is in analysis
# - Check if I2C connections exist
# - Check if validation passed

# Step 6: Generate report
report = f"""
# Self-Validation Report

## Design Spec
{design_spec}

## Created
{project_result}

## Analysis
{analysis}

## Validation
{validation}

## Comparison
✅ ESP32S3 found: {'ESP32' in analysis}
✅ OLED found: {'SSD1306' in analysis or 'OLED' in analysis}
✅ I2C connections: {'I2C' in analysis or 'GPIO6' in analysis}
✅ Validation passed: {'✅' in validation or 'no errors' in validation.lower()}

## Final Result
{'PASS ✅' if all([
    'ESP32' in analysis,
    'OLED' in analysis or 'SSD1306' in analysis,
    '✅' in validation or 'no errors' in validation.lower()
]) else 'FAIL ❌'}
"""
```

#### Benefits of Self-Validation

1. **No External Dependencies**: Don't need pre-existing test files
2. **Closed Loop**: Create → Analyze → Validate → Compare
3. **Continuous Testing**: Can run on every change
4. **Proof of Capability**: Demonstrates tools work correctly
5. **Bug Detection**: Catches inconsistencies between tools

#### Self-Validation Tests to Implement

```python
# tests/test_self_validation.py

async def test_self_validation_esp32s3_oled():
    """Test complete workflow: create → analyze → validate."""
    # 1. Create
    # 2. Analyze
    # 3. Validate
    # 4. Compare
    # 5. Assert all pass

async def test_self_validation_nrf52840_sensor():
    """Test with different MCU: nRF52840."""

async def test_self_validation_power_circuit():
    """Test power supply circuit creation."""

async def test_self_validation_i2c_bus():
    """Test I2C bus with multiple devices."""
```

### Critical Testing Requirements

#### 1. Schematic Validation ✅ MUST IMPLEMENT
```python
@mcp.tool()
async def validate_schematic(
    file_path: str,
    strict_mode: bool = True
) -> str:
    """Validate that a schematic is correct and complete.

    Checks:
    - ✅ File opens in KiCad without errors
    - ✅ All components have valid symbols
    - ✅ All components have footprints assigned
    - ✅ Footprints exist in KiCad libraries
    - ✅ No ERC errors
    - ✅ All pins are connected properly
    - ✅ Power nets are present (3V3, GND)
    - ✅ No duplicate references
    - ✅ File format is valid KiCad 9.0+

    Returns:
        Validation report with pass/fail status
    """
```

**Implementation Steps**:
1. Try opening file in KiCad (via subprocess)
2. Parse file and check for common errors
3. Run KiCad CLI ERC check
4. Verify all footprints exist in libraries
5. Generate detailed report

#### 2. Test Code Compilation ✅ MUST IMPLEMENT
```python
@mcp.tool()
async def compile_test_code(
    code_path: str,
    framework: str,
    target_mcu: str
) -> str:
    """Compile generated test code to verify it works.

    Supported frameworks:
    - Arduino: use arduino-cli
    - ESP-IDF: use idf.py
    - Zephyr: use west build
    - pytest: run pytest

    Returns:
        Compilation result with success/failure
    """
```

**Implementation Steps**:
1. Detect framework from code or parameter
2. Run appropriate compiler:
   - Arduino: `arduino-cli compile`
   - ESP-IDF: `idf.py build`
   - Zephyr: `west build`
   - pytest: `pytest test_file.py`
3. Capture output and errors
4. Report success/failure with details

#### 3. End-to-End Design Test ✅ MUST IMPLEMENT
```python
@mcp.tool()
async def test_design_creation(
    design_spec: str,
    test_path: str
) -> str:
    """Test complete design creation from natural language.

    Example:
        design_spec = "Use ESP32S3, add OLED and IMU,
                      layout on 30x30mm PCB"

    Process:
    1. Parse design spec
    2. Create KiCad project
    3. Add components
    4. Connect components
    5. Generate test code
    6. Validate schematic
    7. Compile test code
    8. Generate final report

    Returns:
        Complete test report with all steps and results
    """
```

#### 4. Schematic Format Validation ✅ MUST IMPLEMENT
```python
@mcp.tool()
async def check_kicad_compatibility(
    file_path: str
) -> str:
    """Check if file is compatible with KiCad 9.0+.

    Checks:
    - File format version
    - JSON structure for .kicad_pro
    - S-expression format for .kicad_sch
    - Required fields present
    - No deprecated features

    Returns:
        Compatibility report with issues found
    """
```

### Test Automation

#### Continuous Testing Pipeline
```yaml
# .github/workflows/test.yml
name: Test KiCad Designs

on: [push, pull_request]

jobs:
  test-schematics:
    runs-on: [self-hosted, kicad]
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Test schematic creation
        run: pytest tests/test_schematic_creation.py
      - name: Test schematic validation
        run: pytest tests/test_validation.py
      - name: Test code generation
        run: pytest tests/test_codegen.py
      - name: Test compilation
        run: pytest tests/test_compilation.py

  test-with-kicad:
    runs-on: [self-hosted, kicad]
    steps:
      - name: Create test project
        run: python tests/create_test_project.py
      - name: Open in KiCad
        run: kicad-cli test_project.kicad_pro --check
      - name: Run ERC
        run: kicad-cli erc test_project.kicad_sch
      - name: Run DRC
        run: kicad-cli drc test_project.kicad_pcb
```

### Test Fixtures

#### Example Test Schematics
```
tests/fixtures/
├── esp32s3_simple/          # Minimal ESP32S3 + LED
│   ├── esp32s3_simple.kicad_pro
│   ├── esp32s3_simple.kicad_sch
│   └── expected_results.json
├── esp32s3_oled/             # ESP32S3 + I2C OLED
│   ├── esp32s3_oled.kicad_pro
│   ├── esp32s3_oled.kicad_sch
│   └── expected_results.json
├── nrf52840_sensor/          # nRF52840 + sensors
│   ├── nrf52840_sensor.kicad_pro
│   ├── nrf52840_sensor.kicad_sch
│   └── expected_results.json
└── test_code_output/         # Generated test code
    ├── arduino/
    │   └── esp32s3_oled.ino
    ├── esp_idf/
    │   └── main.c
    └── pytest/
        └── test_schematic.py
```

#### Expected Results Format
```json
{
  "project": "esp32s3_oled",
  "components": [
    {"ref": "U1", "value": "ESP32-S3", "footprint": "Module:ESP32-WROOM-32"},
    {"ref": "U2", "value": "SSD1306", "footprint": "Display:OLED-0.91-128x32"}
  ],
  "connections": [
    {"from": "U1-GPIO6", "to": "U2-SDA", "type": "I2C"},
    {"from": "U1-GPIO7", "to": "U2-SCL", "type": "I2C"}
  ],
  "test_code": {
    "arduino": {
      "compiles": true,
      "output": "tests/fixtures/test_code_output/arduino/esp32s3_oled.ino"
    },
    "esp_idf": {
      "compiles": true,
      "output": "tests/fixtures/test_code_output/esp_idf/main.c"
    }
  }
}
```

### Test Implementation

#### Unit Tests
```python
# tests/test_validation.py
import pytest
from pathlib import Path

def test_validate_esp32s3_schematic():
    """Test that ESP32S3 schematic validates correctly."""
    from kicad_mcp_server.tools.validation import validate_schematic

    result = validate_schematic(
        "tests/fixtures/esp32s3_oled/esp32s3_oled.kicad_sch"
    )

    assert "✅" in result  # Validation passed
    assert "no errors" in result.lower()

def test_validate_incomplete_schematic():
    """Test that incomplete schematic fails validation."""
    result = validate_schematic(
        "tests/fixtures/incomplete.kicad_sch"
    )

    assert "❌" in result  # Validation failed
    assert "missing footprint" in result.lower()

def test_check_kicad_compatibility():
    """Test KiCad 9.0 compatibility check."""
    from kicad_mcp_server.tools.validation import check_kicad_compatibility

    result = check_kicad_compatibility(
        "tests/fixtures/esp32s3_oled/esp32s3_oled.kicad_pro"
    )

    assert "compatible" in result.lower()
    assert "KiCad 9.0" in result
```

#### Code Compilation Tests
```python
# tests/test_compilation.py
import pytest
import subprocess
from pathlib import Path

def test_arduino_code_compiles():
    """Test that generated Arduino code compiles."""
    code_path = "tests/fixtures/test_code_output/arduino/esp32s3_oled.ino"

    result = subprocess.run(
        ["arduino-cli", "compile", "--fqbn", "esp32:esp32:esp32s3", code_path],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Compilation failed: {result.stderr}"

def test_esp_idf_code_compiles():
    """Test that generated ESP-IDF code compiles."""
    code_path = "tests/fixtures/test_code_output/esp_idf/main"

    result = subprocess.run(
        ["idf.py", "build"],
        cwd=code_path,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Compilation failed: {result.stderr}"
```

#### End-to-End Tests
```python
# tests/test_e2e.py
import pytest
from pathlib import Path

@pytest.mark.e2e
def test_create_esp32s3_oled_design():
    """Test complete design creation from spec."""
    from kicad_mcp_server.tools.design import test_design_creation

    result = test_design_creation(
        design_spec="Use ESP32S3, add OLED display, layout on 30x30mm PCB",
        test_path="/tmp/e2e_test_esp32s3"
    )

    # Check all steps passed
    assert "✅ Project created" in result
    assert "✅ Schematic valid" in result
    assert "✅ Test code compiled" in result
    assert "✅ All tests passed" in result

@pytest.mark.e2e
def test_generated_code_works():
    """Test that generated code actually works."""
    # Upload to real hardware
    # Run tests
    # Verify output
    pass
```

### Integration with KiCad CLI

```python
# Use KiCad CLI for automated testing
import subprocess

def test_kicad_cli_open():
    """Test that KiCad can open the project."""
    result = subprocess.run([
        "kicad-cli", "pcb", "export",
        "test_project.kicad_pro"
    ], capture_output=True)

    assert result.returncode == 0

def test_kicad_cli_erc():
    """Test ERC via KiCad CLI."""
    result = subprocess.run([
        "kicad-cli", "erc", "test_project.kicad_sch"
    ], capture_output=True, text=True)

    assert "0 errors" in result
```

## New Testing Tools to Implement

### 1. Validation Tool (`tools/validation.py`)
```python
@mcp.tool()
async def validate_schematic(file_path: str) -> str:
    """Complete schematic validation."""

@mcp.tool()
async def check_kicad_compatibility(file_path: str) -> str:
    """Check KiCad 9.0+ compatibility."""

@mcp.tool()
async def compile_test_code(code_path: str, framework: str) -> str:
    """Compile test code and verify it works."""
```

### 2. E2E Testing Tool (`tools/e2e_test.py`)
```python
@mcp.tool()
async def test_design_creation(design_spec: str, test_path: str) -> str:
    """End-to-end test of design creation."""

@mcp.tool()
async def verify_generated_code(
    schematic_path: str,
    framework: str
) -> str:
    """Generate and verify test code."""
```

## Implementation Priority

### High Priority (Must Have)
1. ✅ Schematic validation tool
2. ✅ KiCad compatibility checker
3. ✅ Code compilation tester
4. ✅ E2E design test

### Medium Priority (Should Have)
1. Automated test fixtures
2. KiCad CLI integration tests
3. Hardware-in-the-loop tests

### Low Priority (Nice to Have)
1. Continuous integration pipeline
2. Automated regression tests
3. Performance benchmarks

## Success Criteria

A design is considered "working" when:
- ✅ Schematic opens in KiCad 9.0+ without warnings
- ✅ ERC passes with 0 errors
- ✅ All components have valid footprints
- ✅ Generated code compiles without errors
- ✅ Generated code runs on hardware (optional)

## Project Structure (Updated)

```
kicad-mcp-server/
├── src/kicad_mcp_server/
│   ├── tools/
│   │   ├── validation.py      # 🆕 Schematic & code validation
│   │   ├── e2e_test.py        # 🆕 End-to-end testing
│   │   ├── project.py         # Project creation (template-based)
│   │   ├── schematic_editor.py
│   │   ├── footprint_library.py
│   │   ├── summary.py
│   │   ├── testgen.py
│   │   ├── schematic.py
│   │   └── pcb.py
│   └── tests/
│       ├── fixtures/
│       │   ├── esp32s3_simple/
│       │   ├── esp32s3_oled/
│       │   └── nrf52840_sensor/
│       ├── test_validation.py      # 🆕 Validation tests
│       ├── test_compilation.py    # 🆕 Compilation tests
│       └── test_e2e.py            # 🆕 E2E tests
```

## Dependencies (Updated)

```toml
dependencies = [
    "mcp[cli]>=1.2.0",
    "fastmcp>=0.1.0",
    "kicad-skip>=0.2.5",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "jinja2>=3.1.0",
]

dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-cov>=3.0.0",
    "pytest-asyncio>=0.21.0",
]

# Optional (for compilation testing)
# arduino-cli (for Arduino compilation)
# esp-idf (for ESP-IDF compilation)
# zephyr-sdk (for Zephyr compilation)
```

## Commit Workflow

Each feature must be:
1. Implemented with tests
2. Validated on real KiCad files
3. Generated code must compile
4. Committed with conventional commit format

Commit types:
- `feat:` - New feature (with tests)
- `test:` - Test additions
- `fix:` - Bug fix
- `validate:` - Validation improvements
- `docs:` - Documentation updates

## Roadmap

### Immediate (This Week)
- [ ] Implement `validate_schematic` tool
- [ ] Implement `check_kicad_compatibility` tool
- [ ] Implement `compile_test_code` tool
- [ ] Create test fixtures
- [ ] Add unit tests

### Short-term (This Month)
- [ ] Implement `test_design_creation` E2E tool
- [ ] Add integration tests with KiCad CLI
- [ ] Test with real hardware (ESP32S3 dev board)
- [ ] Verify generated code compiles and runs

### Long-term (Next Quarter)
- [ ] Continuous integration setup
- [ ] Automated regression testing
- [ ] Hardware-in-the-loop testing
- [ ] Performance optimization

## Documentation

- **README.md** - User-facing documentation
- **CLAUDE.md** - Development documentation
- **PLAN.md** - This file (implementation plan)
- **TESTING.md** - 🆕 Testing guide (to be created)
