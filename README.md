# KiCad MCP Server

A Model Context Protocol (MCP) server for KiCad file analysis, providing capabilities for schematic analysis, PCB analysis, design rule checking, and automated test code generation.

## Features

- **Schematic Analysis**
  - List and filter components
  - Analyze nets and connectivity
  - Search and inspect symbols
  - Generate human-readable schematic summaries

- **PCB Analysis**
  - List and analyze footprints
  - Track and net analysis
  - PCB statistics

- **Design Rule Checking**
  - Electrical Rules Check (ERC)
  - Design Rules Check (DRC)
  - Schematic-PCB consistency verification

- **Component Management**
  - Query symbol libraries
  - Generate Bills of Materials (BOM)

- **Test Code Generation** 🆕
  - Generate test code for multiple frameworks:
    - pytest (Python)
    - unittest (Python)
    - Arduino (C++)
    - Zephyr RTOS
    - STM32 HAL
    - ESP-IDF
  - Support for connectivity, functional, documentation, and production test types

## Installation

```bash
# Install from source
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Usage

### Running the Server

```bash
# Direct execution
python -m kicad_mcp_server

# Or via installed script
kicad-mcp-server
```

### MCP Tool Examples

```python
# Summarize a schematic
await mcp.call_tool("summarize_schematic", {
    "file_path": "path/to/schematic.kicad_sch",
    "detail_level": "standard"
})

# Generate Arduino test code
await mcp.call_tool("generate_test_code", {
    "schematic_path": "path/to/schematic.kicad_sch",
    "test_framework": "arduino",
    "test_type": "connectivity",
    "target_mcu": "atmega328p"
})

# Generate Zephyr RTOS tests
await mcp.call_tool("generate_test_code", {
    "schematic_path": "path/to/schematic.kicad_sch",
    "test_framework": "zephyr",
    "test_type": "functional",
    "target_mcu": "esp32"
})

# List schematic components
await mcp.call_tool("list_schematic_components", {
    "file_path": "path/to/schematic.kicad_sch",
    "filter_type": "IC"
})
```

## Configuration

Create a `.env` file in your project root (see `.env.example`):

```bash
# Path to KiCad project directories (optional)
KICAD_PROJECT_PATHS=/path/to/projects1,/path/to/projects2

# Default detail level for summaries (brief, standard, detailed)
DEFAULT_SUMMARY_DETAIL_LEVEL=standard
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check --fix src tests

# Type checking
mypy src
```

## Project Structure

```
kicad-mcp-server/
├── src/kicad_mcp_server/
│   ├── tools/          # MCP tool implementations
│   ├── parsers/        # File parsing wrappers
│   ├── models/         # Data models
│   ├── utils/          # Utilities
│   └── templates/      # Jinja2 templates for test code
└── tests/              # Test fixtures and tests
```

## Requirements

- Python 3.10 or higher
- KiCad files (schematic .kicad_sch, PCB .kicad_pcb)
- No KiCad installation required for basic analysis

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
