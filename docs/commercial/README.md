# VPerfectCS Commercial Product Plan

This plan defines how the existing Apache-2.0 Odoo Agent Pro Kit becomes the
community foundation for recurring commercial products without weakening the
open-source project.

## Decision

Maintain two principal repositories:

1. **Public:** `infovpcs/odoo-agent-pro-kit` — community runtime contracts,
   skills, basic single-session sandbox, documentation, examples, and extension
   APIs under Apache-2.0.
2. **Private:** `vperfectcs/odoo-agent-platform-pro` — licensed control plane,
   fleet orchestration, dashboards, organization features, advanced quality and
   upgrade automation, billing/metering adapters, and commercial packaging.

A separate private repository is recommended. Do not maintain Pro as a private
fork of the public repository. Pro should consume versioned Community releases
through documented interfaces. This prevents continual merge conflicts and
allows Community security and compatibility fixes to flow cleanly into Pro.

## Documents

- [`product-options.md`](product-options.md) defines commercial packages,
  customers, value, and revenue mechanics.
- [`repository-strategy.md`](repository-strategy.md) defines public/private
  boundaries, licensing, release flow, and contribution governance.
- [`delivery-roadmap.md`](delivery-roadmap.md) provides the step-by-step product,
  validation, launch, and recurring-revenue plan.

## Product principle

Community proves that the workflow works. Pro makes it manageable across a
team. Cloud removes infrastructure ownership. Services reduce implementation
and upgrade risk.

```text
Community adoption
       |
       v
Developer Pro -> Partner Team -> Enterprise / Managed Cloud
       |               |                    |
       +------- support, upgrades, training-+
```

## Immediate next decision

Before creating Pro code, VPerfectCS should approve:

- the Community/Pro feature boundary;
- the commercial product name and trademark policy;
- the first paid customer profile;
- the licensing model for private artifacts;
- the first three design partners and measurable pilot outcomes.

This is product planning, not legal or tax advice. Have counsel review the
commercial EULA, contributor terms, privacy terms, and use of Odoo/Docker marks.
