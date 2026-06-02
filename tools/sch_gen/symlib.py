from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .sexp import Sym, parse


STOCK_LIB_DIRS = [
    Path("/usr/share/kicad/symbols"),
    Path("/usr/local/share/kicad/symbols"),
]


@dataclass
class PinGeom:
    number: str
    name: str
    x: float
    y: float
    rotation: float


class SymbolLibrary:
    def __init__(self, project_lib: str | None = None) -> None:
        self._files: dict[str, Path] = {}
        for d in STOCK_LIB_DIRS:
            if d.is_dir():
                for f in d.glob("*.kicad_sym"):
                    self._files[f.stem] = f
        if project_lib:
            pl = Path(project_lib)
            if pl.is_file():
                self._files[pl.stem] = pl

    @lru_cache(maxsize=None)
    def _lib_root(self, lib: str) -> Sym:
        if lib not in self._files:
            raise KeyError(f"symbol library {lib!r} not found in: {sorted(self._files)}")
        return parse(self._files[lib].read_text())

    def lookup(self, lib_id: str) -> Sym:
        lib, name = lib_id.split(":", 1)
        root = self._lib_root(lib)
        for sym in root.find_all("symbol"):
            if sym.children and sym.children[0] == name:
                out = copy.deepcopy(sym)
                out.children[0] = lib_id
                # Strip (id N) from properties — not expected in lib_symbols cache
                for child in out.children:
                    if isinstance(child, Sym) and child.head == "property":
                        for i, sub in enumerate(child.children):
                            if isinstance(sub, Sym) and sub.head == "id":
                                child.children.pop(i)
                                break
                return out
        raise KeyError(f"symbol {lib_id!r} not found")

    def pins(self, lib_id: str) -> list[PinGeom]:
        sym = self.lookup(lib_id)
        pins: list[PinGeom] = []
        for container in [sym] + sym.find_all("symbol"):
            for pin in container.find_all("pin"):
                at = pin.find("at")
                if at is None or len(at.children) < 2:
                    continue
                x = float(at.children[0])
                y = float(at.children[1])
                rot = float(at.children[2]) if len(at.children) >= 3 else 0.0
                num = pin.find("number")
                name = pin.find("name")
                pins.append(PinGeom(
                    number=str(num.children[0]) if num and num.children else "?",
                    name=str(name.children[0]) if name and name.children else "~",
                    x=x, y=y, rotation=rot,
                ))
        return pins
