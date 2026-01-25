"""Footprint library management tools for KiCad MCP Server.

Provides functionality to:
- Search for footprints in KiCad's official libraries
- Download footprint libraries from GitHub
- Manage local footprint libraries
- Create custom footprint libraries for projects
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional
from ..server import mcp
import json


@mcp.tool()
async def search_kicad_footprints(
    search_term: str,
    library_path: Optional[str] = None,
) -> str:
    """Search for footprints in KiCad libraries using KiCad CLI or local files.

    Args:
        search_term: Term to search for (e.g., "ESP32", "0805", "OLED")
        library_path: Optional path to footprint library folder (defaults to KiCad user libraries)

    Returns:
        List of matching footprints with library names and descriptions
    """
    try:
        # Try to use KiCad CLI if available
        kicad_cli = shutil.which("kicad-cli")

        if kicad_cli:
            # Use KiCad CLI to search footprints
            result = subprocess.run(
                [kicad_cli, "fp", "list", search_term],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return f"""✅ Found footprints matching "{search_term}":

{result.stdout}

Use the full footprint name (e.g., "Resistor_SMD:R_0805_2012Metric") when adding components.
"""
            else:
                return f"⚠️ KiCad CLI search failed: {result.stderr}"

        # Fallback: Search local footprint files
        search_paths = []

        if library_path:
            search_paths.append(Path(library_path))
        else:
            # Try common KiCad library paths
            possible_paths = [
                Path.home() / "Documents" / "KiCad" / "9.0" / "footprints",
                Path.home() / ".local" / "share" / "kicad" / "9.0" / "footprints",
                Path("/usr/share/kicad/9.0/footprints"),
                Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"),
            ]

            for path in possible_paths:
                if path.exists():
                    search_paths.append(path)

        if not search_paths:
            return """❌ No footprint libraries found.

Please install KiCad footprint libraries or specify a library_path.

**Options:**

1. **Install KiCad Official Libraries:**
   ```bash
   # macOS
   brew install kicad-libraries

   # Linux
   sudo apt install kicad-libraries

   # Or download manually:
   # https://gitlab.com/kicad/libraries/kicad-footprints
   ```

2. **Download footprint libraries to project:**
   Use the `download_footprint_library` tool to download specific libraries.

3. **Use built-in KiCad footprints:**
   Ensure KiCad is properly installed with library packages.
"""

        # Search in local paths
        matches = []
        for search_path in search_paths:
            for lib_file in search_path.rglob("*.pretty"):
                # Read .pretty directory metadata
                lib_name = lib_file.name
                for footprint_file in lib_file.glob("*.kicad_mod"):
                    footprint_name = footprint_file.stem
                    if search_term.lower() in footprint_name.lower() or search_term.lower() in lib_name.lower():
                        matches.append(f"  - {lib_name}:{footprint_name}")

        if matches:
            return f"""✅ Found {len(matches)} footprint(s) matching "{search_term}":

{chr(10).join(matches[:20])}
{f"... and {len(matches) - 20} more" if len(matches) > 20 else ""}

Use the full footprint name (e.g., "Resistor_SMD:R_0805_2012Metric") when adding components.
"""
        else:
            return f"""❌ No footprints found matching "{search_term}"

The local libraries might not be installed. Use `download_footprint_library` to get libraries from GitHub.
"""

    except Exception as e:
        import traceback
        return f"Error searching footprints: {e}\n\n{traceback.format_exc()}"


@mcp.tool()
async def download_footprint_library(
    library_name: str,
    output_path: str,
    source: str = "official",
) -> str:
    """Download a KiCad footprint library from GitHub or other sources.

    Args:
        library_name: Name of the library (e.g., "Resistor_SMD", "LED", "Module")
        output_path: Directory where the library should be saved
        source: Source to download from - "official", "jlcpcb", or "github"

    Returns:
        Confirmation message with download details
    """
    try:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        if source == "official":
            # Download from KiCad official GitLab
            repo_url = "https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/main"

            lib_url = f"{repo_url}/{library_name}.pretty"
            target_dir = output_dir / f"{library_name}.pretty"

            if target_dir.exists():
                return f"⚠️ Library {library_name} already exists at {target_dir}"

            # Use git to clone the specific library
            git_available = shutil.which("git")

            if git_available:
                # Clone the entire repo and checkout just the library we need
                result = subprocess.run(
                    [
                        "git", "clone",
                        "--depth", "1",
                        "--filter=blob:none",
                        "--sparse",
                        "https://gitlab.com/kicad/libraries/kicad-footprints.git",
                        str(target_dir.parent / "temp_clone")
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    # Checkout just the library we need
                    sparse_dir = target_dir.parent / "temp_clone"
                    subprocess.run(
                        ["git", "sparse-checkout", "set", f"{library_name}.pretty"],
                        cwd=sparse_dir,
                        capture_output=True
                    )

                    # Move to target location
                    lib_source = sparse_dir / f"{library_name}.pretty"
                    if lib_source.exists():
                        shutil.move(str(lib_source), str(target_dir))
                        shutil.rmtree(sparse_dir)

                        return f"""✅ Successfully downloaded {library_name} library!

**Source:** KiCad Official (GitLab)
**Location:** {target_dir}
**Files:** {len(list(target_dir.glob("*.kicad_mod")))} footprints

**Next Steps:**

1. Add this library to your KiCad footprint libraries table:
   - Open KiCad
   - Preferences → Configure Paths → Add new nickname: "KICAD_FOOTPRINTS" → {output_dir}
   - Preferences → Footprint Libraries Manager → Add → Select library

2. Use footprints in schematics:
   - Footprint name format: {library_name}:<footprint_name>
   - Example: {library_name}:R_0805_2012Metric
"""
                    else:
                        shutil.rmtree(sparse_dir)
                        return f"❌ Library {library_name} not found in KiCad official libraries"
                else:
                    return f"❌ Failed to clone repository: {result.stderr}"
            else:
                return """❌ Git is not installed. Please install git first:

    macOS: brew install git
    Linux: sudo apt install git
    Windows: https://git-scm.com/downloads

Or download libraries manually from:
https://gitlab.com/kicad/libraries/kicad-footprints
"""

        elif source == "jlcpcb":
            # JLCPCB/LCSC compatible libraries
            repo_url = "https://github.com/LaurentVLblome/KiCad-JLCPCB-Footprints-Library"

            target_dir = output_dir / f"{library_name}.pretty"

            git_available = shutil.which("git")

            if git_available:
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    return f"""✅ Successfully downloaded JLCPCB footprint library!

**Source:** JLCPCB/LCSC Compatible (GitHub)
**Location:** {target_dir}

These footprints are optimized for JLCPCB assembly and match LCSC component footprints.
"""
                else:
                    return f"❌ Failed to clone JLCPCB library: {result.stderr}"
            else:
                return "❌ Git is required for downloading libraries"

        else:
            return f"❌ Unknown source: {source}. Use 'official' or 'jlcpcb'"

    except Exception as e:
        import traceback
        return f"Error downloading footprint library: {e}\n\n{traceback.format_exc()}"


@mcp.tool()
async def list_common_footprints(
    category: str = "all",
) -> str:
    """List commonly used footprints for quick reference.

    Args:
        category: Category to list - "resistors", "capacitors", "leds", "modules", "connectors", "all"

    Returns:
        List of common footprints with descriptions and LCSC compatibility
    """
    footprints = {
        "resistors": [
            ("Resistor_SMD:R_0402_1005Metric", "0402 (1005 metric) - LCSC C250989"),
            ("Resistor_SMD:R_0603_1608Metric", "0603 (1608 metric) - LCSC C231452"),
            ("Resistor_SMD:R_0805_2012Metric", "0805 (2012 metric) - LCSC C17557"),
            ("Resistor_SMD:R_1206_3216Metric", "1206 (3216 metric) - LCSC C173609"),
            ("Resistor_SMD:R_2512_6332Metric", "2512 (6332 metric) - High power"),
        ],
        "capacitors": [
            ("Capacitor_SMD:C_0402_1005Metric", "0402 (1005 metric) - LCSC C24123"),
            ("Capacitor_SMD:C_0603_1608Metric", "0603 (1608 metric) - LCSC C158498"),
            ("Capacitor_SMD:C_0805_2012Metric", "0805 (2012 metric) - LCSC C49678"),
            ("Capacitor_SMD:C_1206_3216Metric", "1206 (3216 metric) - LCSC C135826"),
        ],
        "leds": [
            ("LED_SMD:LED_0402_1005Metric", "0402 LED - Miniature"),
            ("LED_SMD:LED_0603_1608Metric", "0603 LED - LCSC C229018"),
            ("LED_SMD:LED_0805_2012Metric", "0805 LED - LCSC C229018"),
            ("LED_SMD:LED_1206_3216Metric", "1206 LED - High brightness"),
        ],
        "modules": [
            ("Module:ESP32-WROOM-32", "ESP32 WROOM module - LCSC C503592"),
            ("Module:ESP32-WROOM-32-N16R8", "ESP32 WROOM N16R8 - LCSC C503592"),
            ("Module:ESP32-S3-WROOM-1", "ESP32-S3 module - LCSC C2815836"),
        ],
        "connectors": [
            ("Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "4-pin header 2.54mm"),
            ("Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", "6-pin header 2.54mm"),
            ("Connector_USB:USB_C_Plug_USB2.0-16Pin", "USB-C connector"),
        ],
        "oled": [
            ("Display:OLED-0.91-128x32", "0.91\" OLED - LCSC C124233"),
            ("Display:OLED-0.96-128x64", "0.96\" OLED - LCSC C124233"),
        ],
    }

    if category == "all":
        sections = []
        for cat, items in footprints.items():
            sections.append(f"\n## {cat.title()}\n")
            sections.extend([f"  - `{fp}` - {desc}" for fp, desc in items])

        return f"""# Common KiCad Footprints (LCSC Compatible)

{chr(10).join(sections)}

## Usage

Use these footprint names when adding components:

```
add_component_from_library(
    footprint="Resistor_SMD:R_0805_2012Metric"
)
```

## Notes

- All footprints listed are compatible with JLCPCB/LCSC assembly
- 0805 (2012 metric) is recommended for hand soldering
- 0603 (1608 metric) is common for mass production
- KiCad 9.0+ includes these in the standard library package
"""
    else:
        if category not in footprints:
            return f"❌ Unknown category: {category}\n\nAvailable: {', '.join(footprints.keys())}"

        items = footprints[category]
        return f"""# {category.title()} Footprints

{chr(10).join([f"- `{fp}` - {desc}" for fp, desc in items])}
"""


@mcp.tool()
async def create_project_footprint_lib(
    project_path: str,
    library_name: str,
) -> str:
    """Create a project-specific footprint library folder.

    Args:
        project_path: Path to the KiCad project
        library_name: Name for the footprint library

    Returns:
        Confirmation message with library path
    """
    try:
        project_dir = Path(project_path)

        # Create footprint library folder
        fp_lib_dir = project_dir / "footprints" / f"{library_name}.pretty"
        fp_lib_dir.mkdir(parents=True, exist_ok=True)

        # Create .kicad_mod file (empty placeholder for now)
        readme = fp_lib_dir / "README.md"
        readme.write_text(f"""# {library_name} Footprint Library

Project-specific footprint library for {project_dir.name}.

## Usage

1. Add this library to KiCad:
   - File → Footprint Library Manager
   - Add → Browse to this folder

2. Footprints added here will be available in the footprint selector.
""")

        # Update project file to include this library
        pro_file = list(project_dir.glob("*.kicad_pro"))

        if pro_file:
            pro_path = pro_file[0]

            try:
                with open(pro_path, 'r') as f:
                    pro_data = json.load(f)
            except:
                pro_data = {}

            # Add footprint library path
            if "libraries" not in pro_data:
                pro_data["libraries"] = []

            pro_data["libraries"].append({
                "name": library_name,
                "type": "footprint",
                "path": str(fp_lib_dir.relative_to(project_dir))
            })

            with open(pro_path, 'w') as f:
                json.dump(pro_data, f, indent=2)

            return f"""✅ Created project footprint library!

**Library Name:** {library_name}
**Location:** {fp_lib_dir}
**Project File Updated:** {pro_path.name}

This library is now linked to your project and footprints added here will be available in KiCad.

**Next Steps:**

1. Add footprints to this folder (as .kicad_mod files)
2. Use in schematics with: {library_name}:<footprint_name>
3. Update KiCad's footprint library table to recognize this path
"""
        else:
            return f"""✅ Created footprint library folder!

**Location:** {fp_lib_dir}

Note: No .kicad_pro file found in project directory. You'll need to manually add this library to KiCad:
- Preferences → Footprint Library Manager → Add → Browse to: {fp_lib_dir}
"""

    except Exception as e:
        import traceback
        return f"Error creating footprint library: {e}\n\n{traceback.format_exc()}"
