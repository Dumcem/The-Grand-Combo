# AGENTS.md

## Project Alice compatibility policy

- Project Alice is an officially supported runtime target alongside the original Victoria II engine (`v2game.exe`). Changes must not knowingly break either supported engine unless an explicit project decision changes this policy.
- The Project Alice compatibility baseline is the latest stable version that has been explicitly audited and adopted by the project. The current baseline is Project Alice 1.3.0. A newer Project Alice release does not automatically replace the baseline: review relevant changes and compatibility before adopting it.
- When implementing or reviewing changes to scripts, triggers/effects, defines, technologies, inventions, units, buildings, economy, AI, GUI/GFX, mod loading, or other engine-facing data, explicitly consider behavior under both Victoria II and the supported Project Alice baseline.
- Prefer constructs that behave correctly under both engines. When the engines require different behavior, use an intentional engine-specific path where possible, such as `has_global_flag = project_alice` or Alice-specific configuration, rather than degrading one engine silently.
- A construct being accepted by the Project Alice parser is not sufficient evidence of compatibility. Check whether relevant fields and mechanics are actually implemented and used by Alice; recognized-but-discarded fields must not be relied upon for gameplay behavior under Alice.
- When Project Alice does not implement a Victoria II mechanic used by the mod, either provide an Alice-compatible equivalent when practical or explicitly document the remaining behavioral divergence. Do not silently treat ignored behavior as equivalent.
- Compatibility means that the mod remains valid and functionally coherent on both supported engines. It does not require identical simulation results where Project Alice intentionally implements systems differently from Victoria II.
- Changes affecting engine compatibility must include the applicable Project Alice static/scenario validation when such validation is available. Compatibility regressions are treated as implementation regressions, not optional follow-up work.
- After upstream TGC synchronization, consider Project Alice compatibility as part of the mandatory regression review together with core/1966 synchronization.
- If preserving both engines would require a substantive gameplay or design compromise, do not choose one silently: report the conflict and obtain a project decision before proceeding.

## External engine research references

- When an investigation depends on Victoria II engine behavior, Project Alice compatibility, or other opaque mechanics, consider relevant public technical research when it can materially improve accuracy or avoid duplicating work. This may include reverse-engineering studies, engine-extension or patch projects, diagnostic tooling, and reproducible experiments.
- Initial non-exhaustive references are [Victoria2-Reverse-Engineering](https://github.com/maxioten/Victoria2-Reverse-Engineering) and [CreatineCore / V2DLL](https://github.com/artyom-kuznetsov/V2DLL_Victoria-2-Extension). Discover and assess other relevant projects as they appear; inclusion here is not an endorsement or a permanent assertion of validity.
- Before relying on external findings, check their provenance, evidence quality, applicable executable/version and patch state, maintenance and reproducibility. Separate observations of original `v2game.exe` from modified engines, third-party patches, Project Alice behavior, inference, and unresolved hypotheses. Revalidate material conclusions for the supported runtime targets as appropriate.
- Consultation does not authorize installing or incorporating external binaries, DLLs, patches, or code. Respect applicable licenses and legal constraints; keep proprietary game binaries out of the repository. Record consequential findings, citations, uncertainties, and applicability in the relevant technical documentation.

## Local deployment policy

- The Git working copy is the authoritative edit surface. Do not develop or maintain managed TGC components by editing the live Victoria II installation directly.
- Deploy managed components from the repository to the live Victoria II installation with `tools/deploy/deploy_tgc.py`, following `docs/deployment/local_deployment.md`. Do not replace this workflow with manual copy, synchronization, or ad-hoc file deletion.
- Use the normal deployment lifecycle `plan → apply → verify`. Review the plan before applying it, and treat a failed or recovery-required transaction according to the deployment tool's documented recovery procedure rather than repairing its state manually.
- When source changes must be exercised or validated in a runtime, deploy the intended repository state through the deployment tool first so the live installation corresponds to the source under review.
- When Project Alice scenario validation is required after relevant deployed changes, generate or regenerate the Alice scenario from that verified live deployment rather than relying on a scenario built from an older live state.

## Re-baseline verification policy — temporary

- The upstream synchronization checkpoint is closed. The general technical and balance re-baseline continues. Use `docs/upstream_reconciliation.md` for the handoff and `docs/rebaseline_backlog.md` for residual work.
- Treat existing fork changes, prior fixes, audit conclusions, validation results, documentation claims, and legacy AI-generated work as evidence to be re-evaluated, not as proof of correctness.
- During the re-baseline, validate the implementation from first principles where practical. Do not preserve a previous conclusion solely because it is already implemented, documented, tested, or reported as passing.
- Audit the audit tooling itself. Review validator and audit code, parsing assumptions, rulesets, coverage, thresholds, reference values, balance targets, and other parameters used to decide whether content is valid or plausible.
- A validator passing is meaningful only after the relevant validator logic and its reference assumptions have themselves been reviewed to an appropriate level of confidence.
- Reassess historical fixes individually. Confirm the underlying defect, the correctness and completeness of the fix, cross-file consequences, and compatibility with both supported runtime targets before treating the fix as trusted baseline.
- Use current project capabilities and evidence to improve or replace earlier methods where they are incomplete, weakly justified, or obsolete. The purpose of the re-baseline is to reconstruct confidence from the foundations rather than inherit it.
- This policy is scoped to the current re-baseline phase. When the re-baseline is formally completed, review this section as part of the closing checkpoint: remove phase-specific instructions and retain or reformulate only principles that remain useful for normal ongoing development.

## Upstream-first synchronization policy

- Use the original TGC as the reference implementation and adopt upstream updates by default.
- Keep fork differences only as intentional, justified fixes, improvements, extensions, compatibility adaptations, or approved customizations. A gameplay change or an existing fork difference alone does not justify excluding upstream behavior.
- Resolve conflicts from the upstream implementation and reapply justified fork changes. Preserve verified fork fixes and upstream improvements, including in files Git combines automatically.
- Trace intentional differences from upstream commit and behavior through the fork change, its rationale, and its verification. Demonstrate actual incompatibilities and address them where practical.
- Preserve Victoria II and the supported Project Alice baseline unless an explicit project decision changes that policy.
- Record synchronization outcomes and exceptions in `docs/upstream_reconciliation.md`.

## Upstream contribution policy

- Confirmed bugs should be fixed and validated in this fork without waiting for acceptance by the original/upstream TGC project.
- When a confirmed fix is generic to TGC rather than specific to this fork, retain the validated fix locally and separately mark it as a candidate upstream contribution.
- Previously implemented generic fixes must be re-evaluated during the re-baseline before being proposed upstream; prior implementation alone is not evidence that the fix is correct.
- Prepare upstream contributions as minimal, clean patches separated from fork-specific customization whenever practical.
- Upstream review or acceptance must not block continued use of a validated fix in this fork. If upstream later implements the same fix independently, compare the implementations deliberately rather than merging or duplicating them blindly.

## Instruction lifecycle policy

- Keep persistent agent instructions limited to rules that still affect future work. Phase-specific policies must be clearly identifiable and reviewed when their phase closes; remove obsolete instructions instead of allowing AGENTS.md to accumulate historical workflow.

## Validation trigger policy
Run validation from repository root only when the current task includes:

- changes to files covered by the 1966 extension ruleset/tooling, or
- analysis/review requests specifically about 1966 extension validity or balance.

In those cases, run:

- `python TGC/tools/validate_1966_extension.py`
- `python TGC/tools/audit_1966_balance.py`

If the task does **not** touch/assess 1966 extension validity or balance, skip these checks.

## TGC core / 1966 timeline submod synchronization
- `TGC/` is the non-1966 core mod; `TGC_Timeline_1966/` is the 1966 runtime submod.
- Some timeline files are full override/carrier files and can mask core fixes. Generic fixes made in the submod should not remain submod-only unless there is a clear reason.
- When changing a core `TGC/` file that may have a timeline override/carrier, run or explicitly consider `python TGC/tools/check_1966_submod_drift.py`; decide whether to port the change into the submod while preserving 1966 timeline hunks, or explain why not.
- When changing a `TGC_Timeline_1966/` file that is not clearly timeline-only, run or explicitly consider `python TGC/tools/check_1966_submod_drift.py --reverse`; decide whether to port the generic part back to core without bringing 1966 content into `TGC/`, or explain why not.
- Never transfer changes between core and submod automatically: porting must be intentional, drift WARN entries require manual review, and drift FAIL entries must be fixed before proceeding.
- After syncing from the original/upstream mod, treat core/submod drift verification as mandatory. If possible, use the pre-sync commit as `<pre-sync-ref>` and run or explicitly consider `python TGC/tools/check_1966_submod_drift.py --base-ref <pre-sync-ref>` and `python TGC/tools/check_1966_submod_drift.py --reverse --base-ref <pre-sync-ref>`; CI runs both with `--fail-on-warn` for pull requests, pushes, and manual dispatches, so WARNs must be resolved by porting/adapting the change to the counterpart or clearly explaining why it should not transfer.
- After changes affecting 1966 content or rules, continue to run `python TGC/tools/validate_1966_extension.py` and `python TGC/tools/audit_1966_balance.py`.

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
