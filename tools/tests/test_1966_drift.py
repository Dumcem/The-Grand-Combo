"""Exercise both drift directions against an actual Git diff."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


CHECKER = Path(__file__).resolve().parents[2] / "TGC/tools/check_1966_submod_drift.py"


class DriftTests(unittest.TestCase):
    def test_undocumented_override_warns_on_generic_deletion_in_either_direction(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)

            def git(*args):
                subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)

            git("init", "--quiet")
            removed = b"    name = caf\xe9\n"
            shared = b"effect = {\n" + removed + b"    generic_fix = yes\n}\n"
            paths = {}
            for layer in ("Core", "Late"):
                path = root / layer / "events/new_override.txt"
                path.parent.mkdir(parents=True)
                path.write_bytes(shared)
                paths[layer] = path
            git("add", ".")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgsign=false", "-c", "core.hooksPath=.",
                "commit", "--quiet", "-m", "Baseline")

            def check(*flags):
                code = (
                    "import sys; sys.path.insert(0, sys.argv.pop(1)); "
                    "import check_1966_submod_drift as drift; "
                    "drift.WATCHED_RELATIVE_PATHS = []; raise SystemExit(drift.main())"
                )
                return subprocess.run(
                    [sys.executable, "-B", "-c", code, str(CHECKER.parent), "--core-root", "Core",
                     "--timeline-root", "Late", "--fail-on-warn", *flags],
                    cwd=root, capture_output=True, text=True, encoding="utf-8",
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )

            # Explicit historical carriers are absent in this fixture and independently
            # fail the CLI. Exercise the check on the new shared path with the
            # historical watchlist disabled for the fixture.
            for layer, flags in (("Core", []), ("Late", ["--reverse"])):
                with self.subTest(layer=layer):
                    other = paths["Late" if layer == "Core" else "Core"]
                    changed = shared.replace(removed, b"")
                    paths[layer].write_bytes(changed)
                    result = check(*flags)
                    self.assertEqual(result.returncode, 1, result.stderr or result.stdout)
                    self.assertIn("events/new_override.txt: 1 distinct removed line(s)", result.stdout)
                    other.write_bytes(changed)
                    result = check(*flags)
                    self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                    for path in paths.values():
                        path.write_bytes(shared)
