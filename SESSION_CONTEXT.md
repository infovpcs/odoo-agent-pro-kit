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
- Active branch: `feature/docker-sandbox-phase-4`
- Branch base: `main` at commit `192f6c9`
- Last context update: 2026-08-13 (Asia/Kolkata)

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
- [x] Added repository-wide phase workflow rules in `AGENTS.md`: one phase per
  session, mandatory checklist/LIVE TEST/documentation/context/validation, and
  one focused commit before the next phase.
- [x] Accepted ADR-0001 for the outer Sandbox/inner Compose boundary, clone-mode
  default, local-mode compatibility, and Community/Pro interface.
- [x] Selected `postgres:15-bookworm` for the initial Odoo 17/18/19 matrix and
  recorded initial resource and retention defaults.
- [x] Verified the official Odoo 17.0, 18.0, and 19.0 registry indexes contain
  Linux amd64 and arm64/v8 manifests on 2026-08-12.
- [x] Defined the public Community and separately licensed Enterprise addon
  boundary.
- [x] Added version 1.0.0 session and operation-result JSON schemas plus schema
  contract tests; the repository suite now has 9 passing tests.
- [x] Installed official `docker-sbx` 0.38.0 and Git on the authorized Oracle
  Cloud Ubuntu 24.04 validation VPS; added `ubuntu` to the `kvm` group and
  initialized Docker's balanced local Sandbox policy.
- [x] Authenticated `sbx` through Docker's device OAuth flow without recording
  credentials in the repository; all 9 diagnostic checks passed.
- [x] Captured template, kit, secret, policy, ports, shared-skills, SSH, clone,
  CPU, memory, and publish command capabilities. Kits, skills, SSH, and custom
  secrets identify themselves as experimental in 0.38.0.
- [x] Passed the Ubuntu Phase 0 LIVE TEST: stock clone-mode Codex sandbox,
  private Docker 29.7.1, Compose 5.4.0, nginx HTTP, ephemeral loopback port,
  stop/start persistence, evidence copy, sandbox removal, and port cleanup.
- [x] User approved the platform validation policy: use the available Intel Mac
  for repository/Docker/registry checks and the Ubuntu 24.04 KVM VPS for all
  Docker Sandbox microVM and runtime LIVE TESTS.
- [x] Completed the Phase 0 checklist and platform-adjusted exit gate.
- [x] Implemented the Phase 1 Odoo 19 controller, pinned inner runtime,
  generated configuration, fixture addon, structured state/results, bounded
  readiness, diagnostics, and lifecycle harness.
- [x] Passed the Phase 1 Ubuntu Sandbox LIVE TEST twice from clean session
  volumes and twice with a warm image cache, including install, update, Odoo 19
  JSON-RPC verification, restart, export, destroy, writable logs, and cleanup.
- [x] Completed the Phase 2 data-driven Odoo 17/18/19 controller matrix with
  pinned per-version images, XML-RPC for 17/18, JSON-2 for 19, private fixture
  copies, and concurrent lifecycle coverage.
- [x] Built every Phase 2 dev image for linux/amd64 and linux/arm64 as OCI
  output and passed the concurrent amd64 LIVE TEST in an Ubuntu KVM Sandbox.
- [x] Implemented the Phase 3 Compose executor, `sandboxctl module` delegation,
  database-aware install/update resolution, structured results/progress,
  session manifest handoff, unified Odoo file logs, and lifecycle skill gates.
- [x] Passed the Phase 3 underlying Odoo 19 runtime gates in an Ubuntu KVM
  Codex Sandbox: install/update/test, JSON-2 CRUD, result/progress/log gates,
  health wait, destroy, orphan check, and outer Sandbox removal.
- [x] Passed the literal Phase 3 Codex LIVE TEST after OAuth restoration:
  `/plan-analysis`, `/start-coding`, and `/testing` recorded successful
  install/update/test/JSON-2/log gates without raw `odoo-bin` skill calls.
- [x] Implemented the Phase 4 agent-neutral Odoo mixin 0.4.0, pinned artifact
  lock, `sbx` 0.38.x capability/policy/package validation, Codex/Claude/Copilot
  launcher, scoped secret/shared-skills guidance, and VS Code/Cursor SSH tasks.
- [x] Validated the mixin with the real `sbx` 0.38.0 parser and passed the Phase
  4 Codex/Odoo partial live test: clone-mode launch, OAuth, edited fixture copy,
  Odoo 19 create/install/test results, 35,990-byte correlated log retrieval, and
  complete inner/outer cleanup.
- [x] User explicitly approved `sbx exec` as the Ubuntu IDE-equivalent fallback
  after the pinned experimental SSH authentication failure remained
  reproducible following fresh login, daemon restart, setup, and sandbox retry.
- [x] Completed the Phase 4 LIVE TEST and exit gate with Codex plus the approved
  terminal adapter; supplemental OpenCode 1.18.13 also passed the same isolated
  edit, Odoo 19 module-test, correlated-log, and cleanup contract.

## Current state

- FOUNDATION-001 is committed as `2c2b6d6` on
  `feature/docker-sandbox-planning-foundation`.
- Phase 0 is complete and committed on `feature/docker-sandbox-phase-0` with
  subject `Complete Docker Sandbox Phase 0 validation`.
- Docker CLI and daemon are available.
- Docker version observed: `29.7.2`.
- Docker daemon reported Linux `x86_64` containers on this host.
- Docker Sandbox CLI (`sbx`) is not installed. The official Homebrew cask was
  trusted but installation rejected this Intel Mac because it requires arm64.
- The accessible VPS is Ubuntu 20.04 x86_64 with Docker 27.3.1, 256 GiB free,
  and no `/dev/kvm`; it was inspected read-only and is unsupported for `sbx`.
- The Oracle validation VPS is Ubuntu 24.04 x86_64 with 2 vCPU, 15 GiB RAM,
  nested KVM, and 45 GiB root disk. After Sandbox cleanup it used 5.9 GiB.
- The Oracle VPS retains `docker-sbx` 0.38.0, its cached Codex template, Docker
  OAuth login, balanced policy, disposable Git repositories including
  `/home/ubuntu/phase2-src`, and exported `/home/ubuntu/phase0-evidence.txt`;
  no sandbox or published port remains.
- The reusable Oracle validation-host connection is stored locally in the
  Git-ignored `.sandbox/validation-host.env`. Source that file and connect with
  `ssh -i "$VALIDATION_SSH_KEY" "$VALIDATION_SSH_TARGET"`. Never commit or copy
  the private key into this repository.
- The global Conda pytest environment auto-loads an incompatible
  `pytest-asyncio` plugin and fails during collection.
- Repository tests pass when external plugin auto-loading is disabled:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests`.
- Phase 1 is committed as `11a8617` on
  `feature/docker-sandbox-phase-1` (`Complete Docker Sandbox Phase 1 runtime`).
- One disposable local lifecycle run passed on 2026-08-12 using Docker 29.7.2,
  Compose 5.3.1, and the Linux amd64 daemon: create, base initialization,
  fixture install/update, JSON-RPC version check, stop/start, export, destroy,
  and orphan-volume assertion all passed.
- The Phase 1 Ubuntu Sandbox LIVE TEST passed on 2026-08-12 with `sbx` 0.38.0,
  Ubuntu 24.04 x86_64, 2 vCPU, 6 GiB RAM, inner Docker 29.7.1, and Compose
  5.4.0. Four lifecycle runs passed (two clean-volume and two warm-cache), no
  matching inner containers/volumes remained, and the outer sandbox was removed.
- The stock Codex template did not contain pytest; the attempted microVM
  repository validation stopped with `No module named pytest`. Per the approved
  platform split, clean-shell repository validation ran on the Intel workstation.
- No branch has been pushed and no private Pro repository has been created.
- Active branch: `feature/docker-sandbox-phase-4`.
- Phase 2 repository validation passes with 20 tests, 18 validated skills,
  shell/Python syntax checks, and Git whitespace validation.
- The Intel workstation passed the concurrent warm-cache amd64 lifecycle and
  built all three dev images for amd64 and arm64 using a temporary BuildKit
  container builder. The builder and OCI output were removed after validation.
- The Ubuntu 24.04 KVM LIVE TEST passed with `sbx` 0.38.0, a 2-vCPU/8-GiB
  microVM, Docker 29.7.1, and Compose 5.4.0. Odoo 17, 18, and 19 ran
  concurrently and passed install, data-changing update, protocol CRUD,
  restart, export, destroy, and orphan checks. The Sandbox was removed and the
  host returned to 5.9 GiB used.
- Phase 3 contract tests pass locally. A real workstation Docker attempt did
  not provision because the Docker daemon was unavailable; no container or
  volume was created and the disposable failed state was moved away.
- Clean-shell `./scripts/validate.sh` passed on 2026-08-13: 24 tests, 18 skill
  validations, shell/Python syntax, and Git whitespace checks all passed.
- Final post-LIVE-TEST clean-shell validation repeated successfully on
  2026-08-13 with the same 24/18/syntax/whitespace results.
- Phase 3 is complete and committed on `feature/docker-sandbox-phase-3` with
  subject `Complete Docker Sandbox Phase 3 integration`.
- The Phase 3 KVM runtime run produced succeeded install/update/test results,
  verified Odoo 19 JSON-2 CRUD, and retrieved 61,597 bytes through the Odoo log
  gate. The active inner and outer sessions were fully removed.
- Phase 4 implementation tests pass locally: 29 repository tests, 18 skill
  validations, artifact locking, shell/Python syntax, and whitespace checks.
  The Ubuntu host validated, packed, and inspected `odoo-mixin` 0.4.0 with
  `sbx` 0.38.0; the temporary ZIP was removed after the check.
- The Phase 4 LIVE TEST used Codex CLI 0.146.0 in
  `odoo-phase4-codex`. Odoo session `19-sandbox-fixture-107d14` emitted
  succeeded create/install/test results, preserved the candidate fixture edit,
  and returned 35,990 bytes of correlated Odoo logs. Inner volumes and the
  outer sandbox were removed; no sandbox remains.
- Supplemental Phase 4 validation passed with Docker's built-in OpenCode
  template and OpenCode 1.18.13. The same mixin propagated its environment and
  runtime instructions; an isolated fixture edit plus Odoo 19 create/install/
  test passed, and correlated log retrieval returned 34,455 bytes. Session
  `19-sandbox-fixture-f43943` and outer sandbox `odoo-phase4-opencode` were
  fully removed. The approved `sbx exec` fallback, rather than this supplemental
  agent run, satisfies the IDE-adapter gate.
- Final clean-shell `./scripts/validate.sh` passed on 2026-08-13: 29 tests, 18
  skill validations, artifact locking, shell/Python syntax, and Git whitespace
  checks all passed. The workstation Docker daemon was 29.7.2 linux/amd64 with
  Compose 5.3.1; unrelated running containers were not changed.
- Phase 4 is complete and committed with subject
  `Complete Docker Sandbox Phase 4 adapters`.
- Phase 5 local concurrency is the sole next task and must begin in a fresh
  session with this context and the authoritative checklist reread.

## Blockers and risks

### Immediate

- No immediate Phase 4 blocker remains. `ssh odoo-phase4-codex.sbx -- id` negotiated
  the managed server and host key but closed during authentication with
  `Connection closed by UNKNOWN port 65535` and exit 255. The failure repeated
  with the sandbox running, after workspace trust, after `sbx setup ssh`, and
  after `sbx daemon restart`. The daemon recorded HTTP 101 SSH upgrades while
  `sbx exec`, Codex OAuth, policy, kit, inner Odoo, tests, and logs passed. See
  `docs/docker-sandbox/phase-4/live-test.md`.
- The user completed a full `sbx logout` plus device-code `sbx login` on
  2026-08-13. Authentication diagnostics passed afterward, but a newly created
  running Codex sandbox failed SSH identically. Apt reports 0.38.0 as both the
  installed and newest candidate. The retry sandbox was removed. The user
  explicitly approved the validated `sbx exec` terminal fallback; SSH remains a
  tracked experimental platform limitation rather than an exit-gate blocker.
- OpenAI OAuth remains configured only in the Docker Sandbox host secret store;
  no credential was added to the repository.
- Docker supports Sandbox on Apple Silicon macOS 14+; this host is Intel macOS.
- Native macOS Sandbox behavior remains untested because the workstation is
  Intel. It is not required by the approved validation policy unless a future
  task claims native macOS Sandbox support.

### Tracked design risks

- Docker Sandbox kits and SSH are evolving and require CLI capability/version
  checks.
- Odoo image and API behavior must be verified independently for 17/18/19.
- Nested Docker has meaningful disk and memory cost; limits must be measured.
- Clone-mode changes can be lost during destruction without commit/patch export.
- Odoo Enterprise sources and customer data require strict private boundaries.

## Next task

### Task ID: TEMPLATE-001 — Phase 4 agent templates and IDE adapters

Goal: package the validated controller/skills into minimal agent templates and
IDE attach adapters while keeping platform differences outside the runtime.

Steps:

- [ ] Start Phase 4 only in a fresh session after the Phase 3 focused commit.
- [ ] Read the Phase 4 checklist and linked template/kit design contracts.

Work from a fresh session after reading this file and the Phase 4 section of
`docs/docker-sandbox/tasks.md`.

## Following tasks

1. **TEMPLATE-001:** implement Phase 4 agent templates, kits, and IDE adapters.
2. Continue in the order and gates defined by
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

Results on 2026-08-12 after Phase 0 completion:

- Repository tests: `9 passed in 0.44s`.
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
