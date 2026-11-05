"""Conservative research bounds and bounded Alice 1.3.0 functional scenarios.

No country/save simulation or V2 projection. Pinned sources:
commands.cpp can_start_research/can_start_naval_unit_construction;
ai.cpp build_ships/update_ships; military.cpp is_*_better/upgrade_ship;
culture.cpp discover_inventions. All under schombert/Project-Alice v1.3.0.
"""
from collections import Counter, deque
from datetime import date
from fractions import Fraction
import re
import struct

from lib_1966_parser import ScriptError, member, scalar, parse_file, read_text
from lib_1966_semantics import ALICE


def necessary_literals(nodes, definitions, *, disjunction=False, negate=False):
    """Necessary signed atoms only; De Morgan preserves conservative OR bounds.

    Alice NOT wraps an implicit OR (tr_scope_not), then inverts it: multiple
    direct children must all be false. Unknown predicates/scopes produce no atom,
    never an assumed truth. Explicit invention references retain their kind.
    """
    parts = []
    for n in nodes:
        refs = set()
        if n.is_group and n.operator == '=':
            if n.keyword in {'and', 'or', 'not'}:
                refs = necessary_literals(n.children, definitions,
                    disjunction=n.keyword in {'or', 'not'}, negate=negate ^ (n.keyword == 'not'))
        elif not n.is_group and n.operator == '=':
            if n.keyword == 'invention':
                candidates = {('invention', n.value)} & definitions
                positive = True
            else:
                candidates = {k for k in definitions if k[1] == n.key}
                positive = n.value.lower() in {'yes', '1'}
                if n.value.lower() not in {'yes', '1', 'no', '0'}:
                    candidates = set()
            if len(candidates) == 1:
                refs = {(next(iter(candidates)), positive != negate)}
        parts.append(refs)
    if not parts:
        return set()
    return set.intersection(*parts) if disjunction != negate else set.union(*parts)


class ResearchDependencies:
    """Required effects under normal prefix research; extraordinary grants excluded.

    Bounds use necessary POSITIVE closure only; temporal negative conditions never
    remove final sets. A separate bounded search checks acquisition sequences.
    Neither uncertain transitions nor resource limits can prove exclusion.
    """
    def __init__(self, files):
        self.definitions, self.required, self.forbidden = {}, {}, {}
        previous, self.predecessors = {}, {}
        for file in sorted(files):
            kind = 'technology' if '/technologies/' in '/' + file.replace('\\', '/') else 'invention'
            for node in parse_file(file).definitions:
                key = kind, node.key
                if key in self.definitions:
                    raise ScriptError(f'{node.start}: duplicate dependency definition {key}')
                self.definitions[key] = node
                if kind == 'technology':
                    area = scalar(node, 'area', required=True)
                    self.predecessors[key] = previous.get(area)
                    previous[area] = key
        keys = set(self.definitions)
        for key, node in self.definitions.items():
            limit = member(node, 'limit') if key[0] == 'invention' else None
            atoms = necessary_literals(limit.children if limit else (), keys)
            self.required[key] = {k for k, positive in atoms if positive}
            self.forbidden[key] = {k for k, positive in atoms if not positive}
            if self.predecessors.get(key):
                self.required[key].add(self.predecessors[key])
        self._closures = {}

    def closure(self, key):
        if key not in self.definitions:
            return None
        if key not in self._closures:
            result, pending = set(), [key]
            while pending:
                item = pending.pop()
                if item not in result:
                    result.add(item)
                    pending.extend(self.required[item])
            self._closures[key] = frozenset(result)
        return self._closures[key]

    @staticmethod
    def owner(item):
        kind = 'technology' if '/technologies/' in '/' + item['source_file'].replace('\\', '/') else 'invention'
        return kind, item['invention']

    def _condition(self, nodes, acquired, op='and'):
        """Three-valued discovery-time predicate, never a final-state invariant.

        Known false AND unknown is false; known true OR unknown is true. Other
        unknowns remain unknown, including country, dates and unsupported scopes.
        This does not use necessary_literals to evaluate an entire condition.
        """
        values = []
        for n in nodes:
            value = None
            if n.operator == '=':
                if n.is_group and n.keyword in {'and', 'or', 'not'}:
                    value = self._condition(n.children, acquired,
                                            'or' if n.keyword in {'or', 'not'} else 'and')
                    if n.keyword == 'not' and value is not None:
                        value = not value
                elif not n.is_group:
                    key, positive = self._atom(n)
                    if key is not None:
                        value = (key in acquired) == positive
            values.append(value)
        if op == 'or':
            return True if True in values else None if None in values else False
        return False if False in values else None if None in values else True

    def _atom(self, node):
        if node.keyword == 'invention':
            key = ('invention', node.value)
            return (key, True) if key in self.definitions else (None, None)
        keys = [k for k in self.definitions if k[1] == node.key]
        if len(keys) == 1 and node.value.lower() in {'yes', '1', 'no', '0'}:
            return keys[0], node.value.lower() in {'yes', '1'}
        return None, None

    def _references(self, nodes):
        """All boolean alternatives, including negative refs, for search support.

        Necessary-only closure is insufficient here: an optional OR branch may
        break a cycle. Chance modifiers are deliberately not prerequisite edges.
        """
        refs = set()
        for n in nodes:
            if n.operator != '=':
                continue
            if n.is_group and n.keyword in {'and', 'or', 'not'}:
                refs.update(self._references(n.children))
            elif not n.is_group:
                key, _ = self._atom(n)
                if key is not None:
                    refs.add(key)
        return refs

    def _eligible(self, key, acquired):
        if key[0] == 'technology':
            prior = self.predecessors.get(key)
            # Untimed prefix research; country/date/completion are external.
            return prior is None or prior in acquired
        node = self.definitions[key]
        limit = member(node, 'limit')
        condition = self._condition(limit.children if limit else (), acquired)
        chance = member(node, 'chance')
        possible_chance = None
        if chance is None:
            possible_chance = True  # pinned default 1; never a discovery guarantee
        elif chance.is_group and len(chance.children) == 1:
            raw = scalar(chance, 'base')
            if raw is not None and re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', raw):
                value = float(raw)
                # Only exact binary32 constants justify this int32 conversion.
                # Decimal rounding near 1 or INT32_MAX can change eligibility;
                # do not use host double precision to prove an edge impossible.
                if (value < 2**31 and Fraction(value) == Fraction(raw)
                        and struct.unpack('f', struct.pack('f', value))[0] == value):
                    possible_chance = int(value) > 0
        if condition is False or possible_chance is False:
            return False
        return True if condition is True and possible_chance is True else None

    def _search(self, roots, goal, *, max_definitions=16, max_states=4096):
        """Memoized acquisition states; unknown edges can never prove exclusion.

        Roots plus all modeled references form a closed support: omitted owners
        cannot change a modeled predicate or goal. States encode persistent techs
        and inventions separately by typed keys. Each transition adds one owner,
        tests its current eligibility, and never re-tests an already acquired one.
        Only fully known edges establish a possible static sequence. If an unknown
        edge is encountered, exhaustion is UNKNOWN rather than unreachable.
        """
        result = dict(status='unknown', sequence=None, acquired=None, visited_states=0,
                      scope='untimed static acquisition model; no national/runtime discovery guarantee')
        universe, pending = set(), list(sorted(roots))
        while pending:
            key = pending.pop()
            if key not in self.definitions:
                return dict(result, reason='unresolved acquisition owner')
            if key in universe:
                continue
            universe.add(key)
            if len(universe) > max_definitions:
                return dict(result, reason='definition limit')
            if key[0] == 'technology':
                prior = self.predecessors.get(key)
                if prior:
                    pending.append(prior)
            else:
                limit = member(self.definitions[key], 'limit')
                pending.extend(sorted(self._references(limit.children if limit else ())))
        if max_states < 1:
            return dict(result, reason='state limit')
        order = sorted(universe)
        empty = frozenset()
        paths, queue, unknown = {empty: ()}, deque([empty]), False
        while queue:
            acquired = queue.popleft()
            if goal(acquired):
                return dict(result, status='possibly_reachable', sequence=list(paths[acquired]),
                            acquired=sorted(acquired), visited_states=len(paths), reason='known transition sequence')
            for key in order:
                if key in acquired:
                    continue
                eligible = self._eligible(key, acquired)
                if eligible is None:
                    unknown = True
                if eligible is not True:
                    continue
                nxt = acquired | {key}
                if nxt in paths:
                    continue
                if len(paths) >= max_states:
                    return dict(result, visited_states=len(paths), reason='state limit')
                paths[nxt] = paths[acquired] + (key,)
                queue.append(nxt)
        return dict(result, status='unknown' if unknown else 'proven_unreachable',
                    visited_states=len(paths), reason='unknown transition semantics' if unknown else
                    'exhausted complete modeled state graph')

    def acquisition_path(self, targets, *, max_definitions=16, max_states=4096):
        """Existence of a sequence acquiring all targets, allowing support owners.

        POSSIBLY_REACHABLE means possible in this static model, not guaranteed
        discovery. PROVEN_UNREACHABLE is limited to the modeled ordinary path.
        """
        targets = frozenset(targets)
        return dict(self._search(targets, lambda state: targets <= state,
                                 max_definitions=max_definitions, max_states=max_states),
                    goal='all_targets_acquired', targets=sorted(targets))

    def lower_bound(self, projection, *, max_negative_owners=16,
                    max_definitions=16, max_states=4096):
        result = {'status': 'unverified', 'lower_bound': None,
                  'reachability': 'unverified', 'witness': None,
                  'bound_proof': None,
                  'scope': 'normal prefix research; histories, events, grants and saves not modelled'}
        if projection['status'] != 'applied' or projection['baseline'] is None:
            return dict(result, reason='incomplete applied projection')
        grouped = {}
        # Each owning definition is acquired as a whole. Do not select individual
        # negative fields while dropping positive bodies in that same definition.
        for x in projection['assignments']:
            key = self.owner(x)
            grouped[key] = grouped.get(key, 0.) + x['value']
        if any(k not in self.definitions for k in grouped):
            return dict(result, reason='unresolved contribution owner')
        negatives = sorted(k for k, value in grouped.items() if value < 0)
        if len(negatives) > max_negative_owners:
            return dict(result, reason='enumeration limit', negative_owners=len(negatives))
        lower, best = float('inf'), set()
        provenance = []
        for key in negatives:
            closure = self.closure(key)
            provenance.append({'owner': key, 'required': sorted(closure),
                'forced_positive': [{'owner': k, 'value': grouped[k]} for k in sorted(closure)
                                    if grouped.get(k, 0) > 0]})
        for mask in range(1 << len(negatives)):
            selected = [k for j, k in enumerate(negatives) if mask & (1 << j)]
            acquired = set().union(*(self.closure(k) for k in selected)) if selected else set()
            # Positive prerequisites persist, so their effects must be included.
            # Negative eligibility is temporal: NEVER reject a final set here.
            # Every real state's negative owners have such a positive closure;
            # omitted nonnegative-net owners can only raise its value. Taking the
            # minimum of all these closures is therefore a conservative bound.
            value = projection['baseline'] + sum(grouped.get(k, 0.) for k in sorted(acquired))
            if value < lower:
                lower, best = value, acquired
        search = self._search(grouped, lambda state: projection['baseline'] +
                              sum(grouped.get(k, 0.) for k in sorted(state)) < 0,
                              max_definitions=max_definitions, max_states=max_states) if lower < 0 else {
                                  'status': 'proven_unreachable', 'sequence': None, 'acquired': None,
                                  'visited_states': 0, 'reason': 'nonnegative conservative bound',
                                  'scope': 'normal prefix research only'}
        search['goal'] = 'negative_supply_state'
        witness = None
        if search['status'] == 'possibly_reachable':
            witness = {'value': projection['baseline'] + sum(grouped.get(k, 0.) for k in search['acquired']),
                       'acquired': search['acquired'], 'sequence': search['sequence']}
        return dict(result, status='conditional_bound', lower_bound=lower,
                    bound_proof='necessary_positive_closure_overapproximation',
                    minimizing_acquisition=sorted(best), enumerated_subsets=1 << len(negatives),
                    temporal_search=search, negative_dependencies=provenance,
                    reachability='reachable_in_static_research_model' if witness else 'unverified',
                    witness=witness)


def naval_ai_scenario(units, projections, active, ports, *, overseas=False, shortages=()):
    """Given unlocks/ports, isolate selection from actual AI execution.

    Ties stay sets: the repository inventory does not establish engine unit-ID
    order. Refit excludes known shortages and primary-culture-only units as the
    default get_best_* calls do. Fleet budgets, ownership/control, disarmament,
    war, AI control, current queues and damage fractions are external conditions.
    """
    unlocked = {u for u, d in units.items() if d['unit_domain'] == 'naval' and (d['active'] or u in active)}
    rows = {}
    for category in ['transport', 'light_ship', 'big_ship']:
        candidates = sorted(u for u in unlocked if units[u]['unit_type'] == category)
        if not candidates:
            continue
        def base(u, stat):
            return projections[u]['stats'][stat]['baseline']
        if any(base(u, 'hull') is None for u in candidates):
            rows[category] = {'status': 'unverified'}
            continue
        maximum = max(base(u, 'hull') for u in candidates)
        build = [u for u in candidates if base(u, 'hull') == maximum]
        def can_build(u):
            level = base(u, 'min_port_level')
            return level is not None and any(p >= level for p in ports) and (not overseas or units[u]['can_build_overseas'])
        fields = {'big_ship': ['gun_power', 'hull', 'torpedo_attack'],
                  'light_ship': ['maximum_speed', 'gun_power', 'hull'],
                  'transport': ['maximum_speed', 'hull', 'gun_power']}[category]
        scores = {}
        for u in candidates:
            if units[u].get('primary_culture') or u in shortages:
                continue
            q = projections[u]['stats']
            evasion = q['evasion']
            if evasion['status'] != 'applied' or evasion['final'] is None:
                continue
            selected = 'final' if evasion['final'] > 0 else 'baseline'
            if any(q[s]['status'] != 'applied' or q[s][selected] is None for s in fields):
                continue
            scores[u] = tuple(q[s][selected] for s in fields)
        refit = sorted(u for u, score in scores.items() if score == max(scores.values())) if scores else []
        rows[category] = {'status': 'conditional_scenario', 'unlocked': candidates,
            'base_hull_scores': {u: base(u, 'hull') for u in candidates},
            'locally_buildable': [u for u in candidates if can_build(u)],
            'new_build_candidates': build, 'selected_buildable': [u for u in build if can_build(u)],
            'penalized_by_base_hull': [u for u in candidates if u not in build],
            'refit_score_fields': fields, 'refit_scores': scores,
            'refit_candidates': refit, 'refit_unverified': [u for u in candidates
                if u not in scores and not units[u].get('primary_culture') and u not in shortages],
            'assumed_shortages': sorted(shortages),
            'port_fallback': False, 'actual_execution': 'unverified',
            'refit_result': 'type replaced; strength=0.01; repair and fleet composition not simulated'}
    return rows


def campaign_end(inventory):
    source = inventory.selected.get('common/defines.lua')
    if source is None:
        return None
    text = re.sub(r'--\[(=*)\[.*?\]\1\]', '', read_text(source.file), flags=re.DOTALL)
    text = re.sub(r'--[^\n]*', '', text)
    values = re.findall(r'^\s*end_date\s*=\s*[\'\"]([0-9]+\.[0-9]+\.[0-9]+)[\'\"]', text, flags=re.MULTILINE)
    if len(values) != 1:
        raise ScriptError(f'{source.file}: unique quoted campaign end_date required')
    try:
        return date(*(int(v) for v in values[0].split('.')))
    except ValueError as exc:
        raise ScriptError(f'{source.file}: invalid campaign end_date') from exc


def horizon_inventory(dependencies, timing, end):
    rows = []
    for key, node in sorted(dependencies.definitions.items()):
        bounds = [timing[k].not_before for k in dependencies.closure(key) if timing[k].not_before is not None]
        year = max(bounds) if bounds else None
        anchor = date(year, 1, 1) if year is not None else None
        status = ('unverified' if anchor is None or end is None else
                  'no_ordinary_use_window' if anchor >= end else 'reference_before_end')
        rows.append({'kind': key[0], 'owner': key[1], 'source': str(node.start),
            'necessary_reference_year': year, 'status': status,
            'research_start_before_end': anchor < end if key[0] == 'technology' and anchor and end else None,
            'acquisition_and_use': 'unverified; completion, discovery and national exceptions not simulated',
            'probability_years_not_gates': list(timing[key].probability_years)})
    return rows


def report_functional(inventory, units, projections, files, timing, dependencies, rep):
    naval = {u for u, d in units.items() if d['unit_domain'] == 'naval'}
    # All-unlocked is an explicit stress scenario, not a dated nation or forecast.
    if naval:
        levels = sorted({int(projections[u]['stats']['min_port_level']['baseline']) for u in naval
                         if projections[u]['stats']['min_port_level']['baseline'] is not None} | {0})
        for level in levels:
            scenario = naval_ai_scenario(units, projections, naval, [level])
            rep.add('INFO', f'Alice naval AI: all-unlocked scenario, domestic port={level}; '
                'unlock, local eligibility, new-build choice and refit choice remain separate; '
                'no shortages assumed; actual execution unverified.',
                code='naval_ai_selection', category='mechanics', engine=ALICE, cause='naval_ai_selection',
                evidence='pinned_ai_and_military_consumers', data={'port_level': level, 'categories': scenario},
                uncertainty='no country/fleet/market or engine-ID tie ordering simulated; V2 unverified')
    end = campaign_end(inventory)
    rows = horizon_inventory(dependencies, timing, end)
    rep.add('INFO', f'Campaign horizon={end}; nominal tree inclusion is not ordinary acquisition or use. '
        f'Status counts={dict(sorted(Counter(r["status"] for r in rows).items()))}; '
        'end-day inclusion/continue-playing cannot supply research, discovery and operational time before the boundary.',
        code='campaign_horizon', category='availability', engine=ALICE, evidence='effective_end_date_and_research_gates',
        data={'end_date': end.isoformat() if end else None, 'definitions': rows})
    for row in rows:
        if row['status'] == 'no_ordinary_use_window':
            rep.add('WARN', f'{row["kind"]} {row["owner"]}: necessary reference {row["necessary_reference_year"]} '
                f'has no ordinary use window before {end}; not a guarantee of non-acquisition through grants/history.',
                code='horizon_no_use_window', category='availability', engine=ALICE, source=row['source'],
                cause='campaign_horizon', evidence='necessary_research_bound', data=row)
