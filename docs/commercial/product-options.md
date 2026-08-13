# Commercial Product Options

## Target customers

### Independent Odoo developer

Needs rapid local setup, repeatable testing, multiple Odoo versions, and less
time diagnosing environment failures. Usually buys a low-cost individual plan.

### Small Odoo partner

Needs standardized onboarding, shared templates, concurrent projects, upgrade
testing, and proof that modules passed validation. Usually buys seats plus a
small concurrency pool.

### Established Odoo partner

Needs customer/project isolation, audit history, SSO/RBAC, policy, private
registries, capacity controls, SLAs, and management reporting.

### Odoo module vendor

Needs continuous install/update testing across supported Odoo versions and a
shareable independent quality report.

### End customer with custom Odoo

Needs predictable maintenance, upgrade readiness, rehearsals, and an expert who
owns compatibility risk.

## Product ladder

### Community Edition — free

- Odoo 17/18/19 skills and lifecycle commands.
- Local setup and basic single-session Compose sandbox.
- `manage_modules.sh` and public runtime contracts.
- Basic module install/update/live-test results.
- Community documentation and issue support.

Purpose: adoption, trust, contributor growth, partner lead generation, and a
stable compatibility foundation.

### Developer Pro — subscription

- Multiple local sandbox sessions.
- Prebuilt and regularly updated development images.
- Session snapshots, richer logs, test history, and comparison reports.
- Premium IDE/agent integrations.
- Upgrade compatibility scans for selected modules.
- Email support and faster release channels.

Planning price: INR 1,499–3,999 per developer/month. Validate willingness to pay
before publishing permanent pricing.

### Partner Team — subscription

- Shared projects, templates, policies, and artifact retention.
- Fleet dashboard and pooled concurrent sandboxes.
- Role-based access at the VPerfectCS application layer.
- Central test matrix for Odoo 17/18/19.
- Git provider integration and pull-request quality gates.
- Monthly engineering quality and upgrade-readiness reports.
- Standard support SLA.

Planning price: INR 15,000–50,000 per organization/month, combining included
seats and concurrent session capacity.

### Enterprise / Self-hosted — annual contract

- Private deployment and registry support.
- SSO, advanced RBAC, audit export, retention controls, and custom policy.
- Enterprise-addon isolation and customer-specific environments.
- High availability or recovery design where required.
- Priority upgrades and contracted SLA.
- Architecture review and implementation hours.

Planning price: INR 3–15 lakh/year plus onboarding and infrastructure. Third-
party licenses and cloud resources are passed through or purchased directly by
the customer.

### Managed Sandbox Cloud — usage plus subscription

- VPerfectCS operates the control plane and sandbox capacity.
- Browser-ready development URLs, snapshots, backups, artifacts, and cleanup.
- Usage limits by active time, CPU/RAM class, storage, and retention.
- Optional dedicated capacity and regional deployment.

Pricing model: platform fee plus included usage, followed by metered overage.
Avoid “unlimited compute” plans.

### Upgrade Factory — recurring plus project work

- Continuous custom-module compatibility assessment.
- Empty-database installability checks on the target version.
- Source/target API and view-change findings.
- Migration-script validation against upgraded database copies.
- Business-flow regression packs and upgrade rehearsal evidence.
- Remediation estimates and optional engineering delivery.

Revenue model:

- annual partner subscription for continuous readiness;
- per-repository or per-module scan allowance;
- paid remediation and migration projects;
- premium rehearsal and go-live support retainers.

### Module Quality Cloud — subscription

- Manifest/dependency validation.
- Clean install, update, uninstall, access, RPC, and browser tests.
- Odoo-version compatibility matrix.
- Release artifacts, historical trend, and independent verification report.

Use wording such as “VPerfectCS Verified.” Do not imply official Odoo
certification or endorsement without written authorization.

### Managed Maintenance — annual recurring service

- Monthly or release-triggered compatibility checks.
- Dependency and image refresh monitoring.
- Quarterly health and technical-debt report.
- Reserved remediation hours.
- Upgrade readiness score and annual rehearsal.
- Contracted response time for critical module failures.

This should attach to every successful custom-development or migration project.

## Packaging rules

- Price **people and predictable capacity** with seats/concurrency bundles.
- Meter expensive resources: compute time, storage, artifact retention, browser
  minutes, and upgrade-database size.
- Keep implementation, migration, and customer-specific test creation outside
  the base subscription.
- Offer annual prepayment discounts only after real usage costs are measured.
- Provide a 14–30 day trial or a paid proof of value with clear conversion
  criteria.
- Grandfather founding customers for a limited contract term, not indefinitely.

## First sellable package

Launch **VPerfectCS Partner Edition** before building a large SaaS platform:

- five named developers;
- three concurrent Odoo sandboxes;
- Odoo 17/18/19 runtime matrix;
- GitHub integration;
- install/update/RPC/browser smoke tests;
- 30-day artifacts and logs;
- one monthly upgrade-readiness report;
- onboarding and standard support.

Pilot target: three Odoo partners for 90 days. Charge a discounted founding
price so pilots demonstrate buying behavior, not only technical interest.

## Metrics

### Product value

- median time from repository clone to healthy Odoo session;
- developer onboarding time;
- module install success rate;
- defects caught before customer UAT;
- upgrade assessment and remediation time;
- sandbox utilization and failed-session recovery rate.

### Commercial health

- monthly and annual recurring revenue;
- pilot-to-paid conversion;
- gross margin after compute/support;
- net revenue retention;
- logo and seat churn;
- expansion from Community to Pro and Team;
- support hours per paying organization;
- services revenue that converts into maintenance subscriptions.

## Product boundaries with third parties

- Customers buy Odoo Enterprise, Odoo.sh, cloud, Docker organization governance,
  and model/API usage directly unless VPerfectCS has an explicit reseller
  agreement.
- VPerfectCS charges for its own software, operation, automation, support,
  reports, training, and professional services.
- Enterprise source and customer databases remain customer-scoped and are never
  included in public images or shared test data.
