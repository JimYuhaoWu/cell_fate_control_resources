#!/usr/bin/env python
"""
scripts/04_build.py
-------------------
YAML records -> SQLite -> committed TSV snapshots.

Reads:
    vocab/*.yaml            controlled vocabularies
    records/*.yaml          curated entities, with nested ext/links/papers
    literature/papers.yaml  harvested open paper metadata

Writes:
    db/cfcr.db              SQLite (git-ignored)
    db/entities.tsv         committed snapshot
    db/papers.tsv           committed snapshot
    db/entity_paper.tsv     committed snapshot
    db/links.tsv            committed snapshot
    db/build_manifest.json  provenance

Usage:
    python scripts/04_build.py [--repo-root PATH] [--db PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema import CFCR, EXT_TABLES          # noqa: E402

# Keys in a record YAML block that are not `entity` columns.
NESTED_KEYS = set(EXT_TABLES.values()) | {"links", "papers"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_yaml(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data or []


def split_record(rec: dict, today: str, existing_added: dict[str, str]):
    """
    Split one curated record into its table rows.

    Returns (entity_row, ext_table_or_None, ext_row_or_None, link_rows,
    entity_paper_rows).
    """
    entity_id = rec.get("entity_id")
    etype = rec.get("type")
    if not entity_id or not etype:
        raise ValueError(f"record missing entity_id or type: {rec!r}")
    if etype not in EXT_TABLES:
        raise ValueError(
            f"{entity_id}: unknown type '{etype}'. "
            f"Known: {sorted(EXT_TABLES)}")

    entity = {k: v for k, v in rec.items() if k not in NESTED_KEYS}
    # date_added is set once and preserved across rebuilds, so the TSV snapshot
    # does not churn every build; date_updated tracks the current build.
    entity["date_added"] = existing_added.get(entity_id, today)
    entity["date_updated"] = today

    ext_table = EXT_TABLES[etype]
    ext = rec.get(ext_table)
    ext_row = None
    if ext:
        ext_row = dict(ext)
        ext_row["entity_id"] = entity_id

    links = []
    for link in rec.get("links") or []:
        row = dict(link)
        row["entity_id"] = entity_id
        links.append(row)

    eps = []
    for paper in rec.get("papers") or []:
        eps.append({
            "entity_id": entity_id,
            "paper_id": paper["paper_id"],
            "role": paper["role"],
            "note": paper.get("note"),
        })

    return entity, ext_table, ext_row, links, eps


def write_entities_tsv(db: CFCR, path: Path) -> int:
    """
    Write entity LEFT JOIN extension table, all types stacked into one frame.

    Array columns stay as the JSON text they are stored as, so the snapshot
    round-trips through cfcr.load() without a second encoding convention.
    """
    import pandas as pd

    frames = []
    for etype, ext_table in EXT_TABLES.items():
        # Name the ext columns explicitly: `x.*` would re-emit entity_id and
        # leave the frame with a duplicated column name, which pandas cannot
        # concat across types.
        ext_cols = [c for c in db._columns(ext_table) if c != "entity_id"]
        selected = ", ".join(f"x.{c}" for c in ext_cols)
        df = pd.read_sql_query(
            f"SELECT e.*{', ' + selected if selected else ''} FROM entity e "
            f"LEFT JOIN {ext_table} x USING (entity_id) WHERE e.type = ?",
            db.conn, params=(etype,))
        if not df.empty:
            frames.append(df)
    if not frames:
        path.write_text("")
        return 0
    # Reindex every frame onto the union of columns before concat. Each type's
    # frame is missing the other types' ext columns, and concat's handling of
    # all-NA columns is deprecated; doing the alignment here keeps every column
    # object-dtyped and the output stable.
    all_cols: list[str] = []
    for frame in frames:
        all_cols += [c for c in frame.columns if c not in all_cols]
    # astype(object) because reindex introduces all-NA columns for the ext
    # tables of other types, and concat's dtype inference over those is
    # deprecated. Everything is written as text anyway.
    frames = [frame.reindex(columns=all_cols).astype(object)
              for frame in frames]
    out = pd.concat(frames, ignore_index=True, sort=False)
    # Entity columns first, then each extension table's columns grouped in
    # EXT_TABLES order and sorted within the group.
    #
    # The sort is what makes the snapshot environment-independent. Column order
    # cannot come from PRAGMA table_info: ALTER TABLE ADD COLUMN appends, so a
    # database migrated through MIGRATIONS reports a different order than one
    # built fresh from the DDL, and entities.tsv would then differ between an
    # existing checkout and a clean clone with identical data -- a diff with no
    # curation change behind it.
    entity_cols = list(db._columns("entity"))
    ordered: list[str] = list(entity_cols)
    for ext_table in EXT_TABLES.values():
        cols = sorted(c for c in db._columns(ext_table)
                      if c != "entity_id" and c not in ordered)
        ordered += cols
    ordered += sorted(c for c in out.columns if c not in ordered)
    out = out[[c for c in ordered if c in out.columns]]
    out = out.sort_values("entity_id").reset_index(drop=True)
    out.to_csv(path, sep="\t", index=False, lineterminator="\n")
    return len(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=Path(__file__).resolve().parent.parent,
                    type=Path)
    ap.add_argument("--db", default=None, type=Path)
    args = ap.parse_args()

    root: Path = args.repo_root
    db_path: Path = args.db or (root / "db" / "cfcr.db")
    today = date.today().isoformat()

    vocab_files = sorted((root / "vocab").glob("*.yaml"))
    record_files = sorted((root / "records").glob("*.yaml"))
    papers_file = root / "literature" / "papers.yaml"

    if not record_files:
        print(f"error: no record files in {root / 'records'}", file=sys.stderr)
        return 1
    if not papers_file.exists():
        print(f"error: {papers_file} not found", file=sys.stderr)
        return 1

    counts: dict[str, tuple[int, int]] = {}

    with CFCR(db_path) as db:
        existing_added = {
            row["entity_id"]: row["date_added"]
            for row in db.fetch("entity")
        }

        # ── vocab ────────────────────────────────────────────────────────────
        vocab_rows = []
        for path in vocab_files:
            facet_from_name = path.stem
            for term in load_yaml(path):
                row = dict(term)
                row.setdefault("facet", facet_from_name)
                if row["facet"] != facet_from_name:
                    print(f"error: {path.name} declares facet "
                          f"'{row['facet']}' for term '{row.get('term')}'; "
                          f"file name implies '{facet_from_name}'",
                          file=sys.stderr)
                    return 1
                vocab_rows.append(row)
        counts["vocab"] = db.upsert_vocab(vocab_rows)

        # ── papers ───────────────────────────────────────────────────────────
        paper_rows = []
        for paper in load_yaml(papers_file):
            row = dict(paper)
            row["date_added"] = row.get("date_added") or today
            paper_rows.append(row)
        counts["paper"] = db.upsert_papers(paper_rows)

        # ── entities and their satellites ────────────────────────────────────
        entities, exts, links, eps = [], {}, [], []
        for path in record_files:
            for rec in load_yaml(path):
                try:
                    e, ext_table, ext_row, lrows, eprows = split_record(
                        rec, today, existing_added)
                except (ValueError, KeyError) as exc:
                    print(f"error in {path.name}: {exc}", file=sys.stderr)
                    return 1
                entities.append(e)
                if ext_row:
                    exts.setdefault(ext_table, []).append(ext_row)
                links.extend(lrows)
                eps.extend(eprows)

        counts["entity"] = db.upsert_entities(entities)
        for etype, table in EXT_TABLES.items():
            rows = exts.get(table)
            if rows:
                counts[table] = db.upsert_ext(etype, rows)
        counts["link"] = db.upsert_links(links)
        counts["entity_paper"] = db.upsert_entity_papers(eps)

        # ── snapshots ────────────────────────────────────────────────────────
        out = root / "db"
        out.mkdir(parents=True, exist_ok=True)
        written = {}
        # entities.tsv is the DENORMALIZED view: entity LEFT JOIN its own
        # extension table, all types stacked. cfcr.db is git-ignored, so this
        # snapshot is the only thing a fresh clone has -- a raw `entity` dump
        # would leave cfcr.load(type="model", evidence_tier=...) unable to
        # filter on any ext column. Columns not applicable to a type are empty,
        # and each entity is still exactly one line, so `git diff` of a
        # curation change stays readable.
        written["entities.tsv"] = write_entities_tsv(db, out / "entities.tsv")
        written["papers.tsv"] = db.to_tsv("paper", out / "papers.tsv")
        written["entity_paper.tsv"] = db.to_tsv("entity_paper",
                                                out / "entity_paper.tsv")
        written["links.tsv"] = db.to_tsv("link", out / "links.tsv")

        summary = db.counts()

        manifest = {
            "build_date": today,
            "script": "scripts/04_build.py",
            "db_path": str(db_path.relative_to(root)) if db_path.is_relative_to(root)
                       else str(db_path),
            "inputs": {
                str(p.relative_to(root)): sha256(p)
                for p in [*vocab_files, *record_files, papers_file]
            },
            "upserts": {k: {"inserted": v[0], "updated": v[1]}
                        for k, v in counts.items()},
            "snapshots": written,
            "summary": summary,
        }
        (out / "build_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", newline="")

        db.insert_provenance({
            "run_id": f"build-{today}",
            "script": "scripts/04_build.py",
            "run_date": today,
            "source_name": "records/ + vocab/ + literature/papers.yaml",
            "records_added": sum(v[0] for v in counts.values()),
            "records_updated": sum(v[1] for v in counts.values()),
            "notes": f"{summary['n_entities']} entities, "
                     f"{summary['n_papers']} papers",
        })

    print(f"built {db_path}")
    for table, (ins, upd) in counts.items():
        print(f"  {table:24} +{ins:4} ~{upd:4}")
    print(f"  entities by type        {summary['by_type']}")
    print(f"  paper roles             {summary['by_paper_role']}")
    print(f"  snapshots               {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
