# Phase 12 LIVE TEST — batch-migration kit fixes

Status: **passed 2026-09-29** (all four parts). Host agreed with the owner at the start of the
phase: the local Intel macOS workstation (macOS 15.7.9, Docker Desktop 29.8.1, `sandboxctl` exec
mode, bash 3.2.57, Python 3.12.2, `agent-browser` 0.35.1). No cloud run and no spend. Kit: `main`
at `930a842` plus the uncommitted Phase 12 work. Private module code and the work repositories
stay in the gitignored `.sandbox/phase12/`; this record lists names, commands and results only.

## Owner decisions at the start (2026-09-29)

- **LIVE TEST (1) replaced.** The cloud run's group A `requirements-freeze.txt` was never pulled,
  and those sandboxes are gone. The local failure log also showed that finding 7 was not
  requirement drift: pip hit five `Read timed out` retries on `pypi.org/simple/click/`, then
  reported `ResolutionImpossible`. The owner chose "record then replay": build group A's
  requirements, replay the recorded freeze, show a freeze for another version is refused, and
  make the build tolerate a slow index (60 s timeout, 10 retries).
- **Host:** local Docker Desktop, not the KVM host (about 8.6 GB free there; one Odoo 20 session
  needs about 10 GB).

## (1) Requirements freeze: record, replay, refuse

Group A's four requirements files (the merged 22-line set that failed on 2026-09-28):

| Step | Command (abridged) | Result |
|------|--------------------|--------|
| Record | `sandboxctl create --version 19 --module sandbox_fixture --session p12-rec19 --requirements req/a-blog.txt … a-typesafe.txt` | rc 0, 4 min 06 s; freeze has 81 pins after the header `# sandbox-requirements-freeze odoo_version=19.0 base_image=odoo:19.0@sha256:94a4f480…` (`click==8.5.0`, `nltk==3.10.3`) |
| Replay | same `--requirements` plus `--requirements-freeze freeze-a-19.txt` | rc 0, 3 min 33 s; new layer `…-reqdb8c451f7094` (the record's was `…-reqf39b10adec4b`), pip ran with `-c /tmp/sandbox-constraints.txt`; `diff` of the two freezes: **identical** |
| Refuse (version) | `create --version 20 … --requirements-freeze freeze-a-19.txt` | rc 1, `requirements freeze was recorded for Odoo 19.0, not 20.0`; no session directory created |
| Refuse (no header) | `create --version 19 … --requirements-freeze <plain pins>` | rc 1, `requirements freeze has no provenance header …`; no session directory |

Both sessions were destroyed afterwards (rc 0).

## (2) Runner, no-LLM `baseline` + `verify` on group C

Groups file: group `c` = the 19 source of `odoo_whatsapp_mcp` (`VPCS-Cloud` `3530251`) plus a
generic, test-less probe module `p12_install_probe` (for part 3), requirements `req/c-whatsapp.txt`.
After `baseline`, the work repository got one commit with the module from the `VPCS-Cloud` `20.0`
branch (`9f4e1d4`), standing in for the agent `code` stage.

```text
sandbox/scripts/migration-runner.sh --groups groups.txt --from 19 --to 20 --out run --stages baseline          # 3 min 47 s, rc 0
sandbox/scripts/migration-runner.sh --groups groups.txt --from 19 --to 20 --out run --stages "baseline verify"  # 3 min 53 s, rc 0
```

| Stage | Installs (exit code) | Tests | Status line |
|-------|----------------------|-------|-------------|
| baseline (19) | `odoo_whatsapp_mcp` 0, `p12_install_probe` 0 | 9 passed, 3 failed, 4 errors of 16 (the same as the Phase 11 cloud baseline) | `done` |
| (re-run) | — | — | `baseline` `skipped` ("done in an earlier run"): resume works |
| verify (20) | `odoo_whatsapp_mcp` 0, `p12_install_probe` 0 | 13 passed, 3 failed, 4 errors of 20 | `done`, `parity: true`, `pass: true` |

`test-parity.py` output: `parity: PASS`, `result: PASS`, every non-passing test also failed on 19.

## (3) A broken install fails the new pass criterion

The probe's 20 manifest was given a dependency on a module that does not exist (committed), then
`--stages "baseline verify" --rerun verify` (3 min 12 s, runner rc 1):

```text
module     odoo_whatsapp_mcp: install exit 0, tests 16 -> 20
module     p12_install_probe: install exit 255, tests 0 -> 0 — FAIL: install failed (exit 255)
parity: PASS
result: FAIL
```

Status line: `verify` `failed`, `parity: true`, `pass: false`. This is Phase 11 group A's case: a
module with no passing baseline test does not install, and parity alone passes.

## (4) Live UI check on a migrated app

Session `p12-ui` (Odoo 20, group C's `20.0` tree, module installed), a local-only `alpine/socat`
bridge on `127.0.0.1:8718`, `sandbox/scripts/ui-check.py --login admin --runtime-env … --server-log …`:

| Run | Screens | Result |
|-----|---------|--------|
| Clean | the 5 WhatsApp actions (configuration, messages, conversations, inbox, archived) and a new configuration form | 6 × OK, `ui-check: PASS`, rc 0, 6 screenshots |
| Injected | a JS asset calling `console.error("P12 injected console error")`, added to the **session copy** of the module, module updated | 2 × FAIL `console: [error] P12 injected console error`, `ui-check: FAIL`, rc 1 |

The first clean run passed but saved no screenshots, because agent-browser's daemon resolves a
relative path in its own working directory. Test-first fixes: absolute screenshot paths, and a
login that stays on `/web/login` now fails, where it used to pass vacuously on login pages. The
run above is after the fix.

Stop gate, live (real `plugin/hooks/odoo_hook.py`, scratch copy of the work repository as a
migration target, prompt naming `testing_workflow.md`): no `ui_check` record → rc 2 with the
message naming `sandbox/scripts/ui-check.py` and `"ui_check"`; with
`"ui_check": {"passed": true, "result": "<ui-pass.json>"}` → rc 0.

Clean-up: bridge removed, browser session closed, `p12-ui` destroyed; no Phase 12 container or
session directory left. `odoo20-pg16` was not touched.

## Not covered

- The agent stages (`plan`, `code`, `test`) ran only against fake agent binaries in
  `tests/test_phase12_migration_runner.py`: gates, plain-words prompts, quota stop, budget stop.
  No LLM run in this phase (no spend).
- The cloud fleet's `--requirements-freeze` pass-through is unit-tested only.
