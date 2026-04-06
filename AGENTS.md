# AGENTS.md

## Mandatory validation before changes
From repository root, always run:

- `python TGC/tools/validate_1966_extension.py`
- `python TGC/tools/audit_1966_balance.py`

## If validation fails
Do not patch immediately.
First provide a diagnosis and classify the issue as:
- tool bug
- rules/doc issue
- gameplay/balance issue

## If validation passes
Proceed with the requested task.
Always report:
- validator result
- FAIL/WARN/INFO counts from the audit
- PRIORITY SUMMARY
- RECOMMENDED PLAYTEST FOCUS
