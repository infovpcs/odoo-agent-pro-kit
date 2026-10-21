"""The CI smoke fixture must carry a real Odoo test: since 5039a46 a test run with no test fails."""

import ast
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "sandbox" / "fixtures" / "sandbox_fixture"


def test_fixture_carries_an_odoo_test():
    tests = FIXTURE / "tests"
    init = (tests / "__init__.py").read_text()
    imported = [line.split("import", 1)[1].strip() for line in init.splitlines() if line.startswith("from . import")]
    assert imported, "tests/__init__.py imports no test module"
    found = []
    for name in imported:
        tree = ast.parse((tests / f"{name}.py").read_text())
        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            bases = {getattr(b, "attr", getattr(b, "id", "")) for b in cls.bases}
            if bases & {"TransactionCase", "SingleTransactionCase"}:
                found += [f.name for f in cls.body if isinstance(f, ast.FunctionDef) and f.name.startswith("test_")]
    assert found, "no TransactionCase test method in the fixture"


def test_fixture_tests_are_not_removed_for_odoo_20():
    remove = FIXTURE.parent / "_overlays" / "20" / "sandbox_fixture" / ".remove"
    assert "tests" not in remove.read_text()
