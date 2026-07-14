# Autofeeder — Fabrication & Parts Acquisition Plan

Board: **autofeedermod** · 4-layer · 56.1 × 54.1 mm · commit `f922a42` (fab-ready)
Target house: **JLCPCB** (BOM/CPL are in JLCPCB format). Everything here also works at
any house that takes RS-274X gerbers + Excellon drill.

> **Status:** 0 unconnected, 0 DRC error-level violations. Remaining DRC items are
> cosmetic (11 silkscreen overlaps) and do not affect fabrication.

---

## 0. Pre-flight — use the CURRENT files

The fab outputs were regenerated on the last commit. **Always re-zip / re-export from the
committed tree before ordering** — a stale `autofeeder-gerbers.zip` once lagged the copper
by several hours and would have shipped an earlier (shorted) board.

Regenerate from scratch if in any doubt:
```bash
PYTHONPATH=tools python3 hardware/kicad/autofeeder_pcb.py     # full pipeline: route + export
# then rebuild the gerber zip (see fabrication/gerbers/*.g*)
```
Verify the board is clean before spending money:
```bash
kicad-cli pcb drc --severity-all --schematic-parity --format json \
  hardware/kicad/autofeeder.kicad_pcb -o /tmp/drc.json
# expect: 0 unconnected_items, 0 error-severity violations
```

---

## 1. PCB fabrication (bare board)

Upload **`fabrication/autofeeder-gerbers.zip`** (13 files: F/In1/In2/B copper, F/B mask,
F/B paste, F/B silk, Edge.Cuts, drill, job).

| Setting | Value | Notes |
|---|---|---|
| Layers | **4** | F.Cu / In1.Cu / In2.Cu / B.Cu |
| Dimensions | **56.1 × 54.1 mm** | fits the WSG-V1.7 fascia — do not scale |
| Thickness | **1.6 mm** | |
| Copper weight | 1 oz | standard |
| Min track / clearance | 0.20 mm / 0.15 mm | within JLCPCB standard capability |
| Min via | 0.30 mm drill / 0.60 mm pad | plus 0.60/0.65/0.80/1.00/1.10 mm pads, 2.10 mm mounting holes |
| Surface finish | **ENIG (recommended)** | U4 is WSON-10 at 0.5 mm pitch + USB-C — ENIG gives better fine-pitch yield than HASL |
| Impedance control | No | not required |
| Castellated / edge plating | No | |

Mounting holes H1–H4 are **non-plated** (2.1 mm). Leave "remove order number" as
JLCPCB's choice, or set to a silk-free area if you care.

---

## 2. PCB assembly (SMT, JLCPCB) — **double-sided**

SMT reflow parts sit on **both** sides:
- **Bottom:** all ICs, passives, USB-C, LED, fuse, inductor (25 parts)
- **Top:** the 6 tactile switches SW1–SW6 (user-facing)

Upload these **SMT-only** files (they exclude the hand-soldered modules/connectors so the
placement machine is never asked to place something that isn't there):

- BOM → **`fabrication/autofeeder-bom-smt.csv`** (20 lines, 31 placements)
- CPL → **`fabrication/autofeeder-cpl-smt.csv`** (31 placements)

> Do **not** upload the full `autofeeder-bom.csv` / `autofeeder-cpl.csv` for SMT — those
> include U1, DISP1 and the THT connectors (hand-soldered / customer-supplied).

### ⚠️ Decide before ordering assembly
1. **D1 (1N5817) is an axial DO-41 through-hole diode** but is in the assembled BOM.
   JLCPCB's standard SMT line cannot place axial THT. Choose one:
   - Substitute an **SMD Schottky** (e.g. SS34 in SMA, ≥1 A / 40 V) and update the
     footprint + BOM, **or**
   - Move D1 to the hand-solder list and place it yourself.
2. **Extended vs Basic parts:** U4 (C15516), U8 (C2830320), U3 (C18164398), U6 (C12084),
   the switches (C127488) and USB-C (C165948) are likely JLCPCB *extended* parts (one-time
   feeder fee each). Confirm live stock for every LCSC number at order time; have a
   second-source ready for anything out of stock.
3. **Confirm switch orientation** — the KMR2 tactile symbol carries 4 pins but the footprint
   has only pads 1/2 (1→button net, 2→GND). This is expected; buttons are wired correctly.

---

## 3. Parts to acquire separately (not on the SMT order)

### Customer-supplied modules (plug/solder onto the finished board)
| Ref | Part | Qty | Source |
|---|---|---|---|
| U1 | **ESP32-C6-Zero** module (Waveshare) | 1 | Waveshare / distributor. Confirm the U1 land pattern mounting method (castellated solder vs pogo/socket) before assembly. |
| DISP1 | **OLED 1.3" SPI 128×64** (SSD1306/SH1106) | 1 | generic; verify pin order matches the DISP1 header |

### Hand-soldered THT connectors (have LCSC numbers; buy with the SMT order or locally)
| Refs | Part | Qty | LCSC |
|---|---|---|---|
| J1, J_MOTOR_CTRL1, J_MOTOR_PWR1 | JST XH B2B-XH-A 2-pin vertical, 2.5 mm | 3 | C158012 |
| J4, J_RTC1, J_GPS1 | Pin header 1×4, 2.54 mm vertical | 3 | C42431787 |

### External modules that plug into the headers (system-level, buy as needed)
- **DS3231 RTC** module (into J_RTC) — has onboard pull-ups + CR2032 holder
- **NEO-6M / NEO-8M GPS** module (into J_GPS)
- **Battery** (Li-ion, into J1) and **motor** (into J_MOTOR_PWR / J_MOTOR_CTRL)

---

## 4. Hand-assembly order (after the SMT boards arrive)

1. Inspect SMT work; reflow-touch any bridging on U4 (WSON) / J3 (USB-C).
2. Solder THT connectors: J1, J4, J_RTC1, J_GPS1, J_MOTOR_PWR1, J_MOTOR_CTRL1.
3. Solder D1 here if you chose hand-solder in §2.1.
4. Mount U1 (ESP32-C6-Zero) per its chosen method; then DISP1 (OLED).
5. Plug in RTC / GPS modules.

## 5. Power-on bring-up (before connecting a motor)

1. **No module, USB-C only:** confirm 3V3 rail at U4 output; check no short across the
   battery terminals (J1) — this board previously had a BATT_P/BATT_N short that is now
   fixed, so verify 0 Ω is **not** present between J1 pins.
2. Charge path: apply battery, confirm TP4056 (U2) charge LED (LED_CHG1) behaves.
3. Fit U1, flash firmware, verify OLED, buttons SW1–6, RTC, GPS over their buses.
4. Only then connect the motor to J_MOTOR_PWR / J_MOTOR_CTRL.

---

## File manifest (in `fabrication/`)
- `autofeeder-gerbers.zip` — bare-board fab (§1)
- `autofeeder-bom-smt.csv` / `autofeeder-cpl-smt.csv` — **SMT assembly** (§2)
- `autofeeder-bom.csv` — full curated BOM incl. hand/customer parts (reference)
- `autofeeder-cpl.csv` — full placement incl. hand parts (reference)
- `gerbers/` — individual gerber + drill + job files
