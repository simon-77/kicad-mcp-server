# KiCad MCP Server

A Model Context Protocol (MCP) server for KiCad 9.0 EDA software that provides schematic analysis, PCB analysis, and project editing capabilities.

## Overview

This server implements 6 core tools organized into 3 categories:

- **Analysis Tools** (3): Schematic analysis, PCB analysis, netlist-based connection tracing
- **Editing Tools** (2): Schematic editing, PCB layout
- **Project Management** (1): Project creation and management

## Features

### Schematic Analysis

Analyze KiCad schematic files (.kicad_sch):

- `list_schematic_components()` - List all components with optional filtering
- `list_schematic_nets()` - List all nets
- `get_schematic_info()` - Get schematic metadata and statistics
- `search_symbols()` - Search for specific symbols
- `get_symbol_details()` - Get detailed symbol information
- `analyze_functional_blocks()` - Analyze functional blocks in schematic

### PCB Analysis

Analyze KiCad PCB files (.kicad_pcb) using official pcbnew API:

- `list_pcb_footprints()` - List all footprints
- `get_pcb_statistics()` - Get PCB statistics (dimensions, layer count, etc.)
- `find_tracks_by_net()` - Find tracks belonging to a specific net
- `get_footprint_by_reference()` - Get detailed footprint information
- `analyze_pcb_nets()` - Analyze PCB nets

### Netlist Analysis

Parse KiCad XML netlist files for 100% accurate pin-level connection tracking:

- `trace_netlist_connection()` - Trace component connections with pin-level accuracy
- `get_netlist_nets()` - List all nets with optional filtering
- `get_netlist_components()` - List all components with their net connections
- `generate_netlist()` - Export netlist from schematic

**Why use netlist analysis?**
- KiCad official XML format
- Pin-level precision
- Includes all connections (explicit and implicit)
- Bidirectional queries (component <-> network)

### Schematic Editing (Experimental)

Create and modify KiCad schematics:

- `create_kicad_project()` - Create new KiCad project
- `add_component_from_library()` - Add components from library
- `add_wire()` - Add wire connections
- `add_global_label()` - Add global labels
- `add_label()` - Add local labels

### PCB Layout (Experimental)

PCB layout and editing:

- `setup_pcb_layout()` - Initialize PCB with specified dimensions
- `add_footprint()` - Add footprints to PCB
- `add_track()` - Add tracks
- `add_zone()` - Add copper zones
- `export_gerber()` - Export Gerber files for manufacturing

### Project Management

KiCad project creation and management:

- `create_kicad_project()` - Create new project from template
- `copy_kicad_project()` - Copy existing project

## Limitations and Recommendations

### Current Status

**Analysis Tools (Production-Ready)**
- Schematic analysis: Fully functional
- PCB analysis: Fully functional (uses official pcbnew API)
- Netlist analysis: 100% accurate, recommended for connection tracing

**Editing Tools (Experimental)**
- Schematic editing: Basic functionality, has limitations
- PCB layout: Basic functionality, has limitations

### Known Limitations

**Schematic Editing:**
- Components are added with minimal pin definitions
- Wire connections may not form proper electrical connections
- Symbol placement may not be visually aligned
- **Recommendation**: Use KiCad GUI for actual schematic editing

**PCB Layout:**
- Basic initialization only
- No automatic placement or routing
- **Recommendation**: Use KiCad GUI for PCB layout

### Recommended Workflow

```
1. Create Project (MCP or KiCad GUI)
   ↓
2. Edit Schematic in KiCad GUI
   - Add components
   - Wire connections
   - Design validation
   ↓
3. Export Netlist (KiCad CLI)
   kicad-cli sch export netlist --format kicadxml
   ↓
4. Analyze Design (MCP Server)
   - Trace connections (netlist-based)
   - List components
   - Verify topology
   ↓
5. Analyze PCB (MCP Server)
   - Check footprints
   - Verify tracks
   - Get statistics
```

### Future Improvements

The editing tools are currently experimental and will be improved in future releases. For now, we recommend:

- Use KiCad GUI for all design and editing work
- Use MCP server for analysis and verification
- Use netlist export for accurate connection tracing

## Installation

```bash
# Clone repository
git clone https://github.com/LynnL4/kicad-mcp-server.git
cd kicad-mcp-server

# Install dependencies
pip install -r requirements.txt
```

### Requirements

- Python 3.10 or higher
- KiCad 9.0 or later
- macOS / Linux / Windows

## Configuration

### Claude Desktop

Add to Claude Desktop configuration file (`~/.claude.json` on Linux/macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "kicad": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "kicad_mcp_server"],
      "cwd": "/path/to/kicad-mcp-server",
      "env": {
        "PYTHONPATH": "/path/to/kicad-mcp-server/src"
      }
    }
  }
}
```

**Windows Example:**
```json
{
  "mcpServers": {
    "kicad": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "kicad_mcp_server"],
      "cwd": "C:\\Users\\YourName\\Desktop\\kicad-mcp-server",
      "env": {
        "PYTHONPATH": "C:\\Users\\YourName\\Desktop\\kicad-mcp-server\\src"
      }
    }
  }
}
```

## Usage

### Analyze Schematic

```python
# List all resistors
list_schematic_components("Power.kicad_sch", filter_type="R")

# Get schematic information
get_schematic_info("Power.kicad_sch")

# Search for components
search_symbols("Power.kicad_sch", pattern="U1")
```

### Trace Connections Using Netlist (Recommended)

First, export netlist from KiCad:

```bash
kicad-cli sch export netlist --format kicadxml \
  --output Power.net.xml Power.kicad_sch
```

Then trace connections:

```python
# Trace component connections (100% accurate)
trace_netlist_connection("Power.net.xml", "Q3")

# List all I2C nets
get_netlist_nets("Power.net.xml", filter_pattern="I2C")

# Get all components with their nets
get_netlist_components("Power.net.xml", filter_ref="U")
```

### Analyze PCB

```python
# Get PCB statistics
get_pcb_statistics("reSpeaker Lav.kicad_pcb")

# List all footprints
list_pcb_footprints("reSpeaker Lav.kicad_pcb")

# Find tracks by net
find_tracks_by_net("reSpeaker Lav.kicad_pcb", "GND")
```

### Edit Schematic

```python
# Create new project
create_kicad_project(
    path="/projects/MyDesign",
    name="MyDesign",
    title="My Design",
    company="My Company"
)

# Add component
add_component_from_library(
    file_path="Power.kicad_sch",
    library_name="Device",
    symbol_name="R",
    reference="R16",
    value="4.7K",
    x=150,
    y=200
)

# Add wire
add_wire("Power.kicad_sch", points=[(100, 100), (150, 100)])
```

### Edit PCB

```python
# Initialize PCB layout
setup_pcb_layout("Power.kicad_sch", width=100, height=100, unit="mm")

# Export Gerber files
export_gerber("reSpeaker Lav.kicad_pcb")
```

## Architecture

### Tool Organization

The server is organized into 6 modules:

1. **schematic** - Schematic file analysis and parsing
2. **pcb** - PCB file analysis using pcbnew API
3. **netlist** - XML netlist parsing and connection tracing
4. **schematic_editor** - Schematic editing and project creation
5. **pcb_layout** - PCB layout initialization and editing
6. **project** - KiCad project management

### KiCad 9.0 Compatibility

- Uses KiCad official templates for project creation
- Supports `.kicad_pro` (JSON format, version 3)
- Supports `.kicad_sch` (S-expression format, version 20240130)
- Supports `.kicad_pcb` (S-expression format, version 20240130)

### Parser Implementation

- **Schematic parser**: Custom S-expression parser
- **PCB parser**: KiCad pcbnew Python API
- **Netlist parser**: XML parser for KiCad netlist format

## Documentation

- **README.md** - This file (user guide)
- **CLAUDE.md** - Development documentation

## Design Decisions

### Scope

The server focuses on analysis and project management:

1. **Analysis** - Understand existing designs (Production-Ready)
2. **Project Management** - Create and organize projects (Production-Ready)
3. **Editing** - Basic schematic/PCB editing (Experimental)

### Technical Limitations

**Why Editing Tools Are Experimental:**

KiCad 9.0 does not provide Python APIs for schematic editing:

- **PCB**: Has official `pcbnew` API (fully functional)
- **Schematic**: No Python API available (manual S-expression parsing required)
- **Netlist**: Can export via CLI, but cannot import via API

**Schematic Editing Challenges:**

1. **Complex S-expression Format**
   - KiCad schematics use nested Lisp-like expressions
   - Requires precise UUID generation for all elements
   - Pin definitions need exact positions and electrical types

2. **Symbol Instantiation**
   - Must reference library symbols correctly
   - Requires proper pin mapping and units
   - Visual alignment is difficult without GUI

3. **Electrical Connections**
   - Wires must connect to exact pin coordinates
   - Junctions and labels need proper formatting
   - Power symbols have special handling

**Current Approach:**

```python
# Simplified component addition (experimental)
component_entry = f'''
  (symbol (lib_id "{lib_id}") (at {x} {y} 0)
    (exclude_from_sim no)
    (uuid {uuid})
    (pins...)  # Minimal pin definitions
  )
'''
```

**Result**: Components are added but may lack complete electrical information.

### Out of Scope

The following features are intentionally not included:

- Test code generation (not a core requirement)
- Natural language processing (use AI assistant directly)
- Component library management (use KiCad built-in libraries)
- Auto-routing (use KiCad's built-in router)
- Complete schematic editing (use KiCad GUI instead)

### Recommended Usage

**For Best Results:**

1. **Design Phase**: Use KiCad GUI for all schematic and PCB editing
2. **Analysis Phase**: Use MCP server to analyze and verify designs
3. **Connection Tracing**: Export netlist and use MCP netlist tools
4. **Automation**: Use MCP for bulk analysis and reporting

**MCP Server Excels At:**
- Analyzing existing schematics
- Tracing connections (netlist-based)
- Listing components and footprints
- PCB statistics and verification
- Project organization

**KiCad GUI Excels At:**
- Schematic design and editing
- PCB layout and routing
- Visual design verification
- Interactive component placement

### Optimization Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Number of tools | 10 | 6 | -40% |
| Lines of code | ~3500 | ~2250 | -36% |
| Focus | Distributed | Core | Improved |
| Analysis tools | Basic | Production-Ready | ✅ |
| Editing tools | Ambitious | Experimental | ⚠️ |

## Resources

- [KiCad Documentation](https://docs.kicad.org/)
- [KiCad 9.0 File Format Specification](https://dev-docs.kicad.org/en/file-formats/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [KiCad Python Scripting](https://docs.kicad.org/doxygen-python/)

## License

MIT License
