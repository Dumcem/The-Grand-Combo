"""Static checks for the reconciled starting capitals and map references."""

import re
import unittest

from test_upstream_task42 import ROOT, decision, event
from lib_1966_parser import parse_script


CAPITALS = {
    'ABA': 1703, 'ARO': 1933, 'ASM': 1260, 'ATB': 3303, 'AWS': 1875, 'AZH': 2639,
    'BOR': 1299, 'DAM': 1952, 'DAR': 1842, 'ETH': 1855, 'GIZ': 1505, 'GPR': 2410,
    'GRH': 3346, 'HAR': 1853, 'KAF': 1847, 'KAZ': 1187, 'KBO': 1824, 'KGW': 2044,
    'KNG': 1898, 'KUB': 1986, 'LBA': 1989, 'MAI': 1294, 'MAK': 3258, 'MUD': 1302,
    'NAS': 565, 'ORI': 1263, 'OYO': 1927, 'PAL': 1290, 'QAT': 1165, 'RDL': 1117,
    'REU': 3255, 'RPP': 1292, 'SHA': 1355, 'SHI': 1233, 'SID': 1860, 'SLW': 1431,
    'SRN': 928, 'SUR': 1296, 'TIG': 1856, 'TRZ': 1776, 'WAD': 1823,
}
REMOVED_PROVINCES = {3604, 3662, 3663}
REMOVED_TERRAINS = {
    'urban_amapala', 'urban_anapa', 'urban_cordoba', 'urban_corrientes',
    'urban_ekaterinodar', 'urban_grozny', 'urban_gyumri', 'urban_kars',
    'urban_kutais', 'urban_mendoza', 'urban_novorossiysk', 'urban_parana',
    'urban_rosario', 'urban_salta', 'urban_santa_fe', 'urban_shemakha',
    'urban_shushi', 'urban_stavropol', 'urban_sukhum', 'urban_tucuman',
    'urban_vladikavkaz', 'urban_yelizavetpol', 'wonder_mount_elbrus',
    'wonder_mount_kazbek', 'wonder_noahs_mausoleum',
}


def read(path):
    return path.read_bytes().decode('latin-1')


def start_history(path):
    nodes = parse_script(read(path), file=str(path)).nodes
    dated = sorted((tuple(map(int, node.key.split('.'))), node) for node in nodes
                   if re.fullmatch(r'\d+\.\d+\.\d+', node.key or ''))
    return [node for node in nodes if not node.is_group] + [
        child for date, node in dated if date <= (1836, 1, 1)
        for child in node.children if not child.is_group
    ]


class MapReconciliationTests(unittest.TestCase):
    def test_starting_capitals_are_owned_controlled_cores_on_the_map(self):
        core = ROOT / 'TGC'
        definition = {int(row.split(';', 1)[0]) for row in read(core / 'map/definition.csv').splitlines()
                      if row.split(';', 1)[0].isdigit()}
        histories = {int(path.name.split(' ', 1)[0]): path
                     for path in (core / 'history/provinces').rglob('*.txt')
                     if path.name.split(' ', 1)[0].isdigit()}
        for tag, capital in CAPITALS.items():
            with self.subTest(tag=tag, capital=capital):
                country, = (core / 'history/countries').glob(f'{tag} - *.txt')
                self.assertEqual([node.value for node in start_history(country)
                                  if node.key == 'capital'][-1], str(capital))
                self.assertIn(capital, definition)
                province = start_history(histories[capital])
                for key in ('owner', 'controller'):
                    self.assertEqual([node.value for node in province if node.key == key][-1], tag)
                self.assertIn(tag, [node.value for node in province if node.key == 'add_core'])
        self.assertFalse(REMOVED_PROVINCES & (definition | histories.keys()))

    def test_removed_terrain_names_have_no_runtime_assignment(self):
        core = ROOT / 'TGC'
        map_terrain = read(core / 'map/terrain.txt')
        script_names = re.compile(r'\b(?:' + '|'.join(sorted(REMOVED_TERRAINS)) + r')\b')
        self.assertIsNone(script_names.search(map_terrain))
        for directory in ('history/provinces', 'events', 'decisions', 'common'):
            for path in (core / directory).rglob('*.txt'):
                active_text = re.sub(r'#[^\n]*', '', read(path))
                self.assertIsNone(script_names.search(active_text), str(path))

    def test_retired_rampur_and_retained_dominion_definition(self):
        core = ROOT / 'TGC'
        tags = read(core / 'common/countries.txt')
        self.assertNotRegex(tags, r'(?m)^\s*RAM\s*=')
        self.assertRegex(tags, r'(?m)^\s*D01\s*=')
        self.assertFalse((core / 'history/countries/RAM - Rampur.txt').exists())
        self.assertNotRegex(read(core / 'history/diplomacy/PuppetStates.txt'), r'\bsecond\s*=\s*RAM\b')

    def test_suspended_native_menu_leaves_existing_entry_points(self):
        event('TemperanceLeague', 100)
        for name in ('native_integration_status_on', 'native_protection_act'):
            self.assertIsNotNone(decision('New_World', name))
        timeline = ROOT / 'TGC_Timeline_1966'
        for directory in ('map', 'history'):
            self.assertFalse(list((timeline / directory).rglob('*.txt')))
