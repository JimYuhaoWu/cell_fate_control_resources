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

    links            the repository URL, from the primary abstract where it is
                     printed and otherwise from the open-access full text
    <type>_ext       `license`, read from that repository's own LICENSE file
                     via the GitHub API

The abstract is a thin source: 397 of 452 staged records print no GitHub URL in
one. The full text is where a paper actually states its code availability, so
it is read when the abstract has nothing -- **read for the URL and never
stored**, which keeps `literature/papers.yaml` to publisher-released abstracts
as the standing rule requires. Only the Europe PMC open-access subset is
fetched; nothing paywalled is requested at all. Preprints are not covered,
measured rather than assumed: Europe PMC indexes them but serves no full text
for them, 404 on every one tried, and 124 of the link-less records are
preprints.

A paper naming more than one repository is left for a human. The second one is
as often a dataset it compares against as a second home for its own code, and
a card that links the wrong repository is worse than a card that links none.

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


search = None          # literature/01_search.py, loaded on first full-text use


def _search_module():
    """
    01_search.py holds the retrying `_get` and the one User-Agent built from
    config/sources.yaml. Loaded lazily so a run that finds every URL in the
    abstracts opens no Europe PMC connection at all.
    """
    global search
    if search is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cfcr_search", ROOT / "literature" / "01_search.py")
        search = importlib.util.module_from_spec(spec)
        sys.modules["cfcr_search"] = search
        spec.loader.exec_module(search)
    return search


def open_access(doi: str) -> str | None:
    """
    The PMCID for a DOI Europe PMC holds open-access, or None.

    The PMCID and not the record's own `id`: `fullTextXML` is served under the
    PMC identifier, and asking for it under MED/<id> 404s even when the article
    is in the open-access subset.
    """
    s = _search_module()
    data = s._get(s.EUROPEPMC, {"query": f'DOI:"{doi}"', "format": "json",
                                "resultType": "core", "pageSize": 1})
    hit = (data.get("resultList", {}).get("result") or [None])[0]
    if not hit or hit.get("isOpenAccess") != "Y":
        return None
    return hit.get("pmcid")


def full_text_repos(pmcid: str) -> list[str]:
    """
    Distinct `owner/name` repositories named anywhere in the full text.

    The XML is walked for element text and for the xlink:href on <ext-link>,
    because a code availability statement puts the URL in either. Nothing from
    the document is kept beyond the repository names.
    """
    s = _search_module()
    try:
        root = s._get(f"{s.EUROPEPMC.rsplit('/', 1)[0]}/{pmcid}/fullTextXML",
                      {}, parse="xml")
    except s.FetchError:
        # Open-access in the search index does not guarantee a full text to
        # serve, and a missing one is an absence rather than a failed run.
        return []
    found: list[str] = []
    for node in root.iter():
        for blob in [node.text or ""] + [v for v in node.attrib.values()]:
            for m in REPO_URL.finditer(blob):
                name = f"{m.group(1)}/{m.group(2).rstrip('.')}"
                if name not in found:
                    found.append(name)
    return found


def merge_tsv(out: Path, header: str, rows: list[str]) -> int:
    """
    Add rows to a report, keyed on the entity_id in the first column.

    Each run only looks at records that are still missing something, so writing
    the file fresh dropped every row an earlier run had put there: the first
    enrichment left 54 availability proposals and the next run cut the file to
    5. A row for the same entity is replaced, because the newer look at it is
    the better one.
    """
    merged: dict[str, str] = {}
    if out.exists():
        for line in out.read_text(encoding="utf-8").split("\n")[1:]:
            if line.strip():
                merged[line.split("\t", 1)[0]] = line
    for row in rows:
        merged[row.split("\t", 1)[0]] = row
    out.write_text(header + "\n" + "\n".join(v for _, v in sorted(merged.items()))
                   + "\n", encoding="utf-8", newline="")
    return len(merged)


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
    ambiguous: list[str] = []
    from_full_text = 0
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
            if m:
                owner, name = m.group(1), m.group(2).rstrip(".")
                source_of = "abstract"
            else:
                where = (None if not primary or primary.startswith("arxiv:")
                         else open_access(primary))
                repos = full_text_repos(where) if where else []
                if len(repos) != 1:
                    no_url += 1
                    if len(repos) > 1:
                        ambiguous.append(f"{rec['entity_id']}: names "
                                         f"{len(repos)} repositories "
                                         f"({', '.join(repos[:3])})")
                    continue
                owner, name = repos[0].split("/", 1)
                source_of = "full text"
            found += 1
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

            print(f"  {rec['entity_id'][:52]:52s} {source_of:10s} "
                  f"{spdx or '-':14s} {owner}/{name}")
            from_full_text += source_of == "full text"
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

    for line in ambiguous:
        print(f"  ambiguous: {line}", file=sys.stderr)
    if ambiguous and not args.dry_run:
        # Written down rather than left in a log: these are records where a
        # repository was found and only the choice between several is missing,
        # which is a minute of a human's time each and otherwise has to be
        # rediscovered by fetching every full text again.
        out = ROOT / "reports" / "repo_candidates.tsv"
        rows = [line.replace(": names ", "\t", 1) for line in ambiguous]
        total = merge_tsv(out, "entity_id\trepositories_named_in_the_full_text",
                          rows)
        print(f"  wrote {_rel(out)} -- {total} repository choice(s), for a human")
    for line in gone:
        print(f"  unreachable: {line}", file=sys.stderr)

    print(f"\n  records with a repository URL     {found}")
    print(f"  records enriched                  {enriched}")
    print(f"  no repository URL found           {no_url}")
    print(f"  repository unreachable            {len(gone)}")
    print(f"  of those, found in the full text  {from_full_text}")
    print(f"  left alone, several repositories  {len(ambiguous)}")

    if proposals and not args.dry_run:
        out = ROOT / "reports" / "availability_proposals.tsv"
        total = merge_tsv(out, "entity_id\tproposed_availability_tier\tnote",
                          proposals)
        print(f"  wrote {_rel(out)} -- {total} proposal(s), for a human to confirm")
    if enriched:
        print("next: python scripts/04_build.py && python scripts/05_validate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
