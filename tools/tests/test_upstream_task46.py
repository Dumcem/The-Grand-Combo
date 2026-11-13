"""Static regressions for setup, reforms and POP conditions."""

import unittest

from test_upstream_task42 import ROOT, decision, definitions, evaluate, event, section
from test_upstream_task47 import option
from lib_1966_parser import parse_file, parse_script, scalar, walk


class SetupAndPopReconciliationTests(unittest.TestCase):
    def test_optional_billed_services_enable_the_gate_without_clearing_it_on_stop(self):
        apocalypse, = parse_file(
            'TGCApocalypse1836/decisions/InfectionModeDecisions.txt'
        ).definitions
        direct, = parse_file(
            'TGCDirectImmigration/decisions/01_Setup-DirectImmigration.txt'
        ).definitions
        for decisions, name, flag in (
            (apocalypse, 'ap_scouts', 'scouts_activated'),
            (direct, 'override_activate_immigration', 'direct_immigration'),
        ):
            effect = section(section(decisions, name), 'effect')
            self.assertEqual(scalar(effect, 'set_country_flag'), flag)
            self.assertEqual(scalar(effect, 'set_global_flag'), 'override_campaigns')
        stop_scouts = section(section(apocalypse, 'ap_scouts_turn_off'), 'effect')
        self.assertEqual(scalar(stop_scouts, 'clr_country_flag'), 'scouts_activated')
        self.assertIsNone(scalar(stop_scouts, 'clr_global_flag'))
        menu, *_ = parse_file('TGCDirectImmigration/events/DirectImmigrationEvents.txt').definitions
        stop_immigration = option(menu, 'EVTOPTE980000')
        self.assertEqual(scalar(stop_immigration, 'clr_country_flag'), 'direct_immigration')
        self.assertIsNone(scalar(stop_immigration, 'clr_global_flag'))

    def test_campaign_billing_reconciles_without_charging_twice(self):
        path = 'events/JANFlavor.txt'
        loader = ROOT / 'TGCScriptExtender' / path
        copies = (definitions(path), parse_script(loader.read_bytes().decode('latin-1')).definitions)
        colony = ('has_country_modifier', 'more_colonial_settlement')
        emigration = ('has_country_modifier', 'less_emigration')
        birthrate = ('has_country_modifier', 'birthrate_push_low')
        scouts = ('has_country_flag', 'scouts_activated')
        immigration = ('has_country_flag', 'direct_immigration')

        for events in copies:
            by_id = {scalar(node, 'id'): node for node in events if node.key == 'country_event'}
            monthly = section(by_id['52'], 'option')
            reschedule = section(monthly, 'country_event')
            self.assertEqual((scalar(reschedule, 'id'), scalar(reschedule, 'days')), ('52', '30'))
            billing_gate, = (node for node in monthly.children if node.key == 'any_country'
                             and scalar(node, 'set_global_flag') == 'override_campaigns')
            self.assertLess(
                next(i for i, node in enumerate(monthly.children)
                     if node.key == 'clr_global_flag' and node.value == 'override_campaigns'),
                monthly.children.index(billing_gate),
            )
            monthly_gate = section(billing_gate, 'limit')
            self.assertEqual(scalar(monthly_gate, 'exists'), 'yes')
            self.assertEqual(scalar(monthly_gate, 'ai'), 'no')
            self.assertFalse(any(node.key == 'add_tax_relative_income' for node in walk(monthly.children)))

            daily = section(by_id['53'], 'option')
            charge_block, = (node for node in daily.children if node.key == 'random_owned'
                             and any(child.key == 'has_global_flag' and child.value == 'override_campaigns'
                                     for child in walk(section(node, 'limit').children)))
            charges = {}
            for branch in (node for node in charge_block.children if node.key == 'any_country'):
                gate = section(branch, 'limit')
                self.assertEqual(scalar(gate, 'ai'), 'no')
                service, = (node for node in gate.children if node.key != 'ai')
                key = (service.key, service.value)
                self.assertNotIn(key, charges)
                charges[key] = tuple(float(node.value) for node in walk(branch.children)
                                     if node.key == 'add_tax_relative_income')
            self.assertCountEqual([(node.key, node.value) for node in section(monthly_gate, 'OR').children],
                                  charges)
            self.assertEqual(charges[immigration], (-0.02, -0.01))
            self.assertEqual(charges[scouts], (-0.3,))
            self.assertEqual(charges[colony], (-0.2,))
            self.assertEqual(charges[emigration], (-0.2,))
            activations = {
                scalar(node, 'name')
                for event_id in ('69', '70', '81')
                for block in walk(by_id[event_id].children)
                if any(child.key == 'set_global_flag' and child.value == 'override_campaigns'
                       for child in block.children)
                for node in block.children if node.key == 'add_country_modifier'
            }
            self.assertCountEqual(activations, [value for key, value in charges
                                               if key == 'has_country_modifier'])
            self.assertFalse(any(node.key == 'clr_global_flag' and node.value == 'override_campaigns'
                                 for event_id in ('69', '70', '81')
                                 for node in walk(by_id[event_id].children)))

            def tick(countries, flag):
                return [sum(sum(charges[service]) for service in services) if flag else 0
                        for services in countries]

            def reconcile(countries):
                return any(evaluate(monthly_gate.children, lambda node: (
                    (node.key, node.value) in services | {('ai', 'no'), ('exists', 'yes')}
                )) for services in countries)

            def reset(countries, event_id, label):
                effects = option(by_id[event_id], label).children
                removed = {('has_country_modifier', node.value) for node in effects
                           if node.key == 'remove_country_modifier'}
                self.assertFalse(any(node.key == 'clr_global_flag' for node in effects))
                return [countries[0] - removed, *countries[1:]]

            countries = reset([{birthrate, colony, emigration}], '81', 'EVTOPTD81')
            self.assertEqual(tick(countries, True), [-0.4])
            countries = reset([{colony}, {emigration}], '69', 'EVTOPTA69')
            self.assertEqual(tick(countries, True), [0, -0.2])
            self.assertEqual(tick(countries, False), [0, 0])
            self.assertEqual(tick(countries, reconcile(countries)), [0, -0.2])
            for service in (immigration, scouts):
                self.assertTrue(reconcile([{service}]))
                self.assertEqual(tick([{service}], reconcile([{service}])), [sum(charges[service])])
            self.assertEqual(tick([set()], True), [0])
            self.assertFalse(reconcile([set()]))

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

    def test_migration_campaign_choices_toggle_the_modifier_used_by_pops(self):
        path = 'common/pop_types.txt'
        direct = ROOT / 'TGCDirectImmigration' / path
        consumers = (definitions(path),
                     parse_script(direct.read_text(encoding='latin-1'), file=str(direct)).definitions)
        loader = ROOT / 'TGCScriptExtender/events/JANFlavor.txt'
        loader_events = parse_script(loader.read_text(encoding='latin-1'), file=str(loader)).definitions
        event_profiles = tuple(
            {scalar(node, 'id'): node for node in events if node.key == 'country_event'}
            for events in (definitions('events/JANFlavor.txt'), loader_events)
        )
        for section_name, name, label, direction in (
            ('colonialmigration_chance', 'more_colonial_settlement', 'EVTOPTA70', 1),
            ('emigration_chance', 'less_emigration', 'EVTOPTB70', -1),
        ):
            with self.subTest(campaign=name):
                for pop_sections in consumers:
                    migration, = (node for node in pop_sections if node.key == section_name)
                    consumer, = (node for node in migration.children if node.key == 'modifier'
                                 and any(item.value == name for item in walk(node.children)))
                    self.assertGreater(direction * float(scalar(consumer, 'factor')), 0)
                    self.assertEqual(scalar(section(consumer, 'country'), 'has_country_modifier'), name)
                for by_id in event_profiles:
                    event_nodes = tuple(walk(option(by_id['70'], label).children))
                    producer, = (node for node in event_nodes if node.key == 'add_country_modifier'
                                 and scalar(node, 'name') == name)
                    self.assertEqual(scalar(producer, 'duration'), '-1')
                    self.assertTrue(any(node.key == 'remove_country_modifier' and
                                        node.value == name for node in event_nodes))
                    reset = option(by_id['69'], 'EVTOPTA69')
                    self.assertTrue(any(node.key == 'remove_country_modifier' and
                                        node.value == name for node in reset.children))
                    updater = tuple(walk(by_id['53'].children))
                    billing, = (node for node in updater if node.key == 'any_country'
                                and any(child.key == 'limit' and
                                        scalar(child, 'has_country_modifier') == name
                                        for child in node.children))
                    self.assertEqual(scalar(section(billing, 'limit'), 'ai'), 'no')
                    charge, = (node for node in walk(billing.children)
                               if node.key == 'add_tax_relative_income')
                    self.assertLess(float(charge.value), 0)

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

    def test_each_yugoslav_puppet_formation_exclusion_blocks_the_decision(self):
        potential = section(decision('YUG', 'create_yugoslavia'), 'potential')
        gates = tuple(node for node in potential.children if node.key == 'NOT')
        blocked = (
            ('exists', 'YUG'),
            ('is_culture_group', 'south_slavic'),
            ('has_global_flag', 'yugoslavia_formed'),
            ('has_global_flag', 'disable_unite_as_puppet'),
            *(('tag', tag) for tag in ('TUR', 'AUS', 'KUK', 'DNB', 'HUN', 'GCF', 'GER')),
        )
        self.assertTrue(evaluate(gates, lambda node: False))
        for key, value in blocked:
            with self.subTest(key=key, value=value):
                self.assertFalse(evaluate(gates, lambda node: (node.key, node.value) == (key, value)))

    def test_each_military_coup_exclusion_blocks_the_event(self):
        trigger = section(event('Military', 152009873), 'trigger')
        gates = tuple(node for node in trigger.children if node.key == 'NOT')
        blocked = (
            ('has_country_modifier', 'national_confusion'),
            ('has_country_modifier', 'military_strife'),
            ('continent', 'europe'),
            ('is_culture_group', 'american_cultures'),
            ('is_culture_group', 'neo_european_cultures'),
            ('literacy', '0.50'),
        )
        self.assertTrue(evaluate(gates, lambda node: False))
        for key, value in blocked:
            with self.subTest(key=key, value=value):
                def predicate(node):
                    if node.key == 'capital_scope':
                        return (key, value) == ('continent', scalar(node, 'continent'))
                    return (node.key, node.value) == (key, value)

                self.assertFalse(evaluate(gates, predicate))

    def test_military_reform_executes_without_a_fort_requirement(self):
        reform, = (node for node in walk(definitions('common/issues.txt'))
                   if node.key == 'yes_military_constructions')
        execute = section(reform, 'on_execute')
        effect = section(execute, 'effect')
        names = {node.key for node in walk(execute.children)}
        self.assertNotIn('can_build_fort_in_capital', names)
        self.assertNotIn('build_fort_in_capital', names)
        self.assertEqual(scalar(effect, 'treasury'), '-2000')
        self.assertEqual(scalar(effect, 'activate_technology'), 'post_napoleonic_thought')
