import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_skills import check_frontmatter, check_private_strings, parse_frontmatter


class TestParseFrontmatter(unittest.TestCase):
    def test_parses_name_and_description(self):
        text = "---\nname: my-skill\ndescription: Does a thing.\n---\n\nBody text.\n"
        fields = parse_frontmatter(text)
        self.assertEqual(fields["name"], "my-skill")
        self.assertEqual(fields["description"], "Does a thing.")

    def test_returns_empty_dict_without_frontmatter(self):
        self.assertEqual(parse_frontmatter("# Just a heading\n"), {})


class TestCheckFrontmatter(unittest.TestCase):
    def test_valid_file_has_no_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text("---\nname: my-skill\ndescription: Does a thing.\n---\nBody\n")
            self.assertEqual(check_frontmatter(path), [])

    def test_missing_description_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text("---\nname: my-skill\n---\nBody\n")
            errors = check_frontmatter(path)
            self.assertEqual(len(errors), 1)
            self.assertIn("description", errors[0])


class TestCheckPrivateStrings(unittest.TestCase):
    def test_flags_known_private_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(
                "---\nname: my-skill\ndescription: Does a thing.\n---\n"
                "See /Users/vinusoft85/workspace\n"
            )
            errors = check_private_strings(path)
            self.assertEqual(len(errors), 1)
            self.assertIn("vinusoft85", errors[0])

    def test_clean_file_has_no_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(
                "---\nname: my-skill\ndescription: Does a thing.\n---\nSee <workspace-root>\n"
            )
            self.assertEqual(check_private_strings(path), [])


class TestCLI(unittest.TestCase):
    def test_exits_nonzero_when_no_skill_files_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = str(Path(__file__).resolve().parents[1] / "scripts" / "validate_skills.py")
            result = subprocess.run(
                [sys.executable, script, tmp], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
