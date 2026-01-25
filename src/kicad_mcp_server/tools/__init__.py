"""Tools package for KiCad MCP Server."""

# Import tool modules to register their functions with the MCP server
# The actual registration happens when the modules are imported
# and their @mcp.tool() decorators are evaluated

# Import order matters for organization, but all tools will be registered
from . import (
    schematic,
    pcb,
    summary,
    testgen,
    drc,
    components,
    editor,
    pcb_editor,
    project,
    schematic_editor,
    footprint_library,
    validation,
    e2e_test,
    arduino_codegen,
    nl_parser,
    pcb_layout,
)

__all__ = ["schematic", "pcb", "summary", "testgen", "drc", "components", "editor", "pcb_editor", "project", "schematic_editor", "footprint_library", "validation", "e2e_test", "arduino_codegen", "nl_parser", "pcb_layout"]
