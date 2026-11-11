"""Static regressions for the seven Task 35 scripted naval paths."""
import hashlib
import re
import unittest

from test_1966_applied import ROOT, reference_tree
from lib_1966_runtime import compose_runtime


FLAG = [('NOT', [('has_global_flag', 'project_alice')])]
ALICE_FLAG = FLAG[0][1][0]
GUARD = b'NOT = { has_global_flag = project_alice }'
BEIYANG_TERMS = re.compile(
    rb'^\t\t1569 = \{\n\t\t\tlimit = \{ '
    + re.escape(GUARD)
    + rb' \}\n\t\t\tTHIS = \{\n(?P<body>.*?)^\t\t\t\}\n\t\t\}\n',
    re.MULTILINE | re.DOTALL
)
FRENCH_ALICE_PORT = re.compile(
    rb'^\t\t\trandom_owned = \{\n\t\t\t\tlimit = \{\n'
    rb'\t\t\t\t\thas_global_flag = project_alice\n.*?^\t\t\t\}\n',
    re.MULTILINE | re.DOTALL
)
# Whole-file fingerprints at 3dadb6622, with line endings normalized.
# Later baselines include the reconciled Russian, French, Chinese and UncivFlavor hunks.
BASELINE = {
    'decisions/China.txt': (1, '0071e8b893410f110c849ccda3a58d0d97659ba0fbe7e7d12b72373f4911728a'),
    'decisions/France.txt': (1, '7da32585362cd8eef4b18bfb2fee06f4da322c65698477de570b8cdc57350713'),
    'decisions/SWE.txt': (1, '3d717656dc57cf98cf8e7e8e445985cad723bf2c9352d681a185938491e12869'),
    'decisions/UncivFlavor.txt': (1, '71bf5e03191fa2e2db98561e41e318ab5aa7cc2ff62c868b6d953eb329180610'),
    'events/China.txt': (4, '39379e3420ca2ec32a5945cd42ce1c27c2a25e45e413cd1c9195ab01dc271adc'),
    'events/EIC.txt': (1, 'e8c28538980af5ee348a4601eaa3eacd221661e3c1d14da88e4d27ce0ab1eb45'),
    'decisions/JAP.txt': (1, 'b9e5bb33bc61866ac478b313eb9cff798b35b141b781a6e0c65f933254516e97'),
    'decisions/RUS.txt': (1, '76475a97b5d1cbf530ff4a65f82bed9b01351a9196bbd8bebb654b031ebe9227'),
}


def shape(nodes):
    return [(key, shape(value) if isinstance(value, list) else value)
            for key, value, _, _ in nodes]


def fields(nodes, key):
    return [value for name, value in nodes if name == key]


def field(nodes, key):
    value, = fields(nodes, key)
    return value


def project(nodes, *, alice):
    """Project the guarded scopes, assuming other conditions are eligible."""
    result = []
    for key, value in nodes:
        if isinstance(value, list):
            limits = fields(value, 'limit')
            if limits:
                limit, = limits
                if (alice and FLAG[0] in limit) or (not alice and ALICE_FLAG in limit):
                    continue
                rest = [condition for condition in limit if condition not in (FLAG[0], ALICE_FLAG)]
                if rest != limit:
                    value = [(name, item) for name, item in value if name != 'limit']
                    if rest:
                        value.insert(0, ('limit', rest))
            value = project(value, alice=alice)
        result.append((key, value))
    return result


def leaves(nodes):
    for key, value in nodes:
        if isinstance(value, list):
            yield from leaves(value)
        else:
            yield key, value


class ScriptedNavalPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {path: (ROOT / 'TGC' / path).read_bytes().replace(b'\r\n', b'\n')
                     for path in BASELINE}
        cls.trees = {}
        for path, raw in cls.files.items():
            if BASELINE[path][0]:
                # Legacy encodings are safe here because only ASCII script keys
                # and delimiters are interpreted.
                text = raw.removeprefix(b'\xef\xbb\xbf').decode('latin1')
                cls.trees[path] = shape(reference_tree(text))

    def decision(self, file, name):
        return field(field(self.trees[f'decisions/{file}.txt'], 'political_decisions'), name)

    def event(self, file, event_id):
        event, = [node for node in fields(self.trees[f'events/{file}.txt'], 'country_event')
                  if ('id', event_id) in node]
        return event

    def test_effective_paths_are_shared_by_core_and_timeline(self):
        for timeline in (None, 'TGC_Timeline_1966'):
            inventory = compose_runtime(ROOT, timeline_root=timeline)
            for path in BASELINE:
                with self.subTest(timeline=timeline, path=path):
                    self.assertFalse((ROOT / 'TGC_Timeline_1966' / path).exists())
                    self.assertEqual(inventory.require(path), 'TGC/' + path)

    def test_original_scripts_recovered_by_reversing_only_the_approved_guards(self):
        for path, (guard_count, digest) in BASELINE.items():
            with self.subTest(path=path):
                raw = self.files[path]
                self.assertEqual(raw.count(GUARD), guard_count)
                if path == 'events/China.txt':
                    raw, count = BEIYANG_TERMS.subn(
                        lambda match: re.sub(rb'^\t\t', b'', match['body'], flags=re.MULTILINE), raw)
                    self.assertEqual(count, 3)
                if path == 'decisions/France.txt':
                    raw, count = FRENCH_ALICE_PORT.subn(b'', raw)
                    self.assertEqual(count, 1)
                raw = re.sub(rb'^\t+(?:limit = \{ ' + re.escape(GUARD)
                             + rb' \}|' + re.escape(GUARD) + rb')\n', b'', raw, flags=re.MULTILINE)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)

    def test_swedish_and_fishermen_decisions_are_blocked_before_costs(self):
        for file, name, cost in (
            ('SWE', 'svenska_pansarbats_foreningen', ('money', '-0.1')),
            ('UncivFlavor', 'conscript_fishermen', ('treasury', '-10000')),
        ):
            with self.subTest(name=name):
                decision = self.decision(file, name)
                self.assertEqual(field(decision, 'potential')[0], FLAG[0])
                self.assertIn(cost, list(leaves(field(decision, 'effect'))))

    def test_japanese_and_russian_packages_are_blocked_at_entry(self):
        for file, name, charges, ship_count in (
            ('JAP', 'imperial_japanese_navy', ['-80000'], 16),
            ('RUS', 'russian_navy_reforms', ['-100000', '-150000'], 20),
        ):
            with self.subTest(name=name):
                decision = self.decision(file, name)
                self.assertIn(FLAG[0], field(decision, 'potential'))
                effects = list(leaves(field(decision, 'effect')))
                self.assertEqual(fields(effects, 'treasury'), charges)
                self.assertEqual(effects.count(('value', 'current')), ship_count)
                self.assertTrue(fields(effects, 'activate_technology'))

    def test_french_colonial_effects_and_port_selection_survive(self):
        effect = field(self.decision('France', 'ai_french_west_africa'), 'effect')
        alice = project(effect, alice=True)
        self.assertEqual(fields(alice, 'set_global_flag'), ['ai_french_west_africa'])
        self.assertEqual([field(branch, 'country_event') for branch in fields(alice, 'any_country')],
                         ['99954', '99959'])
        port = field(alice, 'random_owned')
        self.assertFalse(fields(port, 'sub_unit'))
        self.assertEqual(field(field(port, 'limit'), 'owner'), [('ai', 'yes')])
        self.assertEqual(field(port, 'owner'), [('badboy', '-15')])
        original = project(effect, alice=False)
        original_port = field(original, 'random_owned')
        self.assertEqual(field(port, 'limit'), field(original_port, 'limit'))
        self.assertEqual(port, [node for node in original_port if node[0] != 'sub_unit'])
        self.assertEqual(fields(original_port, 'sub_unit'),
                         [[('type', 'steam_transport'), ('value', 'current')]] * 11)

    def test_beiyang_modernization_survives_without_calling_the_supplier(self):
        effect = field(self.decision('China', 'establish_the_beiyang_fleet'), 'effect')
        alice = project(effect, alice=True)
        original = project(effect, alice=False)
        supplier = field(original, 'any_greater_power')
        self.assertEqual(field(supplier, 'country_event'), '99951')
        self.assertEqual(alice, [node for node in original if node[0] != 'any_greater_power'])
        self.assertIn(('set_country_flag', 'beiyang_fleet_established'), alice)
        self.assertIn(('military_reform', 'yes_foreign_navies'), list(leaves(alice)))

    def test_each_queued_beiyang_event_is_safe_even_if_dispatched_directly(self):
        # Alice dispatches queued events directly and executes the selected option.
        # A caller-only guard or a trigger on the event does not protect this case.
        for event_id, option_names in (
            ('99951', ['EVTOPTA99951', 'EVTOPTB99951']),
            ('99952', ['EVTOPTA99952']),
            ('99953', ['EVTOPTA99953']),
        ):
            with self.subTest(event_id=event_id):
                event = self.event('China', event_id)
                self.assertFalse(fields(event, 'immediate'))
                options = fields(event, 'option')
                self.assertEqual([field(option, 'name') for option in options], option_names)
                for option in options:
                    self.assertEqual(project(option, alice=True),
                                     [node for node in option if node[0] in {'name', 'ai_chance'}])
        supplier, = [option for option in fields(self.event('China', '99951'), 'option')
                     if ('name', 'EVTOPTA99951') in option]
        supplier_terms = field(field(project(supplier, alice=False), '1569'), 'THIS')
        self.assertIn(('treasury', '50000'), supplier_terms)
        self.assertEqual(field(field(supplier_terms, 'QNG'), 'country_event'),
                         [('id', '99952'), ('days', '5')])
        qing_option = project(field(self.event('China', '99952'), 'option'), alice=False)
        qing = field(field(qing_option, '1569'), 'THIS')
        self.assertIn(('treasury', '-80000'), qing)
        self.assertEqual(field(qing, 'country_event'), [('id', '99953'), ('days', '730')])
        delivery = project(field(self.event('China', '99953'), 'option'), alice=False)
        self.assertEqual(fields(field(delivery, '1569'), 'sub_unit'),
                         [[('type', 'ironclad'), ('value', 'current')]] * 7)

    def test_eic_transfer_survives_without_the_fleet(self):
        option = field(self.event('EIC', '9990013'), 'option')
        self.assertEqual(project(option, alice=True), [
            ('name', 'EVTOPTA9990013'),
            ('release', 'SRI'),
            ('ENG', [('inherit', 'SRI')]),
        ])
        fleet = fields(field(project(option, alice=False), '1321'), 'sub_unit')
        self.assertEqual([field(ship, 'type') for ship in fleet],
                         ['manowar'] * 21 + ['commerce_raider'] * 19 + ['steam_transport'] * 10)
