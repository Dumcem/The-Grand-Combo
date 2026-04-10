# AGENTS.md

## Validation trigger policy
Run validation from repository root only when the current task includes:

- changes to files covered by the 1966 extension ruleset/tooling, or
- analysis/review requests specifically about 1966 extension validity or balance.

In those cases, run:

- `python TGC/tools/validate_1966_extension.py`
- `python TGC/tools/audit_1966_balance.py`

If the task does **not** touch/assess 1966 extension validity or balance, skip these checks.

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
