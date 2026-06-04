# Bill of Materials — Autofeeder Controller

## Active Components

| Qty | Ref | Part | Package | Description |
|---|---|---|---|---|
| 1 | U1 | ESP32-C6-Zero | Module 23×18mm socket (2×9 2.54mm) | MCU: WiFi 6 + BLE 5 + Thread + Matter, via Waveshare module |
| 1 | U2 | TP4056 | SOIC-8 | Linear Li-ion charger, 1A |
| 1 | U3 | DW01A | SOT-23-6 | Li-ion protection IC (overcharge/discharge detect) |
| 1 | U8 | FS8205A | SOT-23-6 | Dual NMOS charge/discharge protection FETs (driven by DW01A) |
| 1 | U4 | TPS63031DSKR | WSON-10 2.5×2.5mm | Buck-boost regulator, fixed 3.3V, 900mA (C15516, LCSC) |
| 1 | U5 | DRV8871 | SOIC-8 | H-bridge motor driver, 3.6A peak |
| 1 | U6 | SN65HVD230 | SOIC-8 | CAN transceiver, 3.3V, 1Mbps |

### Passive Semiconductors

| Qty | Ref | Part | Package | Description |
|---|---|---|---|---|
| 1 | D1 | 1N5817 | DO-41 (P10.16mm, horizontal) | Schottky diode, reverse polarity protection |
| 1 | LED_CHG | RED LED | 0603 | Charge indicator (active low, TP4056 CHRG pin) |
| 1 | F1 | PTC Resettable Fuse 500mA | 1812 | Battery input overcurrent protection |

## Display

| Qty | Ref | Part | Description |
|---|---|---|---|
| 1 | DISP1 | SSD1306/SH1106 1.3" 128×64 SPI OLED module | 7-pin header (GND VCC SCK MOSI RES DC CS) |

## Connectors

| Qty | Ref | Part | Package | Description |
|---|---|---|---|---|---|
| 1 | J1 | JST XH B2B-XH-A | 2-pin vertical 2.5mm | Battery connector (BATT_P / BATT_N) |
| 1 | J2 | JST XH B2B-XH-A | 2-pin vertical 2.5mm | Motor connector (M1+ / M1-) |
| 1 | J3 | USB-C Receptacle HRO TYPE-C-31-M-12 | SMD 16-pin | USB 2.0 + CAN sideband (SBU1/2), shield → GND |
| 1 | J4 | Pin header 1×4, 2.54mm pitch | THT vertical | Debug header: 3.3V, NC, NC, GND |
| 1 | J_RTC | Pin header 1×4, 2.54mm pitch | THT vertical | DS3231 RTC module connector: VCC, GND, SDA, SCL |
| 1 | J_GPS | Pin header 1×4, 2.54mm pitch | THT vertical | GPS module connector: VCC, GND, GPS_RX, GPS_TX |

## Buttons

| Qty | Ref | Part | Package | Description |
|---|---|---|---|---|
| 6 | SW1–SW6 | Alps SKRPADE010 (or equiv CK KMR2) | 4×4mm SMD tactile | Momentary, SPST; each has individual GPIO (GP0–GP5) |

## Pogo Pins (Bottom Edge — ESP32-C6-Zero Castellated Pads)

| Qty | Ref | Part | Description |
|---|---|---|---|
| 7 | P1–P7 | Pogo pin, 0.9mm barrel × 11mm, ~2mm stroke | Soldered in bottom-edge through-holes (pads 19–25, enlarged to 1.0mm drill). Spring tip contacts Zero module bottom castellated pads. |

## External Modules (Customer Fitted — Optional)

| Qty | Ref | Part | Description |
|---|---|---|---|
| 1 | — | DS3231 module (ZS-042 or equiv) | I2C RTC with CR2032 backup. Plugs into J_RTC. Onboard pull-ups + coin cell holder. |
| 1 | — | NEO-6M / NEO-7M / NEO-8M GPS module | UART GPS receiver. Plugs into J_GPS. Provides UTC time via NMEA for offline RTC sync. |
| 1 | — | CR2032 3V lithium coin cell | RTC backup battery. Installed in DS3231 module holder. |

## Resistors

| Qty | Ref | Value | Package | Notes |
|---|---|---|---|---|
| 1 | R2_C | 1.2kΩ ±1% | 0603 | TP4056 PROG resistor (sets 1A charge current) |
| 1 | R3 | 10kΩ ±1% | 0603 | Battery voltage divider top (BATT_PROT → BAT_MON) |
| 1 | R4 | 10kΩ ±1% | 0603 | Battery voltage divider bottom (BAT_MON → GND) |
| 1 | R5 | 120Ω ±1% | 0603 | CAN bus termination (solder-jumper selectable) |
| 1 | R6 | 1kΩ ±5% | 0603 | CAN_H series current limit |
| 1 | R10 | 1kΩ ±5% | 0603 | CAN_L series current limit |
| 1 | R13 | 10kΩ ±5% | 0603 | DISP_RST pull-up to VCC_3V3 |
| 2 | R_CC1, R_CC2 | 5.1kΩ ±5% | 0603 | USB-C CC1/CC2 pull-down to GND |

## Capacitors

| Qty | Ref | Value | Package | Notes |
|---|---|---|---|---|
| 2 | C1, C3 | 100nF ±10% X7R | 0603 | ESP32 decoupling + display decoupling |
| 1 | C2 | 10µF ±10% X7R | 0805 | ESP32 bulk decoupling |
| 1 | C4 | 10µF ±10% X7R | 0805 | TPS63031 input cap |
| 1 | C5 | 22µF ±10% X5R | 0805 | TPS63031 output cap |
| 1 | C6 | 100nF ±10% X7R | 0603 | CAN transceiver decoupling |

## Inductor

| Qty | Ref | Value | Package | Notes |
|---|---|---|---|---|
| 1 | L1 | 4.7µH ±20% | 0805 | TPS63031 buck-boost inductor (L1→L2) |

## Hardware

| Qty | Ref | Part | Description |
|---|---|---|---|
| 4 | H1–H4 | Mounting hole 2.1mm NPTH | M2 screw clearance, corners at (7,6), (48,6), (7,43), (48,43) |
| 1 | — | 18650 Li-ion cell | 3.7V nominal, protected or unprotected (DW01A + FS8205A on board) |
| 1 | — | Custom USB-C cable | With SBU wires broken out for CAN bus access |

## Assembly Notes

### U4 Substitution: TPS63031DSKR
**Original design used RT6150A (SOT-23-6)** which was found to be a non-existent package combination at required current. Replaced with **TPS63031DSKR (C15516, LCSC $0.70–1.35)**: fixed 3.3V output, WSON-10 2.5×2.5mm, 900mA switch current.
- No feedback resistors needed (fixed 3.3V output) — R11/R12 removed
- Pinout per TI DSK package: VOUT, L2, PGND, L1, VIN, EN, PS/SYNC, VINA, GND, FB
- FB (pin 10) tied to VOUT, EN (pin 6) tied to VIN, PS/SYNC (pin 7) tied to GND (power-save enabled)
- Inductor (L1) connects between L1 (pin 4) and L2 (pin 2) — nets L1_NODE / L2_NODE
- Input cap 10µF (C4), output cap 22µF (C5) — unchanged

### JLCPCB Assembly
- `fabrication/autofeeder-bom.csv` — LCSC-importable BOM for JLCPCB assembly
- `fabrication/autofeeder-cpl.csv` — Component placement file
- Parts marked "Hand solder — customer supplied" (ESP32-C6-Zero, OLED module, JST connectors, pin headers) are not placed by JLCPCB
- L1 (4.7µH 0805, C6828258, Würth 74479775247) is rated 850mA — verify saturation current against TPS63031 peak inductor current (~1A); consider a larger package if needed

### General Notes
- **Push buttons**: SMD tactile switches (Alps SKRPADE010 or equivalent CK KMR2), mounted on user-facing (front) side
- **ESP32-C6-Zero**: Socketed via 2×9 female pin headers (2.54mm pitch); Zero's onboard USB-C handles flashing
- **PCB thickness**: 1.6mm standard FR4, 2-layer, ENIG finish preferred for USB-C durability
- **All passives**: 0603 or 0805 metric (highly available, easy to solder with hot air)
- **All SOT-23-6 ICs**: Use the handsoldering variant footprint (extended pads)
- **TPS63031DSKR**: Fixed 3.3V output, no feedback resistors. PS/SYNC grounded for power-save mode. VOUT = 3.3V ±2% — safe for ESP32-C6 (3.0–3.6V range)
