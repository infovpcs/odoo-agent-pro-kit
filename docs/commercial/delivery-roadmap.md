# Commercial Delivery Roadmap

This roadmap runs alongside the technical Docker Sandbox phases. Do not build a
large commercial control plane before proving that partners will pay for the
workflow.

## Stage 0: Product and legal foundation — weeks 1–2

- [ ] Name one product owner and one technical owner.
- [ ] Select the first paid customer profile: small Odoo partner with 5–20
  developers is recommended.
- [ ] Approve the Community/Pro feature matrix in `repository-strategy.md`.
- [ ] Reserve product name/domain after trademark review.
- [ ] Review Apache notices, contribution policy, Pro EULA, support terms,
  privacy/data-processing terms, third-party licenses, and Odoo/Docker naming.
- [ ] Define who pays for Odoo, cloud, Docker governance, model APIs, domains,
  and third-party services.
- [ ] Define data classification: source, database copies, logs, screenshots,
  credentials, usage telemetry, and retention.
- [ ] Create a one-page problem interview script and pilot scorecard.
- [ ] LIVE TEST: conduct five interviews with Odoo partners and record at least
  three problems they already spend money or staff time solving.

Exit gate: at least three partners agree to a pilot with named stakeholders,
repositories/modules in scope, and measurable outcomes.

## Stage 1: Repository and governance setup — weeks 2–3

- [ ] Keep this repository public and document the Community roadmap.
- [ ] Add `NOTICE`, `SECURITY.md`, `TRADEMARKS.md`, and support boundaries after
  review.
- [ ] Create private `vperfectcs/odoo-agent-platform-pro`.
- [ ] Add private license/EULA, CODEOWNERS, branch protection, issue templates,
  secret scanning, dependency scanning, and release workflow.
- [ ] Define the versioned Community-to-Pro contract and compatibility matrix.
- [ ] Add Pro CI that consumes a tagged Community release; do not copy the
  Community tree.
- [ ] Create a private product backlog separated into platform, commercial,
  operations, and customer-validation tracks.
- [ ] LIVE TEST: publish a Community prerelease and demonstrate a private Pro
  smoke test consuming it by version.

Exit gate: public and private repositories can release independently through a
tested compatibility boundary.

## Stage 2: Community sandbox MVP — weeks 3–8

- [ ] Complete Docker Sandbox technical Phases 0–2.
- [ ] Deliver single-session Odoo 19 first, followed by 18 and 17.
- [ ] Keep `sandboxctl`, Compose runtime, schemas, and basic diagnostics public.
- [ ] Publish reproducible installation and one real module walkthrough.
- [ ] Instrument opt-in, privacy-respecting product metrics or collect pilot
  metrics manually.
- [ ] Establish public issue labels for setup, version compatibility, module
  operations, documentation, and feature requests.
- [ ] LIVE TEST: an external developer follows only public documentation and
  completes install, update, test, restart, and cleanup.

Exit gate: three pilot organizations can run the Community foundation without
VPerfectCS manually fixing every environment.

## Stage 3: Paid proof of value — weeks 6–12

- [ ] Sign a short pilot agreement with scope, data handling, support hours,
  success criteria, discounted price, and end date.
- [ ] Charge for onboarding and/or the pilot to validate willingness to pay.
- [ ] Implement the smallest private Partner Edition layer: organization,
  project registry, session allocation, status, logs, and artifact links.
- [ ] Use manual invoicing and entitlement initially; do not build complex
  billing before product-market evidence.
- [ ] Add one valuable report: monthly module quality and upgrade readiness.
- [ ] Hold weekly pilot reviews and categorize feedback as public foundation,
  Pro product, documentation, or service request.
- [ ] Measure onboarding time, sandbox success, defects caught, support effort,
  usage, and partner willingness to renew.
- [ ] LIVE TEST: each design partner completes one production-like module task
  and one failure-recovery scenario through the paid workflow.

Exit gate: at least two of three pilots agree in writing to continue as paying
customers at a stated post-pilot price.

## Stage 4: Partner Edition v1 — months 3–5

- [ ] Package five seats and three concurrent sessions as the initial offer.
- [ ] Add team/project roles, quotas, session retention, activity audit, and Git
  integration.
- [ ] Add Odoo 17/18/19 install/update/RPC/browser quality matrix.
- [ ] Add support portal, severity definitions, response targets, and customer
  onboarding checklist.
- [ ] Add basic subscription entitlement and usage reporting.
- [ ] Publish public comparison of Community and Partner Edition.
- [ ] Create demo video, architecture/security brief, ROI calculator, proposal,
  and standard order form.
- [ ] Train sales and engineering to sell outcomes rather than AI claims.
- [ ] LIVE TEST: onboard a new paying partner using the repeatable checklist,
  without founder-only operational steps.

Exit gate: five paying organizations, documented support cost, and positive
gross margin before expanding the feature surface.

## Stage 5: Upgrade Factory — months 5–8

- [ ] Define supported source/target versions and explicit exclusions.
- [ ] Build continuous empty-database installation and target-version checks.
- [ ] Add upgraded-database rehearsal workflow with safe handling and deletion.
- [ ] Produce prioritized compatibility findings, evidence, and effort ranges.
- [ ] Create reusable functional regression packs by Odoo application area.
- [ ] Separate automatic assessment pricing from engineering remediation.
- [ ] Attach annual readiness monitoring to every completed migration.
- [ ] LIVE TEST: deliver two paid upgrade assessments and compare predicted
  findings/effort with actual remediation work.

Exit gate: assessments are repeatable, reports are trusted, and delivery margin
is measured rather than estimated.

## Stage 6: Managed Cloud and enterprise — months 7–12

- [ ] Validate demand before operating customer source/data in VPerfectCS cloud.
- [ ] Complete threat model, tenant isolation tests, backup/restore, deletion,
  incident response, monitoring, capacity management, and data processing terms.
- [ ] Add metered compute/storage/retention and budget controls.
- [ ] Add SSO/RBAC/audit exports according to signed customer demand.
- [ ] Offer customer-managed deployment for organizations that cannot use a
  shared service.
- [ ] Clarify which Docker governance capabilities require the customer's own
  subscription or a separate commercial arrangement.
- [ ] LIVE TEST: run a controlled beta with synthetic or approved non-production
  data, verify tenant isolation, restore, export, and verified deletion.

Exit gate: security review passes, unit economics are acceptable, and at least
three customers commit to managed or self-hosted enterprise plans.

## Stage 7: Recurring revenue system — ongoing

- [ ] Review monthly recurring revenue, churn, expansion, gross margin, support
  load, capacity, and product usage every month.
- [ ] Run quarterly customer value reviews using defects prevented, onboarding
  time, upgrade readiness, and developer throughput.
- [ ] Convert one-time implementation work into annual maintenance agreements.
- [ ] Maintain public Community releases on a predictable cadence.
- [ ] Publish compatibility updates quickly after supported Odoo releases.
- [ ] Allocate engineering capacity explicitly between Community health, Pro
  roadmap, customer escalations, and security maintenance.
- [ ] Establish a partner referral/reseller program only after direct sales are
  repeatable.
- [ ] LIVE TEST: quarterly disaster recovery, entitlement expiry, customer data
  export/deletion, and Community-to-Pro compatibility exercises.

## Operating cadence

### Weekly

- Product/engineering triage across public and private backlogs.
- Pilot/customer feedback review.
- Build, compatibility, security, and support health review.

### Monthly

- Community release or status update.
- Pro release train where quality gates pass.
- Revenue, usage, infrastructure cost, and support-margin review.
- Customer success report and renewal-risk review.

### Quarterly

- Odoo/Docker/agent compatibility matrix refresh.
- Pricing and packaging review based on usage and sales evidence.
- Security/access review and disaster-recovery exercise.
- Public roadmap update and commercial roadmap reprioritization.

## First 30 days

1. Approve the repository and feature boundary.
2. Interview five partners and recruit three paid/discounted design partners.
3. Create and secure the private Pro repository.
4. Define the Community-Pro schemas and release compatibility contract.
5. Complete the Odoo 19 single-sandbox proof of concept.
6. Demonstrate install/update/test/log/export using a real custom module.
7. Prepare a pilot agreement, onboarding checklist, and scorecard.
8. Begin the first partner pilot before implementing billing or a large UI.

## Definition of done for a commercial feature

- It has a named buyer and measurable value outcome.
- Its Community/Pro ownership is documented.
- Success, failure, audit, and support behavior are specified.
- Security, data retention, licensing, and operating cost are reviewed.
- Documentation, entitlement behavior, telemetry, and migration are covered.
- It is exercised by a LIVE TEST and at least one design partner before general
  availability.
