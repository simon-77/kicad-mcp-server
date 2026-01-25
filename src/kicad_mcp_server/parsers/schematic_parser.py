"""Schematic file parser wrapper using kicad-skip."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..utils.file_handlers import validate_kicad_file


@dataclass
class SchematicComponent:
    """Component from schematic file."""

    reference: str
    value: str
    library_id: str
    footprint: Optional[str] = None
    properties: dict[str, str] = field(default_factory=dict)
    position: tuple[float, float] = (0.0, 0.0)
    unit: Optional[int] = None
    pins: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_kicad_skip(cls, data: dict[str, Any]) -> "SchematicComponent":
        """Create from kicad-skip data structure."""
        # Extract properties
        properties = {}
        for prop in data.get("properties", []):
            key = prop.get("key", "")
            value = prop.get("value", "")
            if key and value:
                properties[key] = value

        # Get position
        at = data.get("at", {})
        position = (float(at.get("x", 0)), float(at.get("y", 0)))

        # Get unit
        unit = data.get("unit")

        return cls(
            reference=data.get("reference", ""),
            value=properties.get("Value", data.get("value", "")),
            library_id=data.get("lib_id", ""),
            footprint=properties.get("Footprint"),
            properties=properties,
            position=position,
            unit=unit,
            pins=data.get("pins", []),
        )


@dataclass
class SchematicNet:
    """Net from schematic file."""

    name: str
    code: int
    node_count: int = 0
    pins: list[str] = field(default_factory=list)

    @classmethod
    def from_kicad_skip(cls, data: dict[str, Any]) -> "SchematicNet":
        """Create from kicad-skip data structure."""
        return cls(
            name=data.get("name", ""),
            code=data.get("code", 0),
        )


@dataclass
class SchematicPin:
    """Pin definition from symbol."""

    number: str
    name: str
    type: str

    @classmethod
    def from_kicad_skip(cls, data: dict[str, Any]) -> "SchematicPin":
        """Create from kicad-skip data structure."""
        return cls(
            number=data.get("number", ""),
            name=data.get("name", ""),
            type=data.get("electrical_type", ""),
        )


class SchematicParser:
    """Parser for KiCad schematic files (.kicad_sch)."""

    def __init__(self, file_path: str) -> None:
        """Initialize parser with schematic file.

        Args:
            file_path: Path to .kicad_sch file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a .kicad_sch file
        """
        self.file_path = validate_kicad_file(file_path, ".kicad_sch")
        self._data: Optional[dict[str, Any]] = None

    def _parse_file(self) -> dict[str, Any]:
        """Parse the schematic file.

        Returns:
            Parsed data structure

        Note:
            This is a simplified parser. For production use, integrate kicad-skip
            or use kicad-netlist for proper parsing.
        """
        if self._data is not None:
            return self._data

        # Simple text-based parser for .kicad_sch (S-expression format)
        # In production, use kicad-skip library
        import re

        content = self.file_path.read_text()

        # Extract basic information using regex patterns
        # This is a simplified implementation
        self._data = {
            "path": str(self.file_path),
            "title_block": self._parse_title_block(content),
            "components": self._parse_components(content),
            "nets": self._parse_nets(content),
            "sheets": self._parse_sheets(content),
        }

        return self._data

    def _parse_title_block(self, content: str) -> dict[str, str]:
        """Parse title block from schematic."""
        title_block = {
            "title": "",
            "date": "",
            "rev": "",
            "company": "",
            "comment": "",
        }

        # Extract title block values using regex
        patterns = {
            "title": r'title\s+"([^"]*)"',
            "date": r'date\s+"([^"]*)"',
            "rev": r'rev\s+"([^"]*)"',
            "company": r'company\s+"([^"]*)"',
            "comment": r'comment\s+\d+\s+"([^"]*)"',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                title_block[key] = match.group(1)

        return title_block

    def _parse_components(self, content: str) -> list[dict[str, Any]]:
        """Parse components from schematic."""
        components = []

        # Find all symbol instances
        # Pattern: (symbol (lib_id ...) (property "Reference" "R1") ...)
        symbol_pattern = r'\(symbol[^)]*lib_id\s+"([^"]+)"[^)]*\(property\s+"Reference"\s+"([^"]+)"[^)]*\(property\s+"Value"\s+"([^"]+)"'

        for match in re.finditer(symbol_pattern, content, re.DOTALL):
            lib_id = match.group(1)
            reference = match.group(2)
            value = match.group(3)

            components.append({
                "lib_id": lib_id,
                "reference": reference,
                "value": value,
                "properties": {"Value": value},
                "pins": [],
            })

        return components

    def _parse_nets(self, content: str) -> list[dict[str, Any]]:
        """Parse nets from schematic."""
        nets = []

        # Find net segments
        # Pattern: (net (code 1) (name "GND") ...)
        net_pattern = r'\(net\s+\(code\s+(\d+)\)\s*\(name\s+"([^"]+)"\)'

        for match in re.finditer(net_pattern, content):
            code = int(match.group(1))
            name = match.group(2)

            nets.append({
                "code": code,
                "name": name,
            })

        return nets

    def _parse_sheets(self, content: str) -> list[dict[str, str]]:
        """Parse hierarchical sheets."""
        sheets = []

        # Find sheet instances
        sheet_pattern = r'\(sheet\s+\(at\s+(\d+)\s+(\d+)\)\s*\(size\s+\d+\s+\d+\)\s*\(fields_autoplaced\s+yes\)\s*\(stroke[^)]*\)\s*\(fill[^)]*\)\s*\(property\s+"Sheetname"\s+"([^"]+)"[^)]*\(property\s+"Sheetfile"\s+"([^"]+)"'

        for match in re.finditer(sheet_pattern, content):
            sheets.append({
                "name": match.group(3),
                "file": match.group(4),
            })

        return sheets

    def get_components(self) -> list[SchematicComponent]:
        """Get all components from schematic.

        Returns:
            List of components
        """
        data = self._parse_file()
        return [SchematicComponent.from_kicad_skip(c) for c in data["components"]]

    def get_nets(self) -> list[SchematicNet]:
        """Get all nets from schematic.

        Returns:
            List of nets
        """
        data = self._parse_file()
        return [SchematicNet.from_kicad_skip(n) for n in data["nets"]]

    def get_title_block(self) -> dict[str, str]:
        """Get title block information.

        Returns:
            Dictionary with title, date, rev, company, comment
        """
        data = self._parse_file()
        return data["title_block"]

    def get_sheets(self) -> list[dict[str, str]]:
        """Get hierarchical sheets.

        Returns:
            List of sheet information
        """
        data = self._parse_file()
        return data["sheets"]

    def get_component_by_reference(self, reference: str) -> Optional[SchematicComponent]:
        """Get a component by its reference designator.

        Args:
            reference: Component reference (e.g., "R1", "U1")

        Returns:
            Component if found, None otherwise
        """
        for component in self.get_components():
            if component.reference == reference:
                return component
        return None

    def search_components(self, pattern: str) -> list[SchematicComponent]:
        """Search for components by pattern.

        Args:
            pattern: Search pattern (matches reference, value, or library_id)

        Returns:
            List of matching components
        """
        import re

        regex = re.compile(pattern, re.IGNORECASE)
        results = []

        for component in self.get_components():
            if (
                regex.search(component.reference)
                or regex.search(component.value)
                or regex.search(component.library_id)
            ):
                results.append(component)

        return results
