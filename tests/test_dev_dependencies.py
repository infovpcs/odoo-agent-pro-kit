"""Guard: ``./scripts/validate.sh`` must never depend on an undeclared package.

A test suite that imports a third-party module which no requirements file
declares does not fail for the person who happens to have it installed — it
fails later, for someone else, halfway through validation. These tests derive
the real dependency set from the source instead of trusting a hand-written
list, so adding an import without declaring it fails here first.
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEV_REQUIREMENTS = REPO_ROOT / "requirements-dev.txt"
RUNTIME_REQUIREMENTS = REPO_ROOT / "plugin" / "odoo_mcp" / "requirements.txt"
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "validate.sh"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Import name -> distribution name. An import that is neither standard library,
# nor local, nor listed here fails the suite on purpose: the mapping is where a
# new dependency must be declared deliberately.
IMPORT_TO_DISTRIBUTION = {
    "yaml": "PyYAML",
    "pytest": "pytest",
}

# Importable names that belong to this repository (or to a tool that runs inside
# Odoo), not to a distributable package.
LOCAL_MODULES = {
    "checks",           # plugin/hooks/checks, reached via sys.path insertion
    "validate_skills",  # scripts/validate_skills.py
    "context_guard",    # plugin/context_guard.py
    "plugin",           # the plugin package
    "tests",
    "conftest",
}

SCANNED_DIRECTORIES = ("tests", "scripts")
STDLIB_MODULES = set(sys.stdlib_module_names)


def declared_distributions() -> set[str]:
    """Every distribution name pinned by a requirements file, lower-cased."""
    declared: set[str] = set()
    for path in (DEV_REQUIREMENTS, RUNTIME_REQUIREMENTS):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue
            # Drop extras, version specifiers, environment markers, and options.
            name = re.split(r"[<>=!~\[;@ ]", line, 1)[0].strip()
            if name:
                declared.add(name.lower())
    return declared


def third_party_imports() -> dict[str, set[str]]:
    """Top-level third-party imports across the suite, mapped to their files."""
    found: dict[str, set[str]] = {}
    for directory in SCANNED_DIRECTORIES:
        for path in sorted((REPO_ROOT / directory).glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:  # a relative import cannot be a distribution
                        continue
                    roots = [(node.module or "").split(".")[0]]
                else:
                    continue
                for root in roots:
                    if not root or root in STDLIB_MODULES or root in LOCAL_MODULES:
                        continue
                    found.setdefault(root, set()).add(path.name)
    return found


class TestDevDependenciesDeclared(unittest.TestCase):
    def test_requirements_file_exists_and_is_pinned(self):
        self.assertTrue(DEV_REQUIREMENTS.is_file(), "requirements-dev.txt is missing")
        text = DEV_REQUIREMENTS.read_text(encoding="utf-8")
        for package in ("PyYAML", "pytest"):
            self.assertIn(package, text, f"{package} must be declared in requirements-dev.txt")
        # Every active requirement line carries a version constraint.
        for line in text.splitlines():
            entry = line.split("#", 1)[0].strip()
            if not entry or entry.startswith("-"):
                continue
            self.assertRegex(entry, r"[<>=!~]", f"unpinned requirement: {entry}")

    def test_every_third_party_import_is_declared(self):
        declared = {name.lower() for name in declared_distributions()}
        undeclared: list[str] = []
        unmapped: list[str] = []

        for module, files in sorted(third_party_imports().items()):
            distribution = IMPORT_TO_DISTRIBUTION.get(module)
            if distribution is None:
                unmapped.append(f"{module} (imported by {', '.join(sorted(files))})")
                continue
            if distribution.lower() not in declared:
                undeclared.append(
                    f"{distribution} (imported as '{module}' by {', '.join(sorted(files))})"
                )

        self.assertEqual(
            unmapped, [],
            "these imports are neither stdlib, local, nor mapped to a distribution in "
            "IMPORT_TO_DISTRIBUTION:\n  - " + "\n  - ".join(unmapped),
        )
        self.assertEqual(
            undeclared, [],
            "these packages are imported by the test suite but declared in no requirements "
            "file, so ./scripts/validate.sh would silently depend on the caller's venv:\n  - "
            + "\n  - ".join(undeclared),
        )

    def test_validate_script_preflights_its_dependencies(self):
        text = VALIDATE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("requirements-dev.txt", text, "validate.sh must name the file to install")
        self.assertIn("Python test dependencies", text, "validate.sh needs a dependency preflight")
        for distribution in ("PyYAML", "pytest"):
            self.assertIn(
                distribution, text,
                f"validate.sh's preflight must cover {distribution}",
            )

    def test_ci_installs_the_declared_dependencies(self):
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "requirements-dev.txt", text,
            "CI must install requirements-dev.txt rather than relying on the runner image",
        )


if __name__ == "__main__":
    unittest.main()
