"""Static contracts for the Project Alice 1.3.0 event overlay."""
from collections import Counter
from datetime import date, timedelta
from fractions import Fraction
from itertools import product
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "tools/deploy"
CORE = ROOT / "TGC"
sys.path[:0] = [str(TOOL), str(CORE / "tools")]

from deploy_tgc import (ALICE_CATALOG, ALICE_PROFILES, EXTENDER_CATALOGS, component_descriptor,
                        descriptor_values, load_catalog, payload_sources, selected_components)
from lib_1966_parser import parse_script, scalar, walk

AID_PATH = "events/CountryAid.txt"
CHUNNEL_PATH = "events/Canals Construction.txt"
LOCALE_PATH = "localisation/tgc_alice_event_options.csv"
FACTORY_TRIGGER = "tgc_state_has_completed_factory"
FACTORY_PATH = f"scripted triggers/{FACTORY_TRIGGER}.txt"
FACTORY_EVENTS = {"events/GERFlavor.txt": ("200049", 1),
                  "events/LiberalRevolutions.txt": ("10150", 7)}
OVERLAY_PATHS = {AID_PATH, CHUNNEL_PATH, LOCALE_PATH, FACTORY_PATH, *FACTORY_EVENTS}
AID_PAGES = dict(zip(("100013", "100003", "100005", "100007", "100009"),
                     ("100014", "100015", "100016", "100017", "100018")))


def nodes(path):
    return parse_script(path.read_bytes().decode("latin-1"), file=str(path)).nodes


def shape(items):
    return [(n.keyword, n.operator, shape(n.children) if n.is_group else n.value) for n in items]


def options(event):
    return [n for n in event.children if n.keyword == "option"]


def effects(option):
    return [n for n in option.children if n.keyword not in {"name", "ai_chance"}]


def child(parent, key):
    item, = (n for n in parent.children if n.keyword == key)
    return item


def ai_condition(node, funds):
    if node.keyword == "not":
        return not any(ai_condition(n, funds) for n in node.children)
    if node.keyword != "check_variable" or scalar(node, "which") != "total_chunnel_funds":
        raise AssertionError(f"Unexpected Chunnel condition: {node.start}")
    # Alice compiles a single '=' on this numeric trigger to >=.
    value = child(node, "value")
    if value.operator != "=":
        raise AssertionError(f"Unexpected Chunnel comparison: {value.start}")
    return funds >= int(value.value)


def weight(option, funds):
    ai = next((n for n in option.children if n.keyword == "ai_chance"), None)
    if ai is None:
        return 0
    result = int(scalar(ai, "factor"))
    for mod in (n for n in ai.children if n.keyword == "modifier"):
        if all(ai_condition(n, funds) for n in mod.children if n.keyword != "factor"):
            result *= int(scalar(mod, "factor"))
    return result


class AliceProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")[:-1]
        cls.inventories = {}
        # The transaction tests exercise the real scanning, staging and link checks.
        with patch("deploy_tgc.snapshot"):
            for profile in ("core", "core+1966", *EXTENDER_CATALOGS, *ALICE_PROFILES):
                filename = ALICE_CATALOG if profile in ALICE_PROFILES else EXTENDER_CATALOGS.get(
                    profile, "components.json"
                )
                catalog = load_catalog(TOOL / filename)
                component_files = {}
                for component in selected_components(catalog, profile, ()):
                    component_files.update(payload_sources(ROOT, component, tracked, catalog))
                    descriptor = component_descriptor(ROOT, component, catalog, tracked)
                    if profile in ALICE_PROFILES:
                        cls.assert_alice_descriptor(profile, descriptor)
                cls.inventories[profile] = component_files

        cls.original = {}
        cls.adapted = {}
        for name in (AID_PATH, CHUNNEL_PATH):
            cls.original.update((scalar(n, "id"), n) for n in nodes(CORE / name))
            cls.adapted.update((scalar(n, "id"), n) for n in nodes(cls.inventories["core+alice"][name]))

    @staticmethod
    def assert_alice_descriptor(profile, descriptor):
        text = descriptor.decode("utf-8")
        cid = ALICE_PROFILES[profile]
        core_text = (ROOT / "TGC.mod").read_text(encoding="utf-8")
        assert descriptor_values(text, "path") == [f"mod/{cid}"]
        assert descriptor_values(text, "user_dir") == [cid]
        assert descriptor_values(text, "replace_path") == descriptor_values(core_text, "replace_path")
        assert not descriptor_values(text, "load") and "dependencies" not in text

    def test_profiles_publish_only_the_expected_changes(self):
        for profile in ("core", "core+1966", *EXTENDER_CATALOGS):
            files = self.inventories[profile]
            self.assertEqual(files[AID_PATH], CORE / AID_PATH)
            self.assertEqual(files[CHUNNEL_PATH], CORE / CHUNNEL_PATH)
            self.assertNotIn(LOCALE_PATH, files)
        for alice, shared in (("core+alice", "core"), ("core+alice+1966", "core+1966")):
            actual, baseline = self.inventories[alice], self.inventories[shared]
            changed = {name for name, src in actual.items() if baseline.get(name) != src}
            self.assertEqual(changed, OVERLAY_PATHS | {"map/default.map"})
            self.assertEqual(actual.keys(), baseline.keys() | {LOCALE_PATH, FACTORY_PATH})
            self.assertIn(f'../mod/{ALICE_PROFILES[alice]}/map/definition.csv'.encode(), actual["map/default.map"])
            self.assertEqual(actual["map/definition.csv"], baseline["map/definition.csv"])

    def test_amazon_region_has_unique_south_american_provinces_in_all_profiles(self):
        region_path = "map/region.txt"
        continent_path = "map/continent.txt"
        definition_path = "map/definition.csv"
        event_paths = ("events/BRZFlavor.txt", "events/Debug.txt")
        for profile, files in self.inventories.items():
            with self.subTest(profile=profile):
                for path in (region_path, continent_path, definition_path, *event_paths):
                    self.assertEqual(files[path], CORE / path)
                region, = (n for n in nodes(files[region_path]) if n.key == "THE_AMAZON_FOREST")
                south_america, = (n for n in nodes(files[continent_path]) if n.key == "south_america")
                provinces = [n.value for n in region.children]
                continental_ids = {n.value for n in child(south_america, "provinces").children}
                defined_ids = {
                    line.partition(";")[0]
                    for line in files[definition_path].read_text(encoding="latin-1").splitlines()
                }
                self.assertTrue(provinces)
                self.assertEqual(len(provinces), len(set(provinces)))
                self.assertLessEqual(set(provinces), continental_ids & defined_ids)
                self.assertTrue(set(provinces).isdisjoint({"1128", "1122", "1120", "1133"}))

    def test_unique_event_ids_option_limit_and_overlay_dependencies(self):
        new = set(AID_PAGES.values()) | {"37001"}
        self.assertEqual(self.adapted.keys(), self.original.keys() | new)
        ids = Counter()
        files = self.inventories["core+alice+1966"]
        for rel, path in files.items():
            if Path(rel).parent.as_posix() != "events" or Path(rel).suffix != ".txt":
                continue
            for event in nodes(path):
                if event.keyword not in {"country_event", "province_event"}:
                    continue
                event_id = scalar(event, "id", required=True)
                ids[event_id] += 1
                self.assertLessEqual(len(options(event)), 8, (rel, event_id))
        self.assertTrue(all(count == 1 for count in ids.values()))
        keys = Counter(
            line.partition(b";")[0].decode("latin-1")
            for rel, path in files.items()
            if Path(rel).parent.as_posix() == "localisation" and Path(rel).suffix == ".csv"
            for line in path.read_bytes().splitlines() if line
        )
        for ev in self.adapted.values():
            for n in walk(ev.children):
                if n.keyword == "country_event":
                    target = scalar(n, "id", required=True) if n.is_group else n.value
                    self.assertEqual(ids[target], 1, (n.start, target))
                if n.keyword in {"title", "desc", "name"} and n.value.startswith(("EVT", "TGC_ALICE_")):
                    self.assertEqual(keys[n.value], 1, (n.start, n.value))

    def test_country_aid_preserves_terminal_choices_and_routes_each_request(self):
        aid_navigation = """
            set_country_flag = tgc_alice_aid_page_donor
            FROM = { this_bounce = {
                if = { limit = { has_country_flag = tgc_alice_aid_page_donor } country_event = TARGET }
                any_defined_country = {
                    limit = { has_country_flag = tgc_alice_aid_page_donor } country_event = TARGET
                }
            } }
            clr_country_flag = tgc_alice_aid_page_donor
        """
        for event_id, target in AID_PAGES.items():
            original = options(self.original[event_id])
            first = options(self.adapted[event_id])
            page = self.adapted[target]
            second = options(page)
            self.assertEqual(shape(first[:-1] + second[1:]), shape(original))
            self.assertEqual(shape(second[:1]), shape(original[:1]))
            self.assertEqual(weight(first[-1], 0), 0)
            self.assertEqual(scalar(page, "allow_multiple_instances"), "yes")
            expected = parse_script(aid_navigation.replace("TARGET", target)).nodes
            self.assertEqual(shape(effects(first[-1])), shape(expected))
            self.assertEqual(scalar(page, "title"), scalar(self.original[event_id], "title"))
            self.assertEqual(scalar(page, "desc"), scalar(self.original[event_id], "desc"))

            # Alice's if handles self; any_defined_country visits every other
            # nation. Queue records capture primary/THIS by value before clearing.
            donor, requester_a, requester_b = "ENG", "FRA", "PRU"
            queued = []
            for requester in (requester_a, requester_b, donor):
                marked = {donor}
                candidates = [requester] + [n for n in (donor, requester_a, requester_b) if n != requester]
                queued.extend((target, primary, requester) for primary in candidates if primary in marked)
                marked.clear()
            self.assertEqual(queued, [(target, donor, n) for n in (requester_a, requester_b, donor)])
            self.assertEqual(len(set(queued)), 3)
            pending = set(queued)
            balances = Counter()
            requests = [(queued[1], second[3]), (queued[0], second[2]), (queued[2], second[0])]
            for event, option in requests:
                self.assertIn(event, pending)
                pending.remove(event)
                for effect in effects(option):
                    if effect.keyword == "treasury":
                        balances[event[1]] += int(effect.value)
                    else:
                        self.assertEqual(effect.keyword, "from")
                        self.assertTrue(all(n.keyword == "treasury" for n in effect.children))
                        balances[event[2]] += sum(int(n.value) for n in effect.children)
                self.assertNotIn(event, pending)  # A stale choice cannot execute again.
            step = int(scalar(original[1], "treasury")) * -1
            self.assertEqual(balances, {donor: -17 * step, requester_a: 8 * step, requester_b: 9 * step})
            self.assertFalse(pending)

    def test_factory_checks_are_scoped_and_cover_the_effective_factory_types(self):
        generic = b"has_factories = yes"
        predicate = f"test = {FACTORY_TRIGGER}".encode()
        for profile, files in self.inventories.items():
            with self.subTest(profile=profile):
                if profile not in ALICE_PROFILES:
                    self.assertNotIn(FACTORY_PATH, files)
                    for path in FACTORY_EVENTS:
                        self.assertEqual(files[path], CORE / path)
                    continue

                helper, = nodes(files[FACTORY_PATH])
                self.assertEqual(helper.key, FACTORY_TRIGGER)
                self.assertEqual(scalar(helper, "main_parameter"), "state")
                checks = child(helper, "or").children
                self.assertTrue(all(n.keyword == "has_building" for n in checks))
                factory_types = {n.key for n in nodes(files["common/buildings.txt"])
                                 if scalar(n, "type") == "factory"}
                self.assertTrue(factory_types)
                self.assertCountEqual([n.value for n in checks], factory_types)

                for path, (event_id, count) in FACTORY_EVENTS.items():
                    before = (CORE / path).read_bytes().replace(b"\r\n", b"\n")
                    after = files[path].read_bytes().replace(b"\r\n", b"\n")
                    self.assertEqual(before.count(generic), count)
                    self.assertEqual(after, before.replace(generic, predicate))
                    event, = (n for n in nodes(files[path]) if scalar(n, "id") == event_id)
                    state_contexts = [
                        child(n, "limit") if n.keyword == "random_state" else n
                        for n in walk(event.children)
                        if n.keyword in {"state_scope", "any_state", "random_state"}
                    ]
                    self.assertEqual(sum(scalar(n, "test") == FACTORY_TRIGGER
                                         for n in state_contexts), count)

    def test_chunnel_financing_times_construction_at_both_ends(self):
        for profile, files in self.inventories.items():
            with self.subTest(profile=profile):
                event, = (n for n in nodes(files[CHUNNEL_PATH]) if scalar(n, "id") == "36999")
                option, = (n for n in options(event) if scalar(n, "name") == "EVTOPTE36999")
                actual = []
                for outcome in child(option, "random_list").children:
                    actual.append((outcome.keyword, [
                        (province.keyword, scalar(child(province, "add_province_modifier"), "name"),
                         scalar(child(province, "add_province_modifier"), "duration"))
                        for province in outcome.children
                    ]))
                self.assertEqual(actual, [
                    (weight, [(province, "chunnel_construction", duration) for province in ("301", "401")])
                    for weight, duration in (("40", "3285"), ("35", "2920"), ("15", "3650"),
                                             ("5", "2190"), ("5", "2555"))
                ])

    def test_carrington_runs_once_independently_of_the_broadcaster(self):
        event_path = "events/NaturalDisasters.txt"
        daily_path = "events/JANFlavor.txt"
        for profile, files in self.inventories.items():
            with self.subTest(profile=profile):
                self.assertEqual(files[event_path], CORE / event_path)
                self.assertNotIn("decisions/Natural_Disasters.txt", files)
                daily, = (n for n in nodes(files[daily_path]) if scalar(n, "id") == "53")
                option = child(daily, "option")
                self.assertEqual(shape(child(option, "country_event").children),
                                 [("id", "=", "53"), ("days", "=", "1")])
                storm, = (n for n in option.children
                          if scalar(n, "set_global_flag") == "carrington_event_fired")
                self.assertEqual(storm.keyword, "random_owned")
                gate = child(child(storm, "limit"), "owner")
                self.assertEqual(shape(gate.children), [
                    ("year", "=", "1859"),
                    ("not", "=", [("year", "=", "1860"),
                                  ("has_global_flag", "=", "carrington_event_fired")]),
                    ("or", "=", [
                        ("and", "=", [("has_global_flag", "=", "project_alice"),
                                      ("month", "=", "9"), ("not", "=", [("month", "=", "10")])]),
                        ("and", "=", [("not", "=", [("has_global_flag", "=", "project_alice")]),
                                      ("month", "=", "8"), ("not", "=", [("month", "=", "9")])]),
                    ]),
                ])

                _, mark, affected, broadcaster = storm.children
                self.assertEqual([mark.keyword, affected.keyword, broadcaster.keyword],
                                 ["set_global_flag", "any_country", "random_country"])
                self.assertEqual(shape(child(affected, "limit").children), [
                    ("exists", "=", "yes"), ("early_railroad", "=", "1"),
                    ("invention", "=", "telegraph_coordination"),
                ])
                self.assertEqual(shape(child(affected, "add_country_modifier").children), [
                    ("name", "=", "magnetic_interference"), ("duration", "=", "60"),
                ])
                self.assertEqual(shape(child(broadcaster, "limit").children),
                                 [("exists", "=", "yes"), ("is_greater_power", "=", "yes")])
                self.assertEqual(scalar(broadcaster, "country_event"), "21501")

        event, = (n for n in nodes(CORE / event_path) if scalar(n, "id") == "21501")
        self.assertEqual(scalar(event, "is_triggered_only"), "yes")
        self.assertEqual(scalar(event, "news"), "yes")
        self.assertFalse(effects(child(event, "option")))
        self.assertFalse(any(n.keyword == "immediate" for n in event.children))

        for alice, marked, initially_eligible, great_power in product((False, True), repeat=4):
            with self.subTest(alice=alice, legacy_marked=marked,
                              initially_eligible=initially_eligible, great_power=great_power):
                fired = marked
                effects_dates, announcements = [], []
                start = date(1859, 8, 30)
                september = date(1859, 9, 1)
                for offset in range(402):
                    current = start + timedelta(days=offset)
                    month = current.month if alice else current.month - 1
                    expected_month = 9 if alice else 8
                    if fired or current.year != 1859 or month != expected_month:
                        continue
                    fired = True
                    if initially_eligible or current > september:
                        effects_dates.append(current)
                    if great_power:
                        announcements.append(current)
                self.assertEqual(effects_dates, [september] if initially_eligible and not marked else [])
                self.assertEqual(announcements, [september] if great_power and not marked else [])

    def test_chunnel_preserves_effects_and_normalized_weights(self):
        original = options(self.original["36996"])
        first, second = (options(self.adapted[event_id]) for event_id in ("36996", "37001"))
        self.assertEqual(shape(first[:-1] + second[1:]), shape(original))
        self.assertEqual(shape(effects(second[0])), shape(effects(original[0])))
        self.assertEqual(shape(effects(first[-1])), [("country_event", "=", "37001")])
        self.assertEqual(scalar(second[0], "name"), scalar(original[0], "name"))
        self.assertEqual(weight(second[0], 0), 0)
        for event_id in self.original.keys() - AID_PAGES.keys() - {"36996"}:
            self.assertEqual(shape([self.original[event_id]]), shape([self.adapted[event_id]]))

        set_funds = [int(scalar(child(child(o, "jan"), "set_variable"), "value"))
                     for o in options(self.original["36994"])]
        add_funds = [int(scalar(child(next(n for n in o.children if n.keyword == "jan"),
                                      "change_variable"), "value"))
                     for o in options(self.original["36995"])]
        pairs = list(product(set_funds, add_funds))
        self.assertEqual(len(pairs), 36)
        self.assertEqual({a + b for a, b in pairs}, set(range(10, 21)))
        for funds in [*(a + b for a, b in pairs), -1, 0, Fraction(19, 2), Fraction(23, 2), 21]:
            with self.subTest(funds=funds):
                raw = [weight(o, funds) for o in original]
                main = [weight(o, funds) for o in first]
                sub = [weight(o, funds) for o in second]
                self.assertEqual(main[-1], sum(raw[7:]))
                self.assertEqual(main[-1], sum(sub))
                self.assertGreater(sum(main), 0)
                distribution = [Fraction(w, sum(main)) for w in main[:-1]]
                distribution += [Fraction(main[-1], sum(main)) * Fraction(w, sum(sub)) for w in sub[1:]]
                self.assertEqual(distribution, [Fraction(w, sum(raw)) for w in raw])
