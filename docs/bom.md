# Bill of Materials — Autofeeder Controller

## Active Components

| Qty | Ref | Part | Package | Description |
|---|---|---|---|---|
| 1 | U1 | ESP32-C6-Zero | Module 23×18mm socket (2×9 2.54mm) | MCU: WiFi 6 + BLE 5 + Thread + Matter, via Waveshare module |
| 1 | U2 | TP4056 | SOIC-8 | Linear Li-ion charger, 1A |
| 1 | U3 | DW01A | SOT-23-6 | Li-ion protection IC (overcharge/discharge detect) |
| 1 | U8 | FS8205A | SOT-23-6 | Dual NMOS charge/discharge protection FETs (driven by DW01A) |
| 1 | U4 | TPS63031DSKR | WSON-10 2.5×2.5mm | Buck-boost regulator, fixed 3.3V, 900mA (C15516, LCSC) |
| 1 | — | MX1508 module (external) | Breakout 15×20mm | Dual H-bridge motor driver, ~1.5A/ch, 2–10V. Plugs into J_MOTOR_CTRL + J_MOTOR_PWR via 2× JST XH cables |
| 1 | U6 | SN65HVD230 | SOIC-8 | CAN transceiver, 3.3V, 1Mbps. RS pin (8) wired to GP9 for standby-mode sleep (~1µA vs 10mA) |

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
| 1 | J_MOTOR_CTRL | JST XH B2B-XH-A | 2-pin vertical 2.5mm | MX1508 control (MOTOR_IN1 / MOTOR_IN2) |
| 1 | J_MOTOR_PWR | JST XH B2B-XH-A | 2-pin vertical 2.5mm | MX1508 power (BATT_PROT / GND) |
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
| 1 | R3 | 47kΩ ±1% | 0603 | Battery voltage divider top (BATT_PROT → BAT_MON) — increased from 10k to reduce sleep current (185→39µA) |
| 1 | R4 | 47kΩ ±1% | 0603 | Battery voltage divider bottom (BAT_MON → GND) — increased from 10k to reduce sleep current |
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

## Pre-Fabrication Checklist

### Order Settings
| Setting | Value | Notes |
|---|---|---|
| Layers | 4 | 4-layer for better power routing and ground plane |
| Dimensions | 56×54mm | Under 100×100mm threshold |
| Quantity | 5 | Minimum batch, spare boards |
| Thickness | 1.6mm | Standard FR4 |
| Surface Finish | **ENIG** | Recommended for USB-C + fine-pitch |
| Solder Mask | Green | Cheapest; colored adds ~$5 |
| Mark on PCB | Order Number: **Remove from all layers** | Cleaner look |
| Stencil | 0.1mm steel stencil (~$15) | Optional but recommended |
| Assembly | Top + Bottom SMD | JLCPCB does all 19 SMD parts |
| PCBA Qty | 5 | All 5 boards assembled |

### Files to Upload
| File | Purpose |
|---|---|
| `autofeeder-gerbers.zip` | 13 gerber layers + drill + job file + CPL |
| `fabrication/autofeeder-bom.csv` | Bill of materials with LCSC part numbers |
| `fabrication/autofeeder-cpl.csv` | Pick-and-place positions (40 components) |

### Verify in Gerber Viewer
- [ ] Board outline: 56×54mm rectangle, no cutouts
- [ ] 4× M2 mounting holes (2.1mm NPTH) at corners
- [ ] All 14 gerber layers load correctly (F.Cu, B.Cu, In1.Cu, In2.Cu, masks, pastes, silkscreen, edge cuts, drill)
- [ ] Silkscreen is legible, reference designators visible
- [ ] Solder mask openings align with pads

### DRC Status

All nets connected (0 unconnected items). Remaining violations are pre-existing marginal clearance/cosmetic issues:

| Issue | Type | Status |
|---|---|---|
| BATT_P/BATT_N at J1 area | Pre-existing clearance | Acceptable for prototype |
| Tracks crossing near (17-20, 32-33) | Pre-existing clearance | Acceptable for prototype |
| Solder mask bridge | Cosmetic | No electrical impact |

OC_GATE and OD_GATE pre-routed (U3↔U8 gate connections) — no bodge wires required.

---

## Fabrication

### Ordering from JLCPCB

Upload `autofeeder-gerbers.zip` at [jlcpcb.com](https://jlcpcb.com):

| Setting | Value | Why |
|---|---|---|
| Layers | 4 | 4-layer for better power routing and ground plane |
| Dimensions | 56×54mm | Base price tier |
| PCB Qty | 5 | 5 is the minimum, cheapest per-board |
| Thickness | 1.6mm | Standard |
| Surface Finish | **ENIG** | ~$5 extra but worth it: flat pads for WSON-10/USB-C, no oxidation |
| Color | Green | Cheapest; colored adds ~$5 |
| Mark on PCB | Order Number: Remove from all layers | Cleaner look |
| Stencil | **Yes — 0.1mm steel stencil** ($15) | Even if you have JLCPCB assemble SMD, the stencil is useful for rework |

### JLCPCB SMD Assembly (Recommended for One-Off)

JLCPCB will assemble all SMD components for ~$25 extra. Upload these files:

| File | Contents |
|---|---|
| `fabrication/autofeeder-bom.csv` | LCSC part numbers for all SMD components |
| `fabrication/autofeeder-cpl.csv` | Pick-and-place positions (40 components) |
| `autofeeder-gerbers.zip` | All gerber layers |

**JLCPCB assembles** (18 parts): TP4056, DW01A, FS8205A, TPS63031, DRV8871, SN65HVD230, 1N5817, LED, PTC fuse, USB-C, 6 tactile switches, all passives (R's, C's, L1)

**You hand-solder**: ESP32-C6-Zero module, OLED display, JST connectors, pin headers, pogo pins

---

## DIY Assembly Guide

### Difficulty Overview

| Component | Package | Difficulty | Method |
|---|---|---|---|
| TPS63031DSKR | WSON-10 2.5×2.5mm | Hard | Hot air or reflow (not feasible with iron alone) |
| USB-C | 16-pin SMD 0.5mm pitch | Moderate | Iron + flux, drag-solder |
| SOIC-8 (TP4056, DRV8871, SN65HVD230) | 1.27mm pitch | Easy | Fine iron, tin one lead first |
| SOT-23-6 (DW01A, FS8205A) | 0.95mm pitch | Moderate | Extended pads help; flux essential |
| 0603/0805 passives | — | Easy | Tweezers + iron |
| Tactile switches | 4×4mm | Easy | Self-aligning when reflowed |
| Pin headers, JST | THT | Easy | Straightforward |
| Pogo pins | 0.9mm × 11mm | Moderate | Keep straight, solder one at a time |

### Recommended Assembly Order

```
1. JLCPCB assembles all SMD (or do steps 2-5 yourself)
2. Solder TPS63031 (WSON-10) — hot air or reflow
3. Solder remaining SMD ICs + passives
4. Solder USB-C connector
5. Solder tactile switches
6. Solder through-hole: pin headers, JST connectors
7. Solder pogo pins (ensure straight alignment)
8. Plug in ESP32-C6-Zero module, OLED display
9. Connect MX1508 module via 2× JST XH cables
10. Flash firmware via ESP32-C6-Zero's onboard USB-C
11. Install in feeder enclosure
```

### TPS63031 (WSON-10) — DIY with Stencil + Hot Air

This is the most critical soldering operation. Procedure:

1. **Apply paste**: Use the steel stencil to apply solder paste to all pads. Align stencil with PCB, apply paste, squeegee across.
2. **Place components**: Place all SMD parts (WSON-10 first, then smaller parts). The paste holds them in place.
3. **Preheat**: Set PCB on a hot plate or skillet at **150°C** for 60 seconds (warms the board from underneath — prevents thermal shock).
4. **Hot air reflow**: Use **8mm nozzle, 320°C, low airflow** (~30%). Sweep across the board in a spiral pattern. Watch for the paste to turn shiny and components to settle (10-20 seconds).
5. **WSON-10 focus**: Spend an extra 5-10 seconds on the WSON-10 specifically. The surface tension of the melted paste will self-align the IC. You'll see it "float" into position.
6. **Done**: Remove heat, let cool for 30 seconds.
7. **Inspect**: Under magnification, check for solder bridges on the WSON-10 (0.5mm pitch). Use solder wick + flux to clean any bridges.
8. **Rework**: If the WSON-10 is misaligned, apply flux to all pins and reheat with hot air. Tap gently with tweezers.

### MX1508 Motor Driver

The DRV8871 H-bridge was replaced with an external **MX1508 dual H-bridge breakout board** to reduce board congestion. The MX1508 connects via 2× JST XH cables:

| Cable | Main PCB (JST XH 2-pin) | MX1508 |
|---|---|---|
| J_MOTOR_CTRL (52, 7) | MOTOR_IN1 (GPIO19), MOTOR_IN2 (GPIO20) | IN1, IN2 |
| J_MOTOR_PWR (52, 25) | BATT_PROT (3.0-4.2V), GND | VCC, GND |

Cable assembly: JST XH 2-pin male on both ends, ~100mm, 26-28AWG. Solder JST XH 2-pin female headers into the MX1508 breakout's open holes.

Motor output (OA1/OA2) connects directly from MX1508 to the auger motor — not on the main PCB. Same control logic: IN1/IN2 = HIGH/LOW forward.

### Cost Breakdown

#### Scenario A: JLCPCB SMD Assembly + DIY THT + MX1508

| Item | Cost |
|---|---|
| PCB 5pcs (56×54mm, 2L, 1.6mm, ENIG, green) | ~$12 |
| SMD assembly setup + placement (19 components) | ~$7 + ~$3 |
| Extended parts fee (WSON-10, USB-C, tactile switches) | ~$10 |
| SMD components sourced by JLCPCB | ~$6 |
| Shipping (PCB + assembled boards) | ~$10 |
| **Subtotal (JLCPCB)** | **~$48** |
| 3× JST XH 2-pin (B2B-XH-A) from LCSC | ~$0.50 |
| 1× MX1508 module (AliExpress, you have these) | ~$1.50 |
| 2× JST XH 2-pin cable assemblies, ~100mm | ~$2 |
| ESP32-C6-Zero module | ~$6 |
| OLED 1.3" SSD1306 SPI | ~$4 |
| DS3231 RTC module + CR2032 | ~$3 |
| NEO-6M GPS (optional) | ~$4 |
| Pogo pins, pin headers, 18650 battery | ~$10 |
| **Total first board** | **~$79** |
| **Each additional board** (shared PCB cost) | **~$60** |

#### Scenario B: Full DIY (Stencil + Hot Air)

| Item | Cost |
|---|---|
| PCB 5pcs + steel stencil (0.1mm) | ~$12 + $15 = $27 |
| SMD components from LCSC (qty 10-50) | ~$12 |
| Solder paste (stencil-grade) | ~$8 |
| Shipping | ~$8 |
| **Subtotal (PCB + stencil + parts)** | **~$55** |
| Same THT/cable costs as Scenario A | ~$27 |
| **Total first board** | **~$82** |
| **Each additional board** (reuse stencil) | **~$35** |

#### Which to choose

| Use Case | Best Option | Why |
|---|---|---|
| One-off prototype | **Scenario A** ($79) | JLCPCB handles the WSON-10; you just do THT + cables |
| 2-3 units | **Scenario A** | Stencil + paste cost doesn't pay back until 4+ units |
| 4+ units or iterative development | **Scenario B** ($35/ea after first) | Stencil is a one-time cost; no JLCPCB assembly fees |
| Learning SMD soldering | **Scenario B** | The MX1508 change removed the DRV8871 (SOIC-8), the trickiest IC left is WSON-10 (TPS63031) |
| Want it work first time | **Scenario A** | Professional assembly guarantees WSON-10 and USB-C joints |

### Solder Mask & Finish Notes

- **Solder mask is included** on all JLCPCB boards — it helps prevent bridges on fine-pitch parts
- **ENIG finish** ($5 extra) is recommended over HASL for:
  - Flat pads (essential for good WSON-10 soldering)
  - USB-C connector durability (multiple insertions)
  - Easier hand-soldering (no uneven HASL bumps)
- **The stencil** (0.1mm steel, ~$15) applies paste precisely; without it, dispensing paste on the WSON-10 pad is unreliable

### Via-in-Pad Note

The U4 pad 2 (L2_NODE connection) has a via beneath the SMD pad. If JLCPCB flags this during DFM:
- Tell them it's **same-net via-in-pad, acceptable**
- If doing DIY, solder this pad with extra flux and a slightly higher iron temperature to ensure the joint forms before solder wicks into the via
