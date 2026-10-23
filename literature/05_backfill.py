#!/usr/bin/env python
"""
literature/05_backfill.py
-------------------------
Record a resource CFCR already decided to carry. Reads `literature/backfill.yaml`,
resolves each entry's primary paper against Europe PMC or arXiv, and writes a
draft record plus that paper into the catalogue.

This is the opposite job from `01_search.py`/`02_triage.py`. Those find
resources nobody has named yet, and route the inclusion call to a human.
A backfill entry has already been included -- `ROADMAP.md` M4 names its
resources one by one -- so there is no scope question left to ask, only
bibliography to fetch. Nothing here scores anything.

What it writes, and what it deliberately leaves blank:

    name, type, fate_axis       from backfill.yaml, because all three are
                                curation calls and no API supplies them
    year, the primary paper     fetched
    review_state: unreviewed    so `07_export_site.py` holds the record off
                                the site until a human fills in the rest
    everything else             absent, not null. `license`,
                                `availability_tier`, `n_parameters_*`,
                                `input_context_bp` and `notes` are read off a
                                repository, a model card or the paper's
                                methods; guessing them is how a catalogue
                                starts publishing claims nobody checked.

An entry resolves by DOI (`10.…`), by arXiv id (`arxiv:2306.15794`), or by
title. A title match must agree with the title that comes back once
punctuation and case are set aside, or the entry is reported and skipped:
admitting the wrong paper under a right name is worse than admitting nothing.

Run from project root (needs the [literature] extra and network):
    python literature/05_backfill.py [--file literature/backfill.yaml]
                                     [--curator NAME] [--dry-run]
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BACKFILL_YAML = ROOT / "literature" / "backfill.yaml"


def _module(filename: str, name: str):
    """
    `01_search.py` and `03_record.py` start with a digit, so neither is a legal
    module name and neither can be imported by `import`. Loading them by path
    is still better than a third copy of the HTTP layer or a second copy of the
    YAML writers -- both are curated-file formats that must not drift.
    """
    spec = importlib.util.spec_from_file_location(name, ROOT / "literature" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


search = _module("01_search.py", "cfcr_search")
record = _module("03_record.py", "cfcr_record")

DOI = re.compile(r"^10\.\d{4,9}/")


def normalise(title: str) -> str:
    """Titles for comparison only: case, punctuation and spacing set aside."""
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def fetch_arxiv(arxiv_id: str) -> dict | None:
    """
    One paper by id. `search_arxiv` takes a search query rather than an id, and
    widening its signature would change a function the discovery run depends
    on, so this asks the same endpoint for `id_list` and reads the same three
    Atom fields.
    """
    root = search._get(search.ARXIV, {"id_list": arxiv_id}, parse="xml")
    entry = root.find("a:entry", search.ATOM)
    if entry is None:
        return None
    published = entry.findtext("a:published", default="", namespaces=search.ATOM)[:4]
    return {
        "paper_id": "arxiv:" + arxiv_id,
        "doi": None,
        "title": " ".join(entry.findtext("a:title", "", search.ATOM).split()),
        "abstract": " ".join(entry.findtext("a:summary", "", search.ATOM).split()) or None,
        "authors": [" ".join(a.findtext("a:name", "", search.ATOM).split())
                    for a in entry.findall("a:author", search.ATOM)] or None,
        "year": int(published) if published.isdigit() else None,
        "venue": "arXiv",
        "venue_type": "preprint",
        "metadata_source": "arxiv",
    }


def fetch_europepmc(query: str) -> list[dict]:
    """Europe PMC's own fields, via the discovery fetcher's `resultType=core`."""
    hits = search.search_europepmc(query, 1900, 10)
    for hit in hits:
        hit["metadata_source"] = "europepmc"
    return hits


def resolve(entry: dict) -> tuple[dict | None, str | None]:
    """(paper, why-not). One of three lookups, chosen by how the entry reads."""
    ident = str(entry["paper"]).strip()

    if ident.startswith("arxiv:"):
        paper = fetch_arxiv(ident.split(":", 1)[1])
        return (paper, None) if paper else (None, f"arXiv has no {ident}")

    if DOI.match(ident):
        hits = fetch_europepmc(f'DOI:"{ident}"')
        if not hits:
            return None, f"Europe PMC has no record for {ident}"
        return hits[0], None

    hits = fetch_europepmc(f'TITLE:"{ident}"')
    if not hits:
        return None, f"no Europe PMC hit for the title {ident!r}"
    wanted = normalise(ident)
    exact = [h for h in hits if normalise(h["title"]) == wanted]
    if not exact:
        return None, (f"nothing titled {ident!r}; closest was "
                      f"{hits[0]['title']!r}. Give a DOI or an arxiv: id")
    if not exact[0].get("paper_id"):
        return None, (f"{ident!r} resolved to a Europe PMC record with no DOI "
                      f"({exact[0].get('europepmc_id')}); give an arxiv: id")
    return exact[0], None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(BACKFILL_YAML))
    parser.add_argument("--curator")
    parser.add_argument("--dry-run", action="store_true",
                        help="resolve every entry and report, writing nothing")
    args = parser.parse_args()

    entries = yaml.safe_load(Path(args.file).read_text(encoding="utf-8")) or []
    homes, _, _ = record.read_records()
    known_papers = record.read_papers()
    curator = args.curator or record.default_curator(homes)
    today = date.today().isoformat()

    new_records: dict[str, list[dict]] = {}
    new_papers: list[dict] = []
    seen: set[str] = set()
    skipped, failed = [], []

    for entry in entries:
        for field in ("name", "type", "paper"):
            if not entry.get(field):
                failed.append(f"{entry.get('name') or entry}: no `{field}`")
                break
        else:
            etype = entry["type"]
            if etype not in record.RECORD_FILES:
                failed.append(f"{entry['name']}: `{etype}` is not an entity type")
                continue
            entity_id = f"{etype}:{record.slugify(entry['name'])}"
            if entity_id in homes or entity_id in seen:
                skipped.append(f"{entity_id} is already in the catalogue")
                continue

            paper, why_not = resolve(entry)
            if why_not:
                failed.append(f"{entry['name']}: {why_not}")
                continue

            print(f"  {entity_id:40s} {paper['paper_id']}")
            seen.add(entity_id)
            if paper["paper_id"] not in known_papers:
                known_papers.add(paper["paper_id"])
                new_papers.append(dict(paper, url=paper.get("url"),
                                       date_added=today))
            new_records.setdefault(record.RECORD_FILES[etype], []).append({
                "entity_id": entity_id,
                "type": etype,
                "name": entry["name"],
                "year": paper.get("year"),
                "fate_axis": entry.get("fate_axis"),
                "review_state": "unreviewed",
                "curator": curator,
                "date_added": today,
                "date_updated": today,
                "papers": [{"paper_id": paper["paper_id"], "role": "primary"}],
            })

    for line in skipped:
        print(f"  skipped: {line}")
    for line in failed:
        print(f"  unresolved: {line}", file=sys.stderr)

    total = sum(len(v) for v in new_records.values())
    if args.dry_run:
        print(f"dry run: {total} record(s) and {len(new_papers)} paper(s) "
              f"would be written")
        return 1 if failed else 0

    for filename, recs in sorted(new_records.items()):
        record.append_blocks(ROOT / "records" / filename,
                             [record.record_entry(r) for r in recs])
    if new_papers:
        record.append_blocks(record.PAPERS_YAML,
                             [record.paper_entry(p) for p in new_papers])

    print(f"  new records           {total}")
    print(f"  new papers            {len(new_papers)}")
    if total:
        print("next: python scripts/04_build.py && python scripts/05_validate.py")
        print("      new records are `unreviewed`, so 07_export_site.py holds "
              "them off the site until a human fills in the rest")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
