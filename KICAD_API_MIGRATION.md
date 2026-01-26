# KiCad MCP Server - API 迁移完成总结

## ✅ 已完成：PCB 解析器（使用 KiCad 官方 API）

### 新文件：`src/kicad_mcp_server/parsers/pcb_parser_kicad.py`

```python
from kicad_mcp_server.parsers.pcb_parser_kicad import PCBParserKiCad

# 使用 KiCad 官方 Python API (pcbnew)
parser = PCBParserKiCad('project.kicad_pcb')

# 获取封装
footprints = parser.get_footprints()

# 获取网络
nets = parser.get_nets()

# 查找特定封装
u6 = parser.get_footprint_by_reference('U6')
print(f"{u6.reference}: {u6.value} at {u6.position}")
```

### 测试结果

```
✓ Total footprints: 165
✓ nPM1300 PMIC (U6): Position: (148.40, 114.22) mm
✓ Q2 MOSFET: Position: (149.38, 116.28) mm
✓ Total nets: 151
```

**关键优势**：
- ✅ 使用 `pcbnew`（KiCad 官方 Python API）
- ✅ 无需脆弱的正则表达式
- ✅ 直接访问数据结构
- ✅ 与 KiCad 文件格式 100% 兼容

---

## ⚠️ 原理图解析器限制

### 为什么 KiCad 9.0 没有原理图 Python API？

| 组件 | Python API | 原因 |
|------|------------|------|
| **PCB 编辑器** | ✅ 完整支持 | `pcbnew` 模块，有 SWIG Python 绑定 |
| **原理图编辑器** | ❌ **不支持** | KiCad 9.0 未实现 Python API |

查看 KiCad 源码：
- `pcbnew/python/` - ✅ Python 绑定
- `eeschema/` - ❌ 无 Python 绑定

### 当前解决方案

**改进的 S-expression 解析器**（`src/kicad_mcp_server/parsers/schematic_parser.py`）
- ✅ 修复了坐标解析（之前返回 0, 0）
- ✅ 修复了引脚提取
- ✅ 改进了网络解析
- ✅ 测试通过：Q2 位置 (119.38, 167.64)

### 未来方案（KiCad 10+）

KiCad 开发团队正在开发原理图 Python API，可能在 KiCad 10 实现。

---

## 使用示例

### 1. PCB 解析（使用 KiCad API）

```python
from kicad_mcp_server.parsers.pcb_parser_kicad import PCBParserKiCad

parser = PCBParserKiCad('project.kicad_pcb')

# 获取所有封装
for fp in parser.get_footprints():
    print(f"{fp.reference}: {fp.value}")
    print(f"  Position: {fp.position} mm")
    print(f"  Rotation: {fp.rotation}°")
    print(f"  Pads: {fp.pads_count}")

# 获取网络信息
for net in parser.get_nets():
    print(f"{net.name}: code {net.code}")

# 获取板子信息
info = parser.get_board_info()
print(f"Footprints: {info['footprints_count']}")
print(f"Nets: {info['nets_count']}")
```

### 2. 原理图解析（使用改进的解析器）

```python
from kicad_mcp_server.parsers.schematic_parser import SchematicParser

parser = SchematicParser('project.kicad_sch')

# 获取组件
components = parser.get_components()
q2 = parser.get_component_by_reference('Q2')
print(f"Q2: {q2.value} at {q2.position}")

# 获取网络
nets = parser.get_nets()

# 获取标题信息
title = parser.get_title_block()
print(f"Project: {title['title']}")
```

---

## 迁移建议

### 对于 PCB 操作
**必须**使用 `PCBParserKiCad`：
```python
from kicad_mcp_server.parsers.pcb_parser_kicad import PCBParserKiCad
parser = PCBParserKiCad('file.kicad_pcb')
```

### 对于原理图操作
**当前**使用 `SchematicParser`：
```python
from kicad_mcp_server.parsers.schematic_parser import SchematicParser
parser = SchematicParser('file.kicad_sch')
```

**注意**：这仍然使用 S-expression 解析，因为 KiCad 9.0 没有提供原理图 Python API。

---

## 技术细节

### pcbnew API 调用示例

```python
import pcbnew

# 加载 PCB
board = pcbnew.LoadBoard('project.kicad_pcb')

# 获取封装
footprints = board.GetFootprints()
for fp in footprints:
    ref = fp.GetReference()
    val = fp.GetValue()
    pos = fp.GetPosition()  # KiCad 内部单位
    pos_mm = (pos[0] / 1e6, pos[1] / 1e6)  # 转换为 mm

# 获取网络
net_info = board.GetNetInfo()
nets_dict = net_info.NetsByName()
for name, net in nets_dict.items():
    code = net.GetNetCode()
```

---

## 总结

| 功能 | 实现方式 | API 类型 |
|------|---------|----------|
| PCB 解析 | `pcb_parser_kicad.py` | ✅ KiCad 官方 API |
| 原理图解析 | `schematic_parser.py` | ⚠️ S-expression 解析（KiCad 无 API） |

**重要**：这不是我们不想用 KiCad API，而是 **KiCad 9.0 根本没有提供原理图的 Python API**！

当 KiCad 10 发布原理图 API 后，我们可以立即迁移。
