#!/usr/bin/env python3
"""Intake audit for a requirements document (Phase 0 of odoo_requirement_gap_analysis).

Extracts text from a PDF, DOCX, Markdown or text file and reports the problems that
should be raised with the author *before* any mapping starts:

* the printed heading map (numbered headings) and gaps or duplicates in the numbering;
* "Section N" / "Sec. N" / "clause N" cross-references that point at a heading that does
  not exist, with the heading each one resolves to so a human can check the meaning;
* sections whose stated priority (Must / Should / Nice to Have) contradicts the wording
  used in the same section ("hard requirement", "mandatory", "critical", ...);
* a rough size summary (pages, words, headings) for scoping.

The script only reads the file. It never writes next to the source document.

Usage:
    python3 audit_document.py REQUIREMENTS.pdf
    python3 audit_document.py REQUIREMENTS.docx --json audit.json
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^\s{0,3}(\d{1,3})[.)]\s+([A-Z][^\n]{2,90})$")
REF_RE = re.compile(r"\b(?:Sections?|Sec\.|Clauses?|Chapters?)\s+(\d{1,3})(?:\s*(?:,|and|&|/)\s*(\d{1,3}))*", re.IGNORECASE)
PRIORITY_RE = re.compile(r"Priority\s*:\s*(Must Have|Should Have|Nice to Have|Could Have|Won.t Have|High|Medium|Low)", re.IGNORECASE)
STRONG_WORDS = re.compile(r"\b(hard requirement|mandatory|must be|non-negotiable|critical|cannot be an afterthought|required regardless)\b", re.IGNORECASE)
WEAK_PRIORITY = re.compile(r"nice to have|could have|low", re.IGNORECASE)


def extract_text(path: Path):
    """Return (text, pages). Tries the best available extractor for the file type."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            import fitz  # PyMuPDF  # type: ignore[import-not-found]
            doc = fitz.open(path)
            return "\n".join(page.get_text() for page in doc), len(doc)  # type: ignore[attr-defined]
        except ImportError:
            pass
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n".join((p.extract_text() or "") for p in reader.pages), len(reader.pages)
        except ImportError:
            pass
        if shutil.which("pdftotext"):
            out = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True).stdout
            return out, out.count("\f") + 1
        raise SystemExit("No PDF extractor found. Install one of: pymupdf, pypdf, poppler (pdftotext).")
    if suffix in (".docx", ".doc", ".odt", ".rtf"):
        if shutil.which("pandoc"):
            out = subprocess.run(["pandoc", "-t", "plain", "--wrap=none", str(path)], capture_output=True, text=True, check=True).stdout
            return out, None
        raise SystemExit("pandoc is required to read %s files." % suffix)
    return path.read_text(encoding="utf-8", errors="replace"), None


def audit(text: str) -> dict:
    lines = text.splitlines()
    headings = []  # (number, title, line_index)
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m and not line.rstrip().endswith((".", ",", ";", ":")):
            headings.append((int(m.group(1)), m.group(2).strip(), i))

    numbers = [h[0] for h in headings]
    seen, duplicates = set(), []
    for n in numbers:
        if n in seen:
            duplicates.append(n)
        seen.add(n)
    expected = set(range(min(numbers), max(numbers) + 1)) if numbers else set()
    missing_numbers = sorted(expected - seen)
    by_number = {}
    for n, title, idx in headings:
        by_number.setdefault(n, (title, idx))

    refs = []
    for i, line in enumerate(lines):
        for m in REF_RE.finditer(line):
            nums = {int(x) for x in re.findall(r"\d+", m.group(0))}
            owner = None
            for n, _title, idx in reversed(headings):
                if idx <= i:
                    owner = n
                    break
            for n in sorted(nums):
                target = by_number.get(n)
                refs.append(dict(line=i + 1, in_section=owner, ref=n, resolves_to=target[0] if target else None,
                                 exists=target is not None, context=line.strip()[:140]))
    unresolved = [r for r in refs if not r["exists"]]

    priority_conflicts = []
    bounds = [h[2] for h in headings] + [len(lines)]
    for k, (n, title, idx) in enumerate(headings):
        block = "\n".join(lines[idx:bounds[k + 1]])
        pm = PRIORITY_RE.search(block)
        if pm and WEAK_PRIORITY.search(pm.group(1)):
            sw = STRONG_WORDS.search(block)
            if sw:
                priority_conflicts.append(dict(section=n, title=title, priority=pm.group(1), wording=sw.group(0)))

    return dict(headings=[dict(number=n, title=t, line=i + 1) for n, t, i in headings], duplicate_numbers=duplicates,
                missing_numbers=missing_numbers, references=refs, unresolved_references=unresolved,
                priority_conflicts=priority_conflicts, words=len(text.split()))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("document", type=Path)
    ap.add_argument("--json", type=Path, help="also write the full audit as JSON")
    args = ap.parse_args(argv)
    if not args.document.exists():
        raise SystemExit("File not found: %s" % args.document)

    text, pages = extract_text(args.document)
    result = audit(text)
    result["pages"] = pages  # type: ignore[assignment]
    print("Document : %s" % args.document.name)
    print("Pages    : %s | Words: %d | Numbered headings: %d" % (pages if pages else "n/a", result["words"], len(result["headings"])))
    if result["missing_numbers"]:
        print("Heading numbers missing from the sequence: %s" % result["missing_numbers"])
    if result["duplicate_numbers"]:
        print("Duplicate heading numbers: %s" % result["duplicate_numbers"])
    print("\nCross-references (%d): %d point at a heading that does not exist" % (len(result["references"]), len(result["unresolved_references"])))
    for r in result["unresolved_references"]:
        print("  - line %d (in section %s): 'Section %d' has no heading | %s" % (r["line"], r["in_section"], r["ref"], r["context"]))
    print("\nReferences that resolve - check the meaning matches (the heading is shown):")
    for r in result["references"]:
        if r["exists"]:
            print("  - line %d (in section %s): Section %d -> '%s' | %s" % (r["line"], r["in_section"], r["ref"], r["resolves_to"], r["context"][:90]))
    print("\nPriority contradictions (%d):" % len(result["priority_conflicts"]))
    for c in result["priority_conflicts"]:
        print("  - Section %d '%s': priority '%s' but text says '%s'" % (c["section"], c["title"], c["priority"], c["wording"]))
    if args.json:
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("\nWrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
