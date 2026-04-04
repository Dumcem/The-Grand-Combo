# 1966 extension static validator

This repository includes a lightweight static validator for late-extension drift:

- Script: `TGC/tools/validate_1966_extension.py`
- Scope manifest: `TGC/tools/1966_extension_scope.json`
- Scope: targeted post-1936 / late-game allowlists for the 1966 extension

The validator reads its tracked scope from the manifest (tech/invention target keys + expected files, localisation files, structural checks, stale-key rules). This keeps scope maintenance separate from validator logic.

## What it checks

For each targeted key, the validator checks:

1. tech key exists in its expected `TGC/technologies/*_tech.txt` file,
2. tech key has localisation key,
3. tech key has `<key>_desc` localisation key,
4. invention key exists in its expected `TGC/inventions/NEW_*_inventions.txt` file,
5. invention key has localisation key,
6. invention key has `<key>_desc` localisation key.

Additional drift checks for the same targeted scope:

7. targeted tech keys are not defined more than once across technology files,
8. targeted invention keys are not defined more than once across invention files,
9. targeted localisation keys and `<key>_desc` keys are not duplicated across scanned localisation files,
10. targeted tech/invention keys are not defined in unexpected files outside their declared expected file,
11. known old-key fallout patterns are reported when legacy keys appear in selected late-extension files.
12. structural alignment checks verify:
   - `TGC/common/defines.lua` keeps `end_date = '1966.1.1'`,
   - `TGC/decisions/00_Setup.txt` keeps `option_end_game` aligned with `year = 1966` in both `potential` and `allow`,
   - `TGC/interface/backend.gui` keeps `text = "The World in 1966"`,
   - `README.md` keeps the canonical pointer to `TGC/docs/1966_extension_audit.md`,
   - stale legacy README snapshot claims (`navy ... 1939`, `industry 1945`, `culture 1950`) are not reintroduced,
   - `TGC/docs/1966_extension_audit.md` is present.

Localisation scan is intentionally limited to:

- `TGC/localisation/00_SUP_technology.csv`
- `TGC/localisation/00_other_tech.csv`

## Run

From repository root:

```bash
python TGC/tools/validate_1966_extension.py
```

The script exits with code `0` when all targeted checks pass, and `1` with a failure list otherwise.

## CI automation

GitHub Actions runs this validator automatically on `push` and `pull_request` when files relevant to the 1966 extension validator scope are changed (workflow, manifest, targeted tech/invention/localisation files, structural alignment files, or the validator/docs themselves).
