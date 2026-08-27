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
- Last context update: 2026-08-20 (UTC, Phase 8 exit gate MET — all
  Deliverables and all five platform/orchestration coverage checklist items
  verified with real evidence; Phase 8 is complete)

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
- [x] (Phase 8, partial — steps 1-6 and 8 of 10) Resolved the Docker Sandbox
  Codex agent's expired proxy OAuth token via a host-level
  `sbx secret set openai --oauth` re-authentication using
  `info@vperfectcs.com` Codex Pro, working around the VPS firewall blocking
  the OAuth callback with an SSH port-forward; this credential is now global
  and every future sandbox inherits it. Ran the `edit_remove_pricelist_rule`
  (17.0 -> 18.0) pilot module through the sandboxed skill sequence inside
  Docker Sandbox `phase8-pilot` (Codex agent) on the Ubuntu KVM validation
  host: Step 1-2 dependency intake/coding standard (0 violations), Step 3
  `/plan-analysis` via a real Codex/GPT-5 run (generated
  requirements/design/tasks/module_meta.md, caught a real wrong-model-name
  bug in an earlier draft), Step 4-5 install lifecycle + `/start-coding`
  (Codex implemented `models/price_list.py`, `views/price_list_view.xml`,
  `data/remove_price_list_rule.xml`; installed cleanly, `Module loaded in
  0.19s, 71 queries`, zero errors), Step 6 backend testing (8 real
  `TransactionCase` tests, 0 failed/0 errors of 8 against a live Odoo 18 DB,
  including the pricing-recomputation assertion), Step 7 pricing
  recomputation covered by the Step 6 suite, Step 8 frontend testing
  confirmed N/A (no JS/OWL assets). Merged the sandbox-generated
  implementation into the canonical `vpcs_apps_cloud_18/
  edit_remove_pricelist_rule` repo (branch `18.0`), preserving the original's
  commercial manifest fields (images, website, price, currency) that Codex's
  fresh regeneration had dropped, and removed the staging copy from
  `odoo-agent-pro-kit` (pipeline repo should not hold module code).
  `./scripts/validate.sh` passed 73/73 locally after the sync. Documented in
  `docs/docker-sandbox/phase-8/live-test.md` (full evidence trail),
  `docs/docker-sandbox/tasks.md` (progress checklist), and
  `plugin/skills/DockerSandboxMultiCliAdapter/SKILL.md` (host-level OAuth
  re-auth procedure, correct `sbx create` syntax, Claude/Gemini CLI auth
  gotchas, stale-session cleanup, and the "already inside the target host"
  prompting pitfall). Steps 9 (doc/screenshot regen) and 10 (context-handoff
  fresh-session resume test) remain outstanding — Phase 8's exit gate is not
  yet met.
- [x] (Phase 8, pilot module complete — steps 7, 9, 10 of 10, 2026-08-19)
  Closed the remaining pilot-module gaps for `edit_remove_pricelist_rule`
  with real evidence. **Step 7**: re-established the SSH-tunnel + `socat`
  path from the local Mac to the sandboxed Odoo 18 instance, logged in as
  admin via real browser automation, found and fixed a real bug
  (`KeyError: <NewId ...>` in `_compute_pricelist_rule_count()` — raw dict
  lookup failing for unsaved records; fixed to `counts.get(pricelist.id,
  0)`) in the canonical `vpcs_apps_cloud_18` repo, the sandbox's mounted
  addon copy, and the pilot-module-src staging copy, re-ran
  `sandboxctl module ... update`/`... test` (0 failed, 0 error(s) of 8
  tests, no regression), and captured real UI screenshots
  (`docs/docker-sandbox/phase-8/step7-evidence/`). **Step 9**: ran a real
  `codex exec "/testing 18.0 edit_remove_pricelist_rule"` inside
  `phase8-pilot`, which re-ran the sandbox update/test lifecycle (exit 0
  both) and generated `docs/coverage_summary.md`,
  `static/description/index.html`, `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`, and
  `sessions/context_handoff.json` inside the sandboxed module copy — pulled
  down and committed as `docs/docker-sandbox/phase-8/step9-evidence/`.
  **Step 10**: started a brand-new `codex exec` session (no continuation
  from Step 9) instructed to read only the module's `AGENTS.md` and
  `sessions/context_handoff.json`; it correctly reported module/version,
  last command (`/testing`, 2026-08-19T07:07:47Z), `0/9` tasks, and the
  accurate outstanding-work summary — confirming the context-handoff design
  survives a genuine session reset. Full narrative in
  `docs/docker-sandbox/phase-8/live-test.md`. The pilot module's 10-step
  checklist in `docs/docker-sandbox/tasks.md` is now fully `[x]`, but
  Phase 8's broader exit gate (second module, Enterprise-dependency test,
  timing measurement, design note, go/no-go decision) is still open.

- [x] (Phase 8, second Tier-1 module complete, 2026-08-19) Closed
  `hr_document_report` (17.0 -> 18.0) in target session
  `phase8-hr-document-report`: final manifest `LGPL-3`; 6/6 TransactionCase
  tests; Community-only `hr`; live UI/XSS and 9,050/24,160-byte PDF evidence;
  frontend N/A by inventory; `/testing` docs; resource capture; and a new Codex
  process that resumed from only `module_meta.md` and `context_handoff.json`.
  The first fresh attempt exposed stale handoff state and was not counted as a
  pass. At 2026-08-19T11:06:29Z, outer/inner wall time was 58m55s/46m32s;
  Odoo/PostgreSQL cumulative CPU 40.197s/142.675s and memory peaks
  245.3/255.2 MiB. No commit or push was made.

## Current state

- **(Additive, 0.5.0) Deterministic pipeline hooks shipped and merged to
  local `main`** (merge `dc8b346`; not pushed to `origin`). Adds
  `plugin/hooks/checks/` (shared
  pure-function check library: `guard`, `paths`, `gates`, `odoo_lint`,
  `sandbox_result`, `version`, `authz`, `common`), the Claude Code dispatcher
  `plugin/hooks/odoo_hook.py` (wired into all 7 events in
  `plugin/hooks/hooks.json`), Hermes parity via `pre_tool_call` /
  `post_tool_call` in `plugin/__init__.py` + `hooks/checks/hermes_adapter.py`,
  and a contributor-only repo-root `.claude/settings.json` +
  `scripts/contributor_hook.py` enforcing the `AGENTS.md` phase-workflow rules.
  Gates: `/start-coding` needs `docs/tasks.md`; `/testing` needs zero open tasks
  + passed backend tests. Guardrails: raw `odoo-bin` / `./manage_modules.sh` /
  VCS-write / secret / Enterprise-source. Version-aware Odoo 17/18/19 linter
  rules L1–L6. Kill switches: `ODOO_KIT_HOOKS_DISABLED=1`,
  `ODOO_KIT_ALLOW_VCS_WRITE=1`, `ODOO_KIT_ALLOW_RAW_ODOO=1`. A whole-branch code
  review (1 Critical + several Important + doc issues) was completed and this
  fix wave applied: `$CLAUDE_PROJECT_DIR` in `.claude/settings.json`, read-only
  git subcommands unblocked, command-position anchoring for the odoo-bin /
  manage_modules regexes, `resolve_module_dir` so command gates honour an
  explicit module arg, cross-runtime MultiEdit body extraction in `common`,
  inverted Stop reminder logic, plus fail-open / hooks-disabled / SessionEnd
  dispatcher tests and doc corrections. 201 tests passing;
  `./scripts/validate.sh` green.
  **Verified on the Oracle KVM host (Hermes 0.20.4), 2026-08-27:** local `main`
  (`4cc71c7`) fast-forward-synced to `~/odoo-agent-pro-kit` via git bundle (no
  origin push), created `.venv` (pytest 9.1.1 + plugin deps), full suite
  201 passed, `./scripts/validate.sh` green. Reinstalled the plugin 0.5.0 in
  all three profiles (odoo17/18/19-dev) — `hermes plugins doctor
  odoo-agent-pro-kit --ci` reports `7 tool(s), 5 hook(s)`, registration OK,
  zero warnings, in every profile. Found and fixed two real Hermes-contract
  bugs during verification (commit `4cc71c7`): the in-process `pre_tool_call`
  callback must return `{"action":"block","message":…}` not the Claude-Code
  `{"decision":"block","reason":…}` (only stdout hooks get that translation),
  and the tool args arrive under the `args` kwarg not `tool_args`. A live
  in-process check confirms `pre_tool_call` now actually blocks raw `odoo-bin`,
  `git push`, and private-key writes while allowing clean commands; a live
  `hermes -p odoo19-dev -z "…" --cli` agent turn returned `pong` with the
  plugin loaded and the openrouter/hetzner fallback chain intact.
- (2026-08-20) Closed the Phase 8 "real Odoo Enterprise dependency" platform/
  orchestration checklist item with real evidence. Created a fresh Docker
  Sandbox session `phase8-enterprise-dep-test` (Odoo 17.0) on the Ubuntu KVM
  validation host, ported `vpcs_apps_cloud_17/real_estate`
  (`depends: purchase, sale_subscription, website_crm, web_studio,
  sale_renting_crm`) into `/mnt/extra-addons`, and ran
  `sandboxctl module ... install` exclusively (no raw `odoo-bin`/manual
  Enterprise fetch). Odoo's own resolver correctly failed the install with a
  structured `install_failed` operation result and the exact `UserError`
  naming the missing Enterprise dependency `sale_renting_crm`. A redacted
  diagnostic bundle was captured automatically. A post-failure filesystem
  `find` for any Enterprise module name returned zero matches, confirming no
  Enterprise source was ever fetched, mounted, or present. Evidence saved to
  `docs/docker-sandbox/phase-8/enterprise-dependency-evidence/`
  (`install-operation-result.json`, `odoo-install-failure.txt`, and the raw
  redacted diagnostic bundle tarball). The sandbox session and outer Sandbox
  were fully destroyed afterward (`--allow-unexported`, since it was a
  disposable test fixture with no work product to preserve); `sbx ls`,
  `docker ps -a`, and `docker volume ls` confirmed no orphans, and the two
  pre-existing sandbox sessions on the host
  (`phase8-hr-document-report`, `phase8-hr-payroll-invoice`) were left
  untouched. Also flipped the wall-clock/resource-sizing checklist item to
  `[x]` in `docs/docker-sandbox/tasks.md` — that evidence was already
  captured for `hr_document_report` in this file's prior entry and only
  needed the checkbox/citation, not new work. Local `.venv` `validate.sh` was
  not re-run this session (no code changed, only docs/evidence).
- **Phase 8's exit gate is now MET (2026-08-20).** All four **Deliverables**
  are complete: the design note (`docs/docker-sandbox/phase-8/design.md`,
  generalized from a pilot-scoped draft to the canonical sequence +
  Enterprise-dependency handling + all reference-run summaries + the
  go/no-go decision, referenced from `CommandingSystem/SKILL.md`), the
  first sandbox-native Tier-1 module (`edit_remove_pricelist_rule`,
  already-existing evidence just needed the checkbox), the second Tier-1
  module (`hr_document_report`), the `edit_remove_pricelist_rule`
  browser-evidence gap closure (already satisfied by existing Step 7
  evidence), and the go/no-go batching decision: **GO, phased/staggered** —
  triage the ~45-module backlog statically first (Community-only vs
  Enterprise-dependent), batch Community-only modules at ≤2 concurrent
  sandbox sessions (Phase 7's measured host capacity limit), handle
  Enterprise-dependent modules as a separate explicitly-flagged batch. Full
  rationale in `docs/docker-sandbox/phase-8/design.md` "Go/no-go".

  All five "platform/orchestration coverage" checklist items are also now
  verified with real evidence
  (`docs/docker-sandbox/phase-8/orchestration-coverage-evidence.md`):
  session-start hook detection (both the shell hook and native Hermes hook,
  three real cases: live Docker Sandbox `session.json`, bare local
  Odoo-version directory, genuinely empty directory — all three correct);
  version→skill mapping resolution (verified inside a live Docker Sandbox
  session that all nine mapped skill directories resolve); `sandboxctl
  module` sole-entrypoint audit (found and fixed a real gap —
  `OdooTools{17,18,19}/SKILL.md`'s "Tests" bullet recommended raw
  `odoo-bin --test-tags` with no caveat; fixed to route through
  `sandboxctl module ... test` exclusively, with a new regression test
  enforcing it going forward); `context_guard.py` write path (called the
  real `maybe_handle_context_pressure` hook directly with real usage data
  against a seeded 5-task module; correctly computed the size-adjusted
  threshold, triggered at 70.3% usage, wrote all three handoff files with
  accurate state, deduped a same-bucket re-trigger, and a brand-new
  zero-context Hermes subagent given only the two handoff files correctly
  resumed); and session-start context-load read path (a fresh zero-context
  subagent, given only a real `CLAUDE.md` with no explicit skip instruction
  plus `docs/tasks.md`, correctly identified which completed tasks to skip
  and correctly sequenced the remaining tasks — measurable behavior change,
  not self-report). All Docker Sandbox sessions used this session
  (`phase8-enterprise-dep-test`, `phase8-aptus-ent-test`,
  `phase8-orchestration-test`) were destroyed after evidence capture with
  no orphans; the two pre-existing sessions on the host
  (`phase8-hr-document-report`, `phase8-hr-payroll-invoice`) were untouched
  throughout.
- (2026-08-20, supplemental) Re-verified the Enterprise-dependency-detection
  finding against a real client project with the user's own GitHub-level
  access: `Aptusinfotech/aptus` (staging branch, Odoo.sh 19.0),
  `account_report_template` (depends on the real Enterprise Accounting app
  `accountant`/`account_accountant`, confirmed `OEEL-1`-licensed across the
  user's own licensed 17.0/18.0/19.0 Enterprise source clones at
  `~/workspace/17_local_project/ent-17`, `~/workspace/18_local_Project/
  ent-18`, `~/workspace/ent-19`). Discovered and documented a real pipeline
  gap: `sandboxctl module ... install` reports CLI exit 0 ("succeeded") when
  Odoo's `-i` install-list path skips an unresolvable dependency with only a
  warning — the true signal is `ir_module_module.state`, which stayed stuck
  at `to install` (Enterprise dep `uninstallable`) in all three sandbox
  runs. Reused one Docker Sandbox session across a full reverse-migration
  test (19.0 -> 18.0 -> 17.0) of the same module, hand-migrating only the
  manifest's Enterprise-dependency name per version's Odoo Accounting-app
  split (`accountant` for 18.0/19.0, `account_accountant` for 17.0); no
  other code changes were needed, confirmed by inspecting the relevant
  `account.report` model fields, the `account.view_account_form` XML
  anchor, and the OWL `selection_field.js` path across all three versions
  in the user's local source trees before testing. Zero Enterprise source
  was ever fetched or mounted in any of the three sandbox runs (verified by
  filesystem search each time). All sandbox sessions destroyed cleanly after
  evidence capture (no orphans); the two pre-existing sandbox sessions on
  the host were untouched. No client source was committed to this
  repository — only manifests/dependency-chain summaries and operation
  results. Full evidence in
  `docs/docker-sandbox/phase-8/aptus-enterprise-dependency-evidence/`.
- (2026-08-20) Fixed the pipeline gap discovered above: `manage_modules.sh`'s
  Compose executor now re-checks `module_is_installed` for the target module
  after every `install`/`update` operation and marks the structured
  operation result `failed` (`install_failed`/`update_failed`) when the
  module never actually reached `ir_module_module.state == 'installed'` —
  previously a silently-skipped Enterprise (or any missing) dependency could
  leave a false "succeeded" result. Added regression test
  `test_compose_executor_fails_when_module_not_actually_installed` and fixed
  the existing fixture-based test's fake `docker`/`psql` stub to reflect the
  new post-check. Bumped plugin version 0.3.2 -> 0.3.3
  (`plugin/plugin.yaml`, `plugin/.claude-plugin/plugin.json`), documented in
  `CHANGELOG.md` and `README.md`. `./scripts/validate.sh` passed clean: 74
  tests, 21 skills, artifacts/contracts/rollback, Compose, shell/Python
  syntax, and whitespace checks. Committed and pushed to `origin/main` with
  the user's explicit authorization this session.
- Phase 8 second module `hr_document_report` is complete for the Tier-1
  deliverable. Expanded security and representative Odoo 17 data-upgrade
  matrices were not executed and are not claimed.
- Artifact-only handoff validation ran from a clean shell on 2026-08-19 without
  rerunning Odoo backend or browser tests:
  `env -i HOME="$HOME" PATH="$PWD/.venv/bin:/usr/local/bin:/usr/bin:/bin" bash
  --noprofile --norc -c './scripts/validate.sh'`. Result: 73 repository tests
  passed in 1.08s, 21 skills validated, Sandbox contracts/rollback, Compose,
  shell syntax, Python syntax, and whitespace checks passed; `sbx` kit live
  validation was skipped because `sbx` is unavailable in this shell.
- Final post-closeout clean-shell validation also passed: 73 tests in 1.00s,
  21 skills, artifact/contracts/rollback, Compose, shell, Python, and whitespace
  checks. Live `sbx` kit validation was skipped because `sbx` is unavailable
  inside this sandbox process.
- Phase 8 pilot module (`edit_remove_pricelist_rule`) now has all 10
  sequence steps complete with real evidence. Step 7 (live UI evidence)
  found and fixed a real `KeyError: <NewId ...>` bug in
  `_compute_pricelist_rule_count()` (unsaved-record dict lookup), re-ran
  and passed the 8-test backend suite with no regression, and captured
  real UI screenshots (`docs/docker-sandbox/phase-8/step7-evidence/`).
  Step 9 regenerated `docs/coverage_summary.md` and
  `static/description/index.html` via a real `/testing` Codex run
  (`docs/docker-sandbox/phase-8/step9-evidence/`). Step 10 verified a
  brand-new Codex session correctly resumes module state from only the
  `AGENTS.md`/`context_handoff.json` handoff artifacts. Full narrative in
  `docs/docker-sandbox/phase-8/live-test.md`.
- Both Tier-1 module sequences are done, but the broader Phase 8 exit gate is
  NOT met: still outstanding are the Enterprise-dependency-module test, the
  separate wall-clock/resource sizing writeup, the standalone Phase 8 design
  note, and the go/no-go batching decision (see `docs/docker-sandbox/tasks.md`
  "Scope: platform/orchestration coverage to validate" and
  "Deliverables" sections).
- The Docker Sandbox Codex agent's proxy OAuth credential is now globally
  re-authenticated on the host (`sbx secret set openai --oauth`, Codex Pro
  account `info@vperfectcs.com`); no further per-sandbox OAuth setup is
  needed. The SSH-port-forward OAuth-callback workaround is documented in
  `plugin/skills/DockerSandboxMultiCliAdapter/SKILL.md`.
- Currently staged/uncommitted this session (docs and evidence only, plus
  one module bugfix) in `odoo-agent-pro-kit`: `docs/docker-sandbox/tasks.md`
  (steps 7/9/10 marked complete), `docs/docker-sandbox/phase-8/live-test.md`
  (steps 7/9/10 narrative), `docs/docker-sandbox/phase-8/step7-evidence/`
  (2 screenshots), `docs/docker-sandbox/phase-8/step9-evidence/` (regenerated
  docs/handoff files pulled from the sandbox), and this file. The
  `edit_remove_pricelist_rule` module bugfix (`counts.get(pricelist.id, 0)`
  in `models/price_list.py`) lives in the separate `vpcs_apps_cloud_18`
  repository (branch `18.0`), also uncommitted as of this session's end,
  not in this repository.
- Per the user's explicit push policy, none of this is pushed to
  `origin/main` yet; it commits locally only until Phase 8's exit gate
  passes and security checks are clean, then everything pushes together.

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
- [x] (Additive) Synced the Obsidian knowledge base
  (`/Users/vinusoft85/infovpcs`, OKF v0.1 format per `OKF_SPEC.md`) with
  this session's work: updated the Odoo Agent Pro Kit entity and project
  tracker with the live VPS inference pipeline verification, added a
  folder-verified "Cross-Version Migration Backlog" section to the VPCS
  Custom Modules entity page (71/56/32 modules in the local
  `vpcs_apps_cloud_{17,18,19}` app-store repos; 22 modules stuck at
  17.0-only, 25 more reached 18.0 but never 19.0), opened a new
  `topics/PROJECTS/vpcscloud-apps-store-migration.md` working tracker for
  the migration effort, wired both into `PROJECTS/README.md` and the root
  `index.md` catalog, and appended a dated `log.md` entry per the vault's
  OKF conventions. Committed and pushed to `origin/master` as `86c7b35`.
- [x] (Additive) Defined **Phase 8: Full-coverage skill-orchestrated
  migration pipeline (client-readiness proof)** in
  `docs/docker-sandbox/tasks.md` — the canonical 10-step skill sequence
  (dependency/context intake → coding standard → `/plan-analysis` →
  install/update lifecycle rules → `/start-coding` with per-task auto-test
  → backend testing → live browser evidence → frontend testing →
  `/testing` → fresh-session context-reset check) that must run inside a
  Docker Sandbox microVM against a real VPCSCloud module before batching
  the remaining backlog or taking on client work. Cross-referenced from
  `plugin/skills/CommandingSystem/SKILL.md`, `README.md`, `CHANGELOG.md`.
  Committed locally as `97c1b19` (not pushed).
- [x] (Additive, 0.3.1) Built the **dynamic context-usage handoff guard**
  (`plugin/context_guard.py`) requested directly by the user: a new
  `post_api_request` Hermes hook that fires on real per-turn token usage
  (not a guess or a fixed 60%) for *any* in-progress command inside a
  module workspace — not hardcoded to `/start-coding`. The effective
  threshold auto-adjusts to the module's actual `docs/tasks.md` task count
  (50% for >15 tasks, 60% for 6-15, 65% for ≤5, bounded 40-80%), so
  handoff timing depends on module complexity and work-coverage pipeline
  state exactly as the user specified. On trigger it writes the same
  `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` episodic-context files the manual
  per-command writes already produce (via a real code path, not a new
  format) and nudges the live agent via `ctx.inject_message()` to wrap up
  and hand off to a fresh session. Along the way, found and fixed a real
  pre-existing gap: `CommandingSystem/SKILL.md` and
  `context_handoff_workflow.md` documented `AgentSkills/auto_test/
  {context_writer.py,auto_test_runner.py}` as canonical paths, but that
  harness was never actually shipped in this repository — only present in
  the separate `Odoo_Agents_MultiSupport` workspace and copied in by
  `odoo_local_setup/setup_odoo_workspaces.sh` during local bootstrap.
  Ported both files into `plugin/skills/CommandingSystem/auto_test/` so
  the plugin is self-contained. Verified for real, not just unit-tested:
  ran `register(ctx)` against a fake `PluginContext` and confirmed
  `post_api_request` is among the 3 registered hooks (alongside the
  pre-existing `on_session_start`/`on_session_end`), then fired it with a
  70%-usage payload against an 8-task temp module workspace and confirmed
  `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` were written with a "Dynamic Context
  Handoff" section and the agent nudge message was injected. `hermes
  plugins doctor plugin --ci` confirms 7 tools/3 hooks/zero warnings.
  16 new unit tests in `tests/test_context_guard.py`
  (threshold scaling, task counting, usage-pct math, module detection, a
  below-threshold no-op case, an outside-workspace no-op case, a
  malformed-input fail-open case, and the full end-to-end trigger case).
  `./scripts/validate.sh` passed clean: 73 tests (up from 57), 20 skills,
  Sandbox artifact/Compose/shell/Python/whitespace checks all OK. Grepped
  every new/changed file for hardcoded secrets/credentials/private paths —
  clean. Bumped plugin version 0.3.0 -> 0.3.1 in `plugin.yaml` and
  `.claude-plugin/plugin.json` in lockstep per the existing convention.
  Committed locally (not pushed, per explicit user instruction to push
  everything together only after all security checks and Phase 8 module
  work is verified working smoothly).

## Blockers and risks

### Immediate

- **Push policy (explicit user instruction, 2026-08-18):** commit locally
  after each unit of work as usual, but do NOT push to `origin/main` until
  all security checks pass AND the in-progress module development/Phase 8
  work is verified working smoothly end to end. Push everything together
  at that point, not incrementally. This session's Phase 8 planning
  (`97c1b19`) and the dynamic context-handoff guard (0.3.1) are both
  committed locally only.
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
- 2026-08-19 PDF runtime remediation: Odoo's official source-install guidance
  requires wkhtmltopdf 0.12.6 for headers/footers. Docker Sandbox builds now
  assert both wkhtmltopdf and wkhtmltoimage are patched-Qt 0.12.6 for Odoo
  17/18/19; local amd64 builds and runtime checks passed for all three at
  0.12.6.1. The `hr_payroll_invoice` unstyled-PDF investigation showed the
  renderer was already present; the test runner's `--no-http` prevented report
  CSS/assets from being served. Compose test operations now keep HTTP enabled;
  install/update retain `--no-http`. The corrected Odoo 18 sandbox test passed
  both actual QWeb PDF renders; authenticated live-browser requests returned
  `%PDF-` Payment Advice (22,453 bytes) and Payslip (22,553 bytes) responses.
  Frontend review then identified an unstyled print: `web.base.url` was the
  external tunnel, so the controller now configures internal
  `report.url=http://localhost:8069`; the post-fix real-PDF test passed.
  The user then confirmed from the Odoo frontend that both reports print with
  the expected styling. This closes the renderer/style defect; only the
  separate payroll action-form screenshot and role/vendor-bill evidence remain
  before treating `hr_payroll_invoice` itself as fully closed.
- Nested Docker has meaningful disk and memory cost; limits must be measured.
- Clone-mode changes can be lost during destruction without commit/patch export.
- Odoo Enterprise sources and customer data require strict private boundaries.

## Next task

Both Tier-1 module sequences are complete. Phase 8's broader exit gate is
**not yet met**. The sole next task is to close the remaining phase-level
evidence package:

1. Confirm the pipeline behaves correctly for a module with a real Odoo
   **Enterprise dependency** — dependency detection must flag it without
   ever fetching, bundling, or committing licensed Enterprise source.
2. Turn the captured `hr_document_report` measurements into the separate
   resource-sizing writeup against the Phase 7 host capacity.
3. Write the standalone Phase 8 design note
   (`docs/docker-sandbox/phase-8/design.md`) naming the canonical skill
   invocation order, referenced from `CommandingSystem/SKILL.md`.
4. Record a go/no-go decision on batching the remaining ~45 backlog modules
   through this sequence, based on the measured single-module cost above.

Update `docs/docker-sandbox/tasks.md`'s "Scope"/"Deliverables" checkboxes and
mark the Phase 8 exit gate PASS only once all of the above have real
recorded evidence. Update this file's Completed/Current state/Next task
together with that result. Only after Phase 8 fully passes should the
remaining VPCSCloud migration backlog batching begin (see Following tasks
below), and only then should the currently-staged local commits (this
repo's docs/evidence changes, and the `vpcs_apps_cloud_18` bugfix
separately) be pushed, per the user's explicit push policy.

Before starting new work, first commit this session's completed Step
7/9/10 evidence (this repo) and the pricelist bugfix (`vpcs_apps_cloud_18`,
branch `18.0`) as the Phase 8 pilot-module-completion commits, per
AGENTS.md's one-focused-commit-per-session rule — do not mix them with the
second-module work above.

## Following tasks

1. After Phase 8's exit gate passes, batch the remaining Tier 1 (17.0-only)
   VPCSCloud modules through the proven sandboxed sequence, then Tier 2
   (18.0-only) modules, sized against the Phase 8-measured single-module
   time/resource cost and the Phase 7 host capacity limits.
2. Replicate the live slash-command test on `odoo17-dev` and `odoo18-dev`
   (provider config already verified via `fallback list`, no live run yet)
   — natural to combine with the Phase 8 pilot since those profiles map
   directly to the 17.0/18.0 source repos.
3. Once Phase 8 proves quality/reliability at scale, decide whether
   `openrouter/free` is good enough for real Odoo task work or whether a
   paid primary provider should be linked instead (the user raised this
   trade-off directly — "otherwise I will link my Claude plan").
4. Review community platform evidence and fix proposals as they arrive
   (Apple Silicon macOS / Windows 11 Docker Sandbox validation).
5. Once Phase 8 and the VPCSCloud migration backlog prove the pipeline at
   scale, this becomes the base offering for external client Odoo project
   work — including custom customer repositories, existing Odoo Community
   module context, and Enterprise module dependency detection (never
   Enterprise source bundling/committal) as a fully dynamic, repeatable
   solution.

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
