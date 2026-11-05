#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lib_1966_parser import (
    Node, ScriptError, integer, member, number, parse_file, read_text,
    rebase_path, scalar, unique_definitions, walk, read_json,
)
from lib_1966_diagnostics import Reporter
from lib_1966_mechanics import report_consumers, report_availability
from lib_1966_runtime import compose_runtime, unit_definitions
from lib_1966_semantics import (
    ALICE, V2, BASE_KNOWN, canonical_stat, effect_body,
    named_entries, numeric_modifier_entries, property_evidence, projected_stat, project_unit, VARIABLE, report_modifier_semantics,
)

ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "TGC/tools/1966_balance_rules.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the TGC 1966 balance audit against the timeline submod layer.")
    parser.add_argument("--json", action="store_true", help="Emit structured diagnostics as JSON only.")
    parser.add_argument("--summary", action="store_true", help="Print counts and grouped findings without the detailed report.")
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
    rules = read_json(str(RULES_PATH))
    validate_rule_structure(rules)
    return _rebase_obj(rules, core_root=core_root, timeline_root=timeline_root)


def validate_rule_structure(rules: dict) -> None:
    """Technical shape checks only, never a calibration of normative values."""
    def numeric(value):
        try:
            return type(value) in {int, float} and math.isfinite(value)
        except OverflowError:
            return False

    def interval(value, where):
        if not isinstance(value, dict) or any(k not in {'min', 'max'} for k in value):
            raise ScriptError(f'{where}: expected min/max interval')
        if not value or not all(numeric(v) for v in value.values()):
            raise ScriptError(f'{where}: interval requires finite numeric bounds')
        if 'min' in value and 'max' in value and value['min'] > value['max']:
            raise ScriptError(f'{where}: inverted interval')

    if not isinstance(rules, dict) or not isinstance(rules.get('units'), dict) or not rules['units']:
        raise ScriptError('rules: nonempty units mapping required')
    years = rules.get('milestone_years')
    if not isinstance(years, list) or not years or any(type(y) is not int for y in years) or len(set(years)) != len(years):
        raise ScriptError('rules: distinct integer milestone years required')
    catalog = rules.get('monitored_stat_catalog')
    if not isinstance(catalog, list) or not all(isinstance(s, str) for s in catalog) or len(set(catalog)) != len(catalog):
        raise ScriptError('rules: distinct stat catalog required')
    for unit, cfg in rules['units'].items():
        if not isinstance(cfg, dict) or not isinstance(cfg.get('monitored_stats'), dict):
            raise ScriptError(f'{unit}: monitored_stats mapping required')
        if type(cfg.get('historical_relevance_start_year', years[0])) is not int:
            raise ScriptError(f'{unit}: historical relevance year must be an integer')
        applicable = cfg.get('applicable_milestone_years', years)
        if not isinstance(applicable, list) or any(type(y) is not int or y not in years for y in applicable) or len(set(applicable)) != len(applicable):
            raise ScriptError(f'{unit}: invalid/duplicate applicable milestone years')
        for stat, cfg_stat in cfg['monitored_stats'].items():
            if stat not in catalog or not isinstance(cfg_stat, dict):
                raise ScriptError(f'{unit}/{stat}: stat outside catalog or invalid configuration')
            if 'final_range' in cfg_stat:
                interval(cfg_stat['final_range'], f'{unit}/{stat}/final_range')
            for key in ('max_single_delta', 'max_cumulative_positive_delta', 'max_cumulative_negative_delta'):
                if key in cfg_stat and (not numeric(cfg_stat[key]) or cfg_stat[key] < 0):
                    raise ScriptError(f'{unit}/{stat}/{key}: expected finite nonnegative magnitude')
            ranges = cfg_stat.get('milestone_ranges', {})
            if not isinstance(ranges, dict):
                raise ScriptError(f'{unit}/{stat}: milestone_ranges mapping required')
            for year, value in ranges.items():
                if str(year) not in {str(y) for y in years}:
                    raise ScriptError(f'{unit}/{stat}: milestone outside global grid: {year}')
                interval(value, f'{unit}/{stat}/{year}')
        for key in ('estimated_build_cost_range', 'estimated_upkeep_cost_range'):
            if key in cfg:
                interval(cfg[key], f'{unit}/{key}')


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
    named_entries(node)
    data: dict[str, Any] = {"stats": {}, "raw_stats": {}, "property_nodes": {}, "numeric_properties": [], "build_cost": {}, "supply_cost": {},
                            "unit_domain": scalar(node, "type", required=True).lower()}
    data['unit_type'] = scalar(node, 'unit_type')
    data['active'] = scalar(node, 'active') != 'no'
    data['primary_culture'] = scalar(node, 'primary_culture') == 'yes'
    data['can_build_overseas'] = scalar(node, 'can_build_overseas') != 'no'
    if data["unit_domain"] not in {"land", "naval"}:
        raise ScriptError(f"{node.start}: unsupported unit domain {data['unit_domain']!r}")
    for field in ("build_cost", "supply_cost"):
        member(node, field, required=True)
    seen: set[str] = set()
    for child in node.children:
        key = canonical_stat(child.key)
        if key in seen and key not in VARIABLE:
            raise ScriptError(f"{child.start}: duplicate unit property {child.key}")
        seen.add(key)
        data["property_nodes"][key] = child
        if child.operator != '=':
            raise ScriptError(f'{child.start}: expected unit property assignment')
        if child.keyword in {"build_cost", "supply_cost"}:
            if not child.is_group or child.operator != "=":
                raise ScriptError(f"{child.start}: expected commodity-cost group")
            data[child.keyword] = numeric_members(child)
        elif not child.is_group and child.operator == "=":
            # Non-numeric flags/names are retained in the tree but are not stats.
            if re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", child.value):
                data["stats"][key] = number(child.value, child.start)
                data["raw_stats"][key] = child.value
                data['numeric_properties'].append(child)
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
        effect = effect_body(definition, kind)
        if effect is None:
            continue
        if not effect.is_group:
            raise ScriptError(f"{effect.start}: expected effect group")
        for scope in effect.children:
            targets = {scope.key} if scope.key in monitored_units else global_scope_units.get(scope.key, set())
            if not targets:
                if (known_units is not None and scope.key not in known_units and scope.key not in global_scope_units and scope.is_group
                        and any(canonical_stat(n.key) in monitored_stats for n in scope.children if n.key)):
                    raise ScriptError(f"{scope.start}: unknown unit-effect scope {scope.key}")
                continue
            if not scope.is_group or scope.operator != "=":
                raise ScriptError(f"{scope.start}: expected unit modifier group")
            for stat, stat_key, value in numeric_modifier_entries(scope):
                if stat_key not in monitored_stats:
                    continue
                if value is None:
                    raise ScriptError(f'{stat.start}: cannot represent grouped {stat_key} as a scalar raw progression')
                for target in sorted(targets):
                    out[target].append({
                        "source_file": rel_path, "invention": key, "line": stat.start.line,
                        "column": stat.start.column, "stat": stat_key, "value": value, "raw_value": stat.value,
                        "raw_stat": stat.key,
                        "block_id": f'{rel_path}:{scope.start.offset}',
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
            rep.add("INFO", f"KEY GOODS mapping present in production types: {good}", code='production_mapping', category='economic_index', stat=good, source=production_types_file, evidence='recipe_presence_not_availability')
        else:
            rep.add("WARN", f"KEY GOODS missing production output mapping: {good}", code='production_mapping', category='economic_index', stat=good, source=production_types_file, evidence='recipe_presence_not_availability')


def _run() -> int:
    args = parse_args()
    rules = read_rules(args.core_root, args.timeline_root)
    rep = Reporter()
    rep.add("INFO", f"AUDIT ROOTS: core={args.core_root}; timeline={args.timeline_root}")
    inventory = compose_runtime(ROOT, args.core_root, args.timeline_root)
    effective_units = unit_definitions(inventory, ROOT)
    unknown = set(rules['units']) - set(effective_units)
    if unknown:
        raise ScriptError(f'unknown monitored unit definitions: {sorted(unknown)}')
    units_cfg: dict[str, Any] = {u: dict(c, unit_file=effective_units[u]) for u, c in rules['units'].items()}
    outside_roster = sorted(set(effective_units) - set(units_cfg))
    if outside_roster:
        rep.add('WARN', f'Effective units without normative configuration: {outside_roster}',
                code='unmonitored_units', category='evidence_gap', evidence='effective_definition_inventory', cause='catalog_coverage')
    scan_files = inventory.files('technologies') + inventory.files('inventions')
    rep.add('INFO', f'Effective direct sources: technologies={len(inventory.files("technologies"))}; inventions={len(inventory.files("inventions"))}; units={len(effective_units)}; legacy scan_files is not the source universe.',
            code='effective_sources', category='source_scope', evidence='descriptor_overlay')
    for source in sorted(inventory.selected.values(), key=lambda s: s.runtime_path):
        if source.classification == 'direct':
            rep.add('INFO', f'{source.runtime_path} <- {source.file} ({source.layer})', code='source_selected', category='source_scope', source=source.file, evidence='descriptor_overlay')
    rep.add('INFO', f'Replaced sources={len(inventory.replaced)}; conditional/context files={sum(s.classification != "direct" for s in inventory.selected.values())}. These are inventoried, not universally accumulated.',
            code='source_boundaries', category='source_scope', evidence='descriptor_overlay')
    for source in inventory.excluded:
        rep.add('WARN', source.classification, code='unscheduled_source', category='source_scope', source=source.file, evidence='pinned_Alice_loader', uncertainty='V2 loading unverified')
    for boundary in inventory.boundaries:
        rep.add('INFO', boundary, code='model_boundary', category='evidence_gap', evidence='declared_model_boundary', cause='conditional_runtime')
    rep.add('INFO', 'Normative basis: UNVALIDATED. All range/cap findings below concern a RAW SCRIPT scenario, not a common V2/Alice runtime or a confirmed gameplay bug. Legacy coverage/confidence thresholds and priority weights are retained unchanged in JSON but inactive as quality criteria.',
            code='unvalidated_rules', category='evidence_gap', evidence='Task_23_audit', cause='normative_basis')
    rep.add('INFO', 'Coverage dimensions: sources=declared descriptor composition, direct unit effects only; property coverage=catalog presence; engine support=pinned Alice schema/V2 unverified; extraction=structural contract with explicit limitations; temporal evidence=anchors/bounds/unknown; indeterminacy=possibility envelopes; normative validity=UNVALIDATED. No aggregate confidence score.',
            code='coverage_dimensions', category='evidence_gap', evidence='analysis_contract', cause='coverage_dimensions')
    rep.add('INFO', 'Victoria II script numeric types, aliases and property application are UNVERIFIED here; no Alice behavior is copied into a V2 projection.',
            code='v2_unverified', category='evidence_gap', engine=V2, evidence='missing_script_specification', cause='V2_semantics')
    files_cfg = {'goods': inventory.require('common/goods.txt'), 'production_types': inventory.require('common/production_types.txt')}
    monitored_units = set(units_cfg.keys())
    discovered_units = set(effective_units)
    unit_groups: dict[str, list[str]] = rules.get("unit_groups", {})
    monitored_stats_set = set(rules["monitored_stat_catalog"])
    detected_stats_by_unit: dict[str, set[str]] = {}
    covered_stats_by_unit: dict[str, set[str]] = {}
    unit_domain_by_unit: dict[str, str | None] = {}

    for group_name, members in unit_groups.items():
        unknown_members = [u for u in members if u not in discovered_units]
        if unknown_members:
            rep.add("WARN", f"UNIT GROUP {group_name}: unknown members {', '.join(sorted(unknown_members))}", code='unit_group', category='source_scope', evidence='configured_group')
        else:
            rep.add("INFO", f"UNIT GROUP {group_name}: {len(members)} member(s)", code='unit_group', category='source_scope', evidence='configured_group')

    goods_costs = parse_goods_costs(files_cfg["goods"])

    baselines: dict[str, dict[str, float]] = defaultdict(dict)
    unit_inputs: dict[str, dict[str, Any]] = {}
    supply_indices: dict[str, float] = {}

    # 2) stat monitorate mancanti/non leggibili + 5) costo build/upkeep non calcolabile
    for unit, cfg in units_cfg.items():
        unit_data = parse_unit_block(cfg["unit_file"], unit)
        unit_inputs[unit] = unit_data
        stats = unit_data["stats"]
        unit_domain_by_unit[unit] = unit_data.get("unit_domain")
        for prop, node in unit_data['property_nodes'].items():
            if prop not in BASE_KNOWN:
                rep.add('WARN', f'{unit}: property {prop} outside verified base schema; retained in tree', code='unknown_base_property', category='engine_semantics', unit=unit, stat=prop, source=str(node.start), engine=ALICE, evidence='pinned_engine_schema', uncertainty='application unverified')
            elif prop in unit_data['raw_stats']:
                e = property_evidence(prop, unit_data['raw_stats'][prop], 'base', ALICE)
                if e.status != 'applied' or e.value != unit_data['stats'][prop]:
                    rep.add('WARN', f'{unit} {prop}: raw={node.value}; Alice={e.value}; {e.status}: {e.note}', code='base_semantics', category='engine_semantics', unit=unit, stat=prop, source=str(node.start), engine=ALICE, evidence='pinned_engine_source', cause=prop)
        detected_stats = {s for s in stats.keys() if s in monitored_stats_set}
        covered_stats = {s for s in cfg.get("monitored_stats", {}).keys() if s in monitored_stats_set}
        detected_stats_by_unit[unit] = detected_stats
        covered_stats_by_unit[unit] = covered_stats
        missing_coverage = sorted(detected_stats - covered_stats)
        if missing_coverage:
            rep.add("WARN", f"{unit}: unit stats detected but not covered by rules: {', '.join(missing_coverage)}", code='property_coverage_gap', category='evidence_gap', unit=unit, source=cfg['unit_file'], cause='catalog_coverage')

        for stat, stat_cfg in cfg["monitored_stats"].items():
            if stat not in stats:
                rep.add("FAIL", f"{unit}: monitored stat missing/unreadable in unit file: {stat}", code='missing_baseline', category='integrity', unit=unit, stat=stat, source=cfg['unit_file'])
            else:
                baseline = stats[stat]
                baselines[unit][stat] = baseline
                rep.add("INFO", f"{unit}: baseline {stat}={baseline}", code='raw_baseline', unit=unit, stat=stat, source=cfg['unit_file'])

        est_build, miss_build, top_build = estimate_costs(unit_data["build_cost"], goods_costs)
        est_upkeep, miss_upkeep, top_upkeep = estimate_costs(unit_data["supply_cost"], goods_costs)

        if miss_build:
            rep.add("FAIL", f"{unit}: cannot estimate build_cost; missing goods costs: {', '.join(sorted(miss_build))}", code='missing_good_price', category='integrity', unit=unit, source=cfg['unit_file'])
        if miss_upkeep:
            rep.add("FAIL", f"{unit}: cannot estimate supply_cost; missing goods costs: {', '.join(sorted(miss_upkeep))}", code='missing_good_price', category='integrity', unit=unit, source=cfg['unit_file'])

        if est_build is not None:
            build_top = ", ".join(f"{g}={v:.2f}" for g, v in top_build) if top_build else "none"
            rep.add("INFO", f"{unit}: build_basket_base_price_index={est_build:.2f}; top3_build=[{build_top}]", code='basket_index', category='economic_index', unit=unit, source=cfg['unit_file'], evidence='base_price_basket')
            build_range = cfg.get("estimated_build_cost_range", {})
            b_min = build_range.get("min")
            b_max = build_range.get("max")
            if (b_min is not None and est_build < b_min) or (b_max is not None and est_build > b_max):
                rep.add("WARN", f"{unit}: build basket index outside legacy unvalidated range ({est_build:.2f}, expected {b_min}..{b_max})", code='legacy_basket_range', category='economic_index', unit=unit, evidence='unvalidated_legacy_index_rule', cause='basket_index')

        if est_upkeep is not None:
            supply_indices[unit] = est_upkeep
            upkeep_top = ", ".join(f"{g}={v:.2f}" for g, v in top_upkeep) if top_upkeep else "none"
            rep.add("INFO", f"{unit}: supply_basket_base_price_index={est_upkeep:.2f}; top3_upkeep=[{upkeep_top}]", code='basket_index', category='economic_index', unit=unit, source=cfg['unit_file'], evidence='base_price_basket')
            upkeep_range = cfg.get("estimated_upkeep_cost_range", {})
            u_min = upkeep_range.get("min")
            u_max = upkeep_range.get("max")
            if (u_min is not None and est_upkeep < u_min) or (u_max is not None and est_upkeep > u_max):
                rep.add("WARN", f"{unit}: supply basket index outside legacy unvalidated range ({est_upkeep:.2f}, expected {u_min}..{u_max})", code='legacy_basket_range', category='economic_index', unit=unit, evidence='unvalidated_legacy_index_rule', cause='basket_index')

        expected_goods = set(cfg.get("key_goods_expectations", []))
        unit_goods = set(unit_data["build_cost"].keys()) | set(unit_data["supply_cost"].keys())
        if expected_goods and expected_goods.isdisjoint(unit_goods):
            rep.add(
                "WARN",
                f"{unit}: none of expected key goods found in unit costs ({', '.join(sorted(expected_goods))})",
             code='key_goods_presence', category='economic_index', unit=unit, evidence='at_least_one_presence_only')

    land_units = {u for u, domain in unit_domain_by_unit.items() if domain == "land"}
    naval_units = {u for u, domain in unit_domain_by_unit.items() if domain == "naval"}
    global_scope_units: dict[str, set[str]] = {
        "army_base": set(land_units),
        "navy_base": set(naval_units),
    }

    milestone_years: list[int] = sorted(
        int(y) for y in rules.get("milestone_years", [1836, 1850, 1870, 1900, 1910, 1919, 1929, 1936, 1945, 1955, 1966])
    )
    default_milestone_year = milestone_years[0] if milestone_years else 1836
    inferred_years = build_year_inference(scan_files)
    report_modifier_semantics(scan_files, discovered_units, rep)
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
    for rel in sorted(scan_files):
        found = parse_effect_unit_assignments(
            rel,
            monitored_units,
            monitored_stats_set | VARIABLE,
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
    for u, cfg in units_cfg.items():
        for item in relevant_assignments_by_unit.get(u, []):
            s = item.get("stat")
            if not s:
                continue
            stat_assignment_count[s] += 1
            stat_assignment_units[s].add(u)
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
        rep.add("WARN", "INVENTION EXAMPLE: none found for monitored units in scanned invention files", code='no_invention_effects', category='evidence_gap', cause='extraction_signal')

    # Expanded contribution counts are descriptive, not confidence grades.
    for unit, cfg in units_cfg.items():
        unit_items = relevant_assignments_by_unit.get(unit, [])
        monitored_stats = set(cfg.get("monitored_stats", {}).keys())
        touched_stats = {x.get("stat") for x in unit_items if x.get("stat") in monitored_stats}
        rep.add(
            "INFO",
            f"{unit}: signal assignments={len(unit_items)}, monitored_stats={len(monitored_stats)}, touched_stats={len(touched_stats)}",
         code='expanded_signal', unit=unit)
        if len(unit_items) == 0:
            rep.add("WARN", f"{unit}: no readable timed deltas found in scanned files; coverage is baseline/economic only", code='no_signal', category='evidence_gap', unit=unit, cause='extraction_signal')

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
                 code='single_delta', category='numeric_rule', unit=unit, stat=stat, source=format_assignment_origin(item), evidence='unvalidated_rule', uncertainty='not a gameplay verdict', cause='raw_progression')

    assignments_by_unit_stat: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for unit, unit_items in relevant_assignments_by_unit.items():
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in unit_items:
            stat_name = item.get("stat")
            if not stat_name:
                continue
            grouped[stat_name].append(item)
        assignments_by_unit_stat[unit] = grouped

    engine_units = {u: project_unit(unit_inputs[u], all_assignments.get(u, []), ALICE) for u in units_cfg}
    report_consumers(unit_inputs, engine_units, rep)
    report_availability(inventory, unit_inputs, engine_units, scan_files, inferred_years, rep)

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
            raw_stat = unit_inputs[unit]['raw_stats'][stat]
            projection = engine_units[unit]['stats'].get(stat, projected_stat(raw_stat, stat, [], ALICE))
            engine_envelopes = {y: milestone_envelope(projection['baseline'], projection['assignments'], y)
                                for y in milestone_years} if projection['baseline'] is not None else None
            rep.add('INFO', f'{unit} {stat}: raw_script_all_effects={estimated_final:.6g}; Alice status={projection["status"]}, baseline={projection["baseline"]}, applied_subset_final={projection["final"]}, excluded_effects={projection["excluded"]}; milestone_envelopes={engine_envelopes}; V2=unverified. No range is applied to a different engine quantity.',
                    code='engine_projection', category='engine_semantics', unit=unit, stat=stat, engine=ALICE,
                    source=cfg['unit_file'], evidence='pinned_engine_source', uncertainty='static additive subset; conditional systems excluded', data=projection)
            if stat == 'supply_consumption' and projection['final'] is not None and unit in supply_indices:
                rep.add('INFO', f'{unit}: Alice conditional supply index baseline={supply_indices[unit] * projection["baseline"]:.6g}, all_effects={supply_indices[unit] * projection["final"]:.6g}; basket at base prices x applied supply multiplier; national modifier=0, full strength, unit demand only. Prices, availability, budget and operating conditions not simulated; legacy ranges NOT applied.',
                        code='conditional_supply_index', category='economic_index', unit=unit, stat=stat, engine=ALICE,
                        evidence='pinned_economy_formula', uncertainty='conditional scenario, not runtime expenditure')
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
                f"research_anchor_share {coverage_pct:.1f}% (descriptive only)",
             code='raw_scenario', unit=unit, stat=stat, evidence='static_raw_script_scenario')
            if unknown_year_count > 0:
                rep.add(
                    "INFO",
                    f"{unit} {stat}: uncertain-date deltas included only as possibility envelopes: count={unknown_year_count}, total={unknown_year_delta:+.3f} "
                    f"(known_count={known_year_count})",
                 code='raw_scenario', unit=unit, stat=stat, evidence='static_raw_script_scenario')
            max_pos = s_cfg.get("max_cumulative_positive_delta")
            max_neg = s_cfg.get("max_cumulative_negative_delta")
            if max_pos is not None and pos_delta > max_pos:
                rep.add(
                    "WARN",
                    f"{unit} {stat} cumulative positive delta too large (+{pos_delta:.3f}, max {max_pos})",
                 code='cumulative_positive', category='numeric_rule', unit=unit, stat=stat, evidence='unvalidated_rule', uncertainty='not a gameplay verdict', cause='raw_progression')
            if max_neg is not None and abs(neg_delta) > max_neg:
                rep.add(
                    "WARN",
                    f"{unit} {stat} cumulative negative delta too large ({neg_delta:.3f}, max -{max_neg})",
                 code='cumulative_negative', category='numeric_rule', unit=unit, stat=stat, evidence='unvalidated_rule', uncertainty='not a gameplay verdict', cause='raw_progression')
            min_final, max_final = get_final_range(s_cfg)
            if (min_final is not None and estimated_final < min_final) or (max_final is not None and estimated_final > max_final):
                rep.add(
                    "WARN",
                    f"{unit} {stat} estimated final outside final_range in all-effects scenario (baseline {baseline:.3f} + delta {total_delta:+.3f} = {estimated_final:.3f}, expected {min_final}..{max_final})",
                 code='final_range', category='numeric_rule', unit=unit, stat=stat, evidence='unvalidated_rule', uncertainty='not a gameplay verdict', cause='raw_progression')
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
                 code='rule_applicability', category='integrity', unit=unit, stat=stat, evidence='configuration')

            for year in applicable_milestone_years:
                cfg_y = milestone_ranges.get(str(year)) or milestone_ranges.get(year)
                if not cfg_y:
                    continue
                m_min = cfg_y.get("min")
                m_max = cfg_y.get("max")
                lo, hi = milestone_bounds[year]
                if (m_min is not None and hi < m_min) or (m_max is not None and lo > m_max):
                    rep.add("WARN", f"{unit} {stat} milestone {year} entirely outside configured range "
                            f"(possible {lo:.3f}..{hi:.3f}, expected {m_min}..{m_max})", code='milestone_range', category='numeric_rule', unit=unit, stat=stat, evidence='unvalidated_rule', uncertainty='not a gameplay verdict', cause='raw_progression')
                elif (m_min is not None and lo < m_min) or (m_max is not None and hi > m_max):
                    rep.add("INFO", f"{unit} {stat} milestone {year} indeterminate: uncertainty envelope "
                            f"{lo:.3f}..{hi:.3f} overlaps configured range {m_min}..{m_max}", code='milestone_indeterminate', category='evidence_gap', unit=unit, stat=stat, evidence='possibility_envelope', uncertainty='overlap is not PASS', cause='temporal_indeterminacy')

    check_key_goods_availability(files_cfg["production_types"], rules["economic"]["key_goods"], rep)

    if args.json:
        print(rep.json())
        return 1 if any(d.level == 'FAIL' for d in rep.diagnostics) else 0
    rep.dump(details=not args.summary)
    rep.summary()
    print("\nSTAT COVERAGE SUMMARY (catalog presence, not source/engine/normative validity)")
    print(f" - total_covered_stats={sum(len(v) for v in covered_stats_by_unit.values())}")
    print(f" - total_detected_stats={sum(len(v) for v in detected_stats_by_unit.values())}")
    print("\nSTAT SOURCE SIGNAL (physical origins; no confidence grade)")
    for stat in sorted(monitored_stats_set):
        origins = {(x['source_file'], x['line'], x['column']) for x in relevant_assignment_items if x['stat'] == stat}
        print(f" - {stat}: physical_assignments={len(origins)}, expanded_contributions={stat_assignment_count.get(stat, 0)}, units={len(stat_assignment_units.get(stat, set()))}")

    # WARN/INFO diagnostics are non-blocking, but FAIL-level structural/tooling errors should fail CI.
    return 1 if any(level == "FAIL" for level, _ in rep.items) else 0


def main() -> int:
    try:
        return _run()
    except (ScriptError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        rep = Reporter()
        rep.add("FAIL", f"INPUT ERROR: {exc}; analysis aborted, no partial conclusions", code='input_error', category='integrity', evidence='invalid_or_outside_structural_contract')
        if '--json' in sys.argv:
            print(rep.json())
            return 1
        rep.dump()
        print("\nPRIORITY SUMMARY\n - structural/data confidence issues: input error")
        print("\nRECOMMENDED PLAYTEST FOCUS\n - Unavailable: analysis aborted before valid conclusions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
