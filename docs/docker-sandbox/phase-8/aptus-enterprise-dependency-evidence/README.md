# Phase 8 — Real Client Enterprise-Dependency Proof + Reverse Migration

Source project: `Aptusinfotech/aptus` (private, GitHub-level access via
`infovpcs`), staging branch, Odoo.sh-hosted, Odoo 19.0. Module under test:
`account_report_template` ("Oman P&L & Balance Sheet"), which extends
`account.account` and defines custom `account.report`/`account.report.line`/
`account.report.expression` records for a country-specific P&L/Balance Sheet
layout. No source from this private client repository is committed here —
only manifests, dependency chains, and operation-result evidence.

## Real Enterprise dependency chain confirmed

- `account_report_template` depends on Odoo's Enterprise Accounting app,
  whose technical module name changed across the 17.0 -> 18.0 -> 19.0 split:
  - **19.0 / 18.0**: depends on `accountant` (license `OEEL-1`, Odoo
    Enterprise Edition License), which itself depends on `account_reports`
    (19.0) / `account_accountant` (18.0) respectively.
  - **17.0**: `accountant` does not exist as a separate module yet; the
    Enterprise Accounting app IS `account_accountant` directly (license
    `OEEL-1`).
- Verified directly against the user's own licensed Enterprise source clones
  (`~/workspace/ent-19`, `~/workspace/18_local_Project/ent-18`,
  `~/workspace/17_local_project/ent-17`) — read locally for manifest/license
  inspection only, never copied into the sandbox or this repository.

## Enterprise-dependency detection proof (19.0, Enterprise-source-free sandbox)

Ran inside Docker Sandbox `phase8-aptus-ent-test` (Odoo 19.0) on the Ubuntu
KVM host, with only `account_report_template` copied into
`/mnt/extra-addons` — no Enterprise source ever fetched or mounted.

`sandboxctl module ... install account_report_template` returned a
CLI-wrapper `exit 0` ("succeeded") — this is a real, useful finding on its
own: Odoo's `-i` install-list CLI path treats an unresolvable dependency as
**skip-with-warning**, not a hard failure, unlike the ORM `button_install()`
path used in the earlier `real_estate` (17.0) test which raised a hard
`UserError`. The authoritative signal is the database state, not the CLI
exit code:

```
name                     |     state     
-------------------------+---------------
accountant               | uninstallable
account_report_template  | to install
```

`account_report_template` never reached `installed` — it is permanently
stuck in `to install` because its Enterprise dependency `accountant` is
`uninstallable` (absent from the image). The Odoo log recorded the exact
skip and the resulting inconsistent-state error:

```
WARNING ... odoo.modules.module_graph: module account_report_template: some depends are not loaded (accountant), skipped
ERROR ... odoo.modules.loading: Some modules have inconsistent states, some dependencies may be missing: ['account_report_template']
```

Full evidence: `19.0-install-operation-result.json`,
`19.0-db-module-state.txt`, `19.0-odoo-install-warning.txt` in this
directory.

**Lesson for the pipeline**: `sandboxctl module ... install` exit code alone
is not sufficient to prove a real install succeeded when Enterprise
dependencies may be involved; the install/update wrapper should also assert
the target module's `ir_module_module.state == 'installed'` (or the caller
must check it explicitly, as done here) rather than trusting exit 0.

## Reverse migration test (19.0 -> 18.0 -> 17.0)

To exercise the reverse-migration agent workflow (per user request, without
mounting licensed Enterprise source — proving detection/failure only, not a
full working install), the module's manifest was hand-migrated for each
target version using the coding-standard/dependency-context skills' version
comparison:

| Version | `depends` (accounting Enterprise dep) | Manifest version string |
|---|---|---|
| 19.0 (source) | `account`, `accountant` | `19.0.1.0.0` |
| 18.0 (migrated) | `account`, `accountant` (name unchanged 18->19) | `18.0.1.0.0` |
| 17.0 (migrated) | `account`, `account_accountant` (17.0 has no separate `accountant` module) | `17.0.1.0.0` |

No Python/XML/JS code changes were needed beyond the manifest: `account.report`
fields used (`hierarchy_level`, `foldable`, `user_groupby`), the `account`
view anchor (`account.view_account_form`, `tag_ids` field), and the
`web.SelectionField` OWL component path
(`web/static/src/views/fields/selection/selection_field.js`) are all present
and unchanged across 17.0/18.0/19.0 in the user's licensed Enterprise/
Community source trees — confirmed by direct inspection before running any
sandbox test, not assumed.

Each migrated copy was installed inside a **reused** Docker Sandbox session
(`phase8-aptus-ent-test`, torn down and recreated per version to respect the
2-vCPU/15-GiB host's ~2-concurrent-session capacity limit from Phase 7) with
only that version's manifest change applied and no Enterprise source
present. Result was identical and consistent across all three versions:

| Version | CLI exit | `ir_module_module.state` (target) | Enterprise dep state |
|---|---|---|---|
| 19.0 | 0 (wrapper "succeeded") | `to install` (blocked) | `accountant` = `uninstallable` |
| 18.0 | 0 (wrapper "succeeded") | `to install` (blocked) | `accountant` = `uninstallable` |
| 17.0 | 0 (wrapper "succeeded") | `to install` (blocked) | `account_accountant` = `uninstallable` |

A post-test filesystem `find` for any Enterprise module name after each
version's run returned zero matches in all three sandboxes — no Enterprise
source was ever fetched, mounted, or present at any point across the
reverse-migration test.

## Cleanup

All three inner Compose runtimes and the single outer Sandbox
(`phase8-aptus-ent-test`) were fully destroyed after evidence capture
(`--allow-unexported`, since this was a disposable evidence-capture run with
no work product requiring preservation). `sbx ls`, `docker ps -a`, and
`docker volume ls` confirmed no orphaned containers/volumes/sandboxes. The
two pre-existing sandbox sessions on the host (`phase8-hr-document-report`,
`phase8-hr-payroll-invoice`) were untouched throughout.
