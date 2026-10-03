"""All write tests use disposable repositories and simulated game installations."""
import copy
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

TOOL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("deploy_tgc", TOOL / "deploy_tgc.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.real_active_processes = d.active_processes
        # Never inspect the user's active games in simulated filesystem tests.
        processes = mock.patch.object(d, "active_processes", return_value=[])
        processes.start()
        self.addCleanup(processes.stop)
        self.temp = tempfile.TemporaryDirectory(prefix="TGC deployment tests ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "canonical repo with spaces"
        self.game = self.base / "Victoria II simulated"
        self.state_base = self.base / "local metadata"
        self.root.mkdir()
        for name in ("mod", "common", "history", "map"):
            (self.game / name).mkdir(parents=True)
        (self.game / "v2game.exe").write_bytes(b"simulation only")
        self.catalog = json.loads((TOOL / "components.json").read_text())
        for c in self.catalog["components"]:
            if c["class"] == "utility/non-mod-target":
                continue
            source = self.root / c["source_dir"]
            source.mkdir(parents=True)
            root = next((x for x in c["runtime_policy"]["roots"] if "." not in x), None)
            self.put(source / root / "payload.txt", (c["id"] + "\r\n").encode())
            descriptor = self.root / c["source_descriptor"]
            descriptor.write_bytes((TOOL.parents[1] / c["source_descriptor"]).read_bytes())
        self.put(self.root / "TGC/settings.txt", b"graphics={fullscreen=no}\r\n")
        self.put(self.root / "TGC/common/empty.txt", b"")
        for path in ("TGC/docs/note.md", "TGC/tools/tool.py", "TGC/gfx/flags/flags.py",
                     "TGC_Timeline_1966/docs/note.md", "TGCBelleCartographieMap/README.md",
                     "TGCPastelMap/Readme.txt", "TGCPastelMap/Robau_font_Readme.txt"):
            self.put(self.root / path, b"excluded")
        self.catalog_path = self.root / "catalog.json"
        self.catalog_path.write_text(json.dumps(self.catalog))
        self.run_git("init", "-b", "master")
        self.run_git("config", "user.name", "Fixture")
        self.run_git("config", "user.email", "fixture@example.invalid")
        self.run_git("config", "core.autocrlf", "false")
        self.run_git("remote", "add", "origin", d.EXPECTED_ORIGIN)
        self.commit()
        self.put(self.game / "mod/CWE/data.txt", b"foreign")
        self.put(self.game / "mod/CWE.mod", b"foreign descriptor")
        self.put(self.game / "mod/dummy.txt", b"keep me")

    def put(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def run_git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))

    def commit(self):
        self.run_git("add", "--all")
        self.run_git("commit", "--quiet", "-m", "fixture")

    def plan(self, profile="core", optional=()):
        return d.build_plan(self.root, self.game, self.catalog_path, profile, optional, self.state_base)

    def apply(self, plan=None, adopt=False):
        return d.apply_plan(plan or self.plan(), self.root, self.game, self.catalog_path,
                            self.state_base, adopt)

    def verify(self):
        return d.verify_target(self.root, self.game, self.catalog_path, self.state_base)

    def rollback(self, txid):
        return d.rollback(self.root, self.game, self.catalog_path, txid, self.state_base)

    def pending(self, owned_lock=None):
        _, _, state_dir = d.target_paths(self.root, self.game, self.state_base)
        return d.pending(self.game, state_dir, self.catalog, owned_lock)

    def legacy(self):
        self.put(self.game / "mod/TGC/common/old.txt", b"old")
        self.put(self.game / "mod/TGC/stale.txt", b"stale")
        self.put(self.game / "mod/TGC.mod", b"old descriptor")

    def test_core_profile(self):
        manifest = self.apply()
        self.assertEqual(set(self.verify()), {"TGC"})
        self.assertFalse((self.game / "mod/TGC_Timeline_1966").exists())
        self.assertEqual(manifest["outcome"], "verified")

    def test_core_1966_profile(self):
        self.apply(self.plan("core+1966"))
        self.assertEqual(set(self.verify()), {"TGC", "TGC_Timeline_1966"})

    def test_optional_root(self):
        self.apply(self.plan(optional=["TGCFantasyFormables"]))
        self.assertIn("TGCFantasyFormables", self.verify())

    def test_niche_mapping(self):
        self.apply(self.plan(optional=["TGCOrganizedStacks"]))
        self.assertTrue((self.game / "mod/TGCOrganizedStacks").is_dir())
        self.assertTrue((self.game / "mod/TGCOrganizedStacks.mod").is_file())
        self.assertFalse((self.game / "mod/TGC Niche Submods").exists())

    def test_zero_byte_override(self):
        self.apply()
        self.assertEqual((self.game / "mod/TGC/common/empty.txt").read_bytes(), b"")

    def test_precise_exclusions_and_settings(self):
        self.apply(self.plan("core+1966", ["TGCPastelMap", "TGCBelleCartographieMap"]))
        for path in ("TGC/docs", "TGC/tools", "TGC/gfx/flags/flags.py", "TGC_Timeline_1966/docs",
                     "TGCPastelMap/Readme.txt", "TGCPastelMap/Robau_font_Readme.txt",
                     "TGCBelleCartographieMap/README.md"):
            self.assertFalse((self.game / "mod" / path).exists(), path)
        self.assertTrue((self.game / "mod/TGC/settings.txt").exists())

    def test_stale_removed_by_replacement(self):
        self.legacy()
        self.apply(adopt=True)
        self.assertFalse((self.game / "mod/TGC/stale.txt").exists())

    def test_foreign_mod_preserved(self):
        before = d.snapshot(self.game / "mod/CWE")
        self.apply()
        self.assertEqual(before, d.snapshot(self.game / "mod/CWE"))
        self.assertEqual((self.game / "mod/CWE.mod").read_bytes(), b"foreign descriptor")

    def test_dummy_preserved(self):
        self.apply()
        self.assertEqual((self.game / "mod/dummy.txt").read_bytes(), b"keep me")

    def test_wrong_installation(self):
        (self.game / "v2game.exe").unlink()
        with self.assertRaises(d.DeploymentError):
            self.plan()

    def test_unauthorized_target_plan(self):
        plan = self.plan()
        plan["target"] = str(self.base)
        with self.assertRaises(d.DeploymentError):
            self.apply(plan)
        self.assertFalse((self.game / ".tgc-deploy").exists())

    def test_traversal(self):
        for value in ("../CWE", "C:/mod", "a/../b", "a\\b", "C:relative", "CON", "a:stream", "a."):
            with self.subTest(value=value), self.assertRaises(d.DeploymentError):
                d.relative(value)

    def test_catalog_traversal(self):
        self.catalog["components"][0]["destination_dir"] = "../CWE"
        self.catalog_path.write_text(json.dumps(self.catalog))
        with self.assertRaises(d.DeploymentError):
            self.plan()

    def test_symlink_refused(self):
        link = self.root / "TGC/common/link.txt"
        try:
            link.symlink_to(self.game / "mod/dummy.txt")
        except OSError as exc:
            self.skipTest(f"Symlink privilege unavailable: {exc}")
        with self.assertRaises(d.DeploymentError):
            self.plan()

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction_refused(self):
        link = self.root / "TGC/common/junction"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.game / "common")],
                                capture_output=True)
        if result.returncode:
            self.skipTest("Junction creation unavailable")
        try:
            with self.assertRaises(d.DeploymentError):
                self.plan()
        finally:
            link.rmdir()  # remove junction itself, never its target

    def test_dirty_diagnostic_plan_not_applyable(self):
        self.put(self.root / "uncommitted.txt", b"dirty")
        plan = self.plan()
        self.assertTrue(plan["blockers"])
        with self.assertRaises(d.DeploymentError):
            self.apply(plan)

    def test_source_changed_after_plan(self):
        plan = self.plan()
        self.put(self.root / "TGC/common/empty.txt", b"new")
        with self.assertRaises(d.DeploymentError):
            self.apply(plan)

    def test_head_changed_after_plan(self):
        plan = self.plan()
        self.put(self.root / "TGC/common/empty.txt", b"new")
        self.commit()
        with self.assertRaises(d.DeploymentError):
            self.apply(plan)

    def test_live_changed_after_plan(self):
        plan = self.plan()
        self.put(self.game / "mod/TGC/extra.txt", b"new")
        with self.assertRaises(d.DeploymentError):
            self.apply(plan, adopt=True)

    def test_adoption_is_explicit(self):
        self.legacy()
        plan = self.plan()
        self.assertTrue(plan["components"][0]["adoption_required"])
        with self.assertRaises(d.DeploymentError):
            self.apply(plan)
        self.assertFalse((self.game / ".tgc-deploy").exists())

    def test_backup_complete_and_retained(self):
        self.legacy()
        original = d.snapshot(self.game / "mod/TGC")
        manifest = self.apply(adopt=True)
        backup = Path(manifest["backup"])
        self.assertEqual(d.snapshot(backup / "TGC"), original)
        self.rollback(manifest["transaction_id"])
        self.assertEqual(d.snapshot(backup / "TGC"), original)

    def test_successful_rollback(self):
        self.legacy()
        old = d.snapshot(self.game / "mod/TGC")
        manifest = self.apply(adopt=True)
        self.rollback(manifest["transaction_id"])
        self.assertEqual(d.snapshot(self.game / "mod/TGC"), old)

    def test_publication_error_rolls_back(self):
        self.legacy()
        old = d.snapshot(self.game / "mod/TGC")
        real_move = d.move
        def fail(source, target):
            if "staging" in Path(source).parts and Path(source).name == "TGC.mod":
                raise OSError("injected publication failure")
            return real_move(source, target)
        with mock.patch.object(d, "move", side_effect=fail), self.assertRaises(d.DeploymentError):
            self.apply(adopt=True)
        self.assertEqual(d.snapshot(self.game / "mod/TGC"), old)
        self.assertFalse(self.pending())

    def test_recovery_required_blocks_apply(self):
        real_move = d.move
        def fail(source, target):
            if "staging" in Path(source).parts and Path(source).name == "TGC.mod":
                raise OSError("publication failure")
            return real_move(source, target)
        with mock.patch.object(d, "move", side_effect=fail), \
                mock.patch.object(d, "restore_transaction", side_effect=OSError("recovery failure")), \
                self.assertRaisesRegex(d.DeploymentError, "Recovery required"):
            self.apply()
        self.assertTrue(self.pending())
        plan = self.plan()
        self.assertTrue(plan["blockers"])
        with self.assertRaises(d.DeploymentError):
            self.apply(plan)
        txid = self.pending()[0]
        self.rollback(txid)
        self.assertFalse(self.pending())

    def test_verify_missing(self):
        self.apply()
        (self.game / "mod/TGC/common/empty.txt").unlink()
        with self.assertRaises(d.DeploymentError):
            self.verify()

    def test_verify_extra(self):
        self.apply()
        self.put(self.game / "mod/TGC/extra.txt", b"extra")
        with self.assertRaises(d.DeploymentError):
            self.verify()

    def test_verify_size(self):
        self.apply()
        self.put(self.game / "mod/TGC/common/empty.txt", b"larger")
        with self.assertRaises(d.DeploymentError):
            self.verify()

    def test_verify_hash_same_size(self):
        self.apply()
        path = self.game / "mod/TGC/settings.txt"
        path.write_bytes(b"X" * path.stat().st_size)
        with self.assertRaises(d.DeploymentError):
            self.verify()

    def test_unselected_intact(self):
        self.put(self.game / "mod/TGCHFMMap/local.txt", b"untouched")
        before = d.snapshot(self.game / "mod/TGCHFMMap")
        self.apply()
        self.assertEqual(before, d.snapshot(self.game / "mod/TGCHFMMap"))

    def test_deterministic_digest_and_plan(self):
        self.assertEqual(d.digest({"b": 2, "a": 1}), d.digest({"a": 1, "b": 2}))
        self.assertEqual(self.plan(), self.plan())

    def test_paths_with_spaces(self):
        self.assertIn(" ", str(self.root))
        self.apply()
        self.verify()

    def test_plan_is_read_only(self):
        before = d.snapshot(self.game)
        self.plan("core+1966")
        self.assertEqual(before, d.snapshot(self.game))
        self.assertFalse(self.state_base.exists())

    def test_downgrade_preserves_timeline(self):
        self.apply(self.plan("core+1966"))
        before = d.snapshot(self.game / "mod/TGC_Timeline_1966")
        self.apply()
        self.assertEqual(before, d.snapshot(self.game / "mod/TGC_Timeline_1966"))
        self.assertEqual(set(self.verify()), {"TGC", "TGC_Timeline_1966"})

    def test_low_ram_refused(self):
        with self.assertRaises(d.DeploymentError):
            self.plan(optional=["TGCLowRam"])

    def test_descriptor_inconsistent(self):
        (self.root / "TGC.mod").write_text('name="wrong"\npath="mod/CWE"\n')
        with self.assertRaises(d.DeploymentError):
            self.plan()

    def test_manifest_tampering(self):
        m = self.apply()
        _, _, state = d.target_paths(self.root, self.game, self.state_base)
        path = state / "manifests" / (m["transaction_id"] + ".json")
        value = d.read_json(path)
        value["files"]["TGC/common/empty.txt"]["size"] = 1
        d.write_json(path, value)
        with self.assertRaises(d.DeploymentError):
            self.verify()

    def test_rollback_changed_live_refused(self):
        m = self.apply()
        self.put(self.game / "mod/TGC/user.txt", b"preserve")
        with self.assertRaises(d.DeploymentError):
            self.rollback(m["transaction_id"])
        self.assertEqual((self.game / "mod/TGC/user.txt").read_bytes(), b"preserve")

    def test_rollback_damaged_backup_refused(self):
        self.legacy()
        m = self.apply(adopt=True)
        self.put(Path(m["backup"]) / "TGC/stale.txt", b"damaged")
        before = d.snapshot(self.game / "mod/TGC")
        with self.assertRaises(d.DeploymentError):
            self.rollback(m["transaction_id"])
        self.assertEqual(before, d.snapshot(self.game / "mod/TGC"))

    def test_rollback_older_transaction_refused(self):
        first = self.apply()
        self.apply()
        with self.assertRaises(d.DeploymentError):
            self.rollback(first["transaction_id"])

    def test_tampered_plan_rejected(self):
        plan = self.plan()
        plan["units"][0]["name"] = "CWE"
        with self.assertRaises(d.DeploymentError):
            self.apply(plan)

    def test_active_game_refused(self):
        with mock.patch.object(d, "active_processes", return_value=["v2game.exe"]), \
                self.assertRaises(d.DeploymentError):
            self.apply()

    def assert_alice_variant_refused(self, image_name):
        self.legacy()
        plan = self.plan()
        before_game = d.snapshot(self.game)
        before_foreign = {name: d.snapshot(self.game / "mod" / name)
                          for name in ("CWE", "CWE.mod", "dummy.txt")}
        output = subprocess.CompletedProcess(
            ["tasklist", "/FO", "CSV", "/NH"], 0,
            (f'"{image_name}","1234","Console","1","100 K"\n'
             '"unrelated.exe","5678","Console","1","100 K"\n').encode(), b"")

        def enumerate_processes():
            # Exercise the real CSV parser and case handling, mocking only tasklist.
            with mock.patch.object(d.os, "name", "nt"), \
                    mock.patch.object(d.subprocess, "run", return_value=output) as tasklist:
                found = self.real_active_processes()
                tasklist.assert_called_once_with(
                    ["tasklist", "/FO", "CSV", "/NH"], capture_output=True, check=False)
                self.assertEqual(found, [image_name])
                return found

        with mock.patch.object(d, "active_processes", side_effect=enumerate_processes) as processes, \
                self.assertRaisesRegex(d.DeploymentError, "Game/launcher process active"):
            self.apply(plan, adopt=True)
        processes.assert_called_once_with()
        self.assertFalse((self.game / ".tgc-deploy").exists())
        self.assertFalse(self.state_base.exists())
        self.assertEqual(before_game, d.snapshot(self.game))
        self.assertEqual(before_foreign, {name: d.snapshot(self.game / "mod" / name)
                                        for name in before_foreign})

    def test_alice512_runtime_refuses_apply_before_transaction(self):
        self.assert_alice_variant_refused("Alice512.exe")

    def test_alicesse_runtime_refuses_apply_before_transaction(self):
        self.assert_alice_variant_refused("AliceSSE.exe")

    def test_process_inspection_failure_refused(self):
        with mock.patch.object(d, "active_processes", side_effect=d.DeploymentError("cannot inspect")), \
                self.assertRaises(d.DeploymentError):
            self.apply()
        self.assertFalse((self.game / ".tgc-deploy").exists())

    def test_invalid_transaction_path(self):
        with self.assertRaises(d.DeploymentError):
            self.rollback("../CWE")

    def test_refused_rollback_does_not_poison_verified_transaction(self):
        m = self.apply()
        self.put(self.game / "mod/TGC/user.txt", b"preserve")
        with self.assertRaises(d.DeploymentError):
            self.rollback(m["transaction_id"])
        self.assertFalse(self.pending())

    def test_backup_junction_refused(self):
        self.legacy()
        m = self.apply(adopt=True)
        saved = Path(m["backup"]) / "TGC"
        link = saved / "link.txt"
        try:
            link.symlink_to(self.game / "mod/dummy.txt")
        except OSError as exc:
            self.skipTest(f"Symlink privilege unavailable: {exc}")
        with self.assertRaises(d.DeploymentError):
            self.rollback(m["transaction_id"])

    def test_overlap_refused(self):
        with self.assertRaises(d.DeploymentError):
            d.target_paths(self.root, self.root, self.state_base)

    def test_windows_collision(self):
        self.catalog["components"][1]["destination_dir"] = "tgc"
        self.catalog_path.write_text(json.dumps(self.catalog))
        with self.assertRaises(d.DeploymentError):
            self.plan()

    def test_after_rename_before_journal_error_rolls_back(self):
        self.legacy()
        old = d.snapshot(self.game / "mod/TGC")
        real_move = d.move
        def fail(source, destination):
            real_move(source, destination)
            if "staging" in Path(source).parts and Path(source).name == "TGC":
                raise OSError("crash window after rename")
        with mock.patch.object(d, "move", side_effect=fail), self.assertRaises(d.DeploymentError):
            self.apply(adopt=True)
        self.assertEqual(d.snapshot(self.game / "mod/TGC"), old)
        self.assertFalse(self.pending())

    def test_source_changes_during_staging(self):
        real_copy = d.shutil.copyfile
        modified = False
        def change(source, destination, *args, **kwargs):
            nonlocal modified
            result = real_copy(source, destination, *args, **kwargs)
            if not modified and "staging" in Path(destination).parts:
                modified = True
                self.put(self.root / "TGC/common/empty.txt", b"changed")
            return result
        with mock.patch.object(d.shutil, "copyfile", side_effect=change), self.assertRaises(d.DeploymentError):
            self.apply()
        self.assertFalse((self.game / "mod/TGC").exists())

    def test_content_digest_independent_of_file_timestamp(self):
        plan = self.plan()
        os.utime(self.root / "TGC/common/empty.txt", (1000000000, 1000000000))
        self.assertEqual(plan, self.plan())

    def test_utf8_bom_plan(self):
        path = self.base / "plan.json"
        path.write_text(json.dumps(self.plan()), encoding="utf-8-sig")
        self.assertEqual(d.read_json(path), self.plan())

    def test_invalid_journal_mapping_refused_before_writes(self):
        m = self.apply()
        path = self.game / ".tgc-deploy/transactions" / m["transaction_id"] / "journal.json"
        journal = d.read_json(path)
        journal["units"][0]["name"] = "../CWE"
        d.write_json(path, journal)
        before = d.snapshot(self.game / "mod")
        with self.assertRaises(d.DeploymentError):
            self.rollback(m["transaction_id"])
        self.assertEqual(before, d.snapshot(self.game / "mod"))

    @unittest.skipUnless(os.name == "nt", "Windows file attributes")
    def test_readonly_selected_file_refused(self):
        import ctypes
        self.legacy()
        path = self.game / "mod/TGC/stale.txt"
        self.assertTrue(ctypes.windll.kernel32.SetFileAttributesW(str(path), 1))
        try:
            with self.assertRaises(d.DeploymentError):
                self.apply(adopt=True)
            self.assertFalse((self.game / ".tgc-deploy").exists())
        finally:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x80)

    def test_foreign_junction_not_traversed(self):
        if os.name != "nt":
            self.skipTest("Windows junction test")
        link = self.game / "mod/foreign-junction"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.base / "canonical repo with spaces")],
                                capture_output=True)
        if result.returncode:
            self.skipTest("Junction creation unavailable")
        try:
            plan = self.plan()
            self.assertIn("foreign-junction", plan["preserved"])
            self.apply(plan)
            self.assertTrue(link.exists())
        finally:
            link.rmdir()

    def test_active_owner_lock_not_removed(self):
        lock = self.game / ".tgc-deploy/lock"
        d.write_json(lock, {"pid": os.getpid(), "started_utc": "fixture"})
        if os.name == "nt":
            output = subprocess.CompletedProcess([], 0, f'"python.exe","{os.getpid()}"\n'.encode(), b"")
            with mock.patch.object(d.subprocess, "run", return_value=output), self.assertRaises(d.DeploymentError):
                d.recover_stale_lock(self.game)
        else:
            with self.assertRaises(d.DeploymentError):
                d.recover_stale_lock(self.game)
        self.assertTrue(lock.exists())

    def test_demonstrably_stale_lock_removed(self):
        lock = self.game / ".tgc-deploy/lock"
        d.write_json(lock, {"pid": 123456789, "started_utc": "fixture"})
        if os.name == "nt":
            output = subprocess.CompletedProcess([], 0, b"no tasks\n", b"")
            with mock.patch.object(d.subprocess, "run", return_value=output):
                d.recover_stale_lock(self.game)
        else:
            with mock.patch.object(d.os, "kill", side_effect=ProcessLookupError):
                d.recover_stale_lock(self.game)
        self.assertFalse(lock.exists())

    def tx_paths(self, txid):
        _, _, state_dir = d.target_paths(self.root, self.game, self.state_base)
        return self.game / ".tgc-deploy/transactions" / txid, state_dir

    def assert_foreign(self):
        self.assertEqual((self.game / "mod/CWE/data.txt").read_bytes(), b"foreign")
        self.assertEqual((self.game / "mod/CWE.mod").read_bytes(), b"foreign descriptor")
        self.assertEqual((self.game / "mod/dummy.txt").read_bytes(), b"keep me")

    def test_f1_identical_successor_and_status_tampering(self):
        first = self.apply()
        second = self.apply()
        self.assertEqual(first["files"], second["files"])
        tx, _ = self.tx_paths(first["transaction_id"])
        journal = d.read_json(tx / "journal.json")
        before = d.snapshot(self.game / "mod")
        for status in ("verified", "publishing", "recovery-required", "rolled-back"):
            with self.subTest(status=status):
                journal["status"] = status
                d.write_json(tx / "journal.json", journal)
                with self.assertRaises(d.DeploymentError):
                    self.rollback(first["transaction_id"])
                self.assertEqual(before, d.snapshot(self.game / "mod"))

    def test_f1_journal_authority_mutations_refused(self):
        m = self.apply()
        tx, _ = self.tx_paths(m["transaction_id"])
        original = d.read_json(tx / "journal.json")
        optional = self.catalog["components"][2]
        attacks = []
        added = copy.deepcopy(original)
        for name, source, kind in ((optional["destination_dir"], optional["source_dir"], "directory"),
                                  (optional["destination_descriptor"], optional["source_descriptor"], "file")):
            added["units"].append({"component": optional["id"], "name": name, "source": source,
                                   "old": {"kind": "absent"}, "new": d.snapshot(self.root / source)})
        attacks.append(("unselected optional", added))
        for label, edit in (
                ("previous state", lambda j: j["previous_state"]["components"].update({"TGC": {"invented": True}})),
                ("mapping", lambda j: j["units"][0].update(name=optional["destination_dir"])),
                ("old snapshot", lambda j: j["units"][0].update(old=j["units"][0]["new"])),
                ("new snapshot", lambda j: j["units"][0].update(new={"kind": "absent"})),
                ("profile", lambda j: j["plan"].update(profile="core+1966")),
                ("adoption", lambda j: j.update(adopt_existing=True))):
            changed = copy.deepcopy(original)
            edit(changed)
            attacks.append((label, changed))
        before = d.snapshot(self.game / "mod")
        for label, journal in attacks:
            with self.subTest(attack=label):
                d.write_json(tx / "journal.json", journal)
                with self.assertRaises(d.DeploymentError):
                    self.rollback(m["transaction_id"])
                self.assertEqual(before, d.snapshot(self.game / "mod"))
        d.write_json(tx / "journal.json", original)
        self.rollback(m["transaction_id"])

    def test_f1_single_record_corruption_refused(self):
        m = self.apply()
        tx, _ = self.tx_paths(m["transaction_id"])
        record = d.read_json(tx / "record.json")
        record["previous_state"]["components"]["TGC"] = {"invented": True}
        d.write_json(tx / "record.json", record)
        before = d.snapshot(self.game / "mod")
        with self.assertRaises(d.DeploymentError):
            self.rollback(m["transaction_id"])
        self.assertEqual(before, d.snapshot(self.game / "mod"))

    def test_f1_cross_target_and_state_root_refused(self):
        m = self.apply()
        tx, state_dir = self.tx_paths(m["transaction_id"])
        other_game = self.base / "another simulated installation"
        d.shutil.copytree(self.game, other_game)
        _, _, other_state = d.target_paths(self.root, other_game, self.state_base)
        d.shutil.copytree(state_dir, other_state)
        before = d.snapshot(other_game / "mod")
        with self.assertRaises(d.DeploymentError):
            d.rollback(self.root, other_game, self.catalog_path, m["transaction_id"], self.state_base)
        with self.assertRaises(d.DeploymentError):
            d.rollback(self.root, self.game, self.catalog_path, m["transaction_id"], self.base / "other state")
        self.assertEqual(before, d.snapshot(other_game / "mod"))

    def test_f1_normal_rollback_cannot_use_recovery_tolerance(self):
        self.legacy()
        old_descriptor = (self.game / "mod/TGC.mod").read_bytes()
        m = self.apply(adopt=True)
        new_descriptor = (self.game / "mod/TGC.mod").read_bytes()
        tx, _ = self.tx_paths(m["transaction_id"])
        journal = d.read_json(tx / "journal.json")
        for status in ("verified", "publishing", "recovery-required"):
            for content in (None, old_descriptor):
                with self.subTest(status=status, absent=content is None):
                    journal["status"] = status
                    d.write_json(tx / "journal.json", journal)
                    path = self.game / "mod/TGC.mod"
                    if content is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.write_bytes(content)
                    before = d.snapshot(self.game / "mod")
                    with self.assertRaises(d.DeploymentError):
                        self.rollback(m["transaction_id"])
                    self.assertEqual(before, d.snapshot(self.game / "mod"))
                    path.write_bytes(new_descriptor)
        journal["status"] = "verified"
        d.write_json(tx / "journal.json", journal)
        self.rollback(m["transaction_id"])

    def test_f2_fabricated_state_even_with_matching_live_refused(self):
        plan = self.plan()
        _, _, state_dir = d.target_paths(self.root, self.game, self.state_base)
        for u in plan["units"]:
            source = self.root / u["source"]
            destination = self.game / "mod" / u["name"]
            if source.is_dir():
                d.shutil.copytree(source, destination)
            else:
                d.shutil.copyfile(source, destination)
        fake = {"schema": d.SCHEMA, "target": str(self.game), "components": {"TGC": {
            "transaction_id": "f" * 32, "commit": plan["identity"]["commit"],
            "mapping": [u["name"] for u in plan["units"]],
            "snapshots": {u["name"]: d.snapshot(self.game / "mod" / u["name"]) for u in plan["units"]}}}}
        d.write_json(state_dir / "state.json", fake)
        before = d.snapshot(self.game / "mod")
        for adopt in (False, True):
            with self.subTest(adopt=adopt), self.assertRaisesRegex(d.DeploymentError, "state is untrusted"):
                self.apply(plan, adopt=adopt)
        self.assertEqual(before, d.snapshot(self.game / "mod"))
        self.assertFalse((self.game / ".tgc-deploy").exists())

    def test_f2_state_and_manifest_corruption_fail_closed(self):
        m = self.apply()
        tx, state_dir = self.tx_paths(m["transaction_id"])
        state_path = state_dir / "state.json"
        manifest_path = state_dir / "manifests" / (m["transaction_id"] + ".json")
        original_state, original_manifest = d.read_json(state_path), d.read_json(manifest_path)
        before = d.snapshot(self.game / "mod")
        attacks = ("missing transaction", "missing manifest", "invalid JSON", "other target",
                   "mapping mismatch", "snapshot mismatch", "wrong component", "wrong schema",
                   "missing completion", "rewound ownership")
        receipt_path = tx / "completed.json"
        original_receipt = d.read_json(receipt_path)
        for attack in attacks:
            with self.subTest(attack=attack):
                state, manifest = copy.deepcopy(original_state), copy.deepcopy(original_manifest)
                if attack == "missing transaction":
                    state["components"]["TGC"]["transaction_id"] = "f" * 32
                elif attack == "mapping mismatch":
                    state["components"]["TGC"]["mapping"] = ["CWE", "CWE.mod"]
                elif attack == "rewound ownership":
                    state["components"] = {}
                elif attack == "other target":
                    manifest["target"] = str(self.base)
                elif attack == "snapshot mismatch":
                    manifest["mapping"][0]["new"] = {"kind": "absent"}
                elif attack == "wrong component":
                    manifest["components"][0]["id"] = "TGCFantasyFormables"
                elif attack == "wrong schema":
                    state["schema"] = 99
                d.write_json(state_path, state)
                d.write_json(manifest_path, manifest)
                if attack == "missing manifest":
                    manifest_path.unlink()
                elif attack == "invalid JSON":
                    manifest_path.write_text("{broken")
                elif attack == "missing completion":
                    receipt_path.unlink()
                with self.assertRaisesRegex(d.DeploymentError, "state is untrusted"):
                    self.plan()
                with self.assertRaises(d.DeploymentError):
                    self.apply(adopt=True)
                self.assertEqual(before, d.snapshot(self.game / "mod"))
                d.write_json(state_path, original_state)
                d.write_json(manifest_path, original_manifest)
                d.write_json(receipt_path, original_receipt)
        self.verify()

    def test_f2_rewinding_state_to_valid_older_owner_refused(self):
        self.apply()
        _, _, state_dir = d.target_paths(self.root, self.game, self.state_base)
        old_state = d.read_json(state_dir / "state.json")
        self.apply()
        d.write_json(state_dir / "state.json", old_state)
        with self.assertRaisesRegex(d.DeploymentError, "state is untrusted"):
            self.plan()

    def test_f3_predictable_hardlink_is_untouched(self):
        external = self.base / "external.txt"
        external.write_bytes(b"external must survive")
        final = self.base / "safe.json"
        predictable = self.base / "safe.json.tmp"
        try:
            os.link(external, predictable)
        except OSError as exc:
            self.skipTest(f"Hardlink creation unavailable: {exc}")
        real_replace = d.os.replace
        temporaries = []
        def replace(source, target):
            temporaries.append(Path(source))
            self.assertNotEqual(Path(source), predictable)
            self.assertEqual(Path(source).parent, final.parent)
            return real_replace(source, target)
        with mock.patch.object(d.os, "replace", side_effect=replace):
            d.write_json(final, {"safe": True})
        self.assertEqual(external.read_bytes(), b"external must survive")
        self.assertEqual(predictable.read_bytes(), b"external must survive")
        self.assertEqual(d.read_json(final), {"safe": True})
        self.assertEqual(len(temporaries), 1)
        self.assertFalse(temporaries[0].exists())

    def test_f3_exclusive_creation_retries_existing_candidate(self):
        final = self.base / "safe.json"
        collision = self.base / "safe.json.collision.tmp"
        collision.write_bytes(b"preexisting must survive")
        with mock.patch.object(d.tempfile, "_get_candidate_names", return_value=iter(("collision", "fresh"))):
            d.write_json(final, {"safe": True})
        self.assertEqual(collision.read_bytes(), b"preexisting must survive")
        self.assertEqual(d.read_json(final), {"safe": True})
        self.assertFalse((self.base / "safe.json.fresh.tmp").exists())

    def test_f3_failed_replace_cleans_only_own_temporary(self):
        final = self.base / "safe.json"
        final.write_bytes(b"original")
        predictable = self.base / "safe.json.tmp"
        predictable.write_bytes(b"preserve")
        with mock.patch.object(d.os, "replace", side_effect=OSError("replace failed")), self.assertRaises(OSError):
            d.write_json(final, {})
        self.assertEqual(final.read_bytes(), b"original")
        self.assertEqual(predictable.read_bytes(), b"preserve")
        self.assertEqual(set(self.base.glob("safe.json.*.tmp")), set())

    def test_f4_rollback_interruptions_and_retry_for_both_units(self):
        for name in ("TGC", "TGC.mod"):
            for point in ("partial-copy", "ready", "after-displace", "after-publish", "before-verification"):
                with self.subTest(unit=name, point=point):
                    self.legacy()
                    before = d.snapshot(self.game / "mod/TGC"), d.snapshot(self.game / "mod/TGC.mod")
                    m = self.apply(adopt=True)
                    tx, _ = self.tx_paths(m["transaction_id"])
                    real_copy, real_move, real_write = d.shutil.copyfile, d.move, d.write_json
                    injected = False
                    def copyfile(source, target, *args, **kwargs):
                        nonlocal injected
                        if point == "partial-copy" and "rollback-staging" in Path(target).parts and name in Path(target).parts and not injected:
                            injected = True
                            Path(target).write_bytes(b"partial")
                            raise OSError("injected partial rollback copy")
                        return real_copy(source, target, *args, **kwargs)
                    def move(source, target):
                        nonlocal injected
                        result = real_move(source, target)
                        matched = (point == "after-displace" and Path(target) == tx / "displaced" / name) or (point == "after-publish" and Path(source) == tx / "rollback-staging" / name)
                        if matched and not injected:
                            injected = True
                            raise OSError("injected rename crash window")
                        return result
                    def write(path, value):
                        nonlocal injected
                        result = real_write(path, value)
                        phase = value.get("rollback_units", {}).get(name) if isinstance(value, dict) else None
                        if not injected and Path(path) == tx / "journal.json" and ((point == "ready" and phase == "ready") or (point == "before-verification" and phase == "published")):
                            injected = True
                            raise OSError("injected checkpoint interruption")
                        return result
                    with mock.patch.object(d.shutil, "copyfile", side_effect=copyfile), mock.patch.object(d, "move", side_effect=move), mock.patch.object(d, "write_json", side_effect=write):
                        with self.assertRaises((d.DeploymentError, OSError)):
                            self.rollback(m["transaction_id"])
                    self.assertTrue(injected)
                    self.assertIn(m["transaction_id"], self.pending())
                    self.assert_foreign()
                    self.rollback(m["transaction_id"])
                    self.assertEqual(before, (d.snapshot(self.game / "mod/TGC"), d.snapshot(self.game / "mod/TGC.mod")))
                    self.assertFalse(self.pending())
                    self.assert_foreign()

    def test_f4_absent_component_displacement_retry(self):
        m = self.apply()
        tx, _ = self.tx_paths(m["transaction_id"])
        real_move = d.move
        def move(source, target):
            real_move(source, target)
            if Path(target) == tx / "displaced/TGC.mod":
                raise OSError("after absent-component displacement")
        with mock.patch.object(d, "move", side_effect=move), self.assertRaises(OSError):
            self.rollback(m["transaction_id"])
        self.assert_foreign()
        self.rollback(m["transaction_id"])
        self.assertFalse((self.game / "mod/TGC").exists())
        self.assertFalse((self.game / "mod/TGC.mod").exists())
        self.assert_foreign()

    def test_f4_retry_unexpected_live_preserves_everything(self):
        self.legacy()
        m = self.apply(adopt=True)
        tx, _ = self.tx_paths(m["transaction_id"])
        real_move = d.move
        def move(source, target):
            real_move(source, target)
            if Path(target) == tx / "displaced/TGC.mod":
                raise OSError("displaced")
        with mock.patch.object(d, "move", side_effect=move), self.assertRaises(OSError):
            self.rollback(m["transaction_id"])
        self.put(self.game / "mod/TGC.mod", b"foreign intervention")
        before = d.snapshot(self.game / "mod")
        with self.assertRaises(d.DeploymentError):
            self.rollback(m["transaction_id"])
        self.assertEqual(before, d.snapshot(self.game / "mod"))
        self.assertIn(m["transaction_id"], self.pending())

    def test_f4_rollback_restores_previous_verified_owner(self):
        first = self.apply()
        self.put(self.root / "TGC/common/empty.txt", b"second version")
        self.commit()
        second = self.apply()
        self.rollback(second["transaction_id"])
        self.assertEqual(self.verify()["TGC"]["transaction_id"], first["transaction_id"])
        self.rollback(first["transaction_id"])
        self.assertFalse((self.game / "mod/TGC").exists())

    def test_f4_retry_after_state_and_terminal_receipts(self):
        for point in ("after-state", "after-receipts"):
            with self.subTest(point=point):
                self.legacy()
                old = d.snapshot(self.game / "mod")
                m = self.apply(adopt=True)
                tx, state_dir = self.tx_paths(m["transaction_id"])
                real_write = d.write_json
                injected = False
                def write(path, value):
                    nonlocal injected
                    if not injected and point == "after-receipts" and Path(path) == tx / "journal.json" and value.get("status") == "rolled-back":
                        injected = True
                        raise OSError("before terminal journal")
                    result = real_write(path, value)
                    if not injected and point == "after-state" and Path(path) == state_dir / "state.json":
                        injected = True
                        raise OSError("after restored state")
                    return result
                with mock.patch.object(d, "write_json", side_effect=write), self.assertRaises(OSError):
                    self.rollback(m["transaction_id"])
                self.assertTrue(injected)
                self.assertEqual(old, d.snapshot(self.game / "mod"))
                self.rollback(m["transaction_id"])
                self.assertFalse(self.pending())
                self.assert_foreign()

    def test_f5_owned_lock_does_not_hide_incomplete_journal(self):
        folder = self.game / ".tgc-deploy/transactions" / ("a" * 32)
        d.write_json(folder / "journal.json", {"status": "recovery-required"})
        with d.target_lock(self.game) as lock:
            self.assertEqual(self.pending(lock), ["a" * 32])
            self.assertEqual(self.pending(), ["a" * 32, "target-lock"])

    def test_f5_interleaving_is_rechecked_under_lock(self):
        plan = self.plan()
        real_lock = d.target_lock
        txid = "b" * 32
        @contextlib.contextmanager
        def interleave(game):
            # A finished preflight; B left recovery-required and released its lock.
            with real_lock(game):
                d.write_json(game / ".tgc-deploy/transactions" / txid / "journal.json", {"status": "recovery-required"})
            with real_lock(game) as token:
                yield token
        before = d.snapshot(self.game / "mod")
        with mock.patch.object(d, "target_lock", side_effect=interleave), self.assertRaisesRegex(d.DeploymentError, "Incomplete transaction"):
            self.apply(plan)
        self.assertEqual(before, d.snapshot(self.game / "mod"))
        self.assertEqual({p.name for p in (self.game / ".tgc-deploy/transactions").iterdir()}, {txid})

    def test_f5_other_owner_lock_refuses_apply(self):
        plan = self.plan()
        d.write_json(self.game / ".tgc-deploy/lock", {"pid": 123, "token": "another owner"})
        before = d.snapshot(self.game / "mod")
        with self.assertRaises(d.DeploymentError):
            self.apply(plan)
        self.assertEqual(before, d.snapshot(self.game / "mod"))

    def test_f5_own_lock_with_no_pending_is_allowed(self):
        with d.target_lock(self.game) as lock:
            self.assertEqual(self.pending(lock), [])
            self.assertEqual(self.pending(), ["target-lock"])
        self.apply()
        self.verify()

    def interrupt_rollback_ready(self, txid):
        tx, state_dir = self.tx_paths(txid)
        real_write = d.write_json
        injected = False
        def write(path, value):
            nonlocal injected
            result = real_write(path, value)
            phases = value.get("rollback_units", {})
            if (not injected and Path(path) == tx / "journal.json"
                    and phases == {"TGC": "ready", "TGC.mod": "ready"}):
                injected = True
                raise OSError("R1 interruption after rollback staging ready")
            return result
        with mock.patch.object(d, "write_json", side_effect=write), mock.patch.object(d, "move") as move:
            with self.assertRaisesRegex(OSError, "R1 interruption"):
                self.rollback(txid)
            move.assert_not_called()
        self.assertTrue(injected)
        journal = d.read_json(tx / "journal.json")
        self.assertEqual(journal["status"], "recovery-required")
        record = d.validate_journal(journal, self.game, self.catalog, state_dir)
        self.assertIsNotNone(d.receipt(self.game, state_dir, record, "completed"))
        self.assertIsNotNone(d.receipt(self.game, state_dir, record, "rollback-authorized"))
        self.assertIsNone(d.receipt(self.game, state_dir, record, "restored"))
        for unit in record["units"]:
            self.assertEqual(d.snapshot(tx / "rollback-staging" / unit["name"]), unit["old"])
            self.assertEqual(d.snapshot(tx / "displaced" / unit["name"]), {"kind": "absent"})
        self.assertIn(txid, self.pending())
        return tx, state_dir

    def test_r1_authorized_rollback_remains_pending_after_terminal_status(self):
        self.legacy()
        original = d.snapshot(self.game / "mod")
        first = self.apply(adopt=True)
        txid = first["transaction_id"]
        live = d.snapshot(self.game / "mod")
        tx, state_dir = self.interrupt_rollback_ready(txid)
        self.assertEqual(live, d.snapshot(self.game / "mod"))
        interrupted = d.read_json(tx / "journal.json")
        # Change only this operational field, leaving both receipt copies intact.
        changed = copy.deepcopy(interrupted)
        changed["status"] = "verified"
        d.write_json(tx / "journal.json", changed)
        self.assertEqual({k: v for k, v in changed.items() if k != "status"},
                         {k: v for k, v in interrupted.items() if k != "status"})
        self.assertIn(txid, self.pending())
        with self.assertRaisesRegex(d.DeploymentError, "Incomplete transaction"):
            self.verify()
        second = self.plan()  # Byte-identical T2 must still be blocked.
        self.assertEqual(second["components"][0]["status"], "identical")
        self.assertIn("Incomplete transaction/lock: recovery required", second["blockers"])
        before_game, before_state = d.snapshot(self.game), d.snapshot(state_dir)
        with mock.patch.object(d.shutil, "copyfile") as copyfile, mock.patch.object(d, "move") as move:
            with self.assertRaisesRegex(d.DeploymentError, "Incomplete transaction"):
                self.apply(second)
            copyfile.assert_not_called()
            move.assert_not_called()
        self.assertEqual(before_game, d.snapshot(self.game))
        self.assertEqual(before_state, d.snapshot(state_dir))
        self.assertEqual({p.name for p in tx.parent.iterdir()}, {txid})
        self.assertEqual(live, d.snapshot(self.game / "mod"))
        self.assert_foreign()
        self.rollback(txid)
        record = d.load_record(self.game, state_dir, self.catalog, txid)
        self.assertIsNotNone(d.receipt(self.game, state_dir, record, "restored"))
        self.assertEqual(d.read_json(tx / "journal.json")["status"], "rolled-back")
        self.assertFalse(self.pending())
        self.assertEqual(original, d.snapshot(self.game / "mod"))
        self.assert_foreign()

    def test_r1_rolled_back_status_without_restored_remains_pending(self):
        self.legacy()
        first = self.apply(adopt=True)
        txid = first["transaction_id"]
        tx, _ = self.interrupt_rollback_ready(txid)
        journal = d.read_json(tx / "journal.json")
        journal["status"] = "rolled-back"
        d.write_json(tx / "journal.json", journal)
        self.assertIn(txid, self.pending())
        with self.assertRaisesRegex(d.DeploymentError, "Incomplete transaction"):
            self.apply()
        with self.assertRaisesRegex(d.DeploymentError, "Incomplete transaction"):
            self.verify()
        self.rollback(txid)
        self.assertFalse(self.pending())

    def test_r1_discordant_rollback_receipts_fail_closed(self):
        self.legacy()
        first = self.apply(adopt=True)
        txid = first["transaction_id"]
        tx, state_dir = self.interrupt_rollback_ready(txid)
        journal = d.read_json(tx / "journal.json")
        journal["status"] = "verified"
        d.write_json(tx / "journal.json", journal)
        authorization = d.read_json(tx / "rollback-authorized.json")
        record = d.load_record(self.game, state_dir, self.catalog, txid)
        for attack in ("authorization copy", "authorization mode", "restored copy"):
            with self.subTest(attack=attack):
                if attack == "restored copy":
                    d.write_receipt(self.game, state_dir, record, "restored")
                    value = d.read_json(tx / "restored.json")
                    value["record_digest"] = "0" * 64
                    d.write_json(tx / "restored.json", value)
                else:
                    value = dict(authorization, mode="recovery")
                    d.write_json(tx / "rollback-authorized.json", value)
                    if attack == "authorization mode":
                        d.write_json(state_dir / "rollback-authorized" / (txid + ".json"), value)
                self.assertIn(txid, self.pending())
                before_game, before_state = d.snapshot(self.game), d.snapshot(state_dir)
                with self.assertRaises(d.DeploymentError):
                    self.apply()
                with self.assertRaises(d.DeploymentError):
                    self.verify()
                with self.assertRaises(d.DeploymentError):
                    self.rollback(txid)
                self.assertEqual(before_game, d.snapshot(self.game))
                self.assertEqual(before_state, d.snapshot(state_dir))
                d.write_json(tx / "rollback-authorized.json", authorization)
                d.write_json(state_dir / "rollback-authorized" / (txid + ".json"), authorization)
                if attack == "restored copy":
                    (tx / "restored.json").unlink()
                    (state_dir / "restored" / (txid + ".json")).unlink()
        self.rollback(txid)
        self.assertFalse(self.pending())
        self.assert_foreign()

    def interrupt_rollback_terminal(self, txid):
        tx, state_dir = self.tx_paths(txid)
        real_write = d.write_json
        injected = False
        def write(path, value):
            nonlocal injected
            if (not injected and Path(path) == tx / "journal.json"
                    and value.get("status") == "rolled-back"):
                injected = True
                raise OSError("R2 interruption before terminal journal")
            return real_write(path, value)
        with mock.patch.object(d, "write_json", side_effect=write):
            with self.assertRaisesRegex(OSError, "R2 interruption"):
                self.rollback(txid)
        self.assertTrue(injected)
        journal = d.read_json(tx / "journal.json")
        self.assertEqual(journal["status"], "recovery-required")
        record = d.validate_journal(journal, self.game, self.catalog, state_dir)
        for name in ("completed", "rollback-authorized", "restored"):
            self.assertIsNotNone(d.receipt(self.game, state_dir, record, name))
        self.assertEqual(d.receipt(self.game, state_dir, record, "rollback-authorized")["mode"],
                         "rollback")
        d.validated_manifest(self.game, state_dir, record)
        for unit in record["units"]:
            self.assertEqual(d.snapshot(self.game / "mod" / unit["name"]), unit["old"])
        self.assertIn(txid, self.pending())
        return tx, state_dir

    def r2_terminal_fixture(self):
        self.legacy()
        self.put(self.game / "mod/TGCHFMMap/local.txt", b"unselected optional")
        self.put(self.game / "mod/TGCHFMMap.mod", b"unselected descriptor")
        original = d.snapshot(self.game / "mod")
        txid = self.apply(adopt=True)["transaction_id"]
        tx, state_dir = self.interrupt_rollback_terminal(txid)
        self.assertEqual(original, d.snapshot(self.game / "mod"))
        self.assert_foreign()
        return txid, tx, state_dir

    def assert_r2_terminal_refused(self, txid, tx, state_dir, error):
        journals = (tx / "journal.json", state_dir / "transactions" / (txid + ".json"))
        before_journals = [p.read_bytes() for p in journals]
        before_state_file = (state_dir / "state.json").read_bytes()
        before_game, before_state = d.snapshot(self.game), d.snapshot(state_dir)
        before_live = d.snapshot(self.game / "mod")
        foreign_paths = ("CWE", "CWE.mod", "dummy.txt", "TGCHFMMap", "TGCHFMMap.mod")
        before_foreign = {p: d.snapshot(self.game / "mod" / p) for p in foreign_paths}
        before_transactions = {p.name for p in tx.parent.iterdir()}
        self.assertIn(txid, self.pending())
        with mock.patch.object(d, "write_json", wraps=d.write_json) as write, \
                mock.patch.object(d, "move") as move, \
                mock.patch.object(d.shutil, "copyfile") as copyfile:
            with self.assertRaisesRegex(d.DeploymentError, error):
                self.rollback(txid)
            write.assert_not_called()
            move.assert_not_called()
            copyfile.assert_not_called()
        self.assertEqual(before_journals, [p.read_bytes() for p in journals])
        self.assertEqual(before_state_file, (state_dir / "state.json").read_bytes())
        self.assertEqual(before_game, d.snapshot(self.game))
        self.assertEqual(before_state, d.snapshot(state_dir))
        self.assertEqual(before_live, d.snapshot(self.game / "mod"))
        self.assertEqual(before_foreign,
                         {p: d.snapshot(self.game / "mod" / p) for p in foreign_paths})
        self.assertEqual(before_transactions, {p.name for p in tx.parent.iterdir()})
        self.assertEqual(before_transactions, {txid})
        self.assertIn(txid, self.pending())
        self.assert_foreign()

    def test_r2_terminal_retry_corrupt_manifest_refused(self):
        txid, tx, state_dir = self.r2_terminal_fixture()
        path = state_dir / "manifests" / (txid + ".json")
        manifest = d.read_json(path)
        manifest["digest"] = "0" * 64
        d.write_json(path, manifest)
        self.assert_r2_terminal_refused(txid, tx, state_dir, "Manifest integrity mismatch")

    def test_r2_terminal_retry_missing_completed_copy_refused(self):
        txid, tx, state_dir = self.r2_terminal_fixture()
        for path in (tx / "completed.json", state_dir / "completed" / (txid + ".json")):
            with self.subTest(copy=str(path)):
                original = path.read_bytes()
                path.unlink()
                self.assert_r2_terminal_refused(txid, tx, state_dir, "Cannot read metadata.*completed")
                path.write_bytes(original)

    def test_r2_terminal_retry_discordant_completed_refused(self):
        txid, tx, state_dir = self.r2_terminal_fixture()
        for path in (tx / "completed.json", state_dir / "completed" / (txid + ".json")):
            with self.subTest(copy=str(path)):
                original = path.read_bytes()
                completed = d.read_json(path)
                completed["manifest_digest"] = "0" * 64
                d.write_json(path, completed)
                self.assert_r2_terminal_refused(txid, tx, state_dir, "completed receipt mismatch")
                path.write_bytes(original)

    def test_r2_terminal_retry_missing_both_completed_copies_refused(self):
        txid, tx, state_dir = self.r2_terminal_fixture()
        (tx / "completed.json").unlink()
        (state_dir / "completed" / (txid + ".json")).unlink()
        self.assert_r2_terminal_refused(txid, tx, state_dir, "Rollback/recovery mode mismatch")

    def test_r2_terminal_retry_wrong_authorization_mode_refused(self):
        txid, tx, state_dir = self.r2_terminal_fixture()
        authorization = d.read_json(tx / "rollback-authorized.json")
        authorization["mode"] = "recovery"
        for path in (tx / "rollback-authorized.json",
                     state_dir / "rollback-authorized" / (txid + ".json")):
            d.write_json(path, authorization)
        self.assert_r2_terminal_refused(txid, tx, state_dir, "Rollback/recovery mode mismatch")

    def test_r2_terminal_retry_valid_evidence_completes_journal(self):
        txid, tx, state_dir = self.r2_terminal_fixture()
        before_live = d.snapshot(self.game / "mod")
        before_state = (state_dir / "state.json").read_bytes()
        before_transactions = {p.name for p in tx.parent.iterdir()}
        with mock.patch.object(d, "move") as move, \
                mock.patch.object(d.shutil, "copyfile") as copyfile:
            result = self.rollback(txid)
            move.assert_not_called()
            copyfile.assert_not_called()
        self.assertEqual(result, {"transaction_id": txid, "status": "rolled-back"})
        journal = d.read_json(tx / "journal.json")
        self.assertEqual(journal["status"], "rolled-back")
        self.assertEqual(journal, d.read_json(state_dir / "transactions" / (txid + ".json")))
        self.assertEqual(before_live, d.snapshot(self.game / "mod"))
        self.assertEqual(before_state, (state_dir / "state.json").read_bytes())
        self.assertEqual(before_transactions, {p.name for p in tx.parent.iterdir()})
        self.assertNotIn(txid, self.pending())
        self.assertFalse(self.pending())
        self.assert_foreign()

    def scan_failure(self, predicate):
        real_walk = d.os.walk
        def walk(path, *args, **kwargs):
            if predicate(Path(path)):
                error = PermissionError(13, "injected enumeration denied", str(Path(path) / "blocked"))
                self.assertIn("onerror", kwargs)
                kwargs["onerror"](error)
                return
            yield from real_walk(path, *args, **kwargs)
        return mock.patch.object(d.os, "walk", side_effect=walk)

    def test_f6_source_and_live_scan_errors_fail_closed(self):
        self.legacy()
        before = d.snapshot(self.game / "mod")
        for base in (self.root / "TGC", self.game / "mod/TGC"):
            with self.subTest(path=base), self.scan_failure(lambda p: p == base):
                with self.assertRaisesRegex(d.DeploymentError, "Snapshot failed.*blocked.*enumeration denied"):
                    self.plan()
            self.assertEqual(before, d.snapshot(self.game / "mod"))
            self.assertFalse((self.game / ".tgc-deploy").exists())

    def test_f6_staging_scan_error_prevents_publication(self):
        self.legacy()
        before = d.snapshot(self.game / "mod")
        with self.scan_failure(lambda p: "staging" in p.parts), self.assertRaises(d.DeploymentError):
            self.apply(adopt=True)
        self.assertEqual(before, d.snapshot(self.game / "mod"))
        self.assertFalse(self.pending())

    def test_f6_backup_and_rollback_staging_scan_errors(self):
        self.legacy()
        m = self.apply(adopt=True)
        before = d.snapshot(self.game / "mod")
        for part in ("backup", "rollback-staging"):
            with self.subTest(area=part), self.scan_failure(lambda p: part in p.parts):
                with self.assertRaisesRegex(d.DeploymentError, "Snapshot failed"):
                    self.rollback(m["transaction_id"])
            self.assertEqual(before, d.snapshot(self.game / "mod"))
        self.rollback(m["transaction_id"])
        self.assert_foreign()

    def test_f6_verify_scan_error_fails_closed(self):
        self.apply()
        before = d.snapshot(self.game / "mod")
        with self.scan_failure(lambda p: p == self.game / "mod/TGC"), self.assertRaisesRegex(d.DeploymentError, "Snapshot failed"):
            self.verify()
        self.assertEqual(before, d.snapshot(self.game / "mod"))


if __name__ == "__main__":
    unittest.main()
