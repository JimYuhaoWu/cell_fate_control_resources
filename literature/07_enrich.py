#!/usr/bin/env python
"""
literature/07_enrich.py
-----------------------
Fill the two fields on a staged record that can be read off a primary source
rather than judged: the code repository, and the licence on it.

A record written by `03_record.py` or `05_backfill.py` is bibliography only --
name, type, year, axis, primary paper. Promoting one publishes a card that says
"no licence stated", and whether a resource's weights can legally be reused is
half of what CFCR claims to be for. This script closes that gap where a machine
honestly can.

    links            the repository URL printed in the primary abstract
    <type>_ext       `license`, read from that repository's own LICENSE file
                     via the GitHub API

Both are facts with a source. Nothing else here is, and the difference is the
whole design:

  `availability_tier` is **proposed and not written.** Its three values turn on
  what was released -- code, weights, or an endpoint -- and a repository licence
  does not say which. model:alphagenome is `api-only` with no repository at
  all. A proposal goes in the report for a human to confirm at promotion.

  `tags` are **not generated at all.** `reports/vocab_candidates.md` promotes a
  tag to vocabulary once ten records carry it, so the signal is a curator
  choosing the same word again. A tagger filling that column would make the
  vocabulary mechanism measure the tagger, which is the argument that already
  decided evidence_tier: derive what has a derivation, route the rest.

  `description` is writing, not lookup, and is left alone.

An existing value is never overwritten; only an absent field is filled.

Needs `gh` authenticated (`gh auth status`) -- it is called as a subprocess so
no token passes through this script. Unauthenticated the API allows 60 requests
an hour, which is not enough for a staging area this size.

Run from project root:
    python literature/07_enrich.py [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RECORDS_DIR = ROOT / "records"
PAPERS_YAML = ROOT / "literature" / "papers.yaml"

EXT_BLOCK = {
    "model": "model_ext",
    "benchmark": "benchmark_ext",
    "dataset": "dataset_ext",
    "module": "module_collection_ext",
    "protocol": "protocol_ext",
    "database": "database_ext",
}

# Only two of the six ext tables have a `license` column (scripts/schema.py),
# so a benchmark's or a database's licence has nowhere in the schema to live
# and QC rejects the record outright. Everything else gets `links` alone.
LICENSED_TYPES = ("model", "dataset")

# Trailing punctuation is part of the sentence, not of the URL: abstracts end
# these with ". " or " ." and one run put a full stop inside six repo names.
REPO_URL = re.compile(
    r"https?://(?:www\.)?github\.com/([A-Za-z0-9][\w.-]*)/([\w.-]+?)(?=[\s,;)\]]|\.$|$)",
    re.I)


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def gh_repo(owner: str, name: str) -> dict | None:
    """{license, archived, html_url} for a repository, or None if it is gone."""
    proc = subprocess.run(
        ["gh", "api", f"repos/{owner}/{name}", "--jq",
         "{license: .license.spdx_id, archived: .archived, url: .html_url}"],
        capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def propose_tier(repo: dict) -> str:
    """
    A proposal for a human, never a written value. A repository with an OSI
    licence is the open-source case; anything else needs someone to look at
    what the release actually contains.
    """
    spdx = repo.get("license")
    if spdx and spdx not in ("NOASSERTION", "none"):
        return "open-source"
    return "needs a look -- no licence on the repository"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode:
        raise SystemExit("gh is not authenticated; run `gh auth login`")

    papers = {p["paper_id"]: p for p
              in yaml.safe_load(PAPERS_YAML.read_text(encoding="utf-8")) or []}

    found, enriched, no_url, gone = 0, 0, 0, []
    proposals: list[str] = []

    for path in sorted(RECORDS_DIR.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        records = yaml.safe_load(text) or []
        lines = text.split("\n")
        changed = False

        for rec in records:
            if rec.get("review_state") != "unreviewed":
                continue
            ext = EXT_BLOCK[rec["type"]]
            if rec.get("links") and (rec.get(ext) or {}).get("license"):
                continue
            if args.limit and found >= args.limit:
                break

            primary = next((p["paper_id"] for p in rec.get("papers") or []
                            if p["role"] == "primary"), None)
            abstract = (papers.get(primary) or {}).get("abstract") or ""
            m = REPO_URL.search(abstract)
            if not m:
                no_url += 1
                continue
            found += 1
            owner, name = m.group(1), m.group(2).rstrip(".")
            repo = gh_repo(owner, name)
            if not repo:
                gone.append(f"{rec['entity_id']}: {owner}/{name} is not reachable")
                continue

            new = []
            if not rec.get("links"):
                new += ["  links:", "    - kind: code",
                        f"      url: {json.dumps(repo['url'], ensure_ascii=False)}"]
            spdx = repo.get("license")
            if spdx and spdx not in ("NOASSERTION", "none") \
                    and rec["type"] in LICENSED_TYPES \
                    and not (rec.get(ext) or {}).get("license"):
                new += [f"  {ext}:", f"    license: {spdx}"]
            if not new:
                continue

            print(f"  {rec['entity_id'][:58]:58s} {spdx or '-':14s} "
                  f"{owner}/{name}")
            proposals.append(f"{rec['entity_id']}\t{propose_tier(repo)}"
                             + ("\tarchived" if repo.get("archived") else ""))
            enriched += 1
            if args.dry_run:
                continue

            start = lines.index(f"- entity_id: {rec['entity_id']}")
            end = next((i for i in range(start + 1, len(lines))
                        if lines[i].startswith("- ")), len(lines))
            # Inserted before `papers:`, which 03_record.py and 05_backfill.py
            # both write last, so the record keeps the shape a curated one has.
            at = next((i for i in range(start, end)
                       if lines[i] == "  papers:"), end)
            lines[at:at] = new
            changed = True

        if changed and not args.dry_run:
            path.write_text("\n".join(lines), encoding="utf-8", newline="")

    for line in gone:
        print(f"  unreachable: {line}", file=sys.stderr)

    print(f"\n  abstracts with a repository URL   {found}")
    print(f"  records enriched                  {enriched}")
    print(f"  no URL in the abstract            {no_url}")
    print(f"  repository unreachable            {len(gone)}")

    if proposals and not args.dry_run:
        out = ROOT / "reports" / "availability_proposals.tsv"
        out.write_text("entity_id\tproposed_availability_tier\tnote\n"
                       + "\n".join(proposals) + "\n",
                       encoding="utf-8", newline="")
        print(f"  wrote {_rel(out)} -- proposals, for a human to confirm")
    if enriched:
        print("next: python scripts/04_build.py && python scripts/05_validate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
