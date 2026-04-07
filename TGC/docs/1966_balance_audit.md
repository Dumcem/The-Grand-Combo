# 1966 balance audit (diagnostic v4 - full stat coverage)

This tool is a **diagnostic balance auditor** for full gameplay progression across the configured tech/invention timeline.

- Script: `TGC/tools/audit_1966_balance.py`
- Rules: `TGC/tools/1966_balance_rules.json`
- Nature: **non-blocking** diagnostic (`exit 0`), intended for balancing iterations and playtest focus.

## Scope in v4

v4 covers the broad monitored unit roster and targets full relevant-stat coverage in `TGC/units/*.txt`.

Current monitored units (from rules):

- `aircraftcarrier`
- `artillery`
- `battleship`
- `cavalry`
- `clipper_transport`
- `commerce_raider`
- `cruiser`
- `cuirassier`
- `dragoon`
- `dreadnought`
- `engineer`
- `frigate`
- `guard`
- `hussar`
- `infantry`
- `ironclad`
- `irregular`
- `manowar`
- `monitor`
- `plane`
- `steam_transport`
- `submarine`
- `tank`

Coverage tiers (rules-driven):

- `core`: high-signal units with strong diagnostic value (primary balancing focus)
- `secondary`: useful but less central units
- `low_signal`: covered for completeness, currently with little timed-delta signal

Stat tiers (rules-driven):

- `primary`: balancing-critical combat/economic throughput stats (includes `maximum_speed`)
- `secondary`: useful tactical/support stats
- `structural`: unit-structure/support stats with often weaker delta signal

How tiers interact:

- unit tiers prioritize *where* to look (`core` units first)
- stat tiers prioritize *what* to look at (`primary` stats first)
- signal quality (`strong_signal` / `limited_signal` / `formal_coverage_only`) prioritizes *how trustworthy/actionable* the stat evidence is

## Unified v4 timeline model

The model uses a **single unified timeline**:

- `baseline_raw` is always the technical starting point (value read from unit file)
- `baseline_raw` is input evidence and is **not** checked against `final_range`
- all known-year deltas are applied cumulatively up to each milestone year (`year <= milestone`)
- unknown-year deltas stay out of milestone sums and are reported separately
- milestones remain configurable and reusable, but are no longer tied to a special 1936 logic branch
- tiered coverage/watchlists are used to keep the final report practical (core-first)
- v4 expands toward full per-unit stat coverage for all relevant stats detected in unit files
- current milestone grid spans the full campaign arc: `1836, 1850, 1870, 1900, 1910, 1919, 1929, 1936, 1945, 1955, 1966`

## Conceptual model (v4)

Per monitored unit stat, rules can define:

- `final_range`: normative envelope for the final estimated value (`estimated_final`)
- `max_single_delta`: largest acceptable single effect delta
- `max_cumulative_positive_delta` / `max_cumulative_negative_delta`
- `milestone_ranges`: per-year guardrails at configured milestone years

Per monitored unit, rules can also define:

- `historical_relevance_start_year`: first milestone year where historical milestone-range checks are meaningful for that unit

v4 distinguishes:

- **covered stat**: stat exists in the unit file and is present in that unit's `monitored_stats` rules
- **strong-signal stat**: covered stat with meaningful readable deltas/placement in scanned tech/invention data

A stat can be covered but still low-signal; this is expected in broad full-coverage mode.
When no readable deltas exist for a covered stat in scanned files, coverage is reported as formal-only (not as high-confidence timeline data).

## Evidence basis of milestone ranges (v4.1 refinement)

To avoid treating all ranges as equally strong, rules should be interpreted with two classes:

- **Evidence-based ranges**: stats with readable and reasonably dated deltas in scanned tech/invention files (especially core combat stats).
- **Heuristic scaffolding ranges**: stats with weak/no timed signal (common in structural stats) where ranges are intentionally diagnostic guardrails, not historical truth.

Practical guidance:

- pre-1936 milestones should **not** be auto-interpolated uniformly when observed progression is step-like;
- use anchor-style ranges around known jumps for core stats (`attack`, `defence`, `supply_consumption`, selected naval combat stats);
- keep structural low-signal stats (`build_time`, `default_organisation`, `max_strength`, `min_port_level`, etc.) broad/prudent to avoid false precision.

### Artillery stepped-envelope philosophy (v4.3)

Artillery is intentionally treated as a **step-escalation** profile rather than a smooth curve:

- **1836–1900**: conservative baseline band with modest improvement (`attack`/`defence`) and manageable supply growth.
- **1910–1939**: major modernization discontinuity (industrialized heavy guns, doctrine/logistics uplift).
- **1939–1956**: second major jump (self-propelled systems, heavy explosive/rocket/guided layers), especially visible in supply burden and late combat output.
- **1966 endpoint**: high late-era cap, but still bounded so warnings remain meaningful when progression overshoots expected late-step bands.

Because of this profile, artillery milestone envelopes are tuned as **piecewise stepped bands** instead of linear trend bands.
This keeps the audit diagnostic: it accepts historically plausible jumps but still flags implausible spikes or runaway cumulative growth.

#### Artillery `support` interpretation note

`support` is an abstract gameplay stat (not a direct historical metric), so ranges are calibrated by inference from doctrine/material progression:

- pre-1900: limited but real uplift from early industrial artillery integration; growth should stay modest.
- 1910–1939: larger jump is plausible due to indirect fire doctrine, coordination, and heavier field integration.
- 1939–1955: another jump is plausible (self-propelled artillery, improved fire direction, rocket artillery integration).
- post-1945: support can keep rising, but typically less explosively than wartime discontinuities; late gains should remain bounded so warnings still surface if support inflation becomes runaway.

In short, support envelopes should be **step-shaped and bounded**, not flat and not permissively linearized.

### Infantry / Guard / Engineer normative doctrine note (v4.4)

This trio should be interpreted as distinct but interacting archetypes:

- `infantry`: backbone, general-purpose line unit; reference envelope for sustained mass combat.
- `guard`: elite/heavier assault-capable line infantry; can exceed infantry combat output, but only within bounded doctrine-era limits.
- `engineer`: specialist support/fortification/siege/combat-engineering unit; may improve mobility/survivability/operational capability, but must not converge into quasi-standard offensive line infantry.

Normative implication: envelope design should be **step-shaped and bounded**, not mechanically linear from 1836 to 1966.

#### Infantry (backbone line unit)

- **1836–1900**: stable baseline doctrine; modest `attack`/`defence` growth, low-to-moderate `supply_consumption`, limited `support`/`siege`, and conservative mobility (`maximum_speed` mostly structural, not breakthrough-oriented).
- **1910–1939**: first major modernization step (industrial firepower, command/logistics improvements); meaningful uplift in `attack` and `defence`, with corresponding non-trivial supply burden.
- **1939–1955**: large wartime discontinuity; envelopes should tolerate stronger combat capability but avoid permissive post-step collapses in floors (especially for `attack`, `defence`, `supply_consumption`).
- **1955–1966**: consolidation and bounded late modernization; maintain high but capped line-combat profile, with no unlimited escalation.

#### Guard (elite/heavier line infantry)

- **1836–1900**: elite premium over infantry can exist, but should remain controlled (quality differential, not a separate super-unit class).
- **1910–1939**: doctrine/training/equipment premium can widen somewhat; `attack`/`defence` envelopes may sit above infantry, while `supply_consumption` should reflect heavier operational burden.
- **1939–1955**: strongest period for elite assault role; guard can exceed infantry in combat output, but bounded ceilings are required to prevent runaway divergence.
- **1955–1966**: late-era premium persists but should flatten; guard must remain superior in role focus without becoming unbounded relative to infantry baselines.

#### Engineer (specialist support/combat-engineering unit)

- **1836–1900**: specialist identity dominates; `attack` should stay secondary, while `defence`, `support`, and `siege` are the primary normative signals.
- **1910–1939**: operational relevance rises (fortifications, bridging, mobility support); `defence` and operational stats can step upward, with moderate mobility gains.
- **1939–1955**: major capability expansion in combat engineering; `support`/`siege` can rise sharply and `maximum_speed` can improve, but offensive `attack` must remain bounded as non-primary.
- **1955–1966**: mature specialist role; better survivability and operational throughput are plausible, yet envelopes must prevent drift toward quasi-infantry offensive parity.

Interpretation guardrails for warnings:

- warnings on guard vs infantry should be read as **relative-boundedness checks** (elite premium allowed, unlimited separation not allowed);
- warnings on engineer combat stats should be read as **role-integrity checks** (specialist evolution allowed, offensive convergence to standard line infantry not allowed);
- where historical jumps are expected, milestone floors/ceilings should move in discrete steps rather than smooth linear ramps.

## Historical applicability for milestone checks (v4.2)

Milestone diagnostics are most useful when evaluated only in years where the unit is historically meaningful/available.

Why this matters:

- late-era units (for example `tank`, `submarine`, `plane`, `aircraftcarrier`) can look "wrong" in early milestones simply because they are being compared before they are historically applicable;
- that creates noisy false warnings and reduces the signal quality of the audit output.

v4.2 behavior:

- if a milestone year is **before** a unit's `historical_relevance_start_year`, milestone-range pass/fail evaluation for that unit/stat/year is skipped;
- the script emits an `INFO` diagnostic showing which pre-applicability milestone years were skipped;
- `final_range`, economic checks, timeline coverage diagnostics, and non-blocking behavior remain unchanged.

Carrier-specific note:

- `aircraftcarrier` is now intentionally modeled as a two-stage pre-supercarrier arc:
  - **1919 early stage** via `converted_carriers` (`oil_driven_ships`): weak converted/interwar carrier entry point with activation.
  - **1929 maturation stage** via `fleet_aircraft_carriers` (`mobile_capital_ships`): main fleet-carrier maturation bump.
- the existing late layer remains on top (`welded_hulls`, then `supercarriers`, `advanced_supercarriers`, `monstrous_supercarriers`).
- milestone interpretation for carrier stats should therefore expect a low 1919 converted-carrier baseline, stronger 1929 fleet-carrier maturation, then 1939+ supercarrier escalation.

Late carrier calibration note (hull vs gun_power):

- `hull`: post-1945 growth is historically plausible to remain strong for carriers (size/aviation facilities/operational endurance), but should gradually flatten by late endpoint rather than rise endlessly.
- `gun_power`: this stat is an abstract combat proxy, not literal main-battery gunnery for carriers. Late increases can be partially justified as air-group lethality / integrated strike capability, but should generally be treated more cautiously than hull growth.
- therefore, carrier gun-power envelopes are calibrated with slightly tighter historical scrutiny around mid-century transitions, while hull envelopes allow clearer late-era expansion.

Interpretation rule:

- `milestone_ranges` are intended as historical guardrails only for years at or after `historical_relevance_start_year`.

Economic checks per unit can define:

- `estimated_build_cost_range`
- `estimated_upkeep_cost_range`
- `key_goods_expectations`

## Data extraction and dating

The auditor scans configured tech and invention files and reads unit stat deltas from effect blocks.

Year placement:

- `direct`: `year = XXXX` found directly in a block
- `inferred_strong`: inferred from clear dated prerequisites (especially hard `limit = { ... }` anchors tied to direct-year tech/invention gates)
- `inferred_weak`: inferred from multiple/weaker propagated references

Confidence refinement note:

- when an invention has multiple mixed references (for example chance modifiers, neighbor checks, war context), the auditor now prioritizes hard `limit` anchors for confidence classification;
- this improves attribution for clearly tech-anchored chains (such as late carrier progression) without globally relabeling all inferred years as strong-confidence.

Coverage metrics:

- `time_coverage`: share of absolute delta with any known year
- `high_conf_coverage`: share of absolute delta with high-confidence dating (`direct + inferred_strong`)
- `signal assignments / touched_stats`: per-unit signal strength summary to separate high-value monitored units from baseline-only coverage

## Implemented checks

- Unknown monitored unit targets in rules (`FAIL`)
- Missing/unreadable monitored baseline stats in unit files (`FAIL`)
- Single stat delta beyond `max_single_delta` (`WARN`)
- Cumulative positive/negative delta beyond configured caps (`WARN`)
- Estimated final (`baseline_raw + cumulative delta`) outside `final_range` (`WARN`)
- Milestone estimate outside per-year `milestone_ranges` (`WARN`)
- Build/upkeep estimate not calculable due to missing goods costs (`FAIL`)
- Build/upkeep estimates outside configured economic ranges (`WARN`)
- Key-good expectation mismatch (`WARN`)
- Timeline coverage / confidence coverage diagnostics (`INFO` / `WARN`)

## Example report lines (v4)

Unified stat summary example:

`tank attack: baseline_raw 16.000, first_known_year 1929, last_known_year 1966, cumulative +20.000, cumulative -0.000, milestones[1836:16.000, 1850:16.000, 1870:16.000, 1900:16.000, 1910:16.000, 1919:16.000, 1929:18.000, 1936:28.000, 1945:32.000, 1955:32.000, 1966:36.000], estimated_final 36.000, time_direct 2.000, time_inferred_strong 11.000, time_inferred_weak 7.000, time_unknown 0.000, time_coverage 100.0%, high_conf_coverage 65.0%`

Economic summary example:

`tank: economic upkeep_est=32.10; top3_upkeep=[barrels=16.66, fuel=7.50, artillery=5.20]`

## Running

From repo root:

```bash
python TGC/tools/audit_1966_balance.py
```

The command prints `FAIL/WARN/INFO`, a priority summary, and a playtest focus shortlist.

### Reading broad v4 coverage quality

When v4 covers many units, not all units have equal diagnostic signal:

- units with many assignments and several touched monitored stats are typically higher-value for balance monitoring
- units with `signal assignments=0` are still covered, but currently provide baseline/economic checks only and should be treated as low-priority diagnostic targets until more dated deltas are available in scanned files

## Tiered end-of-report watchlists

The final report now includes three short practical sections:

- `CORE WATCHLIST`
- `SECONDARY WATCHLIST`
- `LOW-SIGNAL COVERAGE`

Each line summarizes:

- unit
- tier
- signal assignments
- touched stats
- top warning (if any)

This hierarchy does **not** remove detailed diagnostics. It organizes them so core units drive action first, while low-signal units remain visible without dominating playtest focus unless they produce real `FAIL`s.

Rules naming note: unit group names are version-neutral in v4 (for example `legacy_baseline_units`, `all_monitored_units`).

## STAT COVERAGE SUMMARY (v4)

The report now includes a dedicated section:

- `STAT COVERAGE SUMMARY`

It prints:

- total covered stat entries
- total detected stat entries (from unit files, limited to monitored catalog)
- global detected vs covered stat types
- per-unit `covered_stats / detected_stats`
- explicit list of missing coverage when detected stats are not yet covered by rules

## STAT DIAGNOSTIC QUALITY (v4)

The report also includes:

- `STAT DIAGNOSTIC QUALITY`

Grouped by `primary` / `secondary` / `structural`, with per-stat:

- covered units
- assignment count
- units with signal
- quality label:
  - `strong_signal`
  - `limited_signal`
  - `formal_coverage_only`

This makes it explicit when a stat is fully covered in rules but still low-value diagnostically due to sparse/no readable deltas in scanned data.

Structural stats remain visible, but they are de-prioritized in top summaries unless they produce strong anomalies (or FAIL-level issues).

## TOP STAT WATCHLIST (v4)

The final report includes:

- `TOP STAT WATCHLIST`

This is a compact cross-unit stat-priority list ordered by diagnostic priority, combining:

- stat tier weight (`primary` > `secondary` > `structural`)
- signal quality weight (`strong_signal` > `limited_signal` > `formal_coverage_only`)
- unit tier context (issues on `core` units are boosted)

Each line includes:

- stat
- stat tier
- units with signal
- signal quality label
- score
- top issue example

## Current residual hotspots (post carrier-confidence fix)

Current practical WARN triage is:

1. Core land progression pressure (`engineer`, `guard`, `infantry`; mainly `attack` / `defence` / `supply_consumption` cumulative and late milestones).
2. Low-signal coverage-only units (`cavalry`, `cuirassier`, `dragoon`, `hussar`, `ironclad`, `monitor`) with no readable timed deltas.
3. Residual naval progression anomalies (`clipper_transport`/`frigate` speed milestones, `steam_transport` speed single-step jumps, `submarine` torpedo step size).

Recommended single next procedure target: **engineer progression audit/gameplay alignment** (highest concentration of core-stat pressure with strong practical playtest impact).
