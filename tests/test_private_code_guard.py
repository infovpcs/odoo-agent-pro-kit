"""Phase 11: private module code (source, migrated code, patches) must never be committed here."""
import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("private_code_guard", ROOT / "scripts/private_code_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_kit_fixture_modules_are_allowed():
    assert guard.violations(["sandbox/fixtures/sandbox_fixture/__manifest__.py",
                             "sandbox/fixtures/_overlays/20/sandbox_fixture/__manifest__.py"]) == []


def test_an_odoo_module_outside_the_fixtures_is_refused():
    found = guard.violations(["docs/x/vpcs_gitlab/__manifest__.py", "vpcs_llm_provider/__manifest__.py"])
    assert [v.path for v in found] == ["docs/x/vpcs_gitlab/__manifest__.py", "vpcs_llm_provider/__manifest__.py"]
    assert all(v.reason == "odoo-module" for v in found)


def test_an_openerp_manifest_is_a_module_too():
    assert [v.reason for v in guard.violations(["legacy/mod/__openerp__.py"])] == ["odoo-module"]


def test_patches_bundles_and_archives_are_refused():
    names = ["docs/phase-11/group-a.patch", "x/migration.diff", "code.bundle", "mods.tgz", "mods.tar.gz", "mods.zip"]
    assert [v.reason for v in guard.violations(names)] == ["patch-or-archive"] * len(names)


def test_grandfathered_phase8_evidence_is_allowed():
    assert guard.violations(sorted(guard.ALLOWED_ARCHIVES)) == []


def test_ordinary_kit_files_pass():
    assert guard.violations(["README.md", "sandbox/bin/sandboxctl", "tests/test_x.py", "docs/a/manifest.md"]) == []


def test_the_repository_tree_is_clean():
    names = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, text=True,
                           capture_output=True, check=True).stdout.splitlines()
    found = guard.violations(names)
    assert not found, "private module code must stay in the gitignored .sandbox/:\n" + "\n".join(
        f"{v.path}: {v.reason}" for v in found)


def test_cli_exit_codes():
    ok = subprocess.run(["python3", str(ROOT / "scripts/private_code_guard.py")], cwd=ROOT,
                        capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    bad = subprocess.run(["python3", str(ROOT / "scripts/private_code_guard.py"), "mod/__manifest__.py"],
                         cwd=ROOT, capture_output=True, text=True)
    assert bad.returncode == 1 and "odoo-module" in bad.stderr
