from __future__ import annotations

import re
from typing import List

from .common import Violation

# ``odoo-bin`` only in *command position*: at line start, after a shell
# separator (``;`` / ``&`` / ``|``), after ``python``/``python3``, or as an
# explicit path (``./path/odoo-bin``). This deliberately does NOT match
# ``cat odoo-bin`` or ``grep 'odoo-bin' docs/`` — reading/searching the file
# is fine, only *running* it is guarded.
_ODOO_BIN_RE = re.compile(r"(?:^|[\n;&|]|\bpython3?\s+)\s*(?:[\w./-]*/)?odoo[-_ ]bin\b")
_SANDBOXCTL_RE = re.compile(r"\bsandboxctl\b")

# Direct ``manage_modules.sh`` invocation in command position (bare, ``./``,
# or ``sh``/``zsh`` — all wrong on a macOS zsh default shell). ``cat
# manage_modules.sh`` is NOT command position, so it is not flagged.
_MANAGE_DIRECT_RE = re.compile(r"(?:^|[\n;&|]|\bsh\s+|\bzsh\s+)\s*(?:\./)?manage_modules\.sh\b")
# The correct form: ``bash [flags] manage_modules.sh`` (tolerate ``bash -x`` etc).
_MANAGE_BASH_RE = re.compile(r"\bbash\s+(?:-\S+\s+)*(?:\./)?manage_modules\.sh\b")

_VCS_RES = [
    (re.compile(r"\bgit\s+push\b"), "git push"),
    # ``git merge main`` is a write; ``git merge-base`` is read-only.
    (re.compile(r"\bgit\s+merge\b(?!-)"), "git merge"),
    # ``git tag v1.0`` creates a tag; ``git tag -l`` / ``--list`` / ``-n`` list.
    (re.compile(r"\bgit\s+tag\b(?!\s+(?:-l\b|--list\b|-n\d*\b))"), "git tag"),
    (re.compile(r"\bgit\s+commit\b[^\n]*--amend\b"), "git commit --amend"),
    # ``git rebase main`` rewrites history; the recovery sub-commands do not.
    (re.compile(r"\bgit\s+rebase\b(?!\s+(?:--abort|--continue|--skip|--quit|--edit-todo|--show-current-patch))"),
     "git rebase"),
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


def classify_bash(command: str, *, vcs_allowed: bool, raw_allowed: bool = False) -> List[Violation]:
    cmd = command or ""
    out: List[Violation] = []

    if not raw_allowed:
        if _ODOO_BIN_RE.search(cmd) and not _SANDBOXCTL_RE.search(cmd):
            out.append(Violation(
                kind="raw_odoo_bin",
                message="Raw odoo-bin invocation is not allowed from a skill/agent.",
                lift_hint="Route through `sandbox/bin/sandboxctl module <session> install|update|test <module>` "
                          "(sandbox mode) or `bash manage_modules.sh install|update <module>` (local mode). "
                          "Set ODOO_KIT_ALLOW_RAW_ODOO=1 only if the user explicitly needs a raw run.",
            ))

        if _MANAGE_DIRECT_RE.search(cmd) and not _MANAGE_BASH_RE.search(cmd):
            out.append(Violation(
                kind="manage_modules_direct",
                message="manage_modules.sh must be invoked via an explicit `bash` (macOS default shell is zsh).",
                lift_hint="Use `WORKSPACE_PATH=$(pwd) bash manage_modules.sh <args>` — never `./manage_modules.sh`. "
                          "Set ODOO_KIT_ALLOW_RAW_ODOO=1 only if the user explicitly needs a raw run.",
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
