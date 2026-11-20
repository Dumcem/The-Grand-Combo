"""Regression checks for the Yinxu excavation decisions."""

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
