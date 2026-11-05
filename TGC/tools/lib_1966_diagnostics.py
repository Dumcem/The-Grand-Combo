"""Structured findings. Classification and grouping never inspect prose."""
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json

CATEGORIES = ('integrity', 'source_scope', 'engine_semantics', 'evidence_gap', 'numeric_rule', 'economic_index', 'observation')


@dataclass(frozen=True)
class Diagnostic:
    level: str
    message: str
    code: str
    category: str
    unit: str | None = None
    stat: str | None = None
    source: str | None = None
    engine: str = 'raw_script'
    evidence: str = 'inventory'
    uncertainty: str = 'not_runtime_certification'
    cause: str | None = None
    scope: str | None = None
    data: dict | None = None


class Reporter:
    def __init__(self):
        self.diagnostics: list[Diagnostic] = []

    @property
    def items(self):
        # Compatibility view for callers that only need severity and prose.
        return [(d.level, d.message) for d in self.diagnostics]

    def add(self, level, message, *, code='observation', category='observation', **metadata):
        if level not in {'FAIL', 'WARN', 'INFO'} or category not in CATEGORIES:
            raise ValueError('invalid diagnostic severity/category')
        self.diagnostics.append(Diagnostic(level, message, code, category, **metadata))

    def dump(self, *, details=True):
        counts = Counter(d.level for d in self.diagnostics)
        print('1966 BALANCE AUDIT (technical integrity + unvalidated rule diagnostics)')
        for level in ('FAIL', 'WARN', 'INFO'):
            print(f' - {level}: {counts[level]}')
        if not details:
            return
        for level in ('FAIL', 'WARN', 'INFO'):
            group = [d for d in self.diagnostics if d.level == level]
            if group:
                print(f'\n[{level}]')
                for d in group:
                    print(f' - [{d.category}/{d.code}; engine={d.engine}; evidence={d.evidence}] {d.message}')

    def summary(self):
        groups = defaultdict(list)
        for d in self.diagnostics:
            if d.level != 'INFO' or d.category == 'evidence_gap':
                # One engine/property contract issue can affect the entire roster.
                # Group that root cause across units; retain units on each record.
                unit = None if d.category == 'engine_semantics' else d.unit
                key = (d.category, d.engine, d.cause or d.code, unit, d.stat)
                groups[key].append(d)
        print('\nPRIORITY SUMMARY')
        # Technical categories precede possible numerical anomalies. No new
        # numerical balancing weights or quality thresholds are introduced.
        for category in CATEGORIES[:-1]:
            entries = [(k, ds) for k, ds in groups.items() if k[0] == category]
            entries.sort(key=lambda x: (not any(d.level == 'FAIL' for d in x[1]), x[0][3] is not None, str(x[0])))
            print(f' - {category}: {len(entries)} cause group(s)')
            for key, ds in entries[:8]:
                units = sorted({d.unit for d in ds if d.unit})
                scopes = sorted({d.scope for d in ds if d.scope and d.unit is None})
                affected = f' | named_units={len(units)}, global_scopes={scopes}' if category == 'engine_semantics' else ''
                print(f'   * {key[1]} | {key[3] or "global"}/{key[4] or "scope"} | {key[2]} | findings={len(ds)}{affected} | {ds[0].message}')
        print('\nRECOMMENDED PLAYTEST FOCUS (informational only; no correctness verdict)')
        candidates = [(k, ds) for k, ds in groups.items() if k[0] == 'numeric_rule' and k[3] and k[4]]
        candidates.sort(key=lambda x: str(x[0]))
        for key, ds in candidates[:5]:
            print(f' - {key[3]} {key[4]}: {len(ds)} raw-script rule finding(s); normative basis UNVALIDATED')
        if not candidates:
            print(' - No qualified numeric-rule candidates; inspect evidence and integrity groups.')

    def json(self):
        return json.dumps([asdict(d) for d in self.diagnostics], sort_keys=True, ensure_ascii=True)
