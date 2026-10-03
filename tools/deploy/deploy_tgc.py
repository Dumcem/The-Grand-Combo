"""Selective TGC deployment. Standard library only; plan never writes files."""
from __future__ import annotations

import argparse
import contextlib
import ctypes
import datetime as dt
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import stat as statmod
import subprocess
import sys
import tempfile
import uuid

SCHEMA = 1
EXPECTED_ORIGIN = "https://github.com/Dumcem/The-Grand-Combo.git"
INCOMPLETE = {"planned", "staging", "publishing", "verifying", "rolling-back", "recovery-required"}


class DeploymentError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise DeploymentError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path):
    try:
        no_links(path)
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise DeploymentError(f"Cannot read metadata {path}: {exc}") from exc


def write_json(path, value):
    path = Path(path)
    no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    no_links(path.parent)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)  # mkstemp creates exclusively; never opens an existing link.
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        no_links(path)
        os.replace(temporary, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


def no_links(path):
    """Check lexical ancestors before resolve; also rejects Windows junctions."""
    path = Path(os.path.abspath(path))
    for entry in reversed((path, *path.parents)):
        try:
            value = entry.lstat()
        except FileNotFoundError:
            continue
        require(not statmod.S_ISLNK(value.st_mode) and not (getattr(value, "st_file_attributes", 0) & 0x400),
                f"Reparse point/symlink refused: {entry}")
    return path


def relative(value, single=False):
    require(isinstance(value, str) and value and "\\" not in value, "Invalid relative path")
    parts = value.split("/")
    require(not PureWindowsPath(value).is_absolute() and not PureWindowsPath(value).drive,
            f"Absolute/drive path refused: {value}")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}
    for part in parts:
        require(part not in ("", ".", "..") and not any(c in part for c in ':<>"|?*')
                and not any(ord(c) < 32 for c in part) and part == part.rstrip(" .")
                and part.split(".")[0].upper() not in reserved, f"Unsafe path: {value}")
    require(not single or len(parts) == 1, f"Expected direct child: {value}")
    return value


def inside(path, parent):
    try:
        Path(path).relative_to(parent)
        return True
    except ValueError:
        return False


def file_info(path):
    no_links(path)
    with Path(path).open("rb") as stream:
        before = os.fstat(stream.fileno())
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
        after = os.fstat(stream.fileno())
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            f"File changed while hashing: {path}")
    return {"size": after.st_size, "sha256": sha}


def snapshot(path):
    try:
        return _snapshot(path)
    except OSError as exc:
        raise DeploymentError(f"Snapshot failed at {getattr(exc, 'filename', None) or path}: {exc}") from exc


def _snapshot(path):
    """Includes empty directories and absence, so backup identity is complete."""
    path = no_links(path)
    try:
        value = path.lstat()
    except FileNotFoundError:
        return {"kind": "absent"}
    if statmod.S_ISREG(value.st_mode):
        return {"kind": "file", "files": {"": file_info(path)}, "dirs": []}
    require(statmod.S_ISDIR(value.st_mode), f"Not a regular directory/file: {path}")
    files, dirs, names = {}, [], set()
    def scan_error(exc):
        raise exc
    for base, children, leaves in os.walk(path, followlinks=False, onerror=scan_error):
        for name in sorted(children + leaves):
            item = no_links(Path(base) / name)
            rel = relative(item.relative_to(path).as_posix())
            require(rel.casefold() not in names, f"Windows collision: {rel}")
            names.add(rel.casefold())
            if item.is_dir():
                dirs.append(rel)
            else:
                require(item.is_file(), f"Nonregular entry: {item}")
                files[rel] = file_info(item)
    return {"kind": "directory", "files": dict(sorted(files.items())), "dirs": sorted(dirs)}


def payload_snapshot(files):
    dirs = set()
    for path in files:
        parent = Path(path).parent
        while str(parent) != ".":
            dirs.add(parent.as_posix())
            parent = parent.parent
    return {"kind": "directory", "files": dict(sorted(files.items())), "dirs": sorted(dirs)}


def git(root, *args):
    result = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args],
                            capture_output=True, check=False)
    require(result.returncode == 0, result.stderr.decode(errors="replace").strip())
    return result.stdout


def git_identity(root):
    require(Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root,
            "Repository root mismatch")
    origin = git(root, "remote", "get-url", "origin").decode().strip()
    require(origin == EXPECTED_ORIGIN, f"Unexpected origin: {origin}")
    require(not git(root, "ls-files", "--stage").startswith(b"160000 ") and
            b"\n160000 " not in git(root, "ls-files", "--stage"), "Submodules unsupported")
    return {"repository": origin, "branch": git(root, "branch", "--show-current").decode().strip(),
            "commit": git(root, "rev-parse", "HEAD").decode().strip(),
            "clean": not bool(git(root, "status", "--porcelain=v1", "--untracked-files=all"))}


def load_catalog(path):
    catalog = read_json(path)
    require(catalog["schema"] == SCHEMA, "Unsupported catalog schema")
    names, ids = set(), set()
    for component in catalog["components"]:
        cid = relative(component["id"], single=True)
        require(cid not in ids, "Duplicate component ID")
        ids.add(cid)
        relative(component["source_dir"])
        if component["class"] == "utility/non-mod-target":
            require(component["destination_dir"] is None, "Utility cannot target mod")
            continue
        for key in ("source_descriptor",):
            relative(component[key])
        for key in ("destination_dir", "destination_descriptor"):
            name = relative(component[key], single=True)
            require(name.casefold() not in names, "Destination collision")
            names.add(name.casefold())
        require(component["destination_descriptor"] == component["destination_dir"] + ".mod",
                "Descriptor/directory mapping mismatch")
        for exclusion in component["exclusions"]:
            relative(exclusion[:-3] if exclusion.endswith("/**") else exclusion)
    for profile, selected in catalog["profiles"].items():
        require(set(selected) <= ids and len(selected) == len(set(selected)), f"Invalid profile {profile}")
    for component in catalog["components"]:
        require(set(component["dependencies"]) <= ids, "Unknown dependency")
    return catalog


def selected_components(catalog, profile, optional):
    require(profile in catalog["profiles"], "Unknown profile")
    mapping = {c["id"]: c for c in catalog["components"]}
    selected = list(catalog["profiles"][profile])
    for cid in optional:
        require(cid in mapping and mapping[cid]["class"] == "optional", f"Not an optional mod: {cid}")
        if cid not in selected:
            selected.append(cid)
    require("TGC" in selected, "Core profile required")
    for cid in selected:
        require(set(mapping[cid]["dependencies"]) <= set(selected), f"Missing dependency: {cid}")
    return [mapping[cid] for cid in selected]


def check_descriptor(root, component, mapping):
    descriptor = no_links(root / component["source_descriptor"])
    text = descriptor.read_text(encoding="utf-8-sig")
    def values(field):
        return re.findall(r'^\s*' + field + r'\s*=\s*"([^"\r\n]+)"', text, re.M)
    require(values("name") == [component["name"]], "Descriptor name inconsistent")
    require(values("path") == ["mod/" + component["destination_dir"]], "Descriptor path inconsistent")
    blocks = re.findall(r"^\s*dependencies\s*=\s*\{([^}]*)\}", text, re.M)
    dependencies = [x for block in blocks for x in re.findall(r'"([^"\r\n]+)"', block)]
    require(dependencies == [mapping[c]["name"] for c in component["dependencies"]],
            "Descriptor dependencies inconsistent")


def source_payload(root, component, tracked):
    source = no_links(root / component["source_dir"])
    require(source.is_dir(), f"Source directory missing: {source}")
    # Inspect even excluded/ignored entries for links; never follow them.
    snapshot(source)
    prefix = component["source_dir"] + "/"
    files, seen = {}, set()
    for tracked_path in tracked:
        if not tracked_path.startswith(prefix):
            continue
        rel = relative(tracked_path[len(prefix):])
        if any(fnmatch.fnmatchcase(rel, pattern) for pattern in component["exclusions"]):
            continue
        require(rel.casefold() not in seen, f"Windows payload collision: {rel}")
        seen.add(rel.casefold())
        top = rel.split("/")[0]
        require(top in component["runtime_policy"]["roots"], f"Uncatalogued runtime root: {rel}")
        require((source / rel).is_file(), f"Tracked runtime missing: {rel}")
        files[rel] = file_info(source / rel)
    return payload_snapshot(files)


def target_paths(root, game, state_base=None):
    root, game = no_links(root).resolve(), no_links(game).resolve()
    require(not inside(root, game) and not inside(game, root), "Source/target overlap")
    require(not any(p.casefold() in ("legacy", "steamapps") for p in root.parts),
            "Source inside Legacy/Steam refused")
    require((game / "v2game.exe").is_file() and all((game / p).is_dir() for p in
            ("mod", "common", "history", "map")), "Not a Victoria II installation")
    for p in ("v2game.exe", "mod", "common", "history", "map", ".tgc-deploy"):
        no_links(game / p)
    if state_base is None:
        require(bool(os.environ.get("LOCALAPPDATA")), "LOCALAPPDATA unavailable; supply --state-root")
        state_base = Path(os.environ["LOCALAPPDATA"]) / "TGCDeployment"
    state_base = no_links(state_base).resolve()
    require(not inside(state_base, game) and not inside(state_base, root)
            and not inside(game, state_base) and not inside(root, state_base), "Unsafe state-root overlap")
    tid = hashlib.sha256(str(game).casefold().encode()).hexdigest()[:24]
    return root, game, state_base / "targets" / tid


def read_state(state_dir, game):
    path = state_dir / "state.json"
    if not path.exists():
        return {"schema": SCHEMA, "target": str(game), "components": {}}
    try:
        state = read_json(path)
        require(state["schema"] == SCHEMA and state["target"] == str(game)
                and isinstance(state["components"], dict), "State target/schema mismatch")
    except (DeploymentError, KeyError, TypeError) as exc:
        raise DeploymentError(f"Existing state is untrusted; recovery/intervention required: {exc}") from exc
    return state


def pending(game, state_dir, catalog, owned_lock=None):
    work = no_links(game / ".tgc-deploy")
    result = []
    if (work / "lock").exists():
        if owned_lock is None or read_json(work / "lock") != owned_lock:
            result.append("target-lock")
    transactions = no_links(work / "transactions")
    if not transactions.exists():
        return result
    for folder in transactions.iterdir():
        no_links(folder)
        if folder.is_dir():
            journal = folder / "journal.json"
            try:
                value = read_json(journal)
                require(value.get("transaction_id") == folder.name, "Transaction binding mismatch")
                record = validate_journal(value, game, catalog, state_dir)
                complete = receipt(game, state_dir, record, "completed")
                authorized = receipt(game, state_dir, record, "rollback-authorized")
                restored = receipt(game, state_dir, record, "restored")
                if complete is not None:
                    validated_manifest(game, state_dir, record)
                if authorized is not None:
                    mode = "rollback" if complete is not None else "recovery"
                    require(authorized.get("mode") == mode, "Rollback/recovery mode mismatch")
                    # Apply completion cannot cancel an authorized rollback.
                    unfinished = restored is None or value["status"] != "rolled-back"
                else:
                    require(restored is None, "Restored transaction lacks rollback authorization")
                    unfinished = complete is None or value["status"] != "verified"
            except (DeploymentError, AttributeError, KeyError, TypeError, ValueError):
                unfinished = True
            if unfinished:
                result.append(folder.name)
    return sorted(result)


def delta(old, new):
    a, b = old.get("files", {}), new.get("files", {})
    return {"add": sorted(b.keys() - a.keys()), "remove": sorted(a.keys() - b.keys()),
            "modify": sorted(k for k in a.keys() & b.keys() if a[k] != b[k])}


def build_plan(root, game, catalog_path, profile, optional=(), state_base=None, owned_lock=None):
    root, game, state_dir = target_paths(root, game, state_base)
    catalog = load_catalog(catalog_path)
    identity = git_identity(root)
    state = read_state(state_dir, game)
    validate_ownership(state, game, state_dir, catalog)
    tracked = [os.fsdecode(p) for p in git(root, "ls-files", "-z").split(b"\0") if p]
    mapping = {c["id"]: c for c in catalog["components"]}
    selected = selected_components(catalog, profile, optional)
    blockers = [] if identity["clean"] else ["Working tree dirty: plan is diagnostic only; apply refused"]
    if pending(game, state_dir, catalog, owned_lock):
        blockers.append("Incomplete transaction/lock: recovery required")
    units, components = [], []
    for component in selected:
        check_descriptor(root, component, mapping)
        require(component["source_descriptor"] in tracked, "Descriptor is not tracked")
        payload = source_payload(root, component, tracked)
        descriptor = snapshot(root / component["source_descriptor"])
        cid = component["id"]
        own = state["components"].get(cid)
        entries = []
        for name, source, expected in ((component["destination_dir"], component["source_dir"], payload),
                                       (component["destination_descriptor"], component["source_descriptor"], descriptor)):
            live = snapshot(game / "mod" / name)
            require(live["kind"] in ("absent", expected["kind"]), f"Wrong destination type: {name}")
            unit = {"component": cid, "name": name, "source": source, "old": live, "new": expected}
            units.append(unit)
            entries.append(unit)
        if own:
            require(own.get("mapping") == [u["name"] for u in entries], "Ownership mapping mismatch")
            if own.get("snapshots") != {u["name"]: u["old"] for u in entries}:
                blockers.append(f"Owned live changed: {cid}")
        changes = {u["name"]: delta(u["old"], u["new"]) for u in entries}
        exists = any(u["old"]["kind"] != "absent" for u in entries)
        components.append({"id": cid, "ownership": "owned" if own else "unowned",
                           "adoption_required": exists and not own,
                           "status": "new" if not exists else "identical" if all(u["old"] == u["new"] for u in entries) else "modified",
                           "changes": changes, "extra_files": sum(len(c["remove"]) for c in changes.values())})
    scope = {u["name"].casefold() for u in units}
    preserved = []
    for entry in (game / "mod").iterdir():
        # Out-of-scope entries are never traversed, copied or adopted.
        if entry.name.casefold() not in scope:
            preserved.append(entry.name)
        else:
            require(entry.name in {u["name"] for u in units}, "Destination case collision")
    plan = {"schema": SCHEMA, "runtime_policy": catalog["runtime_policy_version"],
            "catalog_digest": digest(catalog), "root": str(root), "target": str(game),
            "state_dir": str(state_dir), "identity": identity, "profile": profile,
            "optional": list(optional), "components": components, "units": units,
            "state_digest": digest(state), "preserved": sorted(preserved), "blockers": blockers,
            "backup_template": str(game / ".tgc-deploy/transactions/<transaction-id>/backup")}
    plan["fingerprint"] = digest(plan)
    return plan


def active_processes():
    if os.name != "nt":
        return []
    result = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, check=False)
    require(result.returncode == 0, "Unable to inspect active Windows processes")
    names = {"v2game.exe", "victoria2.exe", "alice.exe", "alice512.exe", "alicesse.exe",
             "launch_alice.exe", "dbg_alice.exe"}
    import csv
    return [row[0] for row in csv.reader(result.stdout.decode(errors="replace").splitlines())
            if row and row[0].casefold() in names]


def writable_files(units, game):
    require(not active_processes(), "Game/launcher process active")
    if os.name != "nt":
        return
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                       ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    create.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    invalid = ctypes.c_void_p(-1).value
    for unit in units:
        base = game / "mod" / unit["name"]
        for rel in unit["old"].get("files", {}):
            path = base / rel if rel else base
            no_links(path)
            require(not (path.stat().st_file_attributes & 1), f"Read-only file refused: {path}")
            handle = create(str(path), 0x10000, 0, None, 3, 0x80, None)  # DELETE, no sharing; no mutation
            require(handle != invalid, f"Locked/read-only/inaccessible file: {path}")
            kernel.CloseHandle(handle)


def writable_mod_parent(game):
    require(os.access(game / "mod", os.W_OK), "Mod parent is not writable")
    if os.name != "nt":
        return
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                       ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    create.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    # Ask Windows to check directory ACL rights without creating runtime entries:
    # FILE_ADD_FILE | FILE_ADD_SUBDIRECTORY | FILE_DELETE_CHILD.
    handle = create(str(game / "mod"), 0x46, 7, None, 3, 0x02000000, None)
    require(handle != ctypes.c_void_p(-1).value, "Mod parent ACL denies publication rights")
    kernel.CloseHandle(handle)


@contextlib.contextmanager
def target_lock(game):
    work = no_links(game / ".tgc-deploy")
    work.mkdir(exist_ok=True)
    lock = no_links(work / "lock")
    try:
        stream = lock.open("x")
    except FileExistsError as exc:
        raise DeploymentError("Target lock exists; inspect interrupted operation") from exc
    try:
        token = {"pid": os.getpid(), "started_utc": utc(), "token": uuid.uuid4().hex}
        json.dump(token, stream)
        stream.flush()
        os.fsync(stream.fileno())
        stream.close()
        yield token
    finally:
        if not stream.closed:
            stream.close()
        require(read_json(lock) == token, "Target lock ownership changed; manual recovery required")
        lock.unlink()


def move(source, destination):
    no_links(source)
    no_links(destination)
    require(not destination.exists(), f"Refuse overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.rename(source, destination)


def transaction_paths(game, state_dir, txid):
    require(isinstance(txid, str) and re.fullmatch(r"[0-9a-f]{32}", txid), "Invalid transaction ID")
    return (no_links(game / ".tgc-deploy/transactions" / txid),
            no_links(state_dir / "records" / (txid + ".json")))


def load_record(game, state_dir, catalog, txid):
    """Independent copies bind authority; neither journal nor state supplies paths."""
    tx, local = transaction_paths(game, state_dir, txid)
    record = read_json(tx / "record.json")
    require(record == read_json(local), "Immutable transaction copies disagree")
    try:
        require(record["metadata_schema"] == 2 and record["schema"] == SCHEMA
                and record["transaction_id"] == txid and record["target"] == str(game)
                and record["target_id"] == state_dir.name and record["state_dir"] == str(state_dir),
                "Immutable transaction target/schema mismatch")
        plan = record["plan"]
        unsigned = {k: v for k, v in plan.items() if k != "fingerprint"}
        require(digest(unsigned) == plan["fingerprint"], "Immutable plan integrity mismatch")
        require(plan["target"] == str(game) and plan["state_dir"] == str(state_dir)
                and plan["schema"] == SCHEMA and plan["catalog_digest"] == digest(catalog)
                and plan["runtime_policy"] == catalog["runtime_policy_version"]
                and plan["identity"]["clean"] and plan["identity"]["repository"] == EXPECTED_ORIGIN,
                "Immutable plan target/catalog/source mismatch")
        require(isinstance(record["generation"], int) and record["generation"] > 0
                and isinstance(record["adopt_existing"], bool), "Invalid transaction intent")
        require(record["units"] == plan["units"] and record["plan_fingerprint"] == plan["fingerprint"]
                and digest(record["previous_state"]) == plan["state_digest"]
                and record["previous_state"]["target"] == str(game)
                and record["previous_state"]["schema"] == SCHEMA,
                "Immutable snapshots/prior state mismatch")
        selected = selected_components(catalog, plan["profile"], plan["optional"])
        require([c["id"] for c in plan["components"]] == [c["id"] for c in selected],
                "Immutable component selection mismatch")
        pairs = [(c["id"], name, source) for c in selected for name, source in
                 ((c["destination_dir"], c["source_dir"]),
                  (c["destination_descriptor"], c["source_descriptor"]))]
        require([(u["component"], u["name"], u["source"]) for u in record["units"]] == pairs,
                "Immutable mapping/selection mismatch")
        for unit in record["units"]:
            for kind in ("old", "new"):
                value = unit[kind]
                require(value["kind"] in {"absent", "file", "directory"}, "Invalid snapshot kind")
                for name in value.get("files", {}):
                    if name:
                        relative(name)
                for name in value.get("dirs", []):
                    relative(name)
        require(record["adopt_existing"] or not any(c["adoption_required"] for c in plan["components"]),
                "Missing immutable adoption intent")
    except (KeyError, TypeError, ValueError) as exc:
        raise DeploymentError(f"Invalid immutable transaction {txid}: {exc}") from exc
    return record


def receipt(game, state_dir, record, name):
    tx, _ = transaction_paths(game, state_dir, record["transaction_id"])
    a = tx / (name + ".json")
    b = state_dir / name / (record["transaction_id"] + ".json")
    if not a.exists() and not b.exists():
        return None
    value = read_json(a)
    require(isinstance(value, dict) and value == read_json(b) and value.get("schema") == 2
            and value.get("transaction_id") == record["transaction_id"]
            and value.get("record_digest") == digest(record) and value.get("outcome") == name,
            f"Transaction {name} receipt mismatch")
    return value


def write_receipt(game, state_dir, record, name, **extra):
    tx, _ = transaction_paths(game, state_dir, record["transaction_id"])
    value = {"schema": 2, "transaction_id": record["transaction_id"],
             "record_digest": digest(record), "outcome": name, **extra}
    for path in (tx / (name + ".json"), state_dir / name / (record["transaction_id"] + ".json")):
        if path.exists():
            require(read_json(path) == value, "Refuse replacement of immutable receipt")
        else:
            write_json(path, value)


def owned_entry(record, cid):
    units = [u for u in record["units"] if u["component"] == cid]
    return {"transaction_id": record["transaction_id"], "commit": record["plan"]["identity"]["commit"],
            "mapping": [u["name"] for u in units], "snapshots": {u["name"]: u["new"] for u in units}}


def validated_manifest(game, state_dir, record):
    completed = receipt(game, state_dir, record, "completed")
    require(completed is not None, "Transaction has no corroborated verified outcome")
    manifest = read_json(state_dir / "manifests" / (record["transaction_id"] + ".json"))
    require(digest(manifest) == completed.get("manifest_digest"), "Manifest integrity mismatch")
    plan = record["plan"]
    expected = {"schema": SCHEMA, "runtime_policy": plan["runtime_policy"], **plan["identity"],
                "target": str(game), "state_dir": str(state_dir), "transaction_id": record["transaction_id"],
                "profile": plan["profile"], "components": plan["components"], "mapping": record["units"],
                "previous_state": record["previous_state"], "outcome": "verified"}
    require(all(manifest.get(k) == v for k, v in expected.items()), "Manifest transaction binding mismatch")
    files = {u["name"] + ("/" + rel if rel else ""): info for u in record["units"]
             for rel, info in u["new"]["files"].items()}
    require(manifest.get("files") == files and manifest.get("digest") == digest(files)
            and manifest.get("file_count") == len(files)
            and manifest.get("bytes") == sum(f["size"] for f in files.values()), "Manifest snapshot mismatch")
    return manifest


def transaction_records(game, state_dir, catalog):
    base = no_links(game / ".tgc-deploy/transactions")
    records = []
    if base.exists():
        for folder in base.iterdir():
            no_links(folder)
            require(folder.is_dir(), f"Unexpected transaction entry: {folder}")
            records.append(load_record(game, state_dir, catalog, folder.name))
    local = no_links(state_dir / "records")
    if local.exists():
        require({p.name for p in local.iterdir()} == {r["transaction_id"] + ".json" for r in records},
                "Transaction inventory differs between target and state")
    generations = [r["generation"] for r in records]
    require(len(generations) == len(set(generations)), "Duplicate transaction generation")
    return sorted(records, key=lambda r: r["generation"])


def ownership_ledger(game, state_dir, catalog, exclude=None):
    expected = {}
    for record in transaction_records(game, state_dir, catalog):
        restored = receipt(game, state_dir, record, "restored")
        if record["transaction_id"] == exclude or restored:
            continue
        if receipt(game, state_dir, record, "completed"):
            tx, _ = transaction_paths(game, state_dir, record["transaction_id"])
            validate_journal(read_json(tx / "journal.json"), game, catalog, state_dir)
            validated_manifest(game, state_dir, record)
            for cid in {u["component"] for u in record["units"]}:
                expected[cid] = owned_entry(record, cid)
    return expected


def validate_ownership(state, game, state_dir, catalog):
    try:
        require(state["schema"] == SCHEMA and state["target"] == str(game)
                and isinstance(state["components"], dict), "State schema/target mismatch")
        require(state["components"] == ownership_ledger(game, state_dir, catalog),
                "State ownership lacks matching transaction/manifest provenance")
    except (DeploymentError, KeyError, TypeError, ValueError) as exc:
        raise DeploymentError(f"Existing state is untrusted; recovery/intervention required: {exc}") from exc


def validate_journal(journal, game, catalog, state_dir):
    try:
        record = load_record(game, state_dir, catalog, journal["transaction_id"])
        require(all(journal.get(k) == v for k, v in record.items()),
                "Journal authority differs from immutable transaction")
        require(journal.get("record_digest") == digest(record), "Journal record digest mismatch")
        require(journal.get("status") in INCOMPLETE | {"verified", "rolled-back"}, "Unknown journal status")
    except (KeyError, TypeError, ValueError) as exc:
        raise DeploymentError(f"Invalid journal: {exc}") from exc
    return record


def copy_old(backup, staging, expected):
    """Prepare only in our transaction workspace, with link checks on each entry."""
    require(snapshot(backup) == expected, f"Backup damaged: {backup}")
    no_links(staging)
    if expected["kind"] == "directory":
        staging.mkdir()
        for name in expected["dirs"]:
            no_links(backup / name)
            no_links(staging / name).mkdir(parents=True, exist_ok=True)
        for name in expected["files"]:
            source, target = no_links(backup / name), no_links(staging / name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    else:
        shutil.copyfile(no_links(backup), no_links(staging))
    require(snapshot(staging) == expected, f"Rollback staging verification failed: {staging}")


def restore_transaction(journal, game, state_dir, catalog, explicit=False):
    record = validate_journal(journal, game, catalog, state_dir)
    tx, _ = transaction_paths(game, state_dir, record["transaction_id"])
    # Terminal retries need the same apply provenance and mode checks as restoration.
    completed = receipt(game, state_dir, record, "completed")
    mode = "rollback" if completed else "recovery"
    authorized = receipt(game, state_dir, record, "rollback-authorized")
    require(authorized is None or authorized.get("mode") == mode, "Rollback/recovery mode mismatch")
    if completed:
        validated_manifest(game, state_dir, record)
    if receipt(game, state_dir, record, "restored"):
        # Crash after both terminal receipts but before the operational journal.
        require(authorized is not None,
                "Restored transaction lacks rollback authorization")
        validate_ownership(read_state(state_dir, game), game, state_dir, catalog)
        for unit in record["units"]:
            require(snapshot(game / "mod" / unit["name"]) == unit["old"], "Restored live changed; recovery refused")
        journal["status"] = "rolled-back"
        write_json(tx / "journal.json", journal)
        write_json(state_dir / "transactions" / (record["transaction_id"] + ".json"), journal)
        return
    state = read_state(state_dir, game)
    ledger = ownership_ledger(game, state_dir, catalog)
    without = ownership_ledger(game, state_dir, catalog, exclude=record["transaction_id"])
    cids = {u["component"] for u in record["units"]}
    for cid in cids:
        prior = record["previous_state"]["components"].get(cid)
        require(without.get(cid) == prior, "Later deployment owns this component; rollback/recovery refused")
        expected = owned_entry(record, cid) if completed else prior
        require(ledger.get(cid) == expected, "Later deployment owns this component; rollback refused")
        allowed = [expected]
        if not completed:
            allowed.append(owned_entry(record, cid))  # crash after state write, before completion
        elif authorized:
            allowed.append(prior)  # crash after restored state, before restored receipt
        require(state["components"].get(cid) in allowed, "Existing state is untrusted; recovery/intervention required")
    require({k: v for k, v in state["components"].items() if k not in cids}
            == {k: v for k, v in ledger.items() if k not in cids}, "Unrelated ownership is untrusted")

    phases = journal.get("rollback_units", {})
    require(isinstance(phases, dict) and set(phases) <= {u["name"] for u in record["units"]},
            "Unknown rollback unit")
    observations = []
    # Check every unit before changing any live entry. Operational phases only
    # narrow allowed filesystem combinations; they cannot confer authority.
    for unit in record["units"]:
        name, old, new = unit["name"], unit["old"], unit["new"]
        live, backup = game / "mod" / name, tx / "backup" / name
        staging, displaced = tx / "rollback-staging" / name, tx / "displaced" / name
        current, saved, staged, removed = map(snapshot, (live, backup, staging, displaced))
        phase = phases.get(name, "not-started")
        if completed and authorized is None:
            require(current == new and staged["kind"] == "absent" and removed["kind"] == "absent"
                    and phase == "not-started", f"Completed live changed; rollback refused: {live}")
        require(phase in {"not-started", "preparing", "ready", "displacing", "displaced", "publishing", "published", "verified"},
                f"Invalid rollback phase: {name}")
        require(current in (old, new, {"kind": "absent"}), f"Live changed; preserve and recover manually: {live}")
        require(saved == old or (saved["kind"] == "absent" and current == old), f"Backup damaged/unavailable: {backup}")
        require(removed in ({"kind": "absent"}, new), f"Unexpected displaced content: {displaced}")
        require(staged == old or staged["kind"] == "absent" or phase == "preparing",
                f"Unexpected rollback staging: {staging}")
        if phase == "verified":
            require(current == old, f"Restored live changed: {live}")
        if removed["kind"] != "absent":
            require(current == old or current["kind"] == "absent", f"Ambiguous displacement: {live}")
            require(phase in {"displacing", "displaced", "publishing", "published", "verified"},
                    f"Displacement without persisted intent: {live}")
        if current == old and removed["kind"] != "absent":
            require(staged["kind"] == "absent", f"Ambiguous rollback publication: {live}")
        observations.append((unit, live, backup, staging, displaced, current, phase))

    write_receipt(game, state_dir, record, "rollback-authorized", mode=mode)
    journal["rollback_started"] = True
    journal["rollback_mode"] = mode
    journal["status"] = "rolling-back"
    journal["rollback_units"] = phases
    def checkpoint(name, phase):
        phases[name] = phase
        write_json(tx / "journal.json", journal)
    write_json(tx / "journal.json", journal)
    (tx / "rollback-staging").mkdir(exist_ok=True)
    # Prepare and verify all restorations before displacing any live unit. A
    # scan/copy error on a later directory must not publish an earlier descriptor.
    for unit, live, backup, staging, displaced, current, phase in reversed(observations):
        name, old = unit["name"], unit["old"]
        if current == old:
            continue
        if old["kind"] != "absent" and snapshot(staging) != old:
            checkpoint(name, "preparing")
            # Only a partial copy in our derived staging path can be discarded.
            partial = snapshot(staging)  # refuses links and scan errors before cleanup
            if partial["kind"] == "directory":
                shutil.rmtree(no_links(staging))
            elif partial["kind"] == "file":
                staging.unlink()
            copy_old(backup, staging, old)
        checkpoint(name, "ready" if not displaced.exists() else "displaced")
    for unit, live, backup, staging, displaced, current, phase in observations:
        if current != unit["old"] and unit["old"]["kind"] != "absent":
            require(snapshot(staging) == unit["old"], "Rollback staging changed before displacement")
    for unit, live, backup, staging, displaced, current, phase in reversed(observations):
        name, old = unit["name"], unit["old"]
        if current == old:
            checkpoint(name, "verified")
            continue
        if live.exists():
            require(snapshot(live) == unit["new"], f"Live changed before displacement: {live}")
            checkpoint(name, "displacing")
            move(live, displaced)
        checkpoint(name, "displaced")
        if old["kind"] != "absent":
            require(snapshot(staging) == old, "Rollback staging changed before publish")
            checkpoint(name, "publishing")
            move(staging, live)
        checkpoint(name, "published")
        require(snapshot(live) == old, f"Rollback verification failed: {live}")
        checkpoint(name, "verified")
    for unit in record["units"]:
        require(snapshot(game / "mod" / unit["name"]) == unit["old"], "Rollback verification failed")
    for cid in cids:
        previous = record["previous_state"]["components"].get(cid)
        if previous is None:
            state["components"].pop(cid, None)
        else:
            state["components"][cid] = previous
    write_json(state_dir / "state.json", state)
    write_receipt(game, state_dir, record, "restored")
    journal["status"] = "rolled-back"
    journal["finished_utc"] = utc()
    write_json(tx / "journal.json", journal)
    write_json(state_dir / "transactions" / (record["transaction_id"] + ".json"), journal)


def apply_plan(plan, root, game, catalog_path, state_base=None, adopt_existing=False):
    require(plan.get("schema") == SCHEMA, "Invalid plan schema")
    current = build_plan(root, game, catalog_path, plan["profile"], plan["optional"], state_base)
    require(current == plan, "Plan stale/tampered: source, HEAD, live, state or catalog changed")
    require(not current["blockers"], "; ".join(current["blockers"]))
    require(adopt_existing or not any(c["adoption_required"] for c in plan["components"]),
            "Existing unowned live requires --adopt-existing")
    root, game, state_dir = target_paths(root, game, state_base)
    catalog = load_catalog(catalog_path)
    require(not any(getattr((game / "mod" / u["name"]).stat(), "st_file_attributes", 0) & 1
                    for u in plan["units"] if (game / "mod" / u["name"]).is_file()), "Read-only descriptor refused")
    writable_files(plan["units"], game)
    required_bytes = sum(f["size"] for u in plan["units"] for kind in ("old", "new")
                         for f in u[kind].get("files", {}).values()) * 2 + 1024 * 1024
    require(shutil.disk_usage(game).free >= required_bytes, "Insufficient staging/rollback space")
    # Probe only our workspace, outside mod. Check mod parent permissions as well;
    # ACL/rename races can still fail later and are covered by coordinated rollback.
    writable_mod_parent(game)
    work = no_links(game / ".tgc-deploy")
    work.mkdir(exist_ok=True)
    probe = work / ("write-probe-" + uuid.uuid4().hex)
    with probe.open("x") as stream:
        stream.write("probe")
    renamed_probe = probe.with_name(probe.name + ".renamed")
    try:
        os.rename(probe, renamed_probe)
    finally:
        if probe.exists():
            probe.unlink()
        if renamed_probe.exists():
            renamed_probe.unlink()
    with target_lock(game) as lock:
        require(not pending(game, state_dir, catalog, lock), "Incomplete transaction requires recovery")
        check = build_plan(root, game, catalog_path, plan["profile"], plan["optional"], state_base, owned_lock=lock)
        require(check == plan, "Plan changed before staging")
        records = transaction_records(game, state_dir, catalog)
        txid = uuid.uuid4().hex
        tx = game / ".tgc-deploy/transactions" / txid
        tx.mkdir(parents=True)
        for name in ("staging", "backup", "displaced"):
            (tx / name).mkdir()
        previous = read_state(state_dir, game)
        immutable = {"schema": SCHEMA, "metadata_schema": 2, "transaction_id": txid,
                     "target": str(game), "target_id": state_dir.name, "state_dir": str(state_dir),
                     "generation": max((r["generation"] for r in records), default=0) + 1,
                     "started_utc": utc(), "plan": plan, "adopt_existing": adopt_existing,
                     "units": plan["units"], "previous_state": previous, "plan_fingerprint": plan["fingerprint"]}
        write_json(tx / "record.json", immutable)
        write_json(state_dir / "records" / (txid + ".json"), immutable)
        journal = {**immutable, "record_digest": digest(immutable), "status": "planned"}
        def record(status):
            journal["status"] = status
            write_json(tx / "journal.json", journal)
            write_json(state_dir / "transactions" / (txid + ".json"), journal)
        try:
            record("planned")
            write_json(state_dir / "plans" / (txid + ".json"), plan)
            record("staging")
            for unit in journal["units"]:
                destination = tx / "staging" / unit["name"]
                source = root / unit["source"]
                if unit["new"]["kind"] == "directory":
                    destination.mkdir(parents=True)
                    for rel in unit["new"]["files"]:
                        target = destination / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        no_links(source / rel)
                        shutil.copyfile(source / rel, target)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    no_links(source)
                    shutil.copyfile(source, destination)
                require(snapshot(destination) == unit["new"], "Staging verification failed")
            require(git_identity(root) == plan["identity"], "Git changed during staging")
            for unit in journal["units"]:
                require(snapshot(game / "mod" / unit["name"]) == unit["old"], "Live changed during staging")
                if unit["new"]["kind"] == "file":
                    require(snapshot(root / unit["source"]) == unit["new"], "Source changed during staging")
                else:
                    comp = next(c for c in catalog["components"] if c["id"] == unit["component"])
                    tracked = [os.fsdecode(p) for p in git(root, "ls-files", "-z").split(b"\0") if p]
                    require(source_payload(root, comp, tracked) == unit["new"], "Source changed during staging")
            writable_files(plan["units"], game)
            record("publishing")
            for unit in journal["units"]:
                live = game / "mod" / unit["name"]
                journal["intent"] = unit["name"]
                record("publishing")
                if unit["old"]["kind"] != "absent":
                    require(snapshot(live) == unit["old"], "Live changed before backup")
                    move(live, tx / "backup" / unit["name"])
                    require(snapshot(tx / "backup" / unit["name"]) == unit["old"], "Backup verification failed")
                move(tx / "staging" / unit["name"], live)
                record("publishing")
            record("verifying")
            for unit in journal["units"]:
                require(snapshot(game / "mod" / unit["name"]) == unit["new"], "Post-copy verification failed")
            entries = {u["name"] + ("/" + rel if rel else ""): info for u in plan["units"]
                       for rel, info in u["new"]["files"].items()}
            manifest = {"schema": SCHEMA, "runtime_policy": plan["runtime_policy"], **plan["identity"],
                        "target": str(game), "state_dir": str(state_dir),
                        "profile": plan["profile"], "components": plan["components"], "mapping": plan["units"],
                        "files": entries, "file_count": len(entries), "bytes": sum(f["size"] for f in entries.values()),
                        "digest": digest(entries), "utc": utc(), "transaction_id": txid, "outcome": "verified",
                        "backup": str(tx / "backup"), "previous_state": previous}
            write_json(state_dir / "manifests" / (txid + ".json"), manifest)
            state = read_state(state_dir, game)
            for cid in {u["component"] for u in plan["units"]}:
                state["components"][cid] = owned_entry(immutable, cid)
            write_json(state_dir / "state.json", state)
            write_receipt(game, state_dir, immutable, "completed", manifest_digest=digest(manifest))
            record("verified")
            return manifest
        except BaseException as exc:
            journal["error"] = str(exc)
            try:
                restore_transaction(journal, game, state_dir, catalog)
            except BaseException as recovery:
                journal["recovery_error"] = str(recovery)
                record("recovery-required")
                raise DeploymentError(f"Recovery required for {txid}: {recovery}") from exc
            raise DeploymentError(f"Transaction {txid} rolled back: {exc}") from exc


def verify_target(root, game, catalog_path, state_base=None):
    _, game, state_dir = target_paths(root, game, state_base)
    state = read_state(state_dir, game)
    catalog = load_catalog(catalog_path)
    validate_ownership(state, game, state_dir, catalog)
    require(state["components"], "No registered payload")
    require(not pending(game, state_dir, catalog), "Incomplete transaction/lock: recovery required")
    result = {}
    for cid, owned in state["components"].items():
        record = load_record(game, state_dir, catalog, owned["transaction_id"])
        manifest = validated_manifest(game, state_dir, record)
        for name, value in owned["snapshots"].items():
            require(snapshot(game / "mod" / name) == value, f"Live differs from verified manifest: {name}")
        result[cid] = {"commit": owned["commit"], "transaction_id": owned["transaction_id"],
                       "payload_digest": manifest["digest"]}
    return result


def recover_stale_lock(game):
    lock = no_links(game / ".tgc-deploy/lock")
    if not lock.exists():
        return
    value = read_json(lock)
    pid = value["pid"]
    require(isinstance(pid, int) and pid > 0, "Invalid lock PID")
    if os.name == "nt":
        result = subprocess.run(["tasklist", "/FO", "CSV", "/NH", "/FI", f"PID eq {pid}"],
                                capture_output=True, check=False)
        require(result.returncode == 0, "Cannot establish stale lock; manual recovery required")
        import csv
        alive = any(len(row) > 1 and row[1] == str(pid) for row in
                    csv.reader(result.stdout.decode(errors="replace").splitlines()))
    else:
        try:
            os.kill(pid, 0)
            alive = True
        except ProcessLookupError:
            alive = False
    require(not alive, "Lock owner is still running; recovery refused")
    require(read_json(lock) == value, "Lock changed during recovery")
    lock.unlink()


def rollback(root, game, catalog_path, txid, state_base=None, recover_lock=False):
    require(isinstance(txid, str) and re.fullmatch(r"[0-9a-f]{32}", txid), "Invalid transaction ID")
    _, game, state_dir = target_paths(root, game, state_base)
    catalog = load_catalog(catalog_path)
    journal_path = game / ".tgc-deploy/transactions" / txid / "journal.json"
    # Validate before using even a name from the journal for a live probe.
    journal = read_json(journal_path)
    require(journal.get("transaction_id") == txid, "Transaction binding mismatch")
    record = validate_journal(journal, game, catalog, state_dir)
    writable_files([dict(u, old=snapshot(game / "mod" / u["name"])) for u in record["units"]], game)
    if recover_lock:
        recover_stale_lock(game)
    with target_lock(game) as lock:
        other = [p for p in pending(game, state_dir, catalog, lock) if p != txid]
        require(not other, "Other incomplete transaction requires recovery first")
        # Re-read under lock; preflight journal must not survive a concurrent change.
        journal = read_json(journal_path)
        require(journal.get("transaction_id") == txid, "Transaction binding mismatch")
        validate_journal(journal, game, catalog, state_dir)
        journal.pop("rollback_started", None)
        try:
            restore_transaction(journal, game, state_dir, catalog, explicit=True)
        except BaseException as exc:
            if journal.get("rollback_started"):
                journal["status"] = "recovery-required"
                journal["recovery_error"] = str(exc)
                write_json(journal_path, journal)
            raise
    return {"transaction_id": txid, "status": "rolled-back"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply", "verify", "rollback"))
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--state-root", type=Path, help="Override local metadata base; useful for simulations")
    parser.add_argument("--profile", choices=("core", "core+1966"), default="core")
    parser.add_argument("--optional", action="append", default=[])
    parser.add_argument("--plan-file", type=Path, help="apply input; plan always emits JSON to stdout")
    parser.add_argument("--adopt-existing", action="store_true")
    parser.add_argument("--transaction-id")
    parser.add_argument("--recover-lock", action="store_true", help="Rollback only: remove lock if its PID is demonstrably gone")
    args = parser.parse_args(argv)
    catalog = Path(__file__).with_name("components.json")
    try:
        if args.command == "plan":
            result = build_plan(args.repo_root, args.game_root, catalog, args.profile, args.optional, args.state_root)
        elif args.command == "apply":
            require(args.plan_file is not None, "apply requires --plan-file")
            result = apply_plan(read_json(args.plan_file), args.repo_root, args.game_root, catalog,
                                args.state_root, args.adopt_existing)
        elif args.command == "verify":
            result = verify_target(args.repo_root, args.game_root, catalog, args.state_root)
        else:
            require(args.transaction_id is not None, "rollback requires --transaction-id")
            result = rollback(args.repo_root, args.game_root, catalog, args.transaction_id, args.state_root, args.recover_lock)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if args.command == "plan" and result["blockers"] else 0
    except (DeploymentError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
