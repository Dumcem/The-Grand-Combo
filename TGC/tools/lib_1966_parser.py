"""Structural Clausewitz reader for the subset used by the 1966 tools.

Preserves occurrences and contexts, not a complete engine grammar validator.
Malformed structure/encoding never yields a partial document. Strings follow
Alice 1.3.0's single-line, non-escaping tokenizer semantics.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Iterator, TypedDict

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORE_ROOT = "TGC"
DEFAULT_TIMELINE_ROOT = "TGC_Timeline_1966"


@dataclass(frozen=True)
class Position:
    file: str
    line: int
    column: int
    offset: int

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


class ScriptError(ValueError):
    """Unreadable input or structure that cannot support an unambiguous audit."""


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    start: Position
    end: Position


@dataclass(frozen=True)
class Node:
    key: str | None
    operator: str | None
    value: str | tuple[Node, ...]
    start: Position
    end: Position

    @property
    def keyword(self) -> str | None:
        """Schema-keyword view only; user-defined identifiers stay in key."""
        return self.key.lower() if self.key is not None else None

    @property
    def is_group(self) -> bool:
        return isinstance(self.value, tuple)

    @property
    def children(self) -> tuple[Node, ...]:
        return self.value if isinstance(self.value, tuple) else ()


@dataclass(frozen=True)
class Document:
    nodes: tuple[Node, ...]

    @property
    def definitions(self) -> tuple[Node, ...]:
        for node in self.nodes:
            if node.key is None or node.operator != "=" or not node.is_group:
                raise ScriptError(f"{node.start}: expected a named top-level definition, found {node.key or node.value!r}")
        return self.nodes


class TopLevelBlockMeta(TypedDict):
    key: str
    area: str | None
    year: int | None
    file: str
    line: int
    column: int


def resolve_repo_path(rel_path: str) -> Path:
    return ROOT / rel_path


def rebase_path(rel_path: str, *, core_root: str = DEFAULT_CORE_ROOT, timeline_root: str = DEFAULT_TIMELINE_ROOT) -> str:
    """Map manifest/rule paths to caller-selected roots."""
    if core_root != DEFAULT_CORE_ROOT and rel_path.startswith(f"{DEFAULT_CORE_ROOT}/"):
        return f"{core_root}/{rel_path[len(DEFAULT_CORE_ROOT) + 1:]}"
    if timeline_root != DEFAULT_TIMELINE_ROOT and rel_path.startswith(f"{DEFAULT_TIMELINE_ROOT}/"):
        return f"{timeline_root}/{rel_path[len(DEFAULT_TIMELINE_ROOT) + 1:]}"
    return rel_path


def read_text(rel_path: str, encoding: str = "utf-8") -> str:
    """Decode strictly. Legacy encodings must be requested, never guessed."""
    try:
        raw = resolve_repo_path(rel_path).read_bytes()
        codec = "utf-8-sig" if encoding.lower().replace("_", "-") == "utf-8" else encoding
        return raw.decode(codec).replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise ScriptError(f"{rel_path}: invalid {encoding} at byte {exc.start}; select the documented encoding explicitly") from exc
    except OSError as exc:
        raise ScriptError(f"{rel_path}: cannot read input: {exc}") from exc


def read_json(rel_path: str):
    """Configuration must not lose duplicate keys or accept non-finite numbers."""
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ScriptError(f'{rel_path}: duplicate JSON key {key}')
            result[key] = value
        return result

    def invalid_constant(value):
        raise ScriptError(f'{rel_path}: non-finite JSON constant {value}')

    return json.loads(read_text(rel_path), object_pairs_hook=object_pairs, parse_constant=invalid_constant)


def tokenize(text: str, *, file: str = "<memory>") -> tuple[Token, ...]:
    starts = [0] + [i + 1 for i, char in enumerate(text) if char == "\n"]

    def pos(offset: int) -> Position:
        line = bisect_right(starts, offset)
        return Position(file, line, offset - starts[line - 1] + 1, offset)

    out: list[Token] = []
    i = 1 if text.startswith("\ufeff") else 0
    while i < len(text):
        char = text[i]
        if char in " \t\r\n\f,;":
            i += 1
            continue
        if char == "\x00":
            raise ScriptError(f"{pos(i)}: NUL in script (unsupported encoding or invalid character)")
        if char == "#":
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        start = i
        if char in "\"'":
            i += 1
            while i < len(text) and text[i] not in (char, "\r", "\n", "\x00"):
                i += 1
            if i == len(text) or text[i] != char:
                raise ScriptError(f"{pos(start)}: unterminated single-line string")
            value = text[start + 1:i]
            i += 1
            kind = "string"
        elif char in "{}":
            i += 1
            value, kind = char, char
        elif char in "=<>!":
            i += 1
            if i < len(text) and text[start:i + 1] in {"==", "<=", ">=", "!=", "<>"}:
                i += 1
            value, kind = text[start:i], "operator"
            if value == "!":
                raise ScriptError(f"{pos(start)}: incomplete comparison operator")
        else:
            while i < len(text) and text[i] not in " \t\r\n\f,;{}=<>!#\x00":
                i += 1
            value, kind = text[start:i], "word"
        out.append(Token(kind, value, pos(start), pos(i)))
    return tuple(out)


def parse_script(text: str, *, file: str = "<memory>") -> Document:
    tokens = tokenize(text, file=file)
    i = 0

    def group(opening: Token | None = None) -> tuple[tuple[Node, ...], Position | None]:
        nonlocal i
        nodes: list[Node] = []
        while i < len(tokens):
            token = tokens[i]
            i += 1
            if token.kind == "}":
                if opening is None:
                    raise ScriptError(f"{token.start}: unexpected closing brace")
                return tuple(nodes), token.end
            if token.kind == "{":
                children, end = group(token)
                nodes.append(Node(None, None, children, token.start, end))
                continue
            if token.kind not in {"word", "string"}:
                raise ScriptError(f"{token.start}: expected a key or value, found {token.text!r}")
            if i < len(tokens) and tokens[i].kind == "operator":
                operator = tokens[i].text
                i += 1
                if i == len(tokens) or tokens[i].kind not in {"word", "string", "{"}:
                    raise ScriptError(f"{token.start}: missing value after {operator}")
                rhs = tokens[i]
                i += 1
                if rhs.kind == "{":
                    children, end = group(rhs)
                    nodes.append(Node(token.text, operator, children, token.start, end))
                else:
                    nodes.append(Node(token.text, operator, rhs.text, token.start, rhs.end))
            else:
                nodes.append(Node(None, None, token.text, token.start, token.end))
        if opening is not None:
            raise ScriptError(f"{opening.start}: unclosed group at end of file")
        return tuple(nodes), None

    try:
        nodes, _ = group()
    except RecursionError as exc:
        raise ScriptError(f"{file}: nesting exceeds this reader's recursion capacity; no partial document") from exc
    return Document(nodes)


def parse_file(rel_path: str) -> Document:
    return parse_script(read_text(rel_path), file=rel_path)


def walk(nodes: tuple[Node, ...]) -> Iterator[Node]:
    for node in nodes:
        yield node
        yield from walk(node.children)


def member(node: Node, key: str, *, required: bool = False) -> Node | None:
    found = [child for child in node.children if child.keyword == key.lower()]
    if len(found) > 1:
        raise ScriptError(f"{node.start}: duplicate/ambiguous {key}: " + ", ".join(str(n.start) for n in found))
    if not found:
        if required:
            raise ScriptError(f"{node.start}: missing direct {key}")
        return None
    if found[0].operator != "=":
        raise ScriptError(f"{found[0].start}: expected assignment for {key}")
    return found[0]


def scalar(node: Node, key: str, *, required: bool = False) -> str | None:
    value = member(node, key, required=required)
    if value is not None and value.is_group:
        raise ScriptError(f"{value.start}: expected scalar {key}")
    return value.value if value is not None else None


def integer(value: str, position: Position) -> int:
    if re.fullmatch(r"[+-]?[0-9]+", value) is None:
        raise ScriptError(f"{position}: expected complete integer, found {value!r}")
    return int(value)


def number(value: str, position: Position) -> float:
    if re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value) is None:
        raise ScriptError(f"{position}: expected complete number, found {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise ScriptError(f"{position}: non-finite number {value!r}")
    return result


def unique_definitions(nodes: tuple[Node, ...]) -> dict[str, Node]:
    out: dict[str, Node] = {}
    for node in Document(nodes).definitions:
        if node.key in out:
            raise ScriptError(f"{node.start}: duplicate definition {node.key}; first at {out[node.key].start}")
        out[node.key] = node
    return out


def parse_top_level_blocks(rel_path: str) -> tuple[Node, ...]:
    """All occurrences, never a dictionary with implicit duplicate overwrites."""
    return parse_file(rel_path).definitions


def parse_top_level_block_meta(rel_path: str) -> list[TopLevelBlockMeta]:
    out: list[TopLevelBlockMeta] = []
    for node in parse_top_level_blocks(rel_path):
        if any(child.key is None for child in node.children):
            raise ScriptError(f"{node.start}: unsupported free entry in definition body")
        area = scalar(node, "area")
        year = scalar(node, "year")
        out.append({"key": node.key, "area": area,
                    "year": integer(year, member(node, "year").start) if year is not None else None,
                    "file": rel_path, "line": node.start.line, "column": node.start.column})
    return out
