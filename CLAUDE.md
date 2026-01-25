# KiCad MCP Server - Development Documentation

## Project Overview

A **natural language-driven** KiCad 9.0 design tool that enables AI assistants (via MCP protocol) to:
- 🎯 Create schematic and PCB designs
- 📊 Analyze existing KiCad projects
- 🧪 Generate automated test code
- 🔌 Integrate LCSC (LiCheng Mall) component library

## Core Design Principles

### 1. Use KiCad Python API
**Important**: Use KiCad's Python API (pcbnew) whenever possible, instead of manually generating S-expression files.

**Why**:
- ✅ Ensures 100% file format compatibility
- ✅ Avoids manual format errors
- ✅ Automatically handles KiCad version differences

**Implementation**:
```python
# Import KiCad API (requires KiCad environment)
import pcbnew

# Create PCB
board = pcbnew.BOARD()
board.SetFileName("/path/to/project.kicad_pcb")

# Add footprint
footprint = pcbnew.FootprintLoad("Resistor_SMD:R_0805_2012Metric")
footprint.SetReference("R1")
board.Add(footprint)

# Save
pcbnew.SaveBoard("/path/to/project.kicad_pcb", board)
```

### 2. Based on KiCad 9.0
- Project file format: `.kicad_pro` (JSON, version=3)
- Schematic format: `.kicad_sch` (version 20240130)
- PCB format: `.kicad_pcb` (version 20240130)

### 3. Natural Language Interaction
Support design descriptions in Chinese and English, for example:
```
"Use XiaoESP32S3 as main controller, add an OLED display and IMU sensor,
layout on a 30x30mm PCB"
```

### 4. LCSC Integration
- Automatically search for components on LCSC
- Match correct PCB footprints
- Generate BOMs with purchase links

### 5. Project Analysis and Test Code Generation
- Analyze existing project structure and connections
- Generate test code for multiple frameworks
- Support Arduino, ESP-IDF, Zephyr, etc.

## Architecture Design

### MCP Server Structure
```
FastMCP Framework
    ↓
Tool Registration (@mcp.tool())
    ↓
KiCad Python API / File Parsing
    ↓
Result Return (Markdown format)
```

### Core Modules

#### 1. Project Creation (`tools/project.py`)
**Method**: Based on KiCad official templates

```python
def _find_kicad_template() -> Path:
    """Find KiCad template path"""
    templates = [
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/template/Arduino_Mega",
        "/usr/share/kicad/template/Arduino_Mega",
        "C:/Program Files/KiCad/9.0/share/kicad/template/Arduino_Mega",
    ]
    # Return first existing template

async def create_kicad_project(path, name, title, company):
    """Create project by copying template"""
    # 1. Copy template files
    # 2. Modify UUID and title
    # 3. Update .kicad_pro JSON
```

#### 2. Schematic Editing (`tools/schematic_editor.py`)
```python
@mcp.tool()
async def add_component_from_library(
    file_path, library_name, symbol_name,
    reference, value, footprint, x, y
):
    """Add component to schematic"""
    # Parse .kicad_sch file
    # Add symbol instance
    # Generate new UUID
    # Save file

@mcp.tool()
async def add_wire(file_path, points):
    """Add wire connection"""
    # Add wire segment

@mcp.tool()
async def add_global_label(file_path, text, x, y):
    """Add global label"""
```

#### 3. Footprint Library Management (`tools/footprint_library.py`)
```python
@mcp.tool()
async def list_common_footprints(category):
    """List common footprints (LCSC compatible)"""

@mcp.tool()
async def search_kicad_footprints(search_term):
    """Search footprints"""

@mcp.tool()
async def download_footprint_library(library_name, output_path):
    """Download footprint library from GitHub"""
```

#### 4. Project Analysis (`tools/summary.py`)
```python
@mcp.tool()
async def summarize_schematic(
    file_path, detail_level, include_nets
):
    """Generate schematic summary
    - Project information
    - Component list
    - Peripheral identification
    - Connection diagram
    """
```

#### 5. Test Code Generation (`tools/testgen.py`)
```python
@mcp.tool()
async def generate_test_code(
    schematic_path, test_framework,
    test_type, target_mcu
):
    """Generate test code
    - Arduino: C++ sketch
    - ESP-IDF: C code
    - Zephyr: RTOS test
    - pytest: Python test
    """
```

## File Format Handling

### KiCad 9.0 File Formats

#### .kicad_pro (JSON format)
```json
{
  "meta": {
    "filename": "project.kicad_pro",
    "version": 3  // ← Must be 3 for KiCad 9.0
  },
  "board": {
    "design_settings": {...}
  },
  "sheets": [[uuid, "Root"]],
  "libraries": {...}
}
```

#### .kicad_sch (S-expression)
```lisp
(kicad_sch
  (version 20240130)
  (generator "eeschema")
  (generator_version "9.0")  // ← KiCad 9.0
  (uuid "...")
  (paper "A4")
  (title_block ...)
  (lib_symbols ...)
  (symbol ...)
  (wire ...)
)
```

### Footprint Name Format
```
Library:Name
Example: Resistor_SMD:R_0805_2012Metric
```

## Natural Language Processing

### Design Intent Recognition
```python
# Extract design requirements from user input
def parse_design_intent(text):
    """
    "Use XiaoESP32S3, add an OLED, add an IMU"
    ↓
    {
      "mcu": "ESP32-S3",
      "peripherals": [
        {"type": "OLED", "interface": "I2C"},
        {"type": "IMU", "interface": "I2C"}
      ],
      "pcb_size": None
    }
    """
```

### Automatic Pin Assignment
```python
# Select pins based on peripheral type
I2C_PERIPHERALS = {
    "GPIO6": "SDA",
    "GPIO7": "SCL",
}

# Auto-infer connections
def auto_connect_peripherals(mcu, peripherals):
    for peripheral in peripherals:
        if peripheral["interface"] == "I2C":
            # Connect to I2C bus
            add_wire(mcu["GPIO6"], peripheral["SDA"])
            add_wire(mcu["GPIO7"], peripheral["SCL"])
```

## LCSC Integration

### Component Database
```python
LCSC_COMPONENTS = {
    "ESP32-S3": {
        "sku": "C2815836",
        "footprint": "Module:ESP32-WROOM-32",
        "price": 25.0
    },
    "SSD1306": {
        "sku": "C124233",
        "footprint": "Display:OLED-0.91-128x32",
        "price": 15.0
    },
    "MPU6050": {
        "sku": "C241086",
        "footprint": "Sensor_Motion:QFN-24_4x4mm_P0.5mm",
        "price": 8.0
    }
}
```

### BOM Generation
```python
@mcp.tool()
async def generate_bom(file_path, include_pricing):
    """Generate BOM with LCSC pricing and links"""
```

## Test Code Generation

### Template System
Using Jinja2 templates:
```
templates/
├── arduino/
│   └── connectivity_test.cpp.j2
├── esp_idf/
│   └── test_main.c.j2
├── zephyr/
│   └── test_sample.c.j2
└── pytest/
    └── test_schematic.py.j2
```

### Context Data
```python
context = {
    "mcu": {"type": "ESP32-S3", "port": "Arduino"},
    "peripherals": [
        {"name": "OLED", "type": "I2C", "addr": "0x3C"},
        {"name": "IMU", "type": "I2C", "addr": "0x68"}
    ],
    "pins": {
        "I2C_SDA": 6,
        "I2C_SCL": 7
    }
}
```

## Development Standards

### Adding New Tools
```python
# 1. Create in appropriate tools/*.py
from ..server import mcp

@mcp.tool()
async def new_tool(param: type, ...) -> str:
    """Tool description (for AI understanding)"""
    try:
        # Implementation
        return formatted_result
    except Exception as e:
        return f"Error: {e}"
```

### Error Handling Pattern
```python
try:
    # KiCad operations
    result = perform_operation()
except FileNotFoundError:
    return "❌ File not found"
except KiCadError as e:
    return f"❌ KiCad error: {e}"
except Exception as e:
    import traceback
    return f"❌ Unknown error: {e}\n\n{traceback.format_exc()}"
```

### Return Format
Use Markdown for output:
```python
return f"""# ✅ Operation Successful

**File**: {file_path}
**Component**: {component}

## Details
| Item | Value |
|------|-------|
| Footprint | {footprint} |
| Position | ({x}, {y}) |
"""
```

## KiCad API Limitations

### pcbnew Usage Limitations
```python
# ⚠️ pcbnew requires KiCad GUI environment
# Cannot be used in pure CLI environment

# Solution 1: Use KiCad Scripting Console
# Run scripts within KiCad

# Solution 2: Use Template Copy Method
# Copy KiCad template files, modify necessary parts

# ✅ Recommended: Template Copy Method
# See tools/project.py implementation
```

### S-expression Parsing
```python
# Use kicad-skip library if available
try:
    from kicad_skip import parse
    data = parse(file_path)
except ImportError:
    # Fall back to regex parsing
    import re
    # Manual parsing
```

## Testing Strategy

### Unit Tests
```python
def test_create_project():
    """Test project creation"""
    path = Path("/tmp/test_project")
    result = create_kicad_project(str(path), "test")
    assert (path / "test.kicad_pro").exists()
```

### Integration Tests
```bash
# Test in real KiCad environment
1. Create project
2. Open in KiCad 9.0
3. Verify no warnings
4. Run ERC/DRC
```

## Common Issues

### Q: KiCad crashes on opening?
**A**: File format error. Use template copy method, don't manually generate.

### Q: Footprint not found?
**A**:
1. Use KiCad standard footprint names
2. Check if footprint libraries are installed
3. Use `list_common_footprints` to see available footprints

### Q: How to add support for new MCUs?
**A**:
1. Add entry in `LCSC_COMPONENTS`
2. Specify correct footprint name
3. Define pin configuration

### Q: Test code won't compile?
**A**:
1. Check template syntax
2. Verify context data completeness
3. Test generated code

## Performance Optimization

### Large File Processing
```python
# Use streaming
def process_large_schematic(file_path):
    with open(file_path) as f:
        for line in f:
            process_line(line)
```

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_footprint_info(name):
    # Cache footprint info
    return query_footprint(name)
```

## Extension Roadmap

### Short-term
- [ ] More MCU support
- [ ] Auto PCB layout
- [ ] Richer test templates

### Long-term
- [ ] AI auto-routing
- [ ] 3D model generation
- [ ] Real-time price queries
- [ ] Supply chain integration

## Resources

### KiCad Official
- [KiCad 9.0 Documentation](https://docs.kicad.org/)
- [File Format Specification](https://dev-docs.kicad.org/en/file-formats/)
- [Python Scripting](https://docs.kicad.org/doxygen-python/)

### LCSC Mall
- [LCSC Website](https://www.lcsc.com/)
- [API Documentation](https://www.lcsc.com/products)

### MCP Protocol
- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
