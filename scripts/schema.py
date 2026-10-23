"""
scripts/schema.py
-----------------
SQLite schema for Cell Fate Control Resources (CFCR) and the `CFCR`
context-manager class for read/write access.

Mirrors the `ModuleLibrary` pattern in JimYuhaoWu/eCR_mod_lib: context manager,
idempotent `_create_schema()`, partial-column upserts, provenance writes,
DataFrame reads, TSV export.

Schema overview
---------------
  entity                  - the spine; one row per catalogued artifact
  paper                   - open metadata only (Crossref / Europe PMC / bioRxiv)
  entity_paper            - the many-to-many join, carrying `role`
  link                    - resources hanging off entities
  vocab                   - materialized from vocab/*.yaml
  model_ext               - 1:1 extensions, one table per entity type
  benchmark_ext
  dataset_ext
  module_collection_ext
  protocol_ext
  database_ext
  provenance              - one row per script run that wrote records

List-valued columns
-------------------
Stored as JSON arrays in TEXT columns (SQLite has no array type). `encode_row`
and `decode_row` convert at the boundary, so callers always hand in and receive
Python lists. JSON rather than a delimiter because `tags`, `description`-adjacent
free text and author names may contain any separator we would pick, and because
json1 lets QC query inside the arrays:

    SELECT entity_id FROM entity, json_each(entity.fate_axis)
    WHERE json_each.value = 'where';

Usage
-----
    from schema import CFCR

    with CFCR("db/cfcr.db") as db:
        db.upsert_entities(records)       # list[dict]
        db.upsert_ext("model", exts)
        df = db.to_dataframe("model")
"""

from __future__ import annotations

import json
import re
import unicodedata
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pandas as pd


# ── enums ────────────────────────────────────────────────────────────────────
# Kept as Python constants so DDL, the loader and 05_validate.py read enum
# membership from one place rather than three.

ENTITY_TYPES = ("model", "benchmark", "dataset", "module", "protocol", "database")
FATE_AXES = ("where", "what", "how", "with-what")
ENTITY_STATUS = ("active", "deprecated", "superseded", "unmaintained")

# Whether a human has signed off on the record, which is a different question
# from whether the resource is alive (`status`). The literature pipeline admits
# records automatically so the backlog stops being a gate, and this is what
# keeps an unvetted record off the published site: 07_export_site.py exports
# only `reviewed` rows, so an unreviewed record is queryable from the snapshots
# and fully checked by QC, but invisible at cellfatecontrol.com until someone
# has looked at it.
#
# The DDL defaults to `reviewed`, so the twenty hand-curated records say nothing
# and mean what they always did. Only 03_record.py writes `unreviewed`.
REVIEW_STATES = ("reviewed", "unreviewed")
PAPER_ROLES = ("primary", "preprint", "benchmark", "critique", "application",
               "extension", "review")
VENUE_TYPES = ("journal", "conference", "preprint", "workshop", "thesis", "other")
LINK_KINDS = ("code", "weights", "website", "dataset", "docs", "api",
              "supplementary", "demo", "container")

# Degree of independence of the evaluation, and nothing else. Ordered most to
# least independent. A model is NOT lifted by being evaluated repeatedly: one
# group asserting the same claim n times is still one group, and rewarding
# volume would favour the most prolific labs over the most scrutinized models.
#
# Derivation (05_validate.py), over every entity_paper row with
# role IN ('benchmark','critique'), comparing its authors against the authors of
# the `primary` paper, normalized to lastname + first initial:
#
#   shared == 0                                    -> independent
#   0 < shared < 50% of the evaluating paper's authors -> partially independent
#   shared >= 50%                                  -> same group; contributes nothing
#
# The model takes the most independent tier any single evaluation reaches:
# any independent evaluation    -> externally-benchmarked
# else any partially independent -> partially-independent
# else                           -> self-reported
EVIDENCE_TIERS = ("externally-benchmarked", "partially-independent",
                  "self-reported")

# Fraction of the EVALUATING paper's authors that may be shared with the primary
# paper before the evaluation is treated as coming from the same group.
PARTIAL_MAX = 0.50


def norm_author(name: str) -> str:
    """
    Normalize to `lastname|first-initial`, accent- and case-folded.

    Deliberately lossy and therefore conservative: two different people who
    share a surname and initial collide, which counts as author overlap and
    biases the derivation toward the LOWER (less independent) tier. Reporting a
    model as less externally validated than it is, is the safe direction.
    """
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c)).lower()
    parts = [p for p in re.split(r"[\s.\-,]+", n) if p]
    if not parts:
        return ""
    return f"{parts[-1]}|{parts[0][0]}"


def classify_overlap(primary: set[str], evaluating: set[str]) -> tuple[str, set[str]]:
    shared = primary & evaluating
    if not shared:
        return "independent", shared
    if not evaluating:
        return "unknown", shared
    if len(shared) / len(evaluating) < PARTIAL_MAX:
        return "partial", shared
    return "same-group", shared


def derive_tier(primary: set[str],
                evaluations: list[tuple[str, set[str]]]) -> tuple[str, list]:
    verdicts = [(pid, *classify_overlap(primary, authors))
                for pid, authors in evaluations]
    kinds = {v[1] for v in verdicts}
    if "independent" in kinds:
        tier = "externally-benchmarked"
    elif "partial" in kinds:
        tier = "partially-independent"
    else:
        tier = "self-reported"
    return tier, verdicts


# These three live here, beside the tier vocabulary they produce, rather than in
# 05_validate.py where they started. `evidence_tier` is the one claim CFCR rests
# on, and literature/02_triage.py needs the same arithmetic to decide which role
# proposals could move a tier and therefore need a human. Two copies of this
# would be the worst possible thing in this repository to let drift.
AVAILABILITY_TIERS = ("open-source", "open-weights", "api-only")
MODEL_FAMILIES = ("interval-model", "dna-lm", "perturbation-model",
                  "module-predictor", "other")
INPUT_TYPES = ("genomic-interval", "sequence", "expression-matrix", "multimodal")
RECORD_UNITS = ("intervals", "cells", "constructs", "variants", "sequences")
ACCESS_LEVELS = ("open", "registered", "controlled")
VALIDATION_TIERS = ("published-peer-reviewed", "lab-validated", "use-with-caution")
DIFFICULTIES = ("routine", "moderate", "demanding")
PROTOCOL_ORIGINS = ("external", "cfc-lab")
UPDATE_FREQUENCIES = ("continuous", "annual", "static", "unmaintained")
MODULE_TYPES = ("DBD", "ED", "CR")
VALIDATION_LEVELS = ("screen-validated", "ChIP-validated", "motif-only",
                     "predicted", "structurally-resolved")

# `vocab.facet` is deliberately NOT constrained in the DDL. Facets are expected
# to grow (schema §4 ships six; architecture/modality were added to the original
# four), and a CHECK constraint in SQLite cannot be altered without rebuilding
# the table -- every deployed database would need a migration to admit one new
# vocabulary. Instead a facet exists iff `vocab/<facet>.yaml` exists, and
# 05_validate.py validates against the files actually present. Adding a
# vocabulary is then a one-file change with no DDL touch.
VOCAB_FACETS = ("organism", "cell_type", "assay", "task", "architecture",
                "modality")


def _check(col: str, allowed: tuple[str, ...], nullable: bool = True) -> str:
    """Render a CHECK clause for a scalar enum column."""
    values = ", ".join(f"'{v}'" for v in allowed)
    null = f"{col} IS NULL OR " if nullable else ""
    return f"CHECK({null}{col} IN ({values}))"


# ── DDL ──────────────────────────────────────────────────────────────────────

CREATE_ENTITY = f"""
CREATE TABLE IF NOT EXISTS entity (
    entity_id       TEXT    PRIMARY KEY,
    type            TEXT    NOT NULL {_check('type', ENTITY_TYPES, nullable=False)},
    name            TEXT    NOT NULL,
    aliases         TEXT,           -- JSON array
    year            INTEGER,
    description     TEXT,           -- free text: BM25 + embedding source
    notes           TEXT,           -- free text: curator commentary
    tags            TEXT,           -- JSON array; vocabulary staging area
    fate_axis       TEXT,           -- JSON array over FATE_AXES
    organism        TEXT,           -- JSON array, controlled
    cell_type       TEXT,           -- JSON array, controlled
    assay           TEXT,           -- JSON array, controlled
    task            TEXT,           -- JSON array, controlled
    status          TEXT    {_check('status', ENTITY_STATUS)},
    review_state    TEXT    NOT NULL DEFAULT 'reviewed'
                            {_check('review_state', REVIEW_STATES, nullable=False)},
    supersedes      TEXT    REFERENCES entity(entity_id),
    variant_of      TEXT    REFERENCES entity(entity_id),
    date_added      TEXT    NOT NULL,
    date_updated    TEXT    NOT NULL,
    curator         TEXT
);
"""

CREATE_PAPER = f"""
CREATE TABLE IF NOT EXISTS paper (
    paper_id        TEXT    PRIMARY KEY,   -- raw DOI, else biorxiv:/arxiv: id
    doi             TEXT,
    title           TEXT,
    authors         TEXT,           -- JSON array, source order preserved
    year            INTEGER,
    venue           TEXT,
    venue_type      TEXT    {_check('venue_type', VENUE_TYPES)},
    abstract        TEXT,           -- free text: BM25 + embedding source
    url             TEXT,
    preprint_of     TEXT    REFERENCES paper(paper_id),
    metadata_source TEXT,           -- crossref | europepmc | biorxiv | manual
    date_added      TEXT    NOT NULL
);
"""

CREATE_ENTITY_PAPER = f"""
CREATE TABLE IF NOT EXISTS entity_paper (
    entity_id   TEXT    NOT NULL REFERENCES entity(entity_id) ON DELETE CASCADE,
    paper_id    TEXT    NOT NULL REFERENCES paper(paper_id),
    role        TEXT    NOT NULL {_check('role', PAPER_ROLES, nullable=False)},
    note        TEXT,
    PRIMARY KEY (entity_id, paper_id, role)
);
"""

CREATE_LINK = f"""
CREATE TABLE IF NOT EXISTS link (
    entity_id   TEXT    NOT NULL REFERENCES entity(entity_id) ON DELETE CASCADE,
    kind        TEXT    NOT NULL {_check('kind', LINK_KINDS, nullable=False)},
    url         TEXT    NOT NULL,
    label       TEXT,
    checked     TEXT,
    alive       INTEGER,
    PRIMARY KEY (entity_id, kind, url)
);
"""

CREATE_VOCAB = """
CREATE TABLE IF NOT EXISTS vocab (
    facet       TEXT    NOT NULL,   -- unconstrained by design; see VOCAB_FACETS
    term        TEXT    NOT NULL,
    ontology_id TEXT,
    synonyms    TEXT,               -- JSON array
    n_records   INTEGER DEFAULT 0,  -- computed by 05_validate.py
    PRIMARY KEY (facet, term)
);
"""

CREATE_MODEL_EXT = f"""
CREATE TABLE IF NOT EXISTS model_ext (
    entity_id           TEXT PRIMARY KEY REFERENCES entity(entity_id) ON DELETE CASCADE,
    -- Derived, not asserted (schema §3.1). The YAML value is the curator's
    -- claim; 05_validate.py recomputes it from entity_paper + author overlap
    -- and reports every disagreement. See EVIDENCE_TIERS for the three-way
    -- independence rule and its threshold.
    evidence_tier       TEXT {_check('evidence_tier', EVIDENCE_TIERS)},
    availability_tier   TEXT {_check('availability_tier', AVAILABILITY_TIERS)},
    model_family        TEXT {_check('model_family', MODEL_FAMILIES)},
    architecture        TEXT,       -- JSON array, controlled
    input_type          TEXT {_check('input_type', INPUT_TYPES)},
    input_context_bp    INTEGER,
    output_type         TEXT,       -- JSON array, controlled
    output_resolution_bp INTEGER,
    -- Parameter count as a RANGE, because an entity is a named artifact and
    -- several ship as a family of checkpoints under one name: Evo 2 is 7B and
    -- 40B, Nucleotide Transformer spans 50M to 2.5B. A single INTEGER forced
    -- those to null, which made "ships in four sizes" indistinguishable from
    -- "nobody published it" -- and left the column unfilterable either way.
    --   single-size model : min == max
    --   family            : min and max are the extremes of the release
    --   genuinely unknown : both null
    -- Filtering "what can I run on one GPU" is then n_parameters_max.
    n_parameters_min    INTEGER,
    n_parameters_max    INTEGER,
    genome_build        TEXT,       -- JSON array
    training_data       TEXT,       -- JSON array
    license             TEXT,       -- SPDX where possible
    benchmarked_on      TEXT        -- JSON array; v0.2: entity<->entity relation
);
"""

CREATE_BENCHMARK_EXT = """
CREATE TABLE IF NOT EXISTS benchmark_ext (
    entity_id           TEXT PRIMARY KEY REFERENCES entity(entity_id) ON DELETE CASCADE,
    n_tasks             INTEGER,
    n_models_evaluated  INTEGER,
    task_categories     TEXT,       -- JSON array, controlled -> vocab/task.yaml
    evaluation_mode     TEXT,       -- JSON array
    has_leaderboard     INTEGER,
    leaderboard_url     TEXT,
    submission_open     INTEGER,
    baseline_included   INTEGER
);
"""

CREATE_DATASET_EXT = f"""
CREATE TABLE IF NOT EXISTS dataset_ext (
    entity_id       TEXT PRIMARY KEY REFERENCES entity(entity_id) ON DELETE CASCADE,
    n_records       INTEGER,
    record_unit     TEXT {_check('record_unit', RECORD_UNITS)},
    modality        TEXT,           -- JSON array, controlled
    accession       TEXT,           -- JSON array
    genome_build    TEXT,           -- JSON array
    access          TEXT {_check('access', ACCESS_LEVELS)},
    license         TEXT
);
"""

CREATE_MODULE_COLLECTION_EXT = f"""
CREATE TABLE IF NOT EXISTS module_collection_ext (
    entity_id                   TEXT PRIMARY KEY REFERENCES entity(entity_id) ON DELETE CASCADE,
    module_types                TEXT,   -- JSON array over MODULE_TYPES
    n_records                   INTEGER,
    dominant_validation_level   TEXT {_check('dominant_validation_level', VALIDATION_LEVELS)},
    assay_format                TEXT,
    organism_scope              TEXT,   -- JSON array, controlled
    integrated_in_ecr_lib       INTEGER,
    ecr_lib_source_key          TEXT    -- joins eCR_mod_lib.source_screen
);
"""

CREATE_PROTOCOL_EXT = f"""
CREATE TABLE IF NOT EXISTS protocol_ext (
    entity_id       TEXT PRIMARY KEY REFERENCES entity(entity_id) ON DELETE CASCADE,
    validation_tier TEXT {_check('validation_tier', VALIDATION_TIERS)},
    protocol_doi    TEXT,
    canonical_host  TEXT,
    version         TEXT,
    duration_hours  REAL,
    difficulty      TEXT {_check('difficulty', DIFFICULTIES)},
    category        TEXT,           -- JSON array, controlled
    key_reagents    TEXT,           -- JSON array; advisory, catalog numbers go stale
    origin          TEXT {_check('origin', PROTOCOL_ORIGINS)}
);
"""

CREATE_DATABASE_EXT = f"""
CREATE TABLE IF NOT EXISTS database_ext (
    entity_id        TEXT PRIMARY KEY REFERENCES entity(entity_id) ON DELETE CASCADE,
    update_frequency TEXT {_check('update_frequency', UPDATE_FREQUENCIES)},
    last_release     TEXT,
    has_api          INTEGER,
    bulk_download    INTEGER
);
"""

CREATE_PROVENANCE = """
CREATE TABLE IF NOT EXISTS provenance (
    run_id          TEXT    PRIMARY KEY,
    script          TEXT    NOT NULL,
    run_date        TEXT    NOT NULL,
    source_name     TEXT    NOT NULL,
    source_url      TEXT,
    source_version  TEXT,
    file_path       TEXT,
    file_checksum   TEXT,
    records_added   INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    notes           TEXT
);
"""

# One table per entity type, keyed by `entity.type`.
EXT_TABLES: dict[str, str] = {
    "model": "model_ext",
    "benchmark": "benchmark_ext",
    "dataset": "dataset_ext",
    "module": "module_collection_ext",
    "protocol": "protocol_ext",
    "database": "database_ext",
}

ALL_DDL = (CREATE_ENTITY + CREATE_PAPER + CREATE_ENTITY_PAPER + CREATE_LINK
           + CREATE_VOCAB + CREATE_MODEL_EXT + CREATE_BENCHMARK_EXT
           + CREATE_DATASET_EXT + CREATE_MODULE_COLLECTION_EXT
           + CREATE_PROTOCOL_EXT + CREATE_DATABASE_EXT + CREATE_PROVENANCE)

# Columns added after a table shipped. CREATE TABLE IF NOT EXISTS is a no-op on
# an existing database, so a new column in the DDL above would never reach one.
# Each entry is applied only when absent, keeping _create_schema() idempotent.
# Format: (table, column, declaration).
MIGRATIONS: list[tuple[str, str, str]] = [
    ("model_ext", "n_parameters_min", "INTEGER"),
    ("model_ext", "n_parameters_max", "INTEGER"),
]

# Columns removed after a table shipped, dropped when present. Needed because
# db/entities.tsv is generated from the live table shape: a database carried
# over from before a removal would keep emitting the dead column, so the
# committed snapshot would differ between a fresh clone and an existing
# checkout. Requires SQLite 3.35+ for ALTER TABLE DROP COLUMN; older versions
# leave the column in place, which is harmless but does change the snapshot.
# Format: (table, column).
OBSOLETE_COLUMNS: list[tuple[str, str]] = [
    ("model_ext", "n_parameters"),      # replaced by the min/max pair
]

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_entity_type ON entity(type);",
    "CREATE INDEX IF NOT EXISTS idx_entity_status ON entity(status);",
    "CREATE INDEX IF NOT EXISTS idx_entity_year ON entity(year);",
    "CREATE INDEX IF NOT EXISTS idx_ep_paper ON entity_paper(paper_id);",
    "CREATE INDEX IF NOT EXISTS idx_ep_role ON entity_paper(role);",
    "CREATE INDEX IF NOT EXISTS idx_link_entity ON link(entity_id);",
    "CREATE INDEX IF NOT EXISTS idx_vocab_facet ON vocab(facet);",
    "CREATE INDEX IF NOT EXISTS idx_model_evidence ON model_ext(evidence_tier);",
    "CREATE INDEX IF NOT EXISTS idx_model_family ON model_ext(model_family);",
]

# Which columns round-trip through JSON. Anything not listed here is a scalar.
ARRAY_COLUMNS: dict[str, frozenset[str]] = {
    "entity": frozenset({"aliases", "tags", "fate_axis", "organism",
                         "cell_type", "assay", "task"}),
    "paper": frozenset({"authors"}),
    "entity_paper": frozenset(),
    "link": frozenset(),
    "vocab": frozenset({"synonyms"}),
    "model_ext": frozenset({"architecture", "output_type", "genome_build",
                            "training_data", "benchmarked_on"}),
    "benchmark_ext": frozenset({"task_categories", "evaluation_mode"}),
    "dataset_ext": frozenset({"modality", "accession", "genome_build"}),
    "module_collection_ext": frozenset({"module_types", "organism_scope"}),
    "protocol_ext": frozenset({"category", "key_reagents"}),
    "database_ext": frozenset(),
    "provenance": frozenset(),
}


def encode_row(table: str, row: dict) -> dict:
    """Convert list-valued columns to JSON text for storage."""
    arrays = ARRAY_COLUMNS.get(table, frozenset())
    out = {}
    for key, value in row.items():
        if key in arrays and value is not None and not isinstance(value, str):
            out[key] = json.dumps(list(value), ensure_ascii=False)
        elif isinstance(value, bool):
            out[key] = int(value)
        else:
            out[key] = value
    return out


def decode_row(table: str, row: dict) -> dict:
    """Convert JSON text columns back to Python lists."""
    arrays = ARRAY_COLUMNS.get(table, frozenset())
    out = dict(row)
    for key in arrays & out.keys():
        value = out[key]
        if isinstance(value, str) and value:
            try:
                out[key] = json.loads(value)
            except json.JSONDecodeError:
                out[key] = [value]
        elif value is None:
            out[key] = []
    return out


# ── CFCR class ───────────────────────────────────────────────────────────────

class CFCR:
    """
    Context manager wrapping a SQLite connection to the CFCR catalogue.

    Example
    -------
    with CFCR("db/cfcr.db") as db:
        db.upsert_papers(papers)
        db.upsert_entities(entities)
        db.upsert_ext("model", model_exts)
        df = db.to_dataframe("model")
    """

    REQUIRED_ENTITY_FIELDS = {"entity_id", "type", "name",
                              "date_added", "date_updated"}
    REQUIRED_PAPER_FIELDS = {"paper_id", "date_added"}

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: sqlite3.Connection | None = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        # Deliberately OFF during the build. Records are loaded type-file by
        # type-file, so `supersedes`/`variant_of`/`preprint_of` routinely point
        # at rows that arrive later in the same run; enforcing FKs here would
        # make load order significant. 05_validate.py resolves every reference
        # explicitly once the whole catalogue is in, which is the check that
        # actually matters and which reports *which* reference dangles.
        self.conn.execute("PRAGMA foreign_keys=OFF;")
        self._create_schema()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()
        return False

    # ── schema ───────────────────────────────────────────────────────────────

    def _create_schema(self):
        cur = self.conn.cursor()
        cur.executescript(ALL_DDL)
        for table, col, decl in MIGRATIONS:
            cur.execute(f"PRAGMA table_info({table});")
            have = {row["name"] for row in cur.fetchall()}
            if col not in have:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl};")
        for table, col in OBSOLETE_COLUMNS:
            cur.execute(f"PRAGMA table_info({table});")
            have = {row["name"] for row in cur.fetchall()}
            if col in have:
                try:
                    cur.execute(f"ALTER TABLE {table} DROP COLUMN {col};")
                except sqlite3.OperationalError:
                    # SQLite < 3.35 cannot drop a column. Leave it; it is
                    # unused, and the build still succeeds.
                    pass
        for idx in CREATE_INDEXES:
            cur.execute(idx)
        self.conn.commit()

    def _columns(self, table: str) -> list[str]:
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA table_info({table});")
        return [row["name"] for row in cur.fetchall()]

    # ── write ────────────────────────────────────────────────────────────────

    def _upsert(self, table: str, records: list[dict], pk: tuple[str, ...],
                required: set[str] | None = None) -> tuple[int, int]:
        """
        Upsert records into `table`. Returns (inserted, updated).

        Only the columns a record actually mentions are written, so an update
        never NULLs a column the caller did not know about -- the same guarantee
        eCR_mod_lib needs for its dbd_* span columns, and the one that lets
        05_validate.py write derived values (evidence_tier, link.alive,
        vocab.n_records) back without a rebuild erasing them.
        """
        if not records:
            return 0, 0
        inserted = updated = 0
        cur = self.conn.cursor()
        columns = self._columns(table)
        where = " AND ".join(f"{k}=?" for k in pk)

        for rec in records:
            if required:
                missing = required - rec.keys()
                if missing:
                    ident = rec.get(pk[0], "?")
                    raise ValueError(
                        f"{table} record '{ident}' missing required field(s): "
                        f"{sorted(missing)}")
            unknown = rec.keys() - set(columns)
            if unknown:
                ident = rec.get(pk[0], "?")
                raise ValueError(
                    f"{table} record '{ident}' has unknown column(s): "
                    f"{sorted(unknown)} -- not in {table} schema")

            row = encode_row(table, {c: rec[c] for c in columns if c in rec})
            key_values = [row[k] for k in pk]
            cur.execute(f"SELECT 1 FROM {table} WHERE {where}", key_values)
            exists = cur.fetchone() is not None

            cols = list(row.keys())
            if exists:
                assignments = ", ".join(f"{c}=?" for c in cols)
                cur.execute(f"UPDATE {table} SET {assignments} WHERE {where}",
                            list(row.values()) + key_values)
                updated += 1
            else:
                placeholders = ", ".join("?" * len(cols))
                cur.execute(
                    f"INSERT INTO {table} ({', '.join(cols)}) "
                    f"VALUES ({placeholders})", list(row.values()))
                inserted += 1

        self.conn.commit()
        return inserted, updated

    def upsert_entities(self, records: list[dict]) -> tuple[int, int]:
        # `review_state` is defaulted here rather than left to the DDL, because
        # _upsert only writes the columns a record carries: a record that
        # omitted the field would keep whatever the database already held, so
        # removing `review_state: unreviewed` from a YAML file would not
        # un-stage the record and it would stay off the published site
        # silently. Defaulting on every upsert makes records/ authoritative for
        # this column, as it is meant to be for all of them.
        records = [dict(r, review_state=r.get("review_state") or "reviewed")
                   for r in records]
        return self._upsert("entity", records, ("entity_id",),
                            self.REQUIRED_ENTITY_FIELDS)

    def upsert_papers(self, records: list[dict]) -> tuple[int, int]:
        return self._upsert("paper", records, ("paper_id",),
                            self.REQUIRED_PAPER_FIELDS)

    def upsert_entity_papers(self, records: list[dict]) -> tuple[int, int]:
        return self._upsert("entity_paper", records,
                            ("entity_id", "paper_id", "role"),
                            {"entity_id", "paper_id", "role"})

    def upsert_links(self, records: list[dict]) -> tuple[int, int]:
        return self._upsert("link", records, ("entity_id", "kind", "url"),
                            {"entity_id", "kind", "url"})

    def upsert_vocab(self, records: list[dict]) -> tuple[int, int]:
        return self._upsert("vocab", records, ("facet", "term"),
                            {"facet", "term"})

    def upsert_ext(self, entity_type: str, records: list[dict]) -> tuple[int, int]:
        """Upsert into the extension table for `entity_type`."""
        if entity_type not in EXT_TABLES:
            raise ValueError(
                f"No extension table for type '{entity_type}'. "
                f"Known types: {sorted(EXT_TABLES)}")
        return self._upsert(EXT_TABLES[entity_type], records, ("entity_id",),
                            {"entity_id"})

    def insert_provenance(self, record: dict) -> None:
        cur = self.conn.cursor()
        columns = self._columns("provenance")
        row = {col: record.get(col) for col in columns}
        cols = list(row.keys())
        cur.execute(
            f"INSERT OR REPLACE INTO provenance ({', '.join(cols)}) "
            f"VALUES ({', '.join('?' * len(cols))})", list(row.values()))
        self.conn.commit()

    # ── read ─────────────────────────────────────────────────────────────────

    def to_dataframe(self, entity_type: str | None = None,
                     join_ext: bool = True) -> pd.DataFrame:
        """
        Entities as a DataFrame, with the extension table joined in when a
        single type is requested. JSON array columns are decoded to lists.
        """
        if entity_type:
            ext = EXT_TABLES.get(entity_type)
            if join_ext and ext:
                sql = (f"SELECT e.*, x.* FROM entity e "
                       f"LEFT JOIN {ext} x USING (entity_id) WHERE e.type=?")
            else:
                sql = "SELECT * FROM entity WHERE type=?"
            df = pd.read_sql_query(sql, self.conn, params=(entity_type,))
            table_for_arrays = ext if (join_ext and ext) else None
        else:
            df = pd.read_sql_query("SELECT * FROM entity", self.conn)
            table_for_arrays = None

        arrays = set(ARRAY_COLUMNS["entity"])
        if table_for_arrays:
            arrays |= set(ARRAY_COLUMNS[table_for_arrays])
        for col in arrays & set(df.columns):
            df[col] = df[col].map(
                lambda v: json.loads(v) if isinstance(v, str) and v else [])
        return df

    def papers_dataframe(self) -> pd.DataFrame:
        df = pd.read_sql_query("SELECT * FROM paper", self.conn)
        if "authors" in df.columns:
            df["authors"] = df["authors"].map(
                lambda v: json.loads(v) if isinstance(v, str) and v else [])
        return df

    def fetch(self, table: str, where: str = "", params: tuple = ()) -> list[dict]:
        """Rows from `table` as decoded dicts. For QC, which wants plain dicts."""
        cur = self.conn.cursor()
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        cur.execute(sql, params)
        return [decode_row(table, dict(row)) for row in cur.fetchall()]

    def counts(self) -> dict:
        """Record counts by entity type, paper role, and model evidence tier."""
        cur = self.conn.cursor()
        cur.execute("SELECT type, COUNT(*) FROM entity GROUP BY type")
        by_type = dict(cur.fetchall())
        cur.execute("SELECT role, COUNT(*) FROM entity_paper GROUP BY role")
        by_role = dict(cur.fetchall())
        cur.execute("SELECT evidence_tier, COUNT(*) FROM model_ext "
                    "GROUP BY evidence_tier")
        # A model_ext row with no tier is a record holding some other model
        # field -- a licence, say -- and leaving the tier to be derived. Its
        # key has to be a string: build_manifest.json is written with
        # sort_keys=True, and a None among the keys raises TypeError while
        # sorting, which took 04_build.py's exit status to 1 as soon as
        # 07_enrich.py started writing licences.
        by_tier = {(tier if tier is not None else "not asserted"): n
                   for tier, n in cur.fetchall()}
        cur.execute("SELECT COUNT(*) FROM paper")
        n_papers = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM link")
        n_links = cur.fetchone()[0]
        return {
            "n_entities": sum(by_type.values()),
            "n_papers": n_papers,
            "n_links": n_links,
            "by_type": by_type,
            "by_paper_role": by_role,
            "by_evidence_tier": by_tier,
        }

    # ── export ───────────────────────────────────────────────────────────────

    def to_tsv(self, table: str, out_path: str | Path) -> int:
        """
        Export one table to TSV for committing. Array columns stay as JSON text
        so the snapshot round-trips and `git diff` shows one line per record.
        Returns the row count written.
        """
        df = pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
        sort_cols = [c for c in ("entity_id", "paper_id", "facet", "term", "role")
                     if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols).reset_index(drop=True)
        df.to_csv(out_path, sep="\t", index=False, lineterminator="\n")
        return len(df)

    # ── utils ────────────────────────────────────────────────────────────────

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        """Explicit transaction block for batched writes."""
        cur = self.conn.cursor()
        try:
            yield cur
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
