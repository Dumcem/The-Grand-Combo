"""Evidence-scoped engine contracts; absence of V2 evidence is NOT incompatibility.

Pinned evidence: https://github.com/schombert/Project-Alice/blob/v1.3.0/
src/parsing/parser_defs.txt (unit_definition, unit_modifier_body), parsers.cpp
(parse_int), gamestate/modifiers.hpp, culture/culture.cpp, military/military.cpp,
economy/economy.cpp and economy/construction.cpp. V2 HoD manual documents roles
but not full script numeric types/aliases: these remain unverified here.
"""
from dataclasses import dataclass
import re
from lib_1966_parser import Node, ScriptError, number

ALICE = 'alice_1.3.0'
V2 = 'victoria_ii'
VARIABLE = frozenset('default_organisation maximum_speed build_time supply_consumption attack defence support siege hull gun_power torpedo_attack reconnaissance fire_range maneuver evasion discipline'.split())
BASE_INTEGER = frozenset('build_time default_organisation colonial_points min_port_level supply_consumption_score icon naval_icon'.split())
BASE_IGNORED = frozenset('max_strength limit_per_port weighted_value priority move_sound select_sound floating_flag sprite sprite_mount sprite_mount_attach_node sprite_override transport sail'.split())
BASE_FLAGS = frozenset('active can_build_overseas capital primary_culture'.split())
BASE_TEXT = frozenset('type unit_type'.split())
BASE_GROUPS = frozenset({'build_cost', 'supply_cost'})
BASE_KNOWN = VARIABLE | BASE_INTEGER | BASE_IGNORED | BASE_FLAGS | BASE_TEXT | BASE_GROUPS
# Confirmed Alice alias only. Canonicalization in RAW inventory does not claim V2 equivalence.
ALIASES = {'defense': 'defence'}


@dataclass(frozen=True)
class PropertyEvidence:
    status: str
    numeric_type: str | None
    value: float | None
    note: str


def canonical_stat(key: str) -> str:
    key = key.lower()
    return ALIASES.get(key, key)


def property_evidence(key: str, raw: str, context: str, engine: str) -> PropertyEvidence:
    if context not in {'base', 'modifier'} or engine not in {ALICE, V2}:
        raise ValueError('unknown semantic context/engine')
    key = canonical_stat(key)
    if engine == V2:
        return PropertyEvidence('unverified', None, None, 'V2 script application/type not established by Alice sources')
    if context == 'base' and key in BASE_IGNORED:
        return PropertyEvidence('ignored', None, None, 'recognized then discarded by Alice unit-definition parser')
    if (context == 'modifier' and key not in VARIABLE) or (context == 'base' and key not in BASE_KNOWN):
        return PropertyEvidence('unsupported', None, None, 'not an applied property in the pinned Alice context')
    if context == 'base' and key in BASE_FLAGS | BASE_TEXT | BASE_GROUPS:
        return PropertyEvidence('non_numeric', None, None, 'outside numeric progression')
    is_int = key in (BASE_INTEGER if context == 'base' else {'build_time', 'default_organisation'})
    if is_int:
        # std::from_chars(int) consumes the signed integer prefix. Alice checks
        # invalid_argument, not full consumption: 2.5 -> 2; .5/+2 are invalid.
        match = re.match(r'-?[0-9]+', raw)
        if match is None:
            return PropertyEvidence('invalid', 'integer', None, 'Alice integer parser has no valid prefix')
        value = int(match.group())
        if not -(2**31) <= value < 2**31:
            return PropertyEvidence('unverified', 'integer', None, 'integer overflow behavior is outside contract')
        note = 'integer prefix differs from raw token' if match.end() != len(raw) else 'applied integer'
        return PropertyEvidence('applied', 'integer', float(value), note)
    # The raw structural reader has already validated finite numeric syntax.
    if not re.fullmatch(r'-?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)', raw):
        return PropertyEvidence('unverified', 'real', None, 'raw number syntax outside verified Alice decimal subset')
    value = float(raw)
    if abs(value) > 3.4028234663852886e38:
        return PropertyEvidence('unverified', 'real', None, 'outside finite float32 representation')
    return PropertyEvidence('applied', 'real', value, 'applied additive statistic; real-number approximation of engine float32')


def named_entries(node: Node) -> None:
    for child in node.children:
        if child.key is None:
            raise ScriptError(f'{child.start}: free entry outside list context')


def effect_body(definition: Node, kind: str) -> Node | None:
    from lib_1966_parser import member
    named_entries(definition)
    body = member(definition, 'effect') if kind == 'invention' else definition
    if body is not None:
        if not body.is_group or body.operator != '=':
            raise ScriptError(f'{body.start}: expected assigned effect group')
        named_entries(body)
    return body


def numeric_modifier_entries(scope: Node) -> list[tuple[Node, str, float | None]]:
    if not scope.is_group or scope.operator != '=':
        raise ScriptError(f'{scope.start}: expected assigned unit modifier group')
    seen: set[str] = set()
    result = []
    for child in scope.children:
        if child.key is None:
            raise ScriptError(f'{child.start}: free entry in unit modifier')
        key = canonical_stat(child.key)
        if key in seen:
            raise ScriptError(f'{child.start}: duplicate/ambiguous unit modifier {child.key}')
        seen.add(key)
        if child.operator != '=' or (child.is_group and key in VARIABLE):
            raise ScriptError(f'{child.start}: property outside scalar numeric unit-modifier contract: {child.key}')
        if child.is_group:
            # Preserve unsupported structures for an explicit semantic limitation;
            # never reinterpret commodity amounts as scalar unit-stat effects.
            result.append((child, key, None))
        else:
            result.append((child, key, number(child.value, child.start)))
    return result


def projected_stat(raw: str, stat: str, assignments: list[dict], engine: str) -> dict:
    """An applied additive subset, never a full battle/economy simulation."""
    base = property_evidence(stat, raw, 'base', engine)
    if base.status != 'applied':
        return {'status': base.status, 'baseline': None, 'final': None, 'assignments': [], 'excluded': len(assignments)}
    included = []
    excluded = 0
    for item in assignments:
        e = property_evidence(item.get('raw_stat', stat), item.get('raw_value', str(item['value'])), 'modifier', engine)
        if e.status == 'applied':
            included.append(dict(item, value=e.value))
        else:
            excluded += 1
    return {'status': 'applied_subset' if excluded else 'applied', 'baseline': base.value,
            'final': base.value + sum(x['value'] for x in included), 'assignments': included, 'excluded': excluded}


def report_modifier_semantics(files, known_units, rep):
    """One finding per physical property, before global expansion; all properties
    are inspected, including those outside the normative catalog."""
    from lib_1966_parser import parse_file, unique_definitions
    count = 0
    for file in sorted(files):
        contextual: set[str] = set()
        kind = 'technology' if '/technologies/' in '/' + file.replace('\\', '/') else 'invention'
        for definition in unique_definitions(parse_file(file).definitions).values():
            body = effect_body(definition, kind)
            if body is None:
                continue
            for scope in body.children:
                if scope.key not in known_units | {'army_base', 'navy_base'}:
                    contextual.add(scope.key)
                    continue
                for node, key, value in numeric_modifier_entries(scope):
                    count += 1
                    e = property_evidence(node.key, node.value if not node.is_group else '', 'modifier', ALICE)
                    if node.keyword != key:
                        rep.add('INFO', f'{node.key} -> {key}: alias verified for Alice only; raw spelling retained',
                                code='confirmed_alias', category='engine_semantics', unit=scope.key if scope.key in known_units else None, scope=scope.key, stat=key,
                                source=str(node.start), engine=ALICE, evidence='pinned_engine_schema', uncertainty='V2 alias unverified')
                    if e.status != 'applied' or (value is not None and e.value != value):
                        rep.add('WARN', f'{scope.key} {key}: raw={node.value if not node.is_group else "group (preserved, not scalar)"}; Alice={e.value}; {e.status}: {e.note}',
                                code='modifier_semantics', category='engine_semantics', engine=ALICE,
                                source=str(node.start), unit=scope.key if scope.key in known_units else None, scope=scope.key, stat=key, evidence='pinned_engine_source',
                                uncertainty='V2 unverified; not a shared runtime effect', cause=key)
        if contextual:
            rep.add('INFO', f'Non-unit fields/scopes inventoried, not added to unit stats: {", ".join(sorted(contextual))}',
                    code='context_effects', category='source_scope', source=file,
                    evidence='structural_inventory', uncertainty='national/production/metadata semantics outside additive model', cause='conditional_runtime')
    rep.add('INFO', f'Inspected {count} physical unit-modifier properties; unsupported/unmodelled properties are not promoted to applied common progression.',
            code='semantic_inventory', category='engine_semantics', engine=ALICE)
    return count
