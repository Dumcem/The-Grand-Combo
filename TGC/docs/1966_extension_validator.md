# 1966 extension static validator

This repository includes a lightweight static validator for the separated 1966
timeline architecture.

- Script: `TGC/tools/validate_1966_extension.py`
- Scope manifest: `TGC/tools/1966_extension_scope.json`
- Default core root: `TGC/`
- Default 1966 runtime root: `TGC_Timeline_1966/`

The [Timeline manifest](../../TGC_Timeline_1966/docs/manifest_1966_timeline.md)
defines the composition and the carrier inventory. The default validator scope
is the canonical core and Timeline pair. The assembled Loader profiles have a
separate [deployment composition](../../docs/deployment/script_extender_profile.md).

## What it checks

The validator is manifest-driven and now checks two layers:

1. **Timeline submod runtime presence and coherence**
   - `TGC_Timeline_1966/common/defines.lua` keeps `end_date = '1966.1.1'`.
   - `TGC_Timeline_1966/decisions/00_Setup.txt` keeps `option_end_game` aligned
     with `year = 1966` in both `potential` and `allow`.
   - `TGC_Timeline_1966/interface/backend.gui` keeps `text = "The World in 1966"`.
   - The five timeline technology files have the expected 25 areas at 12 tiers
     each.
   - Tracked `NEW_*_inventions.txt` files are present and localized.
   - Carrier/submarine units and key binary assets exist in the submod.
   - Unit-target effects in all effective technology/invention sources resolve
     against identifiers read from effective unit definitions. The source layer
     is composed from the descriptors; a filename is not a unit identifier.

2. **Core cleanup**
   - `TGC/common/defines.lua` must not contain the 1966 end date.
   - `TGC/interface/backend.gui` must not show `The World in 1966`.
   - Timeline-only runtime files such as `TGC/units/aircraftcarrier.txt`,
     `TGC/units/submarine.txt`, `TGC/inventions/NEW_*_inventions.txt`, and the
     old `TGC/localisation/00_SUP_technology.csv` / `00_other_tech.csv` must not
     remain in core.

Known false positives such as historical Hunley submarine flavour text, province
id `1966`, and pre-existing `submarine_warfare` modifiers are not represented as
forbidden validator patterns. The ruleset also requires the root README's
Timeline name and manifest reference, and checks the presence of the extension
audit, validator guide, [mixed-file note](../../TGC_Timeline_1966/docs/TODO_mixed_files.md)
and Timeline manifest at their current paths. The drift checker additionally extracts the manifest's override/carrier
table. Structural checks and drift findings do not establish runtime behavior.
See the [verification boundaries](1966_extension_audit.md).

## Run

From repository root:

```bash
python -B TGC/tools/validate_1966_extension.py
```

Optional roots are available for compatibility/testing:

```bash
python TGC/tools/validate_1966_extension.py --core-root TGC --timeline-root TGC_Timeline_1966
```

The script exits with code `0` when all targeted checks pass, and `1` with a
failure list otherwise.

## Structural extraction contract

The shared reader `TGC/tools/lib_1966_parser.py` tokenizes comments, quoted
strings, operators and braces before constructing a tree. Newlines and inline
layout do not determine which definitions exist. Identifiers are preserved,
including uppercase names such as `IBRD` and `IDA`. Source positions contain
file, physical line, column and character offset. Every occurrence is retained;
there is no implicit last-definition-wins dictionary conversion.

Known schema keywords are matched without case, as in Alice 1.3.0's
[parser generator](https://github.com/schombert/Project-Alice/blob/v1.3.0/ParserGenerator/parser_generator.cpp).
This keyword view never renames technology, invention, area, unit or commodity
identifiers. Duplicate metadata differing only in keyword case is still ambiguous.

`parse_top_level_blocks()` now returns a tuple of `Node` occurrences, not the old
dictionary of body lines. `parse_file()` returns a `Document`; callers explicitly
select named definitions and their direct children. Unsupported free entries in
definition contexts, incomplete groups, stray closing braces, unterminated
single-line strings and unreadable inputs raise `ScriptError`. A caller cannot
consume a partial document after one of these errors.

Technology `area` and `year` are direct properties. Missing, repeated or malformed
metadata and areas outside the manifest are diagnosed, rather than allowing an
unknown year to bypass localisation checks. Years in AI/chance/limit groups are
not technology metadata. Inventions need no direct year: localisation is checked
for every tracked definition independently of dating. Definition duplicates are
checked both inside files and across the tracked files, with occurrence locations.

Unit-target checks select technology modifiers and invention effect bodies
structurally, including inline blocks. They reject free entries outside list
contexts, duplicate `effect` groups, non-assignment operators and malformed known
numeric modifiers. Alice's confirmed `defense` alias is canonicalized for this
inventory without asserting Victoria II alias support. Unsupported grouped unit
properties remain explicit semantic limitations rather than being mistaken for
scalar deltas or declared invalid runtime data solely due to this tool's subset.
Decision-year checks select the named
decision under `political_decisions` and its direct positive section gates;
comments and nested NOT conditions cannot satisfy them. Raw required-pattern
checks for Lua, GUI and documentation remain targeted manifest checks, not a
complete validator for those languages.

Decoding defaults to strict UTF-8 (an initial BOM is consumed). Legacy
localisation is explicitly read as Latin-1; `read_text(..., encoding=...)` allows
other declared encodings without lossy fallback. Invalid bytes produce a
diagnostic with byte offset instead of changing identifiers silently. String
tokenization follows Project Alice v1.3.0's single-line, non-escaping treatment
of single and double quotes; this does not certify every Victoria II string or
encoding convention. Free values and free groups are retained for list contexts;
consumers reject them where their analysis needs named definitions/assignments.

The supported subset is a structural inventory, not the complete engine grammar,
runtime file-loading model or a proof of general Alice/Victoria II compatibility.
Duplicate metadata is treated as ambiguous analysis input even where a runtime
may accept it with an engine-specific precedence. The old parser API has only
the two in-repository callers, both migrated together.

The effective-source contract now covers the declared `TGC + Timeline` pair via
`lib_1966_runtime.py`, including core army inventions. Technology scheduling is
read from effective `common/technology.txt`; invention files overlay by runtime
path. Optional mods, actual launcher state, saves and any unprovided vanilla
fallback are not certified. Localisation/tier/cleanup checks remain manifest
scoped: broadening target validation does not claim broad localisation coverage.

The validator prints a count of physical-property Alice semantic limitations and
explicitly leaves Victoria II script semantics unverified. A structural PASS does
not certify engine application. The balance auditor supplies source-specific
findings and applied-subset projections; see `1966_balance_audit.md`. In
particular, ignored `max_strength`/`limit_per_port`, unsupported modifiers and
integer-prefix organisation conversion are not treated as common engine behavior.
JSON configuration rejects duplicate keys and non-finite constants. Numeric rule
schema checks in the auditor are integrity checks, not normative validation.

Independent regression tests live outside the runtime trees:

```bash
python -B -m unittest discover -s tools/tests -v
```

They compare the current corpus to a separate token-stream/stack inventory,
exercise malformed-input failure and duplicate retention, and run the balance
report across processes and hash seeds. See `1966_balance_audit.md` for temporal
uncertainty, engine references and effect-identity checks. The tests validate
tool behavior; the normative balance parameters require their own audit.

## CI automation

GitHub Actions runs this validator on `push` and `pull_request` when the tool,
manifest, submod runtime, core cleanup guard files, or related docs change.

## Timeline override drift check

Some `TGC_Timeline_1966/` files are full-file overrides or carrier files. They
should behave like "current core plus the 1966 timeline hunk" when the submod is
enabled, so a later core-only fix can be hidden if the matching timeline override
is not refreshed.

When changing a core file that has a timeline override, run the default
core-to-submod read-only drift check from the repository root:

```bash
python TGC/tools/check_1966_submod_drift.py
```

This default mode compares changed core hunks against the timeline override and
warns when a core change is not present in the submod and does not look clearly
1966-specific.

When changing a timeline override directly, also run the reverse submod-to-core
check:

```bash
python TGC/tools/check_1966_submod_drift.py --reverse
```

Reverse mode compares changed submod hunks against core and warns when a submod
change looks like a generic bugfix, typo/encoding cleanup, UI fix, or other
non-timeline edit that is not present in `TGC/`. Non-timeline changes found only
in the submod must be ported to core or removed from the submod.

By default both directions compare changed hunks against `HEAD`, which is useful
while reviewing local edits. For already-committed branch work, pass the branch
base explicitly, for example:

```bash
python TGC/tools/check_1966_submod_drift.py --base-ref origin/main
python TGC/tools/check_1966_submod_drift.py --reverse --base-ref origin/main
```

`OK` means the watched override is currently coherent for the checked hunks,
`INFO` marks expected timeline differences or carrier files without a current
core counterpart, `WARN` marks possible drift that must be reviewed manually, and
`FAIL` marks missing override files, invalid roots, or an invalid base ref. The
drift check is conservative: it does not attempt to prove gameplay intent, and
WARN diagnostics should be inspected before deciding whether to port a hunk into
the timeline override, port it back to core, or remove it from the submod.

CI runs both drift directions automatically for `pull_request`, `push`, and
manual `workflow_dispatch` events. CI uses `--fail-on-warn`, so drift WARNs after
a core/submod sync block the workflow until the hunk is ported to the appropriate
counterpart, removed from the wrong side, or the checker/rules are intentionally
adapted. Local runs without `--fail-on-warn` keep WARN diagnostics non-blocking
for review.
