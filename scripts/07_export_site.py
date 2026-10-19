#!/usr/bin/env python
"""
scripts/07_export_site.py
-------------------------
Committed TSV snapshots -> flat JSON for the static site (schema §7).

Reads the catalogue through the `cfcr` package, not SQLite: `db/cfcr.db` is
git-ignored, so the TSVs are what a fresh clone and CI actually have.

Writes:
    site/data/entities.json   one object per entity, papers inlined
    site/data/facets.json     cfcr.facets() verbatim -- the UI builds its
                              filter panel from this rather than hardcoding it
    site/data/papers.json     one object per paper, citing entities inlined

JSON array columns come out as real arrays, not the stored JSON-in-TEXT
strings; the loader has already decoded them.

Usage:
    python scripts/07_export_site.py [--repo-root PATH] [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cfcr                                   # noqa: E402

# Evidence trails read in this order, not alphabetically: the primary paper
# first, then the evaluations that determine evidence_tier.
PAPER_ROLE_ORDER = ("primary", "preprint", "benchmark", "critique",
                    "application", "extension", "review")


def _clean(value):
    """Drop NaN/empty, leave everything else as the loader decoded it."""
    if isinstance(value, float):
        if math.isnan(value):
            return None
        # Counts arrive as floats from pandas' nullable coercion; bp and
        # parameter counts should not render as "1000000.0".
        if value.is_integer():
            return int(value)
    if isinstance(value, list):
        return value or None
    if value is None or value == "":
        return None
    if hasattr(value, "item"):              # numpy scalar -> JSON-able
        value = value.item()
    return value


def _paper_url(paper_id: str, doi, url):
    """
    Resolution order for the one outbound link per paper. `doi` is the
    identifier QC verifies, so it wins; `papers.tsv.url` is a fallback and for
    the two arXiv-only records it is a doi.org URL built from an arXiv ID,
    which does not resolve. Those are sent to arxiv.org instead.
    """
    if doi:
        return f"https://doi.org/{doi}"
    if paper_id.startswith("arxiv:"):
        return f"https://arxiv.org/abs/{paper_id.removeprefix('arxiv:')}"
    return url


def _role_key(role) -> tuple:
    order = (PAPER_ROLE_ORDER.index(role)
             if role in PAPER_ROLE_ORDER else len(PAPER_ROLE_ORDER))
    return (order, str(role))


def export_entities(joins) -> list[dict]:
    """Flat, denormalized entity records with their full evidence trail."""
    papers_by_entity: dict[str, list[dict]] = {}
    for row in joins:
        papers_by_entity.setdefault(row["entity_id"], []).append(row)

    out = []
    for record in cfcr.load().to_dict("records"):
        entity = {}
        for column, value in record.items():
            if column == "papers":
                continue
            cleaned = _clean(value)
            if cleaned is not None:
                entity[column] = cleaned

        trail = sorted(papers_by_entity.get(record["entity_id"], []),
                       key=lambda r: _role_key(r["role"]))
        entity["papers"] = [{
            "paper_id": p["paper_id"],
            "role": p["role"],
            "title": p["title"],
            "authors": p["authors"],
            "year": p["year"],
            "venue": p["venue"],
            "doi": p["doi"],
            "url": p["url"],
            "note": p["note"],
        } for p in trail]
        primary = next((p for p in trail if p["role"] == "primary"), None)
        if primary:
            entity["primary_paper_id"] = primary["paper_id"]
            entity["primary_paper_title"] = primary["title"]
        out.append(entity)
    return out


def export_papers(joins) -> list[dict]:
    """
    One object per paper, with the entities that cite it and in what role.

    Papers attached to no entity are absent -- the site has nowhere to show
    them, and 05_validate.py already reports them as orphans.
    """
    by_paper: dict[str, dict] = {}
    for row in joins:
        paper = by_paper.setdefault(row["paper_id"], {
            "paper_id": row["paper_id"],
            "doi": row["doi"],
            "title": row["title"],
            "authors": row["authors"],
            "year": row["year"],
            "venue": row["venue"],
            "venue_type": row["venue_type"],
            "abstract": row["abstract"],
            "url": row["url"],
            "preprint_of": row["preprint_of"],
            "entities": [],
        })
        paper["entities"].append({
            "entity_id": row["entity_id"],
            "role": row["role"],
            "note": row["note"],
        })
    for paper in by_paper.values():
        paper["entities"].sort(key=lambda e: _role_key(e["role"]))
    return sorted(by_paper.values(), key=lambda p: p["paper_id"])


def read_joins() -> list[dict]:
    """Every entity_paper join, merged with paper metadata, NaN stripped."""
    rows = []
    for row in cfcr.load_papers().to_dict("records"):
        row = {k: _clean(v) for k, v in row.items()}
        row["url"] = _paper_url(row["paper_id"], row["doi"], row["url"])
        rows.append(row)
    return rows


def write_json(path: Path, payload) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys + trailing newline so re-running on unchanged records is a
    # no-op in `git diff`.
    path.write_text(json.dumps(payload, indent=1, sort_keys=True,
                               ensure_ascii=False) + "\n", encoding="utf-8",
                    newline="")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--out", type=Path, default=None,
                        help="output directory (default: <repo-root>/site/data)")
    args = parser.parse_args()

    out_dir = args.out or args.repo_root / "site" / "data"

    joins = read_joins()
    entities = export_entities(joins)
    papers = export_papers(joins)
    facets = cfcr.facets()

    written = [
        write_json(out_dir / "entities.json", entities),
        write_json(out_dir / "facets.json", facets),
        write_json(out_dir / "papers.json", papers),
    ]

    print(f"exported {len(entities)} entities, {len(papers)} papers, "
          f"{len(facets)} facets")
    for path in written:
        print(f"  {path.relative_to(args.repo_root)}"
              f"  {path.stat().st_size / 1024:.1f} KiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
