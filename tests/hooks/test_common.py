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


def test_raw_odoo_allowed_reads_env(monkeypatch):
    monkeypatch.delenv("ODOO_KIT_ALLOW_RAW_ODOO", raising=False)
    assert common.raw_odoo_allowed() is False
    monkeypatch.setenv("ODOO_KIT_ALLOW_RAW_ODOO", "yes")
    assert common.raw_odoo_allowed() is True
    monkeypatch.setenv("ODOO_KIT_ALLOW_RAW_ODOO", "nope")
    assert common.raw_odoo_allowed() is False


def test_edit_bodies_direct_and_multiedit():
    assert common.edit_bodies({"content": "hello"}) == "hello"
    assert common.edit_bodies({"new_string": "ns"}) == "ns"
    joined = common.edit_bodies({"edits": [{"new_string": "a"}, {"new_string": "b"}, "bad"]})
    assert joined == "a\nb"
    assert common.edit_bodies({}) == ""


def test_resolve_module_dir_uses_explicit_module_arg(tmp_path):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t1\n")
    # called from the PARENT of mymod with an explicit module argument
    assert common.resolve_module_dir(tmp_path, "/testing 19 mymod") == mod.resolve()
    assert common.resolve_module_dir(tmp_path, "19.0 mymod") == mod.resolve()
    assert common.resolve_module_dir(tmp_path, "/start-coding mymod") == mod.resolve()


def test_resolve_module_dir_falls_back_to_find(tmp_path):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t1\n")
    nested = mod / "models"
    nested.mkdir()
    # no usable module token -> fall back to walking up from cwd
    assert common.resolve_module_dir(nested, "/testing 19") == mod.resolve()
    assert common.resolve_module_dir(nested, "") == mod.resolve()
    # token that is not an existing dir -> fall back
    assert common.resolve_module_dir(nested, "/testing 19 nonesuch") == mod.resolve()


def test_newest_tracked_mtime_non_git_is_zero(tmp_path):
    assert common.newest_tracked_mtime(tmp_path) == 0.0
