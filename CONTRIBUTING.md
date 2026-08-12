# Contributing to Odoo Agent Pro Kit

Thanks for considering a contribution. This project covers the Odoo 17/18/19
custom application development lifecycle only — please keep contributions
scoped to that.

## Workflow

1. **Fork** this repository.
2. Keep your fork's `main` branch synced with `infovpcs/odoo-agent-pro-kit:main`
   before starting work:
   ```bash
   git remote add upstream https://github.com/infovpcs/odoo-agent-pro-kit.git
   git fetch upstream
   git checkout main && git merge upstream/main
   ```
3. Create a feature branch for your proposal: `git checkout -b my-proposal`.
4. Make your change, then run the repository validation entrypoint:
   ```bash
   ./scripts/validate.sh
   ```
5. Open a pull request against `infovpcs/odoo-agent-pro-kit:main` using the PR
   template — fill in Summary, Motivation, Odoo version(s) affected,
   skill(s)/component(s) touched, testing done, and the checklist.

## Review process

The validation entrypoint runs the repository tests, checks shell syntax and
Git whitespace, and catches broken skill frontmatter or leaked private strings.
A maintainer will review the PR; if the [Claude GitHub App](https://github.com/apps/claude) is
installed on this repository, it may leave an automated first-pass review
comment — that's assistance for the human reviewer, not an automatic merge.
A human maintainer makes the final merge decision.

## Scope guidance

In scope: Odoo 17.0/18.0/19.0 skills, commands, hooks, local setup scripts,
and agent integrations (Claude Code, Codex, Cursor, Antigravity, VS Code,
GitHub Copilot).

Out of scope: mobile/Flutter development, non-Odoo integrations, client- or
business-specific content of any kind, Odoo versions below 17.0.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
