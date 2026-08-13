#!/usr/bin/env python3
"""Create a deterministic dependency and declared-license inventory."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    locks = {}
    for line in (ROOT / "sandbox/config/images.lock").read_text().splitlines():
        if line and not line.startswith("#"):
            name, value = line.split("=", 1)
            locks[name] = value
    requirements = []
    for path in sorted(ROOT.glob("**/requirements.txt")):
        for line in path.read_text().splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                requirements.append({"source": str(path.relative_to(ROOT)), "requirement": value})
    declared = re.search(r"Apache License[^\n]*Version 2\.0", (ROOT / "LICENSE").read_text())
    report = {
        "schema_version": "1.0.0",
        "project_license": "Apache-2.0" if declared else "UNKNOWN",
        "container_images": locks,
        "python_requirements": requirements,
        "notes": "Image and package transitive licenses require registry/SBOM scanning before release.",
    }
    target = ROOT / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
