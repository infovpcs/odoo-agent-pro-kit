#!/usr/bin/env python3
"""Validate SKILL.md frontmatter and scan for leaked private strings."""
import argparse
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = ("name", "description")

PRIVATE_STRING_PATTERNS = [
    r"GlobalCad",
    r"Aptus",
    r"Aashir",
    r"WSTN",
    r"autopack",
    r"vinusoft85",
    r"vperfectcs",
    r"GITHUB_TOKEN",
    r"@gmail\.com",
]


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip("\n")
    fields = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def check_frontmatter(path: Path) -> list:
    text = path.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    errors = []
    for field in REQUIRED_FIELDS:
        if not fields.get(field):
            errors.append(f"{path}: missing or empty required frontmatter field '{field}'")
    return errors


def check_private_strings(path: Path) -> list:
    text = path.read_text(encoding="utf-8")
    errors = []
    pattern = re.compile("|".join(PRIVATE_STRING_PATTERNS), re.IGNORECASE)
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = pattern.search(line)
        if match:
            errors.append(f"{path}:{lineno}: possible leaked private string '{match.group(0)}'")
    return errors


def find_skill_files(root: Path):
    return sorted(root.glob("**/SKILL.md"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", nargs="?", default="plugin/skills",
        help="Directory to scan for SKILL.md files",
    )
    args = parser.parse_args(argv)

    root = Path(args.root)
    skill_files = find_skill_files(root)
    if not skill_files:
        print(f"No SKILL.md files found under {root}", file=sys.stderr)
        return 1

    all_errors = []
    for skill_file in skill_files:
        all_errors.extend(check_frontmatter(skill_file))
        all_errors.extend(check_private_strings(skill_file))

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        print(
            f"\n{len(all_errors)} issue(s) found across {len(skill_files)} skill file(s).",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {len(skill_files)} skill file(s) validated, no issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
