"""Regression checks for archaeological permissions and discovery."""

import unittest

from test_upstream_task42 import decision, event, section
from lib_1966_parser import scalar, walk


class ExcavationPermissionTests(unittest.TestCase):
    def test_diplomatic_requests_reach_each_site_owner_and_return_to_requester(self):
        sites = (
            ('mesopotamian', '926', 201010, 201011, 201012),
            ('yinxu', '1515', 201090, 201091, 201092),
        )
        for site, province, request, grant, refusal in sites:
            with self.subTest(site=site):
                name = f'{site}_excavations'
                effect = section(decision('Archaeology', name), 'effect')
                owner = section(section(effect, province), 'owner')
                self.assertEqual(scalar(owner, 'country_event'), str(request))

                popup = event('Archaeology', request)
                self.assertEqual(scalar(popup, 'is_triggered_only'), 'yes')
                choices = [node for node in popup.children if node.key == 'option']
                self.assertEqual([scalar(section(choice, 'FROM'), 'country_event')
                                  for choice in choices], [str(grant), str(refusal)])

                granted = section(event('Archaeology', grant), 'option')
                self.assertEqual(scalar(section(granted, 'add_country_modifier'), 'name'), name)
                refused = section(event('Archaeology', refusal), 'option')
                self.assertEqual(scalar(refused, 'set_country_flag'), f'{site}_refused')

    def test_indus_decisions_use_the_province_of_harappa(self):
        diplomatic = decision('Archaeology', 'indus_excavations')
        forced = decision('Archaeology', 'forced_indus_excavations')
        scope_groups = (
            section(section(diplomatic, 'potential'), 'NOT'),
            section(section(forced, 'potential'), 'OR'),
            section(section(forced, 'allow'), 'OR'),
        )
        for group in scope_groups:
            self.assertEqual(scalar(group, 'owns'), '1227')
            owner = section(section(group, '1227'), 'owner')
            self.assertEqual(scalar(owner, 'in_sphere'), 'THIS')
        owner = section(section(section(diplomatic, 'effect'), '1227'), 'owner')
        self.assertEqual(scalar(owner, 'country_event'), '201080')
        modifier = section(section(forced, 'effect'), 'add_country_modifier')
        self.assertEqual(scalar(modifier, 'name'), 'indus_excavations')

    def test_indus_pending_options_do_not_reopen_completed_excavations(self):
        request = event('Archaeology', 201080)
        grant = section(event('Archaeology', 201081), 'option')
        refused = section(event('Archaeology', 201082), 'option')
        options = [node for node in request.children if node.key == 'option']
        conditionals = [section(option, 'random_owned') for option in [*options, grant]]
        for conditional in conditionals:
            self.assertEqual(scalar(section(section(conditional, 'limit'), 'NOT'),
                                    'has_global_flag'), 'harappa_found')
        accept, decline, response = [section(conditional, 'owner') for conditional in conditionals]
        self.assertEqual(scalar(section(accept, 'FROM'), 'country_event'), '201081')
        self.assertEqual(scalar(section(decline, 'FROM'), 'country_event'), '201082')
        self.assertEqual(scalar(accept, 'money'), '15000')
        self.assertEqual(scalar(grant, 'money'), '-15000')
        self.assertEqual(scalar(refused, 'set_country_flag'), 'indus_refused')
        self.assertEqual(scalar(section(response, 'add_country_modifier'), 'name'),
                         'indus_excavations')
        for option, conditional in ((options[0], accept), (grant, response)):
            self.assertIsNone(scalar(option, 'set_global_flag'))
            self.assertEqual(scalar(conditional, 'set_global_flag'), 'indus_excavations_rights')

        finale = event('Archaeology', 201086)
        self.assertEqual(scalar(finale, 'fire_only_once'), 'yes')
        discovery = section(finale, 'option')
        self.assertEqual(scalar(discovery, 'set_global_flag'), 'harappa_found')
        self.assertEqual(scalar(discovery, 'clr_global_flag'), 'indus_excavations_rights')
        self.assertEqual(scalar(section(discovery, 'any_country'), 'remove_country_modifier'),
                         'indus_excavations')
        self.assertEqual(scalar(discovery, 'remove_country_modifier'), 'indus_excavations')

    def test_yinxu_permission_and_discovery_use_distinct_flags(self):
        for name in ('yinxu_excavations', 'forced_yinxu_excavations'):
            with self.subTest(decision=name):
                potential = section(decision('Archaeology', name), 'potential')
                self.assertIn('oracle_bones', [
                    scalar(node, 'has_global_flag') for node in potential.children
                    if node.key == 'NOT'
                ])
                self.assertNotIn('oraclebones_found', [
                    node.value for node in walk(potential.children)
                    if node.key == 'has_global_flag'
                ])

        request = event('Archaeology', 201090)
        accepted = next(node for node in request.children if scalar(node, 'name') == 'EVTOPTA201090')
        self.assertEqual(scalar(accepted, 'set_global_flag'), 'yinxu_excavations_rights')

        granted = section(event('Archaeology', 201091), 'option')
        self.assertIsNone(scalar(granted, 'set_global_flag'))
        finale = event('Archaeology', 201096)
        self.assertEqual(scalar(section(section(finale, 'trigger'), 'NOT'), 'has_global_flag'),
                         'oracle_bones')
        discovery = section(finale, 'option')
        self.assertEqual(scalar(discovery, 'set_global_flag'), 'oracle_bones')
        self.assertEqual(scalar(discovery, 'clr_global_flag'), 'yinxu_excavations_rights')
