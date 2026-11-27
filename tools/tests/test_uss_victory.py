"""Static and deterministic checks for the War of the Americas settlement."""

import unittest

from test_upstream_task42 import ROOT, decision, definitions, evaluate, event, section
from lib_1966_parser import parse_script, scalar, walk


def shape(nodes):
    return [(node.key, node.operator, shape(node.children) if node.is_group else node.value)
            for node in nodes]


class AmericasSettlementTests(unittest.TestCase):
    def test_only_the_attacker_goal_enters_the_settlement(self):
        declaration = decision("USSA", "USS_dismantle_USA")
        war = section(section(declaration, "effect"), "war")
        self.assertEqual(scalar(war, "target"), "USA")
        self.assertEqual(scalar(section(war, "attacker_goal"), "casus_belli"), "war_of_the_americas_ussa")
        self.assertEqual(scalar(section(war, "defender_goal"), "casus_belli"), "cut_down_to_size")
        self.assertNotIn("USS_USA_win", {n.key for n in definitions("decisions/USSA.txt")[0].children})

        for component in ("TGC", "TGCScriptExtender"):
            with self.subTest(component=component):
                path = ROOT / component / "common/cb_types.txt"
                scripts = parse_script(path.read_bytes().decode("latin-1"), file=str(path)).definitions
                cut_down, = (n for n in scripts if n.key == "cut_down_to_size")
                goal, = (n for n in scripts if n.key == "war_of_the_americas_ussa")
                self.assertEqual(shape([n for n in goal.children if not n.is_group and n.key != "war_name"]),
                                 shape([n for n in cut_down.children if not n.is_group and n.key != "war_name"]))
                self.assertEqual(shape(section(goal, "on_add").children), shape(section(cut_down, "on_add").children))
                branch, = section(goal, "on_po_accepted").children
                self.assertEqual(branch.key, "random_owned")
                self.assertEqual(shape(section(branch, "limit").children), [
                    ("owner", "=", [("tag", "=", "USA")]),
                    ("THIS", "=", [("tag", "=", "USS")]),
                    ("NOT", "=", [("has_global_flag", "=", "USS_USA_win"),
                                  ("has_global_flag", "=", "USS_USA_lose")]),
                ])
                self.assertEqual(shape(section(branch, "owner").children), [
                    ("set_global_flag", "=", "USS_USA_win"),
                    ("set_country_flag", "=", "uss_americas_settlement_pending"),
                    ("prestige", "=", "-60"),
                    ("THIS", "=", [("prestige", "=", "40")]),
                    ("country_event", "=", "3755286"),
                ])

    def test_continental_partition_respects_current_ownership(self):
        immediate = section(event("USSFlavor", 3755286), "immediate")
        settlement = section(section(immediate, "any_owned"), "owner")
        transfers = [node for node in settlement.children if node.key == "any_owned"]
        self.assertEqual([scalar(node, "secede_province") for node in transfers],
                         ["MEX", "USS", "NEN", "UOR", "DAK"])
        regions = {n.key: {p.value for p in n.children} for n in definitions("map/region.txt")}
        continents = {n.key: {p.value for p in section(n, "provinces").children}
                      for n in definitions("map/continent.txt")}
        # Kansas overlaps two passes. A neutral province lies in California.
        # Guam has a contrived MEX core to exercise the continental guard.
        owners = dict.fromkeys(("126", "127", "198", "199", "232", "81", "116", "163", "2517"), "USA")
        owners.update({"104": "ENG", "200": "USS"})
        cores = {"2517": {"MEX"}}
        for transfer in transfers:
            for province, owner in owners.items():
                if owner != "USA":
                    continue

                def matches(node):
                    if node.key == "province_id":
                        return province == node.value
                    if node.key == "region":
                        return province in regions[node.value]
                    if node.key == "continent":
                        return province in continents[node.value]
                    if node.key == "is_core":
                        return node.value in cores.get(province, ())
                    raise AssertionError(node.key)

                if evaluate(section(transfer, "limit").children, matches):
                    owners[province] = scalar(transfer, "secede_province")
                    cores.setdefault(province, set()).add(scalar(transfer, "add_core"))
        self.assertEqual(owners, {
            "126": "MEX", "127": "MEX", "198": "USA", "199": "USS", "232": "NEN",
            "81": "UOR", "116": "DAK", "163": "USA", "2517": "USA", "104": "ENG", "200": "USS",
        })
        self.assertNotIn("104", cores)

    def test_dependent_returns_complete_before_the_tag_change(self):
        settlement = event("USSFlavor", 3755286)
        selection = section(section(section(section(settlement, "immediate"), "any_owned"), "owner"),
                            "any_country")
        dependent = event("USSFlavor", 5084910)
        immediate = section(dependent, "immediate")
        return_effect = section(section(immediate, "any_owned"), "owner")
        release = section(return_effect, "random_owned")
        self.assertEqual(shape(section(release, "limit").children),
                         [("owner", "=", [("vassal_of", "=", "USA")])])
        self.assertEqual(scalar(section(release, "USA"), "release_vassal"), "THIS")
        self.assertEqual(scalar(section(section(return_effect, "USA"), "any_owned"), "secede_province"), "THIS")
        self.assertFalse(any(n.key == "all_core" for n in walk(immediate.children)))

        trigger = section(event("USSFlavor", 1033676), "trigger")
        pending = scalar(selection, "set_country_flag")
        self.assertEqual(scalar(selection, "country_event"), "5084910")
        self.assertEqual(scalar(immediate, "clr_country_flag"), pending)
        blockade = [n for n in walk(trigger.children) if n.key == "any_country"]
        self.assertEqual([scalar(n, "has_country_flag") for n in blockade], [pending])
        self.assertEqual(scalar(trigger, "has_country_flag"), "uss_americas_settlement_complete")
        option = section(event("USSFlavor", 1033676), "option")
        conversion = section(option, "random_owned")
        guard = section(section(conversion, "limit"), "owner")
        self.assertEqual(scalar(guard, "has_country_flag"), scalar(trigger, "has_country_flag"))
        self.assertEqual(scalar(guard, "tag"), "USA")
        self.assertEqual(scalar(section(conversion, "owner"), "change_tag"), "UIL")

        for notice in (settlement, dependent):
            self.assertEqual([n.key for n in section(notice, "option").children], ["name"])
