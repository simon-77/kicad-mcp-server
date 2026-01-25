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
)

__all__ = ["schematic", "pcb", "summary", "testgen", "drc", "components", "editor", "pcb_editor", "project"]
