# Odoo Pipeline Hooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert this repo's moment-naming rules (command gates, a version-aware Odoo 17/18/19 coding-standard linter, sandbox operation-result verification, and git/secret/Enterprise-source guardrails) into deterministic hooks that fire in both Claude Code and Hermes, plus a contributor-only `.claude/settings.json` for the `AGENTS.md` phase workflow.

**Architecture:** One runtime-agnostic pure-function check library under `plugin/hooks/checks/`. A `uv` single-file dispatcher `plugin/hooks/odoo_hook.py` wires it to Claude Code events via `plugin/hooks/hooks.json`. A `hermes_adapter.py` + additions to `plugin/__init__.py` `register()` wire the same checks to Hermes `pre_tool_call` / `post_tool_call` / extended `on_session_start` / `on_session_end` and the slash-command handlers. A separate `scripts/contributor_hook.py` + repo-root `.claude/settings.json` enforce the phase-workflow rules for contributors.

**Tech Stack:** Python 3.10+ (stdlib only — no third-party deps in hook code), pytest (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests`), Claude Code hooks JSON, Hermes plugin `register(ctx)` API, bash.

**Spec:** `docs/superpowers/specs/2026-08-27-odoo-pipeline-hooks-design.md`

## Global Constraints

- Python **stdlib only** in every file under `plugin/hooks/` and `scripts/contributor_hook.py`. No `pydantic`, no `requests`, no `uv`-installed deps. (The Hermes plugin declares those deps but hook check code must not import them.)
- Every hook entry point (`odoo_hook.py` event handlers, `hermes_adapter` functions, `contributor_hook.py`) wraps its body in `try/except Exception` and **exits 0 / returns "allow" on any exception** (fail-open). A hook bug must never break a turn.
- Hooks **no-op fast** (exit 0, no output) when `plugin/hooks/checks/common.py::in_odoo_module(cwd)` is False or `hooks_disabled()` is True (`ODOO_KIT_HOOKS_DISABLED=1`).
- `Stop` hook honours `stop_hook_active` from the payload — exit 0 immediately if set.
- Exit codes (Claude Code): `0` = allow (stdout injected for `SessionStart` / `UserPromptSubmit`); `2` = block (stderr shown to the agent); any other = non-blocking error.
- Linter `severity == "block"` is used **only** where the pattern causes a real install/RPC failure on that Odoo version. Everything else is `severity == "warn"` (advisory, never exits 2).
- Test runner is always invoked as `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q <path>` (the global conda env auto-loads an incompatible `pytest-asyncio`).
- New test files live under `tests/hooks/`. New non-test Python lives under `plugin/hooks/checks/` except the dispatcher (`plugin/hooks/odoo_hook.py`) and the contributor hook (`scripts/contributor_hook.py`).
- Dataclasses only — no external schema libs. Use `from __future__ import annotations` in every new module.
- Commit after every task with a `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` trailer. Do not push, tag, or open PRs.
- Plugin version bump: `0.4.0` -> `0.5.0` in **both** `plugin/.claude-plugin/plugin.json` and `plugin/plugin.yaml` (Task 13 only).

---

## File Structure

**New — check library (`plugin/hooks/checks/`):**

| File | Responsibility |
| --- | --- |
| `__init__.py` | Empty package marker. |
| `common.py` | Dataclasses (`Finding`, `Violation`, `Gate`, `OperationResult`), `in_odoo_module`, `hooks_disabled`, `find_module_dir`, `repo_root`. |
| `version.py` | `detect_odoo_version(cwd) -> "17" \| "18" \| "19" \| None`. |
| `guard.py` | `classify_bash(command, *, vcs_allowed) -> list[Violation]`. |
| `paths.py` | `scan_write(target_path, content, repo_root) -> list[Violation]`. |
| `gates.py` | `check_start_coding(module_dir) -> Gate`, `check_testing(module_dir) -> Gate`. |
| `authz.py` | `vcs_write_allowed(cwd) -> bool`. |
| `odoo_lint.py` | `lint(path, content, version) -> list[Finding]` (rules L1–L8). |
| `sandbox_result.py` | `read_operation_result(bash_command, cwd) -> OperationResult \| None`. |
| `hermes_adapter.py` | Translates Hermes hook kwargs into the check calls above; returns Hermes-shaped directives / advisory strings. |

**New — dispatchers:**

| File | Responsibility |
| --- | --- |
| `plugin/hooks/odoo_hook.py` | `uv` single-file script. `odoo_hook.py <Event>`, reads Claude Code stdin JSON, routes to `checks/`, exits 0/2. Fail-open. |
| `scripts/contributor_hook.py` | Repo-contributor hook: `contributor_hook.py <Event>`, same contract, enforces `AGENTS.md` phase rules. |
| `.claude/settings.json` | Repo-root Claude Code settings referencing `contributor_hook.py`. Not shipped in the plugin package. |

**Modified:**

| File | Change |
| --- | --- |
| `plugin/hooks/hooks.json` | Add `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `SessionEnd`; add `odoo_hook.py` to `SessionStart`; move MCP cleanup off `Stop`. |
| `plugin/__init__.py` | `register()`: add `pre_tool_call` / `post_tool_call` hooks, extend `_on_session_start` / `_on_session_end`, add a `gates` pre-check inside the `start-coding` / `testing` command handlers. Update the final log line + count. |
| `plugin/plugin.yaml` | `version: "0.5.0"`, extend `provides_hooks`. |
| `plugin/.claude-plugin/plugin.json` | `"version": "0.5.0"`. |
| `scripts/validate.sh` | Add hook smoke test + `py_compile` for new files. |
| `plugin/skills/CommandingSystem/SKILL.md` | "Deterministic hooks" section. |
| `AGENTS.md` | Note `.claude/settings.json` backs the phase rules. |
| `README.md` | Hooks in the feature list. |
| `CHANGELOG.md` | New `0.5.0` entry. |
| `plugin/hooks/cleanup_mcp.sh` | Keep as-is (still callable); no longer referenced from `hooks.json` `Stop`. |

---

## Task 1: Check library scaffold + `common.py`

**Files:**
- Create: `plugin/hooks/checks/__init__.py` (empty)
- Create: `plugin/hooks/checks/common.py`
- Test: `tests/hooks/__init__.py` (empty), `tests/hooks/test_common.py`

**Interfaces:**
- Produces:
  - `@dataclass Finding(severity: str, rule: str, line: int, message: str, fix: str)`
  - `@dataclass Violation(kind: str, message: str, lift_hint: str)`
  - `@dataclass Gate(ok: bool, message: str)`
  - `@dataclass OperationResult(status: str, module_state_ok: bool, reason: str, result_path: str)`
  - `hooks_disabled() -> bool` — True iff env `ODOO_KIT_HOOKS_DISABLED` in `{"1","true","yes"}`
  - `repo_root(start: Path | None = None) -> Path | None` — walk up for a `.git` dir
  - `find_module_dir(start: Path | None = None) -> Path | None` — walk up from `start` (default cwd) for the first dir containing `docs/tasks.md`, else the first dir that has a `17.0`/`18.0`/`19.0` child, else `None`
  - `in_odoo_module(cwd: Path | None = None) -> bool` — `find_module_dir(cwd) is not None`

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_common.py
from __future__ import annotations
import os
from pathlib import Path
import pytest
from plugin.hooks.checks import common


def test_hooks_disabled_reads_env(monkeypatch):
    monkeypatch.delenv("ODOO_KIT_HOOKS_DISABLED", raising=False)
    assert common.hooks_disabled() is False
    monkeypatch.setenv("ODOO_KIT_HOOKS_DISABLED", "1")
    assert common.hooks_disabled() is True


def test_find_module_dir_by_tasks_md(tmp_path):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t1\n")
    nested = mod / "models"
    nested.mkdir()
    assert common.find_module_dir(nested) == mod


def test_find_module_dir_by_version_dir(tmp_path):
    ws = tmp_path / "ws"
    (ws / "19.0").mkdir(parents=True)
    assert common.find_module_dir(ws) == ws


def test_find_module_dir_none(tmp_path):
    assert common.find_module_dir(tmp_path) is None
    assert common.in_odoo_module(tmp_path) is False


def test_dataclasses_construct():
    f = common.Finding(severity="block", rule="L1", line=3, message="m", fix="x")
    assert f.severity == "block"
    assert common.Gate(ok=False, message="redirect").ok is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_common.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'plugin.hooks.checks'`

- [ ] **Step 3: Write minimal implementation**

```python
# plugin/hooks/checks/__init__.py
```

(empty file)

```python
# plugin/hooks/checks/common.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_TRUE = {"1", "true", "yes", "on"}


@dataclass
class Finding:
    severity: str  # "block" | "warn"
    rule: str
    line: int
    message: str
    fix: str


@dataclass
class Violation:
    kind: str
    message: str
    lift_hint: str = ""


@dataclass
class Gate:
    ok: bool
    message: str = ""


@dataclass
class OperationResult:
    status: str
    module_state_ok: bool
    reason: str
    result_path: str


def hooks_disabled() -> bool:
    return os.environ.get("ODOO_KIT_HOOKS_DISABLED", "").strip().lower() in _TRUE


def repo_root(start: Optional[Path] = None) -> Optional[Path]:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def find_module_dir(start: Optional[Path] = None) -> Optional[Path]:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "docs" / "tasks.md").is_file():
            return candidate
    for candidate in (current, *current.parents):
        if any((candidate / v).is_dir() for v in ("17.0", "18.0", "19.0")):
            return candidate
    return None


def in_odoo_module(cwd: Optional[Path] = None) -> bool:
    return find_module_dir(cwd) is not None
```

Also create empty `tests/hooks/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_common.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add plugin/hooks/checks/__init__.py plugin/hooks/checks/common.py tests/hooks/
git commit -m "feat(hooks): check library scaffold + common dataclasses/guards

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 2: `version.py` — Odoo version detection

**Files:**
- Create: `plugin/hooks/checks/version.py`
- Test: `tests/hooks/test_version.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `detect_odoo_version(cwd: Path | None = None) -> str | None` returning `"17"`, `"18"`, `"19"`, or `None`. Resolution order: (1) `.sandbox/session.json` `odoo_version` (walk up from cwd to find it); (2) a `17.0`/`18.0`/`19.0` directory that is a sibling or child of the module dir from `common.find_module_dir`; (3) `docs/module_meta.md` regex `(?:odoo[_ ]?version|version)\s*[:=]\s*"?(1[789])`; (4) env `DEFAULT_ODOO_VERSION` (accept `"17"`, `"17.0"`); (5) `None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_version.py
from __future__ import annotations
import json
from plugin.hooks.checks import version


def test_from_sandbox_session(tmp_path, monkeypatch):
    (tmp_path / ".sandbox").mkdir()
    (tmp_path / ".sandbox" / "session.json").write_text(json.dumps({"odoo_version": "18.0"}))
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(tmp_path) == "18"


def test_from_version_dir(tmp_path, monkeypatch):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t\n")
    (mod / "19.0").mkdir()
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(mod) == "19"


def test_from_module_meta(tmp_path, monkeypatch):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t\n")
    (mod / "docs" / "module_meta.md").write_text("odoo_version: 17.0\n")
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(mod) == "17"


def test_from_env_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", "18.0")
    assert version.detect_odoo_version(tmp_path) == "18"


def test_none_when_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(tmp_path) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_version.py -v`
Expected: FAIL — `ModuleNotFoundError` / `AttributeError: detect_odoo_version`

- [ ] **Step 3: Write minimal implementation**

```python
# plugin/hooks/checks/version.py
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from .common import find_module_dir

_META_RE = re.compile(r"(?:odoo[_ ]?version|version)\s*[:=]\s*\"?(1[789])", re.IGNORECASE)


def _norm(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    m = re.match(r"\s*(1[789])", str(raw))
    return m.group(1) if m else None


def detect_odoo_version(cwd: Optional[Path] = None) -> Optional[str]:
    start = (cwd or Path.cwd()).resolve()

    for candidate in (start, *start.parents):
        session = candidate / ".sandbox" / "session.json"
        if session.is_file():
            try:
                data = json.loads(session.read_text(encoding="utf-8"))
                v = _norm(data.get("odoo_version"))
                if v:
                    return v
            except (OSError, ValueError):
                pass
            break

    module_dir = find_module_dir(start)
    if module_dir is not None:
        for v in ("19", "18", "17"):
            if (module_dir / f"{v}.0").is_dir() or (module_dir.parent / f"{v}.0").is_dir():
                return v
        meta = module_dir / "docs" / "module_meta.md"
        if meta.is_file():
            try:
                m = _META_RE.search(meta.read_text(encoding="utf-8", errors="replace"))
                if m:
                    return m.group(1)
            except OSError:
                pass

    return _norm(os.environ.get("DEFAULT_ODOO_VERSION"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_version.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add plugin/hooks/checks/version.py tests/hooks/test_version.py
git commit -m "feat(hooks): Odoo 17/18/19 version detection

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 3: `guard.py` — Bash command classification

**Files:**
- Create: `plugin/hooks/checks/guard.py`
- Test: `tests/hooks/test_guard.py`

**Interfaces:**
- Consumes: `common.Violation`.
- Produces: `classify_bash(command: str, *, vcs_allowed: bool) -> list[Violation]`. Returns a `Violation` for each of:
  - `kind="raw_odoo_bin"` — command runs `odoo-bin` / `odoo bin` / `python .../odoo-bin` directly (not via `sandboxctl` or `manage_modules.sh`).
  - `kind="manage_modules_direct"` — invokes `./manage_modules.sh` or `manage_modules.sh` without a leading `bash ` (must be `bash manage_modules.sh`).
  - `kind="vcs_write"` — `git push`, `git merge`, `git tag`, `git commit --amend`, `git rebase`, `gh pr create`, `gh pr merge`, `gh release` — **only when `vcs_allowed` is False**.
  - `kind="destructive_cleanup"` — `sbx rm`/`sbx delete --all`, `docker system prune`, `docker volume rm`, `rm -rf` targeting `.sandbox` or a workspace root — **only when `vcs_allowed` is False** (same authorization marker gates it).
- Each `Violation.message` names what was blocked; `Violation.lift_hint` is the exact corrected command or the env var to set.

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_guard.py
from __future__ import annotations
from plugin.hooks.checks import guard


def _kinds(vs):
    return sorted(v.kind for v in vs)


def test_raw_odoo_bin_blocked():
    vs = guard.classify_bash("python3 odoo-bin -d test -i sale --stop-after-init", vcs_allowed=True)
    assert "raw_odoo_bin" in _kinds(vs)


def test_sandboxctl_not_flagged():
    vs = guard.classify_bash("sandbox/bin/sandboxctl module s-1 install mymod", vcs_allowed=True)
    assert vs == []


def test_manage_modules_direct_blocked():
    vs = guard.classify_bash("./manage_modules.sh update mymod", vcs_allowed=True)
    assert "manage_modules_direct" in _kinds(vs)


def test_manage_modules_via_bash_ok():
    vs = guard.classify_bash("WORKSPACE_PATH=$(pwd) bash manage_modules.sh update mymod", vcs_allowed=True)
    assert vs == []


def test_git_push_blocked_when_not_allowed():
    vs = guard.classify_bash("git push origin main", vcs_allowed=False)
    assert "vcs_write" in _kinds(vs)


def test_git_push_allowed_when_authorized():
    vs = guard.classify_bash("git push origin main", vcs_allowed=True)
    assert vs == []


def test_git_commit_plain_ok():
    vs = guard.classify_bash("git commit -m 'x'", vcs_allowed=False)
    assert vs == []


def test_gh_release_blocked():
    vs = guard.classify_bash("gh release create v1.2.3", vcs_allowed=False)
    assert "vcs_write" in _kinds(vs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_guard.py -v`
Expected: FAIL — `ModuleNotFoundError` / `AttributeError: classify_bash`

- [ ] **Step 3: Write minimal implementation**

```python
# plugin/hooks/checks/guard.py
from __future__ import annotations

import re
from typing import List

from .common import Violation

_ODOO_BIN_RE = re.compile(r"(?<![\w./-])odoo[-_ ]bin(?![\w-])")
_SANDBOXCTL_RE = re.compile(r"\bsandboxctl\b")
_MANAGE_DIRECT_RE = re.compile(r"(?<!bash )(?<!bash\s)(\./)?manage_modules\.sh\b")
_MANAGE_ANY_RE = re.compile(r"manage_modules\.sh\b")
_VCS_RES = [
    (re.compile(r"\bgit\s+push\b"), "git push"),
    (re.compile(r"\bgit\s+merge\b"), "git merge"),
    (re.compile(r"\bgit\s+tag\b"), "git tag"),
    (re.compile(r"\bgit\s+commit\b[^\n]*--amend\b"), "git commit --amend"),
    (re.compile(r"\bgit\s+rebase\b"), "git rebase"),
    (re.compile(r"\bgh\s+pr\s+create\b"), "gh pr create"),
    (re.compile(r"\bgh\s+pr\s+merge\b"), "gh pr merge"),
    (re.compile(r"\bgh\s+release\b"), "gh release"),
]
_DESTRUCTIVE_RES = [
    re.compile(r"\bsbx\s+(rm|delete|destroy)\b"),
    re.compile(r"\bdocker\s+system\s+prune\b"),
    re.compile(r"\bdocker\s+volume\s+rm\b"),
    re.compile(r"\brm\s+-rf?\b[^\n]*\.sandbox\b"),
]


def classify_bash(command: str, *, vcs_allowed: bool) -> List[Violation]:
    cmd = command or ""
    out: List[Violation] = []

    if _ODOO_BIN_RE.search(cmd) and not _SANDBOXCTL_RE.search(cmd):
        out.append(Violation(
            kind="raw_odoo_bin",
            message="Raw odoo-bin invocation is not allowed from a skill/agent.",
            lift_hint="Route through `sandbox/bin/sandboxctl module <session> install|update|test <module>` "
                      "(sandbox mode) or `bash manage_modules.sh install|update <module>` (local mode).",
        ))

    if _MANAGE_ANY_RE.search(cmd) and not re.search(r"\bbash\s+(\./)?manage_modules\.sh\b", cmd):
        out.append(Violation(
            kind="manage_modules_direct",
            message="manage_modules.sh must be invoked via an explicit `bash` (macOS default shell is zsh).",
            lift_hint="Use `WORKSPACE_PATH=$(pwd) bash manage_modules.sh <args>` — never `./manage_modules.sh`.",
        ))

    if not vcs_allowed:
        for rx, label in _VCS_RES:
            if rx.search(cmd):
                out.append(Violation(
                    kind="vcs_write",
                    message=f"`{label}` requires explicit user authorization.",
                    lift_hint="Set ODOO_KIT_ALLOW_VCS_WRITE=1 or create a .sandbox/AUTHORIZED marker "
                              "after the user approves the push/merge/tag/release.",
                ))
                break
        for rx in _DESTRUCTIVE_RES:
            if rx.search(cmd):
                out.append(Violation(
                    kind="destructive_cleanup",
                    message="Destructive sandbox/docker cleanup requires explicit user authorization.",
                    lift_hint="Set ODOO_KIT_ALLOW_VCS_WRITE=1 or create .sandbox/AUTHORIZED after user approval.",
                ))
                break

    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_guard.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add plugin/hooks/checks/guard.py tests/hooks/test_guard.py
git commit -m "feat(hooks): Bash command guard (odoo-bin, manage_modules, vcs, cleanup)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 4: `paths.py` — Write/Edit target scan

**Files:**
- Create: `plugin/hooks/checks/paths.py`
- Test: `tests/hooks/test_paths.py`

**Interfaces:**
- Consumes: `common.Violation`.
- Produces: `scan_write(target_path: str, content: str | None, repo_root: Path) -> list[Violation]`. Flags a write **only when `target_path` resolves inside `repo_root`** and any of:
  - `kind="enterprise_source"` — path contains a segment matching `ent-1[789]`, `enterprise`, `web_studio`, or content contains `"license": "OEEL-1"` / `OPL-1` / `Odoo Enterprise Edition License`.
  - `kind="secret_material"` — content matches `-----BEGIN [A-Z ]*PRIVATE KEY-----`, `AKIA[0-9A-Z]{16}`, `xox[baprs]-[0-9A-Za-z-]{10,}`, `ghp_[0-9A-Za-z]{36}`, or a `.env`-style line with a non-empty value for a key containing `KEY`/`TOKEN`/`SECRET`/`PASSWORD` (and the path is not `*.env.example` / `*.sample`).
  - `kind="customer_data"` — path matches an entry from an optional untracked deny-list file `plugin/hooks/checks/customer_denylist.txt` (one glob per line, `#` comments); missing file = no customer-data checks.
- `Violation.lift_hint` explains the correct location (outside the repo, `.env` outside any git repo, etc.).

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_paths.py
from __future__ import annotations
from plugin.hooks.checks import paths


def _kinds(vs):
    return sorted(v.kind for v in vs)


def test_enterprise_path_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / "addons" / "web_studio" / "x.py"), "x = 1\n", tmp_path)
    assert "enterprise_source" in _kinds(vs)


def test_enterprise_license_content_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / "mymod" / "__manifest__.py"),
                          '{"name": "x", "license": "OEEL-1"}\n', tmp_path)
    assert "enterprise_source" in _kinds(vs)


def test_private_key_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    body = "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----\n"
    vs = paths.scan_write(str(tmp_path / "notes.txt"), body, tmp_path)
    assert "secret_material" in _kinds(vs)


def test_env_example_not_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / ".env.example"), "API_TOKEN=\n", tmp_path)
    assert vs == []


def test_outside_repo_not_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    outside = tmp_path.parent / "elsewhere" / "secret.txt"
    vs = paths.scan_write(str(outside), "ghp_" + "a" * 36, tmp_path)
    assert vs == []


def test_clean_write_ok(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / "mymod" / "models" / "m.py"), "class X: pass\n", tmp_path)
    assert vs == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_paths.py -v`
Expected: FAIL — `ModuleNotFoundError` / `AttributeError: scan_write`

- [ ] **Step 3: Write minimal implementation**

```python
# plugin/hooks/checks/paths.py
from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import List, Optional

from .common import Violation

_ENT_PATH_RE = re.compile(r"(^|/)(ent-1[789]|enterprise|web_studio)(/|$)")
_ENT_CONTENT_RE = re.compile(r"OEEL-1|OPL-1|Odoo Enterprise Edition License")
_SECRET_RES = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    re.compile(r"ghp_[0-9A-Za-z]{36}"),
]
_ENV_LINE_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)[A-Za-z0-9_]*)\s*=\s*(\S.*)$",
    re.MULTILINE,
)
_DENYLIST = Path(__file__).with_name("customer_denylist.txt")


def _load_denylist() -> List[str]:
    if not _DENYLIST.is_file():
        return []
    out = []
    for line in _DENYLIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def scan_write(target_path: str, content: Optional[str], repo_root: Path) -> List[Violation]:
    out: List[Violation] = []
    try:
        target = Path(target_path).resolve()
        root = Path(repo_root).resolve()
    except (OSError, RuntimeError):
        return out

    try:
        rel = target.relative_to(root)
    except ValueError:
        return out  # not inside the repo — not our concern

    rel_str = str(rel)
    body = content or ""
    name = target.name.lower()
    is_sample = name.endswith((".example", ".sample", ".template")) or ".env.example" in name

    if _ENT_PATH_RE.search("/" + rel_str) or _ENT_CONTENT_RE.search(body):
        out.append(Violation(
            kind="enterprise_source",
            message=f"Refusing to write licensed Odoo Enterprise material into the repo: {rel_str}",
            lift_hint="Keep Enterprise source in your licensed clone (e.g. ~/workspace/ent-19), never in this repo.",
        ))

    if not is_sample:
        if any(rx.search(body) for rx in _SECRET_RES):
            out.append(Violation(
                kind="secret_material",
                message=f"Refusing to write secret material into the repo: {rel_str}",
                lift_hint="Put credentials in a .env outside any git repo (e.g. ~/.hermes/.env, chmod 600).",
            ))
        elif _ENV_LINE_RE.search(body):
            out.append(Violation(
                kind="secret_material",
                message=f"Refusing to write a populated secret env var into the repo: {rel_str}",
                lift_hint="Use a *.env.example with empty values; keep real values outside the repo.",
            ))

    for pattern in _load_denylist():
        if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch("/" + rel_str, pattern):
            out.append(Violation(
                kind="customer_data",
                message=f"Path matches the customer-data deny-list: {rel_str}",
                lift_hint="Client source/data must not be committed to this pipeline repo.",
            ))
            break

    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_paths.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add plugin/hooks/checks/paths.py tests/hooks/test_paths.py
git commit -m "feat(hooks): Write/Edit scan for Enterprise source and secrets

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 5: `gates.py` — command prerequisite checks

**Files:**
- Create: `plugin/hooks/checks/gates.py`
- Test: `tests/hooks/test_gates.py`

**Interfaces:**
- Consumes: `common.Gate`.
- Produces:
  - `check_start_coding(module_dir: Path) -> Gate` — `ok` iff `module_dir/docs/tasks.md` exists. `message` on failure: the auto-bootstrap redirect text ("PRD files missing … run /plan-analysis … then resume").
  - `check_testing(module_dir: Path) -> Gate` — `ok` iff `docs/tasks.md` exists, has **no** `- [ ]` lines, **and** `module_dir/sessions/<module_dir.name>_progress.json` exists with `backend_tests_passed == true`. `message` on failure names the specific unmet condition and the redirect to `/start-coding`.
  - Both accept `module_dir=None` -> `Gate(ok=True)` (nothing to gate; not in a workspace).

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_gates.py
from __future__ import annotations
import json
from plugin.hooks.checks import gates


def _mk(tmp_path, tasks="- [x] a\n- [x] b\n", passed=True):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text(tasks)
    (mod / "sessions").mkdir()
    (mod / "sessions" / "mymod_progress.json").write_text(json.dumps({"backend_tests_passed": passed}))
    return mod


def test_start_coding_ok(tmp_path):
    mod = _mk(tmp_path)
    assert gates.check_start_coding(mod).ok is True


def test_start_coding_missing_tasks(tmp_path):
    mod = tmp_path / "empty"
    mod.mkdir()
    g = gates.check_start_coding(mod)
    assert g.ok is False and "plan-analysis" in g.message


def test_testing_ok(tmp_path):
    mod = _mk(tmp_path)
    assert gates.check_testing(mod).ok is True


def test_testing_incomplete_tasks(tmp_path):
    mod = _mk(tmp_path, tasks="- [x] a\n- [ ] b\n")
    g = gates.check_testing(mod)
    assert g.ok is False and "start-coding" in g.message


def test_testing_backend_not_passed(tmp_path):
    mod = _mk(tmp_path, passed=False)
    g = gates.check_testing(mod)
    assert g.ok is False and "backend" in g.message.lower()


def test_none_module_dir_ok(tmp_path):
    assert gates.check_start_coding(None).ok is True
    assert gates.check_testing(None).ok is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_gates.py -v`
Expected: FAIL — `ModuleNotFoundError` / `AttributeError`

- [ ] **Step 3: Write minimal implementation**

```python
# plugin/hooks/checks/gates.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from .common import Gate

_OPEN_TASK_RE = re.compile(r"^\s*- \[ \]", re.MULTILINE)


def check_start_coding(module_dir: Optional[Path]) -> Gate:
    if module_dir is None:
        return Gate(ok=True)
    if (module_dir / "docs" / "tasks.md").is_file():
        return Gate(ok=True)
    return Gate(
        ok=False,
        message=(
            f"/start-coding blocked: PRD files missing for '{module_dir.name}' "
            "(docs/tasks.md not found). Run `/plan-analysis <version> "
            f"{module_dir.name}` to generate requirements.md / design.md / tasks.md / "
            "module_meta.md, then resume /start-coding."
        ),
    )


def check_testing(module_dir: Optional[Path]) -> Gate:
    if module_dir is None:
        return Gate(ok=True)
    tasks = module_dir / "docs" / "tasks.md"
    if not tasks.is_file():
        return Gate(
            ok=False,
            message=(
                f"/testing blocked: docs/tasks.md not found for '{module_dir.name}'. "
                f"Run `/start-coding <version> {module_dir.name}` first."
            ),
        )
    try:
        text = tasks.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return Gate(ok=True)
    if _OPEN_TASK_RE.search(text):
        return Gate(
            ok=False,
            message=(
                f"/testing blocked: '{module_dir.name}' has incomplete tasks in "
                f"docs/tasks.md. Route to `/start-coding <version> {module_dir.name}` "
                "to finish them first."
            ),
        )
    progress = module_dir / "sessions" / f"{module_dir.name}_progress.json"
    passed = False
    if progress.is_file():
        try:
            passed = bool(json.loads(progress.read_text(encoding="utf-8")).get("backend_tests_passed"))
        except (OSError, ValueError):
            passed = False
    if not passed:
        return Gate(
            ok=False,
            message=(
                f"/testing blocked: backend tests not confirmed passed for "
                f"'{module_dir.name}' (sessions/{module_dir.name}_progress.json "
                "backend_tests_passed != true). Route to `/start-coding`."
            ),
        )
    return Gate(ok=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_gates.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add plugin/hooks/checks/gates.py tests/hooks/test_gates.py
git commit -m "feat(hooks): /start-coding and /testing prerequisite gates

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 6: `authz.py` — VCS-write authorization marker

**Files:**
- Create: `plugin/hooks/checks/authz.py`
- Test: `tests/hooks/test_authz.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `vcs_write_allowed(cwd: Path | None = None) -> bool` — True iff env `ODOO_KIT_ALLOW_VCS_WRITE` in `{"1","true","yes","on"}` **or** a `.sandbox/AUTHORIZED` file exists in the repo root (walk up via `common.repo_root`) or in `cwd`.

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_authz.py
from __future__ import annotations
from plugin.hooks.checks import authz


def test_env_grants(monkeypatch, tmp_path):
    monkeypatch.setenv("ODOO_KIT_ALLOW_VCS_WRITE", "1")
    assert authz.vcs_write_allowed(tmp_path) is True


def test_marker_grants(monkeypatch, tmp_path):
    monkeypatch.delenv("ODOO_KIT_ALLOW_VCS_WRITE", raising=False)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".sandbox").mkdir()
    (tmp_path / ".sandbox" / "AUTHORIZED").write_text("ok\n")
    assert authz.vcs_write_allowed(tmp_path) is True


def test_default_denied(monkeypatch, tmp_path):
    monkeypatch.delenv("ODOO_KIT_ALLOW_VCS_WRITE", raising=False)
    (tmp_path / ".git").mkdir()
    assert authz.vcs_write_allowed(tmp_path) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_authz.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# plugin/hooks/checks/authz.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .common import repo_root

_TRUE = {"1", "true", "yes", "on"}


def vcs_write_allowed(cwd: Optional[Path] = None) -> bool:
    if os.environ.get("ODOO_KIT_ALLOW_VCS_WRITE", "").strip().lower() in _TRUE:
        return True
    start = (cwd or Path.cwd()).resolve()
    candidates = [start / ".sandbox" / "AUTHORIZED"]
    root = repo_root(start)
    if root is not None:
        candidates.append(root / ".sandbox" / "AUTHORIZED")
    return any(c.is_file() for c in candidates)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_authz.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add plugin/hooks/checks/authz.py tests/hooks/test_authz.py
git commit -m "feat(hooks): VCS-write authorization marker check

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 7: `odoo_lint.py` — version-aware coding-standard linter

**Files:**
- Create: `plugin/hooks/checks/odoo_lint.py`
- Test: `tests/hooks/test_odoo_lint.py`

**Interfaces:**
- Consumes: `common.Finding`.
- Produces: `lint(path: str, content: str, version: str | None) -> list[Finding]`. `version` is `"17"`/`"18"`/`"19"`/`None`. When `version is None`, apply only `severity="warn"` (never block — we can't be sure). File-type routing by suffix + directory: `.xml` under a `views/`/`security/`/`data/` path -> XML rules; `.py` under `controllers/` -> controller rules; `.py` under `models/` -> model rules. Rules exactly per the spec table (L1–L8). `line` is the 1-based line of the first regex match.

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_odoo_lint.py
from __future__ import annotations
from plugin.hooks.checks import odoo_lint


def _rules(findings):
    return sorted(f.rule for f in findings)


def _sev(findings, rule):
    return next(f.severity for f in findings if f.rule == rule)


def test_l1_tree_blocks_on_19():
    xml = '<odoo>\n<record><field name="arch"><list/></field></record>\n<tree/>\n</odoo>'
    f = odoo_lint.lint("mymod/views/x.xml", xml, "19")
    assert "L1" in _rules(f) and _sev(f, "L1") == "block"


def test_l1_tree_warns_on_18():
    f = odoo_lint.lint("mymod/views/x.xml", "<tree/>", "18")
    assert _sev(f, "L1") == "warn"


def test_l1_tree_ok_on_17():
    f = odoo_lint.lint("mymod/views/x.xml", "<tree/>", "17")
    assert "L1" not in _rules(f)


def test_l3_type_json_blocks_on_19():
    py = "@http.route('/x', type='json', auth='user')\ndef x(self): pass\n"
    f = odoo_lint.lint("mymod/controllers/main.py", py, "19")
    assert "L3" in _rules(f) and _sev(f, "L3") == "block"


def test_l2_attrs_blocks_on_19():
    f = odoo_lint.lint("mymod/views/v.xml", '<field name="x" attrs="{\'invisible\': True}"/>', "19")
    assert "L2" in _rules(f) and _sev(f, "L2") == "block"


def test_l5_category_id_blocks_on_19():
    f = odoo_lint.lint("mymod/security/groups.xml", '<field name="category_id" ref="base.module_category_x"/>', "19")
    assert "L5" in _rules(f) and _sev(f, "L5") == "block"


def test_none_version_only_warns():
    f = odoo_lint.lint("mymod/views/x.xml", "<tree/>", None)
    assert all(x.severity == "warn" for x in f)


def test_clean_file_no_findings():
    f = odoo_lint.lint("mymod/models/m.py", "class M(models.Model):\n    _name = 'm'\n", "19")
    assert f == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_odoo_lint.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# plugin/hooks/checks/odoo_lint.py
from __future__ import annotations

import re
from typing import List, Optional

from .common import Finding

# (rule, compiled regex, {version: severity}, message, fix, applies_to)
#   applies_to: "xml" | "controller" | "model"
_RULES = [
    ("L1", re.compile(r"<tree[\s>/]"),
     {"18": "warn", "19": "block"},
     "<tree> view element", "Replace <tree> with <list>.", "xml"),
    ("L2", re.compile(r"\battrs\s*=|\bstates\s*="),
     {"18": "warn", "19": "block"},
     "attrs=/states= on a view node",
     "Use direct attributes: invisible=, readonly=, required=.", "xml"),
    ("L4", re.compile(r"<group\b[^>]*\b(expand|string)\s*="),
     {"19": "block"},
     "<group expand=/string=> inside a search view",
     "Remove expand/string from <group> in search views.", "xml"),
    ("L5", re.compile(r"name\s*=\s*[\"']category_id[\"']"),
     {"19": "block"},
     "res.groups category_id",
     "Use privilege_id (res.groups.privilege) on Odoo 19.", "xml"),
    ("L3", re.compile(r"type\s*=\s*[\"']json[\"']"),
     {"18": "warn", "19": "block"},
     "type='json' in @http.route",
     "Use type='jsonrpc' on Odoo 18/19.", "controller"),
    ("L6", re.compile(r"_sql_constraints\s*=.*CHECK\s*\(", re.DOTALL),
     {"17": "warn", "18": "warn", "19": "warn"},
     "_sql_constraints CHECK() value rule",
     "Prefer @api.constrains for value validation.", "model"),
]

_ROUTE_XML = ("/views/", "/security/", "/data/", "/report/", "/wizard/")


def _kind(path: str) -> Optional[str]:
    p = "/" + path.replace("\\", "/").lstrip("/")
    if p.endswith(".xml") and any(seg in p for seg in _ROUTE_XML):
        return "xml"
    if p.endswith(".py") and "/controllers/" in p:
        return "controller"
    if p.endswith(".py") and "/models/" in p:
        return "model"
    return None


def _line_of(content: str, match: re.Match) -> int:
    return content.count("\n", 0, match.start()) + 1


def lint(path: str, content: str, version: Optional[str]) -> List[Finding]:
    kind = _kind(path or "")
    if kind is None:
        return []
    text = content or ""
    out: List[Finding] = []
    for rule, rx, sev_map, message, fix, applies in _RULES:
        if applies != kind:
            continue
        m = rx.search(text)
        if not m:
            continue
        if version is None:
            severity = "warn"
        else:
            severity = sev_map.get(version)
            if severity is None:
                continue
        out.append(Finding(severity=severity, rule=rule, line=_line_of(text, m),
                            message=message, fix=fix))
    return out
```

> Note: L7 (models without `ir.model.access.csv`) and L8 (action `return None`) are
> cross-file / semantic and are deferred to a follow-up — they are advisory-only in
> the spec and need multi-file context the single-file `lint()` signature does not
> have. Record this in the Task 13 CHANGELOG entry as a known limitation.

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_odoo_lint.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add plugin/hooks/checks/odoo_lint.py tests/hooks/test_odoo_lint.py
git commit -m "feat(hooks): version-aware Odoo 17/18/19 coding-standard linter

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 8: `sandbox_result.py` — operation-result JSON reader

**Files:**
- Create: `plugin/hooks/checks/sandbox_result.py`
- Test: `tests/hooks/test_sandbox_result.py`

**Interfaces:**
- Consumes: `common.OperationResult`.
- Produces: `read_operation_result(bash_command: str, cwd: Path) -> OperationResult | None`. Returns `None` if `bash_command` is not a `sandboxctl module … install|update|test` or `bash manage_modules.sh install|update` command. Otherwise:
  - Parse `operation` (`install`/`update`/`test`) and `module` from the command.
  - Locate the results dir: env `ODOO_RESULTS_DIR` if set; else if a `.sandbox/session.json` exists at `cwd`-or-parents, use `<repo_root>/.sandbox/sessions/<session_id>/results/`; else `<cwd>/logs/test_results/` (the `manage_modules.sh` `TEST_LOG_DIR` default is `$LOG_DIR/test_results`).
  - Pick the newest `${operation}-*.json` file whose parsed `module` matches (or newest of that operation if module is null).
  - Return `OperationResult(status=<json.status>, module_state_ok=<status=="succeeded" and (json.get("error") is None)>, reason=<message or error.summary or "">, result_path=<abs path>)`.
  - Any parse/IO failure -> `None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_sandbox_result.py
from __future__ import annotations
import json, time
from plugin.hooks.checks import sandbox_result


def _write(results_dir, operation, module, status, extra=None):
    results_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0", "session_id": "s-abc", "operation_id": "op1",
        "operation": operation, "module": module, "attempt": 1, "status": status,
        "started_at": "2026-08-27T00:00:00Z", "finished_at": "2026-08-27T00:01:00Z",
        "duration_ms": 60000, "exit_code": 0 if status == "succeeded" else 1,
        "logs": [], "artifacts": [],
    }
    if extra:
        payload.update(extra)
    p = results_dir / f"{operation}-{int(time.time())}-{id(payload) % 9999}.json"
    p.write_text(json.dumps(payload))
    return p


def test_non_matching_command_returns_none(tmp_path):
    assert sandbox_result.read_operation_result("ls -la", tmp_path) is None


def test_reads_succeeded_install(tmp_path, monkeypatch):
    rd = tmp_path / "results"
    monkeypatch.setenv("ODOO_RESULTS_DIR", str(rd))
    _write(rd, "install", "mymod", "succeeded")
    r = sandbox_result.read_operation_result(
        "sandbox/bin/sandboxctl module s-abc install mymod", tmp_path)
    assert r is not None and r.status == "succeeded" and r.module_state_ok is True


def test_reads_failed_install(tmp_path, monkeypatch):
    rd = tmp_path / "results"
    monkeypatch.setenv("ODOO_RESULTS_DIR", str(rd))
    _write(rd, "install", "mymod", "failed",
           extra={"error": {"code": "install_failed", "summary": "missing dep sale_renting_crm"}})
    r = sandbox_result.read_operation_result(
        "sandbox/bin/sandboxctl module s-abc install mymod", tmp_path)
    assert r.status == "failed" and r.module_state_ok is False
    assert "sale_renting_crm" in r.reason


def test_picks_newest(tmp_path, monkeypatch):
    rd = tmp_path / "results"
    monkeypatch.setenv("ODOO_RESULTS_DIR", str(rd))
    old = _write(rd, "test", "mymod", "failed")
    import os
    os.utime(old, (1, 1))
    _write(rd, "test", "mymod", "succeeded")
    r = sandbox_result.read_operation_result(
        "sandbox/bin/sandboxctl module s-abc test mymod", tmp_path)
    assert r.status == "succeeded"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_sandbox_result.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# plugin/hooks/checks/sandbox_result.py
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from .common import OperationResult, repo_root

_CMD_RE = re.compile(
    r"\b(?:sandboxctl\s+module\s+\S+|bash\s+(?:\./)?manage_modules\.sh)\s+"
    r"(?P<op>install|update|test)\s+(?P<module>[a-z][a-z0-9_]*)",
)


def _results_dir(cwd: Path) -> Optional[Path]:
    env = os.environ.get("ODOO_RESULTS_DIR")
    if env:
        return Path(env)
    start = cwd.resolve()
    for candidate in (start, *start.parents):
        session = candidate / ".sandbox" / "session.json"
        if session.is_file():
            try:
                sid = json.loads(session.read_text(encoding="utf-8")).get("session_id")
            except (OSError, ValueError):
                sid = None
            root = repo_root(start) or candidate
            if sid:
                return root / ".sandbox" / "sessions" / sid / "results"
            break
    return start / "logs" / "test_results"


def read_operation_result(bash_command: str, cwd: Path) -> Optional[OperationResult]:
    m = _CMD_RE.search(bash_command or "")
    if not m:
        return None
    operation, module = m.group("op"), m.group("module")
    rdir = _results_dir(Path(cwd))
    if rdir is None or not rdir.is_dir():
        return None

    candidates = sorted(rdir.glob(f"{operation}-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("module") not in (module, None):
            continue
        status = str(data.get("status", "unknown"))
        err = data.get("error")
        reason = data.get("message") or (err or {}).get("summary") or ""
        return OperationResult(
            status=status,
            module_state_ok=(status == "succeeded" and err is None),
            reason=reason,
            result_path=str(path.resolve()),
        )
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_sandbox_result.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add plugin/hooks/checks/sandbox_result.py tests/hooks/test_sandbox_result.py
git commit -m "feat(hooks): sandbox operation-result JSON reader

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 9: `odoo_hook.py` — Claude Code dispatcher

**Files:**
- Create: `plugin/hooks/odoo_hook.py` (executable, `chmod +x`)
- Test: `tests/hooks/test_dispatcher.py`
- Test fixtures: `tests/hooks/fixtures/` (created inline by the test)

**Interfaces:**
- Consumes: everything in `plugin/hooks/checks/`.
- Produces: CLI `odoo_hook.py <Event>`. Reads a JSON object from stdin. Events handled: `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SessionEnd`. Exit `0` (allow) or `2` (block, reason on stderr). Importable `main(argv: list[str], stdin_text: str) -> int` for testing.
- Claude Code payload fields used: `hook_event_name`, `prompt` (UserPromptSubmit), `tool_name` + `tool_input` (Pre/PostToolUse; `tool_input` has `command` for Bash, `file_path` + `content`/`new_string` for Write/Edit), `stop_hook_active` (Stop), `cwd` (all — fall back to `os.getcwd()`).

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_dispatcher.py
from __future__ import annotations
import json
import importlib.util
from pathlib import Path

_MOD_PATH = Path(__file__).resolve().parents[2] / "plugin" / "hooks" / "odoo_hook.py"
_spec = importlib.util.spec_from_file_location("odoo_hook", _MOD_PATH)
odoo_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(odoo_hook)


def _run(event, payload):
    return odoo_hook.main([event], json.dumps(payload))


def test_no_op_outside_module(tmp_path):
    assert _run("PreToolUse", {"cwd": str(tmp_path), "tool_name": "Bash",
                               "tool_input": {"command": "python odoo-bin -i sale"}}) == 0


def _module(tmp_path):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t1\n")
    (mod / "views").mkdir()
    (tmp_path / ".git").mkdir()
    return mod


def test_pretooluse_blocks_raw_odoo_bin(tmp_path):
    mod = _module(tmp_path)
    rc = _run("PreToolUse", {"cwd": str(mod), "tool_name": "Bash",
                             "tool_input": {"command": "python3 odoo-bin -d x -i sale"}})
    assert rc == 2


def test_pretooluse_allows_sandboxctl(tmp_path):
    mod = _module(tmp_path)
    rc = _run("PreToolUse", {"cwd": str(mod), "tool_name": "Bash",
                             "tool_input": {"command": "sandbox/bin/sandboxctl module s-1 install mymod"}})
    assert rc == 0


def test_posttooluse_blocks_tree_on_19(tmp_path, monkeypatch):
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", "19")
    mod = _module(tmp_path)
    rc = _run("PostToolUse", {"cwd": str(mod), "tool_name": "Write",
                              "tool_input": {"file_path": str(mod / "views" / "v.xml"),
                                             "content": "<odoo><tree/></odoo>"}})
    assert rc == 2


def test_userpromptsubmit_blocks_testing_incomplete(tmp_path):
    mod = _module(tmp_path)
    rc = _run("UserPromptSubmit", {"cwd": str(mod), "prompt": "/testing 19 mymod"})
    assert rc == 2


def test_stop_honours_active_flag(tmp_path):
    mod = _module(tmp_path)
    assert _run("Stop", {"cwd": str(mod), "stop_hook_active": True}) == 0


def test_bad_json_fails_open():
    assert odoo_hook.main(["PreToolUse"], "not json{") == 0


def test_unknown_event_fails_open(tmp_path):
    assert _run("Nonsense", {"cwd": str(tmp_path)}) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_dispatcher.py -v`
Expected: FAIL — `FileNotFoundError` for `odoo_hook.py`

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Claude Code hook dispatcher for odoo-agent-pro-kit.

Usage: odoo_hook.py <Event>   (reads a JSON payload on stdin)
Exit 0 = allow, 2 = block (reason on stderr). Fails open on any error.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # plugin/ on path

from hooks.checks import authz, common, gates, guard, odoo_lint, paths, sandbox_result, version  # noqa: E402


def _cwd(payload: dict) -> Path:
    return Path(payload.get("cwd") or os.getcwd())


def _tool_input(payload: dict) -> dict:
    return payload.get("tool_input") or payload.get("tool_response") or {}


def _handle_session_start(payload: dict) -> int:
    cwd = _cwd(payload)
    mod = common.find_module_dir(cwd)
    v = version.detect_odoo_version(cwd)
    bits = []
    if v:
        bits.append(f"Odoo {v}.0 workspace")
    if mod is not None:
        g_sc = gates.check_start_coding(mod)
        g_t = gates.check_testing(mod)
        bits.append(f"module '{mod.name}'")
        bits.append("tasks.md present" if g_sc.ok else "no tasks.md (run /plan-analysis)")
        bits.append("ready for /testing" if g_t.ok else "not yet ready for /testing")
    if bits:
        print("[odoo-agent-pro-kit] " + " | ".join(bits))
    return 0


def _handle_user_prompt(payload: dict) -> int:
    prompt = (payload.get("prompt") or "").strip()
    mod = common.find_module_dir(_cwd(payload))
    if prompt.startswith("/start-coding"):
        g = gates.check_start_coding(mod)
    elif prompt.startswith("/testing"):
        g = gates.check_testing(mod)
    else:
        return 0
    if not g.ok:
        print(g.message, file=sys.stderr)
        return 2
    return 0


def _handle_pre_tool(payload: dict) -> int:
    tool = payload.get("tool_name") or ""
    ti = _tool_input(payload)
    cwd = _cwd(payload)
    if tool == "Bash":
        vs = guard.classify_bash(ti.get("command", ""), vcs_allowed=authz.vcs_write_allowed(cwd))
        if vs:
            for v in vs:
                print(f"[BLOCKED] {v.message}\n  -> {v.lift_hint}", file=sys.stderr)
            return 2
    elif tool in ("Write", "Edit", "MultiEdit"):
        root = common.repo_root(cwd)
        if root is not None:
            content = ti.get("content") or ti.get("new_string") or ti.get("new_str")
            vs = paths.scan_write(ti.get("file_path", ""), content, root)
            if vs:
                for v in vs:
                    print(f"[BLOCKED] {v.message}\n  -> {v.lift_hint}", file=sys.stderr)
                return 2
    return 0


def _handle_post_tool(payload: dict) -> int:
    tool = payload.get("tool_name") or ""
    ti = _tool_input(payload)
    cwd = _cwd(payload)
    if tool in ("Write", "Edit", "MultiEdit"):
        fp = ti.get("file_path", "")
        content = ti.get("content") or ti.get("new_string") or ti.get("new_str") or ""
        findings = odoo_lint.lint(fp, content, version.detect_odoo_version(cwd))
        blockers = [f for f in findings if f.severity == "block"]
        warns = [f for f in findings if f.severity == "warn"]
        if blockers:
            for f in blockers:
                print(f"[odoo {f.rule}] line {f.line}: {f.message} -> {f.fix}", file=sys.stderr)
            return 2
        for f in warns:
            print(f"[odoo {f.rule}] line {f.line}: {f.message} -> {f.fix}")
    elif tool == "Bash":
        res = sandbox_result.read_operation_result(ti.get("command", ""), cwd)
        if res is not None and not res.module_state_ok:
            print(f"[odoo-agent-pro-kit] sandbox operation status={res.status} "
                  f"({res.reason or 'see result'}). Do NOT mark the task complete. "
                  f"Result: {res.result_path}")
    return 0


def _handle_stop(payload: dict) -> int:
    if payload.get("stop_hook_active"):
        return 0
    # Advisory only: remind about validate.sh if a stamp mechanism is present.
    root = common.repo_root(_cwd(payload))
    if root is not None and (root / "scripts" / "validate.sh").is_file():
        stamp = root / ".git" / "odoo-kit-validate.stamp"
        if not stamp.is_file():
            print("[odoo-agent-pro-kit] Reminder: run ./scripts/validate.sh from a clean "
                  "shell before committing a phase.")
    return 0


def _handle_session_end(payload: dict) -> int:
    plugin_dir = Path(__file__).resolve().parent.parent
    pid_dir = plugin_dir / "odoo_mcp"
    if pid_dir.is_dir():
        for pid_file in pid_dir.glob("mcp_server_*.pid"):
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 15)
            except (OSError, ValueError):
                pass
            try:
                pid_file.unlink()
            except OSError:
                pass
    return 0


_HANDLERS = {
    "SessionStart": _handle_session_start,
    "UserPromptSubmit": _handle_user_prompt,
    "PreToolUse": _handle_pre_tool,
    "PostToolUse": _handle_post_tool,
    "Stop": _handle_stop,
    "SessionEnd": _handle_session_end,
}


def main(argv: list[str], stdin_text: str) -> int:
    try:
        event = argv[0] if argv else ""
        try:
            payload = json.loads(stdin_text) if stdin_text.strip() else {}
        except ValueError:
            return 0
        if not isinstance(payload, dict):
            return 0
        if common.hooks_disabled():
            return 0
        if event not in _HANDLERS:
            return 0
        if event not in ("SessionStart", "SessionEnd") and not common.in_odoo_module(_cwd(payload)):
            return 0
        return _HANDLERS[event](payload)
    except Exception as exc:  # noqa: BLE001 - fail open
        print(f"[odoo-agent-pro-kit] hook error (ignored): {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.read()))
```

- [ ] **Step 4: Make executable and run tests**

```bash
chmod +x plugin/hooks/odoo_hook.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_dispatcher.py -v
```
Expected: PASS (9 tests)

- [ ] **Step 5: Verify the fail-open contract with a broken check**

Run: `printf '{"cwd":"/","tool_name":"Bash","tool_input":{"command":"git push"}}' | python3 plugin/hooks/odoo_hook.py PreToolUse; echo "exit=$?"`
Expected: `exit=0` (cwd `/` is not an Odoo module — no-op)

- [ ] **Step 6: Commit**

```bash
git add plugin/hooks/odoo_hook.py tests/hooks/test_dispatcher.py
git commit -m "feat(hooks): Claude Code hook dispatcher (odoo_hook.py)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 10: Wire `hooks.json` + `uv` fallback

**Files:**
- Modify: `plugin/hooks/hooks.json`
- Modify: `plugin/hooks/odoo_hook.py` (shebang fallback)
- Create: `tests/hooks/test_hooks_json.py`

**Interfaces:**
- Consumes: `plugin/hooks/odoo_hook.py` (Task 9).
- Produces: a `hooks.json` that Claude Code loads without error, with `odoo_hook.py` on all six events and `save_progress.sh` still on `PreCompact`. `cleanup_mcp.sh` removed from `Stop` (its logic now lives in `_handle_session_end`).

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_hooks_json.py
from __future__ import annotations
import json
from pathlib import Path

_HJ = Path(__file__).resolve().parents[2] / "plugin" / "hooks" / "hooks.json"


def test_valid_json_and_events():
    data = json.loads(_HJ.read_text())
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse",
                  "PostToolUse", "Stop", "SessionEnd", "PreCompact"):
        assert event in data, f"missing {event}"


def test_odoo_hook_referenced_per_event():
    data = json.loads(_HJ.read_text())
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"):
        blob = json.dumps(data[event])
        assert "odoo_hook.py" in blob and event.split()[0] in blob


def test_precompact_still_save_progress():
    data = json.loads(_HJ.read_text())
    assert "save_progress.sh" in json.dumps(data["PreCompact"])


def test_stop_no_longer_runs_cleanup_mcp():
    data = json.loads(_HJ.read_text())
    assert "cleanup_mcp.sh" not in json.dumps(data["Stop"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_hooks_json.py -v`
Expected: FAIL — `SessionEnd` / `UserPromptSubmit` missing, `cleanup_mcp.sh` still in `Stop`

- [ ] **Step 3: Write the new `hooks.json`**

```json
{
  "SessionStart": [
    {
      "hooks": [
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/session_start.sh" },
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py SessionStart" }
      ]
    }
  ],
  "UserPromptSubmit": [
    {
      "hooks": [
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py UserPromptSubmit" }
      ]
    }
  ],
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py PreToolUse" }
      ]
    },
    {
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py PreToolUse" }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py PostToolUse" }
      ]
    },
    {
      "matcher": "Bash",
      "hooks": [
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py PostToolUse" }
      ]
    }
  ],
  "PreCompact": [
    {
      "hooks": [
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/save_progress.sh" }
      ]
    }
  ],
  "Stop": [
    {
      "hooks": [
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py Stop" }
      ]
    }
  ],
  "SessionEnd": [
    {
      "hooks": [
        { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py SessionEnd" }
      ]
    }
  ]
}
```

- [ ] **Step 4: Add a `uv`-optional shebang fallback to `odoo_hook.py`**

Replace the first line block of `plugin/hooks/odoo_hook.py`. The `#!/usr/bin/env -S uv run --script` shebang fails on machines without `uv`. Change the shebang to plain `python3` (the script is stdlib-only, so `uv` gives nothing here) and drop the inline-script metadata:

```python
#!/usr/bin/env python3
"""Claude Code hook dispatcher for odoo-agent-pro-kit.

Usage: odoo_hook.py <Event>   (reads a JSON payload on stdin)
Exit 0 = allow, 2 = block (reason on stderr). Fails open on any error.
"""
```

Update `tests/hooks/test_dispatcher.py` docstring reference if any (no code change needed — it imports by path).

- [ ] **Step 5: Run tests + JSON lint**

```bash
python3 -c "import json; json.load(open('plugin/hooks/hooks.json'))"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_hooks_json.py tests/hooks/test_dispatcher.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add plugin/hooks/hooks.json plugin/hooks/odoo_hook.py tests/hooks/test_hooks_json.py
git commit -m "feat(hooks): wire odoo_hook.py into all Claude Code events

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 11: Hermes adapter + `register()` wiring

**Files:**
- Create: `plugin/hooks/checks/hermes_adapter.py`
- Modify: `plugin/__init__.py` (`register()`, `_on_session_start`, `_on_session_end`, `_make_command_handler`)
- Test: `tests/hooks/test_hermes_adapter.py`

**Interfaces:**
- Consumes: all `checks/` modules; the Hermes `ctx` object (duck-typed in tests).
- Produces (`hermes_adapter.py`):
  - `pre_tool_call_directive(tool_name: str, tool_args: dict, cwd: Path) -> dict | None` — returns `{"decision": "block", "reason": "<text>"}` when a `guard`/`paths` violation fires, else `None`. (Confirm the exact directive key names against the installed Hermes version — see Task 13 open item; the adapter centralises this so only one place changes.)
  - `post_tool_call_notes(tool_name: str, tool_args: dict, cwd: Path) -> list[str]` — advisory strings from `odoo_lint` (block-severity findings included as text, since Hermes `post_tool_call` cannot block) + `sandbox_result`.
  - `session_start_lines(cwd: Path) -> list[str]` — same summary `_handle_session_start` prints.
  - `command_gate(command: str, prompt: str, cwd: Path) -> str | None` — for `start-coding`/`testing`, returns the redirect message if the gate fails, else `None`.
- Produces (`plugin/__init__.py`): two new `ctx.register_hook` calls (`pre_tool_call`, `post_tool_call`); `_on_session_start` also logs `session_start_lines`; `_make_command_handler` consults `command_gate` before injecting the prompt; the final log line count updated to `5 hooks`.

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_hermes_adapter.py
from __future__ import annotations
from plugin.hooks.checks import hermes_adapter


def _module(tmp_path):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t1\n")
    (tmp_path / ".git").mkdir()
    return mod


def test_pre_tool_call_blocks_raw_odoo_bin(tmp_path):
    mod = _module(tmp_path)
    d = hermes_adapter.pre_tool_call_directive("Bash", {"command": "python odoo-bin -i sale"}, mod)
    assert d is not None and d["decision"] == "block"


def test_pre_tool_call_allows_clean(tmp_path):
    mod = _module(tmp_path)
    assert hermes_adapter.pre_tool_call_directive("Bash", {"command": "ls"}, mod) is None


def test_post_tool_call_notes_lint(tmp_path, monkeypatch):
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", "19")
    mod = _module(tmp_path)
    (mod / "views").mkdir()
    notes = hermes_adapter.post_tool_call_notes(
        "Write", {"file_path": str(mod / "views" / "v.xml"), "content": "<tree/>"}, mod)
    assert any("L1" in n for n in notes)


def test_command_gate_blocks_testing(tmp_path):
    mod = _module(tmp_path)
    msg = hermes_adapter.command_gate("testing", "/testing 19 mymod", mod)
    assert msg and "start-coding" in msg


def test_command_gate_passes_plan_analysis(tmp_path):
    mod = _module(tmp_path)
    assert hermes_adapter.command_gate("plan-analysis", "/plan-analysis 19 mymod", mod) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_hermes_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `hermes_adapter.py`**

```python
# plugin/hooks/checks/hermes_adapter.py
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from . import authz, common, gates, guard, odoo_lint, paths, sandbox_result, version


def _cwd(cwd) -> Path:
    return Path(cwd) if cwd else Path.cwd()


def pre_tool_call_directive(tool_name: str, tool_args: dict, cwd) -> Optional[dict]:
    if common.hooks_disabled():
        return None
    c = _cwd(cwd)
    if not common.in_odoo_module(c):
        return None
    args = tool_args or {}
    reasons: List[str] = []
    if tool_name in ("Bash", "shell", "run_shell"):
        for v in guard.classify_bash(args.get("command", ""), vcs_allowed=authz.vcs_write_allowed(c)):
            reasons.append(f"{v.message} -> {v.lift_hint}")
    elif tool_name in ("Write", "Edit", "write_file", "edit_file"):
        root = common.repo_root(c)
        if root is not None:
            content = args.get("content") or args.get("new_string") or args.get("new_str")
            for v in paths.scan_write(args.get("file_path") or args.get("path", ""), content, root):
                reasons.append(f"{v.message} -> {v.lift_hint}")
    if reasons:
        return {"decision": "block", "reason": "\n".join(reasons)}
    return None


def post_tool_call_notes(tool_name: str, tool_args: dict, cwd) -> List[str]:
    if common.hooks_disabled():
        return []
    c = _cwd(cwd)
    if not common.in_odoo_module(c):
        return []
    args = tool_args or {}
    notes: List[str] = []
    if tool_name in ("Write", "Edit", "write_file", "edit_file"):
        fp = args.get("file_path") or args.get("path", "")
        content = args.get("content") or args.get("new_string") or args.get("new_str") or ""
        for f in odoo_lint.lint(fp, content, version.detect_odoo_version(c)):
            notes.append(f"[odoo {f.rule}] line {f.line}: {f.message} -> {f.fix}")
    elif tool_name in ("Bash", "shell", "run_shell"):
        res = sandbox_result.read_operation_result(args.get("command", ""), c)
        if res is not None and not res.module_state_ok:
            notes.append(f"sandbox operation status={res.status} ({res.reason or 'see result'}); "
                         f"do not mark the task complete. Result: {res.result_path}")
    return notes


def session_start_lines(cwd) -> List[str]:
    c = _cwd(cwd)
    mod = common.find_module_dir(c)
    v = version.detect_odoo_version(c)
    out: List[str] = []
    if v:
        out.append(f"Odoo {v}.0 workspace detected")
    if mod is not None:
        out.append(f"module '{mod.name}': "
                   + ("tasks.md present" if gates.check_start_coding(mod).ok else "no tasks.md")
                   + ", "
                   + ("ready for /testing" if gates.check_testing(mod).ok else "not ready for /testing"))
    return out


def command_gate(command: str, prompt: str, cwd) -> Optional[str]:
    if common.hooks_disabled():
        return None
    mod = common.find_module_dir(_cwd(cwd))
    if command == "start-coding":
        g = gates.check_start_coding(mod)
    elif command == "testing":
        g = gates.check_testing(mod)
    else:
        return None
    return None if g.ok else g.message
```

- [ ] **Step 4: Wire into `plugin/__init__.py`**

In `_on_session_start`, after the existing detection, add:

```python
    try:
        from .hooks.checks.hermes_adapter import session_start_lines
        for line in session_start_lines(Path.cwd()):
            logger.info("[odoo-agent-pro-kit] %s", line)
    except Exception as exc:  # noqa: BLE001
        logger.debug("[odoo-agent-pro-kit] session_start_lines failed: %s", exc)
```

In `_make_command_handler`, change `_handler` to gate first:

```python
    def _handler(raw_args: str) -> str:
        version, rest = _parse_version_and_rest(raw_args)
        try:
            from .hooks.checks.hermes_adapter import command_gate
            cmd_name = command_md_relpath.split("/")[-1].removesuffix(".md")
            block = command_gate(cmd_name, raw_args, Path.cwd())
            if block:
                return block
        except Exception as exc:  # noqa: BLE001
            logger.debug("[odoo-agent-pro-kit] command_gate failed: %s", exc)
        prompt = _command_prompt(command_md_relpath, version, rest, extra)
        queued = ctx.inject_message(prompt, role="user")
        if queued:
            return None
        return prompt
```

In `register()`, after the `post_api_request` block, add:

```python
    try:
        from .hooks.checks.hermes_adapter import pre_tool_call_directive, post_tool_call_notes

        def _pre_tool_call(**kwargs: Any):
            return pre_tool_call_directive(
                kwargs.get("tool_name", ""), kwargs.get("tool_args") or kwargs.get("arguments") or {}, Path.cwd()
            )

        def _post_tool_call(**kwargs: Any) -> None:
            for note in post_tool_call_notes(
                kwargs.get("tool_name", ""), kwargs.get("tool_args") or kwargs.get("arguments") or {}, Path.cwd()
            ):
                logger.warning("[odoo-agent-pro-kit] %s", note)

        ctx.register_hook("pre_tool_call", _pre_tool_call)
        ctx.register_hook("post_tool_call", _post_tool_call)
    except Exception as exc:  # noqa: BLE001
        logger.warning("odoo-agent-pro-kit: tool-call hook registration failed: %s", exc)
```

Update the final log line: `"... 4 slash commands, 5 hooks, and skills from %s"`.

- [ ] **Step 5: Run tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/ tests/test_context_guard.py -v
python3 -m py_compile plugin/__init__.py
```
Expected: PASS; `py_compile` clean.

- [ ] **Step 6: Commit**

```bash
git add plugin/hooks/checks/hermes_adapter.py plugin/__init__.py tests/hooks/test_hermes_adapter.py
git commit -m "feat(hooks): Hermes pre/post_tool_call + command-gate parity

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 12: Contributor workflow hook + `.claude/settings.json`

**Files:**
- Create: `scripts/contributor_hook.py` (executable)
- Create: `.claude/settings.json`
- Create: `tests/hooks/test_contributor_hook.py`

**Interfaces:**
- Consumes: `plugin/hooks/checks/guard.py` (reused for the VCS/cleanup classification), `plugin/hooks/checks/common.py`.
- Produces: CLI `contributor_hook.py <Event>` (`SessionStart`, `PreToolUse`, `Stop`), same stdin/exit contract. Importable `main(argv, stdin_text) -> int`.
  - `SessionStart` -> print `SESSION_CONTEXT.md` "## Current state" section (first ~40 lines after that header) + `git rev-parse --abbrev-ref HEAD` + `git status -s` + the first unchecked line under "Phase" in `docs/docker-sandbox/tasks.md`.
  - `PreToolUse[Bash]` -> `guard.classify_bash(cmd, vcs_allowed=<AGENTS_PHASE_AUTHORIZED>)`; block on `vcs_write` / `destructive_cleanup`. Also block `git commit` (not `--amend`) when `.git/odoo-kit-validate.stamp` is older than the newest tracked file mtime (i.e. `validate.sh` hasn't run since the last change). Env `AGENTS_PHASE_AUTHORIZED=1` lifts the VCS block.
  - `Stop` -> if `git status -s` shows changed `.py`/`.sh`/`.json` files but none of `docs/docker-sandbox/tasks.md`, `SESSION_CONTEXT.md`, `README.md` changed, print a reminder.
- `.claude/settings.json` references `scripts/contributor_hook.py` for those three events (relative path from repo root).

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_contributor_hook.py
from __future__ import annotations
import json, importlib.util, subprocess, time
from pathlib import Path

_MOD = Path(__file__).resolve().parents[2] / "scripts" / "contributor_hook.py"
_spec = importlib.util.spec_from_file_location("contributor_hook", _MOD)
contributor_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contributor_hook)


def _git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
                   cwd=tmp_path, check=True)
    return tmp_path


def _run(event, payload):
    return contributor_hook.main([event], json.dumps(payload))


def test_git_push_blocked_without_authz(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.delenv("AGENTS_PHASE_AUTHORIZED", raising=False)
    assert _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                               "tool_input": {"command": "git push origin main"}}) == 2


def test_git_push_allowed_with_authz(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.setenv("AGENTS_PHASE_AUTHORIZED", "1")
    assert _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                               "tool_input": {"command": "git push origin main"}}) == 2 - 2


def test_commit_blocked_when_validate_stale(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.delenv("AGENTS_PHASE_AUTHORIZED", raising=False)
    (repo / "b.py").write_text("y = 2\n")  # newer than any stamp
    rc = _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                             "tool_input": {"command": "git commit -m wip"}})
    assert rc == 2


def test_commit_ok_when_stamp_fresh(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.delenv("AGENTS_PHASE_AUTHORIZED", raising=False)
    stamp = repo / ".git" / "odoo-kit-validate.stamp"
    time.sleep(0.01)
    stamp.write_text("ok\n")
    rc = _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                             "tool_input": {"command": "git commit -m done"}})
    assert rc == 0


def test_bad_json_fails_open():
    assert contributor_hook.main(["PreToolUse"], "{bad") == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_contributor_hook.py -v`
Expected: FAIL — `FileNotFoundError` for `contributor_hook.py`

- [ ] **Step 3: Write `scripts/contributor_hook.py`**

```python
#!/usr/bin/env python3
"""Repo-contributor Claude Code hook for odoo-agent-pro-kit.

Enforces the AGENTS.md phase-workflow rules. Referenced from the repo-root
.claude/settings.json (not shipped in the plugin package).
Usage: contributor_hook.py <Event>   (JSON payload on stdin)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugin" / "hooks"))
from checks import guard  # noqa: E402

_TRUE = {"1", "true", "yes", "on"}
_CODE_SUFFIXES = (".py", ".sh", ".json", ".yaml", ".yml")
_PHASE_DOCS = ("docs/docker-sandbox/tasks.md", "SESSION_CONTEXT.md", "README.md")


def _cwd(payload: dict) -> Path:
    return Path(payload.get("cwd") or os.getcwd())


def _phase_authorized() -> bool:
    return os.environ.get("AGENTS_PHASE_AUTHORIZED", "").strip().lower() in _TRUE


def _git(cwd: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                              timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _handle_session_start(payload: dict) -> int:
    cwd = _cwd(payload)
    sc = cwd / "SESSION_CONTEXT.md"
    if sc.is_file():
        lines = sc.read_text(encoding="utf-8", errors="replace").splitlines()
        try:
            start = next(i for i, ln in enumerate(lines) if ln.strip().lower().startswith("## current state"))
            print("\n".join(lines[start:start + 40]))
        except StopIteration:
            pass
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    status = _git(cwd, "status", "-s")
    if branch:
        print(f"\n[branch] {branch}")
    if status:
        print(f"[uncommitted]\n{status}")
    return 0


def _newest_tracked_mtime(cwd: Path) -> float:
    out = _git(cwd, "ls-files")
    newest = 0.0
    for rel in out.splitlines():
        p = cwd / rel
        try:
            newest = max(newest, p.stat().st_mtime)
        except OSError:
            continue
    return newest


def _handle_pre_tool(payload: dict) -> int:
    if (payload.get("tool_name") or "") != "Bash":
        return 0
    cmd = (payload.get("tool_input") or {}).get("command", "")
    cwd = _cwd(payload)

    for v in guard.classify_bash(cmd, vcs_allowed=_phase_authorized()):
        if v.kind in ("vcs_write", "destructive_cleanup"):
            print(f"[BLOCKED] {v.message}\n  -> {v.lift_hint}\n  (set AGENTS_PHASE_AUTHORIZED=1 "
                  "after the user approves)", file=sys.stderr)
            return 2

    import re
    if re.search(r"\bgit\s+commit\b", cmd) and "--amend" not in cmd:
        stamp = cwd / ".git" / "odoo-kit-validate.stamp"
        stamp_mtime = stamp.stat().st_mtime if stamp.is_file() else 0.0
        if _newest_tracked_mtime(cwd) > stamp_mtime:
            print("[BLOCKED] ./scripts/validate.sh has not run since the last tracked change.\n"
                  "  -> Run it from a clean shell, then `touch .git/odoo-kit-validate.stamp`.",
                  file=sys.stderr)
            return 2
    return 0


def _handle_stop(payload: dict) -> int:
    cwd = _cwd(payload)
    status = _git(cwd, "status", "-s")
    changed = [ln[3:] for ln in status.splitlines() if ln[3:].strip()]
    code_changed = any(c.endswith(_CODE_SUFFIXES) for c in changed)
    docs_changed = any(any(c.endswith(d) or c == d for d in _PHASE_DOCS) for c in changed)
    if code_changed and not docs_changed:
        print("[odoo-agent-pro-kit] Reminder: update docs/docker-sandbox/tasks.md, "
              "SESSION_CONTEXT.md, and README.md alongside code changes (AGENTS.md rule 4).")
    return 0


_HANDLERS = {
    "SessionStart": _handle_session_start,
    "PreToolUse": _handle_pre_tool,
    "Stop": _handle_stop,
}


def main(argv: list[str], stdin_text: str) -> int:
    try:
        event = argv[0] if argv else ""
        try:
            payload = json.loads(stdin_text) if stdin_text.strip() else {}
        except ValueError:
            return 0
        if not isinstance(payload, dict) or event not in _HANDLERS:
            return 0
        return _HANDLERS[event](payload)
    except Exception as exc:  # noqa: BLE001 - fail open
        print(f"[odoo-agent-pro-kit] contributor hook error (ignored): {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.read()))
```

- [ ] **Step 4: Write `.claude/settings.json`**

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": "python3 scripts/contributor_hook.py SessionStart" } ] }
    ],
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "python3 scripts/contributor_hook.py PreToolUse" } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "python3 scripts/contributor_hook.py Stop" } ] }
    ]
  }
}
```

- [ ] **Step 5: Make executable, run tests**

```bash
chmod +x scripts/contributor_hook.py
python3 -c "import json; json.load(open('.claude/settings.json'))"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_contributor_hook.py -v
```
Expected: PASS (5 tests)

- [ ] **Step 6: Commit**

```bash
git add scripts/contributor_hook.py .claude/settings.json tests/hooks/test_contributor_hook.py
git commit -m "feat(hooks): contributor .claude/settings.json for AGENTS.md phase rules

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 13: `validate.sh` integration, docs, version bump, CHANGELOG

**Files:**
- Modify: `scripts/validate.sh`
- Modify: `plugin/plugin.yaml`, `plugin/.claude-plugin/plugin.json`
- Modify: `plugin/skills/CommandingSystem/SKILL.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md`
- Modify: `plugin/skills/OdooHermesEnvironmentSetup/SKILL.md` (hook count 2 -> 5)
- Test: `tests/hooks/test_smoke_all_events.py`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: `validate.sh` runs a hook smoke check; `plugin.yaml` `provides_hooks` lists 5 hooks; version is `0.5.0` everywhere; docs describe the hooks.

- [ ] **Step 1: Write the failing test**

```python
# tests/hooks/test_smoke_all_events.py
from __future__ import annotations
import json, importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _load(rel):
    spec = importlib.util.spec_from_file_location(rel.replace("/", "_"), _ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_odoo_hook_all_events_exit_0_on_empty():
    oh = _load("plugin/hooks/odoo_hook.py")
    for ev in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"):
        assert oh.main([ev], "{}") == 0


def test_contributor_hook_all_events_exit_0_on_empty():
    ch = _load("scripts/contributor_hook.py")
    for ev in ("SessionStart", "PreToolUse", "Stop"):
        assert ch.main([ev], "{}") == 0


def test_plugin_versions_match():
    j = json.loads((_ROOT / "plugin" / ".claude-plugin" / "plugin.json").read_text())
    y = (_ROOT / "plugin" / "plugin.yaml").read_text()
    assert j["version"] == "0.5.0"
    assert 'version: "0.5.0"' in y


def test_plugin_yaml_lists_five_hooks():
    y = (_ROOT / "plugin" / "plugin.yaml").read_text()
    for h in ("on_session_start", "on_session_end", "post_api_request", "pre_tool_call", "post_tool_call"):
        assert h in y
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hooks/test_smoke_all_events.py -v`
Expected: FAIL — version still `0.4.0`, `pre_tool_call` not in `plugin.yaml`

- [ ] **Step 3: Bump versions + `provides_hooks`**

In `plugin/.claude-plugin/plugin.json`: `"version": "0.5.0"`.

In `plugin/plugin.yaml`: `version: "0.5.0"` and replace the `provides_hooks` block with:

```yaml
provides_hooks:
  - on_session_start
  - on_session_end
  - post_api_request
  - pre_tool_call
  - post_tool_call
```

- [ ] **Step 4: Extend `scripts/validate.sh`**

After the `==> Python syntax` `py_compile` block, add the new files to the `py_compile` list:

```bash
  plugin/hooks/odoo_hook.py \
  scripts/contributor_hook.py \
  plugin/hooks/checks/common.py \
  plugin/hooks/checks/version.py \
  plugin/hooks/checks/guard.py \
  plugin/hooks/checks/paths.py \
  plugin/hooks/checks/gates.py \
  plugin/hooks/checks/authz.py \
  plugin/hooks/checks/odoo_lint.py \
  plugin/hooks/checks/sandbox_result.py \
  plugin/hooks/checks/hermes_adapter.py
```

Add a new section before `==> Git whitespace validation`:

```bash
echo "==> Hook smoke test"
for ev in SessionStart UserPromptSubmit PreToolUse PostToolUse Stop SessionEnd; do
  echo '{}' | python3 plugin/hooks/odoo_hook.py "$ev" >/dev/null || {
    echo "FAIL: odoo_hook.py $ev did not exit 0 on empty payload"; exit 1; }
done
for ev in SessionStart PreToolUse Stop; do
  echo '{}' | python3 scripts/contributor_hook.py "$ev" >/dev/null || {
    echo "FAIL: contributor_hook.py $ev did not exit 0 on empty payload"; exit 1; }
done
python3 -c "import json; json.load(open('plugin/hooks/hooks.json')); json.load(open('.claude/settings.json'))"
```

Also add `plugin/hooks/checks/*.py` is covered — the `bash -n` shell-syntax block is unchanged (no new shell files).

- [ ] **Step 5: Update docs**

`plugin/skills/CommandingSystem/SKILL.md` — add after the "Gate Rules" section:

```markdown
## 🪝 Deterministic Hooks (v0.5.0)

These rules are now enforced by hooks (`plugin/hooks/odoo_hook.py`, wired in
`plugin/hooks/hooks.json`; Hermes parity via `pre_tool_call` / `post_tool_call`
in `plugin/__init__.py`), so they hold whether or not the agent remembers them:

| Moment | Hook | Effect |
| --- | --- | --- |
| `/start-coding` without `docs/tasks.md` | UserPromptSubmit | blocked, redirect to `/plan-analysis` |
| `/testing` with open tasks or unpassed backend tests | UserPromptSubmit | blocked, redirect to `/start-coding` |
| raw `odoo-bin`, `./manage_modules.sh`, unauthorized `git push/merge/tag` | PreToolUse[Bash] | blocked |
| writing secrets / Enterprise source into the repo | PreToolUse[Write] | blocked |
| Odoo 19 `<tree>` / `type='json'` / `attrs=` / `category_id` in edited files | PostToolUse[Write] | blocked until fixed |
| `sandboxctl module … install/update/test` not `succeeded` | PostToolUse[Bash] | advisory: do not mark task complete |

Disable all hooks with `ODOO_KIT_HOOKS_DISABLED=1`. Authorize VCS writes with
`ODOO_KIT_ALLOW_VCS_WRITE=1` or a `.sandbox/AUTHORIZED` marker.
```

`AGENTS.md` — append to the "Phase workflow" section:

```markdown
The phase-workflow rules above are backed by `.claude/settings.json` +
`scripts/contributor_hook.py` for contributors using Claude Code: it prints the
current state at session start, blocks `git push/merge/tag` and destructive
cleanup unless `AGENTS_PHASE_AUTHORIZED=1`, and blocks `git commit` until
`./scripts/validate.sh` has run (touch `.git/odoo-kit-validate.stamp` after it
passes).
```

`README.md` — in the feature list, add a "Hooks" bullet naming the pipeline
guardrails and the version-aware linter.

`plugin/skills/OdooHermesEnvironmentSetup/SKILL.md` — change every `2 hook(s)` /
`2 hooks` reference to `5 hooks` and note `pre_tool_call` / `post_tool_call` were
added in 0.5.0.

`CHANGELOG.md` — new entry:

```markdown
## [0.5.0] - 2026-08-27

### Added
- Deterministic pipeline hooks (`plugin/hooks/odoo_hook.py` + `plugin/hooks/checks/`):
  command-prerequisite gates for `/start-coding` and `/testing`, a version-aware
  Odoo 17/18/19 coding-standard linter (rules L1–L6), sandbox operation-result
  verification, and `odoo-bin` / `manage_modules.sh` / VCS / secret / Enterprise-source
  guardrails. Wired into all Claude Code hook events and mirrored on Hermes via
  `pre_tool_call` / `post_tool_call` and the slash-command handlers.
- Contributor-only `.claude/settings.json` + `scripts/contributor_hook.py` enforcing
  the `AGENTS.md` phase-workflow rules.

### Changed
- MCP process cleanup moved from the `Stop` hook to `SessionEnd`.
- Plugin version 0.4.0 -> 0.5.0; `plugin.yaml` `provides_hooks` now lists 5 hooks.

### Known limitations
- Linter rules L7 (models without an `ir.model.access.csv` row) and L8 (action
  methods returning `None`) are not yet implemented — they need multi-file context
  the single-file linter does not have.
```

- [ ] **Step 6: Run the full validation suite**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests
./scripts/validate.sh
```
Expected: all tests pass; `validate.sh` ends with `OK: all repository validation checks passed.`

- [ ] **Step 7: Commit**

```bash
git add scripts/validate.sh plugin/plugin.yaml plugin/.claude-plugin/plugin.json \
  plugin/skills/CommandingSystem/SKILL.md AGENTS.md README.md CHANGELOG.md \
  plugin/skills/OdooHermesEnvironmentSetup/SKILL.md tests/hooks/test_smoke_all_events.py
git commit -m "feat(hooks): validate.sh integration, docs, 0.5.0 version bump

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Self-Review

**1. Spec coverage:**

| Spec section | Task |
| --- | --- |
| §4.1 `version.py` | Task 2 |
| §4.1 `odoo_lint.py` | Task 7 |
| §4.1 `sandbox_result.py` | Task 8 |
| §4.1 `guard.py` | Task 3 |
| §4.1 `paths.py` | Task 4 |
| §4.1 `gates.py` | Task 5 |
| §4.1 `authz.py` | Task 6 |
| §4.1 `common.py` | Task 1 |
| §4.2 dispatcher | Task 9 |
| §4.3 `hooks.json` wiring | Task 10 |
| §4.4 Hermes wiring + adapter | Task 11 |
| §4.5 contributor `.claude/settings.json` | Task 12 |
| §5 linter rules L1–L6 | Task 7 |
| §5 linter rules L7–L8 | Deferred — documented in Task 7 note + Task 13 CHANGELOG |
| §7 fail-open / kill switch / `stop_hook_active` | Tasks 1, 9, 11, 12 (Global Constraints) |
| §8 testing (unit + dispatcher + fail-open + Hermes + validate.sh) | every task + Tasks 11, 13 |
| §9 docs + version bump | Task 13 |
| §10 rollout order | Task order 1→13 matches |
| §11 open items | See below |

**Spec §11 open items resolved/carried:**
- `uv` availability — resolved in Task 10 Step 4 (plain `python3` shebang; script is stdlib-only).
- Operation-result JSON path convention — resolved in Task 8 from `manage_modules.sh:163-164,452` and `sandboxctl:358`.
- `cleanup_mcp.sh` absorbed vs separate — resolved: absorbed into `_handle_session_end` (Task 9), script kept but unreferenced (Task 10).
- Hermes `pre_tool_call` directive shape — **carried**: Task 11 centralises it in `hermes_adapter.pre_tool_call_directive`; the implementer must confirm `{"decision": "block", "reason": ...}` against the installed Hermes version and adjust that one function. Noted in Task 11 interfaces.
- Customer-data deny-list — resolved in Task 4: optional untracked `plugin/hooks/checks/customer_denylist.txt`, absent = no customer checks.

**2. Placeholder scan:** No "TBD"/"TODO"/"handle edge cases"/"similar to Task N". L7/L8 deferral is explicit with rationale, not a placeholder. All code steps have full code.

**3. Type consistency:** `Finding(severity, rule, line, message, fix)`, `Violation(kind, message, lift_hint)`, `Gate(ok, message)`, `OperationResult(status, module_state_ok, reason, result_path)` — defined in Task 1, used identically in Tasks 3–11. `detect_odoo_version` returns `"17"`/`"18"`/`"19"`/`None` consistently (Tasks 2, 7, 9, 11). `classify_bash(command, *, vcs_allowed)` signature identical in Tasks 3, 9, 12. `read_operation_result(bash_command, cwd)` identical in Tasks 8, 9, 11. `lint(path, content, version)` identical in Tasks 7, 9, 11.

One naming note fixed inline: Task 9/11 read Write/Edit content via `ti.get("content") or ti.get("new_string") or ti.get("new_str")` — the same fallback chain in both, matching Claude Code (`content`/`new_string`) and Hermes (`new_str`) payload shapes.
