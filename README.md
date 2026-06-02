# Autofeeder Controller

PCB replacement for a timed chicken feed dispenser. Modern ESP32-based controller with Matter/ESPHome support, motor control, and CAN bus integration.

## Features
- **MCU**: ESP32-C6 (Matter, WiFi 6, Thread, BLE 5)
- **Display**: SSD1306 128×64 SPI OLED
- **Motor**: DRV8871 H-bridge for 4VDC auger motor
- **Power**: 18650 Li-ion with TP4056 charger + TPS63802 buck-boost
- **CAN Bus**: SN65HVD230 via USB-C SBU pins (home automation bus)
- **USB-C**: 5V charging + CAN sideband on SBU pins

## Project Structure
```
hardware/          — KiCad design files
  ├── autofeedermod.kicad_pro
  ├── autofeedermod.kicad_sch
  ├── autofeedermod.kicad_pcb
  ├── symbols/      — Custom schematic symbols
  ├── footprints/   — Custom footprints
  └── 3d-models/    — Step files
firmware/esphome/   — ESPHome configuration
docs/               — BOM, pinout, design notes
```

## Status
KiCad project initialized — schematic capture in progress.

## License
CERN Open Hardware Licence Version 2 - Weakly Reciprocal (CERN-OHL-W-2.0)
