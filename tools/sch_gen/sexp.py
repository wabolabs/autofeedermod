from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterator, Union


@dataclass
class Sym:
    head: str
    children: list[Node] = field(default_factory=list)

    def find(self, head: str) -> Sym | None:
        for c in self.children:
            if isinstance(c, Sym) and c.head == head:
                return c
        return None

    def find_all(self, head: str) -> list[Sym]:
        return [c for c in self.children if isinstance(c, Sym) and c.head == head]


Atom = Union[str, int, float, bool]
Node = Union[Sym, Atom]


class Bare(str):
    __slots__ = ()


_BARE_KEYWORDS = frozenset({
    "yes", "no", "default", "none",
    "left", "right", "top", "bottom", "center",
    "input", "output", "bidirectional", "passive", "tri_state",
    "free", "unspecified", "power_in", "power_out",
    "open_collector", "open_emitter", "no_connect",
    "line", "inverted", "clock",
    "solid", "dash", "dot", "dash_dot",
    "horizontal", "vertical",
    "italic", "bold",
})


def _escape(s: str) -> str:
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        else:
            out.append(ch)
    return "".join(out)


def _format_atom(a: Atom) -> str:
    if isinstance(a, bool):
        return "yes" if a else "no"
    if isinstance(a, (int, float)):
        if isinstance(a, float) and a == int(a):
            return str(int(a))
        return str(a)
    if isinstance(a, Bare):
        return str(a)
    if isinstance(a, str):
        return f'"{_escape(a)}"'
    raise TypeError(f"unsupported atom: {a!r}")


def dump(node: Node, indent: int = 0) -> str:
    if not isinstance(node, Sym):
        return _format_atom(node)
    pad = "\t" * indent
    if not node.children:
        return f"{pad}({node.head})"
    leading: list[Atom] = []
    rest: list[Node] = []
    for c in node.children:
        if not isinstance(c, Sym) and not rest:
            leading.append(c)
        else:
            rest.append(c)
    head_line = f"{pad}({node.head}"
    if leading:
        head_line += " " + " ".join(_format_atom(a) for a in leading)
    if not rest:
        return head_line + ")"
    if all(isinstance(c, Sym) and not any(isinstance(cc, Sym) for cc in c.children) for c in rest):
        inline = head_line + " " + " ".join(dump(c, 0).strip() for c in rest) + ")"
        if len(inline) - len(pad) <= 120:
            return inline
    parts = [head_line]
    for c in rest:
        parts.append(dump(c, indent + 1))
    parts.append(f"{pad})")
    return "\n".join(parts)


class ParseError(Exception):
    pass


def parse(src: str) -> Sym:
    tokens = _tokenize(src)
    it = iter(tokens)
    tok = next(it, None)
    if tok != "(":
        raise ParseError(f"expected '(', got {tok!r}")
    return _parse_list(it)


def _parse_list(it: Iterator[str]) -> Sym:
    head_tok = next(it)
    if head_tok in ("(", ")"):
        raise ParseError(f"unexpected {head_tok!r} as list head")
    sym = Sym(head=_unquote(head_tok))
    for tok in it:
        if tok == ")":
            return sym
        if tok == "(":
            sym.children.append(_parse_list(it))
        else:
            sym.children.append(_atomize(tok))
    raise ParseError("unexpected EOF")


def _tokenize(src: str) -> list[str]:
    tokens: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch.isspace():
            i += 1
        elif ch in "()":
            tokens.append(ch)
            i += 1
        elif ch == '"':
            j = i + 1
            buf = []
            while j < n:
                c = src[j]
                if c == "\\" and j + 1 < n:
                    nxt = src[j + 1]
                    buf.append({"n": "\n", "t": "\t", "\\": "\\", '"': '"'}.get(nxt, nxt))
                    j += 2
                elif c == '"':
                    j += 1
                    break
                else:
                    buf.append(c)
                    j += 1
            else:
                raise ParseError("unterminated string")
            tokens.append('"' + "".join(buf) + '"')
            i = j
        else:
            j = i
            while j < n and not src[j].isspace() and src[j] not in "()":
                j += 1
            tokens.append(src[i:j])
            i = j
    return tokens


def _unquote(tok: str) -> str:
    if tok.startswith('"') and tok.endswith('"'):
        return tok[1:-1]
    return tok


def _atomize(tok: str) -> Atom:
    if tok.startswith('"'):
        return tok[1:-1]
    try:
        return int(tok)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        pass
    return Bare(tok)


def S(head: str, *children: Node) -> Sym:
    return Sym(head=head, children=list(children))
