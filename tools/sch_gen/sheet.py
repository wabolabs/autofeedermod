from __future__ import annotations

import math
import uuid as _uuid
from dataclasses import dataclass, field
from pathlib import Path

from .sexp import Bare, S, Sym, dump
from .symlib import PinGeom, SymbolLibrary


GRID = 1.27


def snap(v: float, grid: float = GRID) -> float:
    return round(v / grid) * grid


def snap_xy(xy: tuple[float, float], grid: float = GRID) -> tuple[float, float]:
    return (snap(xy[0], grid), snap(xy[1], grid))


def _u(seed: str | None = None) -> str:
    if seed:
        return str(_uuid.uuid5(_uuid.NAMESPACE_URL, f"autofeeder/{seed}"))
    return str(_uuid.uuid4())


@dataclass
class Placed:
    ref: str
    lib_id: str
    value: str
    footprint: str
    at: tuple[float, float]
    rotation: float = 0.0
    unit: int = 1
    uuid: str = ""
    _pin_cache: dict[str, PinGeom] = field(default_factory=dict)

    def pin_xy(self, number: str | int) -> tuple[float, float]:
        num = str(number)
        if num not in self._pin_cache:
            raise KeyError(f"{self.ref}: no pin {num} in library {self.lib_id}")
        p = self._pin_cache[num]
        rad = math.radians(self.rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        rx = p.x * cos_r - p.y * sin_r
        ry = p.x * sin_r + p.y * cos_r
        ry = -ry  # KiCad +Y down
        return (self.at[0] + rx, self.at[1] + ry)


class Sheet:
    def __init__(
        self,
        name: str,
        uuid: str,
        page: int = 1,
        paper: str = "A4",
        title: str | None = None,
        rev: str = "1.0",
        date: str = "2026-06-02",
        company: str = "CoopTech",
        lib: SymbolLibrary | None = None,
        project_name: str = "autofeedermod",
    ) -> None:
        self.name = name
        self.uuid = uuid
        self.page = page
        self.paper = paper
        self.title = title or name
        self.rev = rev
        self.date = date
        self.company = company
        self.lib = lib or SymbolLibrary()
        self.project_name = project_name
        self.components: list[Placed] = []
        self.local_labels: list[tuple[str, tuple[float, float], float]] = []
        self.wires: list[Wire] = []
        self.junctions: list[tuple[float, float]] = []
        self.no_connects: list[tuple[float, float]] = []
        self.notes: list[tuple[tuple[float, float], str]] = []
        self._wire_set: set[tuple[float, float, float, float]] = set()

    def add(
        self,
        ref: str,
        lib_id: str,
        value: str,
        at: tuple[float, float],
        rotation: float = 0.0,
        footprint: str = "",
        unit: int = 1,
    ) -> Placed:
        if ref and not ref[-1].isdigit() and not ref.startswith("#"):
            ref = ref + "1"
        pins = self.lib.pins(lib_id)
        p = Placed(
            ref=ref,
            lib_id=lib_id,
            value=value,
            footprint=footprint,
            at=snap_xy(at),
            rotation=rotation,
            unit=unit,
            uuid=_u(f"{self.name}/cmp/{ref}"),
            _pin_cache={pg.number: pg for pg in pins},
        )
        self.components.append(p)
        return p

    def local_label(self, name: str, at: tuple[float, float], rotation: float = 0.0) -> None:
        self.local_labels.append((name, at, rotation))

    def wire(self, a: tuple[float, float], b: tuple[float, float]) -> None:
        a = snap_xy(a)
        b = snap_xy(b)
        if a == b:
            return
        key = (*a, *b)
        rev = (*b, *a)
        if key in self._wire_set or rev in self._wire_set:
            return
        self._wire_set.add(key)
        self.wires.append(Wire(a=a, b=b, uuid=_u(f"{self.name}/wire/{len(self.wires)}")))

    def junction(self, at: tuple[float, float]) -> None:
        self.junctions.append(snap_xy(at))

    def no_connect(self, at: tuple[float, float]) -> None:
        self.no_connects.append(snap_xy(at))

    def to_sexp(self) -> Sym:
        root = S("kicad_sch")
        root.children.extend([
            S("version", 20250114),
            S("generator", "autofeeder_sch_gen"),
            S("uuid", self.uuid),
            S("paper", self.paper),
        ])
        root.children.append(S("title_block",
            S("title", self.title),
            S("date", self.date),
            S("rev", self.rev),
            S("company", self.company),
        ))
        # lib_symbols — include custom symbol definitions
        lib_sym = S("lib_symbols")
        seen_lib_ids: set[str] = set()
        for c in self.components:
            if c.lib_id not in seen_lib_ids:
                seen_lib_ids.add(c.lib_id)
                custom = self.lib.get_custom_symbol(c.lib_id)
                if custom:
                    lib_sym.children.append(custom)
        root.children.append(lib_sym)
        # Junctions
        for j in self.junctions:
            root.children.append(S("junction",
                S("at", j[0], j[1]),
                S("diameter", 0),
                S("color", 0, 0, 0, 0),
                S("uuid", _u(f"{self.name}/junction/{j[0]},{j[1]}")),
            ))
        # No-connects
        for nc in self.no_connects:
            root.children.append(S("no_connect",
                S("at", nc[0], nc[1]),
                S("uuid", _u(f"{self.name}/nc/{nc[0]},{nc[1]}")),
            ))
        # Wires
        for w in self.wires:
            root.children.append(S("wire",
                S("pts", S("xy", w.a[0], w.a[1]), S("xy", w.b[0], w.b[1])),
                S("stroke", S("width", 0), S("type", Bare("solid"))),
                S("uuid", w.uuid),
            ))
        # Local labels
        for i, (lbl_name, lbl_at, lbl_rot) in enumerate(self.local_labels):
            root.children.append(S("label", lbl_name,
                S("at", lbl_at[0], lbl_at[1], lbl_rot),
                S("effects",
                    S("font", S("size", 1.27, 1.27)),
                    S("justify", Bare("left"), Bare("bottom")),
                ),
                S("uuid", _u(f"{self.name}/label/{i}/{lbl_name}/{lbl_at[0]},{lbl_at[1]}")),
            ))
        # Component instances
        for c in self.components:
            sym = S("symbol")
            sym.children.append(S("lib_id", c.lib_id))
            sym.children.append(S("at", c.at[0], c.at[1], c.rotation))
            sym.children.append(S("unit", c.unit))
            sym.children.append(S("exclude_from_sim", Bare("no")))
            sym.children.append(S("in_bom", Bare("yes")))
            sym.children.append(S("on_board", Bare("yes")))
            sym.children.append(S("uuid", c.uuid))
            field_specs = [
                ("Reference", c.ref, 0),
                ("Value", c.value, 1),
                ("Footprint", c.footprint, 2),
            ]
            for name, val, idx in field_specs:
                effects_children = [S("font", S("size", 1.27, 1.27))]
                if idx >= 2:
                    effects_children.append(S("hide", Bare("yes")))
                prop = S("property", name, val,
                    S("at", c.at[0] + 2.54, c.at[1] + (-2.54 if idx == 0 else 2.54 if idx == 1 else 0), 0),
                    S("effects", *effects_children),
                )
                sym.children.append(prop)

            sym.children.append(S("instances",
                S("project", self.project_name,
                    S("path", f"/{self.uuid}",
                        S("reference", c.ref),
                        S("unit", c.unit),
                    ),
                ),
            ))
            root.children.append(sym)
        # Sheet instances
        root.children.append(S("sheet_instances",
            S("path", f"/{self.uuid}",
                S("page", str(self.page)),
            ),
        ))
        root.children.append(S("embedded_fonts", Bare("no")))
        return root

    def check_paren_balance(self) -> None:
        text = dump(self.to_sexp())
        depth = 0
        for ch in text:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    raise ValueError(f"sheet {self.name}: extra closing paren")
        if depth != 0:
            raise ValueError(f"sheet {self.name}: unbalanced parens (depth={depth})")

    def write(self, path: str | Path) -> None:
        text = dump(self.to_sexp()) + "\n"
        Path(path).write_text(text)


@dataclass
class Wire:
    a: tuple[float, float]
    b: tuple[float, float]
    uuid: str = ""
