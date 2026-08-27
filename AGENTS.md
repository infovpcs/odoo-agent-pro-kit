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

Preserve unrelated user changes and keep secrets, customer data, and licensed
Odoo Enterprise source out of this repository and its artifacts.
