"""Naval construction contract for Project Alice v1.3.0, ordinary play.

Sources: gamestate/commands.cpp (enqueue), economy/construction.cpp (demand
and progress), economy/economy.cpp (resolve_constructions), parsing/defines.cpp
and defines.hpp (global multiplier). No Victoria II formula is inferred.
"""
import re

from lib_1966_parser import Position, ScriptError, number, read_text
from lib_1966_semantics import ALICE


def naval_time_multiplier(inventory) -> tuple[float, list[str]]:
    key = 'alice_naval_unit_build_time_mult'
    overrides = {}
    for path, source in inventory.selected.items():
        if not path.startswith('common/') or not path.endswith('.lua'):
            continue
        # Alice reads linewise, strips -- comments, takes the first key and
        # numeric token, and parses only lines terminated by a newline.
        for line, raw in enumerate(read_text(source.file).split('\n')[:-1], 1):
            body = raw.split('--', 1)[0].lstrip()
            fields = re.split(r'[\s=]', body, maxsplit=1)
            if fields[0].lower() != key:
                continue
            _, sep, rhs = body.partition('=')
            token = re.split(r'[\s,]', rhs.lstrip(), maxsplit=1)[0] if sep else ''
            origin = Position(source.file, line, 1, 0)
            overrides[source.file] = (number(token, origin), str(origin))
    if not overrides:
        return 1.0, ['Alice v1.3.0 parsing/defines.hpp default']
    values = {value for value, _ in overrides.values()}
    origins = [origin for _, origin in overrides.values()]
    if len(values) != 1:
        raise ScriptError(f'{key}: conflicting effective files, load precedence unresolved: {origins}')
    value = values.pop()
    if value <= 0:
        raise ScriptError(f'{key}: nonpositive construction multiplier at {origins}')
    return value, origins


def delivery_gates(base_days, *, queue_position=None, age_days=None, materials_complete=None) -> dict:
    """Position is one-based. Unknown observations stay unknown."""
    head = queue_position == 1 if queue_position is not None else None
    elapsed = age_days >= base_days if age_days is not None and base_days is not None else None
    gates = (head, elapsed, materials_complete)
    return {
        'queue_position': queue_position, 'age_days_since_enqueue': age_days,
        'at_queue_head': head, 'base_time_elapsed': elapsed,
        'materials_complete': materials_complete,
        'eligible_for_delivery': False if False in gates else True if all(gates) else None,
    }


def procurement_scenario(national_days, multiplier) -> dict:
    nominal = national_days * multiplier if national_days is not None else None
    return {
        'national_build_time_days': national_days,
        'procurement_time_factor_days': nominal,
        'theoretical_required_basket_fraction_per_day': 1 / nominal if nominal is not None and nominal > 0 else None,
    }


def report_naval_construction(composition, inventory, projections, rep) -> None:
    multiplier, origins = naval_time_multiplier(inventory)
    for unit, projection in sorted(projections.items()):
        time = projection['stats']['build_time']
        base = time['baseline']
        national = time['final'] if time['status'] == 'applied' else None
        scenarios = {
            'unmodified': procurement_scenario(base, multiplier),
            'all_direct_effects': procurement_scenario(national, multiplier),
        }
        applied = scenarios['all_direct_effects']
        rate = applied['theoretical_required_basket_fraction_per_day']
        rate_text = f'{rate:.6g}' if rate is not None else 'unresolved'
        rep.add('INFO',
                f'{composition} {unit}: base build_time={base}; national build_time with all direct effects={national}; '
                f'procurement factor={applied["procurement_time_factor_days"]} days ({rate_text} of required basket/day at most); '
                f'earliest calendar eligibility={base} days since enqueue. '
                'Queue position, age, materials and economic completion unobserved.',
                code='alice_naval_construction', category='mechanics', engine=ALICE, unit=unit, stat='build_time',
                source=time['baseline_origin']['source'], evidence='pinned_naval_construction_consumers',
                uncertainty='conditional national stats; budget, prices, supply and queue state unobserved',
                data={'composition': composition, 'base_build_time_days': base,
                      'delivery_calendar_floor_days_since_enqueue': base,
                      'global_naval_time_multiplier': multiplier, 'multiplier_origins': origins,
                      'procurement_scenarios': scenarios, 'observed_state': delivery_gates(base)})
