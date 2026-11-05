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
- `lib_1966_mechanics.py`: conditional consumers, numerical domains and
  activation/infrastructure scenarios independent of the legacy numeric bands.
- `lib_1966_functional.py`: necessary research dependencies, bounded Alice naval
  AI selection scenarios and campaign-horizon diagnostics.
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

Common TXT/Lua, event and decision files are inventoried as conditional/context sources.
The effective `common/defines.lua` is selected through the same layer overlay;
only its quoted end_date is read by the targeted horizon diagnostic, not a Lua interpreter.
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
Numeric occurrences are retained in physical source order. Alice's generated
member parser assigns the last occurrence to its internal field in each body;
distinct bodies then accumulate. This includes exact repeats, `defense/defence`
and the shared pairs `attack/gun_power`, `defence/hull`,
`reconnaissance/fire_range`, `discipline/evasion`, `siege/torpedo_attack`.
The unit domain determines the display name, not a different storage field.
For example `defence = 1 hull = 4` on a tank contributes 4, not 5.
The raw diagnostic inventory still retains both occurrences. Engine projection
JSON `data` retains the selected, superseded and excluded origins separately,
including physical block identifiers; a numeric total alone is not its oracle.
V2 precedence and shared storage remain unverified.
`build_time` and `default_organisation` are integer fields. Alice's parser consumes
the signed integer prefix without checking full token consumption: `2.5 -> 2`,
`0.5 -> 0`; `.5` and `+2` have no accepted integer prefix. Overflow and unverified
real-number syntax are reported without guessing application.

Free entries in definition/effect/modifier bodies, duplicate effect groups,
non-assignment effect/modifier operators and malformed known numeric values
stop structural analysis. Repeated nonnumeric base properties remain outside
the verified contract. Unsupported grouped
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
The Task 24 expanded corpus had 3,636 relevant contributions. These are observations in
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

## Applied consumers and technical invariants

Alice projection now folds shared fields independently of the normative unit/stat
filters. Base assignment order and each physical modifier body are preserved;
distinct bodies accumulate after their members have been assigned. JSON `data`
exposes baseline origins, selected contributions, overwritten occurrences and
unsupported/unverified exclusions. No V2 numeric projection is inferred.

`consumer_factors` reports baseline and all-effects scenarios, holding external
battle conditions equal. Land factors are `1 + attack/10` and
`1 + defence/10`; rear factors multiply by support only for the normal
support/special deployment path. Tank is special, plane is cavalry. Eligibility
does not predict actual deployment. Maneuver target steps use integer conversion.
Infantry/guard ratios exclude discipline, organisation, costs and recruitment.
Naval factors keep small-target gun power, big-target gun power plus torpedoes,
`hull/(1-evasion)`, range and speed separate. Range above 2 covers the initial
two-center-distance separation; it is not a proportional battle advantage.
Sources: Alice v1.3.0 `military.cpp` 4891-4928, 6634-6717, 7405-7454,
7625-7718, 8115-8155 and `military.hpp` 45-47.

Technical checks are separate from numeric bands: positive time/organisation/
hull/land-discipline divisors, nonnegative ordinary consumer inputs, integer base
port/colonial/supply-score properties, and evasion in [0,1]. Evasion exactly 1 is
flagged as an immunity design question. A bad direct baseline is FAIL; a relaxed
combination envelope crossing a domain boundary is WARN with
`basis=conditional_model`, NOT a proved reachable defect. Correlations, discovery,
activation and national modifiers must still be checked. Unsupported or partial
projections do not produce a technical PASS.

Activation diagnostics preserve positive necessary references (AND union, OR
intersection, NOT excluded), research anchors, invention bounds/probability-year
notes, culture/overseas restrictions and commodity baskets. Technology predecessor
references follow source order within each area of the declared scheduled tree.
Country histories, scripted grants, discovery probabilities, actual construction,
industry and national ownership remain explicit boundaries.

Port progression includes BOTH `max_naval_base = 1` and
`activate_building = naval_base`: Alice sets one increase-building boolean per
technology/invention, not one increment per spelling. In the current Timeline,
`post_nelsonian_thought` contributes the previously omitted initial increment.
The research scenario has eight flags: port 7 references 1929, port 8 references
1939. Carrier activation has reference bound 1919; research/building completion
are additional requirements. This corrects the Task 25 seven-flag/1939-port-7
interpretation. No runtime content was changed to achieve that correction.
Sources: `parsers_declarations.cpp` technology_contents/invention_contents
activate_building/any_value; `culture.cpp` clear_existing_tech_effects and tech/
invention application; `commands.cpp` can_start_research/naval_unit_construction.

## Legacy normative contract

All 283 final bands, 2,702 milestone bands and associated caps remain unchanged
and UNVALIDATED. Raw comparisons retain their codes, severities and provenance
for historical comparison; text is explicitly prefixed `LEGACY UNVALIDATED` and
JSON adds `basis=legacy_unvalidated`. This does not promote a warning to a
gameplay defect. New categories `technical_invariant`, `availability`,
`mechanics` and `design_question` distinguish contracts, conditional scenarios
and choices still open. The 23-unit role taxonomy remains a design proposal.

The independent applied-field oracle in `tools/tests/test_1966_applied.py` uses a
separate recursive token reader and literal storage schema, selects the effective
files without the rules, and compares every winning contribution's source and
value, not just the six Task 25 totals. Synthetic fixtures test repeated members,
distinct blocks, base/modifier contexts, discrete domains and consumer sensitivity.

## Necessary research dependencies and supply diagnostics

`consumer_domain` retains its relaxed envelope and selected applied contributions.
For supply consumption, a second model groups contributions by owning technology
or invention: an owner is acquired as a whole, including positive and negative
modifier bodies. It enumerates subsets of negative-net owners and closes them
under necessary positive references and technology predecessors in source order
within each area. Forced positive effects are included; unselected positive owners
can be omitted because they cannot lower the bound. Necessary NOT constraints
reject contradictory closures. AND unions necessary atoms; OR intersects them;
negation uses De Morgan. Alice's NOT has implicit OR children before inversion
(all direct children must be false), as checked in
[trigger_parsing.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/parsing/trigger_parsing.cpp),
`tr_scope_not`, `invert_trigger_internal` and `simplify_trigger`. Country scopes and unknown predicates supply no assumed
truth. Explicit `invention = X` retains its namespace.

This is a conservative lower bound for **normal prefix research**, not a full
acquisition simulator. Unknown predicates, OR alternatives, cycles and chance can
make admitted combinations impossible; ordinary acquisition remains a subset of
the relaxed model. Histories, scripted/console grants, copied technologies and
arbitrary saves may bypass the model and remain unverified. Activation restrictions
are also relaxed. At most 16 negative owners (65,536 subsets) are enumerated;
missing owners, partial projections or the enumeration limit return unverified,
never a technical PASS. The cap is a computational limit, not a balance threshold.

The eleven real land supply cases retain their original negative relaxed endpoints.
The prerequisite model and a separate literal-tree oracle both derive a positive
minimum equal to the current base supply, 0.15, without using 0.15 as a rule or
constant in the implementation. Their consumer findings become INFO with
`classification=relaxed_violation_excluded_by_prerequisites`, retaining both views
and per-negative-owner forced-positive provenance. Other warnings are not removed
by this analysis. Negative prerequisite bounds remain WARN; direct invalid bases
remain FAIL.

A strict sufficient witness checker can mark `reachable_in_static_research_model`
for acyclic chains, completely evaluated reference conditions and positive constant
invention chances without modifiers. This is not runtime reachability, a dated
national path or an operational unit. Unknown country/temporal conditions, cycles,
fractional chance below one and conditional chance modifiers cannot create this
witness. Negative fixtures verify that actual invalid paths in that restricted
model remain visible. Findings outside its contract stay reachability-unverified.

## Alice naval AI selection diagnostics

Pinned evidence, rechecked at v1.3.0:

- [ai.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/ai/ai.cpp),
  `build_ships`, `update_ships`, `will_upgrade_ships`.
- [military.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/military/military.cpp),
  `get_best_*`, `is_*_better`, `upgrade_ship`.
- [military.hpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/military/military.hpp),
  default arguments: primary_culture=false, evaluate_shortages=true.
- [commands.cpp](https://github.com/schombert/Project-Alice/blob/v1.3.0/src/gamestate/commands.cpp),
  `can_start_naval_unit_construction` and `can_start_research`.

`naval_ai_selection` reports explicit all-unlocked stress scenarios for domestic
ports at the roster's requirement levels. It separates unlock, local port/overseas
eligibility, possible new-build choices, penalties from the verified criterion,
refit choices and actual execution (unverified). No discovery date or nation is
inferred. No shortages are assumed in these scenarios; supplied known shortages
can separately exclude refit candidates. Actual construction also needs ownership,
control, disarmament checks, goods, capacity, budget and available queues.

New construction chooses one unit per transport/light_ship/big_ship category by
**base hull**, then checks ports. There is no runner-up fallback when the selected
unit cannot use the available ports. Equal hull candidates remain a set here:
engine unit-ID ordering is outside the repository-order contract. Carrier hull 65
loses to battleship 70 and dreadnought 80 even at port 7. This is a conditional
selection result, not a claim that no nation ever builds carriers.

Refit uses speed/hull/gun for transports, speed/gun/hull for light ships and
gun/hull/torpedo for big ships. It uses applied national stats only when the
candidate's applied evasion is positive; otherwise it uses the base stats. Default
get_best calls exclude primary-culture-only and shortage candidates. Refit and
construction can therefore prefer different classes. The refit call does not
apply the construction port gate. `upgrade_ship` replaces the type and sets
strength to 0.01; recovery consumes repair resources. The AI's peace, battle,
AI-control, transport-use and damage-fraction checks are not simulated by this
static ranking, nor are fleet composition budgets or repeated replacement cycles.

Possible workarounds remain design questions: tuning hull/gun changes combat and
can conflict between the two selection paths; adding another big_ship cannot
create an independent carrier allocation; scripted grants require independently
verified engine effects and may bypass industrial construction. None is applied.
V2 AI behavior is not inferred from these Alice functions.

## Effective campaign horizon

`campaign_horizon` reads the effective end_date (currently 1966.1.1), lists every
effective technology/invention and distinguishes `reference_before_end`,
`no_ordinary_use_window`, and `unverified`. `horizon_no_use_window` warns for a
necessary research/eligibility reference at or beyond the boundary. Necessary
predecessors can delay a technology beyond its own nominal year. Positive
invention references and literal eligibility years contribute; probability-only
years do not become gates. Missing dates remain unverified.

Alice's ordinary research command requires the technology year and its preceding
folder technology, as well as civilization and other command conditions. An
invention additionally requires discovery, not just its limiting technology.
A reference before the end is therefore not proof of research completion,
discovery or useful operational time. An anchor on 1966.1.1 offers no ordinary
research-and-use interval **before** that boundary, irrespective of end-day
inclusion or continuation controls. This diagnostic does not execute the end-game
decisions, simulate dates, rule out historical/scripted grants, or change any
technology, decision or campaign date. V2 numeric/temporal implementation remains
separate and unverified here.

## Provisional transport production curve

Both transports retain base time 90. Task 26 corrected the old nonpositive-time
path: six engineering cuts and two schools of -10, followed by -10 in 1919,
previously reached zero in core and -20 with Timeline's later cuts. Its bounded
-9 correction yielded one day. That was an integer positivity fix, not a balance
validation. The historical arithmetic remains tested.

Task 29 adopts the explicitly authorized provisional design: each of the six
early engineering technologies, modern_naval_design and both naval schools gives
transports a scoped -5. Timeline additionally gives -5 at
mechanized_naval_production and automated_naval_design. Other naval units retain
exactly -10 per applicable owner. Global time cuts are expanded intentionally to
the effective ten-unit core or twelve-unit Timeline roster, without compensation
modifiers or new unit IDs. Future naval classes need an intentional scoped-time
review when added.

| Research reference | Task 26 core/Timeline | New core | New Timeline |
|---|---:|---:|---:|
| Base, no effects | 90 | 90 | 90 |
| 1836 engineering, no schools | 70 | 80 | 80 |
| 1850 engineering, no schools | 60 | 75 | 75 |
| 1870 engineering, no schools | 50 | 70 | 70 |
| 1875, both schools | 30 | 60 | 60 |
| 1900, both schools | 20 | 55 | 55 |
| 1915, both schools | 10 | 50 | 50 |
| 1919, both schools | 1 | 45 | 45 |
| 1929, both schools | 1 | 45 | 40 |
| 1939 onward, both schools | 1 | 45 | 35 |

School discovery dates are not guaranteed. With zero/one/two schools, add 10/5/0
to the new post-1875 rows. All cuts are nonpositive: the full set is a lower bound
for every subset, reachable or otherwise. Independent tests enumerate transport
subsets, compare epochs and check every non-transport cut in both compositions.

At fixed normalized cost, one completed transport per 35/45 nominal days replaces
the former one per day per active provincial queue; goods and budget can still
slow construction. The full daily basket demand is spread over 35/45 instead of
one nominal day. Total construction baskets, transport capacity, supply and combat
stats are unchanged. These endpoints are a provisional production design, not
historically calibrated durations or a runtime balance verdict.

The scripts use ordinary scoped unit build_time modifiers, with no Alice-only
runtime path. Alice parser/application/consumer are covered statically. Exact V2
application, local shipbuilding modifiers, end-to-end construction, economic and
AI outcomes remain unverified. No deployment or scenario generation was performed
for Task 29; the Task 27 live/scenario remains on the earlier source state and
cannot certify these new bytes. A future runtime check must use the controlled
deployment lifecycle and a scenario generated from that verified deployment.

The generic positivity correction and generic tooling improvements remain
possible upstream contributions. This new production curve is an explicit fork
design choice; acceptance upstream is not assumed. No sync or push is involved.
