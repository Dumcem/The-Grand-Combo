"""Checks for reconciled producers and consumers in common event chains."""

import unittest

from test_upstream_task42 import decision, definitions, event, section
from test_upstream_task47 import option
from lib_1966_parser import scalar, walk


class OrdinaryReconciliationTests(unittest.TestCase):
    def test_world_fair_replaces_previous_host_before_setting_new_host(self):
        choice = option(event('WorldFairs', 30001), 'EVTOPTA30001')
        clear = section(choice, 'any_country')
        self.assertEqual(scalar(section(clear, 'limit'), 'has_country_flag'),
                         'held_last_world_fair')
        self.assertEqual(scalar(clear, 'clr_country_flag'), 'held_last_world_fair')
        self.assertEqual(scalar(choice, 'set_country_flag'), 'held_last_world_fair')
        self.assertLess(clear.start.line,
                        next(node.start.line for node in choice.children
                             if node.key == 'set_country_flag'))
        consumer = section(event('USAFlavor', 187760), 'trigger')
        self.assertEqual(scalar(consumer, 'has_country_flag'), 'held_last_world_fair')

    def test_gold_coast_treaty_checks_both_new_and_legacy_flags(self):
        treaty = decision('ENG', 'gold_coast_treaty')
        self.assertTrue(any(node.key == 'set_global_flag' and
                            node.value == 'gold_coast_treaty'
                            for node in walk(section(treaty, 'effect').children)))
        for definition in (treaty, decision('VOC', 'the_aceh_question')):
            flags = {node.key for node in walk(definition.children)
                     if node.value == 'gold_coast_treaty'}
            self.assertTrue({'has_country_flag', 'has_global_flag'} <= flags)

    def test_japanese_policy_and_mobilisation_use_distinct_modifiers(self):
        policy = decision('JAP', 'begin_line_of_advantage')
        effects = tuple(walk(section(policy, 'effect').children))
        self.assertTrue(any(node.key == 'name' and node.value == 'line_of_advantage'
                            for node in effects))
        triggered = {node.key for node in definitions('common/triggered_modifiers.txt')}
        self.assertIn('japanese_ai_mobilisation', triggered)
        self.assertNotIn('line_of_advantage', triggered)
