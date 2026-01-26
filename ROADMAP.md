# kicad-mcp-server 改进计划

## 已完成
- ✅ PCB 解析器：使用 KiCad 官方 API (pcbnew)
- ✅ 原理图解析器：修复坐标和引脚提取
- ✅ 组件属性解析
- ✅ **网络连接跟踪**：通过解析 wire 和 junction 实现真实网络追踪

## 网络连接跟踪实现细节

### 已实现功能
```python
def build_wire_network(self) -> dict:
    """构建导线连接图"""
    # 1. 解析所有 wire 段
    # 2. 解析 junction 合并连接
    # 3. 返回连接图

def trace_wire_network(self, reference: str) -> dict:
    """追踪组件的导线连接"""
    # 1. 获取组件位置
    # 2. 从最近的导线端点开始
    # 3. BFS 遍历导线网络
    # 4. 找到连接的标签
    # 5. 返回连接列表
```

### 实测结果（reSpeaker Lav 项目）
```python
# R16 网络追踪
r16_trace = parser.trace_wire_network('R16')
# 结果：R16 → PMIC_I2C_SDA (0.00mm, 直连)
# 电路作用：4.7K 上拉电阻，上拉 PMIC_I2C_SDA 信号

# R19 网络追踪
r19_trace = parser.trace_wire_network('R19')
# 结果：R19 → PMIC_I2C_SCL (0.00mm, 直连)
# 电路作用：4.7K 上拉电阻，上拉 PMIC_I2C_SCL 信号
```

### 新增 MCP 工具
在 `net_tracking.py` 中新增了 3 个工具：
1. `trace_component_connections()` - 追踪组件的所有网络连接
2. `trace_signal_path()` - 从组件开始追踪信号路径
3. `analyze_nets_by_area()` - 分析特定区域内的所有网络和组件

## 待完成
