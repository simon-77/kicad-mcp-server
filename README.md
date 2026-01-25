# KiCad MCP Server

**Natural Language-Driven KiCad 9.0 Design Tool**

A Model Context Protocol (MCP) server for KiCad EDA software that enables natural language interaction for schematic and PCB design, analysis, and test code generation.

## Core Features

### 🎯 Natural Language Design
Generate complete schematics and PCBs through natural language descriptions:

```
"Use XiaoESP32S3 as main controller, add an OLED display and IMU sensor,
layout on a 30x30mm PCB"
```

The system automatically:
- ✅ Selects appropriate MCU symbols and footprints
- ✅ Adds peripherals (OLED, IMU, etc.)
- ✅ Auto-connects I2C/SPI buses
- ✅ Layouts on specified PCB dimensions
- ✅ Selects footprints from LCSC (LiCheng Mall)

### 📊 KiCad Project Analysis
Intelligently analyze existing KiCad projects:
- 📝 Generate schematic summaries (components, peripherals, connections)
- 🔍 Analyze pin configurations and peripheral setups
- 📈 Generate connection diagrams and topology
- ⚡ Identify power distribution and critical signals

### 🧪 Automated Test Code Generation
Generate test code based on schematics:
- **Arduino** - ESP32/ESP8266/AVR
- **ESP-IDF** - Official ESP32 framework
- **Zephyr RTOS** - Embedded operating system
- **STM32 HAL** - STM32 official library
- **pytest** - Python testing framework

### 🔌 LCSC Integration
- Search for components on LCSC (LiCheng Mall)
- Match PCB footprints
- Generate BOMs with pricing and purchase links

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/kicad-mcp-server.git
cd kicad-mcp-server

# Install dependencies
pip install -e .

# Configure environment (optional)
cp .env.example .env
# Edit .env to set KiCad paths
```

### System Requirements

- **Python**: 3.10 or higher
- **KiCad**: 9.0 or later
- **OS**: macOS / Linux / Windows

## Usage

### 1. Start the MCP Server

```bash
# Method 1: Direct execution
python -m kicad_mcp_server

# Method 2: Via installed command
kicad-mcp-server
```

### 2. Configure in Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kicad": {
      "command": "python",
      "args": ["-m", "kicad_mcp_server"],
      "env": {
        "KICAD_PATH": "/Applications/KiCad/KiCad.app"
      }
    }
  }
}
```

### 3. Natural Language Design Examples

#### Example 1: ESP32S3 Development Board

```
User: "Create an ESP32S3 development board with:
- XiaoESP32S3 main controller
- 0.96" OLED display (I2C)
- MPU6050 IMU sensor (I2C)
- PCB size: 30x30mm
- USB Type-C connector"

The system will:
1. Automatically create KiCad project
2. Add ESP32S3 symbol (select correct footprint)
3. Add SSD1306 OLED (I2C to GPIO6/7)
4. Add MPU6050 (I2C to GPIO6/7)
5. Add USB-C connector
6. Generate PCB layout (30x30mm)
7. Select available footprints from LCSC
```

#### Example 2: nRF52840 Sensor Node

```
User: "Design an nRF52840 Bluetooth sensor node:
- nRF52840 main chip
- BME280 temperature & humidity sensor
- 3.7V Li-Po battery power
- Charging circuit
- PCB size: 25x25mm"

System automatically:
1. Select QFN-40 packaged nRF52840
2. Add BME280 (I2C interface)
3. Add TP4056 charging IC
4. Add battery connector
5. Generate complete PCB layout
```

### 4. Analyze Existing Projects

```
User: "Analyze /path/to/project.kicad_pro"

System outputs:
# KiCad Project Analysis Report

## Project Information
- Name: ESP32 Dev Board
- Date: 2024-01-15
- Revision: 1.0

## Main Controller
- **U1**: ESP32-S3-WROOM-1 (QFN package)
  - Flash: 16MB
  - RAM: 512KB
  - Main power: 3.3V

## Peripherals List

### Display
- **U2**: SSD1306 OLED (128x64)
  - Interface: I2C
  - SDA: GPIO6
  - SCL: GPIO7
  - Address: 0x3C

### Sensor
- **U3**: MPU6050 (6-axis IMU)
  - Interface: I2C
  - SDA: GPIO6
  - SCL: GPIO7
  - Interrupt: GPIO8

### Storage
- **U4**: W25Q128 (16MB Flash)
  - Interface: SPI
  - CS: GPIO10
  - CLK: GPIO11
  MOSI: GPIO12
  MISO: GPIO13

## Connection Diagram
```
ESP32S3 <--I2C--> SSD1306 OLED
      |
      +--I2C--> MPU6050 IMU
      |
      +--SPI--> W25Q128 Flash
```

## Test Code
[Automatically generate Arduino test code...]
```

### 5. Generate Test Code

```
User: "Generate Arduino test code for this ESP32S3 project"

System automatically generates:
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_MPU6050.h>

// I2C configuration
#define I2C_SDA 6
#define I2C_SCL 7

// OLED display
Adafruit_SSD1306 display(128, 64, &Wire, -1);

// IMU sensor
Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(115200);
  Wire.begin(I2C_SDA, I2C_SCL);

  // Initialize OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 allocation failed");
  }
  display.display();

  // Initialize MPU6050
  if(!mpu.begin()) {
    Serial.println("MPU6050 not found");
  }
}

void loop() {
  // Read sensor data
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Display on OLED
  display.clearDisplay();
  display.setCursor(0,0);
  display.printf("X: %.2f Y: %.2f Z: %.2f", a.acceleration.x,
                                               a.acceleration.y,
                                               a.acceleration.z);
  display.display();

  delay(100);
}
```

## Available Tools

### Project Creation Tools
- `create_kicad_project` - Create new project
- `add_component_from_library` - Add components
- `add_wire` - Add wires
- `add_global_label` - Add global labels

### Analysis Tools
- `summarize_schematic` - Generate schematic summary
- `list_schematic_components` - List all components
- `analyze_schematic_nets` - Analyze net connections
- `generate_connection_diagram` - Generate connection diagram

### Test Code Generation
- `generate_test_code` - Generate test code
- `generate_esp32s3_arduino_test` - ESP32 Arduino tests
- `generate_bom` - Generate bill of materials

### Component Library Tools
- `list_common_footprints` - List common footprints
- `search_kicad_footprints` - Search footprints
- `download_footprint_library` - Download footprint libraries

### Design Rule Checking
- `run_basic_erc` - Electrical rules check
- `run_basic_drc` - Design rules check

## Configuration

Create a `.env` file:

```bash
# KiCad installation path
KICAD_PATH=/Applications/KiCad/KiCad.app

# Project search paths (optional, comma-separated)
KICAD_PROJECT_PATHS=/Users/username/KiCadProjects

# Default settings
DEFAULT_SUMMARY_DETAIL_LEVEL=standard
DEFAULT_TEST_FRAMEWORK=arduino
```

## Project Structure

```
kicad-mcp-server/
├── src/kicad_mcp_server/
│   ├── tools/              # MCP tool implementations
│   │   ├── project.py      # Project creation (template-based)
│   │   ├── schematic_editor.py  # Schematic editing
│   │   ├── footprint_library.py # Footprint library management
│   │   ├── summary.py      # Project analysis
│   │   ├── testgen.py      # Test code generation
│   │   ├── schematic.py    # Schematic analysis
│   │   └── pcb.py          # PCB analysis
│   ├── parsers/            # KiCad file parsers
│   ├── templates/          # Test code templates
│   │   ├── arduino/
│   │   ├── esp_idf/
│   │   ├── zephyr/
│   │   └── stm32hal/
│   └── server.py           # MCP server
├── tests/                  # Test files
└── README.md
```

## Technical Architecture

### KiCad 9.0 Compatibility
- Uses KiCad official templates as project base
- Supports `.kicad_pro` (JSON format)
- Supports `.kicad_sch` (S-expression format)
- Version: 20240130+

### File Formats
- **Project file**: `.kicad_pro` (JSON)
- **Schematic**: `.kicad_sch` (S-expression)
- **PCB**: `.kicad_pcb` (S-expression)

### Natural Language Processing
- Rule-based design intent recognition
- Supports Chinese and English input
- Intelligent pin connection inference

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check --fix src tests
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

## License

MIT License

## Resources

- [KiCad Official](https://www.kicad.org/)
- [LCSC Mall](https://www.lcsc.com/)
- [KiCad 9.0 Documentation](https://docs.kicad.org/)
- [MCP Protocol](https://modelcontextprotocol.io/)

## Roadmap

- [x] Basic project creation
- [x] Schematic analysis
- [x] Test code generation
- [ ] AI-assisted PCB layout
- [ ] Auto-routing
- [ ] 3D model generation
- [ ] Real-time price estimation
- [ ] Component supply chain queries
