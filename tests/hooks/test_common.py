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
