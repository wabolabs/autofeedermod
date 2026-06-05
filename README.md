# Autofeeder Controller

Drop-in PCB replacement for a timed chicken feed dispenser. ESP32-C6 based with Matter/ESPHome, local standalone operation, motor control, CAN bus, RTC timekeeping, and optional GPS sync.

## Features

- **MCU**: ESP32-C6-Zero (Matter, WiFi 6, Thread, BLE 5) — socketed via 2×9 2.54mm headers + 7 pogo pins
- **Display**: SSD1306 128×64 SPI OLED with full menu system (status, schedules, settings, GPS, manual feed)
- **Motor**: DRV8871 H-bridge for 4VDC auger motor
- **Power**: 18650 Li-ion with TP4056 charger + TPS63031 buck-boost to 3.3V
- **RTC**: DS3231 module (I2C) with CR2032 backup for offline timekeeping
- **GPS**: NEO-6M/8M module header (UART) for offline RTC time sync
- **CAN Bus**: SN65HVD230 via USB-C SBU pins
- **USB-C**: 5V charging + CAN sideband on SBU pins
- **Buttons**: 6 tactile switches (GP0–GP5) for menu navigation
- **Standalone operation**: Schedules stored in NVS, RTC keeps time without network, full local control via screen and buttons

## Project Structure

```
hardware/kicad/          — KiCad design files (generated)
  ├── autofeeder.kicad_sch      — Generated schematic
  ├── autofeeder.kicad_pcb      — Generated PCB (autorouted + verified)
  ├── autofeeder.kicad_pro      — KiCad project settings
  ├── sheet_specs/autofeeder.py — Python schematic generator
  └── autofeeder_pcb.py         — Python PCB pipeline (place, route, pour, verify, export)
hardware/symbols/         — Custom KiCad symbol library
hardware/footprints/      — Custom KiCad footprints (ESP32-C6-Zero socket, OLED module)
firmware/esphome/         — ESPHome configuration
docs/                     — BOM, pinout, mechanical specs
fabrication/              — Gerbers, drill, BOM, CPL (for JLCPCB)
tools/sch_gen/            — KiCad S-expression generation library
```

## Pin Assignments

See [docs/pinout.md](docs/pinout.md) for full GPIO table.

Key assignments:
- GP0–GP5: Buttons (individual GPIOs)
- GPIO19/20: Motor control (TX/RX repurposed)
- GP14/15/18/12: Display SPI (DC on GP12 via pogo pin)
- GP21/22: CAN bus
- GP6: Battery monitor ADC
- GP13/23: I2C for DS3231 RTC
- GP7/8: UART for GPS module

## Standalone Operation

The controller runs independently of Home Assistant/ESPHome:

- **RTC**: DS3231 keeps time with coin cell backup during power loss
- **Schedules**: Up to 4 daily feeding times stored in ESP32 NVS
- **Display**: Full menu system — status, manual feed, schedule list, time set, GPS status, settings
- **Buttons**: POWER (back), TIMER (cycle), MANUAL (feed), SETTINGS (confirm/toggle), UP/DOWN (adjust)
- **GPS**: Optional module for offline time synchronization
- **Matter**: When network is available, schedules can also be managed via Home Assistant

## Build

### Schematic
```bash
PYTHONPATH=tools python3 hardware/kicad/sheet_specs/autofeeder.py
```

### PCB
```bash
# Requires KiCad 9.0+ and Freerouting on PATH
PYTHONPATH=tools python3 hardware/kicad/autofeeder_pcb.py
```

### Firmware
```bash
cd firmware/esphome
esphome run autofeeder.yaml
```

## BOM

See [docs/bom.md](docs/bom.md) for full bill of materials.

### Required additions (not on main board)
- DS3231 RTC module (ZS-042) with CR2032 cell
- NEO-6M/7M/8M GPS module (optional)
- 7× pogo pins 0.9mm × 11mm (for Zero bottom-edge pads)

## License

CERN Open Hardware Licence Version 2 - Weakly Reciprocal (CERN-OHL-W-2.0)
