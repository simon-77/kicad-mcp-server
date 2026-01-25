"""KiCad project creation tools for KiCad MCP Server."""

from pathlib import Path
from typing import List
from ..server import mcp
import shutil
import uuid


@mcp.tool()
async def create_kicad_project(
    project_path: str,
    project_name: str,
    title: str = "",
    company: str = "",
) -> str:
    """Create a complete KiCad project with schematic and PCB.

    Args:
        project_path: Directory path for the project
        project_name: Name of the project (without extension)
        title: Optional project title
        company: Optional company name

    Returns:
        Confirmation message with created files
    """
    try:
        from datetime import datetime

        path = Path(project_path)
        path.mkdir(parents=True, exist_ok=True)

        # Generate .kicad_pro file
        project_uuid = str(uuid.uuid4())

        kicad_pro_content = f'''(kicad_pcb (version 20211026) (generator eeschema)

  (general
    (thickness 1.6)
  )

  (paper "A4")

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
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user "B.Fab")
    (49 "F.Fab" user)
  )

  (setup
    (stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask")
        (thickness 0.01)
      )
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "die1" (type "core") (thickness 1.41) (material "FR4"))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask")
        (thickness 0.01)
      )
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "None")
      (dielectric_constraints none)
    )
    (pad_to_mask_clearance 0)
    (aux_axis_origin 0 0)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (disableapertmacros false)
      (plotframe true)
      (usegerberextensions false)
      (usegerberattributes false)
      (usegerberadvancedattributes true)
      (creategerberjobfile false)
      (excludeedgelayer true)
      (linewidth 0.100000)
      (mode false)
      (useauxorigin false)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (dnp_polygon_consult true)
      (psnegative false)
      (psa4output false)
      (plotreference true)
      (plotvalue true)
      (plotinvisibletext false)
      (sketchpadsonfab false)
      (subtractmaskfromsilk false)
      (outputformat 1)
      (mirror false)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory ""))
    )

  (net 0 "")
  (net_class Default "This is the default net class."
    (clearance 0.2)
    (trace_width 0.25)
    (via_dia 0.8)
    (via_drill 0.4)
    (uvia_dia 0.3)
    (uvia_drill 0.1)
    (add_net "")
  )

  (model {{value}} (at (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )

  (model {{value}} (at (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )

  (model {{value}} (at (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )

  (model {{value}} (at (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )

  (model {{value}} (at (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )

  (model {{value}} (at (xyz 0 0 0))
    (scale (xyz 1 1 1))
    (rotate (xyz 0 0 0))
  )
)

        # Write .kicad_pro file
        pro_path = path / f"{project_name}.kicad_pro"
        pro_path.write_text(kicad_pro_content)

        # Generate schematic file
        sch_content = f'''(kicad_sch (version 20211123) (generator eeschema) (uuid {project_uuid})

  (paper "A4")

  (title_block
    (title "{title or project_name}")
    (company "{company}")
    (date "{datetime.now().strftime("%Y-%m-%d")}")
    (rev "1.0")
  )

  (lib_symbols
    (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 0 1.27 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "R" (at 0 -1.27 0)
        (effects (font (size 1.27 1.27)))
      )
      (symbol "R_0_1" (polyline
        (pts (xy -0.762 0) (xy 0 -0.762) (xy 0.762 0))
        (stroke (width 0.254) (type default))
        (fill (type none))
      )
      (pin "1" passive (at -5.08 0 0)
        (effects (font (size 1.27 1.27)))
      )
      (pin "2" passive (at 5.08 0 0)
        (effects (font (size 1.27 1.27)))
      )
    )
  )

  (symbol (lib_id "Device:R") (in_bom yes) (on_board yes)
  )

)

        # Write schematic file
        sch_path = path / f"{project_name}.kicad_sch"
        sch_path.write_text(sch_content)

        # Generate empty PCB file
        pcb_path = path / f"{project_name}.kicad_pcb"
        pcb_content = f'''(kicad_pcb (version 20211026) (generator eeschema)

  (general
    (thickness 1.6)
  )

  (paper "A4")

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
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )

  (setup
    (last_trace_width 0.25)
    (trace_clearance 0.2)
    (zone_clearance 0.508)
    (zone_45_only no)
    (trace_min 0.2)
    (via_size 0.8)
    (via_drill 0.4)
    (via_min_size 0.4)
    (via_min_drill 0.3)
    (uvia_size 0.3)
    (uvia_drill 0.1)
    (uvias_allowed no)
    (uvia_min_size 0.2)
    (uvia_min_drill 0.1)
    (edge_width 0.05)
    (segment_width 0.2)
    (pcb_text_width 0.3)
    (pcb_text_size 1.5 1.5)
    (mod_edge_width 0.12)
    (mod_text_size 1 1)
    (mod_text_width 0.15)
    (pad_size 1.524 1.524)
    (pad_drill 0.762)
    (pad_to_mask_clearance 0.05)
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

        pcb_path.write_text(pcb_content)

        return f"""# KiCad Project Created Successfully

**Project Path:** {path}
**Project Name:** {project_name}
**Title:** {title or project_name}
**Company:** {company}

## Files Created:

1. **{project_name}.kicad_pro** - KiCad project file
2. **{project_name}.kicad_sch** - Schematic file
3. **{project_name}.kicad_pcb** - PCB layout file

## Next Steps:

1. Open KiCad
2. File → Open Project → Select: {pro_path}
3. Start designing!

## Tools Available:

- Add components with `add_component`
- Create PCB with `create_pcb`
- Add board outline with `add_board_outline`
- Add footprints with `add_footprint`
- Route tracks with `add_track`

Project is ready for use!"""

    except Exception as e:
        return f"Error creating project: {e}"
