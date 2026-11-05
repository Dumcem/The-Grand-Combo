"""Dependency/AI/horizon fixtures and an independent real-corpus supply oracle."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import itertools
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'TGC/tools'))
import audit_1966_balance as audit
import lib_1966_parser as parser
from lib_1966_diagnostics import Reporter
from lib_1966_functional import (ResearchDependencies, necessary_literals, naval_ai_scenario,
                                 horizon_inventory, campaign_end)
from lib_1966_mechanics import report_consumers
from lib_1966_runtime import compose_runtime, unit_definitions
from lib_1966_semantics import VARIABLE, project_unit
from test_1966_applied import reference_tree
import test_1966_applied as independent


def dependencies(tech, invention=''):
    sources = {'fixture/technologies/t.txt': tech, 'fixture/inventions/i.txt': invention}
    with patch.object(parser, 'read_text', side_effect=lambda f, **kw: sources[f]):
        return ResearchDependencies(list(sources))


def projection(base, rows):
    return {'status': 'applied', 'baseline': base, 'assignments': [
        {'source_file': f'fixture/{"technologies" if kind == "technology" else "inventions"}/x.txt',
         'invention': owner, 'value': value} for kind, owner, value in rows]}


class DependencyFixtures(unittest.TestCase):
    def test_predecessor_and_forced_positive_effects(self):
        d = dependencies('A={ area=x year=1900 } B={ area=x year=1910 }',
                         'C={ limit={ B=1 } chance={ base=3 } }')
        q = projection(.2, [('technology','A',.5), ('technology','B',.3), ('invention','C',-.7)])
        r = d.lower_bound(q)
        self.assertAlmostEqual(r['lower_bound'], .2)
        self.assertIn(('technology','A'), d.closure(('invention','C')))
        self.assertEqual(len(r['negative_dependencies'][0]['forced_positive']), 2)

    def test_whole_owner_not_individual_negative_bodies(self):
        d = dependencies('A={ area=x year=1900 }')
        self.assertAlmostEqual(d.lower_bound(projection(.4, [
            ('technology','A',-.8), ('technology','A',1)]))['lower_bound'], .4)

    def test_or_intersection_and_country_scopes_are_not_grants(self):
        d = dependencies('A={ area=x year=1900 } B={ area=y year=1900 }',
            'C={ limit={ OR={ A=1 B=1 } any_country={ A=1 } } chance={ base=3 } }')
        self.assertEqual(d.required['invention','C'], set())
        r = d.lower_bound(projection(.2, [('technology','A',1), ('invention','C',-.5)]))
        self.assertLess(r['lower_bound'], 0)
        self.assertEqual(r['reachability'], 'unverified')

    def test_negative_fixture_has_explicit_static_reachable_witness(self):
        d = dependencies('A={ area=x year=1900 }', 'C={ limit={ A=1 } chance={ base=3 } }')
        q = projection(.2, [('technology','A',.1), ('invention','C',-.6)])
        r = d.lower_bound(q)
        self.assertAlmostEqual(r['lower_bound'], -.3)
        self.assertEqual(r['reachability'], 'reachable_in_static_research_model')
        self.assertIn(('invention','C'), r['witness']['acquired'])

    def test_unknown_country_or_chance_does_not_prove_reachability(self):
        for limit, chance in [('A=1 tag=ABC','base=3'), ('A=1','base=0.5'),
                              ('A=1','base=3 modifier={factor=-5 war=yes}')]:
            d = dependencies('A={area=x year=1900}', 'C={limit={'+limit+'} chance={'+chance+'}}')
            r = d.lower_bound(projection(.2, [('invention','C',-.5)]))
            self.assertLess(r['lower_bound'],0)
            self.assertEqual(r['reachability'],'unverified')

    def test_mutually_exclusive_combinations_are_rejected(self):
        d = dependencies('', 'A={limit={NOT={invention=B}} chance={base=3}} '
                              'B={limit={NOT={invention=A}} chance={base=3}}')
        r = d.lower_bound(projection(1.5,[('invention','A',-1),('invention','B',-1)]))
        self.assertEqual(r['lower_bound'],.5)
        self.assertEqual(r['rejected_contradictions'],1)

    def test_negated_or_and_explicit_invention_namespace(self):
        text = 'L={ NOT={ OR={ invention=A invention=B } } }'
        nodes = parser.parse_script(text).definitions[0].children
        atoms = necessary_literals(nodes,{('technology','A'),('invention','A'),('invention','B')})
        self.assertEqual(atoms,{(('invention','A'),False),(('invention','B'),False)})

    def test_alice_not_has_implicit_or_children(self):
        d=dependencies('A={area=x year=1900} B={area=y year=1900}',
                       'C={limit={NOT={A=1 B=1}} chance={base=3}}')
        self.assertEqual(d.forbidden['invention','C'],{('technology','A'),('technology','B')})
        self.assertFalse(d._simple_witness({('technology','A'),('invention','C')}))
        self.assertTrue(d._simple_witness({('invention','C')}))

    def test_cycles_and_partial_or_large_inputs_are_not_reachability_proofs(self):
        d = dependencies('', 'A={limit={invention=B} chance={base=3}} '
                              'B={limit={invention=A} chance={base=3}}')
        q=projection(.2,[('invention','A',-.5)])
        self.assertEqual(d.lower_bound(q)['reachability'],'unverified')
        self.assertEqual(d.lower_bound(q,max_negative_owners=0)['status'],'unverified')
        self.assertEqual(d.lower_bound(dict(q,status='applied_subset'))['status'],'unverified')
        self.assertEqual(d.lower_bound(projection(.2,[('technology','missing',-.5)]))['status'],'unverified')

    def test_negative_consumer_finding_stays_visible(self):
        data = {'unit_type':'infantry','unit_domain':'land'}
        d = dependencies('A={area=x year=1900}')
        q = projection(.2,[('technology','A',-.5)])
        q.update(final=-.3,superseded=[],base_superseded=[])
        rep=Reporter();report_consumers({'u':data},{'u':{'stats':{'supply_consumption':q}}},rep,d)
        row=next(x for x in rep.diagnostics if x.code=='consumer_domain')
        self.assertEqual(row.level,'WARN')
        self.assertEqual(row.data['dependency_analysis']['reachability'],'reachable_in_static_research_model')


def navy_unit(category, hull, gun, speed, *, active=False, port=0, evasion=0):
    data={'unit_domain':'naval','unit_type':category,'active':active,
          'can_build_overseas':False,'primary_culture':False}
    values=dict(hull=hull,gun_power=gun,maximum_speed=speed,torpedo_attack=0,
                evasion=evasion,min_port_level=port)
    return data, {'stats':{s:{'baseline':v,'final':v,'status':'applied'} for s,v in values.items()}}


class NavalAIFixtures(unittest.TestCase):
    def fixture(self):
        pairs={k:navy_unit('big_ship',h,g,9,port=p) for k,h,g,p in
               [('carrier',65,21,7),('battleship',70,50,4),('dreadnought',80,60,5)]}
        return {k:v[0] for k,v in pairs.items()},{k:v[1] for k,v in pairs.items()}

    def test_unlock_local_buildability_and_choice_are_distinct(self):
        units,p=self.fixture()
        self.assertEqual(naval_ai_scenario(units,p,set(),[7]),{})
        r=naval_ai_scenario(units,p,set(units),[7])['big_ship']
        self.assertEqual(r['locally_buildable'],['battleship','carrier','dreadnought'])
        self.assertEqual(r['new_build_candidates'],['dreadnought'])
        self.assertIn('carrier',r['penalized_by_base_hull'])
        self.assertEqual(r['refit_candidates'],['dreadnought'])
        r=naval_ai_scenario(units,p,{'carrier','battleship'},[7])['big_ship']
        self.assertEqual(r['new_build_candidates'],['battleship'])

    def test_port_filter_does_not_fallback_to_locally_buildable_runner_up(self):
        units,p=self.fixture();r=naval_ai_scenario(units,p,set(units),[4])['big_ship']
        self.assertEqual(r['locally_buildable'],['battleship'])
        self.assertEqual(r['selected_buildable'],[])
        self.assertEqual(r['refit_candidates'],['dreadnought']) # refit is not gated by port
        self.assertFalse(r['port_fallback'])

    def test_upgrade_uses_base_when_evasion_zero_and_applied_when_positive(self):
        units,p=self.fixture();p['carrier']['stats']['gun_power']['final']=999
        self.assertEqual(naval_ai_scenario(units,p,set(units),[7])['big_ship']['refit_candidates'],['dreadnought'])
        p['carrier']['stats']['evasion']['final']=.1
        self.assertEqual(naval_ai_scenario(units,p,set(units),[7])['big_ship']['refit_candidates'],['carrier'])
        # New construction still uses base hull, never the refit gun score.
        self.assertEqual(naval_ai_scenario(units,p,set(units),[7])['big_ship']['new_build_candidates'],['dreadnought'])

    def test_light_and_transport_use_speed_for_refit_not_construction(self):
        for category in ['light_ship','transport']:
            pairs={'fast':navy_unit(category,5,2,20),'armored':navy_unit(category,10,4,5)}
            units={k:v[0] for k,v in pairs.items()};p={k:v[1] for k,v in pairs.items()}
            r=naval_ai_scenario(units,p,set(units),[0]) [category]
            self.assertEqual(r['new_build_candidates'],['armored'])
            self.assertEqual(r['refit_candidates'],['fast'])

    def test_ties_shortages_overseas_and_primary_culture(self):
        units,p=self.fixture();p['carrier']['stats']['hull']['baseline']=80
        units['carrier']['primary_culture']=True
        r=naval_ai_scenario(units,p,set(units),[7],overseas=True,shortages={'dreadnought'})['big_ship']
        self.assertEqual(r['new_build_candidates'],['carrier','dreadnought'])
        self.assertEqual(r['selected_buildable'],[])
        self.assertEqual(r['refit_candidates'],['battleship'])
        self.assertEqual(r['actual_execution'],'unverified')


class HorizonFixtures(unittest.TestCase):
    def rows(self, tech, inv='', end=date(1966,1,1)):
        sources={'fixture/technologies/t.txt':tech,'fixture/inventions/i.txt':inv}
        with patch.object(parser,'read_text',side_effect=lambda f,**kw:sources[f]):
            d=ResearchDependencies(list(sources));timing=audit.build_year_inference(list(sources))
        return {r['owner']:r for r in horizon_inventory(d,timing,end)}

    def test_end_boundary_and_invention_dependency(self):
        r=self.rows('A={area=x year=1962} B={area=x year=1966}',
                    'C={limit={B=1} chance={base=3}}')
        self.assertEqual(r['A']['status'],'reference_before_end')
        self.assertEqual(r['B']['status'],'no_ordinary_use_window')
        self.assertEqual(r['C']['status'],'no_ordinary_use_window')

    def test_predecessor_can_delay_an_earlier_named_year(self):
        r=self.rows('A={area=x year=1966} B={area=x year=1960}')
        self.assertEqual(r['B']['necessary_reference_year'],1966)

    def test_chance_year_is_not_an_eligibility_gate_and_unknown_remains_unknown(self):
        r=self.rows('A={area=x year=1962}',
            'C={limit={A=1} chance={base=2 modifier={factor=4 year=1966}}} '
            'D={limit={year=1966} chance={base=3}} E={chance={base=3}}')
        self.assertEqual(r['C']['status'],'reference_before_end')
        self.assertEqual(r['C']['probability_years_not_gates'],[1966])
        self.assertEqual(r['D']['status'],'no_ordinary_use_window')
        self.assertEqual(r['E']['status'],'unverified')
        self.assertEqual(self.rows('A={area=x year=1966}',end=date(1966,2,1))['A']['status'],'reference_before_end')

    def test_effective_end_date_is_read_and_not_hardcoded(self):
        class Inventory:
            selected={'common/defines.lua':type('Source',(),{'file':'defines'})()}
        with patch('lib_1966_functional.read_text',return_value="-- end_date='1900.1.1'\nend_date='1970.2.3'"):
            self.assertEqual(campaign_end(Inventory()),date(1970,2,3))
        with patch('lib_1966_functional.read_text',return_value="--[=[\nend_date='1900.1.1'\n]=]\nend_date='1970.2.3'"):
            self.assertEqual(campaign_end(Inventory()),date(1970,2,3))
        with patch('lib_1966_functional.read_text',return_value="end_date='1970.2.31'"):
            with self.assertRaises(parser.ScriptError):campaign_end(Inventory())


class FunctionalCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv=compose_runtime(ROOT);cls.files=cls.inv.files('technologies')+cls.inv.files('inventions')
        cls.paths=unit_definitions(cls.inv,ROOT)
        cls.units={u:audit.parse_unit_block(f,u) for u,f in cls.paths.items()}
        cls.naval={u for u,d in cls.units.items() if d['unit_domain']=='naval'}
        timing=audit.build_year_inference(cls.files);assignments=defaultdict(list)
        for f in cls.files:
            for u,xs in audit.parse_effect_unit_assignments(f,set(cls.units),VARIABLE,timing,
                {'navy_base':cls.naval,'army_base':set(cls.units)-cls.naval}).items():assignments[u].extend(xs)
        cls.projections={u:project_unit(d,assignments[u]) for u,d in cls.units.items()}

    def test_supply_bounds_against_independent_literal_tree_enumeration(self):
        # Independent reader, owner aggregation and direct-positive closures. Real
        # negative-supply limits use direct references; extra conditions are relaxed.
        definitions={};previous={};pred={};effects=defaultdict(dict)
        for f in sorted(self.files):
            kind='technology' if '/technologies/' in f else 'invention'
            for name,body,_,_ in reference_tree((ROOT/f).read_text(encoding='utf-8-sig')):
                key=kind,name;definitions[key]=body
                if kind=='technology':
                    area=next(v for k,v,_,_ in body if k=='area');pred[key]=previous.get(area);previous[area]=key
        for key,body in definitions.items():
            if key[0]=='invention':body=next((v for k,v,_,_ in body if k=='effect'),[])
            for scope,body0,_,_ in body:
                targets=set(self.units)-self.naval if scope=='army_base' else {scope} if scope in self.units else set()
                if not targets or not isinstance(body0,list):continue
                vals=[float(v) for k,v,_,_ in body0 if k=='supply_consumption']
                if vals:
                    for u in targets:effects[u][key]=effects[u].get(key,0)+vals[-1]
        def closure(key):
            found={key};todo=[key]
            while todo:
                k=todo.pop();body=definitions[k]
                limit=next((v for n,v,_,_ in body if n=='limit'),[])
                refs=[]
                for n,v,_,_ in limit:
                    if isinstance(v,list):continue
                    target=v if n=='invention' else n if v in ['1','yes'] else None
                    refs.extend(z for z in definitions if z[1]==target)
                if pred.get(k):refs.append(pred[k])
                for r in refs:
                    if r not in found:found.add(r);todo.append(r)
            return found
        dep=ResearchDependencies(self.files)
        for u in sorted(set(self.units)-self.naval):
            q=self.projections[u]['stats']['supply_consumption']
            negatives=sorted(k for k,v in effects[u].items() if v<0);minimum=float('inf')
            for flags in itertools.product([False,True],repeat=len(negatives)):
                selected=[k for k,on in zip(negatives,flags) if on]
                acquired=set().union(*(closure(k) for k in selected)) if selected else set()
                # Omitting positive inventions is a separate, looser oracle.
                value=q['baseline']+sum(v for k,v in effects[u].items() if k in acquired and (k[0]=='technology' or v<0))
                minimum=min(minimum,value)
            self.assertAlmostEqual(dep.lower_bound(q)['lower_bound'],minimum,u)
            self.assertAlmostEqual(minimum,self.units[u]['stats']['supply_consumption'],u)
            self.assertGreater(minimum,0,u)

    def test_real_ai_and_horizon_are_conditional_and_do_not_change_data(self):
        scenario=naval_ai_scenario(self.units,self.projections,self.naval,[7])['big_ship']
        self.assertIn('aircraftcarrier',scenario['locally_buildable'])
        self.assertEqual(scenario['new_build_candidates'],['dreadnought'])
        self.assertEqual(scenario['refit_candidates'],['dreadnought'])
        self.assertEqual(campaign_end(self.inv),date(1966,1,1))

    def test_every_transport_subset_and_other_ship_times_independently(self):
        helper=independent.TransportRuntimeContracts()
        for layer in ['TGC','TGC_Timeline_1966']:
            _,units,rows=helper.inputs(layer)
            for u,base in units.items():
                cuts=[v for _,_,_,targets,v in rows if u in targets]
                if u.endswith('_transport'):
                    results=[base+sum(v for v,on in zip(cuts,flags) if on)
                             for flags in itertools.product([False,True],repeat=len(cuts))]
                    self.assertEqual(min(results),45 if layer=='TGC' else 35)
                    self.assertTrue(all(x>0 for x in results))
                else:
                    self.assertTrue(all(v==-10 for v in cuts),u)
                    self.assertEqual(len(cuts),9 if layer=='TGC' else 11)

    def test_transport_epoch_curve_and_schools_are_progressive(self):
        helper=independent.TransportRuntimeContracts()
        for layer in ['TGC','TGC_Timeline_1966']:
            _,units,rows=helper.inputs(layer)
            for u in ['clipper_transport','steam_transport']:
                for year,expected in [(1836,80),(1850,75),(1870,70),(1875,60),
                                      (1900,55),(1915,50),(1919,45),(1929,40),(1939,35)]:
                    if layer=='TGC' and year>=1929:expected=45
                    tech=sum(v for _,y,_,targets,v in rows if u in targets and y and y<=year)
                    schools=[v for n,_,_,targets,v in rows if u in targets and n in {'blue_water_school','brown_water_school'}]
                    for number in range(3 if year>=1875 else 1):
                        value=units[u]+tech+sum(schools[:number])
                        self.assertEqual(value,expected+(2-number)*5 if year>=1875 else expected)


if __name__=='__main__':
    unittest.main()
