# Repository Agent Rules

Read `SESSION_CONTEXT.md` before starting work and treat
`docs/docker-sandbox/tasks.md` as the authoritative phase checklist.

## Phase workflow

1. Work on exactly one Docker Sandbox phase per session.
2. Start only after the prior phase exit gate is complete.
3. Complete every checklist item and the phase LIVE TEST before marking the
   phase complete. A failed or unsupported live test is a blocker, not a pass.
   Run repository, Docker client/daemon, and registry checks on the available
   Intel macOS workstation. Run all Docker Sandbox microVM and runtime LIVE
   TESTS on the designated Ubuntu 24.04+ KVM validation host. Do not require an
   Apple Silicon host unless a task specifically tests macOS Sandbox behavior.
   Docker Cloud Sandboxes (`sbx --cloud`, `sbx_cloud_version` in
   `sandbox/config/artifacts.lock`) are also an accepted runtime LIVE TEST host
   for tasks that test cloud behavior, following
   `docs/docker-sandbox/phase-9/cloud-runbook.md`. Every cloud run needs the
   owner's approval of the spend, and every cloud sandbox is removed when the
   run ends. Cloud evidence does not replace a required KVM-host LIVE TEST.
4. Update implementation, `README.md`, related requirements/design/runbooks,
   `docs/docker-sandbox/tasks.md`, and `SESSION_CONTEXT.md` together.
5. Run `./scripts/validate.sh` and all phase-specific tests from a clean shell.
6. Record exact commands, versions, platforms, results, and blockers in
   `SESSION_CONTEXT.md`; never claim unexecuted evidence.
7. Commit the completed phase as one focused commit after validation. Do not
   push, merge, tag, publish, buy services, create external resources, or
   perform destructive cleanup unless the user explicitly authorizes it.
8. Set the next incomplete phase as the sole next task, then end the session so
   the next phase begins with a fresh context read.

The phase-workflow rules above are backed by `.claude/settings.json` +
`scripts/contributor_hook.py` for contributors using Claude Code: it prints the
current state at session start, blocks `git push/merge/tag` and destructive
cleanup unless `AGENTS_PHASE_AUTHORIZED=1`, and blocks `git commit` **only when**
`.git/odoo-kit-validate.stamp` exists and is older than the newest tracked
change (an absent stamp does not block). `./scripts/validate.sh` refreshes that
stamp automatically on success, so the normal flow is just to run it — no manual
`touch` needed. Read-only git subcommands (`git merge-base`, `git tag -l`,
`git rebase --abort`) are not blocked.

## Merging into `main`

Every change reaches `main` through a pull request, and a pull request is merged only when
**every check on its latest commit has passed**:

- `CI / validate`
- `Docker Sandbox release / validate`, `image-build (17)` to `(20)` and `compose-smoke (17)` to `(20)`

Before you merge:

1. Run `./scripts/validate.sh` and `python -m pytest tests -q` locally; both green.
2. Wait for the checks, then read `gh pr checks <number>` once more just before merging
   (`--watch` output can mix in earlier rows). Every row says `pass`; none is `fail`,
   `pending` or `skipping`.
3. If `main` moved, update the branch from `main` and wait for the checks again.

A failing check is a blocker, even when it also fails on `main`: fix it first in its own pull
request, merge that when it is green, then update the waiting branch. Never merge "known red".
A test step that runs no test fails (since `5039a46`), so a module or fixture that CI tests
carries at least one real Odoo test.

`CLAUDE.md` and `GEMINI.md` point here; this file holds the rules.

Preserve unrelated user changes and keep secrets, customer data, and licensed
Odoo Enterprise source out of this repository and its artifacts.
