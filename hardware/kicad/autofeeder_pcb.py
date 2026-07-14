"""Autofeeder PCB pipeline: create, populate, autoroute, pour, verify, export.

Usage:
    cd autofeedermod
    PYTHONPATH=tools python3 hardware/kicad/autofeeder_pcb.py

Requires: KiCad 9.0+, kicad-cli, freerouting on PATH
"""

from __future__ import annotations

import math
import re
import subprocess
import sys
import json
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from sch_gen.sexp import parse

BASE = REPO_ROOT / "hardware/kicad"
SCH = BASE / "autofeeder.kicad_sch"
PRO = BASE / "autofeeder.kicad_pro"
PCB = BASE / "autofeeder.kicad_pcb"
FAB = REPO_ROOT / "fabrication"
NET = FAB / "autofeeder.net"
DSN = FAB / "autofeeder.dsn"
SES = FAB / "autofeeder.ses"

# Board outline (mm) — 56mm wide × 54mm tall
X0, Y0, X1, Y1 = 0.0, 0.0, 56.0, 54.0

# Footprint directories (project lib first, then KiCad stock)
FP_DIRS = [REPO_ROOT / "hardware/footprints", Path("/usr/share/kicad/footprints")]

# Override placements (x, y, rot) — KiCad coords: Y+ down, (0,0) top-left, board 56×54mm.
# Fascia-critical positions (buttons, display, mounting holes) come from real caliper
# measurements in docs/mechanical.md, which use Y+ UP from the bottom-left. Convert with
# kicad_y = BOARD_H - user_y (BOARD_H = 54). Buttons/display sit on the FRONT (fascia) side.
PLACEMENT: dict[str, tuple[float, float, float]] = {
    # === FRONT SIDE — display + buttons only ===
    # Display: footprint origin = active-area center, placed at the fascia window center
    # (user (28,30) -> kicad (28,24)).
    "DISP1":      (28.00, 24.00, 0),

    # Buttons: measured centers. KEY1-3 top (user y=48 -> kicad 6); KEY4-6 bottom (user y=11 -> 43).
    "SW1_POWER1": (12.00,  6.00, 0),   # KEY1 top-left
    "SW2_TIMER1": (28.00,  6.00, 0),   # KEY2 top-mid
    "SW3_MANUAL1":(42.50,  6.00, 0),   # KEY3 top-right

    "SW4_SETTINGS1": (12.00, 43.00, 0),  # KEY4 bottom-left
    "SW5_UP1":       (28.00, 43.00, 0),  # KEY5 bottom-mid
    "SW6_DOWN1":     (42.50, 43.00, 0),  # KEY6 bottom-right

    # === BACK SIDE ===
    # Connectors on board edges (match original: USB-C bottom, JSTs + prog header on right edge).
    "J3":         (30.00, 51.50, 0),   # USB-C, bottom edge (user y=2.5 -> kicad 51.5)
    "J1":         (52.00, 34.00, 90),  # battery JST, right edge, facing left (inward)
    "J_MOTOR_PWR1": (52.00, 24.00, 90), # MX1508 power (BATT_PROT/GND), right edge, above BATT
    "J_MOTOR_CTRL1":(52.00, 14.00, 90), # MX1508 control (IN1/IN2), right edge, above J_MOTOR_PWR
    "J4":         (53.00, 39.00, 0),   # prog header, right edge below JSTs (like original J11)

    # Power section — left column
    "F1":         ( 7.00, 13.00, 0),
    "D1":         (16.00, 18.50, 0),   # moved right so anode PTH (pad2 at x-10.16) lands at x≈5.84mm, inside board; Y offset clears U2 courtyard
    "U2":         (14.00, 14.00, 0),
    "LED_CHG1":   ( 8.00, 22.00, 0),
    "R2_C1":      (16.00, 22.00, 0),
    "U3":         (10.00, 28.00, 0),   # DW01A SOT-23-6
    "U8":         (19.00, 35.00, 0),   # FS8205A SOT-23-6
    "U4":         (13.00, 36.00, 0),   # TPS63031DSKR WSON-10 (fixed 3.3V)
    "L1":         ( 6.00, 36.00, 0),   # 4.7uH inductor, L1-to-L2
    "C4":         (12.00, 42.00, 0),   # input cap, moved right to clear H2 at (7,43)
    "C5":         (20.00, 42.00, 0),   # output cap
    "R3":         (11.00, 46.00, 0),
    "R4":         (11.00, 50.00, 0),

    # MCU — ESP32-C6-Zero (23×18mm footprint, center at 36,18)
    "U1":         (28.00, 18.00, 0),   # Zero: sweet spot — L-rail X=36.89 (>DISP right pad 35.62), R-rail X=19.11 (<DISP left pad 20.38)
    "C1":         (40.00, 23.00, 0),   # near U1 3V3 pin (board X~36.89 post-flip), outside U1 courtyard
    "C2":         (40.00, 26.00, 0),   # near U1 3V3 pin

    "C3":         (35.00, 33.00, 0),   # display decoupling — moved to clear U1 bottom pad19 at (35.62,30.7)

    # Motor driver

    # CAN section — relocated inward (center-bottom) to free the right edge for the JSTs
    "C6":         (46.00, 40.00, 0),   # CAN decoupling — right of U6, clears U6, H4 courtyards
    "U6":         (41.00, 45.00, 0),
    "R5":         (48.00, 46.00, 0),
    "R6":         (42.00, 49.00, 0),
    "R10":        (46.00, 50.00, 0),

    "R13":        (44.00,  8.00, 0),   # DISP_RST pullup, near DISP1 header

    "R_CC1":      (28.00,  3.50, 0),
    "R_CC2":      (34.00,  3.50, 0),

    # RTC and GPS module headers — back side, in free areas
    "J_RTC1":     (42.00, 30.00, 0),  # DS3231 module header (right of center, clear of SW5 at X=28)
    "J_GPS1":     (44.00, 14.00, 0),  # GPS module header (top-right)
    "WABO_LOGO1": (30.00, 36.00, 0),  # Wabo Labs logo silkscreen (back side, centered below ESP32-C6-Zero)
}

# Mounting holes (non-plated). Measured in docs/mechanical.md (Y-up); converted to KiCad Y-down.
# Ø2mm measured -> 2.1mm NPTH footprint (clears M2). (x, y) KiCad mm.
MOUNTING_HOLE_FP = "autofeeder:MountingHole_2.1mm_NPTH"
MOUNTING_HOLES: dict[str, tuple[float, float]] = {
    "H1": ( 7.00,  6.00),   # user (7,48)
    "H2": ( 7.00, 43.00),   # user (7,11)
    "H3": (48.00,  6.00),   # user (48,48)
    "H4": (48.00, 43.00),   # user (48,11)
}

# Refs placed on back side (B.Cu) — everything except display + buttons
BACK_COMPONENTS: set[str] = {
    ref for ref in PLACEMENT
    if not ref.startswith("SW") and ref != "DISP1"
}


def _fp_name(node) -> str:
    """Extract footprint string from a netlist comp node."""
    for c in node.children:
        if isinstance(c, type(node)) and c.head == "footprint" and c.children:
            return str(c.children[0]).strip('"')
    return ""


def _value_name(node) -> str:
    """Extract the component value (e.g. '100nF') from a netlist comp node."""
    for c in node.children:
        if isinstance(c, type(node)) and c.head == "value" and c.children:
            return str(c.children[0]).strip('"')
    return ""


def _ref_name(node) -> str:
    """Extract reference from a netlist comp node."""
    for c in node.children:
        if isinstance(c, type(node)) and c.head == "ref" and c.children:
            return str(c.children[0]).strip('"')
    return ""


def create_board() -> None:
    """Create a fresh 4-layer board with the 56×54mm outline.

    4 layers (F.Cu, In1.Cu, In2.Cu, B.Cu) — the 2-layer version could not route the
    dense U3/U4/U8 protection+WSON corner and the USB-C cluster (BATT_N, BATT_PROT, CC2,
    VBUS stayed stuck). The two extra layers give Freerouting the capacity it needs; GND
    is poured on all four and tied together with stitching vias."""
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    # Set default netclass clearance to 0.15mm — within JLCPCB's 0.127mm capability and
    # needed because the Zero socket rails are 1.27mm from the OLED header outer pads.
    bds = board.GetDesignSettings()
    nc = bds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(pcbnew.FromMM(0.15))
    nc.SetTrackWidth(pcbnew.FromMM(0.2))
    nc.SetViaDiameter(pcbnew.FromMM(0.6))
    nc.SetViaDrill(pcbnew.FromMM(0.3))
    pts = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1), (X0, Y0)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        seg.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.1))
        board.Add(seg)
    PCB.parent.mkdir(parents=True, exist_ok=True)
    board.Save(str(PCB))
    print(f"  created board {X1-X0:.0f} x {Y1-Y0:.0f} mm")


def _place_mounting_holes(board) -> None:
    """Add non-plated mounting holes at measured fascia positions."""
    res = _resolve_fp(MOUNTING_HOLE_FP)
    if res is None:
        print(f"    WARN: mounting-hole footprint {MOUNTING_HOLE_FP} not found; skipping")
        return
    lib_dir, fp_name = res
    for ref, (x, y) in MOUNTING_HOLES.items():
        fp = pcbnew.FootprintLoad(str(lib_dir), fp_name)
        if fp is None:
            print(f"    WARN: failed to load {MOUNTING_HOLE_FP} for {ref}")
            continue
        fp.SetReference(ref)
        fp.Reference().SetVisible(False)  # no silk label needed for mounting holes
        fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        board.Add(fp)


def _resolve_fp(lib_id: str):
    """Find a footprint file. Returns (lib_dir, fp_name) or None."""
    if ":" not in lib_id:
        return None
    lib, name = lib_id.split(":", 1)
    for base in FP_DIRS:
        cand = base / f"{lib}.pretty" / f"{name}.kicad_mod"
        if cand.exists():
            return base / f"{lib}.pretty", name
    return None


def populate() -> None:
    """Export netlist, load PCB, place footprints with nets."""
    FAB.mkdir(parents=True, exist_ok=True)
    # Export netlist
    subprocess.run(
        ["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr",
         "-o", str(NET), str(SCH)],
        check=True, capture_output=True, timeout=60,
    )
    print(f"  netlist exported ({NET.stat().st_size}b)")

    root = parse(NET.read_text())

    # Build pin -> net mapping
    pin_to_net: dict[tuple[str, str], str] = {}
    for net in root.find("nets").find_all("net"):
        name_node = net.find("name")
        net_name = str(name_node.children[0]) if name_node and name_node.children else ""
        for node in net.find_all("node"):
            ref = ""; pin = ""
            for c in node.children:
                if isinstance(c, type(node)):
                    if c.head == "ref" and c.children:
                        ref = str(c.children[0]).strip('"')
                    elif c.head == "pin" and c.children:
                        pin = str(c.children[0])
            if ref and pin:
                pin_to_net[(ref, pin)] = net_name

    # Load board and clear footprints
    board = pcbnew.LoadBoard(str(PCB))
    board.DeleteAllFootprints()
    _place_mounting_holes(board)

    # Register nets
    for name in sorted({n for n in pin_to_net.values() if n}):
        if board.FindNet(name) is None:
            board.Add(pcbnew.NETINFO_ITEM(board, name))

    # Get components from netlist
    comps_node = root.find("components")
    comps = []
    if comps_node:
        for c in comps_node.find_all("comp"):
            ref = _ref_name(c)
            fp_str = _fp_name(c)
            if ref and fp_str:
                comps.append((ref, fp_str, _value_name(c)))

    placed = 0
    errors = []
    for ref, fp_id, value in comps:
        res = _resolve_fp(fp_id)
        if res is None:
            errors.append(f"    SKIP {ref}: footprint {fp_id} not found")
            continue
        lib_dir, fp_name = res
        try:
            fp = pcbnew.FootprintLoad(str(lib_dir), fp_name)
        except Exception as e:
            errors.append(f"    SKIP {ref}: {e}")
            continue
        if fp is None:
            errors.append(f"    SKIP {ref}: footprint load returned None")
            continue
        fp.SetReference(ref)
        # Carry the schematic value + full lib:name FPID onto the footprint. Without this
        # the footprint keeps the library's default Value (the footprint name) and a bare
        # FPID, which makes every component fail schematic-parity on value/footprint fields
        # (cosmetic, but it makes the PCB unreadable and diverges from the schematic).
        if value:
            fp.SetValue(value)
        try:
            fp.SetFPIDAsString(fp_id)
        except Exception:
            pass
        x, y, rot = PLACEMENT.get(ref, (28, 27, 0))
        fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            nn = pin_to_net.get((ref, pad.GetNumber()))
            if nn:
                net = board.FindNet(nn)
                if net is not None:
                    pad.SetNet(net)
        board.Add(fp)
        # Flip to back side AFTER adding to board
        if ref in BACK_COMPONENTS:
            fp.Flip(fp.GetPosition(), False)
        placed += 1

    # Place silkscreen-only logo (not in schematic netlist, only in PLACEMENT)
    logo_ref = "WABO_LOGO1"
    if logo_ref in PLACEMENT:
        fp_tup = _resolve_fp("autofeeder:Wabo_Labs_Logo")
        if fp_tup is None:
            print("    WARN: Wabo_Labs_Logo footprint not found; skipping")
        else:
            lib_dir, fp_name = fp_tup
            fp = pcbnew.FootprintLoad(str(lib_dir), fp_name)
            if fp is None:
                print(f"    WARN: failed to load Wabo_Labs_Logo footprint")
            else:
                x, y, rot = PLACEMENT[logo_ref]
                fp.SetReference(logo_ref)
                fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
                if rot:
                    fp.SetOrientationDegrees(rot)
                board.Add(fp)
                if logo_ref in BACK_COMPONENTS:
                    fp.Flip(fp.GetPosition(), False)
                placed += 1

    board.Save(str(PCB))
    print(f"  placed {placed} footprints")
    if errors:
        for e in errors:
            print(e)


def add_silkscreen_labels() -> None:
    """Add silkscreen text labels for connectors, placed above each connector in the
    connector's own (rotated) reference frame and on the connector's own copper side."""
    board = pcbnew.LoadBoard(str(PCB))

    import math

    # Connector labels: ref -> text. Offset is "above" in the connector's local frame
    # (i.e. perpendicular to the JST insertion axis), transformed by the footprint's
    # actual orientation so it tracks the connector when it is rotated/flipped.
    labels = {"J1": "BATT", "J_MOTOR_PWR1": "PWR", "J_MOTOR_CTRL1": "CTRL"}
    local_above_mm = 4.5  # distance above the connector body in its local frame (clears the JST body)

    for ref, text in labels.items():
        fp = board.FindFootprintByReference(ref)
        if not fp:
            continue

        pos = fp.GetPosition()
        flipped = fp.IsFlipped()
        # Footprint orientation in degrees (KiCad EDA_ANGLE -> tenths internally)
        fp_angle = fp.GetOrientationDegrees()

        # "Above" in the connector's local frame is local -Y. Rotate that vector by the
        # footprint orientation to get the board-space offset so the label always sits
        # above the connector relative to the angle it is plugged in.
        theta = math.radians(fp_angle)
        # local (0, -above) rotated by theta:
        dx = local_above_mm * math.sin(theta)
        dy = -local_above_mm * math.cos(theta)
        # On the back, X is mirrored relative to the front view.
        if flipped:
            dx = -dx

        x_mm = pcbnew.ToMM(pos.x) + dx
        y_mm = pcbnew.ToMM(pos.y) + dy

        text_obj = pcbnew.PCB_TEXT(board)
        text_obj.SetText(text)
        text_obj.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))
        # Put the label on the same copper side as the connector.
        text_obj.SetLayer(pcbnew.B_SilkS if flipped else pcbnew.F_SilkS)
        if flipped:
            text_obj.SetMirrored(True)
        text_obj.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2)))
        text_obj.SetTextThickness(pcbnew.FromMM(0.15))
        # Read along the connector's axis (match its orientation).
        text_obj.SetTextAngle(pcbnew.EDA_ANGLE(int(round(fp_angle * 10))))
        text_obj.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        text_obj.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        board.Add(text_obj)

    board.Save(str(PCB))


def _pre_route_vbus(board) -> None:
    """Stitch J3 VBUS pad groups (A4/B9 at X=32.45 and A9/B4 at X=27.55) with
    a track above the pad row.  The autorouter struggles to route through the
    USB-C connector's dense 0.3/0.6 mm pad column, so we give it a head start."""
    b_cu = pcbnew.B_Cu
    vbus = board.FindNet("/VBUS") or board.FindNet("VBUS")
    if vbus is None:
        return

    def _t(x1, y1, x2, y2):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
        t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
        t.SetLayer(b_cu)
        t.SetWidth(pcbnew.FromMM(0.3))
        t.SetNet(vbus)
        board.Add(t)

    # Right VBUS pad up, then left+right stitched above the pad row (Y=46.0 is
    # safely above the top of the pads at Y≈46.73 but below the J3 courtyard
    # at Y≈46.23; tracks may cross courtyard boundaries to reach pads).
    _t(32.45, 47.455, 32.45, 46.3)
    _t(27.55, 47.455, 27.55, 46.3)
    _t(27.55, 46.3, 32.45, 46.3)
    print("  pre-routed VBUS stitch across J3 pads")


def _pre_route_l2_node(board) -> None:
    """Pre-route L2_NODE. VCC_3V3 will be autorouted around it."""
    net = board.FindNet("/L2_NODE") or board.FindNet("L2_NODE")
    if net is None:
        return
    b_cu = pcbnew.B_Cu
    w = pcbnew.FromMM(0.3)

    def _seg(x1, y1, x2, y2):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
        t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
        t.SetLayer(b_cu)
        t.SetWidth(w)
        t.SetNet(net)
        board.Add(t)

    # B.Cu: L1 pad 2 → up → left to the board's left edge → down → right along the
    # bottom → straight up in the U4/U8 gap (x=15.5) → left into U4-2 at y=35.5.
    # A straight vertical (no diagonal) keeps a solid 0.4mm off the OC_GATE track in
    # the same narrow gap. The final y=35.5 entry stays equidistant (0.225mm) from
    # U4-1 VCC_3V3 (y=35.00) and U4-3 GND (y=36.00) on the 0.5mm-pitch WSON edge —
    # a diagonal entry grazes U4-1.
    _seg(4.9375, 36.0, 4.9375, 33.0)
    _seg(4.9375, 33.0, 2.0, 33.0)
    _seg(2.0, 33.0, 2.0, 40.5)
    _seg(2.0, 40.5, 15.5, 40.5)
    _seg(15.5, 40.5, 15.5, 35.5)
    _seg(15.5, 35.5, 14.21, 35.5)
    print("  pre-routed L2_NODE: L1-2 → U4-2")


def _pre_route_oc_gate(board) -> None:
    net = board.FindNet("/OC_GATE") or board.FindNet("OC_GATE")
    if net is None:
        return
    b_cu = pcbnew.B_Cu
    w = pcbnew.FromMM(0.3)

    def _seg(x1, y1, x2, y2):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
        t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
        t.SetLayer(b_cu)
        t.SetWidth(w)
        t.SetNet(net)
        board.Add(t)

    # U3-3 (11.35,28.95) → down clear of U1 → right below U1 → down in the U4/U8
    # gap → into U8-4 from the left. Stays x<=16.35 to clear U8.6/U8.5 (left edge
    # 16.87) and x>=15.8 to clear U4 (right pad edge 14.62).
    _seg(11.35, 28.95, 11.35, 32.5)
    _seg(11.35, 32.5, 16.2, 32.5)
    _seg(16.2, 32.5, 16.2, 35.95)
    _seg(16.2, 35.95, 17.65, 35.95)
    print("  pre-routed OC_GATE: U3-3 → U8-4")


def _pre_route_od_gate(board) -> None:
    net = board.FindNet("/OD_GATE") or board.FindNet("OD_GATE")
    if net is None:
        return
    b_cu = pcbnew.B_Cu
    w = pcbnew.FromMM(0.3)

    def _seg(x1, y1, x2, y2):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
        t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
        t.SetLayer(b_cu)
        t.SetWidth(w)
        t.SetNet(net)
        board.Add(t)

    # U3-1 (11.35,27.05) → up over U3 pad row → right, stopping at x=18.0 (before the
    # U1 right rail at x=19.11) → down left of the rail & BAT_MON (20.38,30.70) to below
    # U1 → right → down into U8-1. Keeps >=0.15mm off U1.11/U1.10/U1.25.
    _seg(11.35, 27.05, 11.35, 26.2)
    _seg(11.35, 26.2, 18.0, 26.2)
    _seg(18.0, 26.2, 18.0, 32.5)
    _seg(18.0, 32.5, 20.35, 32.5)
    _seg(20.35, 32.5, 20.35, 34.05)
    print("  pre-routed OD_GATE: U3-1 → U8-1")


def _pre_route_l1_node(board) -> None:
    """L1-1 (7.0625,36.0) → U4-4 (14.2125,36.5). Freerouting can't finish this into the
    dense TPS63031 WSON, so route it explicitly: down from L1, right along the bottom,
    then up the U4/U8 gap in the slot inside the L2_NODE pre-route (x=14.95, between
    U4's right pad edge 14.62 and L2's vertical at x=15.5) and left into pad 4 at y=36.5
    (0.225mm off U4-3 GND and U4-5 BATT_PROT)."""
    net = board.FindNet("/L1_NODE") or board.FindNet("L1_NODE")
    if net is None:
        return
    b_cu = pcbnew.B_Cu
    w = pcbnew.FromMM(0.3)

    def _seg(x1, y1, x2, y2):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
        t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
        t.SetLayer(b_cu)
        t.SetWidth(w)
        t.SetNet(net)
        board.Add(t)

    _seg(7.0625, 36.0, 7.0625, 39.0)
    _seg(7.0625, 39.0, 14.95, 39.0)
    _seg(14.95, 39.0, 14.95, 36.5)
    _seg(14.95, 36.5, 14.2125, 36.5)
    print("  pre-routed L1_NODE: L1-1 → U4-4")


def _pre_route_u4_gnd(board) -> None:
    """U4 (WSON-10) left GND pads 7 (11.7875,36.5) and 9 (11.7875,35.5) sit in a pocket
    walled off from the GND pour by the adjacent BATT_PROT/VCC_3V3 pads (0.5mm pitch), so
    their local fill becomes an isolated island. Pull each straight out to the left with a
    short GND stub into the open main pour, staying 0.225mm off the y-adjacent pads."""
    net = board.FindNet("GND")
    if net is None:
        return
    b_cu = pcbnew.B_Cu
    w = pcbnew.FromMM(0.3)

    def _seg(x1, y1, x2, y2):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
        t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
        t.SetLayer(b_cu)
        t.SetWidth(w)
        t.SetNet(net)
        board.Add(t)

    # Pull pad 9 straight left into the large left-side pour, and pad 7 left then up to
    # the same point (its own y=36.5 level is a separate pocket below that pour). The
    # stitching vias later tie this pour region to the F.Cu ground backbone.
    _seg(11.7875, 35.5, 9.5, 35.5)   # pad 9 → left pour
    _seg(11.7875, 36.5, 9.5, 36.5)   # pad 7 → left
    _seg(9.5, 36.5, 9.5, 35.5)       # → up into the pour with pad 9
    print("  pre-routed U4 GND: pads 7,9 → left pour")


def _pre_route_batt_n(board) -> None:
    """Route the full BATT_N net on B.Cu + F.Cu.

    Without this, Freerouting leaves BATT_N split into disconnected islands —
    it can't route through the OC_GATE / OD_GATE corridor on B.Cu, and the
    long F.Cu chain from J1 doesn't complete within 15 passes.

    B.Cu segments:
      U3 pad 6 (8.65,27.05) → U3 pad 2 (11.35,28) → right → down through
      OC/OD gate gap → right above U8 → down right of U8 → U8 pad 2 (20.35,35)
    F.Cu segments:
      J1 pad 2 (52,31.5) → down → right → diagonal → via (21.5561,35.4863)
    """
    net = board.FindNet("/BATT_N") or board.FindNet("BATT_N")
    if net is None:
        return
    w = pcbnew.FromMM(0.3)

    def _seg(x1, y1, x2, y2, layer=pcbnew.B_Cu):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
        t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
        t.SetLayer(layer)
        t.SetWidth(w)
        t.SetNet(net)
        board.Add(t)

    # B.Cu: U3 pad 6 → U3 pad 2 → U8 pad 2.
    # The old path ran right at y=33.3 straight to x=22, crossing OD_GATE's x=20.35
    # vertical (y32.5-34.05) at (20.35,33.3) — a hard OD_GATE/BATT_N short on B.Cu.
    # Keep the high path (so the GND pour still flows through the U8 inter-column gap and
    # feeds the U8-5 GND pocket) but hop OVER the OD_GATE vertical on F.Cu for a short
    # span with two through-vias. The hop zone (x19.5..21.2, y33.3) is clear on F/In1/In2.
    _seg(8.65, 27.05, 11.35, 28.0)     # U3 pad 6 → U3 pad 2
    _seg(11.35, 28.0, 17.0, 28.0)      # right from U3 pad 2
    _seg(17.0, 28.0, 17.0, 33.3)       # down through OC/OD gate gap
    _seg(17.0, 33.3, 19.5, 33.3)       # right on B.Cu, stop before OD_GATE (x=20.35)
    _seg(19.5, 33.3, 21.2, 33.3, pcbnew.F_Cu)  # F.Cu hop over the OD_GATE B.Cu vertical
    _seg(21.2, 33.3, 22.0, 33.3)       # back on B.Cu, past OD_GATE
    _seg(22.0, 33.3, 22.0, 35.0)       # down right of U8
    _seg(22.0, 35.0, 20.35, 35.0)      # left into U8 pad 2
    for _hx in (19.5, 21.2):           # B.Cu <-> F.Cu transition vias for the hop
        _hv = pcbnew.PCB_VIA(board)
        _hv.SetPosition(pcbnew.VECTOR2I_MM(_hx, 33.3))
        _hv.SetDrill(pcbnew.FromMM(0.3))
        _hv.SetWidth(pcbnew.FromMM(0.6))
        _hv.SetNet(net)
        _hv.SetViaType(pcbnew.VIATYPE_THROUGH)
        board.Add(_hv)
    # B.Cu: via → U8 pad 2 (connects the J1 F.Cu chain to U8 cluster)
    _seg(21.5561, 35.4863, 20.35, 35.0)
    # F.Cu: J1 pad 2 → via (connects to U8 B.Cu cluster).
    # J1 pad 1 (BATT_P) sits at (52,34) spanning x51-53 / y33.15-34.85. Exit pad 2
    # (52,31.5) straight left at y=31.5 (still in pad 2's own y-band), then drop down
    # at x=49.69 — left of pad 1's x=51 edge — so the trace never grazes BATT_P. The
    # old diagonal (52,32.6)->(49.69,33.81) clipped pad 1's top-left corner (a hard
    # BATT_N/BATT_P short + solder-mask bridge).
    _seg(52.0, 31.5, 49.69, 31.5, pcbnew.F_Cu)
    _seg(49.69, 31.5, 49.69, 33.81, pcbnew.F_Cu)
    _seg(49.69, 33.81, 23.2324, 33.81, pcbnew.F_Cu)
    _seg(23.2324, 33.81, 21.5561, 35.4863, pcbnew.F_Cu)
    # Via at the F.Cu/B.Cu transition — connects the J1 F.Cu chain to the
    # U8 B.Cu cluster (U8 pad 2 is 1.14mm away via existing B.Cu tracks).
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I_MM(21.5561, 35.4863))
    via.SetDrill(pcbnew.FromMM(0.3))
    via.SetWidth(pcbnew.FromMM(0.6))
    via.SetNet(net)
    via.SetViaType(pcbnew.VIATYPE_THROUGH)
    board.Add(via)
    print("  pre-routed BATT_N: U3-6 → U3-2 → U8-2; J1 → via")


def autoroute() -> None:
    """Export DSN, run Freerouting, import SES."""
    board = pcbnew.LoadBoard(str(PCB))
    # Clear all tracks and zones
    for t in list(board.GetTracks()):
        try:
            board.RemoveNative(t)
        except:
            pass
    for z in list(board.Zones()):
        try:
            board.RemoveNative(z)
        except:
            pass
    # _pre_route_vbus was a 2-layer hack to force VBUS through J3's dense pad column;
    # on 4 layers it locks the access and leaves VBUS unrouted. Let the router handle it.
    _pre_route_l2_node(board)
    _pre_route_oc_gate(board)
    _pre_route_od_gate(board)
    _pre_route_l1_node(board)
    _pre_route_batt_n(board)
    # With U4's EP tied to GND and inner GND planes, the WSON GND pads via straight down;
    # the old lateral GND escape traces just boxed in U4.8 (BATT_PROT), so they're dropped.
    board.Save(str(PCB))

    if not pcbnew.ExportSpecctraDSN(board, str(DSN)):
        raise RuntimeError("ExportSpecctraDSN failed")
    print(f"  exported DSN ({DSN.stat().st_size}b); routing...")

    subprocess.run(
        ["java", "-jar", "/opt/freerouting.jar", "-de", str(DSN), "-do", str(SES),
         "-da", "-mp", "15"],
        capture_output=True, text=True, timeout=300,
    )
    if not SES.exists():
        raise RuntimeError("Freerouting produced no SES")
    print(f"  routed -> {SES.stat().st_size}b SES")


def _deduplicate_prerouted(board) -> None:
    """Remove exact duplicate track segments left by the SES round-trip (pre-routed
    segments can come back doubled). Geometry-keyed over every net, so it covers all
    pre-routed nets (L2_NODE, OC_GATE, OD_GATE, L1_NODE, GND stubs) without hardcoding
    net codes, which are not stable."""
    seen = {}
    for t in list(board.GetTracks()):
        if t.Type() != pcbnew.PCB_TRACE_T:
            continue
        s = t.GetStart(); e = t.GetEnd()
        pts = tuple(sorted([(s.x, s.y), (e.x, e.y)]))
        key = (t.GetNetCode(), pts, t.GetLayer())
        if key in seen:
            try: board.RemoveNative(t)
            except: pass
        else:
            seen[key] = True


def finish() -> None:
    """Import routes, pour GND on both layers, save."""
    board = pcbnew.LoadBoard(str(PCB))
    if not pcbnew.ImportSpecctraSES(board, str(SES)):
        raise RuntimeError("ImportSpecctraSES failed")
    _deduplicate_prerouted(board)
    segs = sum(1 for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T)
    vias = sum(1 for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T)
    print(f"  imported {segs} segments + {vias} vias")

    pour_ground(board)
    add_stitching_vias(board)
    board.Save(str(PCB))
    cleanup_silk()


def add_stitching_vias(board) -> None:
    """Tie the per-layer GND pours together with through stitching vias so the ground
    net is one connected plane (each layer's pour gets chopped into islands by signal
    traces, and a through-via must clear the traces on every layer it passes).

    A via is placed only where its whole annulus + clearance ring (radius 0.5mm) lies
    inside the GND fill on EVERY GND layer — since each fill already respects clearance
    from that layer's non-GND pads/tracks, that guarantees the through-via cannot short
    anything, without per-obstacle distance math. Zones are refilled afterward."""
    gnd = board.FindNet("GND")
    if gnd is None:
        return
    fills = []
    for z in board.Zones():
        if z.GetNetname() == "GND":
            fills.append(z.GetFilledPolysList(z.GetLayer()))
    if not fills:
        return

    r = pcbnew.FromMM(0.5)   # via radius (0.3) + clearance margin (0.2)
    offs = [(0, 0)] + [(int(r * math.cos(a)), int(r * math.sin(a)))
                       for a in [i * math.pi / 4 for i in range(8)]]

    # Keep the via drill away from other drilled holes (min hole-to-hole). A stitch via's
    # hole (0.3mm) must sit >= 0.3mm edge-to-edge from any pad hole; store (x, y, keepout)
    # where keepout = via_hole_r (0.15) + pad_hole_r + 0.3mm margin.
    via_hole_r = pcbnew.FromMM(0.15)
    holes = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            ds = pad.GetDrillSize()
            if ds.x > 0:
                pos = pad.GetPosition()
                keep = via_hole_r + ds.x // 2 + pcbnew.FromMM(0.3)
                holes.append((pos.x, pos.y, keep))

    def _clear(px, py):
        for hx, hy, keep in holes:
            if abs(px - hx) < keep and abs(py - hy) < keep:
                if (px - hx) ** 2 + (py - hy) ** 2 < keep * keep:
                    return False
        for dx, dy in offs:
            q = pcbnew.VECTOR2I(px + dx, py + dy)
            if not all(f.Contains(q) for f in fills):
                return False
        return True

    bb = board.GetBoardEdgesBoundingBox()
    step = pcbnew.FromMM(2.2)
    placed = 0
    y = bb.GetTop()
    while y <= bb.GetBottom():
        x = bb.GetLeft()
        while x <= bb.GetRight():
            if _clear(x, y):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(x, y))
                v.SetDrill(pcbnew.FromMM(0.3))
                v.SetWidth(pcbnew.FromMM(0.6))
                v.SetNet(gnd)
                board.Add(v)
                placed += 1
            x += step
        y += step
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"  stitched GND with {placed} vias")


# Silkscreen reference labels that overlap copper or each other in the dense back-side
# cluster — hidden on silk (they remain on the Fab layer for assembly).
SILK_HIDE_REF = {"R5", "R6", "R7", "LED_STATUS1",
                 # dense back-side cluster — ref labels overlapping copper or each other
                 "U1", "U2", "D1", "C3", "J1", "J4", "R_CC1", "LED_CHG1",
                 "J_MOTOR_PWR1", "J_MOTOR_CTRL1"}
# Edge connectors whose body silk crosses the board edge — drop the redundant silk
# outline (kept on Fab) and hide the ref.
SILK_DROP_OUTLINE = {"J3"}  # edge connectors whose silk crosses the board edge


def _hide_reference(fp) -> None:
    """Hide a footprint's reference text on silk (it stays on the Fab layer)."""
    for f in fp.GetFields():
        if f.IsReference():
            f.SetVisible(False)
            return


def _silk_pass_hide() -> None:
    """Hide overlapping reference labels (own process — see cleanup_silk)."""
    board = pcbnew.LoadBoard(str(PCB))
    for ref in SILK_HIDE_REF | SILK_DROP_OUTLINE:
        fp = board.FindFootprintByReference(ref)
        if fp is not None:
            _hide_reference(fp)
    board.Save(str(PCB))


def _match_paren(text: str, open_idx: int) -> int:
    """Index just past the ')' matching the '(' at open_idx, skipping quoted strings."""
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n and text[i] != '"':
                i += 2 if text[i] == '\\' else 1
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced parens")


def _drop_edge_silk_text() -> int:
    """Delete F/B.Silkscreen graphic shapes from the SILK_DROP_OUTLINE footprints by
    surgical text edit (the pcbnew board-edit API is unreliable in this build). Returns
    the number of shapes removed. Reference labels stay on the Fab layer."""
    text = PCB.read_text()
    removed = 0
    for ref in SILK_DROP_OUTLINE:
        # Locate the footprint block that carries (property "Reference" "<ref>").
        marker = f'(property "Reference" "{ref}"'
        m = text.find(marker)
        if m < 0:
            continue
        fp_open = text.rfind("(footprint", 0, m)
        fp_end = _match_paren(text, fp_open)
        block = text[fp_open:fp_end]
        # Remove each graphic shape whose body sits on a silkscreen layer.
        new_block = []
        i = 0
        while i < len(block):
            j = block.find("(fp_", i)
            if j < 0:
                new_block.append(block[i:])
                break
            new_block.append(block[i:j])
            k = _match_paren(block, j)
            shape = block[j:k]
            head = re.match(r"\(fp_(\w+)", shape)
            on_silk = '"F.SilkS"' in shape or '"B.SilkS"' in shape
            is_graphic = head is not None and head.group(1) in ("line", "poly", "circle", "arc", "rect")
            if is_graphic and on_silk:
                removed += 1  # drop it (append nothing)
            else:
                new_block.append(shape)
            i = k
        text = text[:fp_open] + "".join(new_block) + text[fp_end:]
    if removed:
        PCB.write_text(text)
    return removed


def cleanup_silk() -> None:
    """Resolve cosmetic silkscreen DRC warnings without losing assembly info.

    Reference labels are hidden via pcbnew (reliable); the redundant silk outlines on the
    edge connectors are removed by surgical text edit because the pcbnew footprint
    graphic-removal API returns untyped swig objects unpredictably in this KiCad build.
    """
    code = (f"import sys; sys.path.insert(0, {str(BASE)!r}); "
            f"import autofeeder_pcb as m; m._silk_pass_hide()")
    subprocess.run([sys.executable, "-c", code], check=True, timeout=60)
    dropped = _drop_edge_silk_text()
    print(f"  cleaned silkscreen ({len(SILK_HIDE_REF)} refs hidden, {dropped} silk shapes dropped)")


def GND_LAYERS():
    """Copper layers that carry a GND pour (all four on this 4-layer board)."""
    return [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]


def pour_ground(board) -> None:
    """Pour GND copper on all four layers and fill the zones.

    Stitching vias (see add_stitching_vias) tie the per-layer pours together; the inner
    In1/In2 pours give a near-solid ground reference between the two signal layers.
    """
    gnd = board.FindNet("GND")
    for layer in GND_LAYERS():
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        if gnd:
            zone.SetNet(gnd)
        zone.SetMinThickness(pcbnew.FromMM(0.15))
        zone.SetLocalClearance(pcbnew.FromMM(0.25))  # 0.25mm lets the pour reach dense WSON GND pads while clearing 1.27mm TH gaps
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        zone.SetThermalReliefGap(pcbnew.FromMM(0.3))
        zone.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
        # Drop tiny floating slivers that can't connect to the net (kept islands with a
        # pad/via are retained; stitching vias tie the rest together).
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        outline = zone.Outline()
        corners = [(X0 + 0.5, Y0 + 0.5), (X1 - 0.5, Y0 + 0.5),
                   (X1 - 0.5, Y1 - 0.5), (X0 + 0.5, Y1 - 0.5)]
        outline.NewOutline()
        for x, y in corners:
            outline.Append(int(pcbnew.FromMM(x)), int(pcbnew.FromMM(y)))
        board.Add(zone)
    # Override zone connection to FULL for pads that only touch the zone through a single
    # narrow spoke (starved thermals). USB-C GND: shield/return current + mechanical load.
    # U2 pad 3 (TP4056 GND) and DISP1 pad 2 (OLED GND): single spoke → starved thermal warning.
    # U4 (TPS63031 WSON-10), U8 (FS8205A) and R_CC2 have small/edge GND pads that
    # cannot form the 2 thermal spokes a relief needs → starved/unconnected. Give them
    # a solid (FULL) zone connection instead.
    FULL_GND_REFS = {"J3", "U2", "DISP1", "C3", "U1", "J_MOTOR_PWR1",
                     "U4", "U8", "R_CC2"}
    full_pad_numbers = {"J3": None, "U2": {"3"}, "DISP1": {"2"}, "C3": {"2"},
                        "J_MOTOR_PWR1": {"2"}, "U4": None, "U8": {"5"},
                        "R_CC2": {"2"}}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in FULL_GND_REFS:
            wanted = full_pad_numbers.get(ref)
            for pad in fp.Pads():
                if pad.GetNetname() == "GND":
                    if wanted is None or pad.GetNumber() in wanted:
                        pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    # Actually fill the zones so the pour becomes real copper.
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print(f"  poured + filled GND on F.Cu + B.Cu")


def verify() -> None:
    """Run DRC; must be 0 violations."""
    report = FAB / "autofeeder-drc.json"
    subprocess.run(
        ["kicad-cli", "pcb", "drc", "--format", "json",
         "--severity-error", "-o", str(report), str(PCB)],
        check=False, capture_output=True, timeout=120,
    )
    if report.exists() and report.stat().st_size > 0:
        try:
            with open(report) as f:
                data = json.load(f)
            viol = len(data.get("violations", []))
            unconnected = sum(
                1 for v in data.get("violations", [])
                if "unconnected" in v.get("message", "").lower()
            )
            print(f"  DRC: {viol} violations ({unconnected} unconnected)")
        except (json.JSONDecodeError, KeyError):
            print(f"  DRC: check {report}")
    else:
        print(f"  DRC: no report generated, check {report}")


BOARD_H = Y1 - Y0  # 54 mm — board height for coordinate conversion


def _fix_jlc_cpl(csv_path: Path) -> None:
    """Post-process KiCad CPL export for JLCPCB compatibility.

    KiCad exports positions with origin at top-left (Y+ down, all Y positive).
    But kicad-cli in KiCad 9 outputs with Y+ UP, giving negative Y values for
    components below the top edge. JLCPCB requires origin at bottom-left with
    Y+ UP, so we convert Y → board_height + Y.

    Also switches to JLCPCB's recommended column format:
        Designator, Mid X, Mid Y, Layer, Rotation
    dropping the unnecessary Val/Package columns.
    """
    import csv, io

    lines = csv_path.read_text().splitlines()
    reader = csv.DictReader(io.StringIO("\n".join(lines)))

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])

    for row in reader:
        ref = row.get("Ref", "").strip('"')
        x = float(row.get("PosX", "0").strip('"'))
        y = float(row.get("PosY", "0").strip('"'))
        layer = row.get("Side", "bottom").strip('"')
        rot = float(row.get("Rot", "0").strip('"'))

        # KiCad exports Y+ UP with top-left origin (negative Y below top edge).
        # JLCPCB expects Y+ UP with bottom-left origin.
        y_jlc = round(BOARD_H + y, 6)  # y is negative, so this subtracts from board height
        writer.writerow([ref, round(x, 6), y_jlc, layer, round(rot, 6)])

    csv_path.write_text(out.getvalue())
    print(f"  CPL converted to JLCPCB format ({sum(1 for _ in open(csv_path)) - 1} components)")


def export_fab() -> None:
    """Gerbers, drill, CPL. Exports all gerbers, then removes silkscreen/fab layers."""
    gdir = FAB / "gerbers"
    gdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["kicad-cli", "pcb", "export", "gerbers", "-o", str(gdir) + "/", str(PCB)],
        check=True, capture_output=True, timeout=60,
    )
    subprocess.run(
        ["kicad-cli", "pcb", "export", "drill", "-o", str(gdir) + "/", str(PCB)],
        check=True, capture_output=True, timeout=60,
    )
    cpl_path = FAB / "autofeeder-cpl.csv"
    subprocess.run(
        ["kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm",
         "-o", str(cpl_path), str(PCB)],
        check=True, capture_output=True, timeout=60,
    )

    # Remove busy fab/courtyard/adhesive/user layers (keep silkscreen for component labels)
    for pattern in ["*_Fab.gbr", "*_Courtyard*", "*_Adhesive*", "*User*", "*Margin*"]:
        for f in gdir.glob(pattern):
            f.unlink()

    print(f"  gerbers/drill in {gdir.relative_to(REPO_ROOT)}")
    print(f"  CPL at {cpl_path.relative_to(REPO_ROOT)}")
    _fix_jlc_cpl(cpl_path)


def setup() -> None:
    """Steps 1-3: Create board, populate footprints, add labels."""
    print("=== Autofeeder PCB Setup ===")
    print("[1/3] Creating board...")
    create_board()
    print("[2/3] Populating footprints...")
    populate()
    print("[3/3] Adding silkscreen labels...")
    add_silkscreen_labels()
    print(f"  Board ready with {len(PLACEMENT)} footprints at {PCB.relative_to(REPO_ROOT)}")


def route() -> None:
    """Steps 3-6: Autoroute, finish, verify, export."""
    print("=== Autofeeder PCB Route ===")
    print("[1/4] Autorouting...")
    autoroute()
    print("[2/4] Finishing (pour + stitch)...")
    finish()
    print("[3/4] Verifying DRC...")
    verify()
    print("[4/4] Exporting fabrication files...")
    export_fab()
    print("\nDone.")


def main() -> None:
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] == "route":
        route()
    elif len(_sys.argv) > 1 and _sys.argv[1] == "setup":
        setup()
    else:
        # Full pipeline
        create_board()
        populate()
        add_silkscreen_labels()
        autoroute()
        finish()
        verify()
        export_fab()


if __name__ == "__main__":
    main()
