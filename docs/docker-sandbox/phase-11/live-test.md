# Phase 11 LIVE TEST — batch 19→20 migration on a cloud fleet

Status: **closed 2026-09-28.** Run 1 (cloud) finished with group C passing and A/B partial; the
**completion run (local)** finished all three groups with parity PASS (see below). The owner
accepted this evidence as the Phase 11 LIVE TEST without a no-LLM cloud re-verification. Module source, migrated code and patches are private and stay in the
gitignored `.sandbox/phase11/`. This record lists names, commands and results only.

## Setup

- Client: `sbx-cloud:0.45.1` (linux/amd64 container on Intel macOS), `SANDBOX_SBX` wrapper.
- Source: private `VPCS-Cloud` repository, commit `3530251`, staged with `migrate-local.py`, then
  split into three group trees (a 78 MB marketing `.mp4` left out).
- Allocation (owner-approved spend): three `sandbox-fleet create --cloud --version 19 --module
  <first> --import <group tree> --requirements …` in parallel. Template `codex-docker`, medium
  (4 vCPU / 8 GiB), TTL 120 min, internal-only (no ports published). Created 10:28–10:32 UTC, rc 0 ×3.
  Kit snapshot: working tree at `201d1f3` plus uncommitted `tasks.md` notes.
- Agent: codex-cli 0.149.1 on the owner's ChatGPT subscription (`openai` OAuth secret).
- Gates: Codex does not run Claude Code hooks, so a runner called the kit's own hook entry
  point (`plugin/hooks/odoo_hook.py`, `UserPromptSubmit` for `/start-coding` and `/testing`,
  then `Stop`) between steps (owner decision).
- Independent check (no LLM): the committed work repo is staged again, installed and tested in a
  fresh 20 session, then compared by test name with `sandbox/scripts/test-parity.py`.

## 19.0 baselines (10:33–10:35 UTC)

| Group | Module | Tests on 19 |
|-------|--------|-------------|
| A | `vpcs_llm_provider` | 31: 12 passed, 2 failed, 17 errors |
| A | `vpcs_typesafe_ai` | 8 passed |
| A | `vpcs_ai_livechat` | none |
| A | `website_blog_ai_generator` | 15, all errors |
| B | `currency_rate_of_rbi`, `vpcs_gitlab`, `vpcs_cloud_website_customization` | 28 passed |
| C | `odoo_whatsapp_mcp` | 16: 9 passed, 3 failed, 4 errors |

## Agent run (10:34–10:53 UTC)

| Group | Plan step | Coding step | Stopped by |
|-------|-----------|-------------|------------|
| A | docs + checklist, 194 s | 4 commits, 908 s; 2 of 4 modules migrated, 6 tasks open | ChatGPT usage limit |
| B | nothing written (see finding 2); Codex wrote the plan under `/start-coding` | 7 commits, 1 064 s; 2 tasks open | ChatGPT usage limit |
| C | nothing written (finding 2); plan written under `/start-coding` | 8 commits, 1 069 s, all 4 tasks done, parity recorded | `/testing` step: usage limit after 80 s |

Codex reported `You've hit your usage limit … try again at 12:46 PM` in all three sandboxes at
10:53 UTC. Tokens reported by Codex: A 172 170, B 186 380 (coding), C 39 412 (`/testing` only).
Three parallel runs share one subscription quota.

## Independent verification on 20.0 (11:03–11:20 UTC)

| Group | Installs on 20 | Parity (`test-parity.py`) | Result |
|-------|----------------|---------------------------|--------|
| C | 1 / 1 | PASS: 9 passed, 3 failed, 4 errors of 16 on both | **PASS** |
| A | 2 / 4: `vpcs_ai_livechat`, `website_blog_ai_generator` still at version 19.0 (not migrated) | PASS (13 passed of 17), only because those two modules had no passing test on 19 | partial |
| B | 2 / 3: `vpcs_cloud_website_customization` fails, `External ID not found: website_sale_comparison.product_attributes_body` | FAIL: its 11 tests are missing | partial |

The owner removed the three sandboxes around 11:35 UTC (`sbx --cloud ls`: none left). The work
repositories with full git history, logs and parity JSON were pulled first.

## Findings

1. **Gates fail open (kit bug).** `odoo_hook.py` treats a repository without a root
   `docs/tasks.md` as out of scope, so `/start-coding` (no plan yet) and `/testing` (group C kept
   its checklist in `odoo_whatsapp_mcp/docs/`) passed without checking anything. The gates must
   refuse when they cannot find the checklist for a slash command.
   **Fixed 2026-09-28** (test-first, `tests/hooks/test_gates_fail_closed.py`). Re-checked on the
   pulled repositories: group C's `/testing` is now blocked, because its outcome record sits in
   the repository's `sessions/` while its checklist is in the module; the next run records it
   next to the checklist.
2. **Codex and a leading slash command.** For groups B and C, a prompt that starts with
   `/plan-analysis 20` ended with "goal budget exhausted" and no files written; group A's
   identical prompt worked. The runner should phrase the step in plain words and name the
   workflow file.
3. **Parity alone is not the pass criterion.** A module that fails to install but had no
   passing test on 19 does not show up as a parity regression (group A). The runner's install
   exit codes are part of the result, and `test-parity.py` could take the expected module list.
4. **Quota.** Three parallel Codex runs used the subscription's window in about 20 minutes.
   Batch runs need a quota plan (serial groups, or a second model provider).
5. Undeclared dependency in the source: `vpcs_gitlab` imports `paramiko` at load time without
   declaring it (supplied through group B's requirements file).
6. Runner defects fixed during the run: the verify stage name contained a hyphen (rejected by
   `migrate-local.py`), and a failed earlier create left a session name behind. Both now fail
   fast with the error logged.

## Completion run — local Docker Desktop (2026-09-28, 11:45–13:05 UTC, owner decision)

After the ChatGPT limit, the owner chose to finish the three groups in the local Claude Code
session on the kit's local runtime: Docker Desktop 29.8.0→29.8.1 (it auto-updated during the run),
`sandboxctl` exec mode, pinned image `odoo-agent-dev:20-008173c23f95` (Odoo 20.0-20260926). Work
started from the pulled cloud repositories; every group was re-verified in a **fresh** Odoo 20
session built from the committed work (`git archive` of HEAD, because `migrate-local.py` refuses a
source inside the kit repository), then compared with the **cloud** 19 baseline log by test name.

| Group | Installs on 20 | Parity | 20.0 tests |
|-------|----------------|--------|------------|
| A | 4 / 4 | PASS: 0 regressions, 10 fixed, 9 new | 31 passed, 4 failed, 5 errors of 40 (all 9 non-passing also failed on 19) |
| B | 3 / 3 | PASS | 28 passed of 28 (19: 28 of 28) |
| C | 1 / 1 | PASS | 9 passed, 3 failed, 4 errors of 16 (same on 19) |

Gates (`odoo_hook.py`, fixed in `c980a9e`) pass for all three work repositories: every checklist
item done, and the outcome recorded next to its checklist. Coverage limits: livechat document
ingestion/retrieval (embedding API + pgvector) and browser checks were not exercised.

Odoo 20 migration changes needed (beyond the Phase 10 list):
- Binary fields hold `BinaryValue` objects: read `.content`/`.size`, write `BinaryBytes(...)` or a
  base64 **string**; writing raw `bytes` raises. `ir.attachment.datas` is gone (`create` drops it
  with a warning, reading raises): use `raw`.
- `ir.access` rows without a group are **restrictions**, not grants: 19's "no group = everyone"
  rows need explicit groups.
- `toggle_active` removed: header `action_archive`/`action_unarchive` + `web_ribbon`.
- `website_sale`: `website_sale_comparison.product_attributes_body` moved to `website_sale`; the
  product tile `<form>` became `<article>` (with `t-attf-class`, so `hasclass()` does not match);
  `combination_info['prevent_zero_price_sale']` became `hide_price`.
- `odoo upgrade_code` 19→20: running all scripts fails (`19.3-00-account-groups` KeyError), and
  `19.4-00-ir-access` crashed on module copies; conversions were done by hand.

Kit findings:
7. **Requirement drift.** The same unpinned group A requirements built in the cloud at 10:30 UTC
   but failed locally on the 19 image at 12:47 (`ResolutionImpossible`: `nltk` → `click`). A
   session's `results/requirements-freeze.txt` should be replayable as a pinned input.
   **Corrected in Phase 12 (2026-09-29):** the local build log shows five `Read timed out`
   retries on `pypi.org/simple/click/` before the error. pip reported the unreachable index as
   `ResolutionImpossible`, so it was not drift: the same requirements built later on the 20 image
   (`click` 8.5.0). The fix is a longer pip timeout with more retries, and the freeze replay
   ships anyway for reproducible builds.
8. **Docker Desktop auto-update** restarted the daemon mid-run (one aborted create, cleaned up;
   `unless-stopped` containers came back). Turn auto-update off for long runs and recordings.

## Branch, live UI test and documentation (2026-09-28, 13:10–14:25 UTC, owner request)

The owner asked for a `20.0` branch in `VPCS-Cloud` with all changes, then live testing with the
documentation skill until every app has its `index.html`.

- Branch `20.0` from `3530251`: one commit per group plus migration records
  (`docs/odoo20-migration/`), each module checked file by file against its work repository.
  The contributor hook blocks publishing from this session; the owner publishes the branch.
- One local Odoo 20 session (`docs20`) with all eight modules installed together, a local-only
  `socat` bridge, `agent-browser` 0.35.1. Every screen was accepted only with no page error, no
  console `[error]`, no error dialog and no new server exception; every action was checked over
  JSON-RPC.
- **The live UI test found seven Odoo 20 bugs that the backend tests and the parity check had
  missed** (details in the private repository's `docs/odoo20-migration/LIVE-TEST.md`): a removed
  `_notify_thread` argument that broke the web client, the product page interaction and CTA
  markup, `add_members`, a notice-forwarding loop, a new computed field not assigned, and a test
  fixture colliding with existing data. All fixed with regression tests; afterwards every group
  still passes parity in the same database (A 32/41, B 28/28, C 13/20; all non-passing tests
  also failed on 19).
- 41 screenshots and an "Odoo 20.0 — live tested" section in every module's `index.html`; two
  modules got their first `index.html`, icon and banner.

Kit finding 9: backend parity is necessary but not sufficient for a migration — the `/testing`
live UI step found more real bugs than the backend tests. The documentation skill's acceptance
rule was extended (console errors, error dialogs, server-log exceptions) with the Odoo 20 form
quirks met in this run (`plugin/skills/Odoo_Module_Documentation_Screenshot/SKILL.md`).

## Owner decision and close (2026-09-28)

- Both branches are published: `VPCS-Cloud` `20.0` at `9f4e1d4` and kit `main` at `17c81ab`
  (checked with `git ls-remote`).
- The owner accepted the evidence as is: cloud run 1 (fleet allocation, 19 baselines, Codex,
  group C PASS) plus the local completion run and the live UI test (A, B, C parity PASS; all
  eight modules in one Odoo 20 database). Groups A and B not finishing in the cloud (ChatGPT
  usage limit) is an accepted gap. No no-LLM cloud re-verification was run and no cloud spend
  was made for the close. Pushing migrated code anywhere else remains an owner action.
