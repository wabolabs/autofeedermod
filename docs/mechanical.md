# Mechanical Specification — Form-Factor Fit

The new ESP32-C6 board is a **drop-in replacement** for the original **WSG-V1.7** board
and must fit the **existing fascia unchanged**. The electronics are redesigned, but every
mechanical interface below must match the original so it seats in the same enclosure and
lines up with the fascia's button openings and display window.

> **Status: MEASUREMENTS APPLIED (2026-06-02).** Caliper values below are now baked into
> `hardware/kicad/autofeeder_pcb.py` (board outline, `PLACEMENT`, `MOUNTING_HOLES`). The board
> generates, routes (0 unconnected), and exports fab files cleanly.
>
> DRC: **0 violations (all severities), 0 unconnected.** Button↔hole courtyard and USB-C
> `starved_thermal` errors fixed (tight-courtyard NPTH mounting-hole footprint; solid zone
> connection on the USB-C GND pads). Silkscreen warnings fixed too: overlapping reference
> labels hidden on silk (kept on Fab) and redundant edge-connector silk outlines removed.
>
> **IMPORTANT: ESP32-C6-Zero Programming.** The Waveshare module is **hand-socketed** on 2×9 2.54mm pin headers. The module's **onboard USB-C port** (tucked inside the enclosure) is the ONLY way to program the firmware — open the enclosure, connect USB-C, and use `esptool.py` or the Arduino IDE. The main board's USB-C (J3) is for charging only. The UART pins (TX/RX) are repurposed for motor control on the main board and are NOT connected to the programming header (J4). This choice prioritizes board density; reflashing requires a few minutes of enclosure access.
>
> Remaining JST connector center positions (§3) are still `???` — they were placed along the
> right edge (precision not required per measurement notes); refine if a specific cable exit is needed.

Datum: bottom-left corner of the board = origin (0, 0). X → right, Y → up
(KiCad uses Y-down internally; the script handles the flip).

## 1. Board outline
| Spec | Value | Notes |
|------|-------|-------|
| Width (X)  | 56 mm | |
| Height (Y) | 54 mm | |
| Corner radius | 0 mm | original corners look slightly rounded |
| PCB thickness | 1.6 mm | standard FR4, 2-layer |
| Any non-rectangular notches/cutouts? | no | e.g. tabs, edge cutouts |

## 2. Mounting holes
| Hole | X (mm) | Y (mm) | Drill Ø (mm) | Pad/annular |
|------|--------|--------|--------------|-------------|
| H1 | 7 | 48 | 2 | |
| H2 | 7 | 11 | 2 | |
| H3 | 48 | 48 | 2 | |
| H4 | 48 | 11 | 2` | |
(Original appears to have holes near the corners — confirm count and positions.)

## 3. Connectors (positions along board edges)
| Ref | Part | Edge | Center X (mm) | Center Y (mm) | Overhang past edge (mm) |
|-----|------|------|---------------|---------------|-------------------------|
| J3  | USB-C | bottom | 30 | 2.5? | 1 |
| J4 (motor 电机) | JST-XH 2P | right (doesn't need precision as long as i's along that edge | `???` | `???` | `???` |
| J1 (battery 电池) | JST-XH 2P | right (doesn't need precision as long as it's along that edge)  | `???` | `???` | `???` |

## 4. Buttons (centers — must align with fascia openings)
Original silkscreen: KEY1/KEY2/KEY3 across the top, KEY4/KEY5/KEY6 across the bottom.
| Button | Original label | Center X (mm) | Center Y (mm) |
|--------|----------------|---------------|---------------|
| SW1 | KEY1 | 12 | 48 |
| SW2 | KEY2 | 28 | 48 |
| SW3 | KEY3 | 42.5 | 48 |
| SW4 | KEY4 | 12 | 11 |
| SW5 | KEY5 | 28 | 11 |
| SW6 | KEY6 | 42.5 | 11 |

## 5. Display window
The original is a segment LCD; the replacement is an SSD1306 OLED. The OLED **active area**
must sit behind the fascia's existing window.
| Spec | Value | Notes |
|------|-------|-------|
| Fascia window center X | 28 mm | |
| Fascia window center Y | 30 mm | |
| Fascia window width  | 44 mm | |
| Fascia window height | 26 mm | |
| Display PCB keep-out (if OLED module) | not sure | OLED breakout outline if used |

## 6. Fascia photos
Reference photos are in [reference/](reference/):
- `fascia_front_ruler.jpg` — membrane overlay (button icons + window)
- `fascia_frame_ruler.jpg` — 3D-printed frame (screw bosses, button holes, window rim)
- `board_front_ruler.jpg` / `board_back_ruler.jpg` — original WSG-V1.7 board with ruler
- `originalboard_front.jpeg` / `originalboard_back.jpeg` — original board, close-up
