# 1966 balance auditor: sources, engine semantics and evidence

The auditor is a static diagnostic tool. Successful completion means its declared
structural analysis completed, **not** that the mod is balanced or compatible with
both engines. Numerical ranges and caps in `1966_balance_rules.json` remain
**UNVALIDATED**. They have not been fitted, widened or otherwise changed.

## Running

From repository root (Python 3.11+; standard library only):

```bash
python -B TGC/tools/validate_1966_extension.py
python -B TGC/tools/audit_1966_balance.py --summary
python -B TGC/tools/audit_1966_balance.py
python -B TGC/tools/audit_1966_balance.py --json
python -B -m unittest discover -s tools/tests -v
```

`--summary` keeps counts, grouped findings, catalog coverage and physical-source
signal without the detailed findings. `--json` writes structured diagnostics only
to stdout, including on input failure; it creates no report file. FAIL returns 1;
WARN/INFO return 0. Optional `--core-root` and `--timeline-root` select relative
repository directories with matching adjacent `.mod` descriptors. The tool does
not inspect the live installation, launcher, scenarios or saves.

## Architecture and source contract

- `lib_1966_parser.py`: strict decoding, structural tree, source positions,
  duplicate-preserving occurrences, strict configuration JSON.
- `lib_1966_runtime.py`: descriptor dependency and path checks, file overlay,
  replacement paths, scheduled technologies, effective unit identifiers.
- `lib_1966_semantics.py`: context-specific properties and engine evidence,
  caller contracts, raw-to-Alice additive projections.
- `lib_1966_diagnostics.py`: structured findings and cause grouping.
- `audit_1966_balance.py`: extraction, conditional dating, raw rule comparisons,
  projections and basket indices.

The default declared composition is `TGC + TGC_Timeline_1966`. Descriptor
`replace_path` entries remove lower-layer files in those paths; a later file at
the same runtime path replaces the earlier whole file. All effective inventions
are inventoried. Technology branch files are selected through the effective
`common/technology.txt` folders, as verified in Alice 1.3.0. Unreferenced files
are listed as excluded for that loader, with original-engine loading unverified.
Unit IDs are read from effective definitions, not inferred from filenames.
Ambiguous definitions, case-colliding paths, missing scheduled branches and an
unsupported dependency layout prevent analysis. No dictionary silently chooses
between duplicate effective unit IDs.

The legacy `scan_files`, `unit_file` and economic paths remain unchanged in the
rules JSON. They are not the source universe: effective paths are resolved from
the composition. No new file must be added to `scan_files` to be discovered.
Optional mods and any external vanilla fallback not excluded by descriptor are
explicit boundaries. Only the declared pair is composed; no current launcher
activation is inferred.

The complete effective technology/invention set supplies both extraction and
reference resolution. In particular, core `inventions/army_inventions.txt` remains
loaded; Timeline's `inventions/navy_inventions.txt` replaces the core counterpart.
A source in the repository is not, by itself, evidence of loading.

Common, event and decision files are inventoried as conditional/context sources.
National modifiers, technology metadata and production scopes are recorded outside
the additive unit-stat model, never added universally to every unit. Leader,
terrain, country-history, scripted grants, economic capacity and actual acquisition
paths remain excluded systems. The tool makes no claim of complete simulation.

## Raw values versus engine-applied values

Every extracted contribution retains unit, canonical statistic, raw spelling,
raw numeric token, value, owner, unit/global scope, file/line/column and temporal
evidence. Physical source occurrences and expanded global contributions are
reported separately. Neither count is a confidence score.

There are two distinct numerical views:

1. **RAW SCRIPT scenario**: baseline plus all relevant effective source deltas.
   Existing rule comparisons retain this meaning and are tagged `raw_script` /
   `unvalidated_rule`. They are neither shared-engine progression nor confirmed
   gameplay defects. The final sum is not promised acquisition by 1966.
2. **Alice 1.3.0 applied additive subset**: only properties supported in that
   context contribute, with verified integer parsing. Base fields ignored by Alice
   have no effective baseline/final. Unsupported or unverified contributions are
   excluded and counted. Milestone envelopes are computed on this subset too.
   Real arithmetic approximates engine float32; this is not a battle simulation.

Victoria II's script types, aliases and exact application remain **UNVERIFIED**
where independent evidence is absent. The program produces no invented V2 numeric
projection. The HoD manual supports the qualitative roles of recon, siege, naval
range/evasion/torpedoes and bases/supply; it does not establish the complete script
schema. Alice evidence must not be copied to V2.

### Pinned Alice evidence

- [Unit and modifier grammar](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parser_defs.txt).
- [Integer conversion](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/parsers.cpp).
- [Variable unit stats and addition](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/modifiers.hpp).
- [Technology/invention application and discovery](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/culture/culture.cpp).
- [Military consumers](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/military/military.cpp).
- [Supply demand](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/economy/economy.cpp).
- [Construction](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/economy/construction.cpp).
- [File overlay](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/filesystem/simple_fs_win.cpp).
- [Technology scheduling](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/cultures_parsing.cpp).
- [Directory loading](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/system_state.cpp).

`max_strength` and `limit_per_port` are discarded in Alice unit definitions;
`max_strength` is not an applied unit modifier. The schema distinguishes base
properties from technology/invention modifiers. `defense` canonicalizes to
`defence` for Alice/raw inventory only, while preserving the spelling and V2 gap.
Aliases cannot conceal duplicate properties in a single modifier group.
`build_time` and `default_organisation` are integer fields. Alice's parser consumes
the signed integer prefix without checking full token consumption: `2.5 -> 2`,
`0.5 -> 0`; `.5` and `+2` have no accepted integer prefix. Overflow and unverified
real-number syntax are reported without guessing application.

Free entries in definition/effect/modifier bodies, duplicate effect groups,
non-assignment effect/modifier operators, malformed known numeric values and
conflicting canonical properties stop structural analysis. Unsupported grouped
properties such as a modifier `supply_cost` are preserved as explicit limitations,
not converted into scalar effects and not declared invalid game data merely
because they are outside this auditor's verified contract. The reader remains a
structural subset, not the whole engine grammar. Required Lua/GUI patterns in the
validator remain targeted checks, not full parsers for those languages.

## Dating and uncertainty

A technology's direct year is a reference research-scenario anchor, not an actual
country acquisition date or a universal hard gate. Positive recognized invention
prerequisites in `limit` provide conditional lower bounds, never exact discovery
dates. AND takes the maximum necessary known bound; OR needs all branch bounds
and takes their minimum. Negated/unsupported conditions remain uncertainty notes.
Synchronous updates resolve forward references deterministically; unanchored
cycles remain unknown. Probability years are recorded separately from eligibility.

At a milestone, eligible uncertain positive effects contribute to the upper
endpoint, negative effects to the lower endpoint. Correlations are relaxed. These
are possibility envelopes under the declared model, not statistical intervals.
A whole envelope outside a configured band produces a raw-rule WARN; partial
overlap produces an evidence-gap INFO, explicitly **not PASS**. Indeterminate
findings remain visible in grouped summaries. The global grid and unit-specific
applicability are retained; they do not establish construction availability,
obsolescence dates, sustainable production or sufficient time before `1966.1.1`.

## Economy

`build_basket_base_price_index` and `supply_basket_base_price_index` are sums of
commodity amount times configured base price. Existing economic bands compare
only these legacy indices, explicitly unvalidated. The key-goods check means at
least one listed good is present; production mapping means a recipe exists.
Neither proves economic availability or adequate quantities.

A separate Alice conditional supply index multiplies the supply basket index by
the applied supply-consumption baseline or all-effects multiplier. Assumptions:
base prices, national supply modifier zero, full strength and unit demand only.
Actual demand also depends on country modifiers (including the engine floor),
land strength, prices, availability, budget and operating conditions. The new
quantity is **never** compared with old economic bands. It is not runtime spending.

## Evidence dimensions and diagnostics

Keep these separate: source completeness within the declared composition, catalog
presence, engine support, structural extraction, temporal availability,
indeterminacy and normative validity. There is no aggregate confidence score.
The retained coverage thresholds 60/80, confidence thresholds 80/50/70 and priority
weights are inactive as quality criteria; no replacement balancing thresholds were
invented. Research-anchor share is descriptive only. An empty delta denominator
provides no confidence evidence.

Every finding has severity, code, category, optional unit/stat/source, engine,
evidence type, uncertainty and a cause identifier. Categories are integrity,
source scope, engine semantics, evidence gaps, numerical rule findings, economic
indices and observations. A nonzero FAIL prevents successful completion; WARN is
not automatically a gameplay bug. JSON preserves this information for consumers.

`PRIORITY SUMMARY` orders technical/evidence categories before possible numerical
anomalies and groups common causes. It does not use prose matching or unvalidated
priority weights. `RECOMMENDED PLAYTEST FOCUS` is informational only, grouped by
unit/stat to avoid repeated milestone/final/delta entries for one underlying
progression. It is neither an instruction to playtest nor a correctness criterion.

## Independent regression evidence and limitations

The original 39 tests remain relevant to their legacy five-file extraction corpus.
New tests select effective files and unit identifiers independently of the rules,
using a separate token/stack inventory and controlled overlay fixtures. They
compare individual identities, including the retained core army inventions:
389 physical assignments / 969 expanded contributions at the audited checkpoint.
The expanded corpus has 3,636 relevant contributions. These are observations in
tests, never program constants or normative targets.

The previous perimeter had 12 fractional organisation origins / 134 contributions.
Including the core army file exposes another 10 origins / 110 contributions.
Tests cover the original and expanded sets, engine statuses/types, aliases,
negative caller cases, explicit limitations, diagnostic categories/grouping,
conditional economy output and cross-process determinism. Fixture directories are
created under the test directory and automatically removed.

The independent inventory still shares the documented Clausewitz subset and some
scope assumptions. Hand-authored engine fixtures and pinned sources provide a
separate line of evidence; no test suite certifies the closed-source V2 executable,
actual gameplay balance or the 2,985 final/milestone intervals.
