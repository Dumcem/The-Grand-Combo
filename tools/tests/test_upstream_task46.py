"""Static regressions for setup, reforms and POP conditions."""

import unittest

from test_upstream_task42 import ROOT, decision, definitions, section
from lib_1966_parser import parse_script, scalar, walk


class SetupAndPopReconciliationTests(unittest.TestCase):
    def test_setup_carrier_preserves_the_timeline_end_game_gate(self):
        path = 'decisions/00_Setup.txt'
        core, = definitions(path)
        carrier = (ROOT / 'TGC_Timeline_1966' / path).read_text(encoding='latin-1')
        timeline, = parse_script(carrier, file=path).definitions
        for setup, year in ((core, '1936'), (timeline, '1966')):
            with self.subTest(year=year):
                end_game = section(setup, 'option_end_game')
                for gate in ('potential', 'allow'):
                    self.assertEqual(scalar(section(end_game, gate), 'year'), year)
                nodes = tuple(walk(setup.children))
                retired = {'mexico_city', 'summer_palace', 'moscow_city'}
                self.assertFalse(any(node.key == 'set_province_flag' and
                                     node.value in retired for node in nodes))
                for school in ('prussian', 'czech', 'japanese', 'chinese'):
                    self.assertFalse(any(node.value == f'set_ts_{school}' for node in nodes))
                    self.assertTrue(any(node.key == 'has_country_modifier' and
                                        node.value == f'ts_{school}' for node in nodes))

    def test_migration_campaigns_keep_their_factors_and_country_scope(self):
        sections = {node.key: node for node in definitions('common/pop_types.txt')}
        for section_name, name, factor in (
            ('colonialmigration_chance', 'more_colonial_settlement', '0.1'),
            ('emigration_chance', 'less_emigration', '-0.5'),
        ):
            with self.subTest(campaign=name):
                modifiers = sections[section_name].children
                consumer, = (node for node in modifiers if node.key == 'modifier'
                             and any(item.value == name for item in walk(node.children)))
                self.assertEqual(scalar(consumer, 'factor'), factor)
                self.assertEqual(scalar(section(consumer, 'country'), 'has_country_modifier'), name)
                event_nodes = [item for node in definitions('events/JANFlavor.txt')
                               for item in walk(node.children)]
                producer, = (node for node in event_nodes if node.key == 'add_country_modifier'
                             and scalar(node, 'name') == name)
                self.assertEqual(scalar(producer, 'duration'), '-1')
                self.assertTrue(any(node.key == 'remove_country_modifier' and
                                    node.value == name for node in event_nodes))

    def test_pop_conditions_use_the_modifiers_assigned_by_the_decisions(self):
        pop_types = ('aristocrats', 'artisans', 'bureaucrats', 'capitalists', 'clergymen',
                     'clerks', 'craftsmen', 'farmers', 'labourers', 'officers', 'pioneers',
                     'serfs', 'soldiers')
        for pop_type in pop_types:
            with self.subTest(pop_type=pop_type):
                path = ROOT / 'TGC/poptypes' / f'{pop_type}.txt'
                document = parse_script(path.read_text(encoding='latin-1'), file=str(path))
                nodes = tuple(walk(document.nodes))
                self.assertFalse(any(node.key == 'has_country_flag' and
                                     node.value in ('totalitarian_government', 'central_bank_instituted')
                                     for node in nodes))
                modifiers = [node.value for node in nodes if node.key == 'has_country_modifier']
                self.assertEqual(modifiers.count('totalitarian_system'),
                                 2 if pop_type == 'aristocrats' else 3)
                self.assertEqual(modifiers.count('central_bank_established'),
                                 0 if pop_type == 'serfs' else 1)
        bank = decision('Political', 'institute_central_bank')
        modifier = section(section(bank, 'effect'), 'add_country_modifier')
        self.assertEqual(scalar(modifier, 'name'), 'central_bank_established')
        self.assertEqual(scalar(modifier, 'duration'), '-1')

    def test_reform_gates_use_the_active_country_history(self):
        nodes = tuple(walk(definitions('common/issues.txt')))
        unitary, = (node for node in nodes if node.key == 'unitary')
        alternative = section(section(unitary, 'allow'), 'OR')
        self.assertEqual(scalar(alternative, 'is_cultural_union'), 'no')
        self.assertEqual(scalar(alternative, 'has_country_flag'), 'french_content')
        civilizing, = (node for node in nodes if node.key == 'civilizing')
        allow = section(civilizing, 'allow')
        self.assertFalse(any(node.value == 'islamic_law' for node in walk(allow.children)))
        self.assertEqual(scalar(allow, 'colonial_nation'), 'yes')

    def test_reform_keeps_fort_and_gates_its_execution_package(self):
        reform, = (node for node in walk(definitions('common/issues.txt'))
                   if node.key == 'yes_military_constructions')
        execute = section(reform, 'on_execute')
        trigger = section(section(execute, 'trigger'), 'can_build_fort_in_capital')
        effect = section(execute, 'effect')
        fort = section(effect, 'build_fort_in_capital')
        for node in (trigger, fort):
            self.assertEqual(scalar(node, 'in_whole_capital_state'), 'no')
            self.assertEqual(scalar(node, 'limit_to_world_greatest_level'), 'yes')
        self.assertEqual(scalar(effect, 'treasury'), '-2000')
        self.assertEqual(scalar(effect, 'activate_technology'), 'post_napoleonic_thought')
