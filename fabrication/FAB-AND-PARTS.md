# Autofeeder — Fabrication & Parts Acquisition Plan

Board: **autofeedermod** · 4-layer · 56.1 × 54.1 mm · commit `f922a42` (fab-ready)
Target house: **JLCPCB** (bare PCBs + stencil) · Components: **LCSC**

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

## 1. PCB fabrication (bare board) — JLCPCB

Upload **`fabrication/autofeeder-gerbers.zip`** (13 files: F/In1/In2/B copper, F/B mask,
F/B paste, F/B silk, Edge.Cuts, drill, job).

| Setting | Value | Notes |
|---|---|---|
| Layers | **4** | F.Cu / In1.Cu / In2.Cu / B.Cu |
| Dimensions | **56.1 × 54.1 mm** | fits the WSG-V1.7 fascia — do not scale |
| Quantity | **10 pcs** | marginal cost over 5 pcs; gives spares for rework |
| Thickness | **1.6 mm** | |
| Copper weight | 1 oz | standard |
| Min track / clearance | 0.20 mm / 0.15 mm | within JLCPCB standard capability |
| Min via | 0.30 mm drill / 0.60 mm pad | plus 0.60/0.65/0.80/1.00/1.10 mm pads, 2.10 mm mounting holes |
| Surface finish | **HASL-with-lead** | cheapest; U4 at 0.5 mm pitch is marginal but JLCPCB handles this routinely |
| Solder mask | Green (cheapest) | |
| Impedance control | No | not required |
| Castellated / edge plating | No | |

Estimated bare PCB cost: **~$10-12** for 10 pcs.

Mounting holes H1–H4 are **non-plated** (2.1 mm). Leave "remove order number" as
JLCPCB's choice.

### Shipping

Use **Global Standard Direct Line** (~$12-15 to US) instead of DHL Express (~$43).
This is DAP (Delivered At Place) — you may owe a small customs fee ($4-8) on delivery.
Forum users report successful delivery in 10-14 days with no surprise charges for small orders.

---

## 2. SMT stencil — JLCPCB

Order a **laser-cut stencil** alongside the PCBs (ships together, saves shipping).

| Setting | Value | Notes |
|---|---|---|
| Stencil side | **Bottom only** | all SMT parts are on the bottom |
| Size | **Custom: 60 × 60 mm** | covers the 56.1 × 54.1 mm board with margin |
| Thickness | **0.12 mm** | standard; good for 0603/0805 and 0.5 mm pitch |
| Process | Sanding (cheapest) | nano-coating optional ($4.72) for better paste release on U4 |
| Frame | Frameless | sufficient for manual stencil printing |

Estimated stencil cost: **$3** (≤100×100 mm tier).

**Tip:** If U4 (WSON-10, 0.5 mm pitch) gives reflow trouble, re-order with nano-coating
($4.72) — it improves paste release on fine-pitch pads.

---

## 3. Components — LCSC

All components are ordered from LCSC (lcsc.com). Use the LCSC BOM file for direct upload:

**`fabrication/autofeeder-lcsc-bom.csv`**

This BOM includes every component on the board (SMT + hand-solder) with LCSC part numbers.
Order 10-20% extra for passives (cheap insurance against丢了 during assembly).

### SMT components (reflow with hot air, 25 placements)

| Ref(s) | Part | Qty | LCSC | Package | Notes |
|---|---|---|---|---|---|
| U4 | TPS63031DSKR Buck-Boost 3.3V | 1 | C15516 | WSON-10 2.5×2.5mm 0.5mm pitch | **Hardest part.** Use stencil + hot air. Exposed pad underneath. |
| U8 | FS8205A Dual N-MOSFET | 1 | C908265 | SOT-23-6 | |
| U6 | SN65HVD230DR CAN Transceiver | 1 | C12084 | SOIC-8 | |
| U3 | DW01A Battery Protection IC | 1 | C2909013 | SOT-23-6 | |
| U2 | TP4056 Li-Ion Charger IC | 1 | C725790 | ESOP-8 | |
| J3 | TYPE-C-31-M-12 USB-C Receptacle | 1 | C3020560 | USB-C | Fine-pitch pins; hot air recommended |
| F1 | PTC Resettable Fuse 500mA 15V | 1 | C151169 | 1812 | |
| L1 | 4.7µH 600mA Inductor (TDK) | 1 | C404767 | 0805 | |
| LED_CHG1 | RED LED 0603 (Everlight) | 1 | C965849 | 0603 | |
| C1,C3,C6 | 100nF 50V X7R | 3 | C14663 | 0603 | |
| C2,C4 | 10µF 25V X7R | 2 | C3039694 | 0805 | |
| C5 | 22µF 10V X5R | 1 | C29277 | 0805 | |
| R2_C1 | 1.2kΩ 1% | 1 | C22765 | 0603 | |
| R3,R4 | 47kΩ 1% | 2 | C25819 | 0603 | |
| R13 | 10kΩ 1% | 1 | C25804 | 0603 | |
| R5 | 120Ω 1% | 1 | C22787 | 0603 | |
| R6,R10 | 1kΩ 1% | 2 | C21190 | 0603 | |
| R_CC1,R_CC2 | 5.1kΩ 1% | 2 | C23186 | 0603 | USB-C CC pull-downs |

### Hand-soldered parts (solder with iron after reflow)

| Ref(s) | Part | Qty | LCSC | Package | Notes |
|---|---|---|---|---|---|
| SW1–SW6 | SKRPADE010 Tactile Switch | 6 | C127488 | SW_Push | Large pads, trivial |
| D1 | 1N5817 Schottky Diode | 1 | C3759312 | DO-41 THT | Through-hole, solder with iron |
| J1, J_MOTOR_CTRL1, J_MOTOR_PWR1 | JST XH B2B-XH-A 2-pin Vertical | 3 | C158012 | THT 2.5mm | Through-hole connectors |
| J4, J_RTC1, J_GPS1 | Pin Header 1×4 Vertical | 3 | C2691448 | THT 2.54mm | Through-hole headers |

### External modules (customer-supplied, plug into headers)

| Ref | Part | Source |
|---|---|---|
| U1 | **ESP32-C6-Zero** module (Waveshare) | Waveshare / distributor |
| DISP1 | **OLED 1.3" SPI 128×64** (SSD1306/SH1106) | generic |
| — | **DS3231 RTC** module | into J_RTC |
| — | **NEO-6M / NEO-8M GPS** module | into J_GPS |
| — | Battery (Li-ion) + Motor | into J1 / J_MOTOR_PWR |

---

## 4. DIY reflow assembly

### Equipment needed
- Hot air rework station (you already have one)
- Solder paste (Type 4 recommended for 0.5mm pitch; Type 3 OK for 0603+)
- Flux (no-clean, in syringe or pen)
- Tweezers (ESD-safe)
- Magnifying glass or microscope (helpful for U4 inspection)
- Isopropyl alcohol + brushes for cleanup

### Assembly order

**Step 1 — Stencil + paste (bottom side)**
1. Secure PCB on a flat surface, bottom side up.
2. Align stencil over the PCB pads.
3. Apply solder paste with a squeegee or old credit card — one smooth pass.
4. Carefully lift stencil straight up. Inspect paste deposits under magnification.
5. **Check U4 pads especially** — all 10 signal pads + center thermal pad should have paste.

**Step 2 — Place components (bottom side)**
Place components in this order (smallest/most critical first):
1. **U4 (TPS63031)** — WSON-10, 0.5mm pitch. Align carefully with tweezers.
2. **J3 (USB-C)** — fine-pitch pins.
3. **U2, U3, U6, U8** — SOIC-8 / SOT-23-6.
4. **Passives** — 0603/0805 caps, resistors, inductor, LED, fuse.
5. Verify orientation of polarized parts (LED, diode, USB-C).

**Step 3 — Reflow**
1. Preheat board from below to ~100°C (hot air from above, low airflow).
2. Increase to reflow temperature:
   - **Leaded paste (Sn63/Pb37):** peak 210-220°C
   - **Lead-free paste (SAC305):** peak 235-245°C
3. Hold at peak for 10-20 seconds. Solder should flow and self-align.
4. Cool gradually — don't blow cold air directly on hot joints.
5. **Inspect U4** under magnification — check for bridges on 0.5mm pitch pads.

**Step 4 — Hand-solder THT parts (top side)**
1. SW1–SW6 tactile switches (top side, large pads).
2. D1 1N5817 diode (THT, through-hole).
3. J1, J4, J_RTC1, J_GPS1, J_MOTOR_PWR1, J_MOTOR_CTRL1 (THT connectors).

**Step 5 — Touch-up**
- Fix any bridges on U4/J3 with soldering iron + flux + solder wick.
- Re-reflow individual joints with hot air if needed.

### Tips for U4 (WSON-10, 0.5mm pitch)
- The thermal pad underneath is critical for heat dissipation — ensure good paste coverage.
- Self-alignment works well at 0.5mm pitch if paste volume is correct.
- If bridging occurs: apply flux, use solder wick + iron to remove excess, reapply paste to
  stencil area and re-reflow.
- Consider ordering a nano-coated stencil ($4.72) if first attempt fails — nano-coating
  improves paste release on fine-pitch apertures.

---

## 5. Power-on bring-up (before connecting a motor)

1. **No module, USB-C only:** confirm 3V3 rail at U4 output; check no short across the
   battery terminals (J1) — this board previously had a BATT_P/BATT_N short that is now
   fixed, so verify 0 Ω is **not** present between J1 pins.
2. Charge path: apply battery, confirm TP4056 (U2) charge LED (LED_CHG1) behaves.
3. Fit U1, flash firmware, verify OLED, buttons SW1–6, RTC, GPS over their buses.
4. Only then connect the motor to J_MOTOR_PWR / J_MOTOR_CTRL.

---

## 6. Cost estimate

| Item | Est. Cost |
|---|---|
| 10 pcs bare PCBs (JLCPCB, 4-layer, HASL) | ~$10-12 |
| SMT stencil (JLCPCB, bottom, ≤100mm) | $3 |
| Components from LCSC (18 BOM lines, all parts) | ~$15-25 |
| Global Standard Direct Line shipping | ~$12-15 |
| Customs/duties (DAP) | ~$4-8 |
| Solder paste + flux (if not already stocked) | ~$10-18 |
| **Total (with paste)** | **~$54-81** |
| **Total (paste already stocked)** | **~$44-63** |

Compare to JLCPCB full assembly + DHL: **~$109-119** — saves **~$50-75**.

---

## File manifest (in `fabrication/`)
- `autofeeder-gerbers.zip` — bare-board fab (§1)
- `autofeeder-lcsc-bom.csv` — **LCSC component ordering BOM** (§3)
- `autofeeder-bom-smt.csv` / `autofeeder-cpl-smt.csv` — SMT placement reference
- `autofeeder-bom.csv` — full curated BOM incl. hand/customer parts (reference)
- `autofeeder-cpl.csv` — full placement incl. hand parts (reference)
- `gerbers/` — individual gerber + drill + job files
