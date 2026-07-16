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
| Surface finish | **HASL-with-lead** | Cheapest option ($7 vs $23.80 ENIG). U4 at 0.5 mm pitch is marginal but JLCPCB handles this routinely; switch to ENIG if reflow yield is poor |
| Impedance control | No | not required |
| Castellated / edge plating | No | |

Mounting holes H1–H4 are **non-plated** (2.1 mm). Leave "remove order number" as
JLCPCB's choice, or set to a silk-free area if you care.

---

## 2. PCB assembly (SMT, JLCPCB) — **single-sided (Economic)**

All SMT reflow parts are on the **bottom** side only (25 parts). The 6 tactile switches
SW1–SW6 are on the top but are moved to the hand-solder list (§3) — they have large pads
and are trivial to solder, saving ~$55 in setup/feeder fees by enabling Economic assembly.

Upload these **SMT-only** files (they exclude the hand-soldered switches, modules/connectors
so the placement machine is never asked to place something that isn't there):

- BOM → **`fabrication/autofeeder-bom-smt.csv`** (18 lines, 25 placements — bottom only)
- CPL → **`fabrication/autofeeder-cpl-smt.csv`** (25 placements — bottom only)

> Do **not** upload the full `autofeeder-bom.csv` / `autofeeder-cpl.csv` for SMT — those
> include U1, DISP1, the switches and the THT connectors (hand-soldered / customer-supplied).

### ⚠️ Decide before ordering assembly
1. **Extended vs Basic parts:** U4 (C15516), U8 (C2830320), U3 (C18164398), U6 (C12084)
   and USB-C (C165948) are likely JLCPCB *extended* parts (one-time feeder fee each).
   The switches (C127488) are no longer on the SMT order — hand-solder them yourself.
   Confirm live stock for every LCSC number at order time; have a second-source ready
   for anything out of stock.
2. **D1 (1N5817) is THT** — hand-solder it yourself (see §3).

---

## 3. Parts to acquire separately (not on the SMT order)

### Customer-supplied modules (plug/solder onto the finished board)
| Ref | Part | Qty | Source |
|---|---|---|---|
| U1 | **ESP32-C6-Zero** module (Waveshare) | 1 | Waveshare / distributor. Confirm the U1 land pattern mounting method (castellated solder vs pogo/socket) before assembly. |
| DISP1 | **OLED 1.3" SPI 128×64** (SSD1306/SH1106) | 1 | generic; verify pin order matches the DISP1 header |

### Hand-soldered parts (have LCSC numbers; buy with the SMT order or locally)
| Refs | Part | Qty | LCSC |
|---|---|---|---|
| SW1–SW6 | SKRPADE010 Tactile Switch | 6 | C127488 |
| D1 | 1N5817 Schottky Diode DO-41 (THT) | 1 | C507852 |
| J1, J_MOTOR_CTRL1, J_MOTOR_PWR1 | JST XH B2B-XH-A 2-pin vertical, 2.5 mm | 3 | C158012 |
| J4, J_RTC1, J_GPS1 | Pin header 1×4, 2.54 mm vertical | 3 | C42431787 |

### External modules that plug into the headers (system-level, buy as needed)
- **DS3231 RTC** module (into J_RTC) — has onboard pull-ups + CR2032 holder
- **NEO-6M / NEO-8M GPS** module (into J_GPS)
- **Battery** (Li-ion, into J1) and **motor** (into J_MOTOR_PWR / J_MOTOR_CTRL)

---

## 4. Hand-assembly order (after the SMT boards arrive)

1. Inspect SMT work; reflow-touch any bridging on U4 (WSON) / J3 (USB-C).
2. Solder tactile switches SW1–SW6 (top side, large pads — straightforward).
3. Solder D1 (1N5817 THT diode).
4. Solder THT connectors: J1, J4, J_RTC1, J_GPS1, J_MOTOR_PWR1, J_MOTOR_CTRL1.
5. Mount U1 (ESP32-C6-Zero) per its chosen method; then DISP1 (OLED).
6. Plug in RTC / GPS modules.

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
