"""Filesystem-only cases for the runtime lab commands."""

import argparse
import json
from pathlib import Path
from subprocess import CompletedProcess
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime_lab as lab


class RuntimeLabTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        for name in ("baselines", "fixtures", "scratch", "sessions", "transfer"):
            (self.root / name).mkdir()
        self.protected = self.root / "protected.txt"
        self.protected.write_text("baseline")
        lab.save_json(self.root / "baselines" / "host-protected-paths.json",
                      {"sentinel": str(self.protected)})

    def args(self, **kwargs):
        return argparse.Namespace(lab_root=self.root, run="test", **kwargs)

    def test_rebuild_leaves_protected_file_and_preserves_fixture(self):
        with patch.object(lab, "revision", return_value="a" * 40):
            result = lab.rebuild_smoke(self.args())
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["changed_scopes"], [])
        states = lab.read_json(self.root / "sessions/test/fixture-states.json")
        self.assertEqual(states["baseline"], states["reconstructed"])
        self.assertNotEqual(states["baseline"], states["mutated"])
        self.assertEqual(list((self.root / "scratch").iterdir()), [])
        self.assertEqual(self.protected.read_text(), "baseline")

    def test_sandbox_maps_only_dedicated_folders(self):
        inputs = self.root / "baselines/admission/input"
        inputs.mkdir(parents=True)
        (inputs / "sentinel.txt").write_text("probe")
        with patch.object(lab, "revision", return_value="a" * 40):
            result = lab.sandbox_config(self.args(baseline="admission", commit="HEAD",
                                                 engine="alice", profile="core", vgpu=False, cache_key=None))
        self.assertFalse(result["launched"])
        config = ElementTree.parse(self.root / "sessions/test/session.wsb")
        self.assertEqual(config.findtext("Networking"), "Disable")
        self.assertEqual(config.findtext("ClipboardRedirection"), "Disable")
        self.assertEqual(config.findtext("ProtectedClient"), "Enable")
        self.assertEqual(config.findtext("vGPU"), "Disable")
        maps = config.findall("MappedFolders/MappedFolder")
        self.assertEqual([element.findtext("ReadOnly") for element in maps], ["true", "true", "false"])
        self.assertEqual(Path(maps[2].findtext("HostFolder")), self.root / "transfer/test/outbox")
        lab.host_check(self.args(phase="before"))
        (inputs / "sentinel.txt").write_text("changed")
        result = lab.host_check(self.args(phase="after"))
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["changed_scopes"], ["lab-input"])
        with self.assertRaises(ValueError):
            lab.check_profile("alice", "core+extender")

    def test_archive_requires_matching_guest_receipt_and_host_check(self):
        (self.root / "sessions/test").mkdir()
        lab.host_check(self.args(phase="before"))
        lab.host_check(self.args(phase="after"))
        drop = self.root / "transfer/test/outbox/test"
        drop.mkdir(parents=True)
        (drop / "probe.txt").write_text("evidence")
        lab.save_json(drop / "export-sha256.json", lab.snapshot(drop))
        (drop / "probe.txt").write_text("modified")
        with self.assertRaisesRegex(ValueError, "differs"):
            lab.archive_export(self.args())
        (drop / "probe.txt").write_text("evidence")
        self.assertEqual(lab.archive_export(self.args())["status"], "verified")
        self.assertEqual(lab.snapshot(self.root / "sessions/test/raw"), lab.snapshot(drop))
        self.assertTrue(drop.is_dir())

    def test_guest_stage_uses_private_loader_paths_and_exact_userdir_bytes(self):
        cases = (
            ("victoria2", "core+extender", "Loader"),
            ("victoria2", "core+extender+1966", "Loader1966"),
            ("victoria2", "core", "Shared"),
            ("victoria2", "core+1966", "Shared"),
            ("alice", "core", "Shared"),
            ("alice", "core+1966", "Shared"),
        )
        commit = "a" * 40
        inputs = self.root / "inputs"
        inputs.mkdir()
        (inputs / "checkout.bundle").touch()
        for root in ("Loader", "Loader1966", "Shared"):
            (inputs / "games" / root).mkdir(parents=True)
        input_digest = lab.digest(lab.snapshot(inputs))

        for index, (engine, profile, root) in enumerate(cases):
            with self.subTest(engine=engine, profile=profile):
                workspace = self.root / f"guest-{index}"
                evidence = workspace / "Evidence"
                evidence.mkdir(parents=True)
                game = workspace / "Games" / root
                user_data = workspace / "UserData" / root
                state = workspace / "State" / root
                request = dict(engine=engine, profile=profile, commit=commit,
                               baseline_sha256=input_digest)
                summary = {"phases": {}}
                phases = []

                def run(command, *, stdout, **_kwargs):
                    if command[0] == "git":
                        return CompletedProcess(command, 0)
                    phase = command[3]
                    phases.append(phase)
                    self.assertEqual(command[4:10], ["--game-root", str(game),
                                                     "--state-root", str(state),
                                                     "--profile", profile])
                    if phase == "plan":
                        plan = dict(identity={"commit": commit}, profile=profile,
                                    root=str(workspace / "Checkout"), target=str(game),
                                    state_dir=str(state / "targets" / "fixture"),
                                    blockers=[], components=[], fingerprint="plan")
                        stdout.write(json.dumps(plan).encode("utf-8"))
                    elif phase == "apply":
                        stdout.write(b'{"digest": "payload"}')
                    return CompletedProcess(command, 0)

                with patch.object(lab, "revision", return_value=commit), patch.object(
                        lab.subprocess, "run", side_effect=run):
                    lab.stage_and_deploy(request, workspace, inputs, evidence, summary)

                self.assertEqual(phases, ["plan", "apply", "verify"])
                self.assertEqual(summary["status"], "pass")
                self.assertEqual([path.name for path in (workspace / "Games").iterdir()], [root])
                userdir = game / "userdir.txt"
                if root == "Shared":
                    self.assertFalse(userdir.exists())
                    self.assertFalse((workspace / "UserData").exists())
                else:
                    self.assertTrue(user_data.is_dir())
                    self.assertEqual(userdir.read_bytes(), str(user_data).encode("ascii"))
                self.assertFalse((inputs / "games" / root / "userdir.txt").exists())

    def test_sandbox_can_map_only_the_selected_cache_entry(self):
        inputs = self.root / "baselines/admission/input"
        inputs.mkdir(parents=True)
        (inputs / "sentinel.txt").write_text("probe")
        identity = {"profile": "core", "baseline_sha256": lab.digest(lab.snapshot(inputs))}
        key = lab.digest(identity)
        cached = self.root / "baselines/scenario-cache" / key
        payload = cached / "payload"
        payload.mkdir(parents=True)
        (payload / "scenario.bin").write_bytes(b"fixture")
        lab.save_json(cached / "receipt.json", {"identity": identity, "payload": lab.snapshot(payload)})
        with patch.object(lab, "revision", return_value="a" * 40):
            result = lab.sandbox_config(self.args(baseline="admission", commit="HEAD",
                                                  engine="alice", profile="core", vgpu=False, cache_key=key))
        self.assertEqual(result["cache_key"], key)
        config = ElementTree.parse(self.root / "sessions/test/session.wsb")
        entry = config.findall("MappedFolders/MappedFolder")[-1]
        self.assertEqual(entry.findtext("ReadOnly"), "true")
        self.assertEqual(Path(entry.findtext("HostFolder")), cached)

    def test_cache_miss_hit_and_hash_mismatch(self):
        folder = self.root / "payload"
        folder.mkdir()
        (folder / "scenario.bin").write_bytes(b"synthetic")
        cache = self.root / "cache"
        cache.mkdir()
        identity = self.root / "identity.json"
        metadata = {"engine_version": "1.3.0", "engine_sha256": "a" * 64,
                    "profile": "core", "manifest_sha256": "b" * 64, "baseline_sha256": "c" * 64,
                    "scenario_parameters": {"mode": "fixture"}, "scenario_checksum": "fixture-checksum"}
        lab.save_json(identity, metadata)
        restore = self.root / "restore"
        lookup = self.args(command="scenario-reuse", cache=cache, payload=restore, identity=identity)
        self.assertEqual(lab.scenario_cache(lookup)["status"], "miss")
        stored = lab.scenario_cache(self.args(command="scenario-store", cache=cache,
                                                  payload=folder, identity=identity))
        self.assertEqual(lab.scenario_cache(lookup)["status"], "reused")
        self.assertEqual(lab.snapshot(folder), lab.snapshot(restore))
        mounted = self.args(command="scenario-reuse", cache=None, entry=cache / stored["key"],
                            payload=self.root / "from-mount", identity=identity)
        self.assertEqual(lab.scenario_cache(mounted)["status"], "reused")
        identity.write_text(json.dumps({**metadata, "engine_version": "other"}))
        self.assertEqual(lab.scenario_cache(lookup)["status"], "miss")
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            lab.scenario_cache(mounted)
        identity.write_text(json.dumps(metadata))
        (cache / stored["key"] / "payload/scenario.bin").write_bytes(b"corrupted")
        with self.assertRaisesRegex(ValueError, "damaged"):
            lab.scenario_cache(lookup)
