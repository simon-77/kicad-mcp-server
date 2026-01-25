"""Natural language parser for design specifications.

Supports Chinese and English input like:
- "主控用ESP32S3，添加一个OLED，添加一个IMU，画在一个30*30的PCB中"
- "Use ESP32S3, add OLED and IMU, layout on 30x30mm PCB"
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from ..server import mcp


@dataclass
class DesignSpec:
    """Parsed design specification."""

    # Main controller
    mcu: Optional[str] = None  # e.g., "ESP32S3", "Arduino Nano"

    # Components to add
    components: List[Dict[str, str]] = None

    # PCB specifications
    pcb_width: Optional[float] = None
    pcb_height: Optional[float] = None
    pcb_unit: str = "mm"  # mm or inch

    # Additional requirements
    requirements: List[str] = None

    def __post_init__(self):
        if self.components is None:
            self.components = []
        if self.requirements is None:
            self.requirements = []


# MCU keywords (Chinese and English)
MCU_PATTERNS = {
    # ESP32 family
    r"esp32[-_\s]?s3": "ESP32-S3-WROOM-1",
    r"esp32[-_\s]?s2": "ESP32-S2-WROOM",
    r"esp32[-_\s]?c3": "ESP32-C3",
    r"esp32": "ESP32-WROOM-32",

    # STM32 family
    r"stm32[-_\s]?f103": "STM32F103C8T6",
    r"stm32[-_\s]?f4": "STM32F407",
    r"stm32": "STM32F103C8T6",

    # Arduino
    r"arduino[-_\s]?nano": "Arduino Nano",
    r"arduino[-_\s]?uno": "Arduino Uno",
    r"arduino[-_\s]?mega": "Arduino Mega 2560",
    r"arduino": "Arduino Uno",

    # ESP8266
    r"esp8266": "ESP8266-12E",

    # RP2040
    r"rp2040": "RP2040",
    r"raspberry[-_\s]?pi[-_\s]?pico": "RP2040",

    # ATmega
    r"atmega328[p]?": "ATmega328P",
    r"atmega2560": "ATmega2560",

    # Chinese names
    r"xiao[-_\s]?esp32[-_\s]?s3": "ESP32-S3-WROOM-1",
    r"小esp32[-_\s]?s3": "ESP32-S3-WROOM-1",
}

# Component patterns
COMPONENT_PATTERNS = {
    # Display
    r"oled|ssd1306|显示": {
        "name": "SSD1306",
        "library": "Display",
        "symbol": "SSD1306",
        "footprint": "Display:OLED-0.96-128x64",
        "value": "SSD1306"
    },
    r"lcd|tft": {
        "name": "LCD",
        "library": "Display",
        "symbol": "LCD",
        "footprint": "Display:LCD_1602",
        "value": "LCD1602"
    },

    # Sensors
    r"imu|mpu6050|mpu9250|陀螺仪|加速度计": {
        "name": "MPU6050",
        "library": "Sensor",
        "symbol": "MPU6050",
        "footprint": "Sensor:QFN-24_4x4mm",
        "value": "MPU6050"
    },
    r"bme280|bme680|温湿度|气压": {
        "name": "BME280",
        "library": "Sensor",
        "symbol": "BME280",
        "footprint": "Sensor:BME280",
        "value": "BME280"
    },
    r"dht11|dht22|温湿度传感器": {
        "name": "DHT22",
        "library": "Sensor",
        "symbol": "DHT22",
        "footprint": "Sensor:DHT22",
        "value": "DHT22"
    },

    # LEDs
    r"led|发光": {
        "name": "LED",
        "library": "Device",
        "symbol": "LED",
        "footprint": "LED_SMD:LED_0805_2012Metric",
        "value": "LED"
    },

    # Buttons
    r"button|switch|按键|开关": {
        "name": "Button",
        "library": "Switch",
        "symbol": "SW_Push",
        "footprint": "Button_SMD:Button_Polygon_4.5x4.5mm",
        "value": "Button"
    },

    # Connectors
    r"usb[-_\s]?c|usb[-_\s]?type[-_\s]?c": {
        "name": "USB_C",
        "library": "Connector",
        "symbol": "USB_C_Plug",
        "footprint": "Connector_USB:USB_C_Plug_USB2.0-16Pin",
        "value": "USB_C"
    },

    # Power
    r"battery|电池": {
        "name": "Battery",
        "library": "Device",
        "symbol": "Battery",
        "footprint": "Battery:BatteryHolder_Keystone_1058_1x2032",
        "value": "Battery"
    },

    # Storage
    r"sd[-_\s]?card|tf[-_\s]?card|存储卡": {
        "name": "SD_Card",
        "library": "Connector",
        "symbol": "SD_Card",
        "footprint": "Connector_SD:SD_TE_2002021",
        "value": "SD_Card"
    },
}


def parse_design_spec(text: str) -> DesignSpec:
    """Parse natural language design specification.

    Args:
        text: Design specification in Chinese or English

    Returns:
        DesignSpec with parsed information
    """
    spec = DesignSpec()
    text_lower = text.lower()

    # Detect MCU
    for pattern, mcu in MCU_PATTERNS.items():
        if re.search(pattern, text_lower):
            spec.mcu = mcu
            break

    # Detect components
    for pattern, comp_info in COMPONENT_PATTERNS.items():
        matches = re.findall(pattern, text_lower)
        for _ in matches:
            spec.components.append(comp_info.copy())

    # Detect PCB dimensions
    # Patterns: "30*30", "30x30", "30*30mm", "30mm x 30mm"
    # More specific patterns first (longer matches)
    size_patterns = [
        r'(\d{2,}(?:\.\d+)?)\s*[\*x]\s*(\d{2,}(?:\.\d+)?)\s*(mm|inch)?',  # 30*30, 30x30
        r'(\d+(?:\.\d+)?)\s*[x\*]\s*(\d+(?:\.\d+)?)\s*(mm|inch)?',  # Fallback
    ]

    for pattern in size_patterns:
        match = re.search(pattern, text_lower)
        if match:
            spec.pcb_width = float(match.group(1))
            spec.pcb_height = float(match.group(2))
            if match.lastindex >= 3 and match.group(3):
                spec.pcb_unit = match.group(3)
            break

    # Detect special requirements
    if "wireless" in text_lower or "wifi" in text_lower or "蓝牙" in text_lower:
        spec.requirements.append("wireless")

    if "low power" in text_lower or "低功耗" in text_lower:
        spec.requirements.append("low_power")

    if "small" in text_lower or "compact" in text_lower or "小型" in text_lower:
        spec.requirements.append("compact")

    if "battery" in text_lower or "电池" in text_lower:
        spec.requirements.append("battery_powered")

    return spec


@mcp.tool()
async def parse_design_specification(
    text: str,
) -> str:
    """Parse natural language design specification.

    Supports Chinese and English input for describing electronics projects.

    Examples:
    - "主控用ESP32S3，添加一个OLED，添加一个IMU，画在一个30*30的PCB中"
    - "Use ESP32S3, add OLED and IMU, layout on 30x30mm PCB"
    - "Arduino Nano with LED and button, 50x50mm PCB"
    - "STM32 with temperature sensor and SD card, compact design"

    Extracts:
    - Main controller/MCU type
    - Components to add (displays, sensors, LEDs, etc.)
    - PCB dimensions
    - Special requirements (wireless, low power, compact, etc.)

    Args:
        text: Design specification text (Chinese or English)

    Returns:
        Parsed design specification as structured data
    """
    try:
        spec = parse_design_spec(text)

        # Build response
        lines = []
        lines.append("✅ **Design Specification Parsed**")
        lines.append("")
        lines.append("## 🎯 Main Controller")
        if spec.mcu:
            lines.append(f"- **MCU**: {spec.mcu}")
        else:
            lines.append("- MCU not specified (defaulting to Arduino Uno)")

        lines.append("")
        lines.append("## 📦 Components Detected")

        if spec.components:
            for i, comp in enumerate(spec.components, 1):
                lines.append(f"{i}. **{comp.get('name', 'Unknown')}**")
                lines.append(f"   - Library: {comp.get('library', 'N/A')}")
                lines.append(f"   - Symbol: {comp.get('symbol', 'N/A')}")
                lines.append(f"   - Footprint: {comp.get('footprint', 'N/A')}")
                lines.append(f"   - Value: {comp.get('value', 'N/A')}")
        else:
            lines.append("No components detected")

        lines.append("")
        lines.append("## 📐 PCB Specifications")

        if spec.pcb_width and spec.pcb_height:
            lines.append(f"- **Dimensions**: {spec.pcb_width} x {spec.pcb_height} {spec.pcb_unit}")
            lines.append(f"- **Area**: {spec.pcb_width * spec.pcb_height:.1f} sq {spec.pcb_unit}")
        else:
            lines.append("No PCB dimensions specified (defaulting to 100x100mm)")

        lines.append("")
        lines.append("## ⚙️ Special Requirements")

        if spec.requirements:
            for req in spec.requirements:
                lines.append(f"- ✅ {req}")
        else:
            lines.append("No special requirements detected")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 🚀 Next Steps")
        lines.append("")
        lines.append("To create this project, use the following workflow:")
        lines.append("")

        # Generate suggested commands
        if spec.mcu:
            lines.append(f"1. Create project with {spec.mcu}")
        else:
            lines.append("1. Create project")

        if spec.components:
            lines.append("2. Add components:")
            for comp in spec.components:
                lines.append(f"   - {comp.get('name', 'Unknown')}")

        if spec.pcb_width and spec.pcb_height:
            lines.append(f"3. Set PCB size to {spec.pcb_width}x{spec.pcb_height}{spec.pcb_unit}")
        else:
            lines.append("3. Set PCB size")

        lines.append("4. Route connections")
        lines.append("5. Generate test code")

        return "\n".join(lines)

    except Exception as e:
        import traceback
        return f"Error parsing design specification: {e}\n\n{traceback.format_exc()}"
