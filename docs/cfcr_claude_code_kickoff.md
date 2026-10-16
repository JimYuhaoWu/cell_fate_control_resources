# Kickoff Prompt for Claude Code — CFCR v0.1 Skeleton

Paste everything below the line into a fresh Claude Code session, with
`cell_fate_resource_landscape.md` and `cfcr_schema_draft.md` attached or copied
into the repo first (e.g. into `docs/`).

---

I'm building **Cell Fate Control Resources (CFCR)**, a curated community hub for
researchers working on cell fate regulators and controllers. Repo:
`https://github.com/JimYuhaoWu/cell_fate_control_resources.git`

## Context you need

Two design documents are attached (or in `docs/`):

- `cell_fate_resource_landscape.md` — competitive landscape research. Read §4
  (conclusions) and §5 (my existing eCR_mod_lib architecture) before writing code.
- `cfcr_schema_draft.md` — the agreed data model. **This is the spec. Follow it.**

I'm a researcher in chromatin accessibility and cell fate, at the Cell Fate
Control Lab. I already maintain `JimYuhaoWu/eCR_mod_lib`, a ~10,800-record library
of DNA-binding domains, effector domains, and chromatin remodelers for engineered
cell-fate regulator (eCR) design. CFCR is its sibling: same pipeline pattern, new
content types.

## What CFCR is

A curated index of **models, benchmarks, datasets, module collections, protocols,
and external databases** relevant to controlling cell fate — organized not by
method but by what each resource lets you *do*:

- `where` — genomic interval models (Enformer, Borzoi, AlphaGenome, ChromBPNet, scBasset)
- `what` — perturbation models (shallow; Stegle's Nat Rev Genet catalogue owns this, we link out)
- `how` — DNA language models (NT, Evo 2, GPN-MSA)
- `with-what` — module collections from eCR_mod_lib

Published as a static site on GitHub Pages with client-side faceted filtering and
hybrid search. Long-term target: a database paper.

## Key architectural decisions already made — do not relitigate these

1. **Entity-primary, not paper-primary.** Models/benchmarks/datasets/etc. are the
   records; papers attach to them via a single `entity_paper` join with a `role`
   column (`primary`, `preprint`, `benchmark`, `critique`, `application`,
   `extension`, `review`).
2. **Controlled facet columns AND free-text columns on every entity.** Facets drive
   filtering; `description`/`notes`/`tags` drive BM25 + embeddings.
3. **Vocabularies grow bottom-up.** Free-text `tags` are a staging area; QC reports
   tags appearing on ≥10 records as promotion candidates. Ontology IDs (CL,
   NCBITaxon) only for `organism` and `cell_type` initially.
4. **Module collections, not components.** ~15–30 collection entities in CFCR;
   the ~10,800 individual records stay in eCR_mod_lib behind its own `load()`.
   See schema §6.
5. **`evidence_tier` for models is derived, not asserted** — `externally-benchmarked`
   iff a `benchmark`/`critique` paper exists with no author overlap with the
   `primary` paper. QC computes it and flags conflicts.
6. **Index benchmarks, don't run them.** No per-model scores. GENEB owns evaluation.
7. **No RAG framework, no FAISS.** Corpus is low thousands. Use
   `sentence-transformers` + NumPy. Hybrid retrieval: BM25 over title/abstract/
   description + cosine over embeddings, combined with reciprocal rank fusion.
   Precompute at build time, ship as a static artifact, search client-side.
8. **Protocols: metadata only.** Canonical text lives on protocols.io with a DOI.
9. **Metadata licensed CC0 or CC-BY**, separate from the code license.
10. **Only open paper metadata is stored** — abstracts from Europe PMC / Crossref /
    bioRxiv. No full text of paywalled work.

## What I want from this session

Build the **skeleton only** — I want to feel whether the shape works before
committing to a large backfill. Do not try to populate the catalogue.

1. **Repo scaffolding** matching the layout in schema §7: `config/`, `vocab/`,
   `records/`, `literature/`, `scripts/`, `db/`, `site/`, `reports/`. Include
   `pyproject.toml` (package name `cfcr`, Python 3.10), `environment.yml`
   (reuse the existing `ecr` conda env name so it works alongside eCR_mod_lib),
   `.gitignore`, `LICENSE` (code: MIT), `LICENSE-DATA` (CC-BY-4.0), `README.md`.

2. **`scripts/schema.py`** — SQLite DDL for every table in schema §2, §3, plus a
   `CFCR` class mirroring the `ModuleLibrary` pattern in eCR_mod_lib (upserts,
   provenance writes).

3. **`vocab/` starter files** — `organism.yaml`, `cell_type.yaml`, `assay.yaml`,
   `task.yaml`, `architecture.yaml`, `modality.yaml`. Seed each with only the terms
   needed by the example records below, in the entry shape from schema §4.

4. **`records/` seed data** — roughly 20 entities total, hand-written YAML, chosen
   to stress the schema rather than to be comprehensive:
   - ~8 models spanning all three model families and both availability tiers
     (include at least one `api-only` and one with a `supersedes` link and one
     `variant_of` link — e.g. Enformer → Borzoi → Flashzoi)
   - ~3 benchmarks (GENEB, BEND, DART-Eval)
   - ~3 datasets
   - ~3 module collections (schema §6.1 has a worked Tycko 2025 example)
   - ~2 protocols (one `external`, one `cfc-lab`)
   - ~1 external database
   Seed `literature/papers.yaml` with the papers these reference. The landscape
   doc §3 has a seed list of model families and the key critical-evaluation papers.
   **Verify DOIs and metadata against Crossref/Europe PMC rather than writing them
   from memory — do not invent identifiers.** Leave a field null and flag it if you
   cannot verify it.

5. **`scripts/04_build.py`** — YAML records → SQLite → committed TSV snapshots
   (`db/entities.tsv`, `db/papers.tsv`, `db/entity_paper.tsv`) plus
   `build_manifest.json`.

6. **`scripts/05_validate.py`** — the QC checks in schema §10. This is the most
   important script; make the failure messages precise and actionable.

7. **`cfcr/__init__.py`** — the `load()` / `load_papers()` API from schema §8,
   returning flat pandas DataFrames with papers denormalized.

8. **`README.md`** — what CFCR is, the `fate_axis` organizing principle, quickstart,
   contribution path, and both licenses.

## Explicitly out of scope for this session

- `literature/01_search.py`, `02_triage.py`, `03_record.py` — next session; I'll
  adapt them from eCR_mod_lib rather than writing fresh
- `scripts/06_embed.py`, `07_export_site.py`, and the `site/` front-end
- Any substantial backfill
- CI workflows

## How I work

Show me the schema DDL and two or three seed records early, before building the
rest, so I can correct the shape while it's cheap. Flag anywhere the spec is
ambiguous or where you think a decision in it is wrong — I'd rather argue now
than migrate later.
