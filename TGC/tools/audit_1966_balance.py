#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lib_1966_parser import (
    Node, ScriptError, integer, member, number, parse_file, read_text,
    rebase_path, scalar, unique_definitions, walk,
)

ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "TGC/tools/1966_balance_rules.json"


class Reporter:
    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def add(self, level: str, message: str) -> None:
        self.items.append((level, message))

    def dump(self) -> None:
        levels = ["FAIL", "WARN", "INFO"]
        counts = {k: 0 for k in levels}
        for lvl, _ in self.items:
            counts[lvl] = counts.get(lvl, 0) + 1

        print("1966 BALANCE AUDIT (WARN/INFO diagnostic; FAIL blocks)")
        print(f" - FAIL: {counts.get('FAIL', 0)}")
        print(f" - WARN: {counts.get('WARN', 0)}")
        print(f" - INFO: {counts.get('INFO', 0)}")

        for lvl in levels:
            group = [msg for x, msg in self.items if x == lvl]
            if not group:
                continue
            print(f"\n[{lvl}]")
            for msg in group:
                print(f" - {msg}")


def infer_bucket(message: str) -> str:
    m = message.lower()
    if any(x in m for x in ["build_cost", "upkeep", "key goods", "economic ", "supply_cost"]):
        return "economic plausibility issues"
    if any(x in m for x in ["coverage", "unreadable year", "unknown monitored unit", "missing/unreadable", "cannot estimate", "input error"]):
        return "structural/data confidence issues"
    return "stat progression issues"


def extract_unit_and_subject(message: str) -> tuple[str, str]:
    m_colon = re.match(r"^([a-z0-9_]+):", message)
    if m_colon:
        return m_colon.group(1), "costs/data"
    m_pair = re.match(r"^([a-z0-9_]+)\s+([a-z0-9_]+)\b", message)
    if m_pair:
        return m_pair.group(1), m_pair.group(2)
    return "global", "audit"


def build_stat_tier_map(rules: dict[str, Any], monitored_stats: set[str]) -> dict[str, str]:
    stat_tiers_cfg: dict[str, list[str]] = rules.get("stat_tiers", {})
    tier_by_stat: dict[str, str] = {}
    for tier_name in ("primary", "secondary", "structural"):
        for s in stat_tiers_cfg.get(tier_name, []):
            tier_by_stat[s] = tier_name
    for s in monitored_stats:
        tier_by_stat.setdefault(s, "secondary")
    return tier_by_stat


def get_stat_signal_quality(assignments: int, units_with_signal: int) -> str:
    if assignments == 0:
        return "formal_coverage_only"
    if assignments < 8 or units_with_signal < 2:
        return "limited_signal"
    return "strong_signal"


def build_priority_summary(
    items: list[tuple[str, str]],
    units_cfg: dict[str, Any],
    tier_by_unit: dict[str, str],
    tier_by_stat: dict[str, str],
    stat_signal_quality: dict[str, str],
    stat_priority_weights: dict[str, Any],
) -> tuple[dict[str, list[tuple[int, str]]], list[tuple[int, str]]]:
    buckets: dict[str, list[tuple[int, str]]] = {
        "structural/data confidence issues": [],
        "stat progression issues": [],
        "economic plausibility issues": [],
    }
    playtest_candidates: list[tuple[int, str]] = []

    for level, msg in items:
        if level not in {"FAIL", "WARN"}:
            continue
        unit, subject = extract_unit_and_subject(msg)
        bucket = infer_bucket(msg)
        base = 100 if level == "FAIL" else 60
        score = base

        important_stats = set(units_cfg.get(unit, {}).get("important_stats", []))
        tier = tier_by_unit.get(unit, "secondary")
        if tier == "core":
            score += 20
        elif tier == "secondary":
            score += 5
        elif tier == "low_signal":
            score -= 15
        stat_tier = tier_by_stat.get(subject, "secondary")
        tier_weights = stat_priority_weights.get("tier", {})
        signal_weights = stat_priority_weights.get("signal", {})
        score += int(tier_weights.get(stat_tier, 0))
        signal_quality = stat_signal_quality.get(subject, "limited_signal")
        score += int(signal_weights.get(signal_quality, 0))
        if subject in important_stats:
            score += 20
        if "high-confidence coverage" in msg or "low timeline coverage" in msg:
            score += 15
        if "outside final_range" in msg or "milestone" in msg or "cumulative" in msg:
            score += 10
        if "build_cost outside range" in msg or "upkeep_cost outside range" in msg:
            score += 15

        short = (
            f"{unit} | unit_tier={tier} | stat_tier={stat_tier} | stat_signal={signal_quality} | "
            f"{subject} | {msg} | {level}"
        )
        buckets[bucket].append((score, short))
        structural_warn_floor = int(stat_priority_weights.get("structural_warn_focus_score_min", 100))
        if bucket != "structural/data confidence issues" and not (tier == "low_signal" and level == "WARN"):
            if level == "WARN" and signal_quality == "formal_coverage_only":
                continue
            if level == "WARN" and stat_tier == "structural" and score < structural_warn_floor:
                continue
            playtest_candidates.append((score, f"{unit}: {subject} -> {msg}"))

    for k in buckets:
        buckets[k].sort(key=lambda x: x[0], reverse=True)
    playtest_candidates.sort(key=lambda x: x[0], reverse=True)
    return buckets, playtest_candidates[:5]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the TGC 1966 balance audit against the timeline submod layer.")
    parser.add_argument("--core-root", default="TGC", help="Base/core mod root (default: TGC).")
    parser.add_argument(
        "--timeline-root",
        default="TGC_Timeline_1966",
        help="1966 timeline runtime root (default: TGC_Timeline_1966).",
    )
    return parser.parse_args()


def _rebase_obj(obj: Any, *, core_root: str, timeline_root: str) -> Any:
    if isinstance(obj, str):
        return rebase_path(obj, core_root=core_root, timeline_root=timeline_root)
    if isinstance(obj, list):
        return [_rebase_obj(x, core_root=core_root, timeline_root=timeline_root) for x in obj]
    if isinstance(obj, dict):
        return {k: _rebase_obj(v, core_root=core_root, timeline_root=timeline_root) for k, v in obj.items()}
    return obj


def read_rules(core_root: str = "TGC", timeline_root: str = "TGC_Timeline_1966") -> dict[str, Any]:
    rules = json.loads(read_text(str(RULES_PATH)))
    return _rebase_obj(rules, core_root=core_root, timeline_root=timeline_root)


def get_final_range(stat_cfg: dict[str, Any]) -> tuple[float | None, float | None]:
    final_cfg = stat_cfg.get("final_range", {})
    if not isinstance(final_cfg, dict):
        return None, None
    return final_cfg.get("min"), final_cfg.get("max")


def get_historical_relevance_start_year(unit_cfg: dict[str, Any], default_year: int) -> int:
    value = unit_cfg.get("historical_relevance_start_year", default_year)
    try:
        year = int(value)
    except (TypeError, ValueError):
        return default_year
    return max(year, default_year)


def get_applicable_milestone_years(
    unit_cfg: dict[str, Any],
    milestone_years: list[int],
    default_year: int,
) -> list[int]:
    historical_start_year = get_historical_relevance_start_year(unit_cfg, default_year)
    configured = unit_cfg.get("applicable_milestone_years")
    if configured is None:
        return [year for year in milestone_years if year >= historical_start_year]

    applicable: list[int] = []
    seen: set[int] = set()
    for raw_year in configured:
        try:
            year = int(raw_year)
        except (TypeError, ValueError):
            continue
        if year in milestone_years and year >= historical_start_year and year not in seen:
            applicable.append(year)
            seen.add(year)
    return sorted(applicable)


def numeric_members(node: Node) -> dict[str, float]:
    result: dict[str, float] = {}
    for child in node.children:
        if child.key is None or child.is_group or child.operator != "=":
            raise ScriptError(f"{child.start}: expected a numeric assignment")
        if child.key in result:
            raise ScriptError(f"{child.start}: duplicate numeric property {child.key}")
        result[child.key] = number(child.value, child.start)
    return result


def parse_goods_costs(rel_path: str) -> dict[str, float]:
    costs: dict[str, float] = {}
    categories = unique_definitions(parse_file(rel_path).definitions)
    for category in categories.values():
        for good in unique_definitions(category.children).values():
            cost = scalar(good, "cost", required=True)
            if good.key in costs:
                raise ScriptError(f"{good.start}: duplicate commodity {good.key}")
            costs[good.key] = number(cost, member(good, "cost").start)
    return costs


def parse_unit_block(unit_file: str, unit_key: str) -> dict[str, Any]:
    definitions = unique_definitions(parse_file(unit_file).definitions)
    if unit_key not in definitions:
        raise ScriptError(f"{unit_file}: missing unit definition {unit_key}")
    node = definitions[unit_key]
    data: dict[str, Any] = {"stats": {}, "build_cost": {}, "supply_cost": {},
                            "unit_domain": scalar(node, "type", required=True).lower()}
    if data["unit_domain"] not in {"land", "naval"}:
        raise ScriptError(f"{node.start}: unsupported unit domain {data['unit_domain']!r}")
    for field in ("build_cost", "supply_cost"):
        member(node, field, required=True)
    seen: set[str] = set()
    for child in node.children:
        if child.keyword in seen:
            raise ScriptError(f"{child.start}: duplicate unit property {child.key}")
        seen.add(child.keyword)
        if child.keyword in {"build_cost", "supply_cost"}:
            if not child.is_group or child.operator != "=":
                raise ScriptError(f"{child.start}: expected commodity-cost group")
            data[child.keyword] = numeric_members(child)
        elif not child.is_group and child.operator == "=":
            # Non-numeric flags/names are retained in the tree but are not stats.
            if re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", child.value):
                data["stats"][child.keyword] = number(child.value, child.start)
    return data


def estimate_costs(cost_block: dict[str, float], goods_costs: dict[str, float]) -> tuple[float | None, list[str], list[tuple[str, float]]]:
    missing_goods = [g for g in cost_block if g not in goods_costs]
    if missing_goods:
        return None, missing_goods, []
    contributions = [(g, cost_block[g] * goods_costs[g]) for g in cost_block]
    contributions.sort(key=lambda x: (-x[1], x[0]))
    return sum(v for _, v in contributions), [], contributions[:3]


DefinitionKey = tuple[str, str]


@dataclass(frozen=True)
class YearEvidence:
    # A technology's direct research-year property is a model input, NOT the
    # calendar date at which any particular nation gains its effects.
    year: int | None
    not_before: int | None
    source: str
    notes: tuple[str, ...] = ()
    references: tuple[DefinitionKey, ...] = ()
    probability_years: tuple[int, ...] = ()


def definition_kind(rel_path: str) -> str:
    path = "/" + rel_path.replace("\\", "/").lower()
    if "/technologies/" in path:
        return "technology"
    if "/inventions/" in path:
        return "invention"
    raise ScriptError(f"{rel_path}: explicitly identified technology/invention directory required")


def build_year_inference(scan_files: list[str]) -> dict[DefinitionKey, YearEvidence]:
    """Research-model lower bounds, never exact invention acquisition dates.

    AND takes the maximum known necessary bound; unknown siblings remain noted.
    OR needs a bound for EVERY branch and takes their minimum. NOT and country
    scopes are not converted to positive gates. Synchronous fixed-point updates
    handle chains independently of hash/file order; unresolved cycles stay unknown.
    Scripted early technology grants and actual discovery probability are outside
    this static research model, so even a complete gate only yields a bound.
    """
    definitions: dict[DefinitionKey, Node] = {}
    for rel in sorted(scan_files):
        kind = definition_kind(rel)
        for node in parse_file(rel).definitions:
            key = (kind, node.key)
            if key in definitions:
                raise ScriptError(f"{node.start}: duplicate {kind} {node.key}; first at {definitions[key].start}")
            definitions[key] = node
    definitions = dict(sorted(definitions.items()))

    def reference(node: Node) -> tuple[DefinitionKey | None, str | None]:
        if node.is_group or node.operator != "=":
            return None, None
        if node.keyword == "invention":
            name = node.value
        elif node.value.lower() in {"1", "yes"}:
            name = node.key
        else:
            return None, None
        candidates = [(kind, name) for kind in ("technology", "invention") if (kind, name) in definitions]
        if len(candidates) == 1:
            return candidates[0], None
        if len(candidates) > 1:
            return None, f"ambiguous technology/invention reference: {name}"
        return None, f"unresolved or unmodelled predicate: {name}"

    limits: dict[DefinitionKey, Node | None] = {}
    probability: dict[DefinitionKey, tuple[int, ...]] = {}
    edges: dict[DefinitionKey, set[DefinitionKey]] = {}
    evidence: dict[DefinitionKey, YearEvidence] = {}
    for key, node in definitions.items():
        if key[0] == "technology":
            scalar(node, "area", required=True)
            year = integer(scalar(node, "year", required=True), member(node, "year").start)
            evidence[key] = YearEvidence(year, year, "direct")
            continue
        limit = member(node, "limit")
        if limit is not None and not limit.is_group:
            raise ScriptError(f"{limit.start}: expected limit group")
        limits[key] = limit
        chance = member(node, "chance")
        if chance is not None and not chance.is_group:
            raise ScriptError(f"{chance.start}: expected chance group")
        probability[key] = tuple(sorted({integer(n.value, n.start) for n in walk(chance.children if chance else ())
                                         if n.keyword == "year" and not n.is_group}))
        evidence[key] = YearEvidence(None, None, "unknown", probability_years=probability[key])
        refs: set[DefinitionKey] = set()

        def collect(nodes: tuple[Node, ...]) -> None:
            for child in nodes:
                if child.is_group and child.keyword in {"and", "or"}:
                    collect(child.children)
                elif not child.is_group and child.keyword != "year":
                    ref, _ = reference(child)
                    if ref is not None:
                        refs.add(ref)
        collect(limit.children if limit else ())
        edges[key] = refs

    def in_cycle(start: DefinitionKey) -> bool:
        pending = list(edges.get(start, ()))
        seen: set[DefinitionKey] = set()
        while pending:
            item = pending.pop()
            if item == start:
                return True
            if item not in seen:
                seen.add(item)
                pending.extend(edges.get(item, ()))
        return False

    cycles = {key for key in limits if in_cycle(key)}

    def condition(nodes: tuple[Node, ...], previous: dict[DefinitionKey, YearEvidence],
                  *, disjunction: bool = False) -> tuple[int | None, set[str]]:
        bounds: list[int | None] = []
        notes: set[str] = set()
        for child in nodes:
            bound = None
            if child.is_group:
                if child.keyword in {"and", "or"} and child.operator == "=":
                    bound, subnotes = condition(child.children, previous, disjunction=child.keyword == "or")
                    notes.update(subnotes)
                else:
                    notes.add(f"unmodelled/negated scope: {child.key}")
            elif child.keyword == "year" and child.operator in {"=", ">=", "==", ">"}:
                bound = integer(child.value, child.start) + (child.operator == ">")
            else:
                ref, note = reference(child)
                if note:
                    notes.add(note)
                if ref is not None:
                    bound = previous[ref].not_before
                    if bound is None:
                        notes.add(f"unresolved availability: {ref[0]}:{ref[1]}")
                elif note is None:
                    notes.add(f"unmodelled predicate: {child.key}")
            bounds.append(bound)
        if disjunction:
            return (min(bounds) if bounds and all(b is not None for b in bounds) else None), notes
        known = [b for b in bounds if b is not None]
        return (max(known) if known else None), notes

    while True:
        updated = dict(evidence)
        for key, limit in limits.items():
            bound, notes = condition(limit.children, evidence) if limit else (None, {"no availability limit"})
            if key in cycles:
                notes.add("cycle in availability prerequisites")
            if member(definitions[key], "year") is not None:
                notes.add("unsupported direct invention year; not an acquisition date")
            updated[key] = YearEvidence(None, bound, "availability_bound" if bound is not None else "unknown",
                                        tuple(sorted(notes)), tuple(sorted(edges[key])), probability[key])
        # Bounds live on the finite set of source-year anchors. Notes are derived
        # again from the stable bounds so discovery order never enters provenance.
        if all(updated[k].not_before == evidence[k].not_before for k in evidence):
            return dict(sorted(updated.items()))
        evidence = updated


def parse_effect_unit_assignments(
    rel_path: str,
    monitored_units: set[str],
    monitored_stats: set[str],
    inferred_years: dict[DefinitionKey, YearEvidence],
    global_scope_units: dict[str, set[str]],
    *,
    known_units: set[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    kind = definition_kind(rel_path)
    definitions = unique_definitions(parse_file(rel_path).definitions)
    for key, definition in definitions.items():
        if (kind, key) not in inferred_years:
            raise ScriptError(f"{definition.start}: missing temporal evidence for {kind}:{key}")
        timing = inferred_years[(kind, key)]
        effect = member(definition, "effect") if kind == "invention" else definition
        if effect is None:
            continue
        if not effect.is_group:
            raise ScriptError(f"{effect.start}: expected effect group")
        for scope in effect.children:
            targets = {scope.key} if scope.key in monitored_units else global_scope_units.get(scope.key, set())
            if not targets:
                if (known_units is not None and scope.key not in known_units and scope.key not in global_scope_units and scope.is_group
                        and any(n.keyword in monitored_stats for n in scope.children)):
                    raise ScriptError(f"{scope.start}: unknown unit-effect scope {scope.key}")
                continue
            if not scope.is_group or scope.operator != "=":
                raise ScriptError(f"{scope.start}: expected unit modifier group")
            seen: set[str] = set()
            for stat in scope.children:
                if stat.key is None:
                    raise ScriptError(f"{stat.start}: unsupported free entry in unit modifier")
                if stat.keyword not in monitored_stats:
                    continue
                if stat.keyword in seen:
                    raise ScriptError(f"{stat.start}: duplicate/ambiguous unit modifier {stat.key}")
                seen.add(stat.keyword)
                if stat.is_group or stat.operator != "=":
                    raise ScriptError(f"{stat.start}: expected numeric unit modifier")
                value = number(stat.value, stat.start)
                for target in sorted(targets):
                    out[target].append({
                        "source_file": rel_path, "invention": key, "line": stat.start.line,
                        "column": stat.start.column, "stat": stat.keyword, "value": value,
                        "year": timing.year, "not_before": timing.not_before, "year_source": timing.source,
                        "year_notes": timing.notes, "year_references": timing.references,
                        "probability_years": timing.probability_years,
                        "scope_key": scope.key, "scope_kind": "unit" if scope.key in monitored_units else "global",
                    })
    return dict(sorted(out.items()))


def milestone_envelope(baseline: float, assignments: list[dict[str, Any]], year: int) -> tuple[float, float]:
    """All possible placements under the static model; no invented event dates."""
    low = high = baseline
    for item in assignments:
        if item.get("year") is not None:
            if item["year"] <= year:
                low += item["value"]
                high += item["value"]
        elif item.get("not_before") is None or item["not_before"] <= year:
            low += min(0., item["value"])
            high += max(0., item["value"])
    return low, high


def format_assignment_origin(item: dict[str, Any]) -> str:
    scope_key = item.get("scope_key") or "unknown_scope"
    scope_kind = item.get("scope_kind") or "unit"
    scope_txt = f"{scope_kind}:{scope_key}"
    return f"{scope_txt} in {item['source_file']}:{item['line']}:{item['column']} ({item['invention']})"


def check_key_goods_availability(production_types_file: str, key_goods: list[str], rep: Reporter) -> None:
    nodes = tuple(walk(parse_file(production_types_file).definitions))
    outputs = {n.value for n in nodes if n.keyword == "output_goods" and not n.is_group and n.operator == "="}
    for good in key_goods:
        if good in outputs:
            rep.add("INFO", f"KEY GOODS mapping present in production types: {good}")
        else:
            rep.add("WARN", f"KEY GOODS missing production output mapping: {good}")


def _run() -> int:
    args = parse_args()
    rules = read_rules(args.core_root, args.timeline_root)
    rep = Reporter()
    rep.add("INFO", f"AUDIT ROOTS: core={args.core_root}; timeline={args.timeline_root}")

    units_cfg: dict[str, Any] = rules["units"]
    coverage_tiers_cfg: dict[str, list[str]] = rules.get("coverage_tiers", {})
    tier_by_unit: dict[str, str] = {}
    for tier_name in ("core", "secondary", "low_signal"):
        for u in coverage_tiers_cfg.get(tier_name, []):
            tier_by_unit[u] = tier_name
    for u in units_cfg:
        tier_by_unit.setdefault(u, "secondary")
    files_cfg: dict[str, str] = rules["files"]
    monitored_units = set(units_cfg.keys())
    discovered_units: set[str] = set()
    for rel_dir in (f"{args.core_root}/units", f"{args.timeline_root}/units"):
        unit_dir = ROOT / rel_dir
        if unit_dir.exists():
            discovered_units.update(p.stem for p in unit_dir.glob("*.txt"))
    unit_groups: dict[str, list[str]] = rules.get("unit_groups", {})
    coverage_cfg: dict[str, Any] = rules.get("timeline_coverage", {})
    coverage_warn_below = float(coverage_cfg.get("warn_below_pct_important", 60))
    coverage_info_good = float(coverage_cfg.get("info_good_pct", 80))
    confidence_cfg: dict[str, Any] = rules.get("confidence_coverage", {})
    confidence_time_high = float(confidence_cfg.get("time_high_pct", 80))
    confidence_high_warn_below = float(confidence_cfg.get("high_conf_warn_below_pct", 50))
    confidence_high_good = float(confidence_cfg.get("high_conf_info_good_pct", 70))
    monitored_stats_set = set(rules["monitored_stat_catalog"])
    tier_by_stat = build_stat_tier_map(rules, monitored_stats_set)
    stat_priority_weights: dict[str, Any] = rules.get("stat_priority_weights", {})
    detected_stats_by_unit: dict[str, set[str]] = {}
    covered_stats_by_unit: dict[str, set[str]] = {}
    unit_domain_by_unit: dict[str, str | None] = {}

    for group_name, members in unit_groups.items():
        unknown_members = [u for u in members if u not in discovered_units]
        if unknown_members:
            rep.add("WARN", f"UNIT GROUP {group_name}: unknown members {', '.join(sorted(unknown_members))}")
        else:
            rep.add("INFO", f"UNIT GROUP {group_name}: {len(members)} member(s)")

    # 1) unit target sconosciute nelle regole
    for unit in sorted(monitored_units):
        if unit not in discovered_units:
            rep.add("FAIL", f"RULES unknown monitored unit target: {unit}")

    goods_costs = parse_goods_costs(files_cfg["goods"])

    baselines: dict[str, dict[str, float]] = defaultdict(dict)

    # 2) stat monitorate mancanti/non leggibili + 5) costo build/upkeep non calcolabile
    for unit, cfg in units_cfg.items():
        unit_data = parse_unit_block(cfg["unit_file"], unit)
        stats = unit_data["stats"]
        unit_domain_by_unit[unit] = unit_data.get("unit_domain")
        detected_stats = {s for s in stats.keys() if s in monitored_stats_set}
        covered_stats = {s for s in cfg.get("monitored_stats", {}).keys() if s in monitored_stats_set}
        detected_stats_by_unit[unit] = detected_stats
        covered_stats_by_unit[unit] = covered_stats
        missing_coverage = sorted(detected_stats - covered_stats)
        if missing_coverage:
            rep.add("WARN", f"{unit}: unit stats detected but not covered by rules: {', '.join(missing_coverage)}")

        for stat, stat_cfg in cfg["monitored_stats"].items():
            if stat not in stats:
                rep.add("FAIL", f"{unit}: monitored stat missing/unreadable in unit file: {stat}")
            else:
                baseline = stats[stat]
                baselines[unit][stat] = baseline
                rep.add("INFO", f"{unit}: baseline {stat}={baseline}")

        est_build, miss_build, top_build = estimate_costs(unit_data["build_cost"], goods_costs)
        est_upkeep, miss_upkeep, top_upkeep = estimate_costs(unit_data["supply_cost"], goods_costs)

        if miss_build:
            rep.add("FAIL", f"{unit}: cannot estimate build_cost; missing goods costs: {', '.join(sorted(miss_build))}")
        if miss_upkeep:
            rep.add("FAIL", f"{unit}: cannot estimate supply_cost; missing goods costs: {', '.join(sorted(miss_upkeep))}")

        if est_build is not None:
            build_top = ", ".join(f"{g}={v:.2f}" for g, v in top_build) if top_build else "none"
            rep.add("INFO", f"{unit}: economic build_est={est_build:.2f}; top3_build=[{build_top}]")
            build_range = cfg.get("estimated_build_cost_range", {})
            b_min = build_range.get("min")
            b_max = build_range.get("max")
            if (b_min is not None and est_build < b_min) or (b_max is not None and est_build > b_max):
                rep.add("WARN", f"{unit}: estimated build_cost outside range ({est_build:.2f}, expected {b_min}..{b_max})")

        if est_upkeep is not None:
            upkeep_top = ", ".join(f"{g}={v:.2f}" for g, v in top_upkeep) if top_upkeep else "none"
            rep.add("INFO", f"{unit}: economic upkeep_est={est_upkeep:.2f}; top3_upkeep=[{upkeep_top}]")
            upkeep_range = cfg.get("estimated_upkeep_cost_range", {})
            u_min = upkeep_range.get("min")
            u_max = upkeep_range.get("max")
            if (u_min is not None and est_upkeep < u_min) or (u_max is not None and est_upkeep > u_max):
                rep.add("WARN", f"{unit}: estimated upkeep_cost outside range ({est_upkeep:.2f}, expected {u_min}..{u_max})")

        expected_goods = set(cfg.get("key_goods_expectations", []))
        unit_goods = set(unit_data["build_cost"].keys()) | set(unit_data["supply_cost"].keys())
        if expected_goods and expected_goods.isdisjoint(unit_goods):
            rep.add(
                "WARN",
                f"{unit}: none of expected key goods found in unit costs ({', '.join(sorted(expected_goods))})",
            )

    land_units = {u for u, domain in unit_domain_by_unit.items() if domain == "land"}
    naval_units = {u for u, domain in unit_domain_by_unit.items() if domain == "naval"}
    if not land_units:
        land_units = set(unit_groups.get("all_land_units", [])) & monitored_units
    if not naval_units:
        naval_units = set(unit_groups.get("all_naval_units", [])) & monitored_units
    global_scope_units: dict[str, set[str]] = {
        "army_base": set(land_units),
        "navy_base": set(naval_units),
    }

    milestone_years: list[int] = sorted(
        int(y) for y in rules.get("milestone_years", [1836, 1850, 1870, 1900, 1910, 1919, 1929, 1936, 1945, 1955, 1966])
    )
    default_milestone_year = milestone_years[0] if milestone_years else 1836
    inferred_years = build_year_inference(rules["scan_files"])
    direct_blocks = sum(e.source == "direct" for e in inferred_years.values())
    bound_blocks = sum(e.source == "availability_bound" for e in inferred_years.values())
    unknown_blocks = len(inferred_years) - direct_blocks - bound_blocks
    rep.add("INFO", f"YEAR EVIDENCE: {len(inferred_years)} definitions [research_year={direct_blocks}, availability_bound={bound_blocks}, unknown={unknown_blocks}]")
    rep.add("INFO", "DATING MODEL: technology research-year anchors; invention gates are lower bounds, not acquisition dates. Probability modifiers, scripted early grants, discovery timing and actual nation histories are not simulated.")
    for (kind, key), evidence in inferred_years.items():
        if kind == "invention":
            rep.add("INFO", f"AVAILABILITY {key}: not_before={evidence.not_before}; source={evidence.source}; "
                    f"probability_years={list(evidence.probability_years)} (not availability gates); "
                    f"references={list(evidence.references)}; notes={'; '.join(evidence.notes) or 'bound only; acquisition unknown'}")
    all_assignments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rel in sorted(rules["scan_files"]):
        found = parse_effect_unit_assignments(
            rel,
            monitored_units,
            monitored_stats_set,
            inferred_years,
            global_scope_units,
            known_units=discovered_units,
        )
        for k, vals in found.items():
            all_assignments[k].extend(vals)

    relevant_assignments_by_unit: dict[str, list[dict[str, Any]]] = {}
    for u, cfg in units_cfg.items():
        monitored_stats = set(cfg.get("monitored_stats", {}).keys())
        relevant_assignments_by_unit[u] = [
            item for item in all_assignments.get(u, []) if item.get("stat") in monitored_stats
        ]

    stat_assignment_count: dict[str, int] = defaultdict(int)
    stat_assignment_units: dict[str, set[str]] = defaultdict(set)
    covered_units_by_stat: dict[str, int] = defaultdict(int)
    for u, cfg in units_cfg.items():
        for s in cfg.get("monitored_stats", {}):
            covered_units_by_stat[s] += 1
        for item in relevant_assignments_by_unit.get(u, []):
            s = item.get("stat")
            if not s:
                continue
            stat_assignment_count[s] += 1
            stat_assignment_units[s].add(u)
    stat_signal_quality: dict[str, str] = {}
    for s in monitored_stats_set:
        stat_signal_quality[s] = get_stat_signal_quality(
            stat_assignment_count.get(s, 0),
            len(stat_assignment_units.get(s, set())),
        )

    relevant_assignment_items = [x for vals in relevant_assignments_by_unit.values() for x in vals]
    total_effect_assignments = len(relevant_assignment_items)
    direct_assignments = sum(x.get("year_source") == "direct" for x in relevant_assignment_items)
    bound_assignments = sum(x.get("year_source") == "availability_bound" for x in relevant_assignment_items)
    unknown_assignments = total_effect_assignments - direct_assignments - bound_assignments
    rep.add("INFO", f"MODEL DATE PLACEMENT (count): research_year_anchors={direct_assignments}/{total_effect_assignments}, "
            f"availability_bounds={bound_assignments}, unconstrained={unknown_assignments}")
    rep.add("INFO", "TIMELINE CONFIDENCE: only research-year anchors enter point sums; invention bounds enter possibility envelopes, never exact-year sums.")
    tech_items = [x for x in relevant_assignment_items if "/technologies/" in x.get("source_file", "")]
    inv_items = [x for x in relevant_assignment_items if "/inventions/" in x.get("source_file", "")]
    unit_scoped_assignments = sum(1 for x in relevant_assignment_items if x.get("scope_kind") == "unit")
    global_scoped_assignments = sum(1 for x in relevant_assignment_items if x.get("scope_kind") == "global")
    global_scope_breakdown: dict[str, int] = defaultdict(int)
    for item in relevant_assignment_items:
        if item.get("scope_kind") == "global":
            global_scope_breakdown[item.get("scope_key", "global")] += 1
    if global_scope_breakdown:
        detail = ", ".join(f"{k}={v}" for k, v in sorted(global_scope_breakdown.items()))
        rep.add(
            "INFO",
            f"EFFECT SCOPE COUNTS: unit_scoped={unit_scoped_assignments}, global_scoped={global_scoped_assignments} [{detail}]",
        )
    else:
        rep.add(
            "INFO",
            f"EFFECT SCOPE COUNTS: unit_scoped={unit_scoped_assignments}, global_scoped={global_scoped_assignments}",
        )

    def _src_counts(items: list[dict[str, Any]]) -> tuple[int, int, int, int]:
        direct = sum(1 for x in items if x.get("year_source") == "direct")
        inferred = sum(1 for x in items if x.get("year_source") == "availability_bound")
        unknown = sum(1 for x in items if x.get("year_source") == "unknown")
        return len(items), direct, inferred, unknown

    t_total, t_direct, t_inferred, t_unknown = _src_counts(tech_items)
    i_total, i_direct, i_inferred, i_unknown = _src_counts(inv_items)
    rep.add(
        "INFO",
        "TIMELINE CONFIDENCE BY SOURCE: "
        f"tech_total={t_total}, tech_direct={t_direct}, tech_bounds={t_inferred}, tech_unknown={t_unknown}, "
        f"invention_total={i_total}, invention_direct={i_direct}, invention_bounds={i_inferred}, invention_unknown={i_unknown}",
    )
    direct_tech_examples = [x for x in tech_items if x.get("year_source") == "direct"][:3]
    if direct_tech_examples:
        for ex in direct_tech_examples:
            rep.add(
                "INFO",
                f"DIRECT TECH EXAMPLE: {format_assignment_origin(ex)} {ex['stat']}={ex['value']} year={ex.get('year')}",
            )
    else:
        rep.add("INFO", "DIRECT TECH EXAMPLE: none found in current scanned assignments")

    invention_examples = inv_items[:3]
    if invention_examples:
        for ex in invention_examples:
            rep.add(
                "INFO",
                f"INVENTION EXAMPLE: {format_assignment_origin(ex)} {ex['stat']}={ex['value']} "
                f"model_year={ex.get('year')} not_before={ex.get('not_before')} source={ex.get('year_source') or 'unknown'}",
            )
    else:
        rep.add("WARN", "INVENTION EXAMPLE: none found for monitored units in scanned invention files")

    # v3 signal-quality summary per unit: helps distinguish broad coverage from high-value coverage.
    signal_summary: dict[str, dict[str, int]] = {}
    for unit, cfg in units_cfg.items():
        unit_items = relevant_assignments_by_unit.get(unit, [])
        monitored_stats = set(cfg.get("monitored_stats", {}).keys())
        touched_stats = {x.get("stat") for x in unit_items if x.get("stat") in monitored_stats}
        signal_summary[unit] = {
            "assignments": len(unit_items),
            "touched_stats": len(touched_stats),
            "monitored_stats": len(monitored_stats),
        }
        rep.add(
            "INFO",
            f"{unit}: signal assignments={len(unit_items)}, monitored_stats={len(monitored_stats)}, touched_stats={len(touched_stats)}",
        )
        if len(unit_items) == 0:
            rep.add("WARN", f"{unit}: no readable timed deltas found in scanned files; coverage is baseline/economic only")

    # 3) delta singolo oltre soglia + 4) delta cumulative oltre soglia + 5) stima finale fuori range assoluto
    cumulative_positive: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    cumulative_negative: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for unit, cfg in units_cfg.items():
        for item in relevant_assignments_by_unit.get(unit, []):
            stat = item["stat"]
            delta = item["value"]
            s_cfg = cfg["monitored_stats"].get(stat)
            if not s_cfg:
                continue
            max_delta = s_cfg.get("max_single_delta")

            if delta >= 0:
                cumulative_positive[unit][stat] += delta
            else:
                cumulative_negative[unit][stat] += delta
            if max_delta is not None and abs(delta) > max_delta:
                rep.add(
                    "WARN",
                    f"{unit} {stat} delta too large from {format_assignment_origin(item)} ({delta}, max_single_delta {max_delta})",
                )

    assignments_by_unit_stat: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for unit, unit_items in relevant_assignments_by_unit.items():
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in unit_items:
            stat_name = item.get("stat")
            if not stat_name:
                continue
            grouped[stat_name].append(item)
        assignments_by_unit_stat[unit] = grouped

    for unit, cfg in units_cfg.items():
        historical_start_year = get_historical_relevance_start_year(cfg, default_milestone_year)
        applicable_milestone_years = get_applicable_milestone_years(cfg, milestone_years, default_milestone_year)
        applicable_milestone_years_set = set(applicable_milestone_years)
        for stat, s_cfg in cfg["monitored_stats"].items():
            baseline = baselines.get(unit, {}).get(stat)
            if baseline is None:
                continue
            pos_delta = cumulative_positive[unit][stat]
            neg_delta = cumulative_negative[unit][stat]
            total_delta = pos_delta + neg_delta
            estimated_final = baseline + total_delta

            stat_assignments = assignments_by_unit_stat.get(unit, {}).get(stat, [])
            unknown_year_delta = sum(a["value"] for a in stat_assignments if a.get("year") is None)
            unknown_year_count = sum(1 for a in stat_assignments if a.get("year") is None)
            known_year_count = len(stat_assignments) - unknown_year_count
            known_years = sorted({a["year"] for a in stat_assignments if a.get("year") is not None})
            first_known_year = known_years[0] if known_years else None
            last_known_year = known_years[-1] if known_years else None
            milestone_bounds = {year: milestone_envelope(baseline, stat_assignments, year) for year in milestone_years}

            total_abs_delta = sum(abs(a["value"]) for a in stat_assignments)
            unit_scope_abs_delta = sum(abs(a["value"]) for a in stat_assignments if a.get("scope_kind") == "unit")
            global_scope_abs_delta = sum(abs(a["value"]) for a in stat_assignments if a.get("scope_kind") == "global")
            known_abs_delta = sum(abs(a["value"]) for a in stat_assignments if a.get("year") is not None)
            unknown_abs_delta = total_abs_delta - known_abs_delta
            coverage_pct = 0.0 if total_abs_delta == 0 else (known_abs_delta / total_abs_delta) * 100.0
            direct_abs_delta = sum(abs(a["value"]) for a in stat_assignments if a.get("year_source") == "direct")
            bound_abs_delta = sum(abs(a["value"]) for a in stat_assignments if a.get("year_source") == "availability_bound")
            high_conf_abs = direct_abs_delta
            high_conf_pct = 0.0 if total_abs_delta == 0 else (high_conf_abs / total_abs_delta) * 100.0

            technical_milestone_estimates: list[str] = []
            for year in milestone_years:
                lo, hi = milestone_bounds[year]
                technical_milestone_estimates.append(f"{year}:[{lo:.3f},{hi:.3f}]")
            applicable_milestone_estimates: list[str] = []
            for year in applicable_milestone_years:
                lo, hi = milestone_bounds[year]
                applicable_milestone_estimates.append(f"{year}:[{lo:.3f},{hi:.3f}]")

            rep.add(
                "INFO",
                f"{unit} {stat}: baseline_raw {baseline:.3f}, "
                f"first_research_year {first_known_year if first_known_year is not None else 'n/a'}, "
                f"last_research_year {last_known_year if last_known_year is not None else 'n/a'}, "
                f"cumulative +{pos_delta:.3f}, cumulative -{abs(neg_delta):.3f}, "
                f"technical_envelopes[{', '.join(technical_milestone_estimates)}], "
                f"applicable_envelopes[{', '.join(applicable_milestone_estimates)}], estimated_final_all_effects_scenario {estimated_final:.3f}, "
                f"scope_unit {unit_scope_abs_delta:.3f}, scope_global {global_scope_abs_delta:.3f}, "
                f"research_anchor_abs {direct_abs_delta:.3f}, availability_bound_abs {bound_abs_delta:.3f}, "
                f"unconstrained_abs {unknown_abs_delta - bound_abs_delta:.3f}, "
                f"point_model_coverage {coverage_pct:.1f}%, research_anchor_share {high_conf_pct:.1f}%",
            )
            if unknown_year_count > 0:
                rep.add(
                    "INFO",
                    f"{unit} {stat}: uncertain-date deltas included only as possibility envelopes: count={unknown_year_count}, total={unknown_year_delta:+.3f} "
                    f"(known_count={known_year_count})",
                )
            important_stats = set(cfg.get("important_stats", []))
            if total_abs_delta > 0 and stat in important_stats and coverage_pct < coverage_warn_below:
                rep.add(
                    "WARN",
                    f"{unit} {stat} low timeline coverage ({coverage_pct:.1f}% < {coverage_warn_below:.1f}%; point-model research anchors only)",
                )
            elif coverage_pct >= coverage_info_good:
                rep.add("INFO", f"{unit} {stat} point-model timeline coverage is good ({coverage_pct:.1f}%; research anchors only)")
            if (
                total_abs_delta > 0
                and stat in important_stats
                and coverage_pct >= confidence_time_high
                and high_conf_pct < confidence_high_warn_below
            ):
                rep.add(
                    "WARN",
                    f"{unit} {stat} timeline mostly placed but low high-confidence coverage ({high_conf_pct:.1f}% < {confidence_high_warn_below:.1f}%)",
                )
            elif high_conf_pct >= confidence_high_good:
                rep.add("INFO", f"{unit} {stat} research-anchor coverage is good ({high_conf_pct:.1f}%; not actual acquisition dates)")
            max_pos = s_cfg.get("max_cumulative_positive_delta")
            max_neg = s_cfg.get("max_cumulative_negative_delta")
            if max_pos is not None and pos_delta > max_pos:
                rep.add(
                    "WARN",
                    f"{unit} {stat} cumulative positive delta too large (+{pos_delta:.3f}, max {max_pos})",
                )
            if max_neg is not None and abs(neg_delta) > max_neg:
                rep.add(
                    "WARN",
                    f"{unit} {stat} cumulative negative delta too large ({neg_delta:.3f}, max -{max_neg})",
                )
            min_final, max_final = get_final_range(s_cfg)
            if (min_final is not None and estimated_final < min_final) or (max_final is not None and estimated_final > max_final):
                rep.add(
                    "WARN",
                    f"{unit} {stat} estimated final outside final_range in all-effects scenario (baseline {baseline:.3f} + delta {total_delta:+.3f} = {estimated_final:.3f}, expected {min_final}..{max_final})",
                )
            milestone_ranges = s_cfg.get("milestone_ranges", {})
            configured_milestone_years: set[int] = set()
            for raw_year in milestone_ranges.keys():
                try:
                    configured_milestone_years.add(int(raw_year))
                except (TypeError, ValueError):
                    continue
            non_applicable_configured_years = sorted(configured_milestone_years - applicable_milestone_years_set)
            if non_applicable_configured_years:
                years_txt = ", ".join(str(y) for y in non_applicable_configured_years)
                rep.add(
                    "WARN",
                    f"{unit} {stat}: milestone_ranges configured for non-applicable years [{years_txt}] "
                    f"(historical_relevance_start_year={historical_start_year}, applicable_milestone_years={applicable_milestone_years})",
                )

            for year in applicable_milestone_years:
                cfg_y = milestone_ranges.get(str(year)) or milestone_ranges.get(year)
                if not cfg_y:
                    continue
                m_min = cfg_y.get("min")
                m_max = cfg_y.get("max")
                lo, hi = milestone_bounds[year]
                if (m_min is not None and hi < m_min) or (m_max is not None and lo > m_max):
                    rep.add("WARN", f"{unit} {stat} milestone {year} entirely outside configured range "
                            f"(possible {lo:.3f}..{hi:.3f}, expected {m_min}..{m_max})")
                elif (m_min is not None and lo < m_min) or (m_max is not None and hi > m_max):
                    rep.add("INFO", f"{unit} {stat} milestone {year} indeterminate: uncertainty envelope "
                            f"{lo:.3f}..{hi:.3f} overlaps configured range {m_min}..{m_max}")

    check_key_goods_availability(files_cfg["production_types"], rules["economic"]["key_goods"], rep)

    rep.dump()
    priority_buckets, playtest_focus = build_priority_summary(
        rep.items,
        units_cfg,
        tier_by_unit,
        tier_by_stat,
        stat_signal_quality,
        stat_priority_weights,
    )
    print("\nPRIORITY SUMMARY")
    for bucket in ("structural/data confidence issues", "stat progression issues", "economic plausibility issues"):
        print(f"\n - {bucket}")
        top_items = priority_buckets.get(bucket, [])[:8]
        if not top_items:
            print("   * none")
            continue
        for score, text in top_items:
            print(f"   * [score {score}] {text}")

    print("\nRECOMMENDED PLAYTEST FOCUS")
    if not playtest_focus:
        print(" - No high-priority WARN/FAIL playtest targets identified from current run.")
    else:
        for _, text in playtest_focus:
            print(f" - {text}")

    # Tiered watchlists (short practical summary by unit).
    fail_by_unit = {extract_unit_and_subject(msg)[0] for lvl, msg in rep.items if lvl == "FAIL"}
    main_warn_by_unit: dict[str, str] = {}
    for lvl, msg in rep.items:
        if lvl not in {"FAIL", "WARN"}:
            continue
        u, _ = extract_unit_and_subject(msg)
        if u not in units_cfg:
            continue
        current = main_warn_by_unit.get(u)
        if current is None:
            main_warn_by_unit[u] = msg
            continue
        if lvl == "WARN" and u in fail_by_unit:
            continue
        if "milestone" in msg and "milestone" not in current:
            main_warn_by_unit[u] = msg

    def _print_watchlist(title: str, tier_name: str) -> None:
        print(f"\n{title}")
        members = sorted(u for u in units_cfg if tier_by_unit.get(u, "secondary") == tier_name)
        if not members:
            print(" - none")
            return
        for u in members:
            sig = signal_summary.get(u, {"assignments": 0, "touched_stats": 0})
            top_warn = main_warn_by_unit.get(u, "none")
            print(
                f" - {u} | tier={tier_name} | signal_assignments={sig['assignments']} | "
                f"touched_stats={sig['touched_stats']} | top_warning={top_warn}"
            )

    _print_watchlist("CORE WATCHLIST", "core")
    _print_watchlist("SECONDARY WATCHLIST", "secondary")
    _print_watchlist("LOW-SIGNAL COVERAGE", "low_signal")

    print("\nSTAT COVERAGE SUMMARY")
    total_detected = sum(len(v) for v in detected_stats_by_unit.values())
    total_covered = sum(len(covered_stats_by_unit.get(u, set()) & detected_stats_by_unit.get(u, set())) for u in units_cfg)
    global_detected_stats = sorted({s for vals in detected_stats_by_unit.values() for s in vals})
    global_covered_stats = sorted({s for vals in covered_stats_by_unit.values() for s in vals})
    print(f" - total_covered_stats={total_covered}")
    print(f" - total_detected_stats={total_detected}")
    print(f" - global_detected_stat_types={len(global_detected_stats)}")
    print(f" - global_covered_stat_types={len(global_covered_stats)}")
    for u in sorted(units_cfg):
        det = detected_stats_by_unit.get(u, set())
        cov = covered_stats_by_unit.get(u, set()) & det
        missing = sorted(det - cov)
        if missing:
            print(f" - {u}: covered_stats={len(cov)}/{len(det)} missing={', '.join(missing)}")
        else:
            print(f" - {u}: covered_stats={len(cov)}/{len(det)}")

    print("\nSTAT DIAGNOSTIC QUALITY")
    for tier_name in ("primary", "secondary", "structural"):
        print(f" - {tier_name.upper()}")
        stats = [s for s, t in tier_by_stat.items() if t == tier_name]
        if not stats:
            print("   * none")
            continue
        for s in sorted(stats):
            covered_units = covered_units_by_stat.get(s, 0)
            assignments = stat_assignment_count.get(s, 0)
            units_with_signal = len(stat_assignment_units.get(s, set()))
            quality = stat_signal_quality.get(s, "limited_signal")
            print(
                f"   * {s}: covered_units={covered_units}, assignments={assignments}, "
                f"units_with_signal={units_with_signal}, quality={quality}"
            )

    print("\nTOP STAT WATCHLIST")
    stat_watch: dict[str, tuple[int, str]] = {}
    for level, msg in rep.items:
        if level not in {"FAIL", "WARN"}:
            continue
        unit, subject = extract_unit_and_subject(msg)
        if subject not in monitored_stats_set:
            continue
        score = 100 if level == "FAIL" else 60
        score += int(stat_priority_weights.get("tier", {}).get(tier_by_stat.get(subject, "secondary"), 0))
        score += int(stat_priority_weights.get("signal", {}).get(stat_signal_quality.get(subject, "limited_signal"), 0))
        score += 10 if tier_by_unit.get(unit, "secondary") == "core" else 0
        prev = stat_watch.get(subject)
        if prev is None or score > prev[0]:
            stat_watch[subject] = (score, msg)
    top_stats = sorted(stat_watch.items(), key=lambda x: x[1][0], reverse=True)[:8]
    if not top_stats:
        print(" - none")
    else:
        for stat, (score, msg) in top_stats:
            print(
                f" - {stat} | tier={tier_by_stat.get(stat, 'secondary')} | "
                f"units_with_signal={len(stat_assignment_units.get(stat, set()))} | "
                f"quality={stat_signal_quality.get(stat, 'limited_signal')} | score={score} | top_issue={msg}"
            )

    # WARN/INFO diagnostics are non-blocking, but FAIL-level structural/tooling errors should fail CI.
    return 1 if any(level == "FAIL" for level, _ in rep.items) else 0


def main() -> int:
    try:
        return _run()
    except (ScriptError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        rep = Reporter()
        rep.add("FAIL", f"INPUT ERROR: {exc}; analysis aborted, no partial conclusions")
        rep.dump()
        print("\nPRIORITY SUMMARY\n - structural/data confidence issues: input error")
        print("\nRECOMMENDED PLAYTEST FOCUS\n - Unavailable: analysis aborted before valid conclusions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
