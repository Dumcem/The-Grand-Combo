"""Static regressions for the historical chains reconciled in Task 42."""

from functools import cache
import unittest

from test_1966_applied import ROOT
from lib_1966_parser import member, parse_script, scalar, walk
from lib_1966_runtime import compose_runtime


@cache
def definitions(path):
    data = (ROOT / 'TGC' / path).read_bytes()
    # Script tokens under test are ASCII. Preserve other bytes for legacy files.
    return parse_script(data.decode('latin-1'), file=path).definitions


def decision(file, name):
    container, = definitions(f'decisions/{file}.txt')
    return member(container, name, required=True)


def event(file, event_id):
    result, = (node for node in definitions(f'events/{file}.txt')
               if node.key == 'country_event' and scalar(node, 'id') == str(event_id))
    return result


def section(node, key):
    return member(node, key, required=True)


def evaluate(nodes, predicate):
    """Project conjunctions, disjunctions and negations in selected gates."""
    for node in nodes:
        if node.key == 'AND':
            result = evaluate(node.children, predicate)
        elif node.key in ('OR', 'NOT'):
            result = any(evaluate((child,), predicate) for child in node.children)
            if node.key == 'NOT':
                result = not result
        else:
            result = predicate(node)
        if not result:
            return False
    return True


class UpstreamChainsTests(unittest.TestCase):
    def test_german_texas_routes_only_with_a_live_sponsor_and_adv(self):
        purchase = decision('GEF', 'german_texas')
        effect = section(purchase, 'effect')
        flags = {node.value for node in effect.children if node.key == 'set_global_flag'}
        sponsor = scalar(effect, 'set_country_flag')
        self.assertEqual(scalar(section(purchase, 'potential'), 'ai'), 'no')
        self.assertEqual(scalar(effect, 'inherit'), 'TEX')
        self.assertEqual(scalar(section(effect, 'TEX'), 'change_tag'), 'ADV')
        for name, previous, cost in (
            ('german_texas_funding', None, '100000'),
            ('german_texas_funding2', 'german_texas_funding', '200000'),
            ('german_texas_funding3', 'german_texas_funding2', '400000'),
        ):
            funding = decision('GEF', name)
            potential = section(funding, 'potential')
            self.assertEqual(scalar(potential, 'ai'), 'no')
            self.assertEqual(scalar(potential, 'has_global_flag'), previous)
            self.assertEqual(scalar(section(funding, 'allow'), 'money'), cost)
            self.assertEqual(scalar(section(funding, 'effect'), 'set_global_flag'), name)
        question = event('GEF Events', 800000)
        gate = section(question, 'trigger').children

        def eligible(year=1878, exists=('ADV',), sponsors=(sponsor,), global_flags=flags,
                     allied=False):
            def predicate(node):
                match node.key:
                    case 'tag':
                        return node.value == 'USA'
                    case 'exists':
                        return node.value in exists
                    case 'has_global_flag':
                        return node.value in global_flags
                    case 'year':
                        return year >= int(node.value)
                    case 'alliance_with':
                        return allied
                    case 'any_country':
                        return any(evaluate(node.children, lambda child:
                                            (child.key, child.value) in
                                            {('exists', 'yes'), ('has_country_flag', flag)})
                                   for flag in sponsors)
                    case _:
                        raise AssertionError(node.key)
            return evaluate(gate, predicate)

        self.assertTrue(eligible())
        self.assertFalse(eligible(year=1877))
        self.assertFalse(eligible(year=1914))
        self.assertFalse(eligible(exists=('ADV', 'CSA')))
        self.assertFalse(eligible(exists=()))
        self.assertFalse(eligible(sponsors=()))
        self.assertFalse(eligible(allied=True))
        options = [node for node in question.children if node.key == 'option']
        self.assertEqual([scalar(section(node, 'ai_chance'), 'factor') for node in options],
                         ['0.7', '0.15', '0.1', '0.05'])
        for option, expected in zip(options, (810000, 811000, None, 811100), strict=True):
            answered = scalar(option, 'set_global_flag')
            self.assertFalse(eligible(global_flags=flags | {answered}))
            if expected is not None:
                dispatch = section(option, 'any_country')
                self.assertEqual(scalar(section(dispatch, 'limit'), 'has_country_flag'), sponsor)
                self.assertEqual(scalar(section(dispatch, 'country_event'), 'id'), str(expected))
                self.assertEqual(scalar(event('GEF Events', expected), 'is_triggered_only'), 'yes')
        annex_gate = section(decision('GEF', 'annex_texas'), 'potential')
        self.assertEqual(scalar(annex_gate, 'exists'), 'ADV')

    def test_polish_victory_unlocks_the_existing_krakow_path(self):
        victory = decision('POL', 'january_uprising_victory')
        self.assertEqual(scalar(section(victory, 'allow'), 'war'), 'no')
        neighbor = section(section(victory, 'allow'), 'any_neighbor_country')
        self.assertEqual(scalar(neighbor, 'truce_with'), 'THIS')
        self.assertEqual(scalar(neighbor, 'has_recently_lost_war'), 'yes')
        effect = section(victory, 'effect')
        self.assertEqual(scalar(section(effect, 'any_neighbor_country'), 'clr_country_flag'),
                         'through_january_uprising')
        success = scalar(effect, 'set_global_flag')
        krakow = decision('POL', 'krakow_uprising_decision')
        cpl, = (node for node in walk(section(krakow, 'allow').children) if node.key == 'CPL')

        def eligible(exists, at_war, flags):
            return evaluate(cpl.children, lambda node: {
                ('exists', 'yes'): exists,
                ('war_with', 'RUS'): at_war,
                **{('has_global_flag', flag): True for flag in flags},
            }.get((node.key, node.value), False))

        started = {'january_uprising_happened'}
        self.assertTrue(eligible(True, True, started))
        self.assertFalse(eligible(True, False, started))
        self.assertTrue(eligible(True, False, started | {success}))
        self.assertFalse(eligible(False, False, started | {success}))
        self.assertFalse(eligible(True, False, {success}))

    def test_american_renames_follow_date_owner_and_iron_range(self):
        rename = event('Renaming', 19)

        def final_name(province, year, culture, flags=()):
            name = None
            for node in walk(rename.children):
                if node.key != 'any_land_province':
                    continue
                limit = section(node, 'limit')
                if scalar(limit, 'province_id') != str(province):
                    continue

                def predicate(term):
                    if term.key == 'province_id':
                        return True
                    if term.key == 'year':
                        return year >= int(term.value)
                    if term.key == 'owner':
                        return evaluate(term.children, lambda owner: {
                            'is_culture_group': owner.value == culture,
                            'has_country_flag': owner.value in flags,
                            'primary_culture': False,
                        }[owner.key])
                    raise AssertionError(term.key)

                if evaluate(limit.children, predicate):
                    name = scalar(node, 'change_province_name')
            return name

        american = 'american_cultures'
        self.assertEqual(final_name(130, 1869, american), 'Fort Gibson')
        self.assertEqual(final_name(130, 1870, american), 'Tahlequah')
        self.assertEqual(final_name(130, 1870, 'pan_french'), 'Champlain')
        self.assertEqual(final_name(157, 1870, american), 'Fort Ripley')
        self.assertEqual(final_name(157, 1870, american, {'iron_ranges'}), 'Moorhead')
        self.assertEqual(final_name(157, 1871, american), 'Moorhead')

    def test_alsace_ownership_substitutes_for_the_missing_flag(self):
        formation = section(decision('Germany', 'form_germany'), 'allow')
        alternatives, = (node for node in formation.children if node.key == 'OR' and
                         any(term.key == 'has_country_flag' and term.value == 'ems_dispatch_sent'
                             for term in node.children))
        for owned, expected in (({'409', '410', '412', '3322'}, True),
                                ({'409', '410', '412'}, False)):
            self.assertEqual(evaluate((alternatives,),
                                      lambda term: term.key == 'owns' and term.value in owned),
                             expected)
        treaty = section(decision('Germany', 'treaty_of_elass_lorraine'), 'potential')
        self.assertEqual({term.value for term in treaty.children if term.key == 'owns'},
                         {'409', '410', '412', '3322'})

    def test_haiti_offer_claims_and_own_port(self):
        offer = decision('USA', 'st_nicolas_affair')
        claims = decision('USA', 'st_nicolas_affair_claims')
        for node, expected in ((offer, False), (claims, True)):
            gate = section(section(node, 'potential'), 'HAI')
            sphere = [child for child in gate.children if
                      any(term.key == 'in_sphere' for term in walk((child,)))]
            for in_sphere in (True, False):
                self.assertEqual(evaluate(sphere, lambda term: in_sphere), in_sphere == expected)
        self.assertEqual(scalar(section(section(offer, 'potential'), 'HAI'), 'owns'), '3284')
        relations = section(section(offer, 'allow'), 'HAI')
        for vassal, own_subject, truce, expected in (
            (False, False, False, True), (True, True, False, True),
            (True, False, False, False), (False, False, True, False),
        ):
            self.assertEqual(evaluate(relations.children, lambda term: {
                'is_vassal': not vassal, 'vassal_of': own_subject, 'truce_with': truce,
            }[term.key]), expected)
        self.assertEqual(scalar(section(section(claims, 'potential'), 'HAI'), 'truce_with'), 'THIS')
        choices = event('USA_Expansion', 530010)
        accept, refuse = (node for node in choices.children if node.key == 'option')
        self.assertEqual(scalar(section(accept, '3284'), 'secede_province'), 'FROM')
        self.assertEqual(scalar(section(refuse, 'FROM'), 'country_event'), '530011')
        identity = event('HAIFlavor', 45109)
        african, = (node for node in identity.children if node.key == 'option'
                    and scalar(node, 'name') == 'EVTOPTB45109')
        owned = section(african, 'any_owned')
        self.assertEqual(scalar(section(owned, 'limit'), 'province_id'), '2213')
        self.assertEqual(scalar(section(owned, 'add_province_modifier'), 'duration'), '1825')
        aid = section(decision('NotGreatPowers', 'request_military_aid'), 'allow')
        diplomacy = [node for node in aid.children if node.key == 'NOT']
        for ally, enemy in ((False, False), (True, False), (False, True)):
            self.assertEqual(evaluate(diplomacy, lambda scope: evaluate(
                scope.children, lambda term: {'alliance_with': ally, 'war_with': enemy}[term.key])),
                not (ally or enemy))

    def test_timeline_inherits_the_same_scripts(self):
        for layer in (None, 'TGC_Timeline_1966'):
            inventory = compose_runtime(ROOT, 'TGC', layer)
            for path in ('decisions/GEF.txt', 'decisions/POL.txt', 'decisions/Germany.txt',
                         'decisions/RUS.txt', 'decisions/USA.txt', 'decisions/NotGreatPowers.txt',
                         'events/GEF Events.txt', 'events/Renaming.txt', 'events/HAIFlavor.txt'):
                self.assertEqual(inventory.require(path), f'TGC/{path}')
