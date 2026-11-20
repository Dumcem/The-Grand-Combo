"""Local TGC lab preparation, deployment and evidence."""

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import UUID
from xml.etree import ElementTree

from deploy_tgc import DeploymentError, EXPECTED_ORIGIN, digest, no_links, snapshot, utc
from snapshot_runtime_paths import capture

PROFILES = {
    "victoria2": ("core", "core+1966", "core+extender", "core+extender+1966"),
    "alice": ("core", "core+1966"),
}
ROOTS = {"core": "Shared", "core+1966": "Shared", "core+extender": "Loader",
         "core+extender+1966": "Loader1966"}
SENTINELS = {"changed.txt": b"initial content\n", "removed.txt": b"present at baseline\n"}
IDENTITY_FIELDS = ("engine_version", "engine_sha256", "profile", "manifest_sha256",
                   "baseline_sha256", "scenario_parameters", "scenario_checksum")


def read_json(path):
    return json.loads(no_links(path).read_text(encoding="utf-8-sig"))


def save_json(path, value):
    with no_links(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_id(value):
    require(re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value), f"Invalid ID: {value}")
    return value


def directory(path):
    path = no_links(path).resolve(strict=True)
    require(path.is_dir(), f"Not a directory: {path}")
    return path


def new_session(lab, name):
    session = directory(lab / "sessions") / safe_id(name)
    session.mkdir()
    return session


def protected(lab, inputs=()):
    paths = read_json(lab / "baselines" / "host-protected-paths.json")
    require(isinstance(paths, dict) and paths, "Empty or invalid protected paths")
    return capture([*paths.items(), *inputs])


def changed_scopes(before, after):
    left, right = before["paths"], after["paths"]
    return sorted(key for key in left.keys() | right.keys() if left.get(key) != right.get(key))


def host_check(args):
    lab = directory(args.lab_root)
    session = directory(lab / "sessions" / safe_id(args.run))
    mounts = []
    config = no_links(session / "summary.json")
    if config.exists():
        request = read_json(config)
        if request.get("case") == "sandbox-config":
            mounts = [("lab-input", str(lab / "baselines" / safe_id(request["baseline"]) / "input")),
                      ("lab-request", str(lab / "transfer" / args.run / "request"))]
            if key := request.get("cache_key"):
                require(re.fullmatch(r"[0-9a-f]{64}", key), "Invalid cache key in session")
                mounts.append(("lab-cache-entry", str(lab / "baselines" / "scenario-cache" / key)))
    current = protected(lab, mounts)
    result = {"case": "host-check", "run": args.run, "phase": args.phase,
              "protected_scopes": len(current["paths"]), "snapshot_sha256": digest(current),
              "status": "captured", "utc": utc()}
    if args.phase == "after":
        previous = read_json(session / "host-before.json")
        changed = changed_scopes(previous, current)
        result.update(status="fail" if changed else "pass", changed_scopes=changed)
    save_json(session / f"host-{args.phase}.json", current)
    save_json(session / f"host-{args.phase}-summary.json", result)
    return result


def rebuild_smoke(args):
    lab = directory(args.lab_root)
    before = protected(lab)
    session = new_session(lab, args.run)
    summary = {"case": "rebuild-smoke", "fixture": "sentinels-v1",
               "engine": None, "profile": None, "scenario": None,
               "commit": revision(Path(__file__).resolve().parents[2], "HEAD"),
               "utc": utc(), "status": "fail"}
    try:
        fixtures = directory(lab / "fixtures")
        expected = {"kind": "directory", "dirs": [], "files": {
            name: {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in SENTINELS.items()
        }}
        fixture = no_links(fixtures / "sentinels-v1")
        if not fixture.exists():
            fixture.mkdir()
            for name, data in SENTINELS.items():
                (fixture / name).write_bytes(data)
        require(snapshot(fixture) == expected, "Baseline fixture differs from sentinels-v1")
        save_json(session / "host-before.json", before)
        scratch = directory(lab / "scratch")
        with TemporaryDirectory(prefix="rebuild-", dir=scratch) as first:
            first = directory(first)
            require(first.parent == scratch, "Unexpected scratch parent")
            work = first / "work"
            shutil.copytree(fixture, work)
            require(snapshot(work) == expected, "First reconstruction differs from baseline")
            (work / "changed.txt").write_bytes(b"changed\n")
            (work / "removed.txt").unlink()
            (work / "added.txt").write_bytes(b"created\n")
            mutated = snapshot(work)
            require(set(mutated["files"]) == {"changed.txt", "added.txt"}
                    and mutated["files"]["changed.txt"] != expected["files"]["changed.txt"],
                    "Expected creation, modification and deletion")
        require(not first.exists(), "Original scratch still exists")
        with TemporaryDirectory(prefix="rebuild-", dir=scratch) as second:
            second = directory(second)
            require(second.parent == scratch, "Unexpected scratch parent")
            work = second / "work"
            shutil.copytree(fixture, work)
            restored = snapshot(work)
            require(restored == expected, "Second reconstruction differs from baseline")
        require(not second.exists(), "Reconstructed scratch still exists")
        save_json(session / "fixture-states.json",
                  {"baseline": expected, "mutated": mutated, "reconstructed": restored})
        after = protected(lab)
        save_json(session / "host-after.json", after)
        changed = changed_scopes(before, after)
        summary.update(fixture_sha256=digest(expected), protected_scopes=len(before["paths"]),
                       changed_scopes=changed)
        require(not changed, "Protected path inventory differs")
        summary["status"] = "pass"
    except (OSError, ValueError, DeploymentError) as exc:
        summary["error"] = str(exc)
    save_json(session / "summary.json", summary)
    return summary


def revision(repo, ref):
    result = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--end-of-options",
                             ref + "^{commit}"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def check_profile(engine, profile):
    require(profile in PROFILES[engine], f"Unsupported profile for {engine}: {profile}")


def sandbox_config(args):
    lab = directory(args.lab_root)
    check_profile(args.engine, args.profile)
    run = safe_id(args.run)
    baseline = directory(lab / "baselines" / safe_id(args.baseline))
    inputs = directory(baseline / "input")
    # Only a dedicated baseline payload crosses the boundary. Refuse links even
    # if a mapped reader or a future recursive copy could otherwise follow them.
    input_snapshot = snapshot(inputs)
    for item in input_snapshot["files"]:
        require((inputs / item).stat().st_nlink == 1, f"Hardlinked input refused: {item}")
    commit = revision(Path(__file__).resolve().parents[2], args.commit)
    request = {"run": run, "commit": commit, "engine": args.engine, "profile": args.profile,
               "baseline": args.baseline, "game": ROOTS[args.profile],
               "baseline_sha256": digest(input_snapshot)}
    cache_mount = []
    if args.cache_key:
        require(args.engine == "alice" and re.fullmatch(r"[0-9a-f]{64}", args.cache_key),
                "A lowercase SHA-256 cache key requires an Alice request")
        cached = directory(lab / "baselines" / "scenario-cache" / args.cache_key)
        receipt = read_json(cached / "receipt.json")
        identity = receipt["identity"]
        require(digest(identity) == args.cache_key and identity["profile"] == args.profile
                and identity["baseline_sha256"] == request["baseline_sha256"],
                "Cache entry does not match the requested baseline and profile")
        index = snapshot(cached)
        require(snapshot(cached / "payload") == receipt["payload"], "Cache payload damaged")
        require(all((cached / name).stat().st_nlink == 1 for name in index["files"]),
                "Hardlinked cache entry refused")
        cache_mount.append((cached, r"C:\TGCScenarioEntry", True))
        request["cache_key"] = args.cache_key
    transfer = no_links(directory(lab / "transfer") / run)
    require(not transfer.exists(), "Session transfer already exists")
    session = new_session(lab, run)
    transfer.mkdir()
    request_path = transfer / "request"
    outbox = transfer / "outbox"
    request_path.mkdir()
    outbox.mkdir()
    mounts = [(inputs, r"C:\TGCInput", True), (request_path, r"C:\TGCRequest", True),
              (outbox, r"C:\TGCOutbox", False), *cache_mount]
    save_json(request_path / "request.json", request)
    config = ElementTree.Element("Configuration")
    for key in ("Networking", "ClipboardRedirection", "PrinterRedirection", "AudioInput", "VideoInput"):
        ElementTree.SubElement(config, key).text = "Disable"
    ElementTree.SubElement(config, "ProtectedClient").text = "Enable"
    # Windows Sandbox CLI requires this exact element name.
    ElementTree.SubElement(config, "vGPU").text = "Enable" if args.vgpu else "Disable"
    mappings = ElementTree.SubElement(config, "MappedFolders")
    for host, guest, readonly in mounts:
        mapping = ElementTree.SubElement(mappings, "MappedFolder")
        ElementTree.SubElement(mapping, "HostFolder").text = str(host)
        ElementTree.SubElement(mapping, "SandboxFolder").text = guest
        ElementTree.SubElement(mapping, "ReadOnly").text = str(readonly).lower()
    ElementTree.indent(config)
    with (session / "session.wsb").open("xb") as stream:
        ElementTree.ElementTree(config).write(stream, encoding="utf-8", xml_declaration=True)
    summary = {**request, "case": "sandbox-config", "status": "prepared", "launched": False,
               "request_sha256": digest(request), "outbox": str(outbox), "utc": utc()}
    save_json(session / "summary.json", summary)
    return summary


def guest_request():
    # The guest operator first observes the synthetic write-boundary probe.
    # This receipt records that observation; its presence cannot prove isolation.
    request = read_json(Path(r"C:\TGCRequest\request.json"))
    admission = read_json(Path(r"C:\TGC-Lab\admission.json"))
    require(admission.get("request_sha256") == digest(request) and admission.get("status") == "pass",
            "Guest write-boundary admission receipt is missing or does not match this request")
    check_profile(request["engine"], request["profile"])
    return request


def guest_deploy(_args):
    request = guest_request()
    workspace = directory(Path(r"C:\TGC-Lab"))
    inputs = directory(Path(r"C:\TGCInput"))
    evidence = workspace / "Evidence"
    evidence.mkdir()
    summary = {**request, "case": "guest-deploy", "status": "fail", "phases": {}, "utc": utc()}
    try:
        stage_and_deploy(request, workspace, inputs, evidence, summary)
    except (OSError, ValueError, KeyError, DeploymentError, subprocess.CalledProcessError) as exc:
        summary["error"] = str(exc)
    save_json(evidence / "summary.json", summary)
    return summary


def stage_and_deploy(request, workspace, inputs, evidence, summary):
    require(digest(snapshot(inputs)) == request["baseline_sha256"], "Guest baseline differs from request")
    bundle = no_links(inputs / "checkout.bundle")
    repo = no_links(workspace / "Checkout")
    with (evidence / "checkout.log").open("xb") as log:
        git_commands = [
            ["clone", "--no-checkout", "-c", "core.autocrlf=false", str(bundle), str(repo)],
            ["-C", str(repo), "checkout", "--detach", request["commit"]],
            ["-C", str(repo), "remote", "set-url", "origin", EXPECTED_ORIGIN],
        ]
        require(not repo.exists(), "Guest checkout already exists")
        for command in git_commands:
            subprocess.run(["git", *command], stdout=log, stderr=subprocess.STDOUT, check=True)
    require(revision(repo, "HEAD") == request["commit"], "Guest checkout revision mismatch")
    name = ROOTS[request["profile"]]
    source_game = directory(inputs / "games" / name)
    source_snapshot = snapshot(source_game)
    game = no_links(workspace / "Games" / name)
    shutil.copytree(source_game, game)
    require(snapshot(game) == source_snapshot, "Guest game copy differs from baseline")
    if name != "Shared":
        user_data = no_links(workspace / "UserData" / name)
        user_data.mkdir(parents=True)
        no_links(game / "userdir.txt").write_text(str(user_data) + "\n", encoding="ascii")
    state = no_links(workspace / "State" / name)
    deployer = repo / "tools" / "deploy" / "deploy_tgc.py"
    target = ["--game-root", str(game), "--state-root", str(state), "--profile", request["profile"]]
    plan_path = evidence / "plan.json"
    for phase in ("plan", "apply", "verify"):
        options = ["--plan-file", str(plan_path)] if phase == "apply" else []
        with (evidence / f"{phase}.json").open("xb") as stdout, (evidence / f"{phase}.stderr").open("xb") as stderr:
            result = subprocess.run([sys.executable, "-B", str(deployer), phase, *target, *options],
                                    stdout=stdout, stderr=stderr, check=False)
        summary["phases"][phase] = result.returncode
        if result.returncode:
            break
        if phase == "plan":
            plan = read_json(plan_path)
            require(plan["identity"]["commit"] == request["commit"] and plan["profile"] == request["profile"]
                    and Path(plan["root"]) == repo and Path(plan["target"]) == game
                    and Path(plan["state_dir"]).is_relative_to(state),
                    "Plan differs from the admitted source, profile or target")
            if plan["blockers"] or any(unit["adoption_required"] for unit in plan["components"]):
                summary["error"] = "Plan has blockers or requires adoption"
                break
            summary["plan_sha256"] = plan["fingerprint"]
        if phase == "apply":
            summary["manifest_sha256"] = read_json(evidence / "apply.json")["digest"]
    else:
        summary["status"] = "pass"


def guest_export(_args):
    request = guest_request()
    source = directory(Path(r"C:\TGC-Lab\Evidence"))
    target = directory(Path(r"C:\TGCOutbox")) / safe_id(request["run"])
    expected = snapshot(source)
    shutil.copytree(source, target)
    require(snapshot(target) == expected, "Export differs from guest evidence")
    save_json(target / "export-sha256.json", expected)
    return {"case": "guest-export", "status": "exported", "run": request["run"],
            "files": len(expected["files"]), "sha256": digest(expected), "utc": utc()}


def known_folder(identifier):
    require(os.name == "nt", "Windows Known Folders are required")
    folder_id = (ctypes.c_ubyte * 16).from_buffer_copy(UUID(identifier).bytes_le)
    address = ctypes.c_void_p()
    result = ctypes.windll.shell32.SHGetKnownFolderPath(
        ctypes.byref(folder_id), 0, None, ctypes.byref(address))
    try:
        require(result == 0 and address.value, f"Cannot resolve Known Folder: {identifier}")
        return no_links(Path(ctypes.wstring_at(address.value)))
    finally:
        ctypes.windll.ole32.CoTaskMemFree(address)


def guest_alice_build(_args):
    request = guest_request()
    require(request["engine"] == "alice", "The requested engine is not Alice")
    workspace = directory(Path(r"C:\TGC-Lab"))
    evidence = directory(workspace / "Evidence")
    deployment = read_json(evidence / "summary.json")
    require(deployment["status"] == "pass" and all(deployment[key] == value for key, value in request.items()),
            "A verified deployment for this request is required")
    game = directory(workspace / "Games" / ROOTS[request["profile"]])
    executable = no_links(game / "launch_alice.exe")
    documents = known_folder("FDD39AD0-238F-46AF-ADB4-6C85480369C7")
    local = known_folder("F1B32785-6FBA-4FCF-9D55-7B8E7F157091")
    mask = "TGC - The Grand Combination" if request["profile"] == "core" else "TGC Timeline 1966"
    filename = "tgc-lab-" + request["profile"].replace("+", "-") + ".bin"
    scenario = no_links(documents / "Project Alice" / "scenarios" / filename)
    diagnostics = no_links(local / "Project Alice" / "scenario_errors.txt")
    result = {**request, "case": "guest-alice-build", "status": "fail", "scenario": filename,
              "scenario_parameters": {"mask": mask, "auto_build": True},
              "manifest_sha256": deployment["manifest_sha256"], "utc": utc()}
    had_diagnostics = diagnostics.exists()
    try:
        require(not scenario.exists(), "Scenario already present; check its reuse receipt")
        require(not had_diagnostics, "Guest diagnostic already present; retain it before this build")
        result["launcher"] = snapshot(executable)["files"][""]
        with (evidence / "alice-build.log").open("xb") as log:
            process = subprocess.run([str(executable), "-modsMask", mask, "-outputScenario", filename,
                                      "-autoBuild"], cwd=game, stdout=log, stderr=subprocess.STDOUT,
                                     timeout=1200, check=False)
        result["exit_code"] = process.returncode
        require(process.returncode == 0, "Alice launcher returned an error")
        result["scenario_file"] = snapshot(scenario)["files"][""]
        require(result["scenario_file"]["size"] > 0, "Alice generated an empty scenario")
        result["status"] = "generated"
    except (OSError, ValueError, KeyError, DeploymentError, subprocess.TimeoutExpired) as exc:
        result["error"] = str(exc)
    if not had_diagnostics and diagnostics.is_file():
        shutil.copyfile(no_links(diagnostics), evidence / "scenario_errors.txt")
    save_json(evidence / "alice-build-summary.json", result)
    return result


def archive_export(args):
    lab = directory(args.lab_root)
    run = safe_id(args.run)
    session = directory(lab / "sessions" / run)
    if read_json(session / "host-after-summary.json")["status"] != "pass":
        raise ValueError("Host check failed; retain the drop for diagnosis")
    drop = directory(lab / "transfer" / run / "outbox" / run)
    expected = snapshot(drop)
    content = dict(expected, files={name: entry for name, entry in expected["files"].items()
                                   if name != "export-sha256.json"})
    require(content == read_json(drop / "export-sha256.json"), "Guest export differs from its receipt")
    staging = no_links(session / "raw.incomplete")
    target = no_links(session / "raw")
    require(not target.exists(), "Export already archived")
    shutil.copytree(drop, staging)
    require(snapshot(staging) == expected, "Host archive differs from export")
    staging.rename(target)
    result = {"case": "archive-export", "run": run, "status": "verified",
              "files": len(expected["files"]), "sha256": digest(expected), "utc": utc()}
    save_json(session / "archive-summary.json", result)
    return result


def scenario_cache(args):
    # The identity comes from a verified deployment and an observed scenario.
    # Include companion bookmark files in the payload when the build emits them.
    identity = read_json(args.identity)
    require(all(key in identity and identity[key] for key in IDENTITY_FIELDS),
            "Incomplete scenario identity")
    for key in ("engine_sha256", "manifest_sha256", "baseline_sha256"):
        require(re.fullmatch(r"[0-9a-f]{64}", identity[key]), f"Invalid SHA-256: {key}")
    check_profile("alice", identity["profile"])
    key = digest(identity)
    cache = no_links(directory(args.cache) / key) if args.cache is not None else directory(args.entry)
    payload = no_links(args.payload).resolve()
    require(not payload.is_relative_to(cache) and not cache.is_relative_to(payload),
            "Scenario payload and cache overlap")
    result = {"case": args.command, "key": key}
    if args.command == "scenario-store":
        source = directory(payload)
        expected = snapshot(source)
        require(expected["files"], "Scenario payload is empty")
        require(not cache.exists(), "Scenario identity already cached")
        with TemporaryDirectory(prefix="scenario-", dir=cache.parent) as temporary:
            temporary = directory(temporary)
            require(temporary.parent == cache.parent, "Unexpected cache staging parent")
            staging = temporary / "entry"
            staging.mkdir()
            shutil.copytree(source, staging / "payload")
            require(snapshot(staging / "payload") == expected, "Scenario cache copy differs from source")
            save_json(staging / "receipt.json", {"identity": identity, "payload": expected})
            staging.rename(cache)
        return {**result, "status": "stored"}
    if not cache.exists():
        return {**result, "status": "miss"}
    receipt = read_json(cache / "receipt.json")
    require(receipt["identity"] == identity, "Scenario cache identity mismatch")
    source = directory(cache / "payload")
    require(snapshot(source) == receipt["payload"], "Scenario cache payload damaged")
    shutil.copytree(source, payload)
    require(snapshot(payload) == receipt["payload"], "Restored scenario payload differs")
    return {**result, "status": "reused"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, runner in (("rebuild-smoke", rebuild_smoke), ("sandbox-config", sandbox_config),
                         ("host-check", host_check), ("archive-export", archive_export)):
        command = commands.add_parser(name)
        command.add_argument("--lab-root", required=True, type=Path)
        command.add_argument("--run", required=True)
        command.set_defaults(runner=runner)
    config = commands.choices["sandbox-config"]
    config.add_argument("--baseline", required=True)
    config.add_argument("--commit", required=True)
    config.add_argument("--engine", required=True, choices=PROFILES)
    config.add_argument("--profile", required=True)
    config.add_argument("--vgpu", action="store_true")
    config.add_argument("--cache-key")
    commands.choices["host-check"].add_argument("--phase", choices=("before", "after"), required=True)
    commands.add_parser("guest-deploy").set_defaults(runner=guest_deploy)
    commands.add_parser("guest-export").set_defaults(runner=guest_export)
    commands.add_parser("guest-alice-build").set_defaults(runner=guest_alice_build)
    for name in ("scenario-store", "scenario-reuse"):
        command = commands.add_parser(name)
        command.add_argument("--identity", type=Path, required=True)
        if name == "scenario-reuse":
            source = command.add_mutually_exclusive_group(required=True)
            source.add_argument("--cache", type=Path)
            source.add_argument("--entry", type=Path)
        else:
            command.add_argument("--cache", type=Path, required=True)
        command.add_argument("--payload", type=Path, required=True)
        command.set_defaults(runner=scenario_cache)
    args = parser.parse_args()
    try:
        summary = args.runner(args)
    except (ValueError, OSError, KeyError, TypeError, DeploymentError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"case": args.command, "status": "fail", "error": str(exc)}))
        return 1
    print(json.dumps(summary, sort_keys=True))
    return {"fail": 1, "miss": 2}.get(summary["status"], 0)


if __name__ == "__main__":
    sys.exit(main())
