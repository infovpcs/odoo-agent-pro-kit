# Session Context — Docker Sandbox Foundation

> Read this file first when starting a new Codex session in this repository.
> Update it after every completed task, material decision, blocker, commit, or
> release. Keep it concise and factual; detailed specifications remain in the
> linked documents.

## Resume instruction

Continue the Docker Sandbox Foundation work from the **Current state** below.
Before changing files:

1. Confirm the current Git branch and working tree.
2. Read the next task and its linked design/task sections.
3. Preserve unrelated user changes.
4. Implement only the next unblocked task.
5. Run the relevant validation and record the evidence here.
6. Do not merge, push, tag, publish, install external software, or create the
   private Pro repository without explicit user authorization.

## Project

- Repository: `infovpcs/odoo-agent-pro-kit`
- Organization: VPerfectCS
- Public license: Apache-2.0
- Supported Odoo versions: 17.0, 18.0, and 19.0
- Active workstream: public Docker Sandbox foundation and open-core commercial
  planning
- Active branch: `feature/docker-sandbox-planning-foundation`
- Branch base: `main` at commit `192f6c9`
- Last context update: 2026-08-12 (Asia/Kolkata)

## Objective

Build an open-source, reproducible Docker Sandbox execution layer in which each
Odoo custom-development session has an isolated agent workspace, Git branch,
Odoo runtime, PostgreSQL database, filestore, logs, MCP context, tests, and
progress state. Preserve the existing version-aware Odoo skills and
`/plan-analysis` -> `/start-coding` -> `/testing` lifecycle.

Commercial capabilities will later live in a separate private Pro repository
that consumes stable Community releases instead of forking this repository.

## Authoritative documents

### Technical

- `docs/docker-sandbox/README.md` — technical plan entry point.
- `docs/docker-sandbox/requirements.md` — scope and acceptance scenarios.
- `docs/docker-sandbox/design.md` — architecture and integration contracts.
- `docs/docker-sandbox/tasks.md` — phased implementation backlog and gates.
- `docs/docker-sandbox/source-review.md` — superseded approaches that must not
  be reintroduced.

### Commercial

- `docs/commercial/README.md` — commercial plan entry point.
- `docs/commercial/product-options.md` — packages and revenue options.
- `docs/commercial/repository-strategy.md` — Community/Pro boundaries.
- `docs/commercial/delivery-roadmap.md` — staged validation and launch plan.

## Decisions made

1. One Docker Sandbox microVM represents one agent/module development session.
2. Each sandbox uses its private Docker daemon to run an inner Compose stack
   containing the selected Odoo version and PostgreSQL.
3. Odoo does not belong in the outer agent template. The agent/tooling template
   and version-pinned Odoo service images have separate release lifecycles.
4. Writable concurrent sessions use isolated Git clones/branches by default.
5. Each session owns its database, filestore, Compose project, logs, progress,
   results, and dynamically published ports.
6. `manage_modules.sh` remains the single module install/update/test control
   point and will gain a container-aware executor.
7. Community remains useful and Apache-2.0. Team management, remote fleet,
   advanced upgrade analysis, billing, enterprise controls, and hosted service
   code belong in a separate private Pro repository.
8. Pro will consume tagged Community contracts, schemas, packages, kits, and
   images; it will not be a long-lived private fork.
9. Changes merge into `main` only through a reviewed, tested release pull
   request after the relevant exit gates pass.
10. The earlier standalone Docker Sandbox setup draft was consolidated into the
    authoritative documents and removed to prevent conflicting instructions.

## Completed

- [x] Reviewed the existing repository, local Odoo bootstrap, module manager,
  MCP configuration, hooks, fleet workflow, and agent integrations.
- [x] Validated the high-level architecture against current Docker Sandbox and
  official Odoo container documentation.
- [x] Created Docker Sandbox requirements, technical design, task pipeline, and
  superseded-research decisions.
- [x] Created commercial packages, Community/Pro repository strategy, and the
  staged recurring-revenue roadmap.
- [x] Linked technical and commercial roadmaps from the main README.
- [x] Removed the obsolete `DOCKER_SANDBOX_SETUP.md` draft after consolidation.
- [x] Created and switched to `feature/docker-sandbox-foundation`.
- [x] Ran the repository's isolated test suite: 7 tests passed.
- [x] Validated shell syntax for current shell entry points.
- [x] Validated all 18 skill files.
- [x] Ran `git diff --check` successfully.
- [x] Reviewed the Docker Sandbox and commercial planning documents for
  consistency; clarified that Community concurrency is bounded to one host and
  shared/remote team fleet orchestration belongs in Pro.
- [x] Added `scripts/validate.sh` as the project-owned validation entrypoint and
  documented it in `README.md` and `CONTRIBUTING.md`.
- [x] Ran the validation entrypoint from a clean Bash process on 2026-08-12:
  7 tests passed, 18 skills validated, shell syntax passed, and Git whitespace
  validation passed.
- [x] Completed FOUNDATION-001 and received user approval to create the focused
  planning-foundation commit on a dedicated branch.

## Current state

- FOUNDATION-001 planning-foundation changes are included in the baseline
  commit on `feature/docker-sandbox-planning-foundation`.
- Docker CLI and daemon are available.
- Docker version observed: `29.7.2`.
- Docker daemon reported Linux `x86_64` containers on this host.
- Docker Sandbox CLI (`sbx`) is not installed.
- The global Conda pytest environment auto-loads an incompatible
  `pytest-asyncio` plugin and fails during collection.
- Repository tests pass when external plugin auto-loading is disabled:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests`.
- No branch has been pushed, no commit has been created for this work, and no
  private Pro repository has been created.

## Blockers and risks

### Immediate

- Phase 0 cannot validate Docker Sandbox capabilities until `sbx` is installed
  and authenticated.
- Installing and authenticating the Docker Sandbox CLI for FOUNDATION-002
  requires explicit user authorization.

### Tracked design risks

- Docker Sandbox kits and SSH are evolving and require CLI capability/version
  checks.
- Odoo image and API behavior must be verified independently for 17/18/19.
- Nested Docker has meaningful disk and memory cost; limits must be measured.
- Clone-mode changes can be lost during destruction without commit/patch export.
- Odoo Enterprise sources and customer data require strict private boundaries.

## Next task

### Task ID: FOUNDATION-002 — Docker Sandbox CLI capability baseline

Goal: install and authenticate the Docker Sandbox CLI, then document the exact
supported CLI and capability matrix before relying on it in implementation.

Steps:

- [ ] Obtain explicit authorization to install external Sandbox tooling.
- [ ] Install `sbx` using the supported official installation path.
- [ ] Authenticate if required without recording credentials in the repository.
- [ ] Capture version and diagnostics evidence.
- [ ] Verify template, kit, secret, policy, ports, skills, and SSH commands.
- [ ] Record supported, experimental, unavailable, and version-gated behavior.
- [ ] LIVE TEST: run the documented diagnostics/capability command sequence from
  a clean shell and confirm the recorded matrix matches the installed CLI.

Do not install software or initiate authentication without explicit user
authorization.

## Following tasks

1. **FOUNDATION-003:** write the architecture decision record and approve image,
   PostgreSQL, resource, retention, and Community/Enterprise boundaries.
2. **FOUNDATION-004:** perform the Phase 0 stock-sandbox LIVE TEST.
3. **ODOO19-001:** implement the public Odoo 19 inner Compose proof of concept.
4. Continue in the order and gates defined by
   `docs/docker-sandbox/tasks.md`.

## Validation commands

Run the repository-owned validation entrypoint:

```bash
./scripts/validate.sh
```

Clean-shell LIVE TEST command:

```bash
env -i PATH="$PATH" /bin/bash --noprofile --norc ./scripts/validate.sh
```

Results on 2026-08-12:

- Repository tests: `7 passed in 0.23s`.
- Skills: `18 skill file(s) validated, no issues found`.
- Shell syntax: passed.
- Git whitespace validation: passed.

## Release workflow

```text
feature branch
  -> implementation and documentation
  -> focused validation
  -> phase exit gate
  -> release notes and version update
  -> pull request and review
  -> explicit approval
  -> merge to main
  -> signed tag and release
```

Never treat a task checkbox as permission to push, merge, tag, publish, create
external resources, or perform a paid operation.

## Context update protocol

At the end of every working session:

1. Update **Last context update**.
2. Move finished items into **Completed** with test evidence.
3. Rewrite **Current state** from actual `git status`, tools, and runtime state.
4. Record blockers with the exact failing command or missing authority.
5. Set exactly one **Next task** with acceptance and LIVE TEST requirements.
6. Keep only the next few dependent items under **Following tasks**.
7. Record commits, pull requests, tags, releases, and external resources only
   after they actually exist.
