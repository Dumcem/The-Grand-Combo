#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = "TGC/tools/1966_extension_scope.json"


def read_text(rel_path: str, encoding: str = "utf-8") -> str:
    return (ROOT / rel_path).read_text(encoding=encoding, errors="ignore")


def read_manifest() -> dict:
    return json.loads(read_text(MANIFEST_PATH, encoding="utf-8"))


def parse_top_level_blocks(rel_path: str) -> list[dict]:
    lines = read_text(rel_path).splitlines()
    out: list[dict] = []
    i = 0
    depth = 0
    while i < len(lines):
        line = lines[i]
        if depth == 0:
            m = re.match(r"\s*([a-z0-9_]+)\s*=\s*\{\s*(?:#.*)?$", line)
            if m:
                key = m.group(1)
                depth = 1
                i += 1
                area = None
                year = None
                while i < len(lines) and depth > 0:
                    cur = lines[i]
                    if area is None:
                        ma = re.match(r"\s*area\s*=\s*([a-z0-9_]+)", cur)
                        if ma:
                            area = ma.group(1)
                    if year is None:
                        my = re.match(r"\s*year\s*=\s*(\d+)", cur)
                        if my:
                            year = int(my.group(1))
                    depth += cur.count("{") - cur.count("}")
                    i += 1
                out.append({"key": key, "area": area, "year": year, "file": rel_path})
                depth = 0
                continue
        depth += line.count("{") - line.count("}")
        i += 1
    return out


def build_localisation_index(localisation_files: list[str]) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = {}
    for rel_path in localisation_files:
        for lineno, line in enumerate(read_text(rel_path, encoding="latin-1").splitlines(), 1):
            if not line or line.startswith("#"):
                continue
            key = line.split(";", 1)[0].strip()
            idx.setdefault(key, []).append(f"{rel_path}:{lineno}")
    return idx


UNIT_STAT_HINTS = {
    "attack",
    "defence",
    "hull",
    "gun_power",
    "torpedo_attack",
    "reconnaissance",
    "support",
    "maneuver",
    "siege",
    "maximum_speed",
    "evasion",
    "fire_range",
    "discipline",
    "supply_consumption",
}

NON_UNIT_EFFECT_KEYS = {"army_base", "navy_base"}
LEGACY_UNIT_ALIASES = {"carrier": "aircraftcarrier"}


def discover_unit_keys() -> set[str]:
    unit_dir = ROOT / "TGC/units"
    return {p.stem for p in unit_dir.glob("*.txt")}


def validate_effect_unit_targets(rel_path: str, unit_keys: set[str]) -> list[str]:
    failures: list[str] = []
    lines = read_text(rel_path).splitlines()
    i = 0
    while i < len(lines):
        if re.match(r"\s*effect\s*=\s*\{\s*(?:#.*)?$", lines[i]):
            depth = 1
            i += 1
            effect_lines: list[tuple[int, str, int]] = []
            while i < len(lines) and depth > 0:
                cur = lines[i]
                effect_lines.append((i + 1, cur, depth))
                depth += cur.count("{") - cur.count("}")
                i += 1

            j = 0
            while j < len(effect_lines):
                lineno, txt, local_depth = effect_lines[j]
                if local_depth == 1:
                    ma = re.match(r"\s*activate_unit\s*=\s*([a-z0-9_]+)", txt)
                    if ma:
                        unit_key = ma.group(1)
                        if unit_key not in unit_keys:
                            failures.append(f"UNIT target unknown key '{unit_key}' in {rel_path}:{lineno} (activate_unit)")

                    mb = re.match(r"\s*([a-z0-9_]+)\s*=\s*\{\s*(?:#.*)?$", txt)
                    if mb:
                        key = mb.group(1)
                        sub_depth = 1
                        k = j + 1
                        sub: list[tuple[int, str]] = []
                        while k < len(effect_lines) and sub_depth > 0:
                            ln2, t2, _ = effect_lines[k]
                            sub.append((ln2, t2))
                            sub_depth += t2.count("{") - t2.count("}")
                            k += 1

                        if key not in NON_UNIT_EFFECT_KEYS:
                            joined = "\n".join(x[1] for x in sub)
                            looks_like_unit_target = any(re.search(rf"\b{re.escape(stat)}\b", joined) for stat in UNIT_STAT_HINTS)
                            if looks_like_unit_target and key not in unit_keys:
                                if key in LEGACY_UNIT_ALIASES and LEGACY_UNIT_ALIASES[key] in unit_keys:
                                    failures.append(
                                        f"UNIT target legacy key '{key}' in {rel_path}:{lineno} (use '{LEGACY_UNIT_ALIASES[key]}')"
                                    )
                                else:
                                    failures.append(f"UNIT target unknown key '{key}' in {rel_path}:{lineno}")
                        j = k
                        continue
                j += 1
            continue
        i += 1
    return failures


def main() -> int:
    m = read_manifest()
    branches = m["tech_tree"]["branches"]
    late_min_year = m["tech_tree"].get("late_tech_min_year", 1936)
    invention_files = m["invention_files"]
    loc_files = m["localisation_files"]
    structural = m["structural"]
    stale_rules = m.get("stale_reference_rules", [])
    unit_keys = discover_unit_keys()

    failures: list[str] = []
    loc_index = build_localisation_index(loc_files)
    loc_keys = set(loc_index)

    all_tech: list[dict] = []
    expected_areas = 0

    for b in branches:
        rel_path = b["file"]
        area_spec = b["areas"]
        expected_areas += len(area_spec)
        blocks = parse_top_level_blocks(rel_path)
        all_tech.extend(blocks)
        by_area: dict[str, list[dict]] = defaultdict(list)
        for x in blocks:
            if x["area"]:
                by_area[x["area"]].append(x)
        for area, expected in area_spec.items():
            actual = len(by_area.get(area, []))
            if actual != expected:
                failures.append(f"TECH area tier mismatch in {rel_path}: {area} has {actual}, expected {expected}")

    tech_idx: dict[str, list[str]] = defaultdict(list)
    for x in all_tech:
        tech_idx[x["key"]].append(x["file"])
    for k, files in tech_idx.items():
        if len(files) > 1:
            failures.append(f"TECH duplicate definition for {k}: {', '.join(sorted(set(files)))}")

    late_keys = sorted({x["key"] for x in all_tech if x["year"] is not None and x["year"] >= late_min_year})
    for k in late_keys:
        if k not in loc_keys:
            failures.append(f"TECH missing localisation key: {k}")
        if f"{k}_desc" not in loc_keys:
            failures.append(f"TECH missing localisation desc: {k}_desc")

    all_inv: list[dict] = []
    for rel in invention_files:
        all_inv.extend(parse_top_level_blocks(rel))
    inv_idx: dict[str, list[str]] = defaultdict(list)
    for x in all_inv:
        inv_idx[x["key"]].append(x["file"])
    for k, files in inv_idx.items():
        if len(files) > 1:
            failures.append(f"INVENTION duplicate definition for {k}: {', '.join(sorted(set(files)))}")
        if k not in loc_keys:
            failures.append(f"INVENTION missing localisation key: {k}")
        if f"{k}_desc" not in loc_keys:
            failures.append(f"INVENTION missing localisation desc: {k}_desc")

    unit_target_files = sorted({b["file"] for b in branches} | set(invention_files))
    for rel in unit_target_files:
        failures.extend(validate_effect_unit_targets(rel, unit_keys))

    for rule in stale_rules:
        pat = re.compile(rf"\b{re.escape(rule['old_key'])}\b")
        for rel in rule["files"]:
            for n, line in enumerate(read_text(rel).splitlines(), 1):
                if pat.search(line):
                    failures.append(f"STALE reference {rule['old_key']} found in {rel}:{n} (expected context: {rule['new_key']})")

    d = structural["decision_alignment"]
    setup = read_text(d["file"])
    block = re.search(rf"{re.escape(d['decision_key'])}\s*=\s*\{{.*?\n\t\t\}}", setup, re.S)
    if not block:
        failures.append(f"STRUCTURAL missing {d['decision_key']} block in {d['file']}")
    else:
        btxt = block.group(0)
        if not re.search(rf"potential\s*=\s*\{{[^}}]*year\s*=\s*{d['potential_year']}", btxt, re.S):
            failures.append(f"STRUCTURAL {d['decision_key']} potential must include year = {d['potential_year']}")
        if not re.search(rf"allow\s*=\s*\{{[^}}]*year\s*=\s*{d['allow_year']}", btxt, re.S):
            failures.append(f"STRUCTURAL {d['decision_key']} allow must include year = {d['allow_year']}")

    for chk in structural["required_patterns"]:
        if not re.search(chk["pattern"], read_text(chk["file"]), re.S):
            failures.append(f"STRUCTURAL {chk['message']}")
    for req in structural["required_files"]:
        if not (ROOT / req).exists():
            failures.append(f"STRUCTURAL missing file: {req}")

    print("1966 extension full-tree static validation")
    print(f" - scope manifest: {MANIFEST_PATH}")
    print(f" - expected tech areas: {expected_areas}")
    print(f" - parsed tech definitions: {len(all_tech)}")
    print(f" - late-tech localisation perimeter (year >= {late_min_year}): {len(late_keys)} keys")
    print(f" - tracked invention files: {len(invention_files)}")
    print(f" - parsed inventions in tracked files: {len(all_inv)}")
    print(f" - discovered unit keys: {len(unit_keys)}")
    print(" - structural checks: defines/decision/backend/readme/audit/docs")

    if failures:
        print("\nFAILED checks:")
        for item in failures:
            print(f" - {item}")
        return 1

    print("\nOK: full-tree 1966 static checks passed (25 areas @ 12 tiers + localisation + structure).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
