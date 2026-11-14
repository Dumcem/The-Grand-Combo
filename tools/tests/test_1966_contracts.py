"""Contract regressions from the independent Task 23 review."""
import sys
from pathlib import Path
import unittest
import contextlib
import copy
from collections import Counter
import io
import json
import os
import subprocess
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'TGC/tools'))
import lib_1966_parser as p
import audit_1966_balance as a
import validate_1966_extension as v
import lib_1966_runtime as runtime
import lib_1966_semantics as semantics
from lib_1966_diagnostics import Reporter
from test_1966_analysis import independent_inventory, effect_identity

CATALOG = set('attack defence hull gun_power torpedo_attack reconnaissance support maneuver siege maximum_speed evasion fire_range discipline supply_consumption build_time default_organisation max_strength colonial_points limit_per_port min_port_level supply_consumption_score'.split())


class CallerRegressions(unittest.TestCase):
    def test_free_effect_entry_is_not_silently_accepted(self):
        text = 'I = { effect = { orphan infantry = { attack = 2 } } }'
        with patch.object(p, 'read_text', return_value=text):
            with self.assertRaises(p.ScriptError):
                v.validate_effect_unit_targets('fixture/inventions/i.txt', {'infantry'})

    def test_effect_operator_and_duplicates_are_ambiguous(self):
        for text in ['I = { effect > { infantry = { attack = 2 } } }',
                     'I = { effect = {} effect = {} }']:
            with self.subTest(text=text), patch.object(p, 'read_text', return_value=text):
                with self.assertRaises(p.ScriptError):
                    v.validate_effect_unit_targets('fixture/inventions/i.txt', {'infantry'})

    def test_defense_alias_is_preserved_as_canonical_stat(self):
        with patch.object(p, 'read_text', return_value='T = { infantry = { defense = 7 } }'):
            out = a.parse_effect_unit_assignments('fixture/technologies/t.txt', {'infantry'}, {'defence'},
                {('technology', 'T'): a.YearEvidence(1900, 1900, 'direct')}, {})
        self.assertEqual([(x['stat'], x['value']) for x in out['infantry']], [('defence', 7.)])

    def test_alias_occurrences_are_preserved_before_engine_folding(self):
        with patch.object(p, 'read_text', return_value='T = { infantry = { defense = 7 defence = 8 } }'):
            out = a.parse_effect_unit_assignments('fixture/technologies/t.txt', {'infantry'}, {'defence'},
                {('technology', 'T'): a.YearEvidence(1900, 1900, 'direct')}, {})
        self.assertEqual([x['value'] for x in out['infantry']], [7., 8.])
        self.assertEqual(len({x['block_id'] for x in out['infantry']}), 1)

    def test_supported_numeric_group_and_bad_values_fail(self):
        for body in ['attack = { x = 2 }', 'attack > 2', 'attack = broken', 'orphan']:
            with self.subTest(body=body), patch.object(p, 'read_text', return_value='I = { effect = { infantry = { '+body+' } } }'):
                with self.assertRaises(p.ScriptError):
                    v.validate_effect_unit_targets('fixture/inventions/i.txt', {'infantry'})

    def test_group_outside_numeric_contract_is_explicit_limitation(self):
        text = 'I = { effect = { infantry = { supply_cost = { steel = 2 } } } }'
        rep = Reporter()
        with patch.object(p, 'read_text', return_value=text):
            semantics.report_modifier_semantics(['fixture/inventions/i.txt'], {'infantry'}, rep)
        d = next(d for d in rep.diagnostics if d.level == 'WARN')
        self.assertEqual((d.category, d.stat, d.engine), ('engine_semantics', 'supply_cost', semantics.ALICE))
        self.assertIn('group (preserved', d.message)

    def test_unknown_group_does_not_invent_inner_grammar_restrictions(self):
        node=p.parse_script('infantry = { future_property = { 1 2 3 } }').definitions[0]
        entries=semantics.numeric_modifier_entries(node)
        self.assertEqual([(key,value) for _,key,value in entries],[('future_property',None)])

    def test_configuration_duplicates_and_nonfinite_do_not_overwrite(self):
        for text in ['{"x":1,"x":2}', '{"x":NaN}']:
            with self.subTest(text=text), patch.object(p,'read_text',return_value=text):
                with self.assertRaises(p.ScriptError):p.read_json('fixture.json')

    def test_invalid_rule_shapes_are_integrity_not_balancing(self):
        original=a.read_rules()
        for kind in ['years','range','cap','applicable']:
            rules=copy.deepcopy(original)
            if kind=='years':rules['milestone_years']=[1836,1836]
            elif kind=='range':rules['units']['artillery']['monitored_stats']['attack']['final_range']={'min':9,'max':1}
            elif kind=='cap':rules['units']['artillery']['monitored_stats']['attack']['max_single_delta']='bad'
            else:rules['units']['artillery']['applicable_milestone_years']=['bad']
            with self.subTest(kind=kind),self.assertRaises(p.ScriptError):a.validate_rule_structure(rules)

    def test_json_failure_is_structured_without_partial_report(self):
        with patch.object(a,'read_rules',side_effect=p.ScriptError('fixture error')),patch.object(sys,'argv',['audit','--json']):
            o=io.StringIO()
            with contextlib.redirect_stdout(o):code=a.main()
        rows=json.loads(o.getvalue());self.assertEqual(code,1)
        self.assertEqual([(d['level'],d['category']) for d in rows],[('FAIL','integrity')])


class RuntimeFixtures(unittest.TestCase):
    def fixture(self, base):
        (base / 'Late').mkdir(parents=True)
        def write(name, text):
            f = base / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding='utf-8')
        write('Core.mod', 'name = "Core" path = "mod/Core" replace_path = "common" replace_path = "units" replace_path = "technologies" replace_path = "inventions"')
        write('Late.mod', 'name = "Late" path = "mod/Late" dependencies = { "Core" }')
        write('Core/common/technology.txt', 'folders = { branch = { doctrine } }')
        write('Core/technologies/branch.txt', 'T = { area = doctrine year = 1900 }')
        write('Core/inventions/retained.txt', 'I = { effect = { actual_id = { attack = 2 } } }')
        write('Core/units/different_filename.txt', 'actual_id = { type = land }')
        write('Optional.mod', 'name = "Optional" path = "mod/Optional"')
        write('Optional/inventions/no.txt', 'excluded = {}')
        return write

    def test_overlay_retention_and_definition_identifiers(self):
        with tempfile.TemporaryDirectory(prefix='tgc-contract-', dir=Path(__file__).parent) as td:
            root = Path(td); w = self.fixture(root)
            w('Late/technologies/branch.txt', 'replacement = {}')
            w('Late/inventions/new.txt', 'new = {}')
            w('Late/technologies/orphan.txt', 'not_loaded_by_alice = {}')
            inv = runtime.compose_runtime(root, 'Core', 'Late')
            self.assertEqual(inv.files('inventions'), ['Late/inventions/new.txt', 'Core/inventions/retained.txt'])
            self.assertEqual(inv.files('technologies'), ['Late/technologies/branch.txt'])
            self.assertEqual(runtime.unit_definitions(inv, root), {'actual_id': 'Core/units/different_filename.txt'})
            self.assertEqual([s.file for s in inv.replaced], ['Core/technologies/branch.txt'])
            self.assertEqual([s.file for s in inv.excluded], ['Late/technologies/orphan.txt'])
            self.assertNotIn('Optional/inventions/no.txt', inv.files('inventions'))

    def test_replace_path_removes_earlier_directory(self):
        with tempfile.TemporaryDirectory(prefix='tgc-contract-', dir=Path(__file__).parent) as td:
            root = Path(td); w = self.fixture(root)
            w('Late.mod', 'name = Late path = "mod/Late" dependencies = { Core } replace_path = inventions')
            w('Late/inventions/new.txt', 'new = {}')
            inv = runtime.compose_runtime(root, 'Core', 'Late')
            self.assertEqual(inv.files('inventions'), ['Late/inventions/new.txt'])

    def test_missing_dependency_and_branch_fail(self):
        for alteration in ['dependency', 'branch', 'path']:
            with self.subTest(alteration=alteration), tempfile.TemporaryDirectory(prefix='tgc-contract-', dir=Path(__file__).parent) as td:
                root = Path(td); w = self.fixture(root)
                if alteration == 'dependency': w('Late.mod', 'name = Late path = "mod/Late" dependencies = { Wrong }')
                elif alteration == 'branch': w('Core/common/technology.txt', 'folders = { missing = {} }')
                else: w('Late.mod', 'name = Late path = "../escape" dependencies = { Core }')
                with self.assertRaises(p.ScriptError): runtime.compose_runtime(root, 'Core', 'Late')

    def test_external_vanilla_and_duplicate_units_are_not_certified(self):
        with tempfile.TemporaryDirectory(prefix='tgc-contract-', dir=Path(__file__).parent) as td:
            root = Path(td); w = self.fixture(root)
            inv = runtime.compose_runtime(root, 'Core', 'Late')
            self.assertTrue(any('vanilla fallback' in b for b in inv.boundaries))
            w('Late/units/other.txt', 'actual_id = {}')
            with self.assertRaises(p.ScriptError): runtime.unit_definitions(runtime.compose_runtime(root, 'Core', 'Late'), root)

    def test_full_auditor_uses_sources_not_empty_scan_list_or_unit_filename(self):
        with tempfile.TemporaryDirectory(prefix='tgc-contract-',dir=Path(__file__).parent) as td:
            root=Path(td).resolve();w=self.fixture(root)
            w('Core/common/goods.txt','military = { steel = { cost = 10 } }')
            w('Core/common/production_types.txt','factory = { output_goods = steel }')
            w('Core/units/different_filename.txt','actual_id = { type = land attack = 1 build_time = 90 default_organisation = 30 discipline = 1 supply_consumption = .5 build_cost = { steel = 2 } supply_cost = { steel = .1 } }')
            w('Core/inventions/retained.txt','I = { effect = { actual_id = { attack = 2 supply_consumption = .25 } } }')
            rules={'units':{'actual_id':{'unit_file':'missing.txt','monitored_stats':{'attack':{'final_range':{'min':0,'max':2}},'supply_consumption':{}}}},
                   'files':{},'scan_files':[],'monitored_stat_catalog':['attack','supply_consumption'],'milestone_years':[1900], 'economic':{'key_goods':['steel']}}
            o=io.StringIO()
            with patch.object(a,'ROOT',root),patch.object(p,'ROOT',root),patch.object(a,'read_rules',return_value=rules),patch.object(sys,'argv',['audit','--core-root','Core','--timeline-root','Late','--json']),contextlib.redirect_stdout(o):
                code=a.main()
            self.assertEqual(code,0,o.getvalue()[:1000]);rows=json.loads(o.getvalue())
            warning, = [d for d in rows if d['code'] == 'final_range']
            self.assertEqual((warning['level'], warning['basis'], warning['engine']),
                             ('WARN', 'legacy_unvalidated', 'raw_script'))
            projection=next(d for d in rows if d['code']=='engine_projection')
            self.assertIn('raw_script_all_effects=3',projection['message'])
            self.assertEqual(projection['source'],'Core/units/different_filename.txt')
            conditional=next(d for d in rows if d['code']=='conditional_supply_index')
            self.assertIn('baseline=0.5, all_effects=0.75',conditional['message'])
            self.assertIn('legacy ranges NOT applied',conditional['message'])


class EngineFixtures(unittest.TestCase):
    def test_applied_ignored_unsupported_unverified_are_distinct(self):
        for context, key, expected in [('base','max_strength','ignored'),('base','limit_per_port','ignored'),
                                       ('modifier','max_strength','unsupported'),('modifier','hull','applied'),
                                       ('base','future_stat','unsupported')]:
            with self.subTest(context=context,key=key):
                self.assertEqual(semantics.property_evidence(key, '3', context, semantics.ALICE).status, expected)
                self.assertEqual(semantics.property_evidence(key, '3', context, semantics.V2).status, 'unverified')

    def test_integer_prefix_matches_pinned_parser_not_float_arithmetic(self):
        for raw, expected in [('2.5',2.),('0.5',0.),('-2.5',-2.),('3',3.)]:
            self.assertEqual(semantics.property_evidence('default_organisation',raw,'modifier',semantics.ALICE).value,expected)
        for raw in ['.5','+2']:
            self.assertEqual(semantics.property_evidence('build_time',raw,'base',semantics.ALICE).status,'invalid')
        self.assertEqual(semantics.property_evidence('attack','2.5','modifier',semantics.ALICE).value,2.5)
        self.assertEqual(semantics.property_evidence('attack','2e3','modifier',semantics.ALICE).status,'unverified')

    def test_alias_projection_does_not_assert_v2_support(self):
        self.assertEqual(semantics.property_evidence('defense','7','modifier',semantics.ALICE).value,7.)
        self.assertIsNone(semantics.property_evidence('defense','7','modifier',semantics.V2).value)

    def test_projection_uses_applied_values_and_never_ignored_base(self):
        x=[{'stat':'default_organisation','value':2.5,'raw_value':'2.5'}]
        out=semantics.projected_stat('30','default_organisation',x,semantics.ALICE)
        self.assertEqual(out['final'],32.)
        self.assertIsNone(semantics.projected_stat('123','max_strength',[],semantics.ALICE)['final'])
        self.assertIsNone(semantics.projected_stat('30','default_organisation',x,semantics.V2)['final'])

    def test_outside_projection_contract_is_not_guessed(self):
        self.assertEqual(semantics.property_evidence('icon','1','base',semantics.ALICE).numeric_type,'integer')
        self.assertEqual(semantics.property_evidence('active','yes','base',semantics.ALICE).status,'non_numeric')
        self.assertEqual(semantics.property_evidence('attack','9'*100,'base',semantics.ALICE).status,'unverified')
        self.assertEqual(semantics.property_evidence('default_organisation',str(2**40),'base',semantics.ALICE).status,'unverified')
        x=[{'stat':'attack','value':2000.,'raw_value':'2e3'}]
        projected=semantics.projected_stat('1','attack',x,semantics.ALICE)
        self.assertEqual((projected['status'],projected['final'],projected['excluded']),('applied_subset',1.,1))
        with self.assertRaises(ValueError):semantics.property_evidence('attack','2','bad',semantics.ALICE)


class DiagnosticFixtures(unittest.TestCase):
    def test_classification_grouping_and_focus_do_not_parse_prose(self):
        r=Reporter()
        for code in ['single_delta','milestone_range','final_range']:
            r.add('WARN','arbitrary unrelated prose',code=code,category='numeric_rule',unit='tank',stat='attack',cause='raw_progression',evidence='unvalidated_rule')
        r.add('INFO','overlap',code='indeterminate',category='evidence_gap',cause='temporal_indeterminacy')
        r.add('WARN','engine problem',code='ignored',category='engine_semantics',engine=semantics.ALICE)
        r.add('FAIL','bad data',code='bad_input',category='integrity')
        o=io.StringIO()
        with contextlib.redirect_stdout(o):r.summary()
        self.assertIn('numeric_rule: 1 cause group(s)',o.getvalue())
        self.assertEqual(o.getvalue().split('RECOMMENDED PLAYTEST FOCUS')[1].count('tank attack:'),1)
        rows=json.loads(r.json());self.assertEqual(rows[0]['stat'],'attack')
        self.assertEqual(rows[3]['category'],'evidence_gap')

    def test_engine_cause_groups_across_units_and_global_gaps_stay_visible(self):
        r=Reporter()
        for unit in ['tank','infantry','artillery']:
            r.add('WARN','ignored field',code='base_semantics',category='engine_semantics',engine=semantics.ALICE,unit=unit,stat='max_strength',cause='max_strength')
        for index in range(12):
            r.add('INFO','overlap',code='uncertain',category='evidence_gap',unit=str(index),stat='attack')
        r.add('INFO','V2 UNKNOWN',code='v2_unknown',category='evidence_gap',engine=semantics.V2)
        o=io.StringIO()
        with contextlib.redirect_stdout(o):r.summary()
        self.assertIn('engine_semantics: 1 cause group(s)',o.getvalue())
        self.assertIn('named_units=3',o.getvalue())
        self.assertIn('V2 UNKNOWN',o.getvalue())

    def test_empty_focus_and_bad_diagnostic_contract(self):
        r=Reporter();o=io.StringIO()
        with contextlib.redirect_stdout(o):r.summary()
        self.assertIn('No qualified',o.getvalue())
        with self.assertRaises(ValueError):r.add('PASS','not a verdict')


class IndependentRuntimeCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reference selection uses filesystem names and the separate stack reader,
        # never read_rules(), compose_runtime(), or the production unit parser.
        cls.effective={}
        for directory in ['technologies','inventions','units']:
            by_name={}
            for layer in ['TGC','TGC_Timeline_1966']:
                for file in (ROOT/layer/directory).glob('*.txt'):by_name[file.name]=file.relative_to(ROOT).as_posix()
            cls.effective[directory]=sorted(by_name.values())
        cls.domains={};cls.fields={}
        for file in cls.effective['units']:
            _,ss=independent_inventory((ROOT/file).read_text(encoding='utf-8-sig'))
            for path,key,value,_,_ in ss:
                if len(path)==1:
                    if key=='type':cls.domains[path[0]]=value
                    if key in CATALOG:cls.fields.setdefault(path[0],set()).add(key)
        cls.scopes={'army_base':{u for u,d in cls.domains.items() if d=='land'},'navy_base':{u for u,d in cls.domains.items() if d=='naval'}}

    def oracle(self, files):
        out=Counter();physical=set()
        for file in files:
            _,ss=independent_inventory((ROOT/file).read_text(encoding='utf-8-sig'))
            for path,stat,value,line,col in ss:
                if ('/technologies/' in file and len(path)!=2) or ('/inventions/' in file and (len(path)!=3 or path[1]!='effect')):continue
                targets={path[-1]} if path[-1] in self.domains else self.scopes.get(path[-1],set())
                for unit in targets:
                    if stat in self.fields[unit]:
                        out[(unit,stat,float(value),path[-1],file,line,col,path[0])]+=1
                        physical.add((file,line,col))
        return out,physical

    def test_effective_source_inventory_independent_of_rules(self):
        inv=runtime.compose_runtime(ROOT)
        for directory in ['technologies','inventions','units']:
            self.assertEqual(sorted(inv.files(directory)),self.effective[directory])
        self.assertIn('TGC/inventions/army_inventions.txt',inv.files('inventions'))
        self.assertNotIn('TGC/inventions/navy_inventions.txt',inv.files('inventions'))

    def test_each_core_army_occurrence_and_expansion_is_reconciled(self):
        file='TGC/inventions/army_inventions.txt'
        files=self.effective['technologies']+self.effective['inventions']
        timing=a.build_year_inference(files)
        found=a.parse_effect_unit_assignments(file,set(self.domains),CATALOG,timing,self.scopes)
        actual=Counter(effect_identity(u,x) for u,items in found.items() for x in items if x['stat'] in self.fields[u])
        expected,physical=self.oracle([file])
        self.assertEqual(actual,expected)
        # Observed corpus checkpoints, never production constants.
        self.assertEqual((len(physical),sum(expected.values())),(389,969))
        self.assertEqual({key[0] for key in expected},self.scopes['army_base'])
        self.assertEqual(timing['invention','military_aviation'].not_before,1914)

    def test_all_effects_no_shadow_duplicates(self):
        files=self.effective['technologies']+self.effective['inventions'];timing=a.build_year_inference(files)
        actual=Counter()
        for file in files:
            for unit,items in a.parse_effect_unit_assignments(file,set(self.domains),CATALOG,timing,self.scopes).items():
                actual.update(effect_identity(unit,x) for x in items if x['stat'] in self.fields[unit])
        expected,_=self.oracle(files)
        self.assertEqual(actual,expected)
        # No frozen count target: scoped transport-time fixes change the corpus.
        # Identity-by-identity comparison above remains the independent oracle.

    def test_twelve_fractional_origins_and_134_contributions(self):
        files=self.effective['technologies']+self.effective['inventions'];timing=a.build_year_inference(files)
        origins=set();expanded=0;legacy_origins=set();legacy_expanded=0
        for file in files:
            for unit,items in a.parse_effect_unit_assignments(file,set(self.domains),CATALOG,timing,self.scopes).items():
                for x in items:
                    if x['stat']=='default_organisation' and x['value']!=int(x['value']):
                        origins.add((file,x['line'],x['column']));expanded+=1
                        if file != 'TGC/inventions/army_inventions.txt':
                            legacy_origins.add((file,x['line'],x['column']));legacy_expanded+=1
                        self.assertEqual(semantics.property_evidence(x['stat'],x['raw_value'],'modifier',semantics.ALICE).value,float(int(x['value'])))
        self.assertEqual((len(legacy_origins),legacy_expanded),(12,134))
        self.assertEqual((len(origins),expanded),(22,244))

    def test_structured_report_cross_process_determinism_and_categories(self):
        reports=[]
        code='''import sys
sys.path.insert(0,'TGC/tools')
import audit_1966_balance as a
from lib_1966_runtime import RuntimeInventory
original=RuntimeInventory.files
if sys.argv[1]=='reverse': RuntimeInventory.files=lambda self,d:list(reversed(original(self,d)))
sys.argv=['audit','--json']
raise SystemExit(a.main())'''
        for seed,order in [('0','normal'),('42','reverse')]:
            x=subprocess.run([sys.executable,'-B','-c',code,order],cwd=ROOT,env=dict(os.environ,PYTHONHASHSEED=seed),capture_output=True,text=True)
            self.assertEqual(x.returncode,0,x.stderr or x.stdout[:1000]);reports.append(x.stdout)
        self.assertEqual(reports[0],reports[1]);rows=json.loads(reports[0])
        self.assertFalse(any(d['level']=='FAIL' for d in rows))
        for category in ['source_scope','engine_semantics','evidence_gap','numeric_rule','economic_index']:
            self.assertTrue(any(d['category']==category for d in rows),category)
        self.assertTrue(all(d['category']!='observation' for d in rows if d['level']=='WARN'))
        self.assertTrue(all(d['evidence']=='unvalidated_rule' for d in rows if d['category']=='numeric_rule'))
        self.assertFalse(any('coverage is good' in d['message'] or 'high-confidence coverage' in d['message'] for d in rows))
        indexes=[d for d in rows if d['code']=='conditional_supply_index']
        self.assertEqual(len(indexes),23)
        self.assertTrue(all('legacy ranges NOT applied' in d['message'] for d in indexes))


if __name__ == '__main__':
    unittest.main()
