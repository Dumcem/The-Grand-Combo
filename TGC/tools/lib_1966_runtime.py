"""Declared core + Timeline filesystem, independent of the balance rules.

This is a repository composition, not an observation of a launcher or save.
Alice v1.3.0: simple_fs_win.cpp list_files/open_file; cultures_parsing.cpp
make_tech_folder_list; system_state.cpp invention/unit loading. Victoria II's
dependency/file overlay is the supported project layout; exotic layouts remain
explicit boundaries rather than guessed runtime behavior.
"""
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from lib_1966_parser import Node, Position, ScriptError, member, parse_file, scalar, unique_definitions


@dataclass(frozen=True)
class Source:
    runtime_path: str
    file: str
    layer: str
    classification: str


@dataclass
class RuntimeInventory:
    selected: dict[str, Source]
    replaced: list[Source]
    excluded: list[Source]
    boundaries: list[str]

    def files(self, directory: str) -> list[str]:
        return [s.file for _, s in sorted(self.selected.items())
                if s.runtime_path.startswith(directory + '/') and s.classification == 'direct']

    def require(self, runtime_path: str) -> str:
        if runtime_path not in self.selected:
            raise ScriptError(f'declared composition missing {runtime_path}')
        return self.selected[runtime_path].file


def _safe_path(raw: str) -> str:
    raw = raw.replace('\\', '/')
    path = PurePosixPath(raw)
    if path.is_absolute() or ':' in raw or '..' in path.parts or not path.parts:
        raise ScriptError(f'unsupported descriptor path {raw!r}')
    return str(path)


def compose_runtime(repo: Path, core_root: str = 'TGC', timeline_root: str = 'TGC_Timeline_1966') -> RuntimeInventory:
    selected: dict[str, Source] = {}
    replaced: list[Source] = []
    boundaries = ['Declared core + Timeline only; optional mods, launcher, saves and scripted acquisition histories are not observed.',
                  'National/conditional modifiers, leaders, terrain, production capacity and prices are outside the additive unit-stat scenario.']
    core_name = None
    core_replaces: set[str] = set()
    categories = {'technologies', 'inventions', 'units', 'common', 'events', 'decisions'}
    for layer, root in [('core', core_root), ('timeline', timeline_root)]:
        root = _safe_path(root)
        descriptor = root + '.mod'
        doc = parse_file(str(repo / descriptor))
        # Repeated replace_path is intentional; other scalar metadata is unique.
        pos = Position(descriptor, 1, 1, 0)
        holder = Node('descriptor', '=', doc.nodes, pos, pos)
        name = scalar(holder, 'name', required=True)
        if member(holder, 'archive') is not None:
            raise ScriptError(f'{descriptor}: archive loading is outside the repository-folder composition contract')
        path = _safe_path(scalar(holder, 'path', required=True))
        if path != 'mod/' + PurePosixPath(root).name:
            raise ScriptError(f'{descriptor}: descriptor path does not identify requested root {root}')
        deps = member(holder, 'dependencies')
        if layer == 'core':
            core_name = name
        elif deps is None or not deps.is_group or [n.value for n in deps.children] != [core_name]:
            raise ScriptError(f'{descriptor}: expected dependency on exactly {core_name!r}; composition unresolved')
        replaces = []
        for n in doc.nodes:
            if n.key is None or n.operator != '=':
                raise ScriptError(f'{n.start}: unsupported descriptor entry')
            if n.keyword == 'replace_path':
                if n.is_group:
                    raise ScriptError(f'{n.start}: replace_path must be scalar')
                replaces.append(_safe_path(n.value))
        if layer == 'core':
            core_replaces.update(replaces)
        for prefix in replaces:
            for rel in list(selected):
                if rel == prefix or rel.startswith(prefix + '/'):
                    replaced.append(selected.pop(rel))
        base = repo / root
        if not base.is_dir():
            raise ScriptError(f'{root}: runtime root missing')
        # Engines enumerate immediate files in these data directories, not arbitrary
        # nested repository files. Keep omitted nested inputs visible as a boundary.
        for directory in sorted(categories):
            for f in sorted((base / directory).glob('*.txt')):
                rel = directory + '/' + f.name
                if any(k.casefold() == rel.casefold() and k != rel for k in selected):
                    raise ScriptError(f'{rel}: case-colliding runtime paths')
                if rel in selected:
                    replaced.append(selected[rel])
                classification = 'direct' if directory in {'technologies', 'inventions', 'units'} else 'conditional/context'
                selected[rel] = Source(rel, f.relative_to(repo).as_posix(), layer, classification)
            if any((base / directory).glob('*/*.txt')):
                boundaries.append(f'{root}/{directory}: nested files are not assumed loaded by immediate-directory enumeration')
    for directory in sorted(categories):
        if directory not in core_replaces:
            boundaries.append(f'{directory}: vanilla fallback not excluded by core replace_path; external base is unavailable')
    inv = RuntimeInventory(dict(sorted(selected.items())), replaced, [], boundaries)
    # Alice loads technology branches named by common/technology.txt. An orphan
    # technology file must not become an applied source merely by existing.
    roots = unique_definitions(parse_file(str(repo / inv.require('common/technology.txt'))).definitions)
    if 'folders' not in roots:
        raise ScriptError('common/technology.txt: missing folders')
    branches = unique_definitions(roots['folders'].children)
    scheduled = {'technologies/' + name + '.txt' for name in branches}
    for rel in sorted(scheduled):
        inv.require(rel)
    for rel in list(inv.selected):
        if rel.startswith('technologies/') and rel not in scheduled:
            src = inv.selected.pop(rel)
            inv.excluded.append(Source(rel, src.file, src.layer, 'unreferenced technology; V2 loading unverified'))
    return inv


def unit_definitions(inventory: RuntimeInventory, repo: Path) -> dict[str, str]:
    """Identifiers come from definitions, never filenames or the ruleset."""
    out: dict[str, str] = {}
    for file in inventory.files('units'):
        for key in unique_definitions(parse_file(str(repo / file)).definitions):
            if key in out:
                raise ScriptError(f'duplicate effective unit {key}: {out[key]}, {file}')
            out[key] = file
    return dict(sorted(out.items()))
