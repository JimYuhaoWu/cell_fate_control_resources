"""
cfcr
----
Reader API for the Cell Fate Control Resources catalogue (schema §8).

The loader hides the schema: callers get flat pandas DataFrames with papers
denormalized, and never see the entity/ext/join split.

    from cfcr import load, load_papers

    load(type="model")
    load(type="model", organism="mouse", assay="ATAC-seq")
    load(type="model", fate_axis="where", availability_tier="open-weights")
    load(type="model", evidence_tier="externally-benchmarked")
    load(type="protocol", validation_tier="published-peer-reviewed")
    load_papers("model:borzoi", role="critique")

Data source
-----------
Reads the committed TSV snapshots in `db/` -- the same files `git diff` shows
on a curation change. `db/cfcr.db` is git-ignored, so the TSVs are what a fresh
clone actually has; they are the source of truth for readers, and SQLite is a
build artifact.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

__all__ = ["load", "load_papers", "facets", "ENTITY_TYPES"]

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DB_DIR = _REPO_ROOT / "db"

ENTITY_TYPES = ("model", "benchmark", "dataset", "module", "protocol", "database")

# Columns stored as JSON arrays. Filtering one of these tests membership;
# filtering anything else tests equality.
_ARRAY_COLUMNS = frozenset({
    "aliases", "tags", "fate_axis", "organism", "cell_type", "assay", "task",
    "architecture", "output_type", "genome_build", "training_data",
    "benchmarked_on", "task_categories", "evaluation_mode", "modality",
    "accession", "module_types", "organism_scope", "category", "key_reagents",
    "authors",
})


def _read_tsv(name: str) -> pd.DataFrame:
    path = _DB_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"{name} not found at {path}.\n"
            f"Run `python scripts/04_build.py` to build the snapshots from "
            f"records/ and literature/papers.yaml.")
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                     na_values=[""])
    for col in _ARRAY_COLUMNS & set(df.columns):
        df[col] = df[col].map(_decode)
    return df


def _decode(value: Any) -> list:
    if not isinstance(value, str) or not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [value]
    return parsed if isinstance(parsed, list) else [parsed]


def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for col in ("year", "input_context_bp", "output_resolution_bp",
                "n_parameters_min", "n_parameters_max", "n_tasks",
                "n_models_evaluated", "n_records", "duration_hours"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _matches(series: pd.Series, column: str, wanted: Any) -> pd.Series:
    """Membership test for array columns, equality otherwise."""
    if column in _ARRAY_COLUMNS:
        wanted_set = {wanted} if isinstance(wanted, str) else set(wanted)
        return series.map(lambda cell: bool(wanted_set & set(cell or [])))
    if isinstance(wanted, (list, tuple, set)):
        return series.isin(list(wanted))
    return series == wanted


def load(type: str | None = None, *, with_papers: bool = True,
         **filters: Any) -> pd.DataFrame:
    """
    Return catalogue entities as a flat DataFrame.

    Parameters
    ----------
    type
        One of `cfcr.ENTITY_TYPES`. Omit for every type, in which case columns
        belonging to a single type's extension table are mostly empty.
    with_papers
        Attach a `papers` column (list of dicts: paper_id, role, title, year,
        doi, note) plus `primary_paper_id` and `primary_paper_title`.
    **filters
        Column equality, or membership for list-valued columns. A value may be
        a list to mean "any of". Unknown column names raise ValueError listing
        what is available.

    Examples
    --------
    >>> load(type="model", evidence_tier="externally-benchmarked")
    >>> load(type="model", fate_axis="where", organism="mouse")
    """
    df = _read_tsv("entities.tsv")

    if type is not None:
        if type not in ENTITY_TYPES:
            raise ValueError(
                f"type must be one of {ENTITY_TYPES}; got {type!r}")
        df = df[df["type"] == type].copy()

    for column, wanted in filters.items():
        if column not in df.columns:
            raise ValueError(
                f"unknown filter column {column!r}.\n"
                f"available: {', '.join(sorted(df.columns))}")
        df = df[_matches(df[column], column, wanted)]

    # Drop columns that are entirely empty for the selected rows. Loading one
    # type otherwise returns every other type's extension columns as blanks.
    df = df.dropna(axis=1, how="all")
    df = _coerce_numeric(df).reset_index(drop=True)

    if with_papers:
        df = _attach_papers(df)
    return df


def _attach_papers(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["papers"] = []
        df["primary_paper_id"] = None
        df["primary_paper_title"] = None
        return df

    joins = _read_tsv("entity_paper.tsv")
    papers = _read_tsv("papers.tsv").set_index("paper_id")

    by_entity: dict[str, list[dict]] = {}
    for row in joins.itertuples(index=False):
        meta = (papers.loc[row.paper_id].to_dict()
                if row.paper_id in papers.index else {})
        by_entity.setdefault(row.entity_id, []).append({
            "paper_id": row.paper_id,
            "role": row.role,
            "title": meta.get("title"),
            "year": meta.get("year"),
            "doi": meta.get("doi"),
            "note": getattr(row, "note", None),
        })

    df["papers"] = df["entity_id"].map(lambda e: by_entity.get(e, []))
    primary = df["papers"].map(
        lambda ps: next((p for p in ps if p["role"] == "primary"), None))
    df["primary_paper_id"] = primary.map(lambda p: p and p["paper_id"])
    df["primary_paper_title"] = primary.map(lambda p: p and p["title"])
    return df


def load_papers(entity_id: str | None = None, *, role: str | None = None
                ) -> pd.DataFrame:
    """
    Return papers, optionally restricted to one entity and/or one role.

    With no arguments, returns every paper in the catalogue with its attached
    entities and roles.

    >>> load_papers("model:borzoi", role="critique")
    """
    joins = _read_tsv("entity_paper.tsv")
    papers = _read_tsv("papers.tsv")

    if entity_id is not None:
        joins = joins[joins["entity_id"] == entity_id]
        if joins.empty:
            known = set(_read_tsv("entities.tsv")["entity_id"])
            if entity_id not in known:
                raise ValueError(
                    f"unknown entity_id {entity_id!r}. "
                    f"Use load() to list entities.")
    if role is not None:
        joins = joins[joins["role"] == role]

    out = joins.merge(papers, on="paper_id", how="left")
    return _coerce_numeric(out).reset_index(drop=True)


def facets(type: str | None = None) -> dict[str, list]:
    """
    Distinct values available for each filterable column, for building a UI or
    for finding out what a filter accepts.
    """
    df = load(type=type, with_papers=False)
    out: dict[str, list] = {}
    for column in df.columns:
        if column in ("entity_id", "name", "description", "notes"):
            continue
        if column in _ARRAY_COLUMNS:
            values = {v for cell in df[column] for v in (cell or [])}
        else:
            values = {v for v in df[column].dropna().tolist()}
        if values and len(values) <= 60:
            out[column] = sorted(values, key=str)
    return out
