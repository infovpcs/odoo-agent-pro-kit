"""Tests for the odoo_requirement_gap_analysis skill and its helper scripts."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "plugin" / "skills" / "OdooRequirementGapAnalysis"
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(SCRIPTS))

import audit_document  # noqa: E402
import catalog_match  # noqa: E402
import verify_modules  # noqa: E402
from validate_skills import check_frontmatter, check_private_strings  # noqa: E402

DOC = """1. Executive Summary
Body text. See Section 3 for the flow and Section 9 for the open questions.

2. Sales
Priority: Must Have
Quotation flow.

3. Serial Tracking
Priority: Nice to Have
This is a hard requirement for the certified line.

4. Reporting
Compliance uses Section 2.
"""


class TestSkillFile(unittest.TestCase):
    def test_skill_passes_repository_validation(self):
        skill = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill.is_file())
        self.assertEqual(check_frontmatter(skill), [])
        self.assertEqual(check_private_strings(skill), [])

    def test_skill_documents_every_phase_and_the_lifecycle(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for needle in ("Phase 0", "Phase 6", "Phase 7", "Phase 8", "/plan-analysis", "/start-coding", "/testing", "/fleet",
                       "sandboxctl module", "GAP_PROFILE", "inclusion threshold", "index page", "classification assist", "negative evidence"):
            self.assertIn(needle, text)

    def test_profile_template_is_generic(self):
        template = SKILL_DIR / "templates" / "delivery-profile.template.md"
        self.assertTrue(template.is_file())
        self.assertEqual(check_private_strings(template), [])


class TestAuditDocument(unittest.TestCase):
    def test_finds_unresolved_reference_and_priority_conflict(self):
        result = audit_document.audit(DOC)
        self.assertEqual([h["number"] for h in result["headings"]], [1, 2, 3, 4])
        unresolved = {r["ref"] for r in result["unresolved_references"]}
        self.assertEqual(unresolved, {9})
        self.assertEqual(len(result["priority_conflicts"]), 1)
        self.assertEqual(result["priority_conflicts"][0]["section"], 3)

    def test_reports_gaps_in_heading_numbers(self):
        result = audit_document.audit("1. Alpha section\ntext\n\n3. Gamma section\ntext\n")
        self.assertEqual(result["missing_numbers"], [2])

    def test_cli_reads_a_text_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "req.txt"
            doc.write_text(DOC, encoding="utf-8")
            done = subprocess.run([sys.executable, str(SCRIPTS / "audit_document.py"), str(doc)], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0)
            self.assertIn("Section 9", done.stdout)
            self.assertIn("Priority contradictions (1)", done.stdout)


class TestVerifyModules(unittest.TestCase):
    def _tree(self, root: Path, name: str, version="19.0.1.0"):
        mod = root / name
        mod.mkdir(parents=True)
        (mod / "__manifest__.py").write_text(repr({"name": name, "version": version, "summary": "S", "license": "LGPL-3", "depends": ["base"]}), encoding="utf-8")

    def test_resolves_edition_and_reports_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            community, enterprise = Path(tmp) / "c", Path(tmp) / "e"
            self._tree(community, "sale")
            self._tree(enterprise, "account_budget")
            trees = [("Community", community), ("Enterprise", enterprise), ("Core", None)]
            self.assertEqual(verify_modules.resolve("sale", trees)["edition"], "Community")
            self.assertEqual(verify_modules.resolve("account_budget", trees)["edition"], "Enterprise")
            self.assertIsNone(verify_modules.resolve("nope", trees))

    def test_cli_exits_non_zero_when_a_module_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            community = Path(tmp) / "c"
            self._tree(community, "sale")
            script = str(SCRIPTS / "verify_modules.py")
            ok = subprocess.run([sys.executable, script, "--community", str(community), "--modules", "sale"], capture_output=True, text=True)
            bad = subprocess.run([sys.executable, script, "--community", str(community), "--modules", "sale,missing_mod"], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0)
            self.assertEqual(bad.returncode, 1)
            self.assertIn("missing_mod", bad.stdout)


class TestCatalogMatch(unittest.TestCase):
    def test_port_status(self):
        self.assertEqual(catalog_match.port_status(["17.0", "19.0"], "19.0"), ("ready", "19.0"))
        self.assertEqual(catalog_match.port_status(["17.0", "18.0"], "19.0"), ("port", "18.0"))
        self.assertEqual(catalog_match.port_status([], "19.0"), ("unknown", None))

    def test_shortlists_relevant_module_and_respects_version_gap(self):
        catalog = [
            {"module": "approval_chain", "name": "Purchase approvals", "summary": "Multi level purchase order approval workflow with notifications", "versions": ["18.0"]},
            {"module": "pos_screen", "name": "POS screen", "summary": "Kitchen screen for restaurant point of sale", "versions": ["13.0"]},
        ]
        reqs = [{"id": "R-1", "title": "Multi level purchase order approval", "gap": "approval workflow by amount"}]
        with tempfile.TemporaryDirectory() as tmp:
            c, r, out = Path(tmp) / "c.json", Path(tmp) / "r.json", Path(tmp) / "o.json"
            c.write_text(json.dumps(catalog), encoding="utf-8")
            r.write_text(json.dumps(reqs), encoding="utf-8")
            done = subprocess.run([sys.executable, str(SCRIPTS / "catalog_match.py"), "--catalog", str(c), "--requirements", str(r),
                                   "--target", "19.0", "--json", str(out)], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data[0]["candidates"][0]["module"], "approval_chain")
            self.assertEqual(data[0]["candidates"][0]["target_status"], "port")
            self.assertNotIn("pos_screen", [c_["module"] for c_ in data[0]["candidates"]])


if __name__ == "__main__":
    unittest.main()
