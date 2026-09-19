#!/usr/bin/env python3
"""Shortlist reusable catalogue modules for each requirement (Phase 8 of odoo_requirement_gap_analysis).

An organisation's delivery profile can list a catalogue of ready-made modules (an apps
store, an internal module library, a partner catalogue). This script scores every catalogue
entry against every requirement row with a stdlib-only token-overlap score and writes a
shortlist. It is a *screening* step: a shortlisted module is only a candidate until its
manifest and models have been read and the covered share of the requirement has been
judged and tagged. Never quote a score as coverage.

Catalogue JSON (list of objects):
    {"module": "technical_name", "name": "...", "summary": "...", "description": "...",
     "versions": ["17.0", "18.0", "19.0"], "price_usd": 199, "url": "..."}
Requirements JSON (list of objects): {"id": "R-001", "title": "...", "std": "...", "gap": "..."}
The ``std`` and ``gap`` fields are optional. Scoring uses the gap text first, because the
useful question is "what is still missing after standard Odoo".

Usage:
    python3 catalog_match.py --catalog store.json --requirements reqs.json --target 19.0 \\
        --top 3 --min-score 0.08 --json shortlist.json
"""
import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

STOP = set("""a an and are as at be by for from has have in into is it its of on or that the their this to
with without via per each any all can may must should will not no yes odoo module modules feature features
support supports allow allows using use used new one more also than then when where which who""".split())
TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text: str):
    out = []
    for t in TOKEN.findall((text or "").lower()):
        if len(t) < 3 or t in STOP:
            continue
        out.append(t[:-1] if t.endswith("s") and len(t) > 4 else t)
    return out


def build_idf(docs):
    df = Counter()
    for d in docs:
        df.update(set(d))
    n = max(len(docs), 1)
    return {t: math.log((n + 1) / (c + 0.5)) for t, c in df.items()}


def score(req_tokens, cat_tokens, idf):
    """IDF-weighted overlap coefficient in [0, 1]."""
    if not req_tokens or not cat_tokens:
        return 0.0, []
    rs, cs = set(req_tokens), set(cat_tokens)
    shared = rs & cs
    if not shared:
        return 0.0, []
    num = sum(idf.get(t, 0.0) for t in shared)
    den = min(sum(idf.get(t, 0.0) for t in rs), sum(idf.get(t, 0.0) for t in cs)) or 1.0
    return num / den, sorted(shared, key=lambda t: -idf.get(t, 0.0))[:8]


def port_status(versions, target):
    """ready = published for the target version; port = only older versions exist; none = unknown."""
    vs = sorted(set(versions or []), key=lambda v: float(v) if re.match(r"^\d+(\.\d+)?$", str(v)) else 0)
    if not vs:
        return "unknown", None
    if target in vs:
        return "ready", target
    older = [v for v in vs if re.match(r"^\d+(\.\d+)?$", str(v)) and float(v) < float(target)]
    return ("port", older[-1]) if older else ("unknown", None)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--requirements", type=Path, required=True)
    ap.add_argument("--target", default="19.0", help="Odoo version the project targets (default 19.0)")
    ap.add_argument("--top", type=int, default=3, help="candidates kept per requirement")
    ap.add_argument("--min-score", type=float, default=0.08)
    ap.add_argument("--max-gap", type=float, default=3.0,
                    help="drop modules whose newest version is more than this many major versions behind --target (default 3)")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    reqs = json.loads(args.requirements.read_text(encoding="utf-8"))
    cat_tokens = [tokens(" ".join([c.get("module", "").replace("_", " "), c.get("name", ""), c.get("summary", ""), c.get("description", "")])) for c in catalog]
    req_tokens = [tokens(" ".join([r.get("title", ""), r.get("gap", "") or "", r.get("gap", "") or "", r.get("std", "") or ""])) for r in reqs]
    idf = build_idf(cat_tokens + req_tokens)

    shortlist = []
    for r, rt in zip(reqs, req_tokens):
        scored = []
        for c, ct in zip(catalog, cat_tokens):
            s, shared = score(rt, ct, idf)
            if s >= args.min_score:
                status, source = port_status(c.get("versions"), args.target)
                if status == "port" and float(args.target) - float(source) > args.max_gap:
                    continue
                scored.append(dict(module=c["module"], score=round(s, 3), shared_terms=shared, target_status=status,
                                   source_version=source, versions=c.get("versions"), price_usd=c.get("price_usd")))
        scored.sort(key=lambda x: -x["score"])
        if scored:
            shortlist.append(dict(requirement=r["id"], title=r.get("title", "")[:110], candidates=scored[:args.top]))

    print("%d requirements screened against %d catalogue entries; %d have candidates" % (len(reqs), len(catalog), len(shortlist)))
    for row in shortlist:
        print("\n%s  %s" % (row["requirement"], row["title"]))
        for c in row["candidates"]:
            print("   %.3f  %-42s [%s%s]  shared: %s" % (c["score"], c["module"], c["target_status"],
                                                        (" from " + c["source_version"]) if c["target_status"] == "port" else "", ", ".join(c["shared_terms"][:5])))
    if args.json:
        args.json.write_text(json.dumps(shortlist, indent=2), encoding="utf-8")
        print("\nWrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
