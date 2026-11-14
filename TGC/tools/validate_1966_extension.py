#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from lib_1966_parser import (
    Node, ScriptError, TopLevelBlockMeta, member, parse_file,
    parse_top_level_block_meta, read_text, rebase_path, resolve_repo_path,
    scalar, unique_definitions, walk, read_json,
)
from lib_1966_semantics import canonical_stat, effect_body, numeric_modifier_entries, report_modifier_semantics
from lib_1966_diagnostics import Reporter
from lib_1966_functional import read_campaign_end
from lib_1966_runtime import compose_runtime, unit_definitions

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = "TGC/tools/1966_extension_scope.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the TGC 1966 timeline submod layer.")
    parser.add_argument("--core-root", default="TGC", help="Base/core mod root (default: TGC).")
    parser.add_argument(
        "--timeline-root",
        default="TGC_Timeline_1966",
        help="1966 timeline runtime root (default: TGC_Timeline_1966).",
    )
    return parser.parse_args()


def _rebase_obj(obj, *, core_root: str, timeline_root: str):
    if isinstance(obj, str):
        return rebase_path(obj, core_root=core_root, timeline_root=timeline_root)
    if isinstance(obj, list):
        return [_rebase_obj(x, core_root=core_root, timeline_root=timeline_root) for x in obj]
    if isinstance(obj, dict):
        return {k: _rebase_obj(v, core_root=core_root, timeline_root=timeline_root) for k, v in obj.items()}
    return obj


def read_manifest(core_root: str = "TGC", timeline_root: str = "TGC_Timeline_1966") -> dict:
    manifest = read_json(MANIFEST_PATH)
    return _rebase_obj(manifest, core_root=core_root, timeline_root=timeline_root)


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


def validate_effect_unit_targets(rel_path: str, unit_keys: set[str]) -> list[str]:
    """Only technology modifiers and invention effect bodies, never trigger text."""
    failures: list[str] = []
    is_tech = "/technologies/" in "/" + rel_path.replace("\\", "/").lower()
    # Definition uniqueness is diagnosed by the caller's cross-file inventory;
    # retain occurrences here so its specific diagnostics are not replaced.
    for definition in parse_file(rel_path).definitions:
        body = effect_body(definition, 'technology' if is_tech else 'invention')
        bodies = [body] if body is not None else []
        for body in bodies:
            if not body.is_group:
                raise ScriptError(f"{body.start}: expected effect group")
            for node in body.children:
                if node.keyword == "activate_unit":
                    if node.is_group or node.operator != "=" or node.value not in unit_keys:
                        failures.append(f"UNIT target unknown key {node.value!r} in {node.start} (activate_unit)")
                if node.key in unit_keys | NON_UNIT_EFFECT_KEYS:
                    numeric_modifier_entries(node)
                    continue
                if not node.is_group:
                    continue
                if any(canonical_stat(n.key) in UNIT_STAT_HINTS for n in node.children if n.key) and node.key not in unit_keys:
                    replacement = LEGACY_UNIT_ALIASES.get(node.key)
                    detail = f" (use '{replacement}')" if replacement in unit_keys else ""
                    failures.append(f"UNIT target unknown/legacy key '{node.key}' in {node.start}{detail}")
    return failures


def block_has_section_year(block: Node, section: str, expected_year: int) -> bool:
    """Require the direct positive gate, not a comment, NOT, or another section."""
    child = member(block, section)
    if child is None:
        return False
    if not child.is_group:
        raise ScriptError(f"{child.start}: expected {section} group")
    return scalar(child, "year") == str(expected_year)


def find_decision(rel_path: str, block_key: str) -> Node | None:
    roots = unique_definitions(parse_file(rel_path).definitions)
    containers = [node for node in roots.values() if node.keyword == "political_decisions"]
    if len(containers) > 1:
        raise ScriptError(f"{rel_path}: ambiguous political_decisions containers")
    if not containers:
        return None
    return unique_definitions(containers[0].children).get(block_key)


def _run() -> int:
    args = parse_args()
    m = read_manifest(args.core_root, args.timeline_root)
    branches = m["tech_tree"]["branches"]
    late_min_year = m["tech_tree"].get("late_tech_min_year", 1936)
    invention_files = m["invention_files"]
    loc_files = m["localisation_files"]
    structural = m["structural"]
    stale_rules = m.get("stale_reference_rules", [])
    inventory = compose_runtime(ROOT, args.core_root, args.timeline_root)
    unit_keys = set(unit_definitions(inventory, ROOT))

    failures: list[str] = []
    loc_index = build_localisation_index(loc_files)
    loc_keys = set(loc_index)

    all_tech: list[TopLevelBlockMeta] = []
    expected_areas = 0

    for b in branches:
        rel_path = b["file"]
        area_spec = b["areas"]
        expected_areas += len(area_spec)
        blocks = parse_top_level_block_meta(rel_path)
        all_tech.extend(blocks)
        by_area: dict[str, list[TopLevelBlockMeta]] = defaultdict(list)
        for x in blocks:
            where = f"{x['file']}:{x['line']}:{x['column']}"
            if x["area"] is None:
                failures.append(f"TECH missing direct area for {x['key']} at {where}")
            elif x["area"] not in area_spec:
                failures.append(f"TECH unknown area {x['area']} for {x['key']} at {where}")
            else:
                by_area[x["area"]].append(x)
            if x["year"] is None:
                failures.append(f"TECH missing direct year for {x['key']} at {where}")
        for area, expected in area_spec.items():
            actual = len(by_area.get(area, []))
            if actual != expected:
                failures.append(f"TECH area tier mismatch in {rel_path}: {area} has {actual}, expected {expected}")

    tech_idx: dict[str, list[str]] = defaultdict(list)
    for x in all_tech:
        tech_idx[x["key"]].append(f"{x['file']}:{x['line']}:{x['column']}")
    for k, files in tech_idx.items():
        if len(files) > 1:
            failures.append(f"TECH duplicate definition for {k}: {', '.join(sorted(set(files)))}")

    late_keys = sorted({x["key"] for x in all_tech if x["year"] is not None and x["year"] >= late_min_year})
    for k in late_keys:
        if k not in loc_keys:
            failures.append(f"TECH missing localisation key: {k}")
        if f"{k}_desc" not in loc_keys:
            failures.append(f"TECH missing localisation desc: {k}_desc")

    all_inv: list[TopLevelBlockMeta] = []
    for rel in invention_files:
        all_inv.extend(parse_top_level_block_meta(rel))
    inv_idx: dict[str, list[str]] = defaultdict(list)
    for x in all_inv:
        inv_idx[x["key"]].append(f"{x['file']}:{x['line']}:{x['column']}")
    for k, files in inv_idx.items():
        if len(files) > 1:
            failures.append(f"INVENTION duplicate definition for {k}: {', '.join(sorted(set(files)))}")
        if k not in loc_keys:
            failures.append(f"INVENTION missing localisation key: {k}")
        if f"{k}_desc" not in loc_keys:
            failures.append(f"INVENTION missing localisation desc: {k}_desc")

    unit_target_files = sorted(set(inventory.files('technologies') + inventory.files('inventions')))
    for rel in unit_target_files:
        failures.extend(validate_effect_unit_targets(rel, unit_keys))
    semantic_rep = Reporter()
    if not failures:
        report_modifier_semantics(unit_target_files, unit_keys, semantic_rep)

    for rule in stale_rules:
        for rel in rule["files"]:
            for node in walk(parse_file(rel).nodes):
                if node.key == rule["old_key"] or (not node.is_group and node.value == rule["old_key"]):
                    failures.append(f"STALE reference {rule['old_key']} found at {node.start} (expected context: {rule['new_key']})")

    d = structural["decision_alignment"]
    end_date = date.fromisoformat(structural["campaign_end_date"])
    timeline_defines = inventory.require("common/defines.lua")
    if read_campaign_end(timeline_defines) != end_date:
        failures.append(f"STRUCTURAL {timeline_defines} must set end_date to {end_date}")
    core_defines = f"{args.core_root}/common/defines.lua"
    if read_campaign_end(core_defines) == end_date:
        failures.append(f"CORE CLEANUP {core_defines} must not set the Timeline end_date")
    decision_block = find_decision(d["file"], d["decision_key"])
    if decision_block is None:
        failures.append(f"STRUCTURAL missing {d['decision_key']} block in {d['file']}")
    else:
        if not block_has_section_year(decision_block, "potential", d["potential_year"]):
            failures.append(f"STRUCTURAL {d['decision_key']} potential must include direct year = {d['potential_year']}")
        if not block_has_section_year(decision_block, "allow", d["allow_year"]):
            failures.append(f"STRUCTURAL {d['decision_key']} allow must include direct year = {d['allow_year']}")

    for chk in structural["required_patterns"]:
        if not re.search(chk["pattern"], read_text(chk["file"]), re.S):
            failures.append(f"STRUCTURAL {chk['message']}")
    for chk in structural.get("core_forbidden_patterns", []):
        if resolve_repo_path(chk["file"]).exists() and re.search(chk["pattern"], read_text(chk["file"]), re.S):
            failures.append(f"CORE CLEANUP {chk['message']}")
    for req in structural["required_files"]:
        if not resolve_repo_path(req).exists():
            failures.append(f"STRUCTURAL missing file: {req}")
    for forbidden in structural.get("core_forbidden_files", []):
        if resolve_repo_path(forbidden).exists():
            failures.append(f"CORE CLEANUP forbidden timeline-only file remains: {forbidden}")
    for req_bin in structural.get("required_binary_files", []):
        path = resolve_repo_path(req_bin)
        if not path.exists():
            failures.append(f"STRUCTURAL missing binary asset: {req_bin}")
        elif path.stat().st_size <= 0:
            failures.append(f"STRUCTURAL empty binary asset: {req_bin}")

    print("1966 extension full-tree static validation")
    print(f" - scope manifest: {MANIFEST_PATH}")
    print(f" - core root: {args.core_root}")
    print(f" - timeline root: {args.timeline_root}")
    print(f" - expected tech areas: {expected_areas}")
    print(f" - parsed tech definitions: {len(all_tech)}")
    print(f" - late-tech localisation perimeter (year >= {late_min_year}): {len(late_keys)} keys")
    print(f" - tracked invention files: {len(invention_files)}")
    print(f" - parsed inventions in tracked files: {len(all_inv)}")
    print(f" - discovered unit keys: {len(unit_keys)}")
    print(" - structural checks: submod runtime + core cleanup + docs")
    print(f' - effective source unit-target checks: {len(unit_target_files)} files')
    limits = [d for d in semantic_rep.diagnostics if d.level == 'WARN']
    print(f' - Alice semantic limitations: {len(limits)} physical-property findings; V2 script application remains unverified')
    print(' - semantic limits are NOT a compatibility PASS; use the balance auditor for provenance and engine projections')

    if failures:
        print("\nFAILED checks:")
        for item in failures:
            print(f" - {item}")
        return 1

    print(f"\nOK: manifest-scoped 1966 checks passed ({expected_areas} areas, {len(all_tech)} technology occurrences + localisation + structure).")
    return 0


def main() -> int:
    try:
        return _run()
    except (ScriptError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL: 1966 validation input error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
