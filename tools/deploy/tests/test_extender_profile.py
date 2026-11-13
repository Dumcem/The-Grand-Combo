"""Static contracts for the Extender overlay and its shared inputs."""
from configparser import ConfigParser
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "TGC"
EXTENDED = ROOT / "TGCScriptExtender"
UPSTREAM = "14f2e6ff61e7e1ea07ffef07548560da5bcc47f0"
sys.path.insert(0, str(CORE / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "deploy"))
from deploy_tgc import (EXTENDER_TIMELINE_COMPONENT, DeploymentError, check_descriptor,
                        component_descriptor, descriptor_values, load_catalog, payload_sources,
                        selected_components)
from lib_1966_parser import parse_script, scalar, walk
from lib_1966_runtime import compose_runtime


def script(path):
    return parse_script(path.read_bytes().decode("cp1252"), file=str(path)).nodes


def definitions(path):
    return {node.key: node for node in script(path)}


def events(path):
    return {scalar(node, "id"): node for node in script(path)}


def section(node, name):
    return next(child for child in node.children if child.key == name)


def shape(nodes):
    return [(node.key, shape(node.children) if node.is_group else node.value) for node in nodes]


def localisation_keys(path):
    return {line.partition(b";")[0].decode("cp1252") for line in path.read_bytes().splitlines() if line}


class ExtenderProfileTests(unittest.TestCase):
    def test_four_profiles_select_canonical_content_and_preserve_engine_boundaries(self):
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")[:-1]
        configurations = {
            "core": ("components.json", ["TGC"]),
            "core+1966": ("components.json", ["TGC", "TGC_Timeline_1966"]),
            "core+extender": ("components_extender.json", [EXTENDED.name]),
            "core+extender+1966": ("components_extender_1966.json", [EXTENDER_TIMELINE_COMPONENT]),
        }
        inventories, descriptors = {}, {}
        # Full-tree link and staging checks are exercised by the deployment tests.
        with patch("deploy_tgc.snapshot"):
            for profile, (catalog_file, ids) in configurations.items():
                catalog = load_catalog(ROOT / "tools/deploy" / catalog_file)
                components = selected_components(catalog, profile, ())
                self.assertEqual([component["id"] for component in components], ids)
                files = {}
                for component in components:
                    files.update(payload_sources(ROOT, component, tracked, catalog))
                    source = component_descriptor(ROOT, component, catalog, tracked)
                    data = source if isinstance(source, bytes) else source.read_bytes()
                    descriptors[component["id"]] = data.decode("utf-8-sig")
                inventories[profile] = files

        core, shared_1966, extender, combined = inventories.values()
        jan = "events/JANFlavor.txt"
        self.assertEqual(core[jan], CORE / jan)
        self.assertEqual(shared_1966[jan], core[jan])
        self.assertEqual(extender[jan], EXTENDED / jan)
        self.assertEqual(combined[jan], extender[jan])
        timeline = {name: source for name, source in shared_1966.items() if core.get(name) != source}
        overlay = {name: source for name, source in extender.items() if core.get(name) != source}
        map_path = "map/default.map"
        combined_map = overlay[map_path].read_bytes().replace(
            b"../mod/TGCScriptExtender/map/", b"../mod/TGCScriptExtender1966/map/"
        )
        self.assertEqual(combined, {**core, **timeline, **overlay, map_path: combined_map})
        self.assertFalse(timeline.keys() & overlay.keys())
        self.assertEqual(combined["map/definition.csv"], core["map/definition.csv"])
        self.assertEqual(combined["map/region.txt"], core["map/region.txt"])
        self.assertIn("end_date = '1966.1.1'", combined["common/defines.lua"].read_text(encoding="cp1252"))
        self.assertNotEqual(combined["common/defines.lua"], extender["common/defines.lua"])
        for directory in ("technologies", "inventions", "units", "localisation"):
            self.assertTrue(any(name.startswith(directory + "/") for name in timeline), directory)

        # The Timeline replaces building levels. The scheduler's named buildings still match exactly.
        buildings = definitions(combined["common/buildings.txt"])
        original_buildings = definitions(extender["common/buildings.txt"])
        scheduled = definitions(combined["common/buildings_ai.txt"])
        self.assertEqual(list(buildings), list(original_buildings))
        for name in scheduled:
            self.assertEqual(shape(buildings[name].children), shape(original_buildings[name].children), name)
        for name in ("fort", "naval_base", "railroad"):
            self.assertEqual(scalar(buildings[name], "max_level"), "8")

        for cid in ("TGC", "TGC_Timeline_1966"):
            self.assertEqual(descriptor_values(descriptors[cid], "load"), [])
        # The Alice-specific rules in runtime scripts remain visible in both shared profiles.
        for name, source in core.items():
            if name.startswith(("common/", "decisions/", "events/")) and name.endswith(".txt"):
                if b"project_alice" in source.read_bytes():
                    self.assertEqual(shared_1966[name], source, name)
        base_loader = descriptors[EXTENDED.name]
        combined_loader = descriptors[EXTENDER_TIMELINE_COMPONENT]
        self.assertEqual(descriptor_values(combined_loader, "load"), descriptor_values(base_loader, "load"))
        self.assertEqual(descriptor_values(combined_loader, "replace_path"),
                         descriptor_values(descriptors["TGC"], "replace_path"))
        self.assertEqual(descriptor_values(combined_loader, "path"), ["mod/TGCScriptExtender1966"])
        self.assertEqual(descriptor_values(combined_loader, "user_dir"), ["TGCScriptExtender1966"])
        self.assertEqual(descriptor_values(base_loader, "user_dir"), ["TGCScriptExtender"])
        self.assertNotIn("dependencies", combined_loader)

    def test_profiles_inherit_upstream_event_modifiers_without_legacy_income(self):
        path = "common/event_modifiers.txt"
        upstream, previous = (
            subprocess.check_output(["git", "show", f"{ref}:TGC/{path}"], cwd=ROOT)
            .replace(b"\r\n", b"\n")
            for ref in (UPSTREAM,
                        "d744bb2d73c69928587b58cc7b3607262baa6149")
        )
        income = re.compile(rb"^[ \t]*(?:rich|middle|poor)_income_modifier[ \t]*=")
        before = previous.splitlines(keepends=True)
        self.assertEqual(sum(bool(income.match(line)) for line in before), 15)
        self.assertEqual(b"".join(line for line in before if not income.match(line)), upstream)

        manifest_path = "tools/deploy/extender_overlay.json"
        manifest = json.loads((ROOT / manifest_path).read_bytes())
        # Include the full overlay so the production selector can validate its pins.
        relevant = {manifest_path, f"TGC/{path}"}
        relevant.update(f"{root}/{name}" for root in ("TGC", EXTENDED.name)
                        for name in (*manifest, path))
        tracked = subprocess.check_output(
            ["git", "ls-files", "-z", "--", *sorted(relevant)], cwd=ROOT
        ).split(b"\0")
        catalog = load_catalog(ROOT / "tools/deploy/components_extender.json")
        # This test checks file selection. Link auditing is covered by deployment tests.
        with patch("deploy_tgc.snapshot"):
            extender = payload_sources(ROOT, catalog["components"][0],
                                       [p.decode() for p in tracked if p], catalog)
        sources = {
            "core": ROOT / compose_runtime(ROOT, timeline_root=None).require(path),
            "core+1966": ROOT / compose_runtime(ROOT).require(path),
            "core+extender": extender[path],
        }
        for profile, source in sources.items():
            with self.subTest(profile=profile):
                self.assertEqual(source, CORE / path)
                actual = source.read_bytes().replace(b"\r\n", b"\n")
                self.assertEqual(actual, upstream)

    def test_declared_overlay_and_descriptor(self):
        manifest = json.loads((ROOT / "tools/deploy/extender_overlay.json").read_bytes())
        files = {p.relative_to(EXTENDED).as_posix() for p in EXTENDED.rglob("*") if p.is_file()}
        self.assertEqual(files, set(manifest))
        for path, sha in manifest.items():
            base = CORE / path
            self.assertFalse((ROOT / "TGC_Timeline_1966" / path).exists(), path)
            if sha is None:
                self.assertFalse(base.exists(), path)
            else:
                data = base.read_bytes().replace(b"\r\n", b"\n")
                self.assertEqual(hashlib.sha256(data).hexdigest(), sha, path)
        base = definitions(ROOT / "TGC.mod")
        ext = definitions(EXTENDED.with_suffix(".mod"))
        self.assertNotIn("load", base)
        self.assertNotIn("load", definitions(ROOT / "TGC_Timeline_1966.mod"))
        self.assertEqual(ext["user_dir"].value, "TGCScriptExtender")
        self.assertNotIn("dependencies", ext)
        for key in ("replace_path", "github", "current_release"):
            self.assertEqual(shape(n for n in script(EXTENDED.with_suffix(".mod")) if n.key == key),
                             shape(n for n in script(ROOT / "TGC.mod") if n.key == key))

    def test_map_definition_resolves_to_the_deployed_component(self):
        catalog = json.loads((ROOT / "tools/deploy/components_extender.json").read_bytes())
        component = catalog["components"][0]
        path = "map/default.map"
        core = (CORE / path).read_bytes().replace(b"\r\n", b"\n")
        extended = (EXTENDED / path).read_bytes().replace(b"\r\n", b"\n")
        original = b'definitions = "../mod/TGC/map/definition.csv"'
        target = f'definitions = "../mod/{component["destination_dir"]}/map/definition.csv"'.encode()
        self.assertEqual(core.count(original), 1)
        self.assertEqual(extended.rstrip(b"\n"), core.replace(original, target).rstrip(b"\n"))
        self.assertIn("map", component["runtime_policy"]["roots"])
        self.assertTrue((CORE / "map/definition.csv").is_file())

    def test_province_and_forced_treaty_are_isolated(self):
        path = "common/cb_types.txt"
        core = definitions(CORE / path)
        extended = definitions(EXTENDED / path)
        self.assertEqual(extended.keys() - core.keys(), {"acquire_province"})
        for name in core.keys() - {"peace_order", "dismantle_cb", "dismantle_cb_add", "great_war_penalty_cb"}:
            self.assertEqual(shape(extended[name].children), shape(core[name].children), name)
        province_cb = extended["acquire_province"]
        for field, value in (("po_demand_province", "yes"), ("is_triggered_only", "yes"),
                             ("badboy_factor", "1.0"), ("peace_cost_factor", "1")):
            self.assertEqual(scalar(province_cb, field), value, field)
        peace_order = [n.value for n in extended["peace_order"].children]
        self.assertEqual(peace_order[peace_order.index("acquire_state") + 1], "acquire_province")
        self.assertEqual(localisation_keys(EXTENDED / "localisation/00_se_acquire_province.csv"),
                         {"acquire_province", "acquire_province_desc", "acquire_province_short",
                          "acquire_province_setup"})
        for name, effect in (("dismantle_cb", "dismantled_by"), ("dismantle_cb_add", "dismantled_by_gw"),
                             ("great_war_penalty_cb", "dismantled_by_gw")):
            self.assertEqual(scalar(core[name], "po_reparations"), "yes")
            accept = shape(n for n in walk(section(extended[name], "on_po_accepted").children)
                           if not n.is_group)
            self.assertIn((effect, "THIS"), accept)
            self.assertIn(("set_country_flag", "se_treaty_dismantled"), accept)
            self.assertIn(("set_country_flag", "dismantling_treaty"), accept)
        self.assertEqual(scalar(extended["great_war_penalty_cb"], "po_reparations"), "yes")
        self.assertIsNone(scalar(extended["dismantle_cb"], "po_reparations"))
        self.assertIsNone(scalar(extended["dismantle_cb_add"], "po_reparations"))

    def test_great_war_closure_has_exclusive_ownership_of_flags(self):
        path = "events/Great War.txt"
        core = events(CORE / path)
        ext = events(EXTENDED / path)
        self.assertEqual(set(ext) - set(core), {"96094"})
        flag = ("has_country_flag", "se_treaty_dismantled")
        guarded = {"96010", "96021", "96035", "96040", "96045", "96050",
                   "96051", "96055", "96056", "96057", "96058"}
        for event_id in core:
            with self.subTest(event=event_id):
                content = shape(ext[event_id].children)
                if event_id in guarded:
                    trigger = next(value for key, value in content if key == "trigger")
                    trigger.remove(("NOT", [flag]))
                self.assertEqual(content, shape(core[event_id].children))
        closure = ext["96094"]
        self.assertEqual(shape(section(closure, "trigger").children),
                         [("war", "no"), flag, ("has_country_flag", "dismantling_treaty")])
        outcomes = {n.value for n in section(closure, "option").children if n.key == "clr_country_flag"}
        self.assertTrue({"se_treaty_dismantled", "dismantling_treaty"} <= outcomes)
        self.assertFalse({"secede_province", "release", "add_core", "remove_core"}
                         & {n.key for n in walk(closure.children)})

    def test_partitions_and_interests_reference_playable_map(self):
        regions = definitions(CORE / "map/region.txt")
        countries = definitions(CORE / "common/countries.txt")
        land = {node.value for region in regions.values() for node in region.children if node.key is None}
        defined = {row.split(b";", 1)[0].decode("ascii") for row in
                   (CORE / "map/definition.csv").read_bytes().splitlines() if row.split(b";", 1)[0].isdigit()}
        for name in ("se_partitions.txt", "ai_interests.txt"):
            entries = script(EXTENDED / "common" / name)
            self.assertEqual(len(entries), len({entry.key for entry in entries}))
            for entry in entries:
                self.assertIn(entry.key, countries)
                self.assertTrue(entry.children, entry.key)
                for child in entry.children:
                    if child.key is None:
                        self.assertIn(child.value, regions, entry.key)
                    else:
                        self.assertEqual(child.key, "provinces")
                        self.assertTrue(child.children, entry.key)
                        self.assertTrue({p.value for p in child.children} <= land & defined, entry.key)

    def test_builders_replace_only_the_two_ai_event_triggers(self):
        path = "events/BanksAndUniversities.txt"
        core = events(CORE / path)
        ext = events(EXTENDED / path)
        self.assertEqual(ext.keys(), core.keys())
        for event_id in core:
            if event_id in ("6200", "6201"):
                self.assertEqual(scalar(ext[event_id], "is_triggered_only"), "yes")
                self.assertEqual(shape(n for n in ext[event_id].children if n.key != "is_triggered_only"),
                                 shape(n for n in core[event_id].children if n.key != "trigger"))
            else:
                self.assertEqual(shape(ext[event_id].children), shape(core[event_id].children))
        scheduled = definitions(EXTENDED / "common/buildings_ai.txt")
        self.assertEqual(set(scheduled), {"bank", "university"})
        buildings = definitions(CORE / "common/buildings.txt")
        for name, entry in scheduled.items():
            self.assertIn(name, buildings)
            self.assertGreater(float(scalar(entry, "chance")), 0)
            self.assertGreater(float(scalar(entry, "money")), 0)
            self.assertTrue(section(entry, "weight").children)

    def test_income_curve_replaces_only_the_daily_pop_transfers(self):
        path = "common/triggered_modifiers.txt"
        core = definitions(CORE / path)
        ext = definitions(EXTENDED / path)
        technologies = ("state_n_government", "nationalism_n_imperialism",
                        "revolution_n_counterrevolution", "mass_politics", "the_police_state")
        guards = [[(tech, "1"), ("NOT", [(following, "1")])]
                  for tech, following in zip(technologies, technologies[1:])]
        guards.extend(([(technologies[-1], "1"), ("NOT", [("year", "1990")])],
                       [(technologies[-1], "1"), ("year", "1990")]))
        strata_values = ((.05, .025, .01), (.10, .05, .025), (.15, .10, .05),
                         (.25, .15, .10), (.40, .25, .15), (.50, .40, .25))
        names = ["poor_income_" + suffix for suffix in (*technologies, "the_police_state_1990")]
        self.assertEqual(set(ext) - set(core), set(names))
        for name in core:
            self.assertEqual(shape(ext[name].children), shape(core[name].children))
        keys = localisation_keys(EXTENDED / "localisation/00_poor_income.csv")
        for name, guard, values in zip(names, guards, strata_values, strict=True):
            with self.subTest(modifier=name):
                self.assertTrue({name, "desc_" + name} <= keys)
                self.assertEqual(shape(section(ext[name], "trigger").children), guard)
                actual = tuple(float(scalar(ext[name], stratum + "_income_modifier"))
                               for stratum in ("poor", "middle", "rich"))
                self.assertEqual(actual, values)
        path = "events/JANFlavor.txt"
        core_events, ext_events = events(CORE / path), events(EXTENDED / path)
        self.assertEqual(core_events.keys(), ext_events.keys())
        for event_id in core_events.keys() - {"53"}:
            self.assertEqual(shape(ext_events[event_id].children), shape(core_events[event_id].children), event_id)
        before, after = (section(e["53"], "option").children for e in (core_events, ext_events))
        self.assertEqual(len(before) - len(after), 6)
        self.assertEqual(shape(n for n in before if n.key != "any_country"), shape(after))
        reschedule = section(section(ext_events["53"], "option"), "country_event")
        self.assertEqual(shape(reschedule.children), [("id", "53"), ("days", "1")])

    def test_loader_descriptor_matches_upstream_and_requires_both_plugins(self):
        upstream = subprocess.check_output(
            ["git", "show", f"{UPSTREAM}:TGC.mod"], cwd=ROOT
        ).decode("utf-8")
        expected = shape(node for node in parse_script(upstream, file="TGC.mod").nodes
                         if node.key == "load")
        self.assertEqual(expected, [
            ("load", "script_extender/script_extender.dll"),
            ("load", "performance_patch/performance_patch.dll"),
        ])
        catalog = load_catalog(ROOT / "tools/deploy/components_extender.json")
        component = catalog["components"][0]
        descriptor = ROOT / component["source_descriptor"]
        self.assertEqual(shape(node for node in script(descriptor) if node.key == "load"), expected)
        mapping = {component["id"]: component}
        check_descriptor(ROOT, component, mapping)
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / descriptor.name
            for _, dll in expected:
                with self.subTest(missing=dll):
                    target.write_text(descriptor.read_text(encoding="utf-8").replace(
                        f'load = "{dll}"', ""
                    ), encoding="utf-8")
                    with self.assertRaisesRegex(DeploymentError, "Extender descriptor inconsistent"):
                        check_descriptor(Path(tmp), component, mapping)

    def test_config_preserves_all_enabled_upstream_extender_switches(self):
        config = ConfigParser()
        config.read_string("[extender]\n" + (ROOT / "docs/deployment/script_extender_options.ini").read_text(
            encoding="utf-8"
        ))
        self.assertEqual(dict(config["extender"]), dict.fromkeys((
            "demand_province", "treaty", "buildings_ai", "income_modifiers",
            "building_map_mode", "country_upgrade", "event_background", "province_flags",
            "vassal_map_color", "treaty_infamy",
        ), "1"))
