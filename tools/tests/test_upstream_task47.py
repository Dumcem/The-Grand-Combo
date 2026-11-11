"""Static regressions for the regional reconciliation."""

from collections import Counter
import re
import unittest

from test_upstream_task42 import ROOT, definitions, event, section
from lib_1966_parser import scalar, walk


def option(node, key):
    result, = (child for child in node.children
               if child.key == 'option' and scalar(child, 'name') == key)
    return result


class RegionalReconciliationTests(unittest.TestCase):
    def test_temperance_ids_and_localisation_are_unique(self):
        events = definitions('events/TemperanceLeague.txt')
        ids = [scalar(node, 'id') for node in events]
        self.assertEqual(ids, [str(number) for number in range(180, 192)])
        roots = [ROOT / 'TGC', ROOT / 'TGC_Timeline_1966']
        all_ids = Counter()
        keys = Counter()
        for root in roots:
            for path in (root / 'events').glob('*.txt'):
                all_ids.update(re.findall(rb'(?m)^\s*id\s*=\s*(\d+)[ \t]*(?:#.*)?\r?$',
                                          path.read_bytes()))
            for path in (root / 'localisation').glob('*.csv'):
                keys.update(line.partition(b';')[0] for line in path.read_bytes().splitlines())
        self.assertEqual(all_ids[b'100'], 0)
        self.assertEqual(keys[b'EVTOPTB110'], 0)
        self.assertEqual(keys[b'EVTOPTB15110'], 1)  # NationalistMovements has its own label.
        for node, event_id in zip(events, ids):
            with self.subTest(event=event_id):
                self.assertEqual(all_ids[event_id.encode()], 1)
                labels = [scalar(node, 'title'), scalar(node, 'desc')]
                labels += [scalar(child, 'name') for child in node.children if child.key == 'option']
                for label in labels:
                    self.assertEqual(keys[label.encode()], 1)

    def test_menu_checks_national_value_requirements_and_border_menu_returns(self):
        target = event('JANFlavor', 68)
        trigger = section(target, 'trigger')
        expected = [(node.key, node.value) for node in walk(trigger.children) if not node.is_group]
        choice = option(event('JANFlavor', 64), 'EVTOPTB64')
        self.assertFalse(any(node.key == 'country_event' for node in choice.children))
        conditional = section(choice, 'random_owned')
        limit = section(section(conditional, 'limit'), 'owner')
        observed = [(node.key, node.value) for node in walk(limit.children) if not node.is_group]
        self.assertEqual(observed, expected)
        self.assertEqual(scalar(section(conditional, 'owner'), 'country_event'), '68')
        back = option(event('JANFlavor', 67), 'EVTOPTD67')
        self.assertEqual(scalar(back, 'country_event'), '66')
        setup = option(event('JANFlavor', 63), 'EVTOPTC63')
        self.assertEqual([node.value for node in walk(setup.children)
                          if node.key == 'country_event'], ['63'])

    def test_tobago_options_have_distinct_localisation_and_destinations(self):
        purchase = event('RUSFlavor', 500224)
        localisation = (ROOT / 'TGC/localisation/00_events_0500000.csv').read_bytes().splitlines()
        for suffix, destination in (('A', 500225), ('B', 500226)):
            key = 'EVT500224OPT' + suffix
            with self.subTest(key=key):
                self.assertEqual(sum(line.startswith(key.encode() + b';') for line in localisation), 1)
                self.assertEqual(scalar(section(option(purchase, key), 'FROM'), 'country_event'),
                                 str(destination))
                self.assertEqual(scalar(event('RUSFlavor', destination), 'is_triggered_only'), 'yes')

    def test_partial_collapse_adds_aracaju_to_the_existing_pnb_transfer(self):
        for event_id, key in ((8170, 'EVTOPTB8170'), (8171, 'EVTOPTA8171')):
            with self.subTest(event=event_id):
                choice = option(event('BRZFlavor', event_id), key)
                transfer, = (node for node in choice.children if node.key == 'any_owned'
                             and scalar(node, 'secede_province') == 'PNB')
                selector = section(section(transfer, 'limit'), 'OR')
                self.assertEqual(scalar(transfer, 'add_core'), 'CEQ')
                self.assertEqual({node.value for node in selector.children if node.key == 'region'},
                                 {'BRZ_2429', 'BRZ_2428', 'BRZ_2432'})
                if event_id == 8170:
                    self.assertEqual(scalar(selector, 'province_id'), '2435')
                    self.assertEqual(scalar(selector, 'is_core'), 'PNB')
                else:
                    self.assertIsNone(scalar(selector, 'province_id'))

    def test_amazon_test_event_keeps_its_empty_province_checks(self):
        target = event('BRZFlavor', 8500)
        self.assertEqual(scalar(target, 'is_triggered_only'), 'yes')
        choice = option(target, 'EVTOPTA8403')
        for province in ('3413', '1979', '2401'):
            with self.subTest(province=province):
                transfers = (node for node in choice.children if node.key == 'random_owned'
                             and any(child.key == province for child in node.children))
                transfer, = transfers
                self.assertEqual(scalar(section(transfer, province), 'secede_province'), 'THIS')
                gate = section(section(transfer, 'limit'), province)
                self.assertEqual(scalar(gate, 'empty'), 'yes')
