"""Static regressions for the seven Task 35 scripted naval paths."""
import unittest

from test_1966_applied import ROOT, reference_tree
from lib_1966_runtime import compose_runtime


FLAG = [('NOT', [('has_global_flag', 'project_alice')])]
ALICE_FLAG = FLAG[0][1][0]
GUARDED_PATHS = (
    'decisions/China.txt', 'decisions/France.txt', 'decisions/SWE.txt',
    'decisions/UncivFlavor.txt', 'events/China.txt', 'events/EIC.txt',
    'decisions/JAP.txt', 'decisions/RUS.txt',
)


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


def ship_grants(nodes):
    for key, value in nodes:
        if key == 'sub_unit':
            yield value
        elif isinstance(value, list):
            yield from ship_grants(value)


class ScriptedNavalPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trees = {
            path: shape(reference_tree((ROOT / 'TGC' / path).read_bytes()
                                       .removeprefix(b'\xef\xbb\xbf').decode('latin1')))
            for path in GUARDED_PATHS
        }

    def decision(self, file, name):
        return field(field(self.trees[f'decisions/{file}.txt'], 'political_decisions'), name)

    def event(self, file, event_id):
        event, = [node for node in fields(self.trees[f'events/{file}.txt'], 'country_event')
                  if ('id', event_id) in node]
        return event

    def test_effective_paths_are_shared_by_core_and_timeline(self):
        for timeline in (None, 'TGC_Timeline_1966'):
            inventory = compose_runtime(ROOT, timeline_root=timeline)
            for path in GUARDED_PATHS:
                with self.subTest(timeline=timeline, path=path):
                    self.assertFalse((ROOT / 'TGC_Timeline_1966' / path).exists())
                    self.assertEqual(inventory.require(path), 'TGC/' + path)

    def test_swedish_and_fishermen_decisions_are_blocked_before_costs(self):
        sweden = self.decision('SWE', 'svenska_pansarbats_foreningen')
        fishermen = self.decision('UncivFlavor', 'conscript_fishermen')
        for decision in (sweden, fishermen):
            self.assertIn(FLAG[0], field(decision, 'potential'))

        swedish_effect = field(sweden, 'effect')
        self.assertEqual(field(swedish_effect, 'any_pop'), [('money', '-0.1')])
        self.assertEqual(field(field(swedish_effect, '329'), 'sub_unit'),
                         [('type', 'cruiser'), ('value', 'current')])
        self.assertIn(('set_country_flag', 'hms_sverige_built'), swedish_effect)

        fishing_effect = field(fishermen, 'effect')
        self.assertEqual(field(fishing_effect, 'treasury'), '-10000')
        self.assertEqual(field(fishing_effect, 'add_country_modifier'),
                         [('name', 'law_changed_by_force'), ('duration', '3650')])
        port = field(fishing_effect, 'any_owned')
        self.assertEqual(field(port, 'limit'), [('port', 'yes')])
        self.assertEqual([(field(branch, 'chance'), field(field(branch, 'sub_unit'), 'type'))
                          for branch in fields(port, 'random')],
                         [('75', 'frigate'), ('5', 'manowar')])

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
                ships = list(ship_grants(field(decision, 'effect')))
                self.assertEqual(len(ships), ship_count)
                self.assertTrue(all(field(ship, 'value') == 'current' for ship in ships))
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
