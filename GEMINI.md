# Rules for Gemini CLI

The repository's rules are in [AGENTS.md](AGENTS.md): read it before starting work and follow it.

The rule most often missed: **merge into `main` only through a pull request whose checks all
passed on its latest commit**: `CI / validate`, and `Docker Sandbox release / validate`,
`image-build (17-20)` and `compose-smoke (17-20)`. Read `gh pr checks <number>` once more just
before merging. A check that fails on `main` too is still a blocker: fix it first. Details in
AGENTS.md, "Merging into `main`".
