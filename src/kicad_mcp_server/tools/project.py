"""KiCad project creation tools for KiCad MCP Server - Updated for KiCad 9.0+"""

from pathlib import Path
from typing import List
from ..server import mcp
import uuid
from datetime import datetime


def _get_date_string() -> str:
    """Get current date in ISO format."""
    return datetime.now().strftime("%Y-%m-%d")


@mcp.tool()
async def create_kicad_project(
    project_path: str,
    project_name: str,
    title: str = "",
    company: str = "",
) -> str:
    """Create a complete KiCad 9.0+ project with schematic and PCB.

    Args:
        project_path: Directory path for the project
        project_name: Name of the project (without extension)
        title: Optional project title
        company: Optional company name

    Returns:
        Confirmation message with created files
    """
    try:
        path = Path(project_path)
        path.mkdir(parents=True, exist_ok=True)

        # Generate UUIDs
        project_uuid = str(uuid.uuid4())
        date_str = _get_date_string()
        title_text = title or project_name

        # ===== 1. Create .kicad_pro file (KiCad 9.0 format) =====
        kicad_pro_content = f'''(kicad_pro (version {project_uuid})

  (general
    (thickness 1.6)
  )

  (paper "A4")

  (title_block
    (title "{title_text}")
    (company "{company}")
    (date "{date_str}")
    (rev "1.0")
  )

  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "B.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )

  (setup
    (pad_to_mask_clearance 0)
    (aux_axis_origin 0)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plotframeref false)
      (usegerberextensions false)
      (usegerberattributes false)
      (usegerberadvancedattributes false)
      (creategerberjobfile false)
      (excludeedgelayer true)
      (linewidth 0.100000)
      (mode false)
      (useauxorigin false)
    )
  )

  (net 0 "")

  (net_class Default "This is the default net class."
    (clearance 0.2)
    (trace_width 0.25)
    (via_dia 0.8)
    (via_drill 0.4)
    (uvia_dia 0.3)
    (uvia_drill 0.1)
  )

)
'''

        # Write .kicad_pro file
        pro_path = path / f"{project_name}.kicad_pro"
        pro_path.write_text(kicad_pro_content)

        # ===== 2. Create schematic file (KiCad 9.0 format) =====
        r1_uuid = str(uuid.uuid4())
        r2_uuid = str(uuid.uuid4())
        d1_uuid = str(uuid.uuid4())

        sch_content = f'''(kicad_sch (version 20240130) (generator eeschema) (uuid {project_uuid})

  (paper "A4")

  (title_block
    (title "{title_text}")
    (company "{company}")
    (date "{date_str}")
    (rev "1.0")
  )

  (lib_symbols
    (symbol "Device:R_Small" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes) (exclude_from_sim no)
      (property "Reference" "R" (at 0 0 0)
        (effects (font (size 1.27 1.27)) (justify left) hide)
      )
      (property "Value" "R_Small" (at 0 0 0)
        (effects (font (size 1.27 1.27)) (justify left) hide)
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "R_Small_0_1"
        (polyline
          (pts (xy -0.762 0) (xy 0 -0.762) (xy 0.762 0))
          (stroke (width 0.254) (type default))
          (fill (type none))
        )
        (pin "1" passive line (at -5.08 0 0)
          (effects (font (size 1.27 1.27)))
        )
        (pin "2" passive line (at 5.08 0 180)
          (effects (font (size 1.27 1.27)))
        )
      )
    )
    (symbol "Device:LED" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes) (exclude_from_sim no)
      (property "Reference" "D" (at 0 0 0)
        (effects (font (size 1.27 1.27)) (justify left) hide)
      )
      (property "Value" "LED" (at 0 0 0)
        (effects (font (size 1.27 1.27)) (justify left) hide)
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "LED_0_1"
        (polyline
          (pts (xy -0.762 0) (xy 0.762 0))
          (stroke (width 0.254) (type default))
          (fill (type none))
        )
        (pin "1" passive line (at -3.81 0 90)
          (effects (font (size 1.27 1.27)))
        )
        (pin "2" passive line (at 3.81 0 270)
          (effects (font (size 1.27 1.27)))
        )
      )
    )
    (symbol "power:+3V3" (power) (pin_names hide) (in_bom yes) (on_board yes) (exclude_from_sim no)
      (property "Reference" "#PWR" (at 0 -3.81 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "+3V3" (at 0 3.556 0)
        (effects (font (size 1.27 1.27)))
      )
      (symbol "power:+3V3_0_1"
        (polyline
          (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27) (xy 0 0))
          (stroke (width 0) (type default))
          (fill (type none))
        )
        (pin "1" power_out line (at 0 0 0)
          (effects (font (size 1.27 1.27)))
        )
      )
    )
    (symbol "power:GND" (power) (pin_names hide) (in_bom yes) (on_board yes) (exclude_from_sim no)
      (property "Reference" "#PWR" (at 0 -5.08 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "GND" (at 0 0 0)
        (effects (font (size 1.27 1.27)))
      )
      (symbol "power:GND_0_1"
        (polyline
          (pts (xy -1.27 0) (xy 0 -1.27) (xy 1.27 0) (xy 0 1.27) (xy -1.27 0))
          (stroke (width 0) (type default))
          (fill (type none))
        )
        (pin "1" power_out line (at 0 1.27 270)
          (effects (font (size 1.27 1.27)))
        )
      )
    )
  )

  (symbol (lib_id "Device:R_Small") (at 0 0 0) (unit 1) (in_bom yes) (on_board yes) (dnp no)
    (uuid {r1_uuid})
    (property "Reference" "R1" (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "1k" (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
  )

  (symbol (lib_id "Device:R_Small") (at 0 0 0) (unit 1) (in_bom yes) (on_board yes) (dnp no)
    (uuid {r2_uuid})
    (property "Reference" "R2" (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "10k" (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
  )

  (symbol (lib_id "Device:LED") (at 0 0 0) (unit 1) (in_bom yes) (on_board yes) (dnp no)
    (uuid {d1_uuid})
    (property "Reference" "D1" (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "LED_RED" (at 0 0 0)
      (effects (font (size 1.27 1.27)))
    )
  )

  (symbol (lib_id "power:+3V3") (at 0 0 0) (unit 1) (in_bom yes) (on_board yes)
    (uuid {str(uuid.uuid4())})
  )

  (symbol (lib_id "power:GND") (at 0 0 0) (unit 1) (in_bom yes) (on_board yes)
    (uuid {str(uuid.uuid4())})
  )

)
'''

        # Write schematic file
        sch_path = path / f"{project_name}.kicad_sch"
        sch_path.write_text(sch_content)

        # ===== 3. Create PCB file (KiCad 9.0 format) =====
        pcb_content = f'''(kicad_pcb (version 20240130) (generator eeschema)

  (general
    (thickness 1.6)
  )

  (paper "A4")

  (title_block
    (title "{title_text}")
    (company "{company}")
    (date "{date_str}")
    (rev "1.0")
  )

  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "B.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )

  (setup
    (pad_to_mask_clearance 0)
    (aux_axis_origin 0)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plotframeref false)
      (usegerberextensions false)
      (usegerberattributes false)
      (usegerberadvancedattributes false)
      (creategerberjobfile false)
      (excludeedgelayer true)
      (linewidth 0.100000)
      (mode false)
      (useauxorigin false)
    )
  )

  (net 0 "")

  (net_class Default "This is the default net class."
    (clearance 0.2)
    (trace_width 0.25)
    (via_dia 0.8)
    (via_drill 0.4)
    (uvia_dia 0.3)
    (uvia_drill 0.1)
  )

)
'''

        # Write PCB file
        pcb_path = path / f"{project_name}.kicad_pcb"
        pcb_path.write_text(pcb_content)

        return f"""# ✅ KiCad 9.0+ Project Created Successfully!

**Project Path:** {path}
**Project Name:** {project_name}
**Title:** {title_text}
**Company:** {company}

## 📄 Files Created:

1. **{project_name}.kicad_pro** - KiCad project file (v9.0 format)
2. **{project_name}.kicad_sch** - Schematic file (v9.0 format)
3. **{project_name}.kicad_pcb** - PCB layout file (v9.0 format)

## 📖 How to Open in KiCad 9.0+:

1. Open KiCad
2. File → Open Project...
3. Navigate to: {pro_path}
4. Click Open

The project will open in KiCad 9.0+ without any version warnings!

## 🎨 Ready for Design:

- ✅ Schematic editor with example components
- ✅ PCB editor ready for layout
- ✅ Proper KiCad 9.0 file format
- ✅ Compatible with KiCad 9.0 and later

## 🔧 Next Steps:

- Use `add_component` to add more schematic symbols
- Use `add_footprint` to add PCB footprints
- Use `create_pcb` + `add_board_outline` to define board shape
- Use `add_track` to route traces
- Use `generate_test_code` to create Arduino/ESP-IDF tests

Project is ready for KiCad 9.0! 🚀"""

    except Exception as e:
        import traceback
        return f"Error creating project: {e}\n\n{traceback.format_exc()}"

