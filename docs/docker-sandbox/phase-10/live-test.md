# Phase 10 LIVE TEST — Odoo 20.0 sandbox runtime

Status: **complete (2026-09-28).** The runtime, the requirements/import support,
`/fleet --cloud` (commit `595c2ca`), the 19→20 custom-app migration, acceptance step 7 with both
agent CLIs, and the private-repo clone over HTTPS all pass their LIVE TESTs. Nothing below is
claimed beyond what was run.

## Image design

Docker Hub had no `odoo:20.0` tag on 2026-09-27. `odoo/docker` published `20.0/` on 2026-09-26
(commit `d54316042067`). `sandbox/images/odoo-dev/20.Dockerfile` reproduces that recipe on
`ODOO_20_BASE`, a pinned `ubuntu:noble@sha256:008173c2…` digest:

- Odoo nightly deb `20260926`, sha1 `7cb4a582…`.
- wkhtmltopdf 0.12.6.1-3 (patched Qt), sha1 pinned per architecture.
- pgdg `postgresql-client`.
- `entrypoint.sh`, `odoo.conf` and `wait-for-psql.py` from that commit via `ADD --checksum=sha256:…`.
- Then the same dev layer as 17/18/19.

One deviation from upstream: the pgdg key is fetched with `curl` over HTTPS and must match
fingerprint `B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8` (finding 4 below).

Resulting image: Odoo `20.0-20260926`, Python 3.12.3, wkhtmltopdf `0.12.6.1 (with patched qt)`,
psql 18.6 client, about 2.3 GB. Odoo 20 needs PostgreSQL ≥ 16 (`MIN_PG_VERSION`), so 20 runs on
`POSTGRES_16` = `postgres:16-bookworm@sha256:efedf359…`. 17/18/19 stay on PostgreSQL 15. When Hub
publishes `odoo:20.0`, pin that digest, cut the Dockerfile down to the dev layer, and update
`tests/test_phase10_odoo20_sandbox.py`, which pins the current recipe.

## Odoo 20 findings

Each was fixed test-first (RED → GREEN):

1. `ir.config_parameter.set_param` is gone (typed `set_str` / `get_str` …). `create` crashed in the
   credential script. It now uses `set_str` when present, else `set_param`; so does the PDF script.
2. Odoo 20 defaults `http_interface` to `127.0.0.1`. The MCP sidecar and the run-mode probes
   could not reach `odoo:8069`, while the in-container healthcheck passed.
   `odoo.conf.template` sets `http_interface = 0.0.0.0`, the 17–19 default.
3. `ir.model.access` was replaced by `ir.access`. The fixture gets `fixtures/_overlays/20/`.
4. Inside `sbx` microVMs, build containers reach the network only through transparent 80/443
   interception. `gpg --recv-keys` (dirmngr, hkp 11371 and hkps) fails, while `curl` over
   HTTPS works. Fix: pgdg key over HTTPS plus a fingerprint check.
5. A microVM created with plain `sbx create` (no kit) is default-deny for pgdg, the keyserver and
   `nightly.odoo.com`. Odoo 20 microVMs must be created with `sandbox/bin/sandbox-agent create`.
   Kit 0.6.0 added the Odoo 20 build egress.

## Evidence

### Local exec mode — macOS 15 (Intel), Docker Desktop 29.8.0

- `sandbox/tests/ci-smoke.sh 20`: rc 0, 83 s.
- `SANDBOX_MATRIX_RUN_ID=p10all sandbox/tests/lifecycle.sh` (17/18/19/20 concurrent): rc 0,
  225 s.
  - CRUD: `xmlrpc` on 17.0-20260810 / 18.0-20260810, `json2` on 19.0 / 20.0.
  - PDF `base.ir_module_reference_print`: 266 / 262 / 287 / 298 KB.
  - No leftover containers or volumes.
- MCP sidecar on a 20 session: `protocol=json-2`, `search('sandbox.fixture')` → `[1]`, SSE 200
  on port 8768.

### KVM validation host — Ubuntu 24.04, `sbx` 0.38.0

- Kit-backed microVM `odoo-phase10-kit` (2 vCPU / 8 GiB, Docker 29.7.2, Compose 5.5.0):
  `ci-smoke.sh 20` rc 0 in 425 s, including the first image build.
- Earlier attempts failed on a kit-less VM, then on `gpg` (findings 4 and 5). Their logs were
  kept on the host.
- `lifecycle.sh` 20 was **not** run on KVM because of host disk: one Odoo 20 microVM needs
  about 10 GB, and 8.6 GB is free. The owner moved it to Docker Cloud Sandboxes (below).
- Repository suite on the host: 364 passed; `validate.sh` green, including `sbx kit validate`
  and `pack` for kit 0.6.0.

### Docker Cloud Sandboxes — client `sbx-cloud:0.45.1` on Intel macOS, owner-approved spend

Setup: one large sandbox (`--cpus 8 --memory 16g --platform linux/amd64 --ttl 90m --kit
sandbox/kits/odoo-mixin`), 14:44:09–15:16:40 UTC on 2026-09-27. Afterwards `ls` → "No
sandboxes found."

- `SANDBOX_EXEC_MODE=run SANDBOX_LIFECYCLE_VERSIONS=20 lifecycle.sh`: rc 0, 278 s, including the
  cold 20 image build. No egress denials.
- `phase9-cloud-acceptance.sh`, extended to 20 (warm create 19 and 20; eight concurrent
  sessions, two per version): all 16 steps PASS, rc 0, 439 s.
  - Warm create-to-ready: 19 took 23.0 s, 20 took 22.6 s.
  - Eight concurrent sessions: 40.5 s, 1.67 GB used of 16.8 GB.
  - Phase 6 recovery: 70.7 s.
  - Denied network: `curl https://example.com` → `http_code=000` (blocked).

### Module requirements and real-module import

`sandboxctl create --import DIR --requirements FILE` (design in `sandbox/README.md`). Two pip
approaches failed live before the final design:

- `pip install --break-system-packages` failed: Debian's `typing_extensions` has no `RECORD`.
- `--ignore-installed` replaced Debian's `cryptography` and broke pyOpenSSL. `base` failed to
  load (`GEN_EMAIL`).

Final design: a `--system-site-packages` venv using the image's own pip (`--without-pip`), put
first with `PYTHONPATH`. Only missing or too-old packages are overlaid. The build imports
`odoo.addons.base.models` and fails fast. It works on 18/19/20. On 17, the LLM requirements
upgrade `cryptography`, which conflicts with 17's Debian stack, so the build fails fast there.

LIVE on macOS: a 19 session with `--import` of the real `vpcs_llm_provider` and
`vpcs_progressive_payment_terms`, plus `--requirements vpcs_llm_provider/requirements.txt`.
Create took 73 s and the install succeeded. The **19 test baseline was reproduced**:

- `vpcs_llm_provider`: 2 failed + 2 errors of 8.
- `vpcs_progressive_payment_terms`: 1 failed + 14 errors of 26.

That is 3F/16E of 34, the same as the 2026-09-24 baseline on the validation host.

### `/fleet` in cloud

`sandbox-fleet create --cloud` is internal-only by owner decision: no `sbx ports`. The code goes
in as a git bundle of a working-tree snapshot. Run on 2026-09-27 with `SANDBOX_SBX` = the Intel
wrapper:

- Sessions 20/19/18 in parallel on `codex-docker` medium. Creates rc 0 at 15:47:00, 15:47:01 and
  15:51:27 (20 builds the image).
- `run … test sandbox_fixture`: rc 0 for all three at 15:52:00.
- `sbx --cloud ports`: "No exposed ports" for each.
- `sandbox-fleet destroy --force`: rc 0 × 3 (15:52:21–15:53:13).

## 19→20 migration and agent CLIs in cloud (2026-09-28, owner-approved spend)

The owner replaced the cloud `anthropic` secret with a workspace-scoped key and added $5 API
credit. They then switched the cloud `openai` secret to their ChatGPT subscription
(`sbx --cloud secret set openai --oauth`, TYPE `oauth_refresh`). The OAuth callback targets
`localhost:1455` inside the client container, so it was delivered from inside that container's
network with `docker run --network container:<name> curlimages/curl "<callback URL>"`.
`secret ls` keeps the original CREATED date on an overwrite.

Sandbox `kit-p10-mig3`: large, `claude-code-docker` template, TTL 90 min, created 07:37:56 UTC.
It held the committed kit, and the 19.0 sources of `vpcs_llm_provider` +
`vpcs_progressive_payment_terms` as a throwaway git repo (baseline commit `e2e53a8`).

### Acceptance step 7 — both agent CLIs PASS

| Agent | Sandbox | Credential | Result |
|-------|---------|------------|--------|
| Claude Code 2.1.280 | `kit-p10-mig3` (`claude` template) | workspace-scoped API key | `CLAUDE-OK` on `claude-haiku-4-5`, `--max-budget-usd 0.10`, cost $0.0105 |
| codex-cli 0.149.1 | `kit-p10-codex` (`codex` template, medium, 07:46–removed by owner) | ChatGPT OAuth (`provider: sandboxd`) | `CODEX-OK`, rc 0, model `gpt-5.6-sol`, no API credit used |

`sbx exec` is the approved fallback for the SSH probe.

### Run 3 — `/plan-analysis` → `/start-coding` → `/testing`, headless with the plugin hooks

`claude -p --plugin-dir ~/kit/plugin --dangerously-skip-permissions --model M --max-budget-usd B`:

| Step | Model | Cap | Result |
|------|-------|-----|--------|
| `/plan-analysis 20` | Haiku 4.5 | $0.75 | success, 18 turns, 152 s, $0.154 |
| `/start-coding 20` | Sonnet 5 | $3.00 | success, 87 turns, 975 s, $1.986 — 5 commits (manifest bump, `ir.access`, `toggle_active`/`t-esc`/`Registry._init`, `project.view_task_card` re-target, findings) |
| `/testing 20` | Haiku 4.5 | $0.75 | **blocked by the kit's `/testing` gate**, $0 |

Independent no-LLM check (the same sandbox, `sandboxctl` only):

| Module | 19 baseline (re-run by name, 08:04) | 20 after migration (08:00) |
|--------|-------------------------------------|----------------------------|
| `vpcs_llm_provider` | 2F + 2E of 8 | 2F + 2E of 8 — the same 4 Cerebras tests |
| `vpcs_progressive_payment_terms` | 1F + 14E of 26 | 0F + 14E of 26 — the same 14 errors; `test_milestone_percentage_validation` now passes |

Both modules install on 20, and no test fails on 20 that did not fail on 19: **PASS**. The
agent's summary said all 14 errors come from the missing `construction.project.template`
model. In fact 10 do; one comes from a missing `is_boq_item` field (from the same absent
module), and three are analytic tests (`analytic_account_id` invalid on `project.project`, two
`IndexError`s). All 14 also error on 19.

### Kit finding and fix (test-first)

The `/testing` block had a deeper cause. The Haiku-written `docs/tasks.md` had **no checkboxes**,
so the gate's "no open tasks" check passed vacuously. Also, no step recorded a backend-test
outcome, and the flag could only express a plain pass. Fixes in `plugin/hooks/checks/gates.py`
and `plugin/hooks/odoo_hook.py`, each written RED → GREEN in `tests/hooks/`:

- `/start-coding` and `/testing` block a `tasks.md` without `- [ ]` / `- [x]` lines.
- `/testing` also accepts `backend_tests_baseline_parity: true`, but only with a recorded
  `backend_tests_baseline`.
- The Stop hook blocks once when every task is `[x]` and no outcome is recorded (an honest
  `false` counts as recorded).
- PRD-Writing, `plan_analysis_workflow.md`, `start_coding_workflow.md` (STEP 5) and
  `testing_workflow.md` say the same.

### Run 3b — the chain again with the fixed kit (same sandbox)

| Step | Model | Cap | Result |
|------|-------|-----|--------|
| `/start-coding 20` on the prose `tasks.md` | Haiku | $0.05 | **blocked by the new checklist gate**, $0 |
| Convert `tasks.md` to a checklist | Haiku | $0.30 | 7 turns, 53 s, $0.063: 10 × `- [x] Task N` (commit `30526f0`). Went beyond the brief: it also wrote a parity record from the earlier findings. |
| `/start-coding 20` | Haiku | $0.75 | 43 turns, 732 s, $0.284: re-ran both suites in new sessions `llm-final` (08:23, 2F+2E of 8) and `ppt-final` (08:26, 0F+14E of 26), verified in their logs; parity record with the 19 baseline |
| `/testing 20` | Haiku | $0.75 | **allowed by the gate**, 23 turns, 309 s, $0.121: backend counts vs. baseline, `TESTING_RESULTS.md`, no frontend screenshots |

The Stop-hook enforcement was **not** exercised live: the convert step had already written a
record. It is covered by unit tests only. The agent's closing line ("ready for production
deployment") is its own claim and is not evidence.

Total Anthropic spend: $2.62 (smoke $0.01, run 3 $2.14, run 3b $0.47). OpenAI: $0 (subscription).

## Private-repo clone over HTTPS (2026-09-28, owner-approved spend)

Before this run, the cloud `github` secret (a fine-grained token) could see **0** private
repos (`/user/repos?visibility=private`). The owner changed it to *All repositories* +
Contents; it then saw 62. Test repo: a small private `infovpcs` repo (162 KB). No LLM involved.

| Template (sandbox, UTC) | `git ls-remote` / `git clone` private | public `ls-remote` | `api.github.com` |
|-------------------------|---------------------------------------|--------------------|------------------|
| `shell` (`kit-p10-git`, 09:16) | fail: `could not read Username` / `invalid credentials` (`info/refs` 401) | fail (401) | 200 (secret injected; private repo 200 after the token change; the tarball redirect to `codeload.github.com` is blocked by the kit) |
| `claude` (`kit-p10-tar`, 09:31) | **pass**: rc 0, 50 files, HEAD `d6c3fd3` | pass | 403 (not in the kit allow-list) |
| `codex` (`kit-p10-cgit`, 09:32) | **pass**: rc 0, 50 files | — | 200 |

Result: **PASS** for the agent templates the kit uses (`claude`, `codex`). Plain
`git clone https://github.com/<owner>/<repo>` works, and the proxy supplies the credential. The
`shell` template's proxy does not pass it to git (even public repos get 401). The kit does not use
that template, so this is recorded as a limit. A trial kit 0.8.0 that allowed
`codeload.github.com` (for the API-tarball route) was reverted before commit, because the agent
templates do not need it. Kit stays 0.7.0.

## Known limits carried forward

- Docker Hub still has no `odoo:20.0`; switch `ODOO_20_BASE` when it appears.
- `lifecycle.sh` 20 was not run on the KVM host (disk); cloud evidence covers it.
- The `shell` cloud template cannot use git over HTTPS to GitHub (see above).
- A cloud sandbox whose TTL expires is `stopping`/`hibernating` for several minutes; `rm`
  is refused (`failed_precondition`) until it settles.

Evidence files (gitignored, local): `.sandbox/phase10-cloud/.sandbox/release/phase9/` (cloud
acceptance) and `.sandbox/phase10-cloud/run2/r2.log` (the 2026-09-27 blocked run). Run 3/3b are
in `.sandbox/phase10-cloud/run3/`: `smoke.log`, `codex.log`, `loop.log`, `loop-*.json`,
`verify.log`, `verify-odoo.log`, `base19.log`, `base19-odoo.log`, `rerun.log`, `re-*.json`,
`private_*.log`, and the migrated repos `vpcs_apps_20.tgz` / `vpcs_apps_20b.tgz`.
