"""Independent transition oracles for persistent inventions (Alice 1.3.0).

Expected states and supply are computed without the production dependency,
condition or closure helpers. No fixture changes runtime data.
"""
import itertools
import json
import os
from pathlib import Path
import random
import sys
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'TGC/tools'))
import lib_1966_parser as parser
from lib_1966_functional import ResearchDependencies
from lib_1966_mechanics import report_consumers
from lib_1966_diagnostics import Reporter


def model(tech='', inventions='', *, reverse=False):
    sources = {'fixture/technologies/t.txt': tech, 'fixture/inventions/i.txt': inventions}
    with patch.object(parser, 'read_text', side_effect=lambda f, **kw: sources[f]):
        return ResearchDependencies(list(reversed(sources)) if reverse else list(sources))


def supply(base, rows):
    return dict(status='applied', baseline=base, final=base + sum(v for _, _, v in rows),
                superseded=[], base_superseded=[], assignments=[
                    dict(source_file=f'fixture/{"technologies" if k == "technology" else "inventions"}/x.txt',
                         invention=n, value=v) for k, n, v in rows])


def finding(d, q):
    r = Reporter()
    report_consumers({'u': dict(unit_type='infantry', unit_domain='land')},
                     {'u': {'stats': {'supply_consumption': q}}}, r, d)
    return next(x for x in r.diagnostics if x.code == 'consumer_domain')


def independent_paths(requirements):
    """Tiny exhaustive sequence oracle; keeps all orders, unlike production BFS."""
    result = {frozenset(): ()}
    def visit(state, path):
        for name, eligible in requirements.items():
            if name not in state and eligible(state):
                nxt = state | {name}
                result.setdefault(nxt, path + (name,))
                visit(nxt, path + (name,))
    visit(frozenset(), ())
    return result


class TemporalSupply(unittest.TestCase):
    PAIR = ('A={limit={NOT={invention=B}} chance={base=3}} '
            'B={limit={invention=A} chance={base=3}}')

    def test_task30_counterexample_keeps_acquired_A_and_warning(self):
        paths = independent_paths({'A': lambda s: 'B' not in s, 'B': lambda s: 'A' in s})
        self.assertEqual(paths[frozenset({'A', 'B'})], ('A', 'B'))
        self.assertNotIn(('B', 'A'), paths.values())
        expected = min(1.5 - len(s) for s in paths)
        self.assertEqual(expected, -.5)
        d = model(inventions=self.PAIR)
        q = supply(1.5, [('invention', 'A', -1), ('invention', 'B', -1)])
        self.assertAlmostEqual(d.lower_bound(q)['lower_bound'], expected)
        self.assertEqual(finding(d, q).level, 'WARN')
        r = d.acquisition_path({('invention', 'A'), ('invention', 'B')})
        self.assertEqual(r['status'], 'possibly_reachable')
        self.assertEqual(r['sequence'], [('invention', 'A'), ('invention', 'B')])
        self.assertEqual(d.lower_bound(q)['witness']['value'], -.5)

    def test_negative_invention_before_later_technology(self):
        d = model('T={area=x year=1900}',
                  'A={limit={NOT={T=1}} chance={base=3}}')
        r = d.acquisition_path({('technology', 'T'), ('invention', 'A')})
        self.assertEqual(r['sequence'], [('invention', 'A'), ('technology', 'T')])
        q = supply(.5, [('invention', 'A', -1), ('technology', 'T', .1)])
        self.assertEqual(finding(d, q).level, 'WARN')

    def test_real_mutual_exclusion_and_positive_cycles(self):
        cases = ['A={limit={NOT={invention=B}} chance={base=3}} '
                 'B={limit={NOT={invention=A}} chance={base=3}}',
                 'A={limit={invention=B} chance={base=3}} '
                 'B={limit={invention=A} chance={base=3}}']
        for text in cases:
            d = model(inventions=text)
            self.assertEqual(d.acquisition_path({('invention', 'A'), ('invention', 'B')})['status'],
                             'proven_unreachable')
            # Reachability rejection must never tighten the positive-only bound.
            self.assertEqual(d.lower_bound(supply(1.5, [('invention', 'A', -1),
                                                       ('invention', 'B', -1)]))['lower_bound'], -.5)

    def test_simultaneous_contradiction_and_self_not(self):
        d = model(inventions='A={limit={invention=A NOT={invention=A}} chance={base=3}}')
        self.assertEqual(d.acquisition_path({('invention', 'A')})['status'], 'proven_unreachable')
        d = model(inventions='A={limit={NOT={invention=A}} chance={base=3}}')
        self.assertEqual(d.acquisition_path({('invention', 'A')})['status'], 'possibly_reachable')

    def test_forced_positive_chain_and_whole_owner_effects(self):
        d = model('P={area=x year=1900} T={area=x year=1910}',
                  'A={limit={T=1} chance={base=3}}')
        q = supply(.2, [('technology', 'P', .6), ('technology', 'T', .3),
                         ('invention', 'A', -.7), ('invention', 'A', .1)])
        self.assertAlmostEqual(d.lower_bound(q)['lower_bound'], .2)
        self.assertEqual(finding(d, q).level, 'INFO')
        self.assertEqual(d.acquisition_path({('invention', 'A')})['sequence'],
                         [('technology', 'P'), ('technology', 'T'), ('invention', 'A')])

    def test_or_alternative_is_included_even_if_not_necessary(self):
        d = model(inventions='A={limit={invention=B} chance={base=3}} '
                  'B={limit={OR={invention=A invention=C}} chance={base=3}} '
                  'C={chance={base=3}}')
        r = d.acquisition_path({('invention', 'A')})
        self.assertEqual(r['sequence'], [('invention', 'C'), ('invention', 'B'), ('invention', 'A')])

    def test_unknown_conditions_and_chance_never_exclude_paths(self):
        for body in ['limit={tag=ABC} chance={base=3}',
                     'limit={any_country={invention=A}} chance={base=3}',
                     'limit={year=1966} chance={base=3}',
                     'chance={base=3 modifier={factor=2 year=1966}}']:
            d = model(inventions='A={' + body + '}')
            self.assertEqual(d.acquisition_path({('invention', 'A')})['status'], 'unknown')
            q = supply(.2, [('invention', 'A', -.5)])
            self.assertLess(d.lower_bound(q)['lower_bound'], 0)
            self.assertEqual(finding(d, q).level, 'WARN')

    def test_probability_conditions_are_not_eligibility_prerequisites(self):
        d = model('T={area=x year=1966}',
                  'A={chance={base=3 modifier={factor=2 T=1}}}')
        self.assertEqual(d.required['invention', 'A'], set())
        self.assertEqual(d.acquisition_path({('invention', 'A')})['status'], 'unknown')
        self.assertEqual(d.lower_bound(supply(.2, [('invention', 'A', -.5)]))['lower_bound'], -.3)
        # A constant sub-one chance is rounded to zero in the pinned consumer.
        for chance in ['0', '0.5']:
            d = model(inventions='A={chance={base=' + chance + '}}')
            self.assertEqual(d.acquisition_path({('invention', 'A')})['status'], 'proven_unreachable')

    def test_inexact_chance_conversion_cannot_prove_impossibility(self):
        for raw in ['0.99999999', '2147483647', '0.1']:
            d = model(inventions='A={chance={base=' + raw + '}}')
            self.assertEqual(d.acquisition_path({('invention', 'A')})['status'], 'unknown')
            self.assertEqual(finding(d, supply(.2, [('invention', 'A', -.5)])).level, 'WARN')

    def test_kleene_unknown_does_not_poison_known_or_or_false_and(self):
        d = model(inventions='A={limit={OR={NOT={invention=A} tag=ABC}} chance={base=3}}')
        self.assertEqual(d.acquisition_path({('invention', 'A')})['status'], 'possibly_reachable')
        d = model(inventions='A={limit={invention=A tag=ABC} chance={base=3}}')
        self.assertEqual(d.acquisition_path({('invention', 'A')})['status'], 'proven_unreachable')

    def test_limits_are_unknown_and_cannot_declassify(self):
        d = model(inventions=self.PAIR)
        q = supply(1.5, [('invention', 'A', -1), ('invention', 'B', -1)])
        for kwargs in [dict(max_states=1), dict(max_definitions=1)]:
            self.assertEqual(d.acquisition_path({('invention', 'B')}, **kwargs)['status'], 'unknown')
        r = d.lower_bound(q, max_states=1)
        self.assertEqual(r['temporal_search']['status'], 'unknown')
        self.assertEqual(r['lower_bound'], -.5)
        self.assertEqual(d.lower_bound(q, max_negative_owners=0)['status'], 'unverified')

    def test_independent_inventions_merge_equivalent_orders(self):
        text = ' '.join(f'{n}={{chance={{base=3}}}}' for n in 'ABCD')
        d = model(inventions=text)
        r = d.acquisition_path({('invention', n) for n in 'ABCD'})
        self.assertEqual(r['status'], 'possibly_reachable')
        self.assertLessEqual(r['visited_states'], 16)  # 2**4 states, not 4! paths
        self.assertEqual(r, model(inventions=text, reverse=True).acquisition_path(
            {('invention', n) for n in 'DCBA'}))

    def test_search_and_bound_are_deterministic_across_process_seeds_and_file_order(self):
        script = '''
import json,sys
sys.path.insert(0,'tools/tests')
from test_1966_temporal import model,supply,TemporalSupply
d=model(inventions=TemporalSupply.PAIR,reverse=sys.argv[1]=='reverse')
q=supply(1.5,[('invention','A',-1),('invention','B',-1)])
print(json.dumps([d.lower_bound(q),d.acquisition_path({('invention','A'),('invention','B')})],sort_keys=True))
'''
        outputs = []
        for seed, order in [('1', 'forward'), ('731', 'reverse'), ('31415', 'forward')]:
            r = subprocess.run([sys.executable, '-B', '-c', script, order], cwd=ROOT,
                               env=dict(os.environ, PYTHONHASHSEED=seed), capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0, r.stderr)
            outputs.append(json.loads(r.stdout))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], outputs[2])

    def test_direct_bad_base_stays_fail_and_bound_needs_explicit_proof(self):
        d = model(inventions='A={chance={base=3}}')
        self.assertEqual(finding(d, supply(-.1, [('invention', 'A', 1)])).level, 'FAIL')
        class Unproved:
            def lower_bound(self, q):
                return dict(status='conditional_bound', lower_bound=10, reachability='unverified')
        self.assertEqual(finding(Unproved(), supply(.1, [('invention', 'A', -1)])).level, 'WARN')

    def test_small_generated_graphs_against_independent_sequence_oracle(self):
        rng = random.Random(31030)
        # Exhaustive tiny sequences include positive/negative cycles and disjunctions.
        for _ in range(40):
            rules = {n: (rng.choice(['and', 'or', 'not']), rng.choice('ABC'), rng.choice('ABC'))
                     for n in 'ABC'}
            def eligible(rule, state):
                op, a, b = rule
                return ((a in state and b in state) if op == 'and' else
                        (a in state or b in state) if op == 'or' else
                        (a not in state and b not in state))
            paths = independent_paths({n: lambda s, rule=r: eligible(rule, s) for n, r in rules.items()})
            text = ' '.join(f'{n}={{limit={{{op.upper()}={{invention={a} invention={b}}}}} chance={{base=3}}}}'
                            for n, (op, a, b) in rules.items())
            d = model(inventions=text)
            for mask in itertools.product([False, True], repeat=3):
                names = {n for n, on in zip('ABC', mask) if on}
                expected = any(names <= s for s in paths)
                r = d.acquisition_path({('invention', n) for n in names})
                self.assertEqual(r['status'], 'possibly_reachable' if expected else 'proven_unreachable', rules)
            effects = {n: rng.choice([-.8, -.3, .2, .9]) for n in 'ABC'}
            actual_min = min(.5 + sum(effects[n] for n in s) for s in paths)
            bound = d.lower_bound(supply(.5, [('invention', n, v) for n, v in effects.items()]))
            self.assertLessEqual(bound['lower_bound'], actual_min + 1e-12)
            if actual_min < 0:
                self.assertEqual(finding(d, supply(.5, [('invention', n, v) for n, v in effects.items()])).level,
                                 'WARN')


if __name__ == '__main__':
    unittest.main()
