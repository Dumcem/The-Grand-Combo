"""Regressions for the shared scripted guard and Alice 1.3.0 construction."""
import hashlib
from itertools import product
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_1966_applied as independent
from lib_1966_construction import delivery_gates, naval_time_multiplier, procurement_scenario
from lib_1966_parser import ScriptError
from lib_1966_runtime import RuntimeInventory, Source, compose_runtime
from test_upstream_task42 import decision, evaluate, section
from lib_1966_parser import scalar, walk


ROOT = independent.ROOT
DECISION_PATH = 'decisions/3_Clean-Up.txt'
TARGETS = {
    'ai_give_warships_steamer': (45, '9c6715a928ae733f3c945b498fa694d822ca7699147c3d87291a9a6eabc71eca'),
    'ai_give_warships_steamer_secondary_power': (14, '2aec8833483dfe00c8e05a9a6df82f2c73cecff23e55e441d16ef9a32ec22f09'),
}
GUARD_LINE = b'\t\t\tNOT = { has_global_flag = project_alice }\n'


class ScriptedNavalGuard(unittest.TestCase):
    def test_shared_effective_file(self):
        # Independent direct overlay check, and production inventory agreement.
        self.assertTrue((ROOT / 'TGC' / DECISION_PATH).is_file())
        self.assertFalse((ROOT / 'TGC_Timeline_1966' / DECISION_PATH).exists())
        for timeline in (None, 'TGC_Timeline_1966'):
            inventory = compose_runtime(ROOT, timeline_root=timeline)
            self.assertEqual(inventory.require(DECISION_PATH), 'TGC/' + DECISION_PATH)

    def test_only_two_guards_and_original_decisions_preserved(self):
        raw = (ROOT / 'TGC' / DECISION_PATH).read_bytes().replace(b'\r\n', b'\n')
        self.assertEqual(raw.count(GUARD_LINE), 2)
        definitions = independent.reference_tree(raw.decode('utf-8-sig'))[0][1]
        for name, (expected_ships, original_digest) in TARGETS.items():
            with self.subTest(name=name):
                body, = [fields for k, fields, _, _ in definitions if k == name]
                potential, = [fields for k, fields, _, _ in body if k == 'potential']
                key, children, _, _ = potential[0]
                self.assertEqual((key, [(k, v) for k, v, _, _ in children]),
                                 ('NOT', [('has_global_flag', 'project_alice')]))
                effect, = [fields for k, fields, _, _ in body if k == 'effect']
                effect_keys = list(self.keys(effect))
                self.assertEqual(effect_keys.count('sub_unit'), expected_ships)
                self.assertIn('treasury', effect_keys)
                self.assertIn('add_country_modifier', effect_keys)
                # Fingerprints of the ordered original blocks at 158ab2d.
                del potential[0]
                allow, = [fields for k, fields, _, _ in body if k == 'allow']
                allow[:] = [item for item in allow if item[0] != 'OR']
                scope, = [fields for k, fields, _, _ in effect if k == 'any_owned']
                original, = [fields for k, fields, _, _ in scope if k == 'owner']
                effect[:] = original
                restored = json.dumps(self.shape(body), separators=(',', ':')).encode()
                self.assertEqual(hashlib.sha256(restored).hexdigest(), original_digest)

                flag_name = children[0][1]
                # A conjunctive potential blocks entry to the entire effect.
                # Pinned Alice evaluates the token true; canonical V2 has no flag.
                for flags, original_potential, allowed in [
                    ({}, False, False), ({}, True, True),
                    ({'project_alice': True}, False, False),
                    ({'project_alice': True}, True, False),
                ]:
                    guard_passes = not flags.get(flag_name, False)
                    eligible_effects = effect_keys if all((guard_passes, original_potential)) else []
                    self.assertEqual(eligible_effects, effect_keys if allowed else [])

    def test_package_guard_matches_sum_of_eligible_debits_at_both_checks(self):
        inventions = ('pre_dreadnought', 'ironclads', 'protected_cruisers',
                      'steamer_transports', 'commerce_raiders')
        ports = ((), ((True, False, False, True),), ((True, False, True, True),),
                 ((True, True, True, True),), ((True, False, False, False),))
        for name in TARGETS:
            package = decision('3_Clean-Up', name)
            allow = section(package, 'allow')
            apply = section(section(package, 'effect'), 'any_owned')
            limit = section(apply, 'limit')
            self.assertEqual(scalar(limit, 'is_capital'), 'yes')
            owner = section(limit, 'owner')
            effects = section(apply, 'owner')
            floor = int(scalar(allow, 'money'))
            selectors = [
                (section(n, 'limit').children,
                 -sum(int(e.value) for e in walk(n.children) if e.key == 'treasury'))
                for n in effects.children if n.key == 'random_owned'
            ]
            entry_gate = [n for n in allow.children if n.key in {'money', 'OR'}]
            payment_gate = [n for n in owner.children if n.key in {'money', 'OR'}]
            for bits, culture, owned_ports in product(product((False, True), repeat=5),
                                                      ('british', 'japanese', 'other'), ports):
                discovered = {key for key, enabled in zip(inventions, bits) if enabled}
                def matches(node, balance, province=None):
                    if node.key == 'invention':
                        return node.value in discovered
                    if node.key in {'is_culture_group', 'primary_culture'}:
                        return culture == {'pan_british': 'british', 'japanese': 'japanese'}[node.value]
                    if node.key == 'money':
                        return balance >= int(node.value)
                    if node.key == 'owner':
                        return evaluate(node.children, lambda n: matches(n, balance))
                    if node.key == 'any_owned_province':
                        return any(evaluate(node.children, lambda n: matches(n, balance, p))
                                   for p in owned_ports)
                    if node.key in {'port', 'is_overseas', 'is_colonial', 'controlled_by'}:
                        index = ('port', 'is_overseas', 'is_colonial', 'controlled_by').index(node.key)
                        return province[index] == (node.value in {'yes', 'THIS'})
                    raise AssertionError(node.key)

                debit = sum(cost for gate, cost in selectors
                            if any(evaluate(gate, lambda n: matches(n, 0, p)) for p in owned_ports))
                minimum = max(debit, floor)
                for balance in (minimum - 1, minimum):
                    for gate in (entry_gate, payment_gate):
                        self.assertEqual(evaluate(gate, lambda n: matches(n, balance)), balance >= minimum,
                                         (name, discovered, culture, owned_ports, balance))

    @staticmethod
    def shape(tree):
        return [(key, ScriptedNavalGuard.shape(value) if isinstance(value, list) else value)
                for key, value, _, _ in tree]

    @staticmethod
    def keys(tree):
        for key, value, _, _ in tree:
            yield key
            if isinstance(value, list):
                yield from ScriptedNavalGuard.keys(value)


class NavalConstructionGates(unittest.TestCase):
    def test_calendar_and_economic_gates_are_independent(self):
        for age, goods, expected in [(35, True, False), (89, True, False),
                                     (90, False, False), (90, True, True)]:
            with self.subTest(age=age, goods=goods):
                gates = delivery_gates(90, queue_position=1, age_days=age, materials_complete=goods)
                self.assertIs(gates['eligible_for_delivery'], expected)

    def test_queue_promotion_keeps_enqueue_age(self):
        behind = delivery_gates(90, queue_position=2, age_days=110, materials_complete=True)
        promoted = delivery_gates(90, queue_position=1, age_days=111, materials_complete=False)
        complete = delivery_gates(90, queue_position=1, age_days=146, materials_complete=True)
        self.assertTrue(behind['base_time_elapsed'])
        self.assertFalse(behind['eligible_for_delivery'])
        self.assertTrue(promoted['base_time_elapsed'])
        self.assertFalse(promoted['eligible_for_delivery'])
        self.assertTrue(complete['eligible_for_delivery'])

    def test_effective_override_changes_rate_only(self):
        source = Source('common/test.lua', 'TGC/common/test.lua', 'core', 'conditional/context')
        inventory = RuntimeInventory({source.runtime_path: source}, [], [], [])
        with patch('lib_1966_construction.read_text', return_value=(
            '-- ALICE_NAVAL_UNIT_BUILD_TIME_MULT = 99\n'
            'ALICE_NAVAL_UNIT_BUILD_TIME_MULT = 0.5, -- first assignment\n'
            'alice_naval_unit_build_time_mult = 2\n'
            'ALICE_NAVAL_UNIT_BUILD_TIME_MULT = 99'
        )):
            multiplier, origins = naval_time_multiplier(inventory)
        self.assertEqual(multiplier, 2)
        self.assertEqual(origins, ['TGC/common/test.lua:3:1'])
        scenario = procurement_scenario(35, multiplier)
        self.assertEqual(scenario['national_build_time_days'], 35)
        self.assertEqual(scenario['procurement_time_factor_days'], 70)
        self.assertAlmostEqual(scenario['theoretical_required_basket_fraction_per_day'], 1 / 70)
        self.assertFalse(delivery_gates(90, queue_position=1, age_days=70,
                                        materials_complete=True)['eligible_for_delivery'])

    def test_conflicting_overrides_do_not_guess_load_precedence(self):
        sources = {f'common/{name}.lua': Source(f'common/{name}.lua', f'TGC/common/{name}.lua',
                                               'core', 'conditional/context') for name in ('a', 'b')}
        inventory = RuntimeInventory(sources, [], [], [])
        with patch('lib_1966_construction.read_text',
                   side_effect=['ALICE_NAVAL_UNIT_BUILD_TIME_MULT=2\n',
                                'ALICE_NAVAL_UNIT_BUILD_TIME_MULT=3\n']):
            with self.assertRaisesRegex(ScriptError, 'load precedence unresolved'):
                naval_time_multiplier(inventory)


class NavalConstructionAudit(unittest.TestCase):
    def test_json_matches_independent_roster_and_times(self):
        result = subprocess.run([sys.executable, '-B', 'TGC/tools/audit_1966_balance.py', '--json'],
                                cwd=ROOT, capture_output=True, check=True)
        rows = [row for row in json.loads(result.stdout) if row['code'] == 'alice_naval_construction']
        for layer, composition in [('TGC', 'core'), ('TGC_Timeline_1966', 'core + Timeline')]:
            _, units, cuts = independent.TransportRuntimeContracts().inputs(layer)
            selected = [row for row in rows if row['data']['composition'] == composition]
            self.assertCountEqual([row['unit'] for row in selected], units.keys())
            for row in selected:
                unit, data = row['unit'], row['data']
                with self.subTest(layer=layer, unit=unit):
                    base = units[unit]
                    national = base + sum(delta for _, _, _, targets, delta in cuts if unit in targets)
                    self.assertEqual(row['engine'], 'alice_1.3.0')
                    self.assertEqual(row['level'], 'INFO')
                    self.assertEqual(data['base_build_time_days'], base)
                    self.assertEqual(data['delivery_calendar_floor_days_since_enqueue'], base)
                    self.assertEqual(data['global_naval_time_multiplier'], 1.0)
                    self.assertEqual(data['procurement_scenarios']['unmodified']['national_build_time_days'], base)
                    scenario = data['procurement_scenarios']['all_direct_effects']
                    self.assertEqual(scenario['national_build_time_days'], national)
                    self.assertEqual(scenario['procurement_time_factor_days'], national)
                    self.assertAlmostEqual(scenario['theoretical_required_basket_fraction_per_day'], 1 / national)
                    self.assertTrue(data['observed_state'])
                    self.assertTrue(all(value is None for value in data['observed_state'].values()))
                    if unit in {'clipper_transport', 'steam_transport'}:
                        self.assertEqual((base, national), (90, 45 if layer == 'TGC' else 35))


if __name__ == '__main__':
    unittest.main()
