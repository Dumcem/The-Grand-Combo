# 1966 Extension Audit (updated: 2026-04-04)

## Current static status

- Campaign endpoint alignment is present and statically checked:
  - `TGC/common/defines.lua` keeps `end_date = '1966.1.1'`.
  - `TGC/decisions/00_Setup.txt` keeps `option_end_game` aligned to `year = 1966` in both `potential` and `allow`.
  - `TGC/interface/backend.gui` keeps `text = "The World in 1966"`.
- Late-extension tech scope is now closed through 1966 across all five branches in the tracked validator scope (army/commerce/culture/industry/navy).
- Linked late inventions for the tracked scope are present and localized (`key` + `key_desc`) in the declared extension localisation files.
- Carrier animation naming has been normalized in interface references for the extension ship actor chain.
- Theocracy extension event key `800041` now has explicit event localisation entries.
- Static hardening tooling remains in place:
  - validator script: `TGC/tools/validate_1966_extension.py`,
  - canonical manifest-driven scope: `TGC/tools/1966_extension_scope.json`,
  - CI automation: `.github/workflows/validate-1966-extension.yml`.

## What is now automatically enforced

- No missing/duplicate/unexpected-file drift for targeted late tech and invention keys.
- No missing/duplicate localisation drift for targeted late tech/invention `key` and `_desc` keys.
- Structural 1966 alignment remains enforced (defines/decision/backend/readme/audit presence).

## Known limitations of static validation

Static validation does **not** certify gameplay quality or release balance. It validates structural coherence only for the declared tracked scope.

## Final status judgment

- **Static completion for the declared 1966 extension scope is complete.**
- Remaining work outside static scope is optional balancing iteration, not missing structural integration.
