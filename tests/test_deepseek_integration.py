"""DeepSeek Harness (DSH) integration tests.

Covers the two artifacts that make the DSH integration real:

* the agent preset under ``integrations/deepseek/preset`` — composition shape,
  realm/plane placement, and the installer contract; and
* the ``odoo-kit`` Cordis plugin's behaviour, exercised by
  ``integrations/deepseek/tests/plugin.test.mjs`` against a recording stub of
  the Cordis context (skipped when Node.js is unavailable).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = REPO_ROOT / "integrations" / "deepseek"
PRESET = INTEGRATION / "preset"
COMPOSITION = PRESET / "agent.cordis.yml"
PLUGIN_TEST = INTEGRATION / "tests" / "plugin.test.mjs"


def load_composition() -> list:
    """Parse the composition with the loader's YAML dialect (``!!js`` tags)."""
    class JsTagLoader(yaml.SafeLoader):
        pass

    def js_tag(loader, node):  # noqa: ANN001 - PyYAML callback signature
        return node.value

    JsTagLoader.add_constructor("tag:yaml.org,2002:js", js_tag)
    with COMPOSITION.open(encoding="utf-8") as handle:
        return yaml.load(handle, Loader=JsTagLoader)


def flatten(rows: list) -> list:
    """Flatten groups into one row list."""
    out = []
    for row in rows:
        out.append(row)
        if row.get("group") is True:
            out.extend(flatten(row.get("config") or []))
    return out


class TestPresetShape(unittest.TestCase):
    def test_preset_files_exist(self):
        for name in ("agent.cordis.yml", "preset.yml", "odoo-kit.mjs"):
            self.assertTrue((PRESET / name).is_file(), f"missing {name}")

    def test_preset_id_is_a_valid_dsh_preset_id(self):
        # `dsh-agent-presets` requires the directory name (the preset id) to
        # match this grammar; it becomes a path segment.
        self.assertRegex("odoo-agent-pro-kit", r"^[a-z0-9][a-z0-9-]*$")

    def test_metadata_declares_name_and_description(self):
        meta = yaml.safe_load((PRESET / "preset.yml").read_text(encoding="utf-8"))
        self.assertTrue(meta["name"].strip())
        self.assertTrue(meta["description"].strip())
        self.assertIsInstance(meta["order"], int)

    def test_composition_is_a_top_level_row_list(self):
        rows = load_composition()
        self.assertIsInstance(rows, list)
        self.assertTrue(rows)
        for row in rows:
            self.assertIsInstance(row, dict)
            self.assertIsInstance(row.get("name"), str)
            self.assertTrue(row["name"])

    def test_row_ids_are_unique(self):
        ids = [row["id"] for row in flatten(load_composition()) if "id" in row]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate row ids: {ids}")


class TestPresetPlanes(unittest.TestCase):
    """The `isolate` realm rules the DSH preset loader enforces."""

    def setUp(self):
        self.rows = load_composition()
        self.by_id = {row.get("id"): row for row in self.rows}

    def test_preset_owned_services_stay_behind_isolate_realms(self):
        # planMode, compaction/toolResultPruner, and workflowEngine have no
        # consumer outside one agent, so each provider and its consumers share
        # one entry-local realm.
        for group_id, realm_keys in (
            ("planning", {"planMode"}),
            ("compaction", {"compaction", "toolResultPruner"}),
            ("delegation", {"workflowEngine"}),
        ):
            group = self.by_id.get(group_id)
            self.assertIsNotNone(group, f"missing group {group_id}")
            self.assertTrue(group.get("group"), f"{group_id} must be a group")
            realms = group.get("isolate") or {}
            self.assertEqual(
                {key for key, value in realms.items() if value},
                realm_keys,
                f"{group_id} realm mismatch",
            )

    def test_host_plane_rows_sit_outside_every_realm(self):
        # These rows only consume host registries; putting them behind a realm
        # would make them resolve a registry this preset never populated.
        for row_id in ("odoo-kit", "tool-bash", "tool-fs", "tool-jobs",
                       "skill-filesystem", "tool-skill", "tool-web", "present",
                       "tool-goal", "command-goal", "tool-todo", "tool-ask-user"):
            self.assertIn(row_id, self.by_id, f"missing host-plane row {row_id}")

        # No loose row may declare an isolate realm of its own.
        for row in self.rows:
            if row.get("group") is True:
                continue
            self.assertNotIn("isolate", row, f"{row.get('id')} must not carry its own realm")

    def test_odoo_kit_row_points_at_the_preset_local_plugin(self):
        row = self.by_id["odoo-kit"]
        # A `./` specifier resolves against the preset's own directory, which
        # is what lets the plugin ship inside the preset with no node_modules.
        self.assertEqual(row["name"], "./odoo-kit.mjs")
        self.assertTrue((PRESET / "odoo-kit.mjs").is_file())

    def test_odoo_kit_does_not_provide_a_service_realm(self):
        # It registers into the scoped tools/commands/skills/systemPrompt
        # registries and provides nothing, so it must sit loose.
        self.assertNotIn("isolate", self.by_id["odoo-kit"])


class TestInstaller(unittest.TestCase):
    def test_dry_run_reports_the_user_preset_root(self):
        result = subprocess.run(
            ["bash", str(INTEGRATION / "install.sh"), "--dry-run"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        )
        self.assertIn(".agent-presets/odoo-agent-pro-kit", result.stdout)
        self.assertIn(str(REPO_ROOT), result.stdout)

    def test_shell_syntax_is_valid(self):
        subprocess.run(["bash", "-n", str(INTEGRATION / "install.sh")], check=True)


@unittest.skipUnless(shutil.which("node"), "Node.js is required for the DSH plugin test")
class TestPluginBehaviour(unittest.TestCase):
    def test_plugin_behaviour_suite_passes(self):
        result = subprocess.run(
            ["node", str(PLUGIN_TEST)],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=180,
        )
        if result.returncode != 0:
            self.fail(f"plugin test failed:\n{result.stdout}\n{result.stderr}")
        self.assertIn("all odoo-agent-pro-kit DSH plugin checks passed", result.stdout)

    def test_plugin_is_dependency_free_esm(self):
        """A user preset cannot resolve the harness's own packages."""
        source = (PRESET / "odoo-kit.mjs").read_text(encoding="utf-8")
        offenders = []
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped.startswith("import "):
                continue
            if "from 'node:" in stripped or 'from "node:' in stripped:
                continue
            offenders.append(stripped)
        self.assertEqual(offenders, [], f"non-builtin imports are not resolvable from a user preset: {offenders}")


class TestDocumentation(unittest.TestCase):
    def test_readme_and_install_doc_exist(self):
        for name in ("README.md", "INSTALL.md"):
            path = INTEGRATION / name
            self.assertTrue(path.is_file(), f"missing {name}")
            self.assertGreater(len(path.read_text(encoding="utf-8").strip()), 500)

    def test_integration_is_linked_from_the_main_readme(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("integrations/deepseek", readme)


if __name__ == "__main__":
    sys.exit(unittest.main())
