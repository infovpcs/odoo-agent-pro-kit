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
