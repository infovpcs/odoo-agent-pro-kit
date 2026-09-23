# Deliverables and quality gates

Produce only the formats the user requests. For a full pre-sales package, use a narrative DOCX plus a formula-driven XLSX companion.

## Narrative document

Recommended structure:

1. Executive summary and headline decisions
2. Scope, sources, target version/edition, and method
3. Proposed Odoo solution landscape and external-system boundary
4. Coverage summary by business area
5. Module-wise Fit/Partial/Gap detail
6. Customisation plan, dependencies, and build sequence
7. Edge cases and control coverage
8. Effort scenarios, assumptions, exclusions, and indicative elapsed time
9. Reuse/Apps Store findings and proposed requirement changes, when analyzed
10. Integrations
11. Risks, open questions, and decisions required
12. Appendices for verified modules, requirement notes, and evidence

Keep executive conclusions readable without the workbook. Use tables for repeated mappings and diagrams only when they materially clarify architecture or flow.

## Companion workbook

Recommended sheets:

- Read Me
- Summary
- Requirement Mapping
- App Mapping
- Module Inventory
- Gap & Customisation
- Estimation
- Scenario Estimate, if multiple scenarios are justified
- Requirement Changes, if process/scope alternatives were proposed
- Reuse or Apps Store Mapping, Modules, and Screening, if assessed
- Edge Cases
- Integrations
- Open Questions & Risks

Make inputs visually distinct from formulas and imported evidence. Use data validation for Fit, priority, inclusion flags, confidence, and scope. Prefer formula-linked summaries over copied values. Freeze headers, enable filters, wrap long text, set practical widths, and configure print areas.

## Validation gates

- Reconcile requirement and Fit/Partial/Gap counts between all artifacts.
- Validate unique IDs and all cross-references.
- Verify module names and editions against the target version.
- Check formulas for broken references and divide-by-zero conditions.
- If using `openpyxl`, remember it does not calculate formulas; recalculate with LibreOffice/Excel where available and reopen with `data_only=True` for spot checks.
- Render the complete DOCX and relevant workbook sheets. Inspect for clipping, unreadable tables, accidental blank pages, stale dates, and inconsistent branding.
- Keep source citations human-readable and remove internal tool tokens, absolute private paths, temporary artifacts, and secrets from client deliverables.
