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
- all known-year deltas are applied cumulatively up to each milestone year (`year <= milestone`)
- unknown-year deltas stay out of milestone sums and are reported separately
- milestones remain configurable and reusable, but are no longer tied to a special 1936 logic branch
- tiered coverage/watchlists are used to keep the final report practical (core-first)
- v4 expands toward full per-unit stat coverage for all relevant stats detected in unit files
- current milestone grid spans the full campaign arc: `1836, 1850, 1870, 1900, 1910, 1919, 1929, 1936, 1945, 1955, 1966`

## Conceptual model (v4)

Per monitored unit stat, rules can define:

- `final_range`: plausible range for final estimated value
- `max_single_delta`: largest acceptable single effect delta
- `max_cumulative_positive_delta` / `max_cumulative_negative_delta`
- `milestone_ranges`: per-year guardrails at configured milestone years

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

Economic checks per unit can define:

- `estimated_build_cost_range`
- `estimated_upkeep_cost_range`
- `key_goods_expectations`

## Data extraction and dating

The auditor scans configured tech and invention files and reads unit stat deltas from effect blocks.

Year placement:

- `direct`: `year = XXXX` found directly in a block
- `inferred_strong`: inferred from one clear dated prerequisite
- `inferred_weak`: inferred from multiple/weaker propagated references

Coverage metrics:

- `time_coverage`: share of absolute delta with any known year
- `high_conf_coverage`: share of absolute delta with high-confidence dating (`direct + inferred_strong`)
- `signal assignments / touched_stats`: per-unit signal strength summary to separate high-value monitored units from baseline-only coverage

## Implemented checks

- Unknown monitored unit targets in rules (`FAIL`)
- Missing/unreadable monitored baseline stats in unit files (`FAIL`)
- Baseline stat outside configured `final_range` (`WARN`)
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
