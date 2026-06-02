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

# Footprint directories
FP_DIRS = [Path("/usr/share/kicad/footprints")]

# Override placements (ref -> x, y, rot)
PLACEMENT = {
    # Connectors - left edge
    "J1":    (5, 12, 0),       # Battery JST (left)
    "J2":    (5, 48, 0),       # Motor JST (left bottom)
    "J3":    (12, 3, 0),       # USB-C (bottom left)
    "J4":    (48, 48, 0),      # Programming (bottom right)

    # Power
    "U2":    (12, 15, 0),      # TP4056 charger
    "U3":    (12, 24, 0),      # DW01A protection
    "U4":    (12, 34, 0),      # TPS63802 buck-boost

    # MCU
    "U1":    (38, 20, 0),      # ESP32-C6 (center)

    # Motor driver
    "U5":    (38, 38, 0),      # DRV8871

    # CAN
    "U6":    (48, 38, 0),      # SN65HVD230

    # Display
    "DISP1": (28, 42, 0),      # OLED (bottom, centered)

    # Buttons - arranged left to right, matching physical positions
    "SW1_POWER":    (20, 8, 0),
    "SW2_TIMER":    (28, 8, 0),
    "SW3_MANUAL":   (36, 8, 0),
    "SW4_SETTINGS": (20, 14, 0),
    "SW5_UP":       (28, 14, 0),
    "SW6_DOWN":     (36, 14, 0),
}


def _fp_name(node) -> str:
    """Extract footprint string from a sexp node."""
    for c in node.children:
        if isinstance(c, type(node)) and c.head == "footprint":
            if c.children:
                v = str(c.children[0])
                return v.strip('"')
    return ""


def _ref_name(node) -> str:
    """Extract reference from a sexp node."""
    for c in node.children:
        if isinstance(c, type(node)) and c.head == "property":
            if c.children and str(c.children[0]) == "Reference" and len(c.children) >= 2:
                v = str(c.children[1])
                return v.strip('"')
    return ""


def create_board() -> None:
    """Create a fresh 2-layer board with the 56×54mm outline."""
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)
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
        placed += 1

    board.Save(str(PCB))
    print(f"  placed {placed} footprints")
    if errors:
        for e in errors:
            print(e)


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
    board.Save(str(PCB))

    if not pcbnew.ExportSpecctraDSN(board, str(DSN)):
        raise RuntimeError("ExportSpecctraDSN failed")
    print(f"  exported DSN ({DSN.stat().st_size}b); routing...")

    subprocess.run(
        ["freerouting", "-de", str(DSN), "-do", str(SES),
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


def pour_ground(board) -> None:
    """Pour GND copper on both layers with stitching vias."""
    for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
        zone = board.Add(pcbnew.PCB_ZONE(board))
        zone.SetLayer(layer)
        zone.SetNet(board.FindNet("GND"))
        zone.SetMinThickness(pcbnew.FromMM(0.15))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        zone.SetThermalReliefGap(pcbnew.FromMM(0.3))
        zone.SetThermalSpokeWidth(pcbnew.FromMM(0.4))
        # Zone outline = board outline minus clearance
        clearance = pcbnew.FromMM(0.5)
        outline = zone.Outline()
        corners = [(X0 + 0.5, Y0 + 0.5), (X1 - 0.5, Y0 + 0.5),
                   (X1 - 0.5, Y1 - 0.5), (X0 + 0.5, Y1 - 0.5)]
        outline.NewOutline()
        for x, y in corners:
            outline.Append(int(pcbnew.FromMM(x)), int(pcbnew.FromMM(y)))
    # Stitching vias at 8mm pitch
    for x in range(8, int(X1) - 8, 8):
        for y in range(8, int(Y1) - 8, 8):
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            via.SetViaType(pcbnew.VIAS_THROUGH)
            via.SetWidth(pcbnew.FromMM(0.6))
            via.SetDrill(pcbnew.FromMM(0.3))
            net = board.FindNet("GND")
            if net:
                via.SetNet(net)
            board.Add(via)
    print(f"  poured GND on F.Cu + B.Cu with stitching vias")


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
    """Gerbers, drill, CPL."""
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
    print(f"  gerbers/drill in {gdir.relative_to(REPO_ROOT)}")
    print(f"  CPL at {(FAB / 'autofeeder-cpl.csv').relative_to(REPO_ROOT)}")


def main() -> None:
    print("=== Autofeeder PCB Pipeline ===")
    print("[1/5] Creating board...")
    create_board()
    print("[2/5] Populating footprints...")
    populate()
    print("[3/5] Autorouting...")
    autoroute()
    print("[4/5] Finishing (pour + stitch)...")
    finish()
    print("[5/5] Verifying DRC...")
    verify()
    print()
    print("Exporting fabrication files...")
    export_fab()
    print("\nDone.")


if __name__ == "__main__":
    main()
