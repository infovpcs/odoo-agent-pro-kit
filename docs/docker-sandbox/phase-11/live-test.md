# Phase 11 LIVE TEST — batch 19→20 migration on a cloud fleet

Status: **run 1 finished 2026-09-28. The LIVE TEST has not passed yet:** group C passes, groups
A and B are partial. Module source, migrated code and patches are private and stay in the
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

## Next

Finish groups A and B from the pulled repositories in fresh sandboxes (owner approval of spend
and model quota first), after fixing finding 1 test-first.
