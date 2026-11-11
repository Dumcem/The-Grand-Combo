"""Static checks for the territorial settlements reconciled in Task 43."""

import unittest

from test_upstream_task42 import ROOT, decision, definitions, evaluate, event, section
from lib_1966_parser import member, scalar, walk
from lib_1966_runtime import compose_runtime


class EuropeanDiplomacyTests(unittest.TestCase):
    def test_lowlands_settlement_uses_only_live_parties_and_dutch_batavia(self):
        settlement = event('GEF Events', 9111117)
        net = section(section(settlement, 'trigger'), 'NET')
        self.assertEqual(scalar(net, 'exists'), 'yes')
        self.assertEqual(scalar(net, 'truce_with'), 'GER')
        self.assertEqual(scalar(net, 'is_disarmed'), 'yes')
        option = section(settlement, 'option')
        europe, colonies, england = (node for node in walk(option.children)
                                      if member(node, 'annex_to') is not None)
        for scope, recipient, countries in (
            (europe, 'THIS', {'BEL', 'LUX', 'LBG'}),
            (colonies, 'NET', {'JAV', 'BAL', 'DJA', 'RIA', 'SAK', 'ATJ', 'BTN', 'SLW',
                               'LUW', 'PIT', 'KTI', 'BGN', 'SUL', 'KLM', 'SLA', 'STG',
                               'SBS', 'PTK', 'MAL'}),
        ):
            self.assertEqual(scalar(scope, 'annex_to'), recipient)
            limit = section(scope, 'limit')
            for country in countries | {'NET', 'ENG'}:
                for alive in (False, True):
                    self.assertEqual(evaluate(limit.children, lambda term:
                                              alive if term.key == 'exists' else term.value == country),
                                     alive and country in countries)
        colony_holder, migration, handover = (node for node in option.children
                                               if node.key == 'random_country')
        for scope in (colony_holder, migration, handover):
            limit = section(scope, 'limit')
            self.assertEqual(scalar(limit, 'tag'), 'NET')
            self.assertEqual(scalar(limit, 'exists'), 'yes')
        self.assertEqual(scalar(section(migration, 'limit'), 'owns'), '1413')
        self.assertEqual({node.value for node in walk(migration.children) if node.key == 'move_pop'},
                         {'1413'})
        self.assertEqual(scalar(england, 'annex_to'), 'ENG')
        self.assertEqual(scalar(section(section(handover, 'limit'), 'ENG'), 'exists'), 'yes')
        self.assertLess(colony_holder.start.offset, migration.start.offset)
        self.assertLess(migration.start.offset, handover.start.offset)

    def test_london_offers_keep_the_net_goal_in_both_wars(self):
        for sender, name, event_id in (
            ('Germany', 'dutch_prussian_alliance', 36725),
            ('FranceExtra', 'dutch_french_alliance', 36727),
        ):
            with self.subTest(event=event_id):
                offer = decision(sender, name)
                dispatch = section(section(offer, 'effect'), 'NET')
                self.assertEqual(scalar(dispatch, 'country_event'), str(event_id))
                treaty = event('LondonTreaty', event_id)
                accept, refuse = (node for node in treaty.children if node.key == 'option')
                war = section(section(accept, 'FROM'), 'war')
                self.assertEqual(scalar(war, 'target'), 'BEL')
                attacker = section(war, 'attacker_goal')
                self.assertEqual((scalar(attacker, 'casus_belli'), scalar(attacker, 'country')),
                                 ('liberate_country', 'NET'))
                self.assertEqual(scalar(section(war, 'defender_goal'), 'casus_belli'), 'humiliate')
                self.assertFalse(any(node.key == 'war' for node in walk(refuse.children)))
        cb, = (node for node in definitions('common/cb_types.txt') if node.key == 'liberate_country')
        self.assertEqual(scalar(cb, 'all_allowed_states'), 'yes')
        self.assertEqual(scalar(cb, 'po_transfer_provinces'), 'yes')
        states = section(section(cb, 'allowed_states'), 'any_owned_province')
        self.assertEqual(scalar(states, 'is_core'), 'FROM')

    def test_berlin_refusal_and_ottoman_countermove_read_the_producers(self):
        congress = event('BerlinCongress', 90060)
        _, refuse = (node for node in congress.children if node.key == 'option')
        refusal_flag = scalar(refuse, 'set_country_flag')
        blockers, = (node for node in section(congress, 'trigger').children if node.key == 'NOT'
                     and any(term.key == 'tag' for term in node.children))
        for refused in (False, True):
            self.assertEqual(evaluate((blockers,), lambda term:
                                      term.key == 'has_country_flag' and term.value == refusal_flag and refused),
                             not refused)
        russian_escalation = section(decision('RUS', 'eastern_crisis_dismantle_ottomans'), 'effect')
        russian_flag = scalar(russian_escalation, 'set_country_flag')
        ottoman = decision('RUS', 'kick_russians_out_oe')
        gate = section(section(ottoman, 'potential'), 'RUS')
        for russian, turkish in ((True, False), (False, True), (False, False)):
            flags = {'RUS': {russian_flag} if russian else set(),
                     'TUR': {russian_flag} if turkish else set()}
            self.assertEqual(evaluate(gate.children, lambda term: term.value in flags[gate.key]),
                             russian)

    def test_anatolia_scope_and_undefined_cb_order_entries(self):
        anatolia = event('RUSFlavor', 500291)
        option, = (node for node in anatolia.children if node.key == 'option'
                   and scalar(node, 'name') == 'EVTOPTC500291')
        transfer, = (node for node in option.children if node.key == 'any_owned'
                     and scalar(node, 'secede_province') == 'GRE')
        self.assertEqual(scalar(section(transfer, 'limit'), 'is_core'), 'GRE')
        cbs = definitions('common/cb_types.txt')
        order, = (node for node in cbs if node.key == 'peace_order')
        keys = {node.value for node in order.children}
        self.assertTrue({'dismantle_cb_add', 'claim_holy_land'} <= keys)
        self.assertFalse({'dismantle_cb_add_new', 'reclaim_the_empire'} & keys)

    def test_both_profiles_inherit_the_reconciled_scripts(self):
        for timeline in (None, 'TGC_Timeline_1966'):
            inventory = compose_runtime(ROOT, 'TGC', timeline)
            for path in ('common/cb_types.txt', 'decisions/ENG.txt', 'decisions/RUS.txt',
                         'events/GEF Events.txt', 'events/LondonTreaty.txt',
                         'events/BerlinCongress.txt', 'events/RUSFlavor.txt'):
                self.assertEqual(inventory.require(path), f'TGC/{path}')
        self.assertFalse((ROOT / 'TGC_Timeline_1966/localisation/00_decisions.csv').exists())
