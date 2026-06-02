# Bill of Materials — Autofeeder Controller

## Active Components

| Qty | Ref | Part | Package | Description |
|---|---|---|---|---|
| 1 | U1 | ESP32-C6-WROOM-1 | Module 18×20mm | MCU: WiFi 6 + BLE 5 + Thread + Matter |
| 1 | U2 | TP4056 | SOIC-8 | Linear Li-ion charger, 1A |
| 1 | U3 | DW01A + FS8205A | SOT-23-6 + TSSOP-8 | Li-ion protection (overcharge/discharge/current) |
| 1 | U4 | TPS63802 | QFN-10 (1.6×1.6mm) | Buck-boost regulator, 3.3V/2A |
| 1 | U5 | DRV8871 | SOIC-8 | H-bridge motor driver, 3.6A peak |
| 1 | U6 | SN65HVD230 | SOIC-8 | CAN transceiver, 3.3V, 1Mbps |

## Display

| Qty | Ref | Part | Description |
|---|---|---|---|
| 1 | DISP1 | SSD1306 128×64 SPI OLED | 0.96"–2.42" white/blue, 7-pin interface |

## Connectors

| Qty | Ref | Part | Package | Description |
|---|---|---|---|---|
| 1 | J1 | JST XH 2.54mm 2-pin | THT vertical | 18650 battery connector (B+ / B-) |
| 1 | J2 | JST XH 2.54mm 2-pin | THT vertical | Motor connector (M1+ / M1-) |
| 1 | J3 | USB-C Receptacle HRO TYPE-C-31-M-12 | SMD 16-pin | USB 2.0 + CAN sideband (SBU1/2) |
| 1 | J4 | Pin header 1×4, 2.54mm pitch | THT | Programming header: 3.3V, TX, RX, GND |

## Buttons

| Qty | Ref | Part | Package | Description |
|---|---|---|---|---|
| 6 | SW1–SW6 | Tactile switch 6×6×5mm | THT | Momentary, SPST |

## Resistors

| Qty | Ref | Value | Package | Notes |
|---|---|---|---|---|
| 1 | R1 | 10kΩ ±1% | 0603 | Button ADC pull-up to 3.3V |
| 1 | R2 | 1.2kΩ ±1% | 0603 | TP4056 PROG (sets 1A charge) |
| 2 | R3, R4 | 10kΩ ±1% | 0603 | Battery voltage divider (BAT_MON) |
| 1 | R5 | 120Ω ±1% | 0603 | CAN bus termination (solder-jumper selectable) |
| 1 | R6 | 1kΩ ±5% | 0603 | CANH series current limit |
| 1 | R7 | 330Ω ±5% | 0603 | Status LED current limit |
| 1 | R8 | 1kΩ ±5% | 0603 | PTC fuse pre-charge / battery sense |
| 1 | R9 | 10kΩ ±5% | 0603 | EN pull-up to 3.3V |
| 1 | R10 | 1kΩ ±5% | 0603 | CANL series current limit |
| 1 | R11 | 10kΩ ±5% | 0603 | Display CS pull-up to 3.3V |

**Button Ladder Resistors (SW1–SW6 on GPIO2 ADC):**

| Ref | Value | Package | ADC Voltage (approx) |
|---|---|---|---|
| R_BTN1 | 1kΩ ±5% | 0603 | 0.15V (SW1) |
| R_BTN2 | 3.3kΩ ±5% | 0603 | 0.45V (SW2) |
| R_BTN3 | 6.8kΩ ±5% | 0603 | 0.80V (SW3) |
| R_BTN4 | 12kΩ ±5% | 0603 | 1.20V (SW4) |
| R_BTN5 | 22kΩ ±5% | 0603 | 1.65V (SW5) |
| R_BTN6 | 47kΩ ±5% | 0603 | 2.20V (SW6) |

## Capacitors

| Qty | Ref | Value | Package | Notes |
|---|---|---|---|---|
| 2 | C1, C3 | 100nF ±10% X7R | 0603 | ESP32 + CAN decoupling |
| 1 | C2 | 10µF ±10% X7R | 0805 | ESP32 bulk decoupling |
| 1 | C4 | 10µF ±10% X7R | 0805 | TPS63802 input cap |
| 1 | C5 | 22µF ±10% X5R | 0805 | TPS63802 output cap |
| 1 | C6 | 100nF ±10% X7R | 0603 | CAN transceiver decoupling |

## Diodes / Protection

| Qty | Ref | Part | Package | Description |
|---|---|---|---|---|
| 1 | D1 | 1N5817 | DO-41 | Schottky, reverse polarity protection |
| 1 | F1 | PTC Resettable Fuse 500mA | 1812 | Battery input overcurrent |
| 2 | TVS1, TVS2 | PESD5V0S2BT | SOT-23 | ESD protection on CANH/CANL (SBU pins) |

## LEDs

| Qty | Ref | Color | Package | Notes |
|---|---|---|---|---|
| 1 | LED1 | Green | 0603 | Status indicator (GPIO6 active high) |
| 1 | LED2 | Red | 0603 | Charge indicator (TP4056 CHRG) |

## Other

| Qty | Part | Description |
|---|---|---|
| 1 | 18650 Li-ion cell | 3.7V nominal, protected or unprotected + DW01A |
| 1 | Custom USB-C cable | With SBU wires broken out for CAN bus access |

## Notes
- **Push buttons**: Use 6×6mm tactile switches, mounted on user-facing side of PCB
- **PCB thickness**: 1.6mm standard FR4, 2-layer, ENIG finish preferred for USB-C durability
- **All passives**: 0603 or 0805 metric (highly available, easy to solder with hot air)
- **LED current**: GREEN LED at ~5mA through 330Ω resistor from 3.3V
