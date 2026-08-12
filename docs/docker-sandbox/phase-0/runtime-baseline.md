# Runtime Baseline

Evidence captured on 2026-08-12. Tags are build inputs; Phase 1 lock files must
pin immutable platform-specific digests.

## PostgreSQL

Use PostgreSQL 15 on Debian Bookworm for Odoo 17, 18, and 19 during the initial
runtime matrix. Odoo 17 and 18 documentation supports PostgreSQL 12 or newer,
and the official Odoo images install a current PostgreSQL client. A single major
reduces matrix size while remaining conservative and supported.

Initial input: `postgres:15-bookworm`. Observed multi-platform index digest:
`sha256:e8db9bd3e9e1751eb639fb17be53cc6d1b62a322adf75b99e791767a7a16ce69`
(PostgreSQL 15.18). It includes Linux amd64 and arm64/v8 manifests.

This is a development default, not a promise that customer production databases
must use PostgreSQL 15. Phase 2 must test every Odoo version against the pinned
image before the choice becomes a released compatibility guarantee.

## Official Odoo image availability

`docker buildx imagetools inspect` confirmed these official tags and platforms:

| Odoo | Observed index digest | linux/amd64 | linux/arm64/v8 |
| --- | --- | --- | --- |
| 17.0 | `sha256:4959237918da385a5befe007fc95177bc2244c048ebc55097b7aa71c703e70ba` | yes | yes |
| 18.0 | `sha256:4ea9b4667921130add13c1b859aa170a4572b5c3c3d747bfb0ef152fdb0b48a7` | yes | yes |
| 19.0 | `sha256:94a4f480b8039dc9ca2bca9e77e59f97d3311f66e2aad663cf2670be9c66d4ea` | yes | yes |

These observations prove registry availability only. They do not replace the
per-platform pull, boot, install, and test gates in Phases 1 and 2.

## Edition and addon boundary

- Public images contain only the official Odoo Community base image, public
  dependencies, this repository's public tooling, and synthetic fixtures.
- Odoo Enterprise source is never copied into an image, kit, fixture, cache,
  diagnostic bundle, or repository.
- A licensed user may explicitly mount an authorized Enterprise addons checkout
  read-only into one private session through the `enterprise` Compose profile.
- Customer addons use a session-owned Git clone. Customer databases are allowed
  only when explicitly approved, non-production, and covered by a retention and
  deletion decision.
- Logs and exports redact credentials and exclude addon source by default.

## Initial local defaults

Defaults are conservative starting values and remain configurable per session:

| Control | Default |
| --- | --- |
| Maximum active Community sessions | 3 |
| Sandbox CPU target | 4 vCPU |
| Sandbox memory target | 8 GiB |
| Sandbox disk budget | 40 GiB |
| Odoo container memory | 3 GiB |
| PostgreSQL container memory | 2 GiB |
| Readiness timeout | 180 seconds |
| Operation timeout | 15 minutes |
| Idle stop | 60 minutes |
| Stopped-session retention | 7 days |
| Diagnostic/result retention | 14 days |
| Maximum diagnostic bundle | 250 MiB |

If the pinned `sbx` version cannot enforce an outer resource value, the
controller records it as an advisory target and enforces the inner Compose and
retention controls it owns. Phase 7 replaces these starting values with measured
capacity guidance.

## Sources

- [Odoo 17 source installation](https://www.odoo.com/documentation/17.0/administration/on_premise/source.html)
- [Odoo 18 source installation](https://www.odoo.com/documentation/18.0/administration/on_premise/source.html)
- [Official Odoo Docker source](https://github.com/odoo/docker)
- [Official Odoo image](https://hub.docker.com/_/odoo)
- [Official PostgreSQL image](https://hub.docker.com/_/postgres)
