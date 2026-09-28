#!/usr/bin/env python3
"""Refuse private module code in this public repository.

Custom-module migrations (Phase 11) import the owner's private Odoo modules. Their source, the
migrated code and any patch of it stay in the gitignored ``.sandbox/``. Module names may appear in
docs; code may not. This check fails on any Odoo module outside ``sandbox/fixtures/`` and on any
patch, bundle or archive that is not grandfathered evidence.
Usage: private_code_guard.py [PATH ...]   (default: tracked + untracked, non-ignored files)
"""
import subprocess
import sys
from collections import namedtuple
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PurePosixPath("sandbox/fixtures")
MANIFESTS = {"__manifest__.py", "__openerp__.py"}
ARCHIVE_SUFFIXES = (".patch", ".diff", ".bundle", ".tgz", ".tar", ".tar.gz", ".tar.xz", ".zip")
# Committed before Phase 11 as Phase 8 evidence; reviewed, and not private module code.
ALLOWED_ARCHIVES = frozenset({
    "docs/docker-sandbox/phase-8/enterprise-dependency-evidence/1787206019028-module-install-failed.tar.gz",
    "docs/docker-sandbox/phase-8/mig-excel-18/excel_sheet.py.diff",
})

Violation = namedtuple("Violation", "path reason")


def violations(paths):
    found = []
    for name in paths:
        path = PurePosixPath(name)
        if path.name in MANIFESTS and FIXTURES not in path.parents:
            found.append(Violation(name, "odoo-module"))
        elif name.lower().endswith(ARCHIVE_SUFFIXES) and name not in ALLOWED_ARCHIVES:
            found.append(Violation(name, "patch-or-archive"))
    return found


def repository_files():
    return subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, text=True,
                          capture_output=True, check=True).stdout.splitlines()


def main(argv):
    found = violations(argv or repository_files())
    for v in found:
        print(f"{v.path}: {v.reason} (keep private module code in the gitignored .sandbox/)", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
