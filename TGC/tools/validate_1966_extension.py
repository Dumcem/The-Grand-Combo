#!/usr/bin/env python3
"""
Lightweight static validator for the TGC 1966 extension (late-game drift guard).

Checks a focused allowlist of post-1936 techs/inventions used by the extension:
  1) targeted tech key exists in expected technology file
  2) targeted tech has localisation key + *_desc key
  3) targeted invention key exists in expected invention file
  4) targeted invention has localisation key + *_desc key
  5) duplicate-definition / duplicate-localisation drift checks for targeted keys
  6) unexpected-file and stale renamed-key reference checks for targeted scope
  7) core structural 1966 alignment checks (defines/decision/ui/readme/audit presence)
"""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MANIFEST_PATH = "TGC/tools/1966_extension_scope.json"

TECH_FILES_GLOB = "TGC/technologies/*_tech.txt"
INVENTION_FILES_GLOB = "TGC/inventions/*.txt"


def read_text(rel_path: str, encoding: str = "utf-8") -> str:
    return (ROOT / rel_path).read_text(encoding=encoding, errors="ignore")


def read_manifest() -> dict:
    return json.loads(read_text(MANIFEST_PATH, encoding="utf-8"))


def has_top_level_key(file_text: str, key: str) -> bool:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*\{{\s*$", re.M)
    return bool(pattern.search(file_text))


def build_top_level_index(paths: list[str]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for rel_path in paths:
        text = read_text(rel_path)
        for match in re.finditer(r"(?m)^\s*([a-z0-9_]+)\s*=\s*\{\s*$", text):
            key = match.group(1)
            index.setdefault(key, []).append(rel_path)
    return index


def build_localisation_index(localisation_files: list[str]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for rel_path in localisation_files:
        for lineno, line in enumerate(read_text(rel_path, encoding="latin-1").splitlines(), 1):
            if not line or line.startswith("#"):
                continue
            key = line.split(";", 1)[0].strip()
            index.setdefault(key, []).append(f"{rel_path}:{lineno}")
    return index


def main() -> int:
    manifest = read_manifest()
    tech_targets = {entry["file"]: entry["keys"] for entry in manifest["tech_targets"]}
    invention_targets = {entry["file"]: entry["keys"] for entry in manifest["invention_targets"]}
    localisation_files = manifest["localisation_files"]
    stale_reference_rules = manifest["stale_reference_rules"]
    structural = manifest["structural"]

    failures: list[str] = []
    all_tech_files = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob(TECH_FILES_GLOB))
    all_invention_files = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob(INVENTION_FILES_GLOB))

    tech_def_index = build_top_level_index(all_tech_files)
    inv_def_index = build_top_level_index(all_invention_files)
    loc_index = build_localisation_index(localisation_files)
    loc_keys = set(loc_index.keys())

    for rel_path, keys in tech_targets.items():
        for key in keys:
            locations = tech_def_index.get(key, [])
            if not locations:
                failures.append(f"TECH missing in {rel_path}: {key}")
            if len(locations) > 1:
                failures.append(f"TECH duplicate definition for {key}: {', '.join(locations)}")
            if any(loc != rel_path for loc in locations):
                failures.append(f"TECH unexpected file for {key}: {', '.join(locations)} (expected {rel_path})")
            if key not in loc_keys:
                failures.append(f"TECH missing localisation key: {key}")
            if f"{key}_desc" not in loc_keys:
                failures.append(f"TECH missing localisation desc: {key}_desc")
            if len(loc_index.get(key, [])) > 1:
                failures.append(f"TECH localisation duplicate key {key}: {', '.join(loc_index[key])}")
            if len(loc_index.get(f'{key}_desc', [])) > 1:
                failures.append(
                    f"TECH localisation duplicate desc {key}_desc: {', '.join(loc_index[f'{key}_desc'])}"
                )

    for rel_path, keys in invention_targets.items():
        for key in keys:
            locations = inv_def_index.get(key, [])
            if not locations:
                failures.append(f"INVENTION missing in {rel_path}: {key}")
            if len(locations) > 1:
                failures.append(f"INVENTION duplicate definition for {key}: {', '.join(locations)}")
            if any(loc != rel_path for loc in locations):
                failures.append(
                    f"INVENTION unexpected file for {key}: {', '.join(locations)} (expected {rel_path})"
                )
            if key not in loc_keys:
                failures.append(f"INVENTION missing localisation key: {key}")
            if f"{key}_desc" not in loc_keys:
                failures.append(f"INVENTION missing localisation desc: {key}_desc")
            if len(loc_index.get(key, [])) > 1:
                failures.append(f"INVENTION localisation duplicate key {key}: {', '.join(loc_index[key])}")
            if len(loc_index.get(f'{key}_desc', [])) > 1:
                failures.append(
                    f"INVENTION localisation duplicate desc {key}_desc: {', '.join(loc_index[f'{key}_desc'])}"
                )

    for rule in stale_reference_rules:
        old_key = rule["old_key"]
        new_key = rule["new_key"]
        pattern = re.compile(rf"\b{re.escape(old_key)}\b")
        for rel_path in rule["files"]:
            text = read_text(rel_path)
            for lineno, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    failures.append(
                        f"STALE reference {old_key} found in {rel_path}:{lineno} "
                        f"(expected modern key context: {new_key})"
                    )

    decision_alignment = structural["decision_alignment"]
    setup_text = read_text(decision_alignment["file"])
    end_game_block = re.search(rf"{re.escape(decision_alignment['decision_key'])}\s*=\s*\{{.*?\n\t\t\}}", setup_text, re.S)
    if not end_game_block:
        failures.append(f"STRUCTURAL missing {decision_alignment['decision_key']} block in {decision_alignment['file']}")
    else:
        block = end_game_block.group(0)
        if not re.search(rf"potential\s*=\s*\{{[^}}]*year\s*=\s*{decision_alignment['potential_year']}", block, re.S):
            failures.append(
                f"STRUCTURAL {decision_alignment['decision_key']} potential must include year = {decision_alignment['potential_year']}"
            )
        if not re.search(rf"allow\s*=\s*\{{[^}}]*year\s*=\s*{decision_alignment['allow_year']}", block, re.S):
            failures.append(
                f"STRUCTURAL {decision_alignment['decision_key']} allow must include year = {decision_alignment['allow_year']}"
            )

    for check in structural["required_patterns"]:
        text = read_text(check["file"])
        if not re.search(check["pattern"], text, re.S):
            failures.append(f"STRUCTURAL {check['message']}")

    for check in structural["forbidden_patterns"]:
        text = read_text(check["file"])
        if re.search(check["pattern"], text, re.S):
            failures.append(f"STRUCTURAL {check['message']}")

    for required_file in structural["required_files"]:
        if not (ROOT / required_file).exists():
            failures.append(f"STRUCTURAL missing file: {required_file}")

    print("1966 extension static validation")
    print(f" - scope manifest: {MANIFEST_PATH}")
    print(f" - targeted tech keys: {sum(len(v) for v in tech_targets.values())}")
    print(f" - targeted invention keys: {sum(len(v) for v in invention_targets.values())}")
    print(f" - localisation files scanned: {len(localisation_files)}")
    print(f" - technology files indexed: {len(all_tech_files)}")
    print(f" - invention files indexed: {len(all_invention_files)}")
    print(" - structural alignment checks: defines/decision/backend/readme/audit")

    if failures:
        print("\nFAILED checks:")
        for item in failures:
            print(f" - {item}")
        return 1

    print("\nOK: all targeted late-extension tech/invention keys and localisation entries are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
