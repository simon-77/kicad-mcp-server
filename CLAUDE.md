# Claude Code Context for KiCad MCP Server

## Project Overview
This is a Model Context Protocol (MCP) server for KiCad EDA software, enabling AI assistants (like Claude) to analyze KiCad schematics and PCBs, generate test code, and perform design rule checks.

## Key Architecture Points

### MCP Server Structure
- Uses **FastMCP** framework for MCP protocol implementation
- Tools are registered via `@mcp.tool()` decorators in `tools/` modules
- Main entry point: `src/kicad_mcp_server/server.py`
- Server initialized with `mcp = FastMCP(name="kicad-mcp-server", ...)`

### Tool Implementation Pattern
```python
from ..server import mcp

@mcp.tool()
async def tool_name(param: type, ...) -> str:
    """Tool description for users."""
    # Implementation
    return result
```

### File Parsers
- **SchematicParser** (`parsers/schematic_parser.py`):
  - Parses `.kicad_sch` files (S-expression format)
  - Extracts components, nets, title block
  - Uses regex-based parsing (can be enhanced with kicad-skip)

- **PCBParser** (`parsers/pcb_parser.py`):
  - Parses `.kicad_pcb` files
  - Extracts footprints, tracks, vias, zones
  - Calculates board statistics

### Test Code Generation
- Uses **Jinja2** templates in `templates/` directory
- Supports 6 frameworks: pytest, unittest, arduino, zephyr, st_hal, esp_idf
- Template rendering with context from schematic data
- Framework-specific initialization and test patterns

### Configuration Management
- Environment variables via `.env` file
- Singleton pattern in `config.py`
- Configurable paths, detail levels, framework defaults

## Important Implementation Details

### Data Models (`models/types.py`)
- Pydantic models for type safety
- `ComponentInfo`, `NetInfo`, `PinInfo`, `SymbolInfo`
- `FootprintInfo`, `PCBStatistics`
- `ERCError`, `DRCError`

### File Handlers (`utils/file_handlers.py`)
- `validate_kicad_file()` - Validates file path and extension
- `resolve_project_path()` - Resolves relative paths with search directories

### Common Patterns

1. **Error Handling Pattern:**
```python
try:
    parser = SchematicParser(file_path)
    # ... work
except FileNotFoundError as e:
    return f"Error: {e}"
except Exception as e:
    return f"Error doing X: {e}"
```

2. **Output Formatting Pattern:**
```python
lines = [
    f"# Title",
    "",
    "| Header1 | Header2 |",
    "|---------|---------|",
]
for item in items:
    lines.append(f"| {item.a} | {item.b} |")
return "\n".join(lines)
```

3. **Template Usage:**
```python
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)
template = env.get_template("template_name.j2")
return template.render(**context_data)
```

### Tool Categories

1. **Schematic Tools** (`schematic.py`):
   - Component listing and search
   - Net listing
   - Symbol details
   - General info

2. **PCB Tools** (`pcb.py`):
   - Footprint listing
   - Statistics
   - Net analysis
   - Track finding

3. **Summary Tools** (`summary.py`):
   - Human-readable summary generation
   - Functional block analysis
   - Power supply detection

4. **Test Generation** (`testgen.py`):
   - Multi-framework test generation
   - Template-based code generation
   - Framework selection and configuration

5. **DRC Tools** (`drc.py`):
   - ERC (Electrical Rules Check)
   - DRC (Design Rules Check)
   - Consistency checking

6. **Component Tools** (`components.py`):
   - BOM generation
   - Component analysis
   - Export functionality

## Testing

### Test Fixtures
- `tests/fixtures/example_schematic.kicad_sch` - Example schematic
- `tests/fixtures/example_pcb.kicad_pcb` - Example PCB

### Test Pattern
```python
@pytest.fixture
def example_file():
    return Path("tests/fixtures/example.kicad_sch")

def test_function(example_file):
    parser = SchematicParser(str(example_file))
    # assertions...
```

## Dependencies

Core dependencies:
- `fastmcp` - MCP server framework
- `mcp[cli]` - MCP SDK with CLI tools
- `kicad-skip` - KiCad file parsing
- `pydantic` - Data validation
- `jinja2` - Template engine
- `python-dotenv` - Configuration

## Development Notes

### When Adding New Tools

1. Create tool function in appropriate `tools/*.py` file
2. Use `@mcp.tool()` decorator
3. Add async function signature
4. Include comprehensive docstring
5. Return formatted string results
6. Import module in `tools/__init__.py`

### When Adding New Test Frameworks

1. Create template in `templates/<framework>/`
2. Add template name mapping in `testgen.py`
3. Update framework list in docs
4. Add framework-specific context data
5. Test generated code compiles/runs

### When Modifying Parsers

1. Maintain backward compatibility
2. Add new extraction methods as needed
3. Update docstrings
4. Add tests for new features
5. Handle edge cases (missing data, malformed files)

## Common Issues & Solutions

1. **Syntax Errors with `lines.extend([...])`**:
   - Should be `lines.extend([...])` - closing is `])`
   - NOT `lines = [...]` - closing is `]`

2. **Missing `import re` in parsers**:
   - Both `schematic_parser.py` and `pcb_parser.py` need `import re`

3. **Tool Registration**:
   - Tool modules must be imported in `tools/__init__.py`
   - Decorators run at import time

4. **Template Paths**:
   - Use `Path(__file__).parent.parent / "templates"` for relative paths
   - Templates use `.j2` extension

## Future Work Directions

1. **Enhanced Parsing**: Full kicad-skip integration for complete file parsing
2. **Real-time Updates**: KiCad IPC for live design synchronization
3. **Advanced DRC**: Track width, clearance, zone analysis
4. **More Frameworks**: CMSIS-Pack, PlatformIO, custom frameworks
5. **Testing**: Automated testing with real KiCad files
6. **Documentation**: API docs, user guides, examples

## Repository Management

- **Branch**: `main` (default)
- **Commit Format**: Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Version**: `0.1.0` (initial release)

## Related Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [KiCad File Format](https://dev-docs.kicad.org/en/file-formats/)
- [kicad-skip](https://github.com/devbism/kicad-skip)
