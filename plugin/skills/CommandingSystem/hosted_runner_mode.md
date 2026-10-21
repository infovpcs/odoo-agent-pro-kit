# Hosted runner mode

For an agent that runs **without Docker beside it** — a hosted Hermes whose terminal is a
workspace container — sandboxes run on a remote **runner** reached through MCP tools. This
mode replaces `sandbox/bin/sandboxctl` and the local `manage_modules.sh` steps of
`start_coding_workflow.md` and `testing_workflow.md`; everything else in those workflows
(tasks, gates, progress, handoff) stays as written.

## When it applies

Both hold:

- `runner_health` is among your tools, and it answers `status: ok`;
- `command -v docker` finds nothing in your terminal.

If `runner_health` does not answer, the runner is offline (it runs on a machine that may be
off): say so, keep working on code and documents, and leave every runtime gate open. Never
mark a task done without a runner result.

## The loop

1. **Send the module.** In the terminal, from the folder that holds it:
   `runner-upload <module-folder> [<module-it-depends-on> ...]`. It prints JSON with an
   `upload` id and the `modules` it took. The manifest version must already be the target
   series (`20.0.x.y.z` for Odoo 20); `docs/`, `sessions/`, `.git` and caches are left out.
2. **Create a session.** `runner_session_create_upload(version, upload, module, also)`.
   It asks the member first. It starts in the background: call
   `runner_session_status(session, wait=45)` until `busy` is null and `state` is `ready`.
3. **Install, then test.** `runner_module_install(session, module)`, wait with
   `runner_session_status`, then `runner_module_test(session, module)` and wait again.
   A step passed only when its `gate_result` is `passed`. A failed step carries the Odoo
   errors: read them, fix the code in the workspace.
4. **After each change.** `runner-upload` again (a new `upload` id), then
   `runner_module_replace(session, upload)`, then `runner_module_update(session, module)` and
   `runner_module_test` again. No new session is needed for a code change.
5. **Evidence.** For each task, record in `sessions/<module>_progress.json` the `run_id`, the
   `session`, and each step's name and `gate_result`, and tick the task in `docs/tasks.md` only
   when install and test both report `passed`.
6. **Finish.** `runner_session_export(session)` keeps the session's archive and, if the module
   changed in the session, its patch; then `runner_session_destroy(session)`. The runner allows
   only a few sessions at once: destroy yours when the work stops.

## Limits and refusals

- `version_mismatch`: the manifest is for another Odoo series than the session's version.
- `dependency_missing`: something it depends on is neither Odoo's own, nor Odoo Enterprise for
  people allowed to use it, nor in the upload or another of the member's links: upload that
  module too (`runner-upload a b`).
- `too_many_sessions`: destroy a session first.
- An upload is kept 24 hours after its last use; a run from an upload is the member's own and
  is never promoted to a staging server.
