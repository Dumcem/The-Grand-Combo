"""Static contracts for the upstream-first reconciliation."""

from collections import defaultdict
import re
import unittest

from test_upstream_task42 import ROOT, decision, definitions, evaluate, section, event
from test_upstream_task47 import option
from lib_1966_parser import member, parse_script, scalar, walk
from lib_1966_runtime import compose_runtime


NATIVE_MENU_ID = re.compile(rb'(?m)^\s*id\s*=\s*100[ \t]*(?:#.*)?\r?$')


def shape(nodes):
    return [(node.key, shape(node.children) if node.is_group else node.value) for node in nodes]


class UpstreamFirstTests(unittest.TestCase):
    def test_officer_notifications_name_the_officer_and_match_the_effect(self):
        names = (
            'Kiwi', 'Wyrm', 'Koba', 'Pixelaes', 'Gelre', "Ryan 'Rennes' Gosling",
            'Napoleon I', 'Helmuth von Moltke', 'Albrecht von Roon', 'Josef Radetzky',
            'Winfield Scott', 'Ulysses S. Grant', 'William Tecumseh Sherman', 'John', 'Jane',
        )
        officers = dict(enumerate(names, start=10000106))
        keys = {f'EVT{kind}{event_id}'.encode() for event_id in officers for kind in ('NAME', 'DESC')}
        layers = {}
        for root in ('TGC', 'TGC_Timeline_1966', 'TGCScriptExtender'):
            rows = defaultdict(list)
            for path in (ROOT / root / 'localisation').glob('*.csv'):
                for line in path.read_bytes().splitlines():
                    key, _, fields = line.partition(b';')
                    if key in keys:
                        rows[key].append(fields.partition(b';')[0].decode('latin-1'))
            layers[root] = rows

        for event_id, name in officers.items():
            notification = event('Military', event_id)
            title_key, desc_key = f'EVTNAME{event_id}', f'EVTDESC{event_id}'
            admiral = event_id in (10000111, 10000120)
            rank, branch = ('admiral', 'navy') if admiral else ('general', 'army')
            with self.subTest(event=event_id):
                self.assertEqual(scalar(notification, 'title'), title_key)
                self.assertEqual(scalar(notification, 'desc'), desc_key)
                officer, = (node for node in walk(notification.children)
                            if node.key in ('define_general', 'define_admiral'))
                self.assertEqual(officer.key, f'define_{rank}')
                self.assertIn(name, scalar(officer, 'name', required=True))
            for profile, overlay in (('core', None), ('core+1966', 'TGC_Timeline_1966'),
                                     ('core+extender', 'TGCScriptExtender')):
                with self.subTest(event=event_id, profile=profile):
                    expected = {
                        title_key: f'A New {rank.title()}',
                        desc_key: f'A new {rank} has joined our {branch}: {name}.',
                    }
                    for key, value in expected.items():
                        key = key.encode()
                        matches = layers['TGC'][key] + (layers[overlay][key] if overlay else [])
                        self.assertEqual(matches, [value])

    def test_ruling_party_support_threshold_after_rebel_victory(self):
        # Upstream 81f56b379 sets these six POP filters to 0.5.
        rebels = ('reactionary', 'fascist', 'communist', 'carlist', 'christino', 'socialist')
        path = 'common/rebel_types.txt'
        for timeline in (None, 'TGC_Timeline_1966'):
            source = compose_runtime(ROOT, timeline_root=timeline).require(path)
            data = (ROOT / source).read_bytes().decode('latin-1')
            rebel_definitions = parse_script(data, file=source).definitions
            for name in rebels:
                with self.subTest(profile=timeline or 'core', rebels=name):
                    definition, = (node for node in rebel_definitions if node.key == f'{name}_rebels')
                    effect = section(definition, 'demands_enforced_effect')
                    threshold, = (
                        member(section(pop, 'limit'), 'agree_with_ruling_party', required=True)
                        for pop in effect.children
                        if pop.key == 'any_pop' and scalar(pop, 'militancy') == '-4'
                    )
                    self.assertEqual((threshold.operator, threshold.value), ('=', '0.5'))

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
            menu_ids = sum(
                len(NATIVE_MENU_ID.findall((ROOT / source.file).read_bytes()))
                for path, source in inventory.selected.items()
                if path.startswith('events/')
            )
            self.assertEqual(menu_ids, 1)
        root = ROOT / 'TGC'
        self.assertFalse((ROOT / 'TGC_Timeline_1966/map/region.txt').exists())
        self.assertIn(b'cant_do_because = {}', (root / 'map/region.txt').read_bytes())
        picture = root / 'gfx/pictures/events/native_americans.dds'
        self.assertEqual(picture.read_bytes()[:4], b'DDS ')
        labels = (root / 'localisation/00_events-utility.csv').read_bytes().splitlines()
        for key in ('EVTNAME100', 'EVTDESC100', *(f'EVTOPT{letter}100' for letter in 'ABCD')):
            self.assertEqual(sum(line.startswith(key.encode() + b';') for line in labels), 1)

    def test_anatolia_greek_core_and_cession_sets(self):
        regions = {
            'TUR_863': {862, 863, 864, 865, 866},
            'TUR_869': {867, 869, 871, 872},
            'TUR_873': {870, 873, 874, 875, 895},
            'TUR_876': {868, 876, 877, 878, 880, 881},
            'TUR_860': {828, 858, 859, 3387},
            'TUR_861': {860, 861},
        }
        mapped = {node.key: {int(p.value) for p in node.children}
                  for node in definitions('map/region.txt') if node.key in regions}
        self.assertEqual(mapped, regions)
        anatolia = set.union(*(regions[key] for key in ('TUR_863', 'TUR_869', 'TUR_873', 'TUR_876')))
        straits = regions['TUR_860'] | regions['TUR_861']
        excluded = straits | {862, 865, 866}
        playable = {int(line.split(b';', 1)[0]) for line in
                    (ROOT / 'TGC/map/definition.csv').read_bytes().splitlines()[1:]
                    if line.split(b';', 1)[0].isdigit()}
        self.assertLessEqual(anatolia | straits | {805, 855, 883, 994}, playable)

        popup = event('RUSFlavor', 500291)
        gates = section(popup, 'trigger')
        self.assertEqual({int(node.key) for node in gates.children if node.key.isdecimal()},
                         {860, 873, 876})
        for letter, core_area, retained in (('B', anatolia, excluded),
                                             ('C', anatolia | straits, set())):
            choice = option(popup, f'EVTOPT{letter}500291')
            grant, transfer = (node for node in choice.children if node.key == 'any_owned')
            self.assertEqual(scalar(grant, 'add_core'), 'GRE')
            self.assertEqual(scalar(transfer, 'secede_province'), 'GRE')
            for russian, owned, previous in (
                (True, anatolia | straits | {805, 855, 883, 994}, {805}),
                (True, {860, 873, 876, 862, 865, 866, 859, 805, 855, 883, 994},
                 {805, 855, 859, 860, 862, 865, 866, 883, 869}),
                (True, {860, 873, 876}, set()),
                (True, {873, 876, 994}, {860}),
                (False, {860, 873, 876, 855}, {855}),
            ):
                def select(scope, cores):
                    def matches(node, province):
                        if node.key == 'region':
                            return province in mapped[node.value]
                        if node.key == 'province_id':
                            return province == int(node.value)
                        if (node.key, node.value) == ('owned_by', 'RUS'):
                            return russian and province in owned
                        if (node.key, node.value) == ('is_core', 'GRE'):
                            return province in cores
                        raise AssertionError(node.key)

                    limit = section(scope, 'limit')
                    return {p for p in owned if evaluate(limit.children, lambda node: matches(node, p))}

                with self.subTest(option=letter, russian=russian, owned=sorted(owned), previous=sorted(previous)):
                    russian_land = owned if russian else set()
                    granted = select(grant, previous)
                    self.assertEqual(granted - previous, (russian_land & core_area) - previous)
                    self.assertEqual(select(transfer, previous | granted),
                                     (russian_land & (previous | core_area)) - retained)

    def test_anatolia_greek_vassal_and_capital_effects_follow_cession(self):
        popup = event('RUSFlavor', 500291)
        for letter, capital in (('B', None), ('C', '860')):
            choice = option(popup, f'EVTOPT{letter}500291')
            grant, transfer = (node for node in choice.children if node.key == 'any_owned')
            relation = section(choice, 'relation')
            selection = section(choice, 'random_country')
            self.assertLess(grant.start.offset, transfer.start.offset)
            self.assertLess(transfer.start.offset, relation.start.offset)
            self.assertLess(relation.start.offset, selection.start.offset)
            self.assertEqual(scalar(relation, 'who'), 'GRE')
            self.assertEqual(shape(section(selection, 'limit').children),
                             [('THIS', [('tag', 'RUS')]), ('tag', 'GRE'),
                              ('ai', 'yes'), ('exists', 'yes')])
            self.assertIsNone(scalar(selection, 'capital'))
            overlord = section(selection, 'RUS')
            self.assertEqual(scalar(overlord, 'create_vassal'), 'GRE')
            if capital:
                owned = section(selection, 'any_owned')
                self.assertEqual(shape(section(owned, 'limit').children), [('province_id', capital)])
                self.assertEqual(scalar(section(owned, 'owner'), 'capital'), capital)
                self.assertLess(overlord.start.offset, owned.start.offset)

    def test_direct_immigration_cleanup_protects_other_human_countries(self):
        immigration = ROOT / 'TGCDirectImmigration'
        setup, = parse_script((immigration / 'decisions/01_Setup-DirectImmigration.txt')
                              .read_bytes().decode('latin-1')).definitions
        activate = section(section(setup, 'override_activate_immigration'), 'effect')
        events = parse_script((immigration / 'events/DirectImmigrationEvents.txt')
                              .read_bytes().decode('latin-1')).definitions
        menu, = (n for n in events if scalar(n, 'id') == '980000')
        stop = option(menu, 'EVTOPTE980000')
        for action in (activate, stop):
            cleanup = section(action, 'any_country')
            self.assertEqual(shape(section(cleanup, 'limit').children), [('exists', 'yes'), ('ai', 'yes')])
            self.assertEqual(shape(section(cleanup, 'any_owned').children), shape(section(stop, 'any_owned').children))
            self.assertIsNone(member(action, 'all_land_provinces'))

    def test_latin_union_converts_owned_cores_before_extinct_tag_cleanup(self):
        reform = option(event('FRAFlavourExtra', 10417), 'EVTOPTC10417')
        scopes = [node for node in reform.children if node.key == 'random_owned']
        for tag in ('SIC', 'PAP'):
            with self.subTest(tag=tag):
                early, = (node for node in scopes if member(section(node, 'limit'), tag))
                later, = (node for node in scopes if scalar(section(node, 'limit'), 'is_core') == tag)
                self.assertLess(scopes.index(early), scopes.index(later))
                self.assertEqual(shape(early.children), [
                    ('limit', [(tag, [('exists', 'no')])]),
                    ('owner', [('any_owned', [
                        ('limit', [('is_core', tag)]),
                        ('add_core', 'THIS'),
                        ('remove_core', tag),
                    ])]),
                    (tag, [('all_core', [('remove_core', tag)])]),
                ])
                self.assertEqual(shape([section(later, 'owner')]), shape([section(early, 'owner')]))

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
