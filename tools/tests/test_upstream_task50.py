"""Regression contracts for the Rotterdam settlement in both profiles."""

import unittest

from test_upstream_task42 import ROOT, decision, evaluate, section
from test_upstream_task49 import shape
from lib_1966_parser import scalar, walk
from lib_1966_runtime import compose_runtime


class RotterdamTests(unittest.TestCase):
    def setUp(self):
        self.treaty = decision('GEF', 'treaty_of_rotterdam')
        self.eligible = section(section(self.treaty, 'allow'), 'any_country')
        self.loser = section(section(self.treaty, 'effect'), 'random_country')

    def qualifies(self, tag, *, exists=True, at_war=True, exhaustion):
        def predicate(node):
            if node.key == 'war_exhaustion':
                return exhaustion >= int(node.value)
            return node.value == {'exists': 'yes' if exists else 'no',
                                  'war_with': 'THIS' if at_war else None,
                                  'tag': tag}[node.key]

        return evaluate(self.eligible.children, predicate)

    def test_same_belligerent_must_exist_be_at_war_and_meet_its_own_threshold(self):
        self.assertEqual(shape(self.eligible.children), shape(section(self.loser, 'limit').children))
        for tag, threshold in [('PRU', 99), ('NGF', 95), ('GER', 90), ('GCF', 90)]:
            with self.subTest(tag=tag):
                self.assertFalse(self.qualifies(tag, exhaustion=threshold - 1))
                self.assertTrue(self.qualifies(tag, exhaustion=threshold))
                self.assertFalse(self.qualifies(tag, exhaustion=100, at_war=False))
                self.assertFalse(self.qualifies(tag, exhaustion=100, exists=False))
        self.assertFalse(self.qualifies('FRA', exhaustion=100))

    def test_peace_targets_only_the_selected_belligerent(self):
        # The four province witnesses run from the single selected country.
        # The peace call targets its owner from NET's scope.
        peace = [node for node in self.loser.children if node.key == 'random_owned']
        observed = [(scalar(section(node, 'limit'), 'owned_by'),
                     scalar(section(node, 'NET'), 'end_war')) for node in peace]
        self.assertCountEqual(observed, [(tag, tag) for tag in ('PRU', 'NGF', 'GER', 'GCF')])
        effects = [node for node in walk(section(self.treaty, 'effect').children) if node.key == 'end_war']
        self.assertCountEqual([node.value for node in effects], [tag for tag, _ in observed])

    def test_transfers_require_ownership_and_claims_only_change_on_dutch_land(self):
        cessions = section(self.loser, 'any_owned')
        self.assertEqual(scalar(cessions, 'secede_province'), 'THIS')
        limit = section(section(cessions, 'limit'), 'OR')
        target_ids = {node.value for node in limit.children if node.key == 'province_id'}
        self.assertEqual(target_ids, {'563', '1743'})
        owners = {'563': 'GER', '1743': 'PRU', '573': 'FRA'}
        self.assertEqual({p for p in target_ids if owners[p] == 'GER'}, {'563'})
        owners['1743'] = 'NET'
        self.assertEqual({p for p in target_ids if owners[p] == 'GER'}, {'563'})
        net = section(self.loser, 'NET')
        region = section(net, 'any_owned')
        self.assertEqual(scalar(section(region, 'limit'), 'region'), 'PRU_575')
        self.assertEqual(scalar(region, 'add_core'), 'NET')
        self.assertCountEqual([node.value for node in region.children if node.key == 'remove_core'],
                              ['GER', 'PRU', 'NGF', 'GCF', 'RHI', 'LUX', 'OLD'])
        release, = (node for node in net.children if node.key == 'random_owned'
                    and scalar(section(node, 'limit'), 'province_id') == '573')
        self.assertEqual(shape(section(release, 'limit').children), [
            ('province_id', '573'), ('owner', [('NOT', [('exists', 'SAA')])]),
        ])
        self.assertEqual(scalar(section(release, 'owner'), 'release_vassal'), 'SAA')
        self.assertEqual(sum(node.key == 'secede_province' for node in walk(self.treaty.children)), 1)

    def test_upstream_land_requirements_and_once_only_guard_apply_in_both_profiles(self):
        potential = section(self.treaty, 'potential')
        self.assertCountEqual([node.value for node in potential.children if node.key == 'owns'], ['397', '575'])
        self.assertIn(('has_global_flag', 'treaty_of_rotterdam'), shape(section(potential, 'NOT').children))
        self.assertEqual(scalar(section(self.loser, 'NET'), 'set_global_flag'), 'treaty_of_rotterdam')
        for timeline in (None, 'TGC_Timeline_1966'):
            self.assertEqual(compose_runtime(ROOT, 'TGC', timeline).require('decisions/GEF.txt'),
                             'TGC/decisions/GEF.txt')
