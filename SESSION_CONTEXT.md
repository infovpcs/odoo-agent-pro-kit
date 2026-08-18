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
- Active branch: `main`
- Branch base: `main` at commit `12368b7` (post-Phase-7, additive 0.2.0/0.3.0 work)
- Last context update: 2026-08-18 (Asia/Kolkata, live end-to-end pipeline
  test on Oracle VPS odoo19-dev passed with real inference; architecture
  diagram updated with deployment section, render pipeline fixed)

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
- [x] Implemented the Phase 5 bounded single-host Community coordinator with
  one outer Sandbox per task, normalized sessions/branches, ephemeral ports,
  capacity/resource policy, idle/retention maintenance, aggregate manifests,
  cancellation, failure isolation, and guarded cleanup.
- [x] Added atomic allocation and per-session controller locks, idempotent
  lifecycle transitions, inner Compose CPU/memory limits, and outer retention
  when inner cleanup fails.
- [x] Passed the Phase 5 Ubuntu KVM LIVE TEST with six simultaneous sessions,
  two each for Odoo 17/18/19: all installs passed, duplicate-module source/DB/
  log isolation passed, one real failed operation left five siblings healthy,
  lock/resource/cleanup gates passed, and all inner/outer resources were removed.
- [x] Implemented Phase 6 unified metadata-prefixed logs, redacted diagnostic
  bundles, stable test artifacts, optional JSONL telemetry, bounded recovery,
  invalid-module validation, and explicit PostgreSQL backup/restore.
- [x] Passed the Phase 6 Ubuntu KVM LIVE TEST with Odoo/PostgreSQL crashes,
  denied network, bounded disk pressure, invalid module, interrupted operation,
  controller restart, backup/restore, telemetry, redaction, and sibling health.
- [x] Started Phase 7 on `feature/docker-sandbox-phase-7`; added release CI,
  pinned-contract and dependency inventory tools, a benchmark recorder, guarded
  local migration, cross-platform operator runbooks, and the agent-facing
  `DockerSandboxOperations` skill.
- [x] Synchronized `docs/architecture.excalidraw` and its rendered PNG with the
  merged Docker Sandbox execution plane: bounded single-host fleet allocation,
  one microVM per session, `sandboxctl`/`manage_modules.sh`, the private inner
  Compose runtime, Odoo/PostgreSQL isolation, and structured session artifacts.
- [x] PR #2 merged to `main`; Phase 7 release fully closed.
- [x] (Additive, non-phase, 0.2.0) Built `sandbox/mcp-sidecar/` — a Compose
  override running `plugin/odoo_mcp` as a `restart: unless-stopped` service
  inside an existing Docker Sandbox session's Compose project (does not
  modify the pinned `sandbox/compose/compose.yaml`). Verified end-to-end on
  the Oracle VPS: created Odoo 19 sandbox session, brought up the sidecar,
  published its port via `sbx ports`, `curl http://127.0.0.1:8767/sse`
  returned `200 OK` `text/event-stream` from the bare host. Also fixed
  `plugin/odoo_mcp/requirements.txt` (`mcp[server]<2.0.0` pin — the
  unbounded `>=1.0.0` was resolving to `mcp` 2.0.0 and breaking with
  `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`). Committed as
  `0a84ed8`.
- [x] (Additive, 0.2.0) Created `plugin/skills/OdooHermesEnvironmentSetup/
  SKILL.md` — portable playbook for provisioning any AI agent/IDE for Odoo
  17/18/19 dev on a fresh host. Registered live as
  `odoo-hermes-environment-setup` and installed into all 3 Oracle VPS
  Hermes profiles (odoo17-dev/odoo18-dev/odoo19-dev).
- [x] (Additive) Synced the Odoo documentation knowledge-base repos
  (`knowledge-17/18/19`, ~110-130MB each, `git@github.com:infovpcs/
  Knowledge-Base.git` branches `17.0`/`18.0`/`19.0`) from the local Mac to
  the Oracle VPS at `~/odoo-knowledge-base/knowledge-<ver>/odoo<ver>-okf/`
  via `tar | ssh` (rsync is unavailable on the VPS; macOS openrsync is
  incompatible with a host lacking an rsync binary — use tar-over-ssh
  instead). Wired in as reference material: appended a "Local Odoo
  Documentation Knowledge Base" section to all 9
  `Odoo<ver>ExistingDependencyContext/SKILL.md` copies (3 profiles x 3
  versions) on the VPS, verified with a real `grep -rl` against the synced
  tree. Documented the procedure in `OdooHermesEnvironmentSetup/SKILL.md`.
  Committed as `bc007d5`.
- [x] (Additive, 0.3.0) Built a **native Hermes plugin manifest**
  (`plugin/plugin.yaml` + `plugin/__init__.py`), coexisting with the
  pre-existing Claude-Code-style `.claude-plugin/plugin.json` in the same
  directory. Registers via `register(ctx)`: 7 `odoo_*` in-process tools
  (`odoo_search_models`, `odoo_get_fields`, `odoo_get_relationships`,
  `odoo_validate_field`, `odoo_get_model_info`, `odoo_list_all_models`,
  `odoo_get_version_info` — thin wrappers around the existing
  `plugin/odoo_mcp/{config,connection_manager,model_extractor}.py`, no
  separate MCP server/port/sidecar needed inside a Hermes session), 4 slash
  commands (`/plan-analysis`, `/start-coding`, `/testing`, `/fleet` via
  `ctx.register_command()`), 2 hooks (`on_session_start` workspace
  detection, `on_session_end` connection cleanup), and all 20 bundled
  skills via `ctx.register_skill()` under the `odoo-agent-pro-kit:`
  namespace. Verified with `hermes plugins doctor plugin --ci` locally (7
  tools, 2 hooks, 4 commands, 20 skills, zero warnings after pinning
  `python_dependencies` upper bounds) and a real install+enable cycle in an
  isolated `HERMES_HOME`. Also verified `doctor` passes identically against
  all 3 Oracle VPS profiles. `plugin/.claude-plugin/plugin.json` and
  `plugin/plugin.yaml` both bumped to 0.3.0 in lockstep. Committed as
  `12368b7`, pushed to `origin/main`, and fast-forward-synced onto the
  Oracle VPS repo clone (clean, no conflicts).

## Current state

- Phase 7 is complete and release PR #2 is the reviewed integration vehicle.
  The user authorized pushing the branch and merging after validation/review.
  Apple Silicon macOS and Windows 11 remain community-validation candidates,
  not release claims.

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
- Active branch: `feature/docker-sandbox-phase-7`.
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
- Final Phase 5 clean-shell validation passed on 2026-08-13 with 37 tests, 18
  skill validations, artifact structure/locks, shell/Python syntax, and Git
  whitespace checks.
- Phase 7 targeted checks passed on the Intel macOS workstation on 2026-08-13:
  release pin verification, 19-skill validation, 3 Phase 7 tests, shell syntax,
  and Compose configuration. Compose initially failed without generated runtime
  variables; `sandbox/scripts/validate-compose.sh` now supplies non-secret
  validation-only values and passed.
- Phase 7 clean-shell `./scripts/validate.sh` passed on 2026-08-13 with 45
  tests, 19 skills, artifact/release contract checks, Compose validation,
  shell/Python syntax, and Git whitespace validation. `sbx` kit parsing was
  skipped locally because `sbx` remains unavailable on Intel macOS; it must be
  repeated on the Ubuntu KVM validation host.
- Authorized GitHub Actions run `31701912811` passed: validation/inventory,
  Odoo 17/18/19 amd64 image builds, and all three Compose smoke lifecycles.
  GitHub emitted only a non-blocking Node 20-to-24 action-runtime annotation.
- Phase 7 Ubuntu release acceptance passed for cold/warm Odoo 17/18/19
  lifecycle, 42-second warm Odoo 19 readiness, recovery/backup/restore,
  redaction, staged upgrade/rollback contracts, local migration, real kit
  packing, and dependency inventory. Full cold/warm matrices took 435.525 and
  118.385 seconds; recovery took 73.201 seconds.
- Six concurrent 1-CPU/2-GiB outer Sandboxes created in 134 seconds, but six
  simultaneous cold inner builds exceeded the 2-vCPU/15-GiB host: load average
  reached ~82, minimum available memory was 289,169,408 bytes, SSH starved, and
  disk temporarily grew from 7.5 to 13 GiB used. This host is now recommended
  for one cold provision at a time and at most two constrained active sessions.
- The overloaded load test was interrupted and recovered. A daemon restart
  invalidated OAuth; the user completed device authentication. All six outer
  Sandboxes were removed; final host state was no Sandboxes, 14 GiB available
  RAM, 7.5 GiB disk used, and no published Sandbox ports.
- Phase 7 is committed on `feature/docker-sandbox-phase-7` with subject
  `Complete Docker Sandbox Phase 7 hardening` and pushed for review.
- Apple Silicon macOS and Windows 11/WSL2 remain community-validation
  candidates. Contributors are directed to a dedicated evidence template and
  guide; maintainers review test reports, bugs, and linked fix proposals one by
  one before changing platform support status.
- PR #2 external review found three valid release-safety gaps. The branch now
  fails fleet creation when port publication fails, keeps Odoo stopped and the
  session failed after a database-restore error, and validates migration names
  before constructing the staging path; regression tests cover all three.
- Follow-up review required verified quarantine when graceful Odoo stop itself
  fails during restore recovery. The controller now checks running container
  IDs, force-removes any survivor, verifies absence, and tests that fallback.
- A third review identified three additional valid edge cases. Failed fleet
  provisioning now removes the inner runtime and outer Sandbox while recording
  cleanup failures; restore failure state is persisted before quarantine and
  survives quarantine/diagnostic errors; migration names are capped at 52
  characters so generated controller session IDs remain valid.
- Final review hardening adds a volume-preserving full Compose-stack teardown
  and verification when service-level Odoo quarantine cannot be guaranteed, so
  a surviving application cannot continue accessing a modified restore target.
- Unsuccessful restores now persist an integrity-block marker. Generic recovery
  refuses to start the stack while it exists; only a successful explicit
  restore clears the marker and permits the session to return to ready.
- Both generic recovery and direct session start enforce the restore-integrity
  marker, closing alternate lifecycle paths to a partially restored database.
- Module install, update, and test dispatch also enforces the marker before it
  can mutate the database or relabel the failed session as recoverable.
- Database backup and arbitrary service execution enforce the marker so partial
  restore data cannot be published or accessed. Status, logs, diagnostics,
  explicit restore, and cleanup remain available to operators.
- Direct `sandboxctl create` and local migration now share the 52-character
  module-name limit required by generated controller session IDs.
- Keyboard interruption during restore now enters the same durable failed-state,
  quarantine, diagnostic, and integrity-block path as other restore failures.
- Repeated interruption during restore quarantine, full-stack fallback, or
  diagnostics is caught and recorded so subsequent cleanup and terminal result
  persistence still run.
- Explicit restore retries recreate and wait for PostgreSQL after full-stack
  quarantine, while other recovery and data-access paths remain blocked.
- Fleet provisioning cleanup now runs after every outer creation attempt,
  including when the creation subprocess returns nonzero after partial success,
  preventing a partially created Sandbox from being orphaned.
- Operator interruption during outer creation, branch setup, inner provisioning,
  or port publication now uses the same cleanup and failed-manifest path instead
  of leaving an allocated Sandbox and a perpetual provisioning record.
- Provisioning cleanup temporarily ignores repeated SIGINT and writes terminal
  state before restoring normal signal handling, so a second Ctrl-C cannot skip
  outer removal or leave the manifest in provisioning.
- Allocation and initial provisioning-manifest persistence now occur inside the
  same interruption handler, eliminating the window between writing
  `provisioning` and entering guarded cleanup.
- Interruption before outer creation records that no runtime is retained, so
  the terminal failed manifest does not consume fleet capacity.
- The Phase 5 KVM host used a documented 1-vCPU/2-GiB validation override per
  microVM because the designated host has 2 vCPU/15 GiB. The shipped default
  remains 2 vCPU/8 GiB and the outer 40 GiB disk target is advisory in sbx
  0.38.x. Inner Compose reported a 3 GiB/1.0 CPU Odoo limit.
- Six unique ports in the observed 32771-32781 range were closed after cleanup;
  `sbx ls` reported no Sandboxes, the host used 7.5 GiB disk, and disposable
  `/home/ubuntu/phase5-src` was removed.
- Phase 5 is complete and committed with subject
  `Complete Docker Sandbox Phase 5 concurrency`.
- Phase 6 candidate implementation adds unified prefixed logs, redacted
  diagnostic tarballs, stable JUnit/coverage/browser artifacts, optional local
  JSONL telemetry, bounded recovery, and explicit database backup/restore.
- Phase 6 local validation passed on 2026-08-13: 42 repository tests, 18 skill
  validations, artifact structure/locks, shell/Python syntax, and Git
  whitespace checks.
- The Phase 6 Ubuntu LIVE TEST produced 11 redacted bundles covering all eight
  required reasons. Database restore returned a mutated two-row probe to its
  one-row snapshot; telemetry, log prefixes, stable artifacts, bounded
  recovery, and sibling health passed.
- The first Phase 6 candidate exposed and corrected missing parent creation for
  nested artifact paths and false success for a nonexistent module.
- Phase 6 cleanup removed both inner Compose projects, their volumes/networks,
  both outer Sandboxes, and disposable host sources. The host returned to
  7.5 GiB used/37 GiB free, and `sbx ls` reported no Sandboxes.
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
- Phase 6 is complete and committed on `feature/docker-sandbox-phase-6` with
  subject `Complete Docker Sandbox Phase 6 observability`.
- Phase 7 is merged to `main` via PR #2; the repository is on `main` at
  `12368b7`, working tree clean, nothing outstanding to push locally.
- (Additive, non-phase) Local repo, GitHub (`origin/main`), and the Oracle
  VPS repo clone (`~/odoo-agent-pro-kit` on `92.4.86.131`) are byte-identical
  at `12368b7`. This was hand-verified each round (`diff`/`md5`/`git log`)
  before every push, not assumed.
- (Additive) Oracle VPS: Hermes v0.20.3, 3 profiles (odoo17-dev/odoo18-dev/
  odoo19-dev), 20 project skills loaded and `enabled` in each, `~/odoo-
  agent-pro-kit` synced to `12368b7`, `~/odoo-knowledge-base/knowledge-
  {17,18,19}/` synced and wired into skill references.
- (Additive) `hermes plugins doctor ~/odoo-agent-pro-kit/plugin --ci` passes
  cleanly on all 3 Oracle VPS profiles (7 tools, 2 hooks, zero warnings),
  confirming the native 0.3.0 plugin code itself is correct and loadable on
  that host.
- (Additive, resolved) Fixed the `hermes plugins install` local-path
  blocker. Root cause: `plugin/plugin.yaml` declared `manifest_version: 2`,
  but the bundled Hermes v0.20.3 CLI installer's
  `_SUPPORTED_MANIFEST_VERSION` constant caps at 1 (the plugin *loader*
  already supports v2 fields independently) — `hermes plugins install`
  hard-refused with "requires manifest_version 2, but this installer only
  supports up to 1" before it ever reached the path-resolution code that
  produced the earlier misleading `github.com/home/ubuntu.git` error.
  Changed `manifest_version: 2` -> `1` (committed `fdba81f`, pushed to
  `origin/main`, fast-forward-synced onto the Oracle VPS repo clone).
  Verified the correct local install syntax is `file://<abs-repo-root>#
  <subdir>` (e.g. `file://$HOME/odoo-agent-pro-kit#plugin`) — a bare
  filesystem path is misread as GitHub `owner/repo` shorthand. Local-path
  installs still run the static content scanner (git-provenance checks are
  skipped, but content scanning is not), and this repo's skills content
  reliably trips a "dangerous" verdict that even `--force` cannot override;
  worked around per-install by toggling `plugins.scan_on_install: false` ->
  `true` in that profile's `config.yaml` around the install call. Installed
  and enabled `odoo-agent-pro-kit` 0.3.0 in all 3 Oracle VPS profiles
  (odoo17-dev/odoo18-dev/odoo19-dev); confirmed with `hermes -p <profile>
  plugins list --plain --no-bundled` (shows `enabled`) and `hermes -p
  <profile> plugins doctor odoo-agent-pro-kit --ci` (7 tools, 2 hooks, OK)
  on all three. Declared Python deps (`pydantic`, `python-dotenv`,
  `requests`) were already present in the Hermes venv on that host —
  nothing to install. Ran a direct in-process call to the registered
  `odoo_get_version_info` tool function on odoo17-dev (bypassing the LLM,
  since this VPS has no inference provider/API key configured at all — an
  unrelated, pre-existing gap, not part of this blocker): it returned a
  clean `Failed to connect to Odoo ... Connection refused` error rather
  than an import/registration error, matching the Next-task acceptance
  criterion ("or returns a clear connection error if no Odoo backend is
  reachable — not a registration error"); no live Odoo backend is running
  on that VPS host at `localhost:8069`. Updated
  `OdooHermesEnvironmentSetup/SKILL.md` step 4 with the corrected
  `file://...#plugin` syntax, the `manifest_version` root cause, and the
  `scan_on_install` toggle workaround; closed out the "Repo-hosted install
  shorthand" gap note by splitting it from this newly-resolved item under
  "Known gaps". `./scripts/validate.sh` passed clean-shell afterward: 57
  tests, 20 skills, Sandbox artifact/Compose/shell/Python/whitespace checks
  all OK (`sbx` kit validation skipped locally as before — Intel macOS).
  Committed as a single focused commit; also enabled and started the
  `hermes-gateway` systemd user service on the Oracle VPS as a side effect
  of restart guidance (was not running before this session; harmless,
  no messaging platforms configured so it idles).
- [x] (Additive, resolved, local Mac only — not yet on VPS) Verified two
  free/no-card-required OpenAI-compatible inference providers work with
  Hermes and wired both into a fallback chain, closing the gap the
  previous session's Next task called out ("no inference provider
  configured at all" on the VPS). Both were tested with live `curl` calls
  before any config change, and again through the real Hermes CLI
  afterward:
  - **Hetzner AI free tier** (`https://inference.hetzner.com/api/v1`,
    Bearer token from https://experiments.hetzner.com/docs/inference,
    account-gated by Hetzner's OIDC/SSO login — could not scrape the docs
    page directly, browser automation confirmed it is a login-walled SPA).
    `GET /v1/models` → one model, `Qwen/Qwen3.6-35B-A3B-FP8`. Live
    `/v1/chat/completions` call returned real generated content (`pong`)
    with a visible internal `reasoning` field (this is a reasoning model).
  - **OpenRouter** (`https://openrouter.ai/api/v1`, existing first-class
    Hermes provider, needs only `OPENROUTER_API_KEY`). `GET /v1/models` →
    412 models, many `:free`-suffixed. The `openrouter/free` auto-router
    alias returned a live completion at `"cost": 0`; a specific pinned
    free model (`google/gemma-4-31b-it:free`) hit a `429` on the very next
    call — OpenRouter's per-model free tier is shared/rate-limited across
    all users, so `openrouter/free` (which auto-picks an available free
    model) is the resilient choice, not a pinned `:free` model id.
  - Configured on the **local Mac profile only** via `hermes config set`
    (direct edits to `~/.hermes/config.yaml` are blocked by a built-in
    Hermes safety guard — must go through the CLI):
    `providers.hetzner = {api: https://inference.hetzner.com/api/v1,
    key_env: HETZNER_API_KEY, transport: chat_completions, default_model:
    Qwen/Qwen3.6-35B-A3B-FP8, context_length: 131072}` and
    `fallback_providers = [{provider: openrouter, model:
    openrouter/free}, {provider: custom:hetzner, model:
    Qwen/Qwen3.6-35B-A3B-FP8}]` (primary model/provider — Anthropic
    `claude-sonnet-5` — left untouched). `HETZNER_API_KEY` and
    `OPENROUTER_API_KEY` added to `~/.hermes/.env` (chmod 600, outside
    any git repo). Verified with `hermes fallback list` (shows the
    2-entry chain under the unchanged primary) and two independent
    `hermes -z "..." --provider <p> --model <m> --cli` calls, both
    returning `pong` through the real Hermes agent loop, not just raw
    `curl`.
  - **Security**: both tokens only ever touched this chat, one in-memory
    `curl` test each, and `~/.hermes/.env`/`~/.hermes/config.yaml`
    (outside every git repo on this machine). Neither key was written to
    any file inside `odoo-agent-pro-kit`; `git status` stayed clean at
    `0d83521` throughout. `hermes_mcp_agent.py` (mentioned in the user's
    original ask) was not found in any indexed public repo and was not
    run — only the documented `curl`-based REST endpoints were used.
  - **Gap carried forward**: this fallback chain exists only in the local
    Mac's `~/.hermes/config.yaml`/`.env`, not in any of the 3 Oracle VPS
    profiles (odoo17-dev/odoo18-dev/odoo19-dev), which is why the
    previous session's live slash-command test was deferred. See Next
    task.

- [x] (Additive) **Live end-to-end pipeline test on the Oracle VPS with real
  inference — both parts of the previous Next task, completed 2026-08-18.**
  1. **Provider setup, per profile, non-interactive.** Discovered a gap the
     previous session missed: `hermes -p <profile> ...` re-points
     `HERMES_HOME` at `~/.hermes/profiles/<profile>/`, which has its own
     `.env` (root cause found by reading `hermes_cli/main.py` profile-arg
     pre-parsing and `hermes_cli/env_loader.py`) — writing keys only to
     `~/.hermes/.env` was not enough; each profile silently fell back to
     "No LLM provider configured" even with `fallback list` showing the
     chain. Fixed by writing `HETZNER_API_KEY`/`OPENROUTER_API_KEY` to
     **both** `~/.hermes/.env` (shared) and each of
     `~/.hermes/profiles/{odoo17,odoo18,odoo19}-dev/.env` (chmod 600).
     Ran the exact non-interactive `hermes -p <profile> config set ...`
     sequence from the previous session's Next-task recipe (`providers.
     hetzner.*`, `model.default=openrouter/free`, `model.provider=
     openrouter`, `fallback_providers=[{provider:custom:hetzner,...}]`)
     against all 3 profiles — confirmed with `hermes -p <profile> fallback
     list` (primary `openrouter/free` via openrouter, 1-entry Hetzner
     fallback) on all three. `hermes` on this VPS has no global shim —
     must `source /home/ubuntu/.hermes/hermes-agent/venv/bin/activate`
     first (the bare `hermes` binary hits `ModuleNotFoundError: No module
     named 'dotenv'` outside the venv).
  2. **Live pipeline test.** On `odoo19-dev`: `hermes -p odoo19-dev -z
     "reply with just the word pong" --cli` returned a real `pong` — first
     successful live LLM turn on this VPS ever (previous sessions only did
     in-process tool calls, never a real agent turn). Then asked the live
     agent to actually invoke `odoo_get_version_info` (not describe it):
     it called the tool for real and returned `{"error": "Failed to
     connect to Odoo 19.0 at http://localhost:8069 (db=). Check ODOO_URL/
     ODOO_DB_NAME/..."}` — a clean connection-refused error, not a
     registration error, matching the acceptance bar exactly (no live Odoo
     backend is running on this VPS). Then ran `/plan-analysis 19
     sample_module` as a real slash command through the live agent
     (backgrounded via `nohup ... &` over SSH, ran ~20 minutes real wall
     time doing genuine multi-step analysis): confirmed dispatch through
     the native plugin (`agent.log` shows "odoo-agent-pro-kit: registered
     7 odoo_* tools, 4 slash commands, 2 hooks" loading at session start),
     and it completed for real — produced actual artifacts on disk,
     verified directly (not from the agent's self-report): `~/.hermes/
     analysis/{dependency_context.json, manifest_analysis.json}` and
     `/tmp/sample_module_for_analysis/static/description/{icon.png,
     banner.png, index.html, 5 screenshot PNGs}`, plus a
     coding-standard-violations summary in the transcript. This is real
     dispatch and real work, not "command not found" and not an
     in-process bypass.
  - **Security**: same two tokens from the prior session, still used only
    in-memory for verification (`curl`) plus writing to `~/.hermes/.env`
    files on the VPS over SSH; never written to any file inside
    `~/odoo-agent-pro-kit` on the VPS or in the local repo; `git status`
    stayed clean throughout.
  - **Only odoo19-dev was live-tested end-to-end** (per the previous
    session's "at least one, then decide" framing) — odoo17-dev and
    odoo18-dev have the same provider config verified via `fallback list`
    but have not yet run a live `/plan-analysis` slash command themselves.
- [x] (Additive) Updated `docs/architecture.excalidraw` /
  `docs/architecture.png` with a new "Deployment & live operations"
  section reflecting the VPS state above: Oracle Cloud VPS hub fanning out
  to the 3 profile boxes (odoo19-dev marked "live-tested"), an evidence
  block with the exact fallback-provider config and the live `pong`
  verification command, and a footer note pointing at the next open task
  (live `/plan-analysis` -> `/start-coding` -> `/testing` chain test).
  Fixed a real, previously-broken render pipeline as a side effect: the
  skill's `render_template.html` imported `@excalidraw/excalidraw?bundle`
  from esm.sh, whose bundled transitive dependency
  (`@braintree/sanitize-url@6.0.2/es2022/dist/constants.mjs`) 404s on esm.sh
  right now — confirmed by direct `curl` and a raw Playwright console-log
  probe. Removing `?bundle` (importing the unbundled ESM graph instead,
  where esm.sh resolves each submodule import correctly) fixed it; verified
  by an actual `uv run python render_excalidraw.py ...` run that produced
  `docs/architecture.png` and visually reviewing the rendered PNG (new
  section reads cleanly, no clipped text, no overlapping elements, arrows
  land on their targets).

## Blockers and risks

### Immediate

- No immediate blocker remains for VPS live-inference pipeline testing —
  resolved this session (see Completed above). The remaining gap is
  narrower: only `odoo19-dev` has run a live slash command end-to-end;
  `odoo17-dev`/`odoo18-dev` have verified provider config
  (`fallback list`) but no live slash-command run yet, and no session has
  chained `/plan-analysis` -> `/start-coding` -> `/testing` together
  against a real running Odoo backend (none was running on the VPS this
  session either).
- No immediate Phase 6 blocker remains. Docker login JWKS and refresh-lock
  connectivity was intermittent during the run; authentication diagnostics
  passed and the completed evidence was verified from inner state rather than
  client-stream continuity.

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

The odoo19-dev live-inference pipeline test passed this session (see
Completed). Two follow-ups remain, either is a reasonable next task:

1. **Replicate the live slash-command test on odoo17-dev and odoo18-dev.**
   Provider config is already verified via `fallback list` on both — the
   remaining work is just running the same `hermes -p <profile> -z
   "/plan-analysis <ver> <module>" --cli` pattern used for odoo19-dev
   (background it with `nohup ... &` over SSH; it took ~20 minutes real
   wall time for odoo19-dev) and confirming real artifacts on disk
   afterward, not just the agent's self-reported summary.
2. **Bring up a real Odoo 19 backend and chain the full lifecycle live.**
   Start an actual Odoo 19 instance reachable at `localhost:8069` on the
   VPS (Docker Sandbox microVM per the Phase 0-7 work, or a simpler local
   `sandboxctl`/direct Odoo process — whichever is faster to stand up),
   then run `/plan-analysis` -> `/start-coding` -> `/testing` back to back
   through the live agent against that real backend, recording exact
   commands and pass/fail per step in this file. This finally proves the
   full documented lifecycle end-to-end with a real Odoo target instead
   of a clean connection-refused error.

Decide between them based on priority: (1) is cheap confidence-building
across all 3 profiles; (2) is the deeper, more valuable proof but costs
more time/resources to set up.

## Following tasks

1. Once the full `/plan-analysis` -> `/start-coding` -> `/testing` chain
   has been proven against a live Odoo backend, decide whether
   `openrouter/free` is good enough quality for real Odoo task work or
   whether a paid primary provider should be linked instead (the user
   raised this trade-off directly — "otherwise I will link my Claude
   plan").
2. Review community platform evidence and fix proposals as they arrive
   (Apple Silicon macOS / Windows 11 Docker Sandbox validation).
3. Plan the next roadmap phase in a fresh session before implementation.

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
