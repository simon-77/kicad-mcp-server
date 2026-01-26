# kicad-mcp-server - 简化版 KiCad MCP Server

**专注核心功能：分析 + 编辑 KiCad 项目**

## 🎯 核心功能（3类6个工具）

### 📊 分析类（3个工具）

#### 1. **schematic** - 原理图分析
列出、查询、分析 KiCad 原理图文件

**工具列表**：
- `list_schematic_components()` - 列出所有组件
- `list_schematic_nets()` - 列出所有网络
- `get_schematic_info()` - 获取原理图信息
- `search_symbols()` - 搜索组件
- `get_symbol_details()` - 获取组件详情
- `analyze_functional_blocks()` - 分析功能模块

**使用场景**：
```python
# 查找所有电阻
list_schematic_components("Power.kicad_sch", filter_type="R")

# 列出所有网络
list_schematic_nets("Power.kicad_sch")
```

#### 2. **pcb** - PCB 分析
分析 KiCad PCB 文件（使用官方 pcbnew API）

**工具列表**：
- `list_pcb_footprints()` - 列出所有封装
- `get_pcb_statistics()` - 获取 PCB 统计信息
- `find_tracks_by_net()` - 查找网络的走线
- `get_footprint_by_reference()` - 获取封装详情
- `analyze_pcb_nets()` - 分析 PCB 网络

**使用场景**：
```python
# 查找 U6 封装
get_footprint_by_reference("reSpeaker Lav.kicad_pcb", "U6")

# 获取 PCB 统计
get_pcb_statistics("reSpeaker Lav.kicad_pcb")
```

#### 3. **netlist** - 网表分析（⭐ 最准确的连接追踪）
解析 KiCad XML 网表文件，提供 100% 准确的引脚级连接

**工具列表**：
- `trace_netlist_connection()` - 追踪组件的网络连接
- `get_netlist_nets()` - 列出所有网络
- `get_netlist_components()` - 列出所有组件及其网络
- `generate_netlist()` - 从原理图导出网表

**使用场景**：
```python
# 追踪 Q3 的所有连接（100% 准确）
trace_netlist_connection("Power.net.xml", "Q3")

# 查看 I2C 网络
get_netlist_nets("Power.net.xml", filter_pattern="I2C")
```

**为什么网表最准确？**
- ✅ KiCad 官方格式
- ✅ 引脚级精度
- ✅ 包含所有连接（显式 + 隐式）
- ✅ 双向查询（组件↔网络）

### ✏️ 编辑类（2个工具）

#### 4. **schematic_editor** - 原理图编辑
创建和修改 KiCad 原理图

**工具列表**：
- `create_kicad_project()` - 创建新项目
- `add_component_from_library()` - 添加组件
- `add_wire()` - 添加连线
- `add_global_label()` - 添加全局标签
- `add_label()` - 添加本地标签
- `setup_pcb_layout()` - 初始化 PCB 布局

**使用场景**：
```python
# 添加电阻
add_component_from_library(
    "Power.kicad_sch",
    library_name="Device",
    symbol_name="R",
    reference="R16",
    value="4.7K",
    x=150,
    y=200
)
```

#### 5. **pcb_layout** - PCB 布局
PCB 布局和编辑功能

**工具列表**：
- `setup_pcb_layout()` - 初始化 PCB
- `add_footprint()` - 添加封装
- `add_track()` - 添加走线
- `add_zone()` - 添加铺铜区域
- `export_gerber()` - 导出 Gerber 文件

**使用场景**：
```python
# 创建 100x100mm PCB
setup_pcb_layout("Power.kicad_sch", width=100, height=100)

# 导出生产文件
export_gerber("reSpeaker Lav.kicad_pcb")
```

### 🏗️ 创建类（1个工具）

#### 6. **project** - 项目管理
KiCad 项目创建和管理

**工具列表**：
- `create_kicad_project()` - 创建新项目
- `copy_kicad_project()` - 复制现有项目

**使用场景**：
```python
# 创建新项目
create_kicad_project(
    path="/path/to/project",
    name="MyProject",
    title="My Project",
    company="My Company"
)
```

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/LynnL4/kicad-mcp-server.git
cd kicad-mcp-server

# 安装依赖（如果需要）
pip install -r requirements.txt
```

## ⚙️ 配置 Claude Desktop

将以下内容添加到 Claude Desktop 配置文件（`~/.claude.json` 或 `%APPDATA%\Claude\claude_desktop_config.json`）：

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

## 🚀 快速开始

### 1. 分析原理图

```bash
# 列出所有组件
mcp: list_schematic_components("Power.kicad_sch", filter_type="R")

# 查看原理图摘要
mcp: get_schematic_info("Power.kicad_sch")
```

### 2. 使用网表追踪连接（推荐）

```bash
# 导出网表
kicad-cli sch export netlist --format kicadxml \
  --output Power.net.xml Power.kicad_sch

# 追踪组件连接
mcp: trace_netlist_connection("Power.net.xml", "Q3")

# 查看所有 I2C 网络
mcp: get_netlist_nets("Power.net.xml", filter_pattern="I2C")
```

### 3. 分析 PCB

```bash
# 获取 PCB 统计
mcp: get_pcb_statistics("reSpeaker Lav.kicad_pcb")

# 列出所有封装
mcp: list_pcb_footprints("reSpeaker Lav.kicad_pcb")
```

### 4. 编辑原理图

```bash
# 创建新项目
mcp: create_kicad_project(
    path="/projects/MyDesign",
    name="MyDesign",
    title="My Design"
)

# 添加组件
mcp: add_component_from_library(
    "Power.kicad_sch",
    "Device",
    "R",
    "R16",
    "4.7K",
    150,
    200
)
```

## 📚 文档

- **NETLIST_GUIDE.md** - 网表使用完整指南
- **KICAD_API_MIGRATION.md** - KiCad API 迁移文档
- **ROADMAP.md** - 项目路线图

## 🎯 设计理念

**专注核心，少即是多：**
- ✅ 只做 3 件事：**分析 + 编辑 + 管理**
- ✅ 网表分析提供 100% 准确的连接追踪
- ✅ 使用 KiCad 官方 API（pcbnew）
- ✅ 简化代码，易于维护

**不做：**
- ❌ 测试代码生成（不是你的需求）
- ❌ 复杂的导线追踪（网表更准确）
- ❌ 冗余的组件查询（合并到分析工具）

## 📊 优化成果

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| 工具数量 | 10 | 6 | ↓ 40% |
| 代码行数 | ~3500 | ~2250 | ↓ 36% |
| 功能聚焦 | 分散 | 核心 | ✅ |
| 维护成本 | 高 | 低 | ✅ |

## 🔗 相关资源

- [KiCad 官方文档](https://docs.kicad.org/)
- [KiCad 9.0 文件格式](https://dev-docs.kicad.org/en/file-formats/)
- [MCP 协议规范](https://modelcontextprotocol.io/)

## 📝 许可证

MIT License

---

**简单、专注、强大** - 这就是 kicad-mcp-server v2.0！
