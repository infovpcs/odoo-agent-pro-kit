#!/usr/bin/env python3
"""
Helper for templating and writing Odoo config files.

**Linux (Ubuntu) Setup Requirements:**
- Python 3.12.12 (installed from deadsnakes PPA: ppa:deadsnakes/ppa)
- PostgreSQL 14+ (auto-installed via apt-get)
- uv 0.10.0+ (fast Python package manager, auto-installed via pip)

This module is part of the unified bootstrap process:
1. bootstrap_odoo_env.sh - Creates virtual environments with uv
2. bootstrap_odoo_env.py - Generates configuration files from templates
3. setup_agent_skills.py - Deploys AI agent skills
4. deploy_copilot_agent.py - Installs Copilot agents

**Template System:**
Config templates in config/odoo.conf.{VER} use {{WORKSPACE_PATH}} placeholders
that are substituted with actual workspace paths during config generation.
After placeholder substitution, key-value pairs (db_name, port, etc.) are
updated to match the workspace's specific settings.

**Port/DB Convention (matches manage_modules.sh):**
    PORT  = 8090 + VERSION  (e.g., 8107 for v17, 8109 for v19)
    DB    = odoo{VERSION}   (e.g., odoo17, odoo19)

**Usage:**
    python3 bootstrap_odoo_env.py --workspace /path/to/19_workspace \\
        --version 19 --write-config

**Note on Odoo Versions:**
- Odoo 12-14: Requires Python 3.6/3.7 (uses pyenv)
- Odoo 15-19: Requires Python 3.12 (uses uv)
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List


DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parent / "config"


def _update_or_append(lines: List[str], key: str, value: str, insert_after_idx: int) -> None:
    pattern = re.compile(rf"^(\s*{re.escape(key)}\s*=).*$", re.IGNORECASE)
    for i, line in enumerate(lines):
        if pattern.match(line):
            prefix = pattern.match(line).group(1)
            lines[i] = f"{prefix} {value}\n"
            return

    # Not found; insert after the [options] header block
    insertion = f"{key} = {value}\n"
    lines.insert(insert_after_idx, insertion)


def _find_options_insert_idx(lines: List[str]) -> int:
    for i, line in enumerate(lines):
        if line.strip().lower() == "[options]":
            return i + 1
    return 0


def render_config(
    template_path: Path,
    output_path: Path,
    replacements: Dict[str, str],
    workspace_path: str = "",
) -> None:
    text = template_path.read_text(encoding="utf-8")
    # Substitute {{WORKSPACE_PATH}} placeholders first
    if workspace_path:
        text = text.replace("{{WORKSPACE_PATH}}", workspace_path)
    
    # Substitute DB credentials if present in replacements
    if "db_user" in replacements:
        text = text.replace("{{DB_USER}}", replacements["db_user"])
    if "db_password" in replacements:
        text = text.replace("{{DB_PASSWORD}}", replacements["db_password"])
    lines = text.splitlines(keepends=True)
    insert_idx = _find_options_insert_idx(lines)

    for key, value in replacements.items():
        _update_or_append(lines, key, value, insert_idx)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Odoo config files for a workspace.")
    parser.add_argument("--detect-versions", action="store_true", help="Print min/max Python and min PG from repo")
    parser.add_argument("--repo", default="", help="Path to Odoo repo for --detect-versions")
    parser.add_argument("--workspace", help="Workspace path (e.g., /path/to/19_workspace)")
    parser.add_argument("--version", help="Odoo major version (e.g., 12, 13, 14, 15, 16, 17, 18, 19)")
    parser.add_argument("--db-user", default="odoo")
    parser.add_argument("--db-password", default="odoo")
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-port", default="5432")
    parser.add_argument("--admin-passwd", default="admin")
    parser.add_argument("--port", help="HTTP/XMLRPC port")
    parser.add_argument("--extra-addons", default="", help="Comma-separated extra addons paths")
    parser.add_argument("--template", default="", help="Override template path")
    parser.add_argument("--write-config", action="store_true", help="Write config file")

    args = parser.parse_args()

    if args.detect_versions:
        repo = Path(args.repo).resolve()
        release_py = repo / "odoo" / "release.py"
        init_py = repo / "odoo" / "__init__.py"
        setup_py = repo / "setup.py"

        def _find_tuple(src: str, key: str) -> str:
            match = re.search(rf"{key}\\s*=\\s*\\((\\d+)\\s*,\\s*(\\d+)\\)", src)
            if not match:
                return ""
            return f"{match.group(1)}.{match.group(2)}"

        min_py = max_py = min_pg = ""
        if release_py.exists():
            content = release_py.read_text(encoding="utf-8", errors="ignore")
            min_py = _find_tuple(content, "MIN_PY_VERSION")
            max_py = _find_tuple(content, "MAX_PY_VERSION")
            match_pg = re.search(r"MIN_PG_VERSION\\s*=\\s*(\\d+)", content)
            if match_pg:
                min_pg = match_pg.group(1)

        if (not min_py or not max_py) and init_py.exists():
            content = init_py.read_text(encoding="utf-8", errors="ignore")
            min_py = min_py or _find_tuple(content, "MIN_PY_VERSION")
            max_py = max_py or _find_tuple(content, "MAX_PY_VERSION")

        if (not min_py or not max_py) and setup_py.exists():
            content = setup_py.read_text(encoding="utf-8", errors="ignore")
            # Example: python_requires='>=3.10'
            match_min = re.search(r"python_requires\\s*=\\s*['\\\"]>=\\s*(\\d+)\\.(\\d+)", content)
            if match_min and not min_py:
                min_py = f"{match_min.group(1)}.{match_min.group(2)}"
            # Example: python_requires='>=3.6,<3.9'
            match_max = re.search(r"python_requires\\s*=\\s*['\\\"][^'\\\"]*<\\s*(\\d+)\\.(\\d+)", content)
            if match_max and not max_py:
                major = int(match_max.group(1))
                minor = int(match_max.group(2))
                # Convert "<3.9" to max "3.8"
                if minor > 0:
                    minor -= 1
                max_py = f"{major}.{minor}"

        if min_py:
            print(f"MIN_PY_VERSION={min_py}")
        if max_py:
            print(f"MAX_PY_VERSION={max_py}")
        if min_pg:
            print(f"MIN_PG_VERSION={min_pg}")
        return

    if not args.workspace:
        raise SystemExit("--workspace is required unless --detect-versions is used")
    if not args.version or not args.port:
        raise SystemExit("--version and --port are required unless --detect-versions is used")

    if not args.version.isdigit():
        raise SystemExit("--version must be a numeric major version, e.g., 16")

    workspace = Path(args.workspace).resolve()
    version = args.version

    template = Path(args.template) if args.template else DEFAULT_TEMPLATE_DIR / f"odoo.conf.{version}"
    template_exists = template.exists()

    odoo_dir = workspace / f"{version}.0"
    extra_dir = workspace / f"extra-{version}"
    config_path = workspace / "config" / f"odoo.conf.{version}"
    log_path = workspace / "logs" / "odoo.log"
    data_dir = workspace / "data"

    addons_paths = [
        str(odoo_dir / "addons"),
        str(extra_dir),
    ]
    if args.extra_addons:
        for part in args.extra_addons.split(","):
            part = part.strip()
            if part:
                addons_paths.append(part)

    db_name = f"odoo{version}"
    replacements = {
        "db_host": args.db_host,
        "db_port": args.db_port,
        "db_user": args.db_user,
        "db_password": args.db_password,
        "db_name": db_name,
        "dbfilter": f"^{db_name}$",
        "http_port": args.port,
        "xmlrpc_port": args.port,
        "addons_path": ",".join(addons_paths),
        "data_dir": str(data_dir),
        "logfile": str(log_path),
        "admin_passwd": args.admin_passwd,
        "test_file": str(workspace / "logs" / "test-results.xml"),
    }

    if args.write_config:
        if template_exists:
            render_config(template, config_path, replacements, workspace_path=str(workspace))
        else:
            # Minimal config fallback for older versions without a template
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                """[options]\n"""
                f"db_host = {args.db_host}\n"
                f"db_port = {args.db_port}\n"
                f"db_user = {args.db_user}\n"
                f"db_password = {args.db_password}\n"
                f"db_name = odoo{version}\n"
                f"dbfilter = ^odoo{version}$\n"
                f"http_port = {args.port}\n"
                f"xmlrpc_port = {args.port}\n"
                f"addons_path = {','.join(addons_paths)}\n"
                f"data_dir = {data_dir}\n"
                f"logfile = {log_path}\n"
                f"admin_passwd = {args.admin_passwd}\n"
                "log_level = info\n"
                """\n""",
                encoding="utf-8",
            )
        print(f"Wrote config: {config_path}")
    else:
        print("--write-config not provided; no files written")


if __name__ == "__main__":
    main()
