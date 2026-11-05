"""Independent regression evidence for the 1966 analysis tools (no runtime writes)."""
from __future__ import annotations

from collections import Counter
import contextlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "TGC/tools"))
import lib_1966_parser as p
import validate_1966_extension as v
import audit_1966_balance as a


def independent_inventory(text):
    """Regex token stream + explicit stack, independent of the production lexer/tree.

    Returns every named group and scalar with its full ancestor path and position.
    The oracle is intentionally limited to the balanced, annotated input corpus;
    malformed-input acceptance is tested against explicit expectations separately.
    """
    pattern = re.compile(r'#[^\n]*|"[^"\r\n]*"|\'[^\'\r\n]*\'|[{}]|[<>=!]+|[^\s{}<>=!#,;]+')
    tokens = [(m.group(), text.count("\n", 0, m.start()) + 1,
               m.start() - text.rfind("\n", 0, m.start()))
              for m in pattern.finditer(text) if not m.group().startswith("#")]
    stack, groups, scalars = [], [], []
    i = 0
    while i < len(tokens):
        value, line, column = tokens[i]
        if value == "}":
            if not stack:
                raise AssertionError("oracle: extra close")
            stack.pop()
            i += 1
        elif value == "{":
            stack.append(None)
            i += 1
        elif i + 2 < len(tokens) and tokens[i + 1][0] in {"=", "<", ">", "<=", ">=", "!=", "==", "<>"}:
            rhs = tokens[i + 2][0]
            name = value.strip("\"'")
            if rhs == "{":
                groups.append((tuple(stack), name, line, column))
                stack.append(name)
            else:
                scalars.append((tuple(stack), name, rhs.strip("\"'"), line, column))
            i += 3
        else:
            i += 1
    if stack:
        raise AssertionError("oracle: unclosed group")
    return groups, scalars


def real_inputs():
    manifest = json.loads((ROOT / v.MANIFEST_PATH).read_text(encoding="utf-8"))
    rules = json.loads((ROOT / "TGC/tools/1966_balance_rules.json").read_text(encoding="utf-8"))
    return manifest, rules


def oracle_effects(rules, overrides=None):
    """No production parser, unit reader, or effect reader supplies expected data."""
    domains = {}
    for unit, cfg in rules["units"].items():
        _, scalars = independent_inventory((ROOT / cfg["unit_file"]).read_text(encoding="utf-8"))
        domains[unit] = next(value for path, key, value, _, _ in scalars if path == (unit,) and key == "type")
    scopes = {"army_base": {u for u, d in domains.items() if d == "land"},
              "navy_base": {u for u, d in domains.items() if d == "naval"}}
    expected = Counter()
    for file in rules["scan_files"]:
        text = overrides[file] if overrides and file in overrides else (ROOT / file).read_text(encoding="utf-8")
        _, scalars = independent_inventory(text)
        for path, stat, raw, line, column in scalars:
            if "/technologies/" in file:
                if len(path) != 2:
                    continue
            elif len(path) != 3 or path[1] != "effect":
                continue
            owner, scope = path[0], path[-1]
            targets = {scope} if scope in domains else scopes.get(scope, set())
            for unit in targets:
                if stat in rules["units"][unit]["monitored_stats"]:
                    expected[(unit, stat, float(raw), scope, file, line, column, owner)] += 1
    return expected, scopes


def effect_identity(unit, item):
    return (unit, item["stat"], item["value"], item["scope_key"], item["source_file"],
            item["line"], item["column"], item["invention"])


class StructuralTests(unittest.TestCase):
    def test_oracle_annotated_sample(self):
        groups, scalars = independent_inventory('# {\nIBRD = { effect = { infantry = { attack = 2 } } }')
        self.assertEqual(groups, [((), "IBRD", 2, 1), (("IBRD",), "effect", 2, 10),
                                  (("IBRD", "effect"), "infantry", 2, 21)])
        self.assertEqual(scalars, [(("IBRD", "effect", "infantry"), "attack", "2", 2, 34)])

    def test_layout_comments_quotes_and_positions(self):
        text = '# {\nIBRD\n= { area = "army}#doctrine" year = 1936 } # }\nIDA = {}'
        doc = p.parse_script(text, file="fixture")
        self.assertEqual([n.key for n in doc.definitions], ["IBRD", "IDA"])
        first = doc.definitions[0]
        self.assertEqual((first.start.line, first.start.column), (2, 1))
        self.assertEqual(p.scalar(first, "area"), "army}#doctrine")
        self.assertEqual(p.scalar(first, "year"), "1936")

    def test_duplicates_preserved(self):
        doc = p.parse_script("x = { year = 1900 } x = { year = 1960 }")
        self.assertEqual([p.scalar(n, "year") for n in doc.definitions], ["1900", "1960"])

    def test_nested_metadata_not_promoted(self):
        text = 'x = { ai_chance = { modifier = { year = 1945 } } area = army_doctrine year = 1936 }'
        with patch.object(p, "read_text", return_value=text):
            meta = p.parse_top_level_block_meta("fixture")
        self.assertEqual((meta[0]["area"], meta[0]["year"]), ("army_doctrine", 1936))

    def test_schema_keyword_case_does_not_change_identifier_case(self):
        with patch.object(p, "read_text", return_value='IBRD = { AREA = Army YEAR = 1936 }'):
            meta = p.parse_top_level_block_meta('fixture')
        self.assertEqual((meta[0]['key'], meta[0]['area'], meta[0]['year']), ('IBRD', 'Army', 1936))
        with patch.object(p, "read_text", return_value='x = { year = 1936 YEAR = 1945 }'):
            with self.assertRaises(p.ScriptError):
                p.parse_top_level_block_meta('fixture')

    def test_missing_metadata_explicit_none(self):
        with patch.object(p, "read_text", return_value="x = { limit = { year = 1945 } }"):
            meta = p.parse_top_level_block_meta("fixture")
        self.assertIsNone(meta[0]["area"])
        self.assertIsNone(meta[0]["year"])

    def test_ambiguous_metadata_rejected(self):
        for text in ["x = { year = 1900 year = 1900 }", "x = { area = a area = b }", "x = { year = bad }"]:
            with self.subTest(text=text), patch.object(p, "read_text", return_value=text):
                with self.assertRaises(p.ScriptError):
                    p.parse_top_level_block_meta("fixture")

    def test_malformed_never_returns_partial_document(self):
        for text in ["x = {", "x = { y = { }", "x = { }}", "} x = {}", 'x = { y = "open\n }', "x ="]:
            with self.subTest(text=text), self.assertRaises(p.ScriptError):
                p.parse_script(text, file="malformed")

    def test_free_list_values_are_preserved(self):
        doc = p.parse_script("x = { values = { 1 2 3 } date > 1900 }")
        self.assertEqual([n.value for n in doc.definitions[0].children[0].children], ["1", "2", "3"])
        self.assertEqual(doc.definitions[0].children[1].operator, ">")

    def test_encoding_strict_and_explicit(self):
        # BytesIO avoids machine-specific temporary-directory permissions.
        with patch.object(Path, "read_bytes", return_value=b'al\xffpha = {}'):
            with self.assertRaises(p.ScriptError):
                p.read_text("fixture")
            self.assertEqual(p.read_text("fixture", encoding="cp1252"), "alÿpha = {}")

    def test_encoding_markers_and_identifiers_are_not_lost(self):
        for raw in [b'\xff\xfeX\x00', b'caf\xe9 = {}']:
            with self.subTest(raw=raw), patch.object(Path, "read_bytes", return_value=raw):
                with self.assertRaises(p.ScriptError):
                    p.read_text("fixture")
        with patch.object(Path, "read_bytes", return_value=b'\xef\xbb\xbfIBRD = {}'):
            self.assertEqual(p.parse_file("fixture").definitions[0].key, "IBRD")
        doc = p.parse_script('café-name = {}')
        self.assertEqual(doc.definitions[0].key, "café-name")

    def test_excessive_nesting_is_an_explicit_error(self):
        with self.assertRaises(p.ScriptError):
            p.parse_script('x = {' * 2000 + '}' * 2000)

    def test_bom_and_unrecognised_top_level(self):
        self.assertEqual(p.parse_script('\ufeffIBRD = {}').definitions[0].key, "IBRD")
        for text in ["garbage x = {}", "year = 1900", "{ x = {} }", "x\x00 = {}"]:
            with self.subTest(text=text), self.assertRaises(p.ScriptError):
                p.parse_script(text).definitions


class ValidatorTests(unittest.TestCase):
    def run_validator(self, changes):
        original = p.read_text
        def read(file, encoding="utf-8"):
            return changes[file] if file in changes else original(file, encoding=encoding)
        out = io.StringIO()
        with patch.object(p, "read_text", side_effect=read), patch.object(v, "read_text", side_effect=read), \
                patch.object(sys, "argv", ["validator"]), contextlib.redirect_stdout(out):
            code = v.main()
        return code, out.getvalue()

    def test_current_baseline(self):
        code, out = self.run_validator({})
        self.assertEqual(code, 0, out)
        self.assertIn("parsed inventions in tracked files: 232", out)

    def test_no_false_pass_on_syntax_or_duplicates(self):
        manifest, _ = real_inputs()
        file = manifest["tech_tree"]["branches"][0]["file"]
        text = (ROOT / file).read_text(encoding="utf-8")
        for addition in ["\n}", "\nprobe = {", "\npost_napoleonic_thought = { area = army_doctrine year = 1836 }"]:
            with self.subTest(addition=addition):
                code, out = self.run_validator({file: text + addition})
                self.assertEqual(code, 1, out)
                self.assertNotIn("OK:", out)

    def test_no_false_pass_on_missing_or_ambiguous_metadata(self):
        manifest, _ = real_inputs()
        file = manifest["tech_tree"]["branches"][0]["file"]
        text = (ROOT / file).read_text(encoding="utf-8")
        for block in ["probe = {}", "probe = { area = invented }", "probe = { area = army_doctrine year = 1960 year = 1966 }"]:
            with self.subTest(block=block):
                code, out = self.run_validator({file: text + "\n" + block})
                self.assertEqual(code, 1, out)

    def test_uppercase_localisation_checked(self):
        manifest, _ = real_inputs()
        changes = {}
        keys = {"IBRD", "IBRD_desc", "IDA", "IDA_desc"}
        for file in manifest["localisation_files"]:
            changes[file] = "\n".join(line for line in (ROOT / file).read_text(encoding="latin-1").splitlines()
                                      if line.split(";", 1)[0] not in keys)
        code, out = self.run_validator(changes)
        self.assertEqual(code, 1, out)
        for key in keys:
            self.assertIn(key, out)

    def test_duplicates_across_files_and_uppercase_inventions(self):
        manifest, _ = real_inputs()
        file = manifest["tech_tree"]["branches"][1]["file"]
        text = (ROOT / file).read_text(encoding="utf-8")
        code, out = self.run_validator({file: text + '\npost_napoleonic_thought = { area = army_doctrine year = 1836 }'})
        self.assertEqual(code, 1, out)
        self.assertIn('TECH duplicate definition for post_napoleonic_thought', out)
        file = 'TGC_Timeline_1966/inventions/NEW_commerce_inventions.txt'
        text = (ROOT / file).read_text(encoding="utf-8")
        code, out = self.run_validator({file: text + '\nIBRD = { limit = { year = 1944 } }'})
        self.assertEqual(code, 1, out)
        self.assertIn('INVENTION duplicate definition for IBRD', out)

    def test_layout_only_change_keeps_pass(self):
        manifest, _ = real_inputs()
        file = manifest["tech_tree"]["branches"][0]["file"]
        text = (ROOT / file).read_text(encoding="utf-8")
        text = text.replace("post_napoleonic_thought = {", "post_napoleonic_thought\n=\n{")
        code, out = self.run_validator({file: text})
        self.assertEqual(code, 0, out)


class DatingTests(unittest.TestCase):
    TECH = "fixture/technologies/tree.txt"
    INV = "fixture/inventions/tree.txt"

    def infer(self, tech, inventions, order=None):
        files = {self.TECH: tech, self.INV: inventions}
        with patch.object(p, "read_text", side_effect=files.__getitem__):
            return a.build_year_inference(order or list(files))

    def test_chance_years_and_references_are_not_availability_dates(self):
        result = self.infer("early = { area = a year = 1900 } late = { area = a year = 1960 }",
                            "x = { limit = { early = 1 } chance = { modifier = { year = 1950 late = 1 } } }")
        item = result[("invention", "x")]
        self.assertIsNone(item.year)
        self.assertEqual(item.not_before, 1900)
        self.assertEqual(item.probability_years, (1950,))
        self.assertEqual(item.source, "availability_bound")

    def test_incomplete_and_compound_conditions(self):
        tech = "early = { area = a year = 1900 } late = { area = a year = 1960 }"
        inv = '''and_gate = { limit = { early = 1 missing = 1 } }
                 or_gate = { limit = { OR = { early = 1 late = 1 } } }
                 open_or = { limit = { OR = { early = 1 missing = 1 } } }
                 negated = { limit = { NOT = { late = 1 } } }
                 scoped = { limit = { any_neighbor_country = { late = 1 } } }'''
        result = self.infer(tech, inv)
        self.assertEqual(result[("invention", "and_gate")].not_before, 1900)
        self.assertTrue(result[("invention", "and_gate")].notes)
        self.assertEqual(result[("invention", "or_gate")].not_before, 1900)
        for key in ["open_or", "negated", "scoped"]:
            self.assertIsNone(result[("invention", key)].not_before)

    def test_cycles_and_dependency_order(self):
        inv = '''a = { limit = { invention = b } } b = { limit = { invention = a } }
                 final = { limit = { invention = middle late = 1 } }
                 middle = { limit = { early = 1 } }'''
        tech = "early = { area = a year = 1900 } late = { area = a year = 1960 }"
        x = self.infer(tech, inv)
        y = self.infer(tech, inv, [self.INV, self.TECH])
        self.assertEqual(x, y)
        self.assertEqual(x[("invention", "final")].not_before, 1960)
        self.assertIsNone(x[("invention", "a")].not_before)
        self.assertIn("cycle", " ".join(x[("invention", "a")].notes))

    def test_namespace_and_duplicates(self):
        result = self.infer("same = { area = a year = 1900 }", "same = { limit = { same = 1 } }")
        self.assertEqual(len(result), 2)
        with self.assertRaises(p.ScriptError):
            self.infer("same = { area = a year = 1900 } same = { area = a year = 1960 }", "")

    def test_comments_and_layout_do_not_change_dates(self):
        tech = "early = { area = a year = 1900 } late = { area = a year = 1960 }"
        first = self.infer(tech, "x = { limit = { early = 1 } # late = 1\n }")
        second = self.infer(tech, "x\n=\n{ limit =\n{ early = 1\n# { year = 2000 }\n}\n}")
        self.assertEqual(first, second)

    def test_milestone_is_an_envelope_for_uncertain_effects(self):
        items = [{"value": 2., "year": 1900, "not_before": 1900},
                 {"value": 10., "year": None, "not_before": 1950},
                 {"value": -3., "year": None, "not_before": None}]
        self.assertEqual(a.milestone_envelope(5., items, 1940), (4., 7.))
        self.assertEqual(a.milestone_envelope(5., items, 1960), (4., 17.))

    def test_probability_only_and_unknown_dates_stay_unknown(self):
        result = self.infer("", "x = { chance = { modifier = { year = 1945 } } }")
        evidence = result[("invention", "x")]
        self.assertIsNone(evidence.year)
        self.assertIsNone(evidence.not_before)
        self.assertEqual(evidence.probability_years, (1945,))

    def test_reference_uncertainty_not_silently_resolved_by_namespace(self):
        result = self.infer("same = { area = a year = 1900 }",
                            "same = {} x = { limit = { invention = same } }")
        self.assertIsNone(result[("invention", "x")].not_before)
        self.assertIn("ambiguous", " ".join(result[("invention", "x")].notes))

    def test_forward_chains_do_not_freeze_partial_results(self):
        tech = "early = { area = a year = 1900 } late = { area = a year = 1960 }"
        inv = "x = { limit = { early = 1 invention = y } } y = { limit = { late = 1 } }"
        result = self.infer(tech, inv)
        self.assertEqual(result[("invention", "x")].not_before, 1960)
        self.assertEqual(result[("invention", "y")].not_before, 1960)

    def test_logical_keyword_case_and_literal_year_gates(self):
        result = self.infer('', 'x = { LIMIT = { and = { YEAR = 1936 or = { year >= 1950 year > 1960 } } } }')
        self.assertEqual(result[('invention', 'x')].not_before, 1950)
        self.assertIsNone(result[('invention', 'x')].year)
        result = self.infer('year = { area = a year = 1900 }', 'x = { limit = { year = 1 } }')
        self.assertEqual(result[('invention', 'x')].not_before, 1)
        self.assertEqual(result[('invention', 'x')].references, ())


class AuditorTests(unittest.TestCase):
    def test_unmonitored_units_are_distinct_from_unknown_units(self):
        file = 'fixture/technologies/tree.txt'
        timing = {('technology', 'T'): a.YearEvidence(1900, 1900, 'direct')}
        with patch.object(p, 'read_text', return_value='T = { cavalry = { attack = 2 } }'):
            actual = a.parse_effect_unit_assignments(file, {'infantry'}, {'attack'}, timing, {},
                                                    known_units={'infantry', 'cavalry'})
            self.assertEqual(actual, {})
            with self.assertRaises(p.ScriptError):
                a.parse_effect_unit_assignments(file, {'infantry'}, {'attack'}, timing, {}, known_units={'infantry'})
        with patch.object(p, 'read_text', return_value='T = { army_base = { attack = 2 } }'):
            self.assertEqual(a.parse_effect_unit_assignments(file, {'cruiser'}, {'attack'}, timing, {'army_base': set()},
                                                            known_units={'cruiser'}), {})

    def test_no_partial_conclusions_on_structural_input_errors(self):
        _, rules = real_inputs()
        file = rules["scan_files"][0]
        original = p.read_text
        text = original(file)
        for suffix in ["\n}", "\nprobe = {", "\npost_napoleonic_thought = { area = army_doctrine year = 1836 }"]:
            def read(path, encoding="utf-8"):
                return text + suffix if path == file else original(path, encoding=encoding)
            out = io.StringIO()
            with self.subTest(suffix=suffix), patch.object(p, "read_text", side_effect=read), \
                    patch.object(sys, "argv", ["audit"]), contextlib.redirect_stdout(out):
                code = a.main()
                self.assertEqual(code, 1)
                self.assertIn("FAIL: 1", out.getvalue())
                self.assertIn("no partial conclusions", out.getvalue())
                self.assertNotIn("estimated_final", out.getvalue())
                self.assertIn("PRIORITY SUMMARY\n", out.getvalue())

    def test_effects_are_contextual_and_bad_values_are_not_discarded(self):
        file = "fixture/technologies/tree.txt"
        prefix = 'T = { area = a year = 1900 ai_chance = { modifier = { infantry = { attack = 999 } } } '
        timing = {("technology", "T"): a.YearEvidence(1900, 1900, "direct")}
        text = prefix + 'infantry = { attack = 2 } }'
        with patch.object(p, "read_text", return_value=text):
            result = a.parse_effect_unit_assignments(file, {"infantry"}, {"attack"}, timing, {})
        self.assertEqual([n["value"] for n in result["infantry"]], [2.])
        with patch.object(p, "read_text", return_value=prefix + 'infantry = { ATTACK = 3 } }'):
            result = a.parse_effect_unit_assignments(file, {"infantry"}, {"attack"}, timing, {})
        self.assertEqual([(n['stat'], n['value']) for n in result['infantry']], [('attack', 3.)])
        for body in ['attack = 2garbage', 'attack = { value = 2 }', 'orphan attack = 2']:
            with self.subTest(body=body), patch.object(p, "read_text", return_value=prefix + 'infantry = { ' + body + ' } }'):
                with self.assertRaises(p.ScriptError):
                    a.parse_effect_unit_assignments(file, {"infantry"}, {"attack"}, timing, {})

    def test_baselines_and_costs_do_not_depend_on_layout(self):
        text = 'infantry = { type = land attack = 2 build_cost = { steel = 3 } supply_cost = { steel = .1 } }'
        with patch.object(p, "read_text", return_value=text):
            data = a.parse_unit_block("fixture", "infantry")
        self.assertEqual(data["stats"]["attack"], 2.)
        self.assertEqual(data["build_cost"], {"steel": 3.})
        self.assertEqual(data["supply_cost"], {"steel": .1})
        for changed in [text.replace('build_cost = { steel = 3 }', ''),
                        text.replace('steel = 3', 'steel = broken')]:
            with self.subTest(text=changed), patch.object(p, "read_text", return_value=changed):
                with self.assertRaises(p.ScriptError):
                    a.parse_unit_block("fixture", "infantry")


class RealDataTests(unittest.TestCase):
    def test_baselines_and_economic_inputs_match_independent_inventory(self):
        _, rules = real_inputs()
        for unit, cfg in rules["units"].items():
            _, scalars = independent_inventory((ROOT / cfg["unit_file"]).read_text(encoding="utf-8"))
            parsed = a.parse_unit_block(cfg["unit_file"], unit)
            expected_stats = {key: float(value) for path, key, value, _, _ in scalars
                              if path == (unit,) and key in cfg["monitored_stats"]}
            self.assertEqual({s: parsed["stats"][s] for s in cfg["monitored_stats"]}, expected_stats)
            for group in ["build_cost", "supply_cost"]:
                expected = {key: float(value) for path, key, value, _, _ in scalars if path == (unit, group)}
                self.assertEqual(parsed[group], expected, (unit, group))
        _, scalars = independent_inventory((ROOT / rules["files"]["goods"]).read_text(encoding="utf-8"))
        expected_goods = {path[-1]: float(value) for path, key, value, _, _ in scalars if len(path) == 2 and key == "cost"}
        self.assertEqual(a.parse_goods_costs(rules["files"]["goods"]), expected_goods)

    def test_independent_definition_and_metadata_inventory(self):
        manifest, rules = real_inputs()
        tech_files = [b["file"] for b in manifest["tech_tree"]["branches"]]
        files = list(dict.fromkeys(tech_files + manifest["invention_files"] + rules["scan_files"]))
        actual_total = expected_total = 0
        invention_count = 0
        for file in files:
            text = (ROOT / file).read_text(encoding="utf-8")
            groups, scalars = independent_inventory(text)
            expected = [(key, line, col) for path, key, line, col in groups if not path]
            actual = [(n.key, n.start.line, n.start.column) for n in p.parse_file(file).definitions]
            self.assertEqual(actual, expected, file)
            actual_total += len(actual)
            expected_total += len(expected)
            if file in manifest["invention_files"]:
                invention_count += len(actual)
            if file in tech_files:
                direct = {(path[0], key): value for path, key, value, _, _ in scalars
                          if len(path) == 1 and key in {"area", "year"}}
                for meta in p.parse_top_level_block_meta(file):
                    self.assertEqual(meta["area"], direct[(meta["key"], "area")])
                    self.assertEqual(meta["year"], int(direct[(meta["key"], "year")]))
                self.assertEqual(len(actual), 60)
        self.assertEqual((actual_total, expected_total, invention_count), (626, 626, 232))

    def test_effects_individually_match_independent_inventory(self):
        _, rules = real_inputs()
        expected, scopes = oracle_effects(rules)
        self.assertEqual(sum(expected.values()), 2667)
        actual = Counter()
        inference = a.build_year_inference(rules["scan_files"])
        for file in rules["scan_files"]:
            found = a.parse_effect_unit_assignments(file, set(rules["units"]), set(rules["monitored_stat_catalog"]), inference, scopes)
            for unit, items in found.items():
                actual.update(effect_identity(unit, item) for item in items if item["stat"] in rules["units"][unit]["monitored_stats"])
        self.assertEqual(actual, expected)
        # Hand-annotated source rows: neither extractor supplies these expectations.
        file = "TGC_Timeline_1966/technologies/navy_tech.txt"
        annotated = [(976, "steam_transport", 10), (977, "commerce_raider", 2),
                     (1088, "steam_transport", 2), (1089, "commerce_raider", 2),
                     (1090, "ironclad", 1), (1091, "monitor", 1),
                     (1186, "steam_transport", 6), (1187, "monitor", 6),
                     (1188, "cruiser", 5), (1189, "battleship", 3),
                     (1285, "steam_transport", 4), (1286, "cruiser", 3), (1287, "dreadnought", 3),
                     (1372, "steam_transport", 7), (1373, "cruiser", 5), (1374, "dreadnought", 4)]
        for line, unit, value in annotated:
            self.assertEqual(sum(count for (u, stat, val, scope, f, ln, col, owner), count in actual.items()
                                 if (u, stat, val, scope, f, ln) == (unit, "maximum_speed", value, unit, file, line)), 1)

    def test_hash_seed_and_file_order_invariance(self):
        code = '''import sys,json; from dataclasses import asdict
sys.path.insert(0, 'TGC/tools')
import audit_1966_balance as a
r=a.read_rules(); fs=r['scan_files']
if sys.argv[1]=='reverse': fs=list(reversed(fs))
print(json.dumps([(k,asdict(v)) for k,v in a.build_year_inference(fs).items()],sort_keys=True))'''
        outputs = []
        for seed, order in [("0", "normal"), ("2", "reverse"), ("42", "normal"), ("100", "reverse")]:
            env = dict(os.environ, PYTHONHASHSEED=seed)
            result = subprocess.run([sys.executable, "-B", "-c", code, order], cwd=ROOT, env=env,
                                    capture_output=True, text=True, check=True)
            outputs.append(result.stdout)
        self.assertEqual(len(set(outputs)), 1)

    def test_semantically_equivalent_layout_matches_each_effect(self):
        _, rules = real_inputs()
        baseline, scopes = oracle_effects(rules)
        overrides = {}
        token_pattern = re.compile(r'#[^\n]*|"[^"\r\n]*"|\'[^\'\r\n]*\'|[{}]|[<>=!]+|[^\s{}<>=!#,;]+')
        for file in rules["scan_files"]:
            text = (ROOT / file).read_text(encoding="utf-8")
            # One token per line + adversarial brace/reference comments.
            overrides[file] = '\n# } year = 2999 invention = fake {\n'.join(
                m.group() for m in token_pattern.finditer(text) if not m.group().startswith('#'))
        expected, _ = oracle_effects(rules, overrides)
        original = p.read_text
        def read(file, encoding="utf-8"):
            return overrides[file] if file in overrides else original(file, encoding=encoding)
        with patch.object(p, "read_text", side_effect=read):
            timing = a.build_year_inference(rules["scan_files"])
            actual = Counter()
            for file in rules["scan_files"]:
                found = a.parse_effect_unit_assignments(file, set(rules["units"]), set(rules["monitored_stat_catalog"]), timing, scopes)
                for unit, items in found.items():
                    actual.update(effect_identity(unit, item) for item in items if item["stat"] in rules["units"][unit]["monitored_stats"])
        self.assertEqual(actual, expected)
        def semantic(counter):
            result = Counter()
            for (unit, stat, value, scope, file, line, column, owner), count in counter.items():
                result[(unit, stat, value, scope, file, owner)] += count
            return result
        self.assertEqual(semantic(actual), semantic(baseline))

    def test_complete_report_is_identical_across_processes_and_input_order(self):
        code = '''import sys
sys.path.insert(0, 'TGC/tools')
import audit_1966_balance as a
from unittest.mock import patch
rules=a.read_rules()
if sys.argv[1]=='reverse': rules['scan_files'].reverse()
with patch.object(a, 'read_rules', return_value=rules), patch.object(sys, 'argv', ['audit']):
    raise SystemExit(a.main())'''
        reports = []
        for seed, order in [("0", "normal"), ("2", "reverse"), ("42", "normal"), ("100", "reverse")]:
            result = subprocess.run([sys.executable, "-B", "-c", code, order], cwd=ROOT,
                                    env=dict(os.environ, PYTHONHASHSEED=seed), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout[:1000])
            self.assertIn(" - FAIL: 0", result.stdout)
            reports.append(result.stdout)
        self.assertEqual(len(set(reports)), 1)


if __name__ == "__main__":
    unittest.main()
