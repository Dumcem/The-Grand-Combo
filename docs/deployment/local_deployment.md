# Local selective deployment

`tools/deploy/deploy_tgc.py` publishes selected runtime components from the
canonical Git working copy to a separately configured Victoria II installation.
Python 3.11+ and Git are required; no Python packages are required. Windows is
the production target. Never use the Steam installation as a working copy.

## Profiles and runtime policy

- `core`: `TGC` and `TGC.mod` only.
- `core+1966`: core plus `TGC_Timeline_1966` and its descriptor.
- `--optional ID` may be repeated for explicitly selected catalog entries.

The catalog lists nine optional root components and six niche components.
`TGCPastelMap` selects a root map skin. `TGCOrganizedStacks` reads its nested
source under `TGC Niche Submods` and installs the pair directly under `mod` as
its descriptor requires. The container is never copied. `TGCLowRam` is a cache
utility, not an installable mod-directory component, and is refused.

Only Git-tracked runtime files are published, using actual working-copy bytes,
including CRLF/LF and zero-byte overrides. `TGC/settings.txt` is included.
The catalog precisely excludes core docs/tools, `gfx/flags/flags.py`, timeline
docs and Belle/Pastel readmes. Other `.txt` files are not generally excluded.
New runtime top-level entries require catalog review. Even excluded source
trees are inspected for symlinks/junctions and refused if found.

Installing files does not activate them in a launcher. Enable core and Timeline
to play the extension. Updating `core` after `core+1966` preserves Timeline,
its ownership and its prior commit; disable it in the launcher for core-only
play. There is no implicit uninstall operation. Optional-mod compatibility
with Timeline or other options is not certified by the deployment tool.

## Target configuration and commands

The repository defaults to the tool's repository root, verified by Git and the
canonical origin URL. `--repo-root` supports explicit fixture/canonical roots.
`--game-root` is required; the tool does not autodetect or authorize Steam paths.
`config.example.json` illustrates configuration values and is not loaded.
Supply the path manually. No machine-specific configuration is committed.

PowerShell examples (substitute an explicitly chosen installation):

```powershell
$gameRoot = 'D:\Games\Victoria 2'
python -B tools/deploy/deploy_tgc.py plan --game-root "$gameRoot" --profile core
python -B tools/deploy/deploy_tgc.py plan --game-root "$gameRoot" --profile 'core+1966'
python -B tools/deploy/deploy_tgc.py plan --game-root "$gameRoot" --profile core --optional TGCOrganizedStacks
```

`plan` emits JSON to stdout and creates no state, backup, staging, probe, log or
installation file. It reports changes, ownership/adoption, preserved root
entries, old/new fingerprints and blockers. Exit 0 means prerequisites passed;
adoption may still be required. Exit 2 means diagnostic output with blockers
(including dirty Git). Exit 1 means an error, including untrusted metadata.

For a future real deployment, save a plan outside the repository and game:

```powershell
python -B tools/deploy/deploy_tgc.py plan --game-root "$gameRoot" --profile 'core+1966' |
    Set-Content -Encoding utf8 "$env:TEMP\tgc-plan.json"
python -B tools/deploy/deploy_tgc.py apply --game-root "$gameRoot" --plan-file "$env:TEMP\tgc-plan.json"
python -B tools/deploy/deploy_tgc.py verify --game-root "$gameRoot"
python -B tools/deploy/deploy_tgc.py rollback --game-root "$gameRoot" --transaction-id '<32-hex-ID>'
```

UTF-8 JSON with a BOM from Windows PowerShell 5.1 is accepted. A saved plan
contains fingerprints, not permission to bypass guards. Apply rebuilds the
complete plan and refuses changes in source bytes/HEAD/clean state, catalog,
live, state, target, selection or preserved root inventory. It repeats this
comparison under its own lock before staging.

## Clean Git and first adoption

Only a clean working tree can produce an applicable commit-attributable plan.
Dirty trees produce diagnostic plans explicitly blocked from apply. This allows
review while developing without misrepresenting an approved build. Review and
commit the tool before the eventual real applicable plan. The tool never
commits or fetches. A dirty-build mode is not implemented.

Known directory names do not establish ownership. Existing unowned selected
pairs are marked `adoption_required`; applying them requires deliberate adoption:

```powershell
python -B tools/deploy/deploy_tgc.py apply --game-root "$gameRoot" --plan-file "$env:TEMP\tgc-plan.json" --adopt-existing
```

This backs up complete previous selected pairs, including stale files, local
documentation, empty directories and old descriptors. It does not adopt
unselected components. Owned live drift blocks apply. Adoption intent is
recorded with the accepted plan; it cannot bypass corrupt existing state.

## Transaction, manifests and local state

Flow: preflight -> locked revalidation -> immutable transaction recording ->
staging verification -> backup -> per-unit replacement -> full verification ->
manifest/state recording -> corroborated completion receipts.

Production metadata defaults to
`%LOCALAPPDATA%\TGCDeployment\targets\<target-id>\`, with `state.json`, `plans`,
`manifests`, diagnostic journal mirrors in `transactions`, immutable `records`,
and `completed`, `rollback-authorized`, and `restored` receipts. `--state-root`
overrides the base for disposable simulations. Do not move, edit or discard
metadata while it owns a target. Transaction metadata schema 2 is required;
legacy journals without new records are refused and require intervention.
Catalog and plan schema versions remain unchanged.

Staging, backup, rollback staging, displaced payloads and the operational
journal live at `<game-root>\.tgc-deploy\transactions\<transaction-id>\`, outside
`mod` and on the same volume. Each transaction also has `record.json` and copies
of its receipts there. Record/receipt pairs must agree with the independent
local-state copies before use. Immutable means written once by the tool and
checked against the other copy; files are not OS write-protected or signed.

The record binds the full accepted plan, transaction/target IDs, game/state
roots, generation, profile and exact selected pairs, source identity, catalog
digest/policy, old/new snapshots, previous state and adoption intent. The plan
fingerprint and previous-state digest are checked again. Operational paths are
rebuilt from the configured target, validated transaction ID and catalog.
Catalog changes stop historical recovery until a matching catalog is restored
or reviewed; old mappings are not silently reinterpreted.

The journal repeats the record authority fields and digest, which must match.
Mutable fields describe intent, per-unit progress and diagnostic errors.
Statuses include `planned`, `staging`, `publishing`, `verifying`, `verified`,
`rolling-back`, `rolled-back`, and `recovery-required`. Status alone cannot prove
completion, confer ownership or authorize rollback. Corroborated completion
receipts bind the entire manifest digest to the record. Restored receipts mark
finished rollback/recovery; rollback-authorized receipts bind its mode.

`journal.status` is operational metadata, not terminal authority. A valid,
corroborated `rollback-authorized` receipt keeps the transaction pending until
a valid, concordant `restored` receipt exists. The earlier apply's `completed`
receipt does not cancel that rollback, even if only the journal status is
changed to `verified` or `rolled-back`. Pending classification reuses record,
journal, receipt-pair and completed-manifest validation; inconsistent metadata
fails closed. Terminal classification also requires the corresponding terminal
journal checkpoint; an interrupted checkpoint can be completed by retry.
New apply operations are blocked before creating a transaction or staging while
rollback/recovery is incomplete, including byte-identical payloads. Verify
refuses to report a consistent target while such a transaction is pending.

The manifest records schema/policy, repository, branch, full commit, clean
status, profile, mappings, per-file path/size/SHA-256, counts/bytes/content digest,
UTC timestamp, transaction, outcome, backup and prior state. Content digest
uses sorted path/size/hash data, not dates. With `core.autocrlf`, commit alone
does not identify deployed bytes.

Ownership is per component. Plan and verify reconstruct an ownership ledger
from validated records and completed, unrestored transactions ordered by
generation. Every state entry must exactly match it: component, transaction,
commit, mapping and snapshots. Completed journals and manifests are
corroborated, including target/schema, selection, full payload, counts and
hashes. Missing, corrupt, foreign or inconsistent metadata makes state
untrusted and requires recovery/intervention. Adoption cannot mask corruption.
A valid older manifest or identical live bytes cannot override a later owner.

Preserved optional components retain their prior identity or remain unowned.
Verify also checks actual paths, sizes, hashes, directory layout and absence
of extras; it reports commit, transaction and manifest payload digest per
component. A manifest can cover several components. Backups are retained
indefinitely; no automatic purge is provided. Rollback retains original backups
and displaced newer files.

## Rollback and interrupted publication

Multiple directory/descriptor replacements are not globally atomic. Publication
persists intent before each rename; recovery compares old/new/absent snapshots.
Every enumeration error aborts snapshot construction with path and cause. A
partial scan never produces an accepted snapshot. Automatic restoration is
attempted for staging/publication/verification errors.

The rollback command distinguishes two operations from corroborated receipts,
independently of journal status: normal rollback of a completed transaction,
and recovery of incomplete publication. Normal rollback initially requires its
exact verified live bytes and current ownership. Recovery permits only previous
ownership or the transaction's exact prospective state entry (the crash window
before completion). Neither can override a subsequent owner. All selected
units and unrelated ownership are checked before live mutations; previous
ownership is merged only for the recorded selection.

Rollback uses **backup -> rollback staging -> hash verification -> rename**.
Backups are never copied directly into live. All required old payloads are
prepared and verified before any live displacement. Each unit records
`not-started` (implicit), `preparing`, `ready`, `displacing`, `displaced`,
`publishing`, `published`, and `verified`. A corroborated rollback-authorized
receipt binds the operation mode before rollback begins. Intent is persisted
before moving live into deterministic transaction-local `displaced/<unit>` and
before publishing verified staging. Originally absent components are displaced
and left absent with the same progress tracking.

Retry inspects live, backup, staging and displaced snapshots for every unit and
can infer completed renames before their following checkpoint. A partial copy
is discarded only from derived rollback staging with a preparing checkpoint,
after link/scan checks. Verified old live is kept. Unexpected contents/phases
are refused before further live mutations. Interrupted rollback retains
recovery-required and blocks apply; initial refusal of an untouched completed
transaction leaves it completed. Correct the diagnosed obstruction and retry
rollback for that ID. Do not edit journals to suppress blockers.
If both restored receipts exist but the terminal journal update was interrupted,
`restored` is necessary but not sufficient for terminal success. Before updating
either journal copy, retry revalidates the immutable record and its concordant
copies, transaction/target/selection/mapping bindings, and the previous apply's
provenance. For a completed apply, both `completed` copies must agree with that
record and a valid manifest, including its schema, target, transaction, digest,
mapping and snapshots. Both `rollback-authorized` copies must agree and bind the
correct rollback/recovery mode; both `restored` copies must bind the same record
and agree with that authorization. An authorized rollback cannot become recovery
merely because its `completed` receipts disappear. Incomplete-apply recovery
does not require a completed-apply manifest.

Missing, corrupt or inconsistent required terminal evidence fails closed before
changing journals, state or live; retry does not repair that evidence. Correct
live bytes alone do not mean the transaction is formally concluded. Only after
all provenance checks, corroborated ownership/state validation and verification
of old live bytes does retry set the terminal journal to `rolled-back`, without
another live replacement. Inconsistent evidence remains detectable by `pending()`.

The target lock distinguishes the current call's unique token from another
owner. Pending transactions are enumerated even when a lock exists. Apply
rechecks under lock before staging and ignores only its own lock. Rollback also
refuses other pending transactions. `--recover-lock` removes a stale lock only
when its recorded PID is demonstrably absent and lock contents are unchanged.
Inspection failure and PID reuse are handled conservatively.

JSON writes use a unique same-directory temporary created exclusively, complete
writing, flush, file fsync, close, then os.replace. Preexisting temporary files
are not reused or cleaned up. Only the current call's temporary is cleaned up.
Directory fsync is attempted outside Windows; Windows has no portable
standard-library directory flush here. Individual replacements/renames do not
guarantee power-loss atomicity across multiple metadata files or hardware.
A crash leaving one record/receipt copy, missing initial journal, corrupt
metadata or unreadable backups stops automatic operations and requires manual
inspection. Authority is deliberately not inferred from one copy. Retain all
metadata/backups and report recovery evidence.

## Safety, UAC and limits

The tool validates canonical origin/root, installation markers, nonoverlapping
source/target/state, descriptor names/paths/dependencies, catalog selections,
Windows-invalid paths and case collisions. Source roots inside Legacy or a
steamapps ancestor are refused. Lexical ancestors and traversed entries are
checked for symlinks/junctions/reparse points; observed links are refused.
The same checks apply to backup reads and rollback staging. These are path-based
checks, not race-proof handle-relative filesystem operations. Source/HEAD/live
are checked again before publication and staging hashes are verified. Free
space is checked by a conservative estimate, not reserved with an OS quota.

Apply checks active game/launcher processes with Windows tasklist and selected
live files with exclusive DELETE-access handles. Process inspection failure is
refused. A unique temporary probe checks write/rename capability only in the
tool workspace and is removed before the transaction. Windows directory ACL
rights to add files/subdirectories and delete children are probed without
mutation. ACL changes can still cause failure. No ACL changes, automatic
elevation or forced read-only attribute clearing are performed. Use appropriate
permissions for Program Files; plan and verify need read access only.

Checks cannot prevent a noncooperating process modifying files after a check.
Locks, antivirus and filesystem errors may arise. Rollback recovers documented
checkpoint states or refuses ambiguous ones without further live mutations.
This is a cooperative local tool. It detects accidental corruption, inconsistent
metadata and single-authority-file manipulation. It does not defend against an
administrator coordinating changes to both copies, catalogs and receipts or
changing filesystem paths during an operation. Windows link/ACL/process checks
and durability are best-effort observations with TOCTOU/power-loss limits.

Only selected catalog directory/descriptor pairs are replaced. The tool does
not mirror/delete root mod, select ownership using TGC*, or modify CWE,
CWE.mod, dummy.txt, unselected mods, saves or user cache. Its probe, staging,
metadata and recovery data are the additional objects it creates. Plan has
none of these writes.

## Project Alice and validation boundary

Project Alice 1.3.0 remains the supported baseline. If Alice shares the same
installation/mod directory, deployment uses the same files. The tool does not
locate/install Alice, rebuild scenarios, activate mods or claim old scenarios
match updated files. Runtime compatibility and playtesting are separate steps.
This tooling changes no runtime data and does not assess 1966 validity/balance;
the 1966 validator and balance audit are not run for tooling-only changes.

## Simulated tests

```powershell
python -B -m unittest discover -s tools/deploy/tests -v
```

Tests use disposable repositories, game roots and state; they never deploy to
Steam. Process detection is simulated for filesystem tests; refusal is tested
separately. Symlink tests skip when creation privileges are unavailable.
Hardlink and exclusive-temporary tests cover JSON replacement. Negative tests
cover state/journal/manifest provenance, later ownership and cross-target
refusal. Failure injection covers partial rollback copies, ready staging,
displacement, publication/verification checkpoints, retries and absent units.
Enumeration errors cover source/live/backup/staging/verification. Lock tests
cover preflight/acquisition interleaving. `-B` avoids bytecode artifacts.
The R1 regression interrupts rollback after all old payloads are staged and
verified, before displacement, changes only `journal.status` to `verified`,
checks that pending/plan/apply/verify still block a successor without writes,
then retries rollback through corroborated `restored` receipts. Additional
cases cover `rolled-back` without restoration and discordant rollback receipts.
R2 regressions interrupt after both `restored` receipts but before the terminal
journal, then corrupt only the manifest digest, remove either `completed` copy,
or make either copy discordant. They also cover disappearance of both completion
copies and a concordant authorization with the wrong mode. Refused retries must
leave both journals, all game/live and state metadata, foreign/unselected
components and the transaction inventory unchanged, and remain pending. A valid
terminal retry completes both journals without replacing live or rewriting state.
Review and commit the tool separately before a real applicable plan and
explicit adoption of an installation.
