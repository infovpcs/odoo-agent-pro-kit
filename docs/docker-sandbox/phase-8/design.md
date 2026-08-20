# Phase 8 Design: Full-Coverage Skill-Orchestrated Migration Pipeline

Status: complete (2026-08-20). All Deliverables and all five
platform/orchestration coverage checklist items in
`docs/docker-sandbox/tasks.md` Phase 8 are verified with real evidence. See
`docs/docker-sandbox/phase-8/orchestration-coverage-evidence.md` for the
session-start hook, version→skill mapping, sole-entrypoint, and
context-handoff (write + read) verification.

## Purpose

Prove that this repository's complete skill set, dynamic context handoff, and
Docker Sandbox microVM execution model together form a mature, client-ready
pipeline for real Odoo custom-module work — not a synthetic fixture. This is
the bridge from "the sandbox runs Odoo" (Phases 0-7) to "the sandbox runs a
correctly sequenced, multi-skill agent development lifecycle end to end,
unattended, inside an isolated microVM, with evidence."
`CommandingSystem/SKILL.md` "Phase 8: Sandbox-native canonical skill
sequence" references this document as the canonical source for the sequence
rather than duplicating it.

## Canonical skill invocation sequence (binding)

This is the exact, ordered sequence every real module port/migration run
must follow inside a Docker Sandbox session, per
`docs/docker-sandbox/tasks.md` Phase 8 "Scope: skill sequence to validate":

1. **Dependency/context intake** — `Odoo{V}ExistingDependencyContext` (source
   version, then target version) against the module, including Odoo
   Enterprise dependency detection where relevant.
2. **Coding standard** — `Odoo{V}CodingStandard` for the *target* version,
   applied to every ported file (manifest, models, views, security, data,
   static assets).
3. **Planning** — `PRD-Writing` + `CommandingSystem` `/plan-analysis
   {version} {module}` producing `docs/requirements.md`, `docs/design.md`,
   `docs/tasks.md`, `docs/module_meta.md`, using the intake context from
   step 1 as input.
4. **Install/update lifecycle** — `sandboxctl module <session>
   install|update|test <module>` is the sole entrypoint; no raw `odoo-bin`
   calls bypass it. Governed by `Odoo_Custom_App_Install_Update` +
   `OdooRestartUpgradeRules` decision rules. As of `odoo-agent-pro-kit`
   0.3.3, the Compose executor also re-verifies `ir_module_module.state`
   after the operation, so a silently-skipped missing dependency (e.g. an
   Enterprise app) correctly reports `failed` instead of a CLI-exit-0 false
   "succeeded" — see "Enterprise-dependency handling" below.
5. **Coding loop** — `CommandingSystem` `/start-coding {version} {module}`:
   per-task implementation with `auto_test_runner.py` after every task,
   `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` episodic-context writes per
   `context_handoff_workflow.md`, and the PASS/PARTIAL/FAIL gate (no `[x]`
   without a passing or reviewed-PARTIAL auto-test).
6. **Backend testing** — `Odoo_Custom_Backend_Testing` against the sandboxed
   Compose Odoo instance (ORM/ACL/constraint/report coverage as applicable).
7. **Live UI evidence** — `Agent-browser-skill` (or
   `Odoo_Module_Documentation_Screenshot` where it supersedes it) drives the
   sandbox's real published port for a cookie/CSRF-clean session — never a
   local-workspace/ad hoc browser login.
8. **Frontend testing** — `Odoo_Custom_Frontend_Testing` for any
   JS/OWL/QWeb-touching module; modules with no such assets are scoped N/A
   and recorded as such, never silently skipped.
9. **Documentation regeneration** — `CommandingSystem` `/testing {version}
   {module}` regenerates `static/description/index.html` and screenshots
   from the live sandboxed instance for the *target* version.
10. **Context handoff and session reset** — verify `CLAUDE.md` reflects
    100%-complete state, then start a **fresh** agent session/context
    against the same module directory and confirm it resumes purely from
    `CLAUDE.md` + `docs/tasks.md` state — proving the dynamic
    context-handoff design survives a full context reset, not just
    in-session memory carryover.

## Enterprise-dependency handling

Steps 1 and 4 must correctly surface a module's real Odoo Enterprise
dependencies without ever fetching, bundling, or committing licensed
Enterprise source into the sandbox or this repository:

- Step 1 (`Odoo{V}ExistingDependencyContext`) records Enterprise dependency
  detection in the dependency matrix as a normal risk/constraint row — it
  does not require Enterprise source to be present to *identify* the
  dependency (manifest `depends`/`license` inspection is sufficient).
- Step 4 (`sandboxctl module ... install|update`) is the enforcement point:
  Odoo's own `-i`/`-u` CLI path treats an unresolvable dependency (missing
  from the sandbox image, e.g. an Enterprise-only app) as a
  skip-with-warning and still exits 0 — it does **not** raise a hard error
  the way the ORM `button_install()` path does. The authoritative signal is
  `ir_module_module.state`: a module stuck at `to install` (rather than
  `installed`) after the operation means an unresolved dependency blocked
  it. `manage_modules.sh`'s Compose executor (0.3.3+) re-checks this state
  automatically and fails the structured operation result
  (`install_failed`/`update_failed`) so the pipeline never reports a false
  "succeeded" for a module that cannot actually run.
- Sandbox sessions never mount Enterprise addon source unless a session
  explicitly requests it (`docs/docker-sandbox/design.md` "enterprise"
  Compose profile, read-only, opt-in per session) — the default posture,
  and the one used for every Phase 8 Enterprise-dependency test to date, is
  Enterprise-source-free: the pipeline proves *detection*, not a full
  Enterprise-backed install.

Verified twice with real evidence: an internal fixture module
(`real_estate`, 17.0, depends on Enterprise `sale_subscription`/
`web_studio`/`sale_renting_crm` — ORM hard-failure path) and a real client
project module (`account_report_template` from `Aptusinfotech/aptus`,
depends on the real Enterprise Accounting app `accountant`/
`account_accountant` — CLI skip-with-warning path), the second reproduced
consistently across Odoo 17.0/18.0/19.0 in a reverse-migration test. See
`docs/docker-sandbox/phase-8/enterprise-dependency-evidence/` and
`docs/docker-sandbox/phase-8/aptus-enterprise-dependency-evidence/`.

## Reference runs

### Pilot: `edit_remove_pricelist_rule` (17.0 -> 18.0)

- Validation host: Ubuntu 24.04+ KVM (see `.sandbox/validation-host.env` for
  connection details; not committed).
- Outer Docker Sandbox microVM: `phase8-pilot` (Codex agent), reused across
  dispatches.
- Inner Compose sandbox session: `phase8-pricelist-18`.
- All 10 steps completed with real evidence, including a real bug found and
  fixed during step 7 (`KeyError: <NewId ...>` in a smart-button compute
  method — see the "NewId compute pitfall" section added to the
  `Odoo{17,18,19}CodingStandard` skills). Full narrative:
  `docs/docker-sandbox/phase-8/live-test.md`.

### Second module: `hr_document_report` (17.0 -> 18.0)

- Outer Docker Sandbox microVM: `phase8-hr-document-report`.
- All 10 steps completed: 6/6 `TransactionCase` tests, live UI/XSS and both
  PDF-layout checks, frontend N/A by inventory, regenerated `/testing` docs,
  resource capture, and fresh-process context-handoff resume. Wall-clock:
  outer/inner 58m55s/46m32s; Odoo/PostgreSQL cumulative CPU
  40.197s/142.675s; memory peaks 245.3/255.2 MiB. Full narrative:
  `docs/docker-sandbox/tasks.md` "Progress record" and `SESSION_CONTEXT.md`.

### Enterprise-dependency proof: `real_estate` (17.0) + `account_report_template` (17.0/18.0/19.0)

- Two dedicated sandbox sessions (`phase8-enterprise-dep-test`,
  `phase8-aptus-ent-test`), each destroyed immediately after evidence
  capture. See "Enterprise-dependency handling" above for the two distinct
  failure-detection paths this exercised (ORM hard-failure vs CLI
  skip-with-warning), and the `manage_modules.sh` 0.3.3 fix this surfaced.

## Go/no-go: batching the remaining ~45 backlog modules

**Decision: GO**, with a phased/staggered batching approach — not a single
unbounded batch run.

Rationale, from measured evidence:

- The canonical 10-step sequence has now been proven end-to-end, unattended,
  inside a real Docker Sandbox microVM, across three independent real
  modules (one pilot, one full second Tier-1 module, one Enterprise-blocked
  module tested across all three Odoo versions) with zero process deviation
  and zero fallback to bare local execution.
- Per-module wall-clock cost is non-trivial but bounded and predictable:
  `hr_document_report`'s full 10-step run took ~59 minutes outer / ~47
  minutes inner wall time on the Phase 7-measured 2-vCPU/15-GiB Oracle host.
  At that rate, ~45 backlog modules run strictly serially would take
  roughly 44 hours of wall time on a single host — too slow for a "batch
  overnight" pattern on this hardware, but entirely workable staggered
  across sessions/days, or parallelized modestly.
- Phase 7's own load testing found this host degrades sharply beyond ~2
  concurrent cold provisions (load average ~82, SSH starvation) and
  recommended "one cold provision at a time, at most two constrained active
  sessions." Phase 8's reference runs respected that limit by reusing one
  sandbox session sequentially rather than fanning out.
- The Enterprise-dependency detection path is now proven reliable and
  Enterprise-source-free by default, which matters directly for batching:
  many VPCSCloud Apps Store backlog modules likely have zero Enterprise
  dependencies, but some may not, and the pipeline now correctly reports
  `install_failed`/`update_failed` for those rather than a false pass —
  batch runs will surface these automatically instead of silently
  fabricating a "done" module.

Recommended batching shape:

1. **Triage pass first** (cheap, no sandbox needed): run step 1
   (dependency/context intake) statically across the full ~45-module
   backlog to classify each module as Community-only vs
   Enterprise-dependent, and flag any with unusually large/complex
   `depends` chains. This produces a batching order, not a batch run.
2. **Batch Community-only, low-complexity modules first**, at most 2
   concurrent sandbox sessions per the Phase 7 capacity limit, sequenced
   rather than fully parallel-fanned to avoid host degradation. Expect
   roughly 45-70 minutes wall time per module based on the two measured
   reference runs.
3. **Handle Enterprise-dependent modules as a separate, explicitly-flagged
   batch** — these require either (a) accepting the pipeline's correct
   `install_failed` result as the terminal state for a Community-only
   sandbox, with the port left as a documented static/manual deliverable,
   or (b) a follow-up decision on optionally mounting the user's own
   licensed Enterprise source read-only per the existing "enterprise"
   Compose profile design (not yet exercised end-to-end for a full
   Enterprise-backed install/test pass — that remains future work, not
   assumed complete by this decision).
4. **Re-run the four still-open platform/orchestration checklist items**
   (session-start hook detection, skill-mapping resolution, sole-entrypoint
   audit, `context_guard.py` live proof) before committing to full-scale
   batching, since they validate orchestration correctness that a batch run
   would otherwise implicitly assume.

This decision does not itself close the Phase 8 exit gate — the four
platform/orchestration checklist items above remain the final blockers.
