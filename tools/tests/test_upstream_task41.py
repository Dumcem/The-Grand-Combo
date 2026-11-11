"""Exercise the changed event gates and transitions from the parsed scripts."""

from itertools import product
import unittest

from test_1966_applied import ROOT
from lib_1966_parser import member, parse_script, read_text, scalar, walk
from lib_1966_runtime import compose_runtime


def event(path, event_id):
    source = str(ROOT / path)
    document = parse_script(read_text(source, encoding='cp1252'), file=source)
    matches = [
        node for node in document.definitions
        if node.key == 'country_event' and scalar(node, 'id') == str(event_id)
    ]
    result, = matches
    return result


def conditions(nodes, tag, countries, global_flags=(), year=1847):
    """Evaluate only the predicate subset used by the gates under test."""
    country = countries.get(tag, {})
    for node in nodes:
        key, value = node.key, node.value
        if key in ('OR', 'NOT'):
            results = [conditions((child,), tag, countries, global_flags, year)
                       for child in node.children]
            passed = any(results) if key == 'OR' else not any(results)
        elif key in ('SWI', 'AUS', 'FRA', 'MEX'):
            passed = conditions(node.children, key, countries, global_flags, year)
        elif key == 'tag':
            passed = tag == value
        elif key == 'year':
            passed = year >= int(value)
        elif key == 'exists':
            passed = (tag in countries) == (value == 'yes')
        elif key == 'has_country_flag':
            passed = value in country.get('flags', ())
        elif key == 'has_global_flag':
            passed = value in global_flags
        elif key in ('war', 'is_vassal'):
            passed = country.get(key, 'no') == value
        elif key in ('ruling_party_ideology', 'owns', 'truce_with'):
            passed = country.get(key) == value
        else:
            raise AssertionError(f'Unmodelled trigger {key}')
        if not passed:
            return False
    return True


class UpstreamEventTests(unittest.TestCase):
    def test_both_profiles_inherit_the_event_files_and_localisation(self):
        for timeline in (None, 'TGC_Timeline_1966'):
            inventory = compose_runtime(ROOT, 'TGC', timeline)
            for name in ('SWIFlavor', 'MEXFlavor', 'USA_Minors'):
                path = f'events/{name}.txt'
                self.assertEqual(inventory.require(path), f'TGC/{path}')
        path = 'localisation/00_events_0090000.csv'
        self.assertFalse((ROOT / 'TGC_Timeline_1966' / path).exists())
        self.assertNotIn('replace_path', (ROOT / 'TGC_Timeline_1966.mod').read_text())
        invitation = event('TGC/events/SWIFlavor.txt', 99797)
        options = [node for node in invitation.children if node.key == 'option']
        keys = [scalar(invitation, 'title'), scalar(invitation, 'desc')]
        keys.extend(scalar(option, 'name') for option in options)
        loc = (ROOT / 'TGC' / path).read_bytes().splitlines()
        for key in keys:
            self.assertEqual(sum(line.startswith(key.encode() + b';') for line in loc), 1)

    def test_sonderbund_independent_invitations_and_responses(self):
        path = 'TGC/events/SWIFlavor.txt'
        invitation, war = (event(path, event_id) for event_id in (99797, 99800))
        self.assertIsNone(member(invitation, 'fire_only_once'))
        self.assertEqual(scalar(war, 'fire_only_once'), 'yes')
        self.assertEqual(scalar(member(invitation, 'mean_time_to_happen'), 'months'), '1')
        self.assertEqual(scalar(member(war, 'mean_time_to_happen'), 'months'), '5')
        self.assertFalse(any(node.key == 'country_event' for node in walk(invitation.children)))
        invite_gate, war_gate = (member(node, 'trigger').children for node in (invitation, war))
        immediate = member(invitation, 'immediate')
        support, refuse = (node for node in invitation.children if node.key == 'option')
        war_options = [node for node in war.children if node.key == 'option']
        self.assertEqual([scalar(member(option, 'ai_chance'), 'factor')
                          for option in (support, refuse)], ['5', '95'])
        self.assertEqual([scalar(member(option, 'ai_chance'), 'factor')
                          for option in war_options], ['1', '0'])
        relation = member(support, 'relation')
        self.assertEqual((scalar(relation, 'who'), scalar(relation, 'value')), ('ENG', '-50'))
        self.assertIsNone(member(refuse, 'relation'))

        # None means absent, not an existing country that declined.
        for austria, france in product((None, support, refuse), repeat=2):
            for first, second in (('AUS', 'FRA'), ('FRA', 'AUS')):
                with self.subTest(austria=austria is not None, france=france is not None, first=first):
                    replies = {'AUS': austria, 'FRA': france}
                    countries = {'SWI': {'ruling_party_ideology': 'liberal'}}
                    countries.update({tag: {'flags': set()} for tag, reply in replies.items()
                                      if reply is not None})
                    self.assertFalse(conditions(war_gate, 'SWI', countries, year=1846))
                    self.assertEqual(conditions(war_gate, 'SWI', countries), len(countries) == 1)
                    for tag in (first, second):
                        reply = replies[tag]
                        if reply is None:
                            continue
                        self.assertFalse(conditions(invite_gate, tag, countries, year=1846))
                        self.assertTrue(conditions(invite_gate, tag, countries))
                        flags = countries[tag]['flags']
                        flags.add(scalar(immediate, 'set_country_flag'))
                        self.assertFalse(conditions(invite_gate, tag, countries))
                        self.assertFalse(conditions(war_gate, 'SWI', countries))
                        flags.update(node.value for node in reply.children
                                     if node.key == 'set_country_flag')
                        self.assertEqual('sonderbund_ally' in flags, reply is support)
                    self.assertTrue(conditions(war_gate, 'SWI', countries))
                    for option in war_options:
                        alliance = member(option, 'any_country')
                        self.assertEqual(scalar(alliance, 'create_alliance'), 'SDB')
                        self.assertEqual([tag for tag in replies if tag in countries and conditions(
                            member(alliance, 'limit').children, tag, countries)],
                            [tag for tag, reply in replies.items() if reply is support])
                        self.assertLess(alliance.start.offset, member(option, 'war').start.offset)
                    countries['SWI']['flags'] = {'sonderbund'}
                    self.assertFalse(conditions(war_gate, 'SWI', countries))

        for switzerland in ({}, {'SWI': {'ruling_party_ideology': 'conservative'}}):
            self.assertFalse(conditions(invite_gate, 'AUS', switzerland))
        self.assertFalse(conditions(invite_gate, 'ENG', {'SWI': {'ruling_party_ideology': 'liberal'}}))

    def test_velasco_branch_controls_independence_after_peace(self):
        path = 'TGC/events/MEXFlavor.txt'
        capture = event(path, 44840)
        offer = event(path, 44841)
        independence = event('TGC/events/USA_Minors.txt', 99960)
        self.assertEqual(scalar(independence, 'fire_only_once'), 'yes')
        gate = member(independence, 'trigger').children
        capture_options = [node for node in capture.children if node.key == 'option']
        self.assertEqual(scalar(member(capture_options[0], 'MEX'), 'country_event'), '44841')
        self.assertFalse(any(node.key == 'country_event' for node in walk(capture_options[1].children)))
        for option, target, ai_weight in zip(
            (node for node in offer.children if node.key == 'option'),
            (44842, 44843, 44844), ('5', '80', '15'), strict=True
        ):
            self.assertEqual(scalar(member(option, 'TEX'), 'country_event'), str(target))
            self.assertEqual(scalar(member(option, 'ai_chance'), 'factor'), ai_weight)
            self.assertEqual(scalar(option, 'end_war'), 'TEX' if target != 44844 else None)
            outcome = event(path, target)
            flags = {node.value for node in walk(outcome.children) if node.key == 'set_global_flag'}
            self.assertEqual(flags, {'texas_velasco_peace'} if target == 44842 else set())
            if target != 44844:
                treaty = member(member(outcome, 'option'), 'add_country_modifier')
                self.assertEqual(scalar(treaty, 'duration'), '1825' if target == 44842 else '1095')
            for truce, owns, at_war, vassal, recaptured in product((False, True), repeat=5):
                tex = {'owns': '132' if owns else '133', 'war': 'yes' if at_war else 'no',
                       'is_vassal': 'yes' if vassal else 'no', 'truce_with': 'MEX' if truce else None}
                mexico = {'flags': {'texas_recaptured'} if recaptured else set()}
                expected = owns and not (at_war or vassal or recaptured) and (truce or target == 44842)
                self.assertEqual(conditions(gate, 'TEX', {'TEX': tex, 'MEX': mexico}, flags), expected)
                self.assertFalse(conditions(gate, 'USA', {'USA': tex, 'MEX': mexico}, flags))
        self.assertEqual(scalar(member(independence, 'option'), 'set_global_flag'), 'texas_independent')


if __name__ == '__main__':
    unittest.main()
