# 1966 Extension Audit (updated: 2026-04-04)

## Current static status

- Campaign endpoint alignment is present and statically checked:
  - `TGC/common/defines.lua` keeps `end_date = '1966.1.1'`.
  - `TGC/decisions/00_Setup.txt` keeps `option_end_game` aligned to `year = 1966` in both `potential` and `allow`.
  - `TGC/interface/backend.gui` keeps `text = "The World in 1966"`.
- Late-extension content tracked by the validator is present in the expected scope:
  - late tech targets (post-1936 extension scope),
  - linked late inventions,
  - localisation coverage (`key` + `key_desc`) in the declared extension localisation files.
- Static hardening tooling is now in place:
  - validator script: `TGC/tools/validate_1966_extension.py`,
  - canonical manifest-driven scope: `TGC/tools/1966_extension_scope.json`,
  - CI automation: `.github/workflows/validate-1966-extension.yml` on relevant `push`/`pull_request` paths.
- Late-unit presentation remnants are clarified as maintenance placeholders:
  - heavy/mechanized UI button/sprite chains remain disabled/commented,
  - legacy localisation note is present to reduce maintenance confusion.

## What is now automatically enforced

- No missing/duplicate/unexpected-file drift for targeted late tech and invention keys.
- No missing/duplicate localisation drift for targeted late tech/invention `key` and `_desc` keys.
- No reintroduction of known stale README snapshot claims (`navy ... 1939`, `industry 1945`, `culture 1950`) in canonical status text.
- Required structural files/patterns for 1966 alignment remain in place, including presence of this audit file.

## Known limitations of static validation

Static validation does **not** certify gameplay quality or release balance. In particular, it cannot validate:

- AI research behavior and pacing in long campaigns,
- late-war combat feel/lethality/attrition quality,
- macroeconomic stability and market behavior through late decades,
- final balancing quality of late modifiers/costs under real campaign conditions.

## Final status judgment

- **Static hardening for the 1966 extension is complete** for the declared tracked scope (validator + manifest + CI + structural checks).
- **Release-readiness is not fully certified** by static checks alone.
- Remaining uncertainty is gameplay validation and post-test tuning only (if observed in campaign runs).
