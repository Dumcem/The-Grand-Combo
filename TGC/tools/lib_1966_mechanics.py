"""Bounded Alice 1.3.0 consumers, not a battle or acquisition simulator.

Evidence: military.cpp get_reg_*_damage, add_army_to_battle, get_land_combat_target,
get_ship_*_damage; military.hpp naval_battle_distance_to_center; commands.cpp
can_start_research/can_start_naval_unit_construction; culture.cpp tech effects;
parsers_declarations.cpp technology_contents/invention_contents any_value.
All at https://github.com/schombert/Project-Alice/tree/v1.3.0/src .
"""
from lib_1966_parser import member, scalar, integer, parse_file, unique_definitions
from lib_1966_semantics import ALICE, effect_body


def land_factors(values: dict, unit_type: str | None) -> dict:
    """Equal strength/tactics/experience/terrain; excludes org damage modifiers.

    Special/support reserve types can occupy the back row; cavalry cannot enter
    that row through the verified normal deployment path. This is eligibility,
    never a prediction of a particular battle's actual placement.
    """
    a, d, support = (values.get(k) for k in ('attack', 'defence', 'support'))
    rear = unit_type in {'special', 'support'}
    return {'unit_type': unit_type, 'rear_eligible': rear,
            'front_attack': 1+a/10 if a is not None else None,
            'front_defence': 1+d/10 if d is not None else None,
            'rear_attack': (1+a/10)*support if rear and a is not None and support is not None else None,
            'rear_defence': (1+d/10)*support if rear and d is not None and support is not None else None,
            'support': support, 'maneuver_target_steps': int(values['maneuver']) if values.get('maneuver') is not None else None}


def naval_factors(values: dict) -> dict:
    g, t, h, e, r = (values.get(k) for k in ('gun_power', 'torpedo_attack', 'hull', 'evasion', 'fire_range'))
    return {'salvo_small_target': g, 'salvo_big_target': g+t if g is not None and t is not None else None,
            'hull_over_received_damage_factor': h/(1-e) if h is not None and e is not None and 0 <= e < 1 else None,
            'fire_range': r, 'covers_initial_separation': r > 2 if r is not None else None,
            'speed': values.get('maximum_speed')}


def domain_violation(stat: str, value: float) -> str | None:
    if stat in {'build_time', 'default_organisation', 'hull', 'discipline'} and value <= 0:
        return 'nonpositive value in verified time/damage divisor'
    if stat in {'min_port_level', 'colonial_points', 'supply_consumption_score'} and (value < 0 or int(value) != value):
        return 'nonnegative integer required in verified base context'
    if stat == 'evasion' and not 0 <= value <= 1:
        return 'outside received-damage fraction domain [0,1]'
    if stat in {'support', 'supply_consumption', 'maximum_speed', 'fire_range', 'maneuver'} and value < 0:
        return 'negative value outside ordinary consumer domain'
    return None


def projection_bounds(q: dict) -> tuple[float, float] | None:
    """Correlation-relaxed subset envelope, not a reachability proof."""
    if q['baseline'] is None or q['status'] != 'applied':
        return None
    return (q['baseline'] + sum(min(0, x['value']) for x in q['assignments']),
            q['baseline'] + sum(max(0, x['value']) for x in q['assignments']))


def report_consumers(units: dict, projections: dict, rep) -> None:
    factors = {}
    for unit in sorted(units):
        data = units[unit]
        qs = projections[unit]['stats']
        scenarios = {}
        for scenario, field in [('baseline', 'baseline'), ('all_effects', 'final')]:
            values = {s:q[field] if q['status']=='applied' else None for s,q in qs.items()}
            scenarios[scenario] = (land_factors(values, data['unit_type']) if data['unit_domain']=='land' else naval_factors(values))
        factors[unit] = scenarios
        rep.add('INFO', f'{unit}: conditional {data["unit_domain"]} consumer factors={scenarios}; '
                'equal external battle conditions; all-effects is not dated acquisition; V2 unverified.',
                code='consumer_factors', category='mechanics', engine=ALICE, unit=unit,
                evidence='pinned_consumer_formula', uncertainty='no full battle or placement simulation', data=scenarios)
        for stat, q in sorted(qs.items()):
            if q['superseded'] or q['base_superseded']:
                rep.add('INFO', f'{unit} {stat}: source-order member precedence; overwritten occurrences retained.',
                        code='member_precedence', category='engine_semantics', engine=ALICE, unit=unit, stat=stat,
                        evidence='pinned_generated_parser', data={'base_superseded':q['base_superseded'], 'superseded':q['superseded'], 'selected':q['assignments']})
            bounds = projection_bounds(q)
            if bounds is None:
                continue
            bad_base = domain_violation(stat, q['baseline'])
            problems = [domain_violation(stat, v) for v in bounds]
            if bad_base or any(problems):
                rep.add('FAIL' if bad_base else 'WARN',
                        f'{unit} {stat}: baseline={q["baseline"]}; relaxed bounds={bounds}; '
                        f'{bad_base or next(p for p in problems if p)}. Bounds do not prove acquisition.',
                        code='consumer_domain', category='technical_invariant', engine=ALICE, unit=unit, stat=stat,
                        evidence='pinned_consumer_domain', uncertainty='base is direct; envelope combinations conditional',
                        basis='technical_contract' if bad_base else 'conditional_model',
                        data={'baseline':q['baseline'], 'bounds':bounds, 'assignments':q['assignments']})
            if stat=='evasion' and bounds[1] == 1:
                rep.add('WARN', f'{unit}: evasion=1 permits immunity in this consumer; requires an explicit design decision.',
                        code='evasion_immunity', category='design_question', engine=ALICE, unit=unit, stat=stat)
        rear = scenarios['baseline'].get('rear_eligible')
        if rear and scenarios['baseline']['support'] == 0:
            rep.add('WARN', f'{unit}: type={data["unit_type"]} is rear-eligible with baseline support=0; '
                    'zero damage when deployed there. Activation/actual formation must be considered; no role change applied.',
                    code='zero_rear_support', category='design_question', engine=ALICE, unit=unit, stat='support',
                    evidence='pinned_deployment_and_damage', uncertainty='conditional on activation and rear placement')
        if data['unit_domain']=='naval' and scenarios['all_effects']['covers_initial_separation']:
            rep.add('INFO', f'{unit}: all-effects fire_range exceeds initial separation (2 center distances); '
                    'not a linear range upgrade, not a full battle outcome.', code='range_geometry', category='mechanics',
                    engine=ALICE, unit=unit, stat='fire_range', evidence='pinned_initial_geometry')
    if {'infantry','guard'} <= factors.keys():
        comparison = {}
        for name in ['baseline','all_effects']:
            inf, guard = factors['infantry'][name], factors['guard'][name]
            comparison[name] = {k:guard[k]/inf[k] if inf[k] and guard[k] is not None else None
                                for k in ['front_attack','front_defence']}
        rep.add('INFO', f'guard/infantry equal-condition damage-factor ratios={comparison}; '
                'discipline, organisation, cost and recruitment restrictions remain separate.',
                code='infantry_guard_comparison', category='mechanics', engine=ALICE,
                evidence='pinned_consumer_formula', data=comparison)


def necessary_references(nodes, definitions: set[tuple[str, str]], *, disjunction=False) -> set[tuple[str, str]]:
    """Only positive necessary references. OR intersects; NOT is not a grant.

    Country scopes, probability conditions and unknown predicates are NOT claimed
    satisfied. An empty result therefore does not mean unconditional availability.
    """
    parts = []
    for n in nodes:
        refs = set()
        if n.is_group:
            if n.keyword in {'and','or'} and n.operator=='=':
                refs = necessary_references(n.children,definitions,disjunction=n.keyword=='or')
        elif n.operator=='=':
            name = n.value if n.keyword=='invention' else n.key if n.value.lower() in {'yes','1'} else None
            candidates = {k for k in definitions if k[1]==name}
            if len(candidates)==1:
                refs = candidates
        parts.append(refs)
    if not parts:
        return set()
    return set.intersection(*parts) if disjunction else set.union(*parts)


def availability_inventory(files, timing) -> tuple[dict, list]:
    definitions = {}
    previous_by_area, predecessors = {}, {}
    for file in sorted(files):
        kind = 'technology' if '/technologies/' in '/' + file.replace('\\','/') else 'invention'
        for n in parse_file(file).definitions:
            definitions[kind,n.key] = (file,n)
            if kind=='technology':
                area = scalar(n,'area',required=True)
                predecessors[kind,n.key] = previous_by_area.get(area)
                previous_by_area[area] = ('technology',n.key)
    activations, increments = {}, []
    for key,(file,n) in sorted(definitions.items()):
        body = effect_body(n,key[0])
        if body is None:
            continue
        limit = member(n,'limit') if key[0]=='invention' else None
        refs = necessary_references(limit.children if limit else (),set(definitions))
        if predecessors.get(key):
            refs.add(predecessors[key])
        row = {'kind':key[0], 'owner':key[1], 'source':str(n.start),
               'research_reference_year':timing[key].year,
               'research_model_not_before':timing[key].not_before,
               'necessary_references':sorted(refs), 'notes':list(timing[key].notes),
               'probability_years':list(timing[key].probability_years),
               'limit_source':str(limit.start) if limit else None,
               'acquisition':'conditional; research completion/discovery/country not simulated'}
        for child in body.children:
            if child.keyword=='activate_unit' and not child.is_group:
                activations.setdefault(child.value,[]).append(dict(row,source=str(child.start)))
        port = [x for x in body.children if x.keyword=='max_naval_base']
        activate = [x for x in body.children if x.keyword=='activate_building' and x.value=='naval_base']
        if port or activate:
            # Each definition sets one bool increase_building flag, even if both
            # forms/repeated entries occur. Only numeric 1 is accepted by Alice.
            valid = bool(activate) or any(integer(x.value,x.start)==1 for x in port if not x.is_group)
            increments.append(dict(row,increment=1 if valid else 0,
                                   invalid_tokens=[str(x.start) if x.is_group else x.value for x in port if x.is_group or integer(x.value,x.start)!=1]))
    return activations,increments


def report_availability(inventory, units, projections, files, timing, rep) -> None:
    activations, increments = availability_inventory(files,timing)
    has_navy = any(d['unit_domain']=='naval' for d in units.values())
    if has_navy:
        buildings = unique_definitions(parse_file(inventory.require('common/buildings.txt')).definitions)
        cap = integer(scalar(buildings['naval_base'],'max_level',required=True), buildings['naval_base'].start)
    else:
        cap = None
    tech_increments = sorted([x for x in increments if x['kind']=='technology'],key=lambda x:(x['research_reference_year'],x['owner']))
    potential = sum(x['increment'] for x in increments)
    research_potential = sum(x['increment'] for x in tech_increments)
    if has_navy:
        rep.add('INFO', f'Naval bases: configured max={cap}; direct tech/invention increase flags={potential}; '
            'initial levels, scripted grants, ownership and completion are outside this research scenario; V2 unverified.',
            code='port_progression',category='availability',engine=ALICE,evidence='pinned_building_flags',
            data={'configured_max':cap,'direct_flag_potential':potential,'increments':increments})
    if cap is not None and potential < cap:
        rep.add('WARN', f'Configured naval-base level {cap} exceeds direct increase-flag potential {potential}; '
                'not proof of global impossibility (history/scripts are not simulated).',
                code='port_cap_gap',category='availability',engine=ALICE,evidence='effective_sources',cause='port_progression')
    if any(x['invalid_tokens'] for x in increments):
        rep.add('FAIL','Invalid max_naval_base token in pinned Alice increase-building contract.',
                code='port_increment_domain',category='technical_invariant',engine=ALICE,data={'increments':increments})
    for unit,data in sorted(units.items()):
        gates = activations.get(unit,[])
        detail = {'active_in_definition':data['active'],'activation_paths':gates,
                  'primary_culture_only':data.get('primary_culture'),
                  'can_build_overseas':data.get('can_build_overseas'),
                  'construction_goods':data['build_cost'], 'supply_goods':data['supply_cost'],
                  'buildability':'conditional; goods, recruitment, control, disarmament and national history excluded'}
        rep.add('INFO',f'{unit}: initially_active={data["active"]}; activation paths={gates}; unlock is not construction.',
                code='unit_activation',category='availability',engine=ALICE,unit=unit,evidence='effective_activation_sources',data=detail)
        if data['unit_domain']!='naval':
            continue
        q = projections[unit]['stats'].get('min_port_level',{})
        required = q.get('final')
        if required is None:
            continue
        raw = data['raw_stats'].get('min_port_level')
        if raw is not None and float(raw)!=required:
            rep.add('WARN',f'{unit}: raw port token {raw} is parsed as integer {required}; V2 unverified.',
                    code='port_integer_conversion',category='engine_semantics',engine=ALICE,unit=unit,stat='min_port_level')
        if required > cap:
            rep.add('FAIL',f'{unit}: required port {required} exceeds configured cap {cap}.',
                    code='port_requirement_cap',category='technical_invariant',engine=ALICE,unit=unit,stat='min_port_level')
        count, year = 0, None
        for inc in tech_increments:
            count += inc['increment']
            if count >= required:
                year = inc['research_reference_year']
                break
        if required==0:
            year = None
        anchors = [g['research_model_not_before'] for g in gates if g['research_model_not_before'] is not None]
        gate = min(anchors) if anchors else None
        rep.add('WARN' if (required > research_potential or (gate is not None and year is not None and year > gate)) else 'INFO',
                f'{unit}: port={required}, activation research bound={gate}, tech-only port reference={year}; '
                'completion and national alternatives remain conditional, no absolute availability date.',
                code='construction_path',category='availability',engine=ALICE,unit=unit,stat='min_port_level',
                evidence='research_infrastructure_scenario',data={'required_port':required,'activation_bound':gate,
                'tech_port_reference':year,'configured_cap':cap,'direct_flag_potential':potential})
