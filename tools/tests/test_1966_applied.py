"""Independent engine-field regressions pinned to Project Alice v1.3.0.

The oracle below is deliberately separate from the production lexer, source
composer, rules and semantic tables. It implements assignment into engine slots,
then addition across modifier objects. It is not an acquisition/battle simulator.
"""
import collections
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'TGC/tools'))
import audit_1966_balance as a
import lib_1966_parser as p
import lib_1966_semantics as s
import lib_1966_mechanics as m
from lib_1966_diagnostics import Reporter
from lib_1966_runtime import compose_runtime, unit_definitions


def reference_tree(text):
    tokens = [(m.group(), text.count('\n', 0, m.start()) + 1,
               m.start() - text.rfind('\n', 0, m.start())) for m in
              re.finditer(r'#[^\n]*|"[^"\n]*"|[{}=]|[^\s{}=]+', text)
              if not m.group().startswith('#')]
    def group(i):
        out = []
        while i < len(tokens) and tokens[i][0] != '}':
            key, line, col = tokens[i]
            if tokens[i+1][0] != '=':
                # Lists occur outside the unit fields under examination.
                i += 1
                continue
            if tokens[i+2][0] == '{':
                value, i = group(i+3)
            else:
                value = tokens[i+2][0].strip('"')
                i += 3
            out.append((key, value, line, col))
        return out, i+1
    return group(0)[0]


# Literal oracle storage schema, independently transcribed from parser_defs.txt
# 512-554 / 869-886, modifiers.hpp 265-289, parser_generator.cpp 831-836.
SLOTS = dict(attack='attack', gun_power='attack', defence='defence', defense='defence',
             hull='defence', reconnaissance='recon', fire_range='recon',
             discipline='discipline', evasion='discipline', siege='siege', torpedo_attack='siege',
             support='support', maneuver='maneuver', maximum_speed='speed',
             supply_consumption='supply', build_time='time', default_organisation='org')


def fixture(text, modifiers):
    with patch.object(p, 'read_text', return_value=text):
        data = a.parse_unit_block('fixture/units/u.txt', 'u')
    with patch.object(p, 'read_text', return_value=modifiers):
        found = a.parse_effect_unit_assignments('fixture/technologies/t.txt', {'u'}, set(s.VARIABLE),
            {('technology', 'T'): a.YearEvidence(1900, 1900, 'direct')}, {})
    return data, found.get('u', [])


class AppliedFixtures(unittest.TestCase):
    def test_member_order_and_distinct_objects(self):
        data, xs = fixture('u = { type = land defence = 3 hull = 9 build_cost = {} supply_cost = {} }',
                          'T = { u = { defence = 1 hull = 4 } u = { hull = 2 defence = 7 } }')
        q = s.project_unit(data, xs)['stats']['defence']
        self.assertEqual((q['baseline'], q['final']), (9, 20))
        self.assertEqual([x['value'] for x in q['assignments']], [4, 7])
        self.assertEqual([x['raw_stat'] for x in q['superseded']], ['defence', 'hull'])
        self.assertEqual(len(q['base_superseded']), 1)

    def test_exact_repeats_and_aliases_last_assignment(self):
        data, xs = fixture('u = { type = land defense = 3 defence = 5 build_cost = {} supply_cost = {} }',
                          'T = { u = { ATTACK = 1 attack = 2 gun_power = 6 } }')
        q = s.project_unit(data, xs)['stats']
        self.assertEqual(q['defence']['baseline'], 5)
        self.assertEqual(q['attack']['final'], 6)
        self.assertEqual(len(q['attack']['superseded']), 2)

    def test_context_domain_and_v2_gap(self):
        data, xs = fixture('u = { type = naval hull = 10 fire_range = .5 max_strength = 100 build_cost = {} supply_cost = {} }',
                          'T = { u = { reconnaissance = 2 defence = 3 } }')
        q = s.project_unit(data, xs)['stats']
        self.assertEqual(q['fire_range']['final'], 2.5)
        self.assertEqual(q['hull']['final'], 13)
        self.assertEqual(q['max_strength']['status'], 'ignored')
        self.assertEqual(s.project_unit(data, xs, s.V2)['stats'], {})
        self.assertEqual(s.property_evidence('colonial_points', '5', 'modifier', s.ALICE).status, 'unsupported')

    def test_integer_assignment_before_addition(self):
        data, xs = fixture('u = { type = land default_organisation = 30 build_cost = {} supply_cost = {} }',
                          'T = { u = { default_organisation = 2.5 } u = { default_organisation = 2.5 } }')
        self.assertEqual(s.project_unit(data, xs)['stats']['default_organisation']['final'], 34)


class IndependentAppliedCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {}
        for directory in ['technologies', 'inventions', 'units']:
            overlay = {}
            for layer in ['TGC', 'TGC_Timeline_1966']:
                for f in (ROOT/layer/directory).glob('*.txt'):
                    overlay[f.name] = f.relative_to(ROOT).as_posix()
            cls.files[directory] = sorted(overlay.values())
        cls.trees = {f: reference_tree((ROOT/f).read_text(encoding='utf-8-sig'))
                     for fs in cls.files.values() for f in fs}

    def test_every_applied_contribution_and_total_against_independent_slots(self):
        units, expected, origins = {}, {}, collections.defaultdict(list)
        for f in self.files['units']:
            for u, fields, _, _ in self.trees[f]:
                units[u] = (dict((k, v) for k,v,_,_ in fields)['type'], f)
                expected[u] = {slot: 0. for slot in SLOTS.values()}
                for k, raw, _, _ in fields:
                    if k in SLOTS:
                        expected[u][SLOTS[k]] = float(int(float(raw))) if k in {'build_time','default_organisation'} else float(raw)
        for f in self.files['technologies'] + self.files['inventions']:
            for owner, fields, _, _ in self.trees[f]:
                if '/inventions/' in f:
                    fields = next((v for k,v,_,_ in fields if k=='effect'), [])
                for scope, fields0, _, _ in fields:
                    targets = [scope] if scope in units else [u for u,(d,_) in units.items()
                        if scope == ('army_base' if d=='land' else 'navy_base')]
                    if not targets or not isinstance(fields0, list):
                        continue
                    chosen = {}
                    for k, raw, line, col in fields0:
                        if k in SLOTS:
                            value = float(int(float(raw))) if k in {'build_time','default_organisation'} else float(raw)
                            chosen[SLOTS[k]] = (value, k, line, col)
                    for u in targets:
                        for slot, (value, k, line, col) in chosen.items():
                            expected[u][slot] += value
                            origins[u,slot].append((f, owner, scope, k, line, col, value))
        inv = compose_runtime(ROOT)
        self.assertEqual(inv.files('technologies'), self.files['technologies'])
        files = inv.files('technologies') + inv.files('inventions')
        timing = a.build_year_inference(files)
        scopes = {scope:{u for u,(d,_) in units.items() if d==domain}
                  for scope,domain in [('army_base','land'),('navy_base','naval')]}
        assignments = collections.defaultdict(list)
        for f in files:
            for u,xs in a.parse_effect_unit_assignments(f,set(units),set(s.VARIABLE),timing,scopes).items():
                assignments[u].extend(xs)
        projections = {}
        for u, (domain, f) in units.items():
            q = s.project_unit(a.parse_unit_block(f,u),assignments[u])['stats']
            projections[u] = q
            for key, value in q.items():
                if key not in SLOTS or value['final'] is None:
                    continue
                slot = SLOTS[key]
                with self.subTest(unit=u,field=key):
                    self.assertAlmostEqual(value['final'],expected[u][slot])
                    actual = [(x['source_file'],x['invention'],x['scope_key'],x['raw_stat'],x['line'],x['column'],x['value'])
                              for x in value['assignments']]
                    self.assertCountEqual(actual, origins[u,slot])
        for u, stat, value in [('aircraftcarrier','hull',117),('aircraftcarrier','gun_power',56),
            ('aircraftcarrier','fire_range',4.5),('cruiser','fire_range',2.65),
            ('submarine','fire_range',4.7),('tank','defence',44.6)]:
            self.assertAlmostEqual(projections[u][stat]['final'], value)


class MechanicalContracts(unittest.TestCase):
    def test_land_formula_and_formation_are_separate(self):
        values = dict(attack=10, defence=20, support=3, maneuver=2.9)
        artillery = m.land_factors(values,'support')
        self.assertEqual((artillery['front_attack'],artillery['rear_attack'],artillery['rear_defence']), (2,6,9))
        self.assertEqual(artillery['maneuver_target_steps'],2)
        self.assertEqual(m.land_factors(dict(values,support=0),'special')['rear_attack'],0)
        self.assertIsNone(m.land_factors(values,'cavalry')['rear_attack'])
        perturbed = m.land_factors(dict(values,attack=12,support=3.6),'support')
        self.assertAlmostEqual(perturbed['rear_attack']/artillery['rear_attack'],1.32)

    def test_naval_domains_and_geometry_independent_of_mod(self):
        values = dict(gun_power=20,torpedo_attack=7,hull=30,evasion=.5,fire_range=2,maximum_speed=8)
        out = m.naval_factors(values)
        self.assertEqual((out['salvo_small_target'],out['salvo_big_target']), (20,27))
        self.assertEqual(out['hull_over_received_damage_factor'],60)
        self.assertFalse(out['covers_initial_separation'])
        self.assertTrue(m.naval_factors(dict(values,fire_range=2.01))['covers_initial_separation'])
        self.assertIsNone(m.naval_factors(dict(values,evasion=1))['hull_over_received_damage_factor'])
        for stat,value in [('build_time',0),('hull',-1),('min_port_level',2.5),('evasion',1.1),('supply_consumption_score',-1)]:
            self.assertIsNotNone(m.domain_violation(stat,value))
        for stat,value in [('build_time',1),('min_port_level',0),('evasion',1),('evasion',.99)]:
            self.assertIsNone(m.domain_violation(stat,value))

    def test_requirements_or_intersection_and_unknowns(self):
        node = p.parse_script('L = { or = { and = { A = 1 B = 1 } A = 1 } NOT = { C = 1 } }').definitions[0]
        known = {('technology',x) for x in ['A','B','C']}
        self.assertEqual(m.necessary_references(node.children,known),{('technology','A')})
        node = p.parse_script('L = { or = { A = 1 unknown = yes } }').definitions[0]
        self.assertEqual(m.necessary_references(node.children,known),set())

    def test_port_flags_include_activation_and_fold_per_definition(self):
        file = 'fixture/technologies/a.txt'
        text = 'A = { year = 1836 area = x activate_building = naval_base max_naval_base = 1 } B = { year = 1900 area = x max_naval_base = 1 }'
        timing = {('technology',x):a.YearEvidence(y,y,'direct') for x,y in [('A',1836),('B',1900)]}
        with patch.object(p,'read_text',return_value=text):
            _,incs = m.availability_inventory([file],timing)
        self.assertEqual([x['increment'] for x in incs],[1,1])

    def test_real_port_path_corrects_task25_omitted_activation(self):
        inv = compose_runtime(ROOT); files = inv.files('technologies')+inv.files('inventions')
        activations, incs = m.availability_inventory(files,a.build_year_inference(files))
        rows = sorted((x['research_reference_year'],x['owner'],x['increment']) for x in incs if x['kind']=='technology')
        self.assertIn((1836,'post_nelsonian_thought',1),rows)
        self.assertEqual(sum(v for _,_,v in rows),8)
        self.assertEqual(next(y for i,(y,_,_) in enumerate(rows,1) if i==7),1929)
        self.assertEqual(activations['aircraftcarrier'][0]['research_model_not_before'],1919)
        self.assertEqual(activations['plane'][0]['research_model_not_before'],1914)
        self.assertEqual(activations['tank'][0]['research_model_not_before'],1917)

    def test_legacy_metadata_never_promotes_rule_to_invariant(self):
        rep = Reporter()
        rep.add('WARN','test',category='numeric_rule',code='final_range',evidence='unvalidated_rule')
        rep.add('FAIL','test',category='technical_invariant')
        self.assertEqual([d.basis for d in rep.diagnostics],['legacy_unvalidated','technical_contract'])
        self.assertTrue(rep.diagnostics[0].message.startswith('LEGACY UNVALIDATED:'))

    def test_direct_invalid_divisor_and_relaxed_envelope_have_different_basis(self):
        data,xs = fixture('u = { type = land build_time = 0 default_organisation = 30 discipline = 1 build_cost = {} supply_cost = {} }',
                          'T = { u = { build_time = -10 } }')
        rep = Reporter();m.report_consumers({'u':data},{'u':s.project_unit(data,xs)},rep)
        row = next(d for d in rep.diagnostics if d.code=='consumer_domain' and d.stat=='build_time')
        self.assertEqual((row.level,row.basis),('FAIL','technical_contract'))
        data,xs = fixture('u = { type = land build_time = 5 default_organisation = 30 discipline = 1 build_cost = {} supply_cost = {} }',
                          'T = { u = { build_time = -10 } }')
        rep = Reporter();m.report_consumers({'u':data},{'u':s.project_unit(data,xs)},rep)
        row = next(d for d in rep.diagnostics if d.code=='consumer_domain' and d.stat=='build_time')
        self.assertEqual((row.level,row.basis),('WARN','conditional_model'))

    def test_unverified_later_member_supersedes_verified_earlier_member(self):
        data,xs = fixture('u = { type = naval hull = 10 build_cost = {} supply_cost = {} }',
                          'T = { u = { hull = 2 defence = 2e3 } }')
        q = s.project_unit(data,xs)['stats']['hull']
        self.assertEqual((q['status'],q['final'],q['excluded']),('applied_subset',10,1))
        self.assertEqual(q['assignments'],[])
        self.assertEqual(q['superseded'][0]['raw_value'],'2')

    def test_port_above_configured_cap_is_a_technical_failure(self):
        data,xs = fixture('u = { type = naval hull = 10 min_port_level = 9 build_cost = {} supply_cost = {} }','T = {}')
        class Inventory:
            def require(self,path):return path
        rep = Reporter()
        with patch.object(p,'read_text',return_value='naval_base = { max_level = 8 }'):
            m.report_availability(Inventory(),{'u':data},{'u':s.project_unit(data,xs)},[],{},rep)
        row = next(d for d in rep.diagnostics if d.code=='port_requirement_cap')
        self.assertEqual((row.level,row.basis,row.engine),('FAIL','technical_contract','alice_1.3.0'))


class TransportRuntimeContracts(unittest.TestCase):
    def inputs(self, layer):
        files = {}
        for directory in ['units','technologies','inventions']:
            by_name = {}
            for root in (['TGC'] if layer=='TGC' else ['TGC','TGC_Timeline_1966']):
                for f in (ROOT/root/directory).glob('*.txt'):
                    by_name[f.name] = f
            files[directory] = list(by_name.values())
        units = {}
        for f in files['units']:
            for u, fields, _, _ in reference_tree(f.read_text(encoding='utf-8-sig')):
                fields = dict((k,v) for k,v,_,_ in fields)
                if fields['type']=='naval':
                    units[u] = int(fields['build_time'])
        rows = []
        for f in files['technologies']+files['inventions']:
            for name,fields,_,_ in reference_tree(f.read_text(encoding='utf-8-sig')):
                meta = dict((k,v) for k,v,_,_ in fields)
                body = meta.get('effect',[]) if f.parent.name=='inventions' else fields
                for scope,values,_,_ in body:
                    targets = units if scope=='navy_base' else [scope] if scope in units else []
                    if not targets or not isinstance(values,list):
                        continue
                    cuts = [int(v) for k,v,_,_ in values if k=='build_time']
                    if cuts:
                        rows.append((name,int(meta.get('year',0)),scope,set(targets),cuts[-1]))
        return files,units,rows

    def test_schools_have_joint_positive_discovery_path_in_both_layers(self):
        for layer in ['TGC','TGC_Timeline_1966']:
            files,_,_ = self.inputs(layer)
            f = next(f for f in files['inventions'] if f.name=='navy_inventions.txt')
            schools = {n:dict((k,v) for k,v,_,_ in fields) for n,fields,_,_ in
                       reference_tree(f.read_text(encoding='utf-8-sig')) if n in {'blue_water_school','brown_water_school'}}
            self.assertEqual(len(schools),2)
            for school in schools.values():
                self.assertEqual([(k,v) for k,v,_,_ in school['limit']], [('blue_and_brown_water_schools','1')])
                self.assertGreater(int(next(v for k,v,_,_ in school['chance'] if k=='base')),0)
                # No mutual-exclusion predicate in either necessary limit;
                # acquiring the prerequisite permits both positive base chances.

    def test_scoped_late_reductions_leave_all_other_ships_unchanged(self):
        transports = {'clipper_transport','steam_transport'}
        for layer in ['TGC','TGC_Timeline_1966']:
            _,units,rows = self.inputs(layer)
            names = ['modern_naval_design'] if layer=='TGC' else ['modern_naval_design','mechanized_naval_production','automated_naval_design']
            for name in names:
                actual = {u:delta for n,_,_,targets,delta in rows if n==name for u in targets}
                expected = {u:(-5 if u in transports else -10) for u in units}
                self.assertEqual(actual,expected)
                self.assertTrue(all(scope!='navy_base' for n,_,scope,_,_ in rows if n==name))

    def test_positive_for_every_subset_and_provisional_progression(self):
        for layer in ['TGC','TGC_Timeline_1966']:
            _,units,rows = self.inputs(layer)
            for u in ['clipper_transport','steam_transport']:
                cuts = [(n,y,v) for n,y,_,targets,v in rows if u in targets]
                # All cuts are nonpositive: all-effects is a lower bound for
                # EVERY subset, including subsets that are not reachable.
                self.assertTrue(all(v<=0 for _,_,v in cuts))
                self.assertEqual(units[u],90)
                self.assertEqual(units[u]+sum(v for _,_,v in cuts),45 if layer=='TGC' else 35)
                before = [(n,y,v) for n,y,v in cuts if y and y<1919]
                self.assertEqual([v for _,_,v in before],[-5]*6)
                self.assertEqual(units[u]+sum(v for _,_,v in before)-10,50)
                self.assertEqual([v for n,_,v in cuts if n=='modern_naval_design'],[-5])
                self.assertTrue(all(v == -5 for _,_,v in cuts))
                self.assertEqual(len(cuts),9 if layer=='TGC' else 11)

    def test_old_bug_and_minimal_integer_correction_are_independent(self):
        # Six earlier techs and two jointly discoverable schools consume 80 days.
        # The old seventh -10 reaches zero; further -10 cuts make it negative.
        old_core = 90 - 6*10 - 2*10 - 10
        old_timeline = old_core - 2*10
        self.assertEqual((old_core,old_timeline),(0,-20))
        safe_last_cut = max(c for c in range(11) if 90-80-c>0)
        self.assertEqual(safe_last_cut,9)


if __name__ == '__main__':
    unittest.main()
