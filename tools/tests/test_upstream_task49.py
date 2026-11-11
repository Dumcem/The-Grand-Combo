"""Static contracts for the upstream-first reconciliation."""

import unittest

from test_upstream_task42 import ROOT, decision, definitions, section, event
from test_upstream_task47 import option
from lib_1966_parser import scalar, walk
from lib_1966_runtime import compose_runtime


def shape(nodes):
    return [(node.key, shape(node.children) if node.is_group else node.value) for node in nodes]


class UpstreamFirstTests(unittest.TestCase):
    def test_native_menu_uses_a_country_pending_flag_until_any_response(self):
        pending = 'native_policy_menu_pending'
        menu = decision('New_World', 'native_integration_status_on')
        potential = section(menu, 'potential')
        guards = [shape(node.children) for node in potential.children if node.key == 'NOT']
        self.assertIn([('has_country_flag', pending)], guards)
        self.assertNotIn([('has_country_flag', 'native_integration_status_on')], guards)
        self.assertEqual(shape(section(menu, 'effect').children), [
            ('clr_country_flag', 'native_integration_status_on'),
            ('set_country_flag', pending), ('country_event', '100'),
        ])
        popup = event('Utility', 100)
        self.assertEqual(scalar(popup, 'is_triggered_only'), 'yes')
        self.assertEqual(scalar(popup, 'allow_multiple_instances'), 'yes')
        choices = [node for node in popup.children if node.key == 'option']
        self.assertEqual([scalar(node, 'name') for node in choices],
                         [f'EVTOPT{letter}100' for letter in 'ABCD'])
        for choice in choices:
            self.assertEqual(scalar(choice, 'clr_country_flag'), pending)
        for choice in choices[:3]:
            retry, = (node for node in walk(choice.children)
                      if node.is_group and scalar(node, 'country_event') == '100')
            self.assertEqual(shape(retry.children), [
                ('set_country_flag', pending), ('country_event', '100'),
            ])

    def test_native_ai_negates_the_full_eligibility_gate(self):
        popup = event('Utility', 100)
        for letter in 'ABC':
            choice = option(popup, f'EVTOPT{letter}100')
            chance = section(choice, 'ai_chance')
            zero_weight = next(node for node in chance.children if node.key == 'modifier')
            self.assertEqual(scalar(zero_weight, 'factor'), '0')
            negated = section(section(zero_weight, 'NOT'), 'AND')
            execution = next(node for node in choice.children if node.key == 'random_owned')
            eligible = section(section(execution, 'limit'), 'owner')
            self.assertEqual(shape(negated.children), shape(eligible.children))

    def test_native_menu_assets_are_shared_by_both_profiles(self):
        for timeline in (None, 'TGC_Timeline_1966'):
            inventory = compose_runtime(ROOT, 'TGC', timeline)
            for path in ('events/Utility.txt', 'decisions/New_World.txt'):
                self.assertEqual(inventory.require(path), f'TGC/{path}')
        root = ROOT / 'TGC'
        self.assertFalse((ROOT / 'TGC_Timeline_1966/map/region.txt').exists())
        self.assertIn(b'cant_do_because = {}', (root / 'map/region.txt').read_bytes())
        picture = root / 'gfx/pictures/events/native_americans.dds'
        self.assertEqual(picture.read_bytes()[:4], b'DDS ')
        labels = (root / 'localisation/00_events-utility.csv').read_bytes().splitlines()
        for key in ('EVTNAME100', 'EVTDESC100', *(f'EVTOPT{letter}100' for letter in 'ABCD')):
            self.assertEqual(sum(line.startswith(key.encode() + b';') for line in labels), 1)

    def test_anatolia_without_bosphorus_cedes_only_the_selected_provinces(self):
        choice = option(event('RUSFlavor', 500291), 'EVTOPTB500291')
        cessions = [node for node in choice.children if scalar(node, 'secede_province') == 'GRE']
        cession, = cessions
        self.assertEqual(cession.key, 'any_owned')
        limit = section(cession, 'limit')
        self.assertEqual(scalar(limit, 'is_core'), 'GRE')
        exclusions = {shape(node.children)[0] for node in limit.children if node.key == 'NOT'}
        self.assertEqual(exclusions, {('region', 'TUR_861'), ('region', 'TUR_860'),
                                      ('province_id', '865'), ('province_id', '866'),
                                      ('province_id', '862')})
        self.assertEqual(scalar(section(choice, 'relation'), 'who'), 'GRE')

    def test_petrograd_rewards_are_one_time_in_each_direction(self):
        for name, flag in (
            ('petrograd_renaming_act', 'petrograd_renaming_completed'),
            ('petrograd_renaming_act2', 'petersburg_restoration_completed'),
        ):
            with self.subTest(name=name):
                rename = decision('RUS', name)
                guards = [shape(node.children) for node in section(rename, 'potential').children
                          if node.key == 'NOT']
                self.assertIn([('has_country_flag', flag)], guards)
                effects = list(walk(section(rename, 'effect').children))
                self.assertIn(('set_country_flag', flag), [(node.key, node.value) for node in effects])
                self.assertFalse(any(node.key == 'clr_country_flag' and node.value == flag for node in effects))

    def test_peace_goals_keep_the_new_terms_without_extender(self):
        cbs = {node.key: node for node in definitions('common/cb_types.txt')}
        self.assertEqual(scalar(cbs['take_puppet'], 'po_release_puppet'), 'yes')
        self.assertIsNone(scalar(cbs['take_puppet'], 'po_add_to_sphere'))
        self.assertIsNotNone(section(cbs['free_peoples'], 'allowed_countries'))
        self.assertIsNotNone(section(cbs['liberate_country'], 'allowed_countries'))
        self.assertNotIn('acquire_province', cbs)
        self.assertNotIn(b'load = ', (ROOT / 'TGC.mod').read_bytes())

    def test_morocco_cleanup_matches_a_buyer_who_can_pay(self):
        cleanup = decision('North_Africa', 'cleanup_morocco')
        effect = section(cleanup, 'effect')
        self.assertEqual(scalar(effect, 'set_global_flag'), 'cleanup_morocco')
        buyer = section(section(effect, 'random_country'), 'limit')
        self.assertEqual(scalar(buyer, 'exists'), 'yes')
        self.assertEqual(scalar(buyer, 'money'), '75000')
