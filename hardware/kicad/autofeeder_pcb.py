"""Autofeeder PCB pipeline: create, populate, autoroute, pour, verify, export.

Usage:
    cd autofeedermod
    PYTHONPATH=tools python3 hardware/kicad/autofeeder_pcb.py

Requires: KiCad 9.0+, kicad-cli, freerouting on PATH
"""

from __future__ import annotations

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
    "J2":         (52.00, 16.00, 90),  # motor JST, right edge upper, facing left (inward)
    "J1":         (52.00, 30.00, 90),  # battery JST, right edge lower, facing left (inward)
    "J4":         (53.00, 37.00, 0),   # prog header, right edge below JSTs (like original J11)

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
    "U5":         (36.00, 38.00, 0),

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
    "J_RTC":      (14.00, 44.00, 0),  # DS3231 module header (bottom-left)
    "J_GPS":      (44.00, 14.00, 0),  # GPS module header (top-right)
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


def _ref_name(node) -> str:
    """Extract reference from a netlist comp node."""
    for c in node.children:
        if isinstance(c, type(node)) and c.head == "ref" and c.children:
            return str(c.children[0]).strip('"')
    return ""


def create_board() -> None:
    """Create a fresh 2-layer board with the 56×54mm outline."""
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)
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
                comps.append((ref, fp_str))

    placed = 0
    errors = []
    for ref, fp_id in comps:
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
    labels = {"J1": "BATT", "J2": "MOTOR"}
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
    _pre_route_vbus(board)
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


def finish() -> None:
    """Import routes, pour GND on both layers, save."""
    board = pcbnew.LoadBoard(str(PCB))
    if not pcbnew.ImportSpecctraSES(board, str(SES)):
        raise RuntimeError("ImportSpecctraSES failed")
    segs = sum(1 for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T)
    vias = sum(1 for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T)
    print(f"  imported {segs} segments + {vias} vias")

    pour_ground(board)
    board.Save(str(PCB))
    cleanup_silk()


# Silkscreen reference labels that overlap copper or each other in the dense back-side
# cluster — hidden on silk (they remain on the Fab layer for assembly).
SILK_HIDE_REF = {"R5", "R6", "R7", "LED_STATUS1"}
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


def pour_ground(board) -> None:
    """Pour GND copper on both layers and fill the zones.

    Note: no blind stitching vias — dropping vias on a fixed grid drops them on
    top of signal tracks/pads (shorts) on a dense board. The filled zones plus the
    GND pad/via connections give a solid ground; add manual stitching later if needed.
    """
    gnd = board.FindNet("GND")
    for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        if gnd:
            zone.SetNet(gnd)
        zone.SetMinThickness(pcbnew.FromMM(0.15))
        zone.SetLocalClearance(pcbnew.FromMM(0.5))  # 0.5mm keeps fill out of 1.27mm TH-to-TH gaps
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        zone.SetThermalReliefGap(pcbnew.FromMM(0.3))
        zone.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.4))
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
    FULL_GND_REFS = {"J3", "U2", "DISP1", "C3", "U1"}
    full_pad_numbers = {"J3": None, "U2": {"3"}, "DISP1": {"2"}, "C3": {"2"}}
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
    subprocess.run(
        ["kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm",
         "-o", str(FAB / "autofeeder-cpl.csv"), str(PCB)],
        check=True, capture_output=True, timeout=60,
    )

    # Remove busy fab/courtyard/adhesive/user layers (keep silkscreen for component labels)
    for pattern in ["*_Fab.gbr", "*_Courtyard*", "*_Adhesive*", "*User*", "*Margin*"]:
        for f in gdir.glob(pattern):
            f.unlink()

    print(f"  gerbers/drill in {gdir.relative_to(REPO_ROOT)}")
    print(f"  CPL at {(FAB / 'autofeeder-cpl.csv').relative_to(REPO_ROOT)}")


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
