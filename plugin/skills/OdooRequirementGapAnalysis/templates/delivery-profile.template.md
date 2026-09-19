---
title: "Delivery profile - <organisation>"
type: delivery-profile
version: 1
updated: YYYY-MM-DD
---

# Delivery profile - <organisation>

A delivery profile tells `odoo_requirement_gap_analysis` how *this organisation* delivers, so the
generic method can produce a faster, defensible estimate. Keep it private: it holds business content
(rates, catalogue prices, prior engagements) that must not be published with the skill.

Load order: `$GAP_PROFILE`, `./gap_profile.md`, `~/.config/odoo-gap-analysis/profile.md`.
Every reduction below needs an evidence tag (Measured / Catalogue / Pattern / Assumption) and a
confidence level (High / Medium / Low).

## 1. Delivery pipeline and measured evidence

| Capability | What it removes from the estimate | Evidence tag | Source / how measured |
|---|---|---|---|
| e.g. automated lifecycle with sandbox gates | separate module-test and QA effort | Measured / Assumption | path to run logs, benchmark file |

Host capacity for parallel module runs: `<vCPU / RAM / disk>` -> `<max concurrent sessions>` (measured or assumed).

## 2. Factor overrides

| Effort type | Generic factor | Profile factor | Tag | Confidence | Note |
|---|---|---|---|---|---|
| Model and UI | 0.50 | | | | |
| Business logic | 0.55 | | | | |
| Reports and dashboards | 0.55 | | | | |
| Integration | 0.70 | | | | |
| Configuration | 0.80 | | | | |
| Data migration | 0.60 | | | | |
| Testing, UAT, training, go-live | 1.00 | | | | which human activities the pipeline really covers, as a % |

## 3. Reuse catalogue

Where the catalogue lives (repositories, listing URLs, raw export), how to refresh it, and the rules for
using it.

| Field | Value |
|---|---|
| Catalogue sources | paths or URLs of the module repositories per Odoo version |
| Listing export | file with product code, name, version, price, features |
| Inclusion threshold | 70% of the requirement or sub-feature |
| Version policy | published for the target version = ready; older only = port (state port days) |
| Licence / ownership | what the client receives (source, licence, updates), price basis |

### Catalogue candidates by capability (curated, verify in code every time)

| Capability | Module(s) | Versions | Typical coverage | Tag | Note |
|---|---|---|---|---|---|

## 4. Pattern library (know-how from earlier engagements)

Design patterns that can be re-implemented faster because they were built before. Describe the pattern, not
another client's code or data.

| Pattern | Applies to | Typical saving | Tag | Confidence |
|---|---|---|---|---|

## 5. Requirement-change playbook

Organisation-specific wording changes that shorten delivery (replace a side tool by the Odoo app, warn before
block, defer analytics, fit to standard ...). For each: when it is safe, when it needs the client's decision,
the usual trade-off.

## 6. Rate card and commercial terms

Hourly or daily rates, fixed-price items, training rates, what is excluded. Used only to turn person-days into cost.

## 7. Calibration log

| Date | Project / module | Estimated days | Actual days | Pipeline result | Factor updated |
|---|---|---|---|---|---|
