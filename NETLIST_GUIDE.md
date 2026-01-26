# 网表（Netlist）功能使用指南

## 为什么使用网表？

网表文件包含**精确的组件连接关系**，比解析导线和电源符号更可靠：

### 网表的优势
- ✅ **精确的引脚到网络映射**：每个组件的每个引脚连接到哪个网络
- ✅ **完整的网络列表**：所有网络及其连接的组件
- ✅ **KiCad官方格式**：由KiCad导出，100%准确
- ✅ **双向查询**：
  - 给定组件 → 查找所有连接的网络
  - 给定网络 → 查找所有连接的组件

### 与导线追踪的对比

| 方法 | 优点 | 缺点 |
|------|------|------|
| **网表解析** | 100%准确，包含所有连接 | 需要先导出网表 |
| **导线追踪** | 直接从原理图读取 | 可能遗漏隐式连接，依赖距离推断 |
| **电源符号推断** | 能找到电源连接 | 不够精确，基于位置猜测 |

## 使用方法

### 方法1: KiCad GUI 导出网表（推荐）

1. 打开 KiCad Schematic Editor
2. 打开原理图文件（例如 `Power.kicad_sch`）
3. 菜单：**Tools → Generate Netlist**
4. 选择格式：**KiCad XML**
5. 保存为：`Power.xml`（与原理图同目录）

### 方法2: 命令行导出

```bash
eeschema export netlist --format kicadxml Power.kicad_sch Power.xml
```

### 方法3: 使用 MCP 工具生成

```python
# 通过 MCP 服务
generate_netlist("path/to/Power.kicad_sch")
```

## 网表解析工具

### 1. trace_netlist_connection() - 追踪组件连接

**查询 R16 的所有网络连接：**
```python
trace_netlist_connection(
    netlist_path="Power.xml",
    reference="R16"
)
```

**查询 R16 引脚1的具体连接：**
```python
trace_netlist_connection(
    netlist_path="Power.xml",
    reference="R16",
    pin_number="1"
)
```

**返回结果：**
```markdown
## Netlist Connection Trace: R16

**Pin:** 1
**Net:** PMIC_I2C_SDA

### Connected Components:
| Reference | Pin |
|-----------|-----|
| U6        | 24  |
| R19       | 2   |
```

### 2. get_netlist_nets() - 列出所有网络

**列出所有网络：**
```python
get_netlist_nets(netlist_path="Power.xml")
```

**过滤 I2C 相关网络：**
```python
get_netlist_nets(
    netlist_path="Power.xml",
    filter_pattern="I2C"
)
```

### 3. get_netlist_components() - 列出所有组件

**列出所有组件及其网络：**
```python
get_netlist_components(netlist_path="Power.xml")
```

**只列出电阻（R开头）：**
```python
get_netlist_components(
    netlist_path="Power.xml",
    filter_ref="R"
)
```

## 实际使用案例

### 案例1: 分析 I2C 总线

```python
# 1. 导出网表
generate_netlist("Power.kicad_sch")

# 2. 查找 PMIC_I2C_SCL 网络上的所有组件
get_netlist_nets(
    netlist_path="Power.xml",
    filter_pattern="PMIC_I2C_SCL"
)

# 3. 查看R19（SCL上拉电阻）的连接
trace_netlist_connection(
    netlist_path="Power.xml",
    reference="R19"
)
```

### 案例2: 分析电源树

```python
# 查找所有 +3V0 网络的连接
get_netlist_nets(
    netlist_path="Power.xml",
    filter_pattern="+3V0"
)

# 这会显示所有连接到 +3V0 的组件和引脚
```

### 案例3: 追踪特定信号

```python
# 追踪 SHPHLD 信号
get_netlist_nets(
    netlist_path="Power.xml",
    filter_pattern="SHPHLD"
)
```

## 网表文件格式

KiCad XML 网表示例：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<export version="D">
  <design>
    <source>C:\Projects\Power.kicad_sch</source>
    <date>2026-01-26 17:45:00</date>
    <tool>Eeschema 9.0</tool>
  </design>
  <components>
    <component ref="R16">
      <value>4.7K</value>
      <footprint>Resistor:R0201</footprint>
      <libsource lib="Resistors" part="RE20147K00"/>
      <pins>
        <pin num="1" net="3"/>
        <pin num="2" net="1"/>
      </pins>
    </component>
  </components>
  <nets>
    <net code="1" name="+3V0">
      <node ref="R16" pin="2"/>
      <node ref="R19" pin="2"/>
      <node ref="U6" pin="15"/>
    </net>
    <net code="3" name="PMIC_I2C_SDA">
      <node ref="R16" pin="1"/>
      <node ref="U6" pin="24"/>
    </net>
  </nets>
</export>
```

## Python API 使用

```python
from kicad_mcp_server.parsers.netlist_parser import NetlistParser

# 解析网表
parser = NetlistParser("Power.xml")

# 获取所有组件
components = parser.get_components()
for ref, comp in components.items():
    print(f"{ref}: {comp.value}")
    for pin, net in comp.pins.items():
        print(f"  Pin {pin} -> {net}")

# 获取所有网络
nets = parser.get_nets()
for net_name, net in nets.items():
    print(f"{net_name}:")
    for ref, pin in net.pins:
        print(f"  {ref} pin {pin}")

# 追踪特定组件的连接
connections = parser.get_component_nets("R16")
print(f"R16 连接到 {len(connections)} 个网络")

# 查找特定网络上的所有组件
components_on_net = parser.get_net_components("PMIC_I2C_SDA")
print(f"PMIC_I2C_SDA 上有 {len(components_on_net)} 个组件")
```

## 故障排除

### 问题: "Netlist file not found"

**解决**:
1. 检查文件路径是否正确
2. 确认已经导出网表文件（.xml）
3. 查看文件扩展名是否是 `.xml` 而不是 `.net`

### 问题: "Component not found in netlist"

**解决**:
1. 确认组件参考（Reference）正确
2. 检查网表文件是否是最新的
3. 重新导出网表

### 问题: 网络连接看起来不完整

**解决**:
1. 确认原理图中已经运行了 Electrical Rules Check (ERC)
2. 重新保存原理图
3. 重新导出网表

## 总结

**推荐工作流程：**
1. ✅ 在 KiCad 中完成原理图设计
2. ✅ 运行 ERC 检查错误
3. ✅ 导出 KiCad XML 网表
4. ✅ 使用网表工具分析连接关系

**这样可以获得最准确的连接信息！**
