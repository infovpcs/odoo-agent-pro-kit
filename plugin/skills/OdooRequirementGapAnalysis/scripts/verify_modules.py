#!/usr/bin/env python3
"""Verify that Odoo module names used in a gap analysis exist in the code trees (Phase 2).

Reads each module's ``__manifest__.py`` (without importing it) and reports the edition,
version, licence and summary, so every "module X covers requirement Y" claim is backed by
code rather than memory. Exits 1 when any module is missing, so it can gate a build.

Usage:
    python3 verify_modules.py --community ~/odoo-workspaces/19_workspace/19.0/addons \\
        --enterprise ~/workspace/ent-19 --modules crm,sale,account_budget
    python3 verify_modules.py --community ... --enterprise ... --dataset requirements.json --json out.json

``--dataset`` is a JSON list of objects that carry a ``mods`` list (the mapping rows).
Modules that belong to Odoo core (``base``, ``web``, ...) live outside ``addons/`` - pass
``--core PATH`` (the ``odoo/addons`` folder) to resolve them too.
"""
import argparse
import ast
import json
import sys
from pathlib import Path


def read_manifest(root: Path, module: str):
    path = root / module / "__manifest__.py"
    if not path.is_file():
        return None
    try:
        data = ast.literal_eval(path.read_text(encoding="utf-8"))
    except (ValueError, SyntaxError):
        data = {}
    return dict(version=str(data.get("version", "")), name=str(data.get("name", "")),
                summary=" ".join(str(data.get("summary", "")).split()), license=str(data.get("license", "")),
                depends=list(data.get("depends", [])))


def resolve(module: str, trees):
    """Return the manifest info plus the edition of the first tree that has the module."""
    for edition, root in trees:
        if root is None:
            continue
        info = read_manifest(root, module)
        if info is not None:
            return dict(module=module, edition=edition, **info)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--community", type=Path, help="Community addons directory")
    ap.add_argument("--enterprise", type=Path, help="Enterprise addons directory")
    ap.add_argument("--core", type=Path, help="Odoo core addons directory (odoo/addons)")
    ap.add_argument("--modules", help="comma-separated module names")
    ap.add_argument("--dataset", type=Path, help="JSON list of rows with a 'mods' list")
    ap.add_argument("--json", type=Path, help="write results to this JSON file")
    args = ap.parse_args(argv)

    names = []
    if args.modules:
        names += [m.strip() for m in args.modules.split(",") if m.strip()]
    if args.dataset:
        for row in json.loads(args.dataset.read_text(encoding="utf-8")):
            names += list(row.get("mods", []))
    names = sorted(set(names))
    if not names:
        ap.error("give --modules and/or --dataset")

    trees = [("Community", args.community), ("Enterprise", args.enterprise), ("Core", args.core)]
    missing_trees = [n for n, p in trees[:2] if p is not None and not p.is_dir()]
    if missing_trees:
        raise SystemExit("Directory not found for: %s" % ", ".join(missing_trees))

    found, missing = [], []
    for name in names:
        info = resolve(name, trees)
        (found if info else missing).append(info or name)

    print("%-38s %-11s %-9s %s" % ("module", "edition", "version", "summary"))
    for m in found:
        print("%-38s %-11s %-9s %s" % (m["module"], m["edition"], m["version"], m["summary"][:70]))
    if missing:
        print("\nNOT FOUND (%d): %s" % (len(missing), ", ".join(missing)))
    print("\n%d verified, %d missing" % (len(found), len(missing)))
    if args.json:
        args.json.write_text(json.dumps(dict(found=found, missing=missing), indent=2), encoding="utf-8")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
