# Community platform validation

Ubuntu 24.04 x86_64 KVM is the currently validated Docker Sandbox runtime.
Apple Silicon macOS and Windows 11/WSL2 are candidate platforms whose runbooks
need community hardware validation. This is intentional: platform support is
promoted from candidate to validated only from reproducible evidence.

## How to contribute a test

1. Fork the repository and start from current `main` in a clean clone.
2. Read `phase-7/operator-runbooks.md` and select the matching platform.
3. Run common preflight and the narrowest safe lifecycle first.
4. If it passes, run the clean-host matrix in `phase-7/release-acceptance.md`.
5. Export or commit useful work, destroy disposable resources, and prove no
   matching sandbox, container, volume, network, or published port remains.
6. Open a **Docker Sandbox platform validation** issue with exact versions,
   commands, results, timings, and redacted evidence.

Never post credentials, OAuth tokens, private keys, customer data, databases,
filestores, private repository contents, or licensed Odoo Enterprise source.

## Bugs and fixes

For a failure, open the platform-validation issue before or with a pull request.
Include the smallest reproducer, expected versus actual behavior, terminal exit
code, bounded timeout, and sanitized diagnostic bundle. Search existing issues
first and add new evidence to a matching issue instead of fragmenting it.

Fixes should be narrowly scoped and preserve the stable controller/Compose
contract. Add regression coverage, update the affected runbook, run
`./scripts/validate.sh`, and link the issue from the pull request. Maintainers
review reports and proposals one by one; passing on one machine does not by
itself establish broad platform support.

## Promotion criteria

A candidate platform may be marked validated after maintainers review:

- a clean-host run using pinned controller, Compose, template, kit, and images;
- complete version and command evidence with no unsupported substitutions;
- lifecycle, cleanup, rollback, and relevant recovery gates;
- repeatable results or independent confirmation when practical;
- documentation and automated regression coverage for discovered differences.

Platform-specific adapters are welcome. Changes that redefine the common Odoo
runtime, weaken isolation, include secrets, or distribute Enterprise source are
not accepted as portability fixes.
