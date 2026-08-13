# Public and Private Repository Strategy

## Why create a separate private Pro repository

Yes, create one when paid code begins. The public repository is Apache-2.0, so
code intentionally published here can be used and redistributed under that
license. Removing it later does not withdraw rights already granted to existing
recipients.

A private repository provides a clean boundary for licensed source, customer
connectors, operational infrastructure, billing, commercial release artifacts,
and security-sensitive deployment details.

## Recommended topology

```text
infovpcs/odoo-agent-pro-kit                 PUBLIC, Apache-2.0
  contracts, CLI, skills, local runtime, schemas, SDK, examples
                         |
                         | versioned packages/releases
                         v
vperfectcs/odoo-agent-platform-pro          PRIVATE, commercial license
  control plane, fleet, dashboard, advanced tests, license checks
                         |
              +----------+-----------+
              |                      |
              v                      v
vperfectcs/platform-deployments   customer configuration repositories
PRIVATE infrastructure           PRIVATE, one repo/project boundary per customer
```

Initially, `platform-deployments` may be a directory in the Pro repository.
Split it once customer credentials, regional deployments, or different operator
permissions require an independent boundary.

## Public repository responsibilities

Keep these public:

- Odoo 17/18/19 coding and testing skills.
- Basic lifecycle commands and context templates.
- Core `sandboxctl` interface and single-session implementation.
- Docker Compose development runtime and public image definitions.
- `manage_modules.sh` local and Compose execution contracts.
- Session/result JSON schemas.
- Extension/plugin interfaces used by Pro.
- Basic logs and local diagnostic collection.
- Small fixture modules and compatibility tests.
- Security disclosures, contribution rules, and public roadmap.

The public project must remain genuinely useful on its own. Otherwise the
community will treat it as a demo rather than infrastructure they can trust.

## Private Pro repository responsibilities

Keep these private:

- Multi-tenant control-plane service and web dashboard.
- Organization, team, project, seat, quota, and concurrency management.
- SSO/SAML, advanced RBAC, audit retention/export, and policy management.
- Scheduler, worker fleet, remote session brokers, and capacity optimization.
- Commercial upgrade-analysis rules and advanced regression packs.
- Long-term artifact history, analytics, executive reporting, and comparisons.
- Billing, metering, subscription entitlement, and license enforcement.
- Hosted-service infrastructure, deployment charts, alerting, and runbooks.
- Premium connectors and customer-specific integrations.
- White-label configuration and commercial support tooling.

## Customer code repositories

Do not copy customer addons into either product repository. Connect or clone
their repositories into isolated sessions. Store only references and approved
metadata in the control plane.

For customer-specific extensions:

- prefer a repository owned by the customer with VPerfectCS access;
- otherwise create a private repository dedicated to that customer;
- define ownership, reuse rights, offboarding/export, and retention in the
  contract;
- never move licensed Enterprise code into Community or generic Pro fixtures.

## Integration contract

Pro should depend on Community through stable, versioned boundaries:

- `sandboxctl` commands and exit codes;
- `session.json` and operation-result schemas;
- versioned OCI images and Docker Sandbox kits/templates;
- optional Python package or API client if later required;
- documented extension points for advanced tests and log exporters.

Pro must not import random Community source files by relative filesystem paths.
It should consume tagged releases, pinned commits, packages, or images.

## Versioning

- Use semantic versioning for Community contracts.
- Publish compatibility metadata from Pro, for example:
  `community >=0.3,<0.5`.
- Pin production artifacts by immutable commit and image digest.
- Allow deprecation for at least one documented minor release before removing a
  public interface.
- Maintain a compatibility matrix for Community, Pro, Odoo, PostgreSQL, Docker
  Sandbox, agents, and supported host platforms.

## Change flow

```text
Community issue/fix
  -> public PR and tests
  -> Community release
  -> Pro compatibility CI
  -> Pro integration/release

Pro-discovered generic bug
  -> sanitize customer context
  -> fix public contract/runtime first
  -> release Community
  -> consume release in Pro

Pro-only feature
  -> private issue/PR
  -> exercise public extension interface
  -> commercial release
```

Avoid copying a bug fix into both repositories. Generic runtime fixes belong in
Community; Pro consumes the corrected release.

## Branching and release policy

### Community

- protected `main`;
- short-lived feature branches;
- pull request, tests, changelog entry, and review;
- signed version tags and public release notes;
- public security policy with private vulnerability reporting.

### Pro

- protected `main` and release branches only when customer support requires it;
- mandatory dependency/secret/license scans;
- Community compatibility CI on every dependency bump;
- signed artifacts and software bill of materials;
- separate development, staging, and production environments;
- customer-visible release notes without private implementation details.

## License and contribution controls

- Retain Apache-2.0 for Community unless there is a compelling, reviewed reason
  to change it.
- Add `NOTICE`, `SECURITY.md`, `TRADEMARKS.md`, and an explicit contribution
  guide before broad external contributions.
- Consider a Developer Certificate of Origin or contributor license agreement
  only after legal review and only if commercial relicensing requires it.
- Put the Pro EULA/license in the private repository and customer contracts.
- Verify third-party dependencies independently in both repositories.
- Never accept code copied from Odoo Enterprise or a customer project into the
  public repository.

## Branding

Use distinct names so “Pro” in the current public repository name does not
confuse editions. A possible family is:

- **Odoo Agent Pro Kit Community** — current public repository.
- **VPerfectCS Odoo Dev Platform** — commercial product.
- **VPerfectCS Partner Edition** — team package.
- **VPerfectCS Upgrade Factory** — upgrade service/product.

Run trademark clearance before committing to names or domains. State clearly
that independent verification is not official Odoo certification.

## Secret and access management

- Require MFA and least-privilege teams for all private repositories.
- Separate product engineering, production operations, and customer-repository
  access.
- Use workload identity or secret managers in CI; never repository secrets in
  files.
- Keep a customer access register and remove access during offboarding.
- Prohibit production database dumps in product repositories and CI artifacts.

## When not to create more repositories

Do not create one repository per feature, Odoo version, agent, or deployment
environment. That produces release and security overhead. Split only for a real
license, ownership, access-control, deployment, or lifecycle boundary.

Recommended starting count: two product repositories—one public Community and
one private Pro—plus customer repositories only when contracts require them.
