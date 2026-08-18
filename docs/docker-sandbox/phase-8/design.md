# Phase 8 Design: Full-Coverage Skill-Orchestrated Migration Pipeline

Status: in progress (live validation run started 2026-08-18, continued across
multiple bounded dispatches on the Ubuntu KVM validation host).

## Purpose

Prove that this repository's complete skill set, dynamic context handoff, and
Docker Sandbox microVM execution model together form a mature, client-ready
pipeline for real Odoo custom-module work, using the VPCSCloud Apps Store
`edit_remove_pricelist_rule` (17.0 -> 18.0) module as the live pilot, executed
**inside** a Docker Sandbox session rather than the bare local workspace used
for the initial ad hoc pilot.

## Canonical skill invocation sequence (binding)

This is the exact, ordered sequence every pilot/batch module run must follow
inside a Docker Sandbox session, per `docs/docker-sandbox/tasks.md` Phase 8.
`CommandingSystem/SKILL.md` should reference this document as the canonical
source for the sequence rather than duplicating it.

1. Dependency/context intake — `Odoo17ExistingDependencyContext` (source),
   then `Odoo18ExistingDependencyContext` (target) against the pilot module.
2. Coding standard — `Odoo18CodingStandard` applied to every ported file.
3. Planning — `PRD-Writing` + `CommandingSystem /plan-analysis 18.0
   edit_remove_pricelist_rule` producing `docs/requirements.md`,
   `docs/design.md`, `docs/tasks.md`, `docs/module_meta.md` for the port.
4. Install/update lifecycle — `sandboxctl module <session> install|update
   edit_remove_pricelist_rule` (the sole entrypoint; no raw `odoo-bin`),
   governed by `Odoo_Custom_App_Install_Update` +
   `OdooRestartUpgradeRules` decision rules.
5. Coding loop — `CommandingSystem /start-coding 18.0
   edit_remove_pricelist_rule` with `auto_test_runner.py` after every task and
   `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` episodic-context writes per
   `context_handoff_workflow.md`.
6. Backend testing — `Odoo_Custom_Backend_Testing` against the sandboxed
   Compose Odoo instance.
7. Live UI evidence — `Agent-browser-skill` against the sandbox's published
   Odoo port (closes the local-pilot's blocked-browser-screenshot gap).
8. Frontend testing — `Odoo_Custom_Frontend_Testing` (only if the module
   touches JS/OWL/QWeb; `edit_remove_pricelist_rule` is backend/view-only, so
   this step is scoped N/A and recorded as such, not skipped silently).
9. Documentation regeneration — `CommandingSystem /testing 18.0
   edit_remove_pricelist_rule` regenerates
   `static/description/index.html` and screenshots from the live instance.
10. Context handoff and session reset — verify `CLAUDE.md` reflects
    100%-complete state, then start a fresh agent session/context against the
    same module directory and confirm it resumes purely from `CLAUDE.md` +
    `docs/tasks.md`.

## Execution environment for this run

- Validation host: Ubuntu 24.04+ KVM (see `.sandbox/validation-host.env` for
  connection details; not committed here).
- Outer Docker Sandbox microVM: `phase8-pilot` (Codex agent), reused across
  dispatches — not recreated per step.
- Host repo clone bind-mounted into the sandbox: `~/odoo-agent-pro-kit` on
  branch `main-phase8` (branched from local `main` at commit `c4d4af1`).
- Inner Compose sandbox session: `phase8-pricelist-18`, created via
  `sandbox/bin/sandboxctl create --version 18.0 --module sandbox_fixture
  --session phase8-pricelist-18` from inside `phase8-pilot`, then the pilot
  module `edit_remove_pricelist_rule` (18.0 target tree, transferred from the
  Mac workstation) was copied into the session's
  `.sandbox/sessions/phase8-pricelist-18/addons/` directory (the directory
  `sandboxctl module` operates against) so it can be installed/updated in
  place of the generic fixture module.
- Inference for `/plan-analysis`, `/start-coding`, `/testing`: Hermes
  `odoo18-dev` profile on the same host, openrouter/free + Hetzner fallback
  chain (`source /home/ubuntu/.hermes/claude-code/venv/bin/activate`).

## Deviations / open items (updated as the run progresses)

- The `edit_remove_pricelist_rule` module has no JS/OWL/QWeb assets in either
  version's manifest as transferred; step 8 (frontend testing) is expected to
  be scoped N/A pending confirmation during the coding-standard/dependency
  intake steps, not silently skipped.
- Progress and blockers for this specific run are tracked live in
  `docs/docker-sandbox/phase-8/live-test.md` and
  `.sandbox/phase8-progress-notes.md` (untracked scratch state, gitignored).
