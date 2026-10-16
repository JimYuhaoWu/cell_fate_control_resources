# CFCR Schema Draft v0.1

**Cell Fate Control Resources** — data model for a curated hub of models,
benchmarks, datasets, modules, protocols, and the papers that evidence them.

**Status:** draft for review · 2026-10-16
**Designed to extend:** `JimYuhaoWu/eCR_mod_lib` pipeline pattern, not replace it.

---

## 1. Design principles

1. **Entity-primary.** The thing being catalogued is a model, benchmark, dataset,
   module, or protocol. Papers are *evidence attached to entities*, not the
   primary record.
2. **One join table.** `entity_paper` with a `role` column carries the
   many-to-many. Entity↔entity relations are deferred to v0.2.
3. **Controlled columns drive facets; free text drives search.** Both exist on
   every entity. Neither is optional.
4. **Vocabularies grow bottom-up.** Free-text `tags` are a staging area; terms
   that recur get promoted into `vocab/` with synonyms and (where it matters)
   ontology IDs.
5. **SQLite is the build artifact; TSV/JSON snapshots are committed.** Same as
   eCR_mod_lib — enables `git diff` review of every curation change.
6. **The loader hides the schema.** Users get flat DataFrames. Normalization is a
   build-time concern.
7. **Metadata licensed CC0 or CC-BY**, separately from the code license.

---

## 2. Core tables

### 2.1 `entity`

The spine. Every catalogued object gets exactly one row.

| Column | Type | Notes |
|---|---|---|
| `entity_id` | TEXT PK | Stable slug, e.g. `model:borzoi`, `protocol:cutrun-lowinput-v2` |
| `type` | TEXT | enum: `model` `benchmark` `dataset` `module` `protocol` `database` |
| `name` | TEXT | Canonical display name |
| `aliases` | TEXT[] | Other names seen in the literature |
| `year` | INT | Year of first public release |
| `description` | TEXT | **Free text.** 1–3 sentences: what it does, what it contributes |
| `notes` | TEXT | **Free text.** Curator's commentary, caveats, gotchas |
| `tags` | TEXT[] | **Free text.** Vocabulary staging area |
| `fate_axis` | TEXT[] | enum, multi: `where` `what` `how` `with-what` (see §5) |
| `organism` | TEXT[] | **Controlled** → `vocab/organism.yaml` (NCBITaxon) |
| `cell_type` | TEXT[] | **Controlled** → `vocab/cell_type.yaml` (CL) |
| `assay` | TEXT[] | **Controlled** → `vocab/assay.yaml` |
| `task` | TEXT[] | **Controlled** → `vocab/task.yaml` |
| `status` | TEXT | enum: `active` `deprecated` `superseded` `unmaintained` |
| `supersedes` | TEXT | FK → `entity.entity_id`, nullable |
| `variant_of` | TEXT | FK → `entity.entity_id`, nullable (replicates, ports, forks) |
| `date_added` | DATE | |
| `date_updated` | DATE | |
| `curator` | TEXT | Who made the call |

**Entity granularity rule (write this down, enforce in QC):**
> One entity per *named, independently citable artifact*. Replicate checkpoints
> of one model are **one** entity. A re-implementation or port under a distinct
> name (Flashzoi, enformer-pytorch) is a **separate** entity with
> `variant_of` set. A successor model with its own paper (Enformer → Borzoi) is a
> **separate** entity with `supersedes` set.

### 2.2 `paper`

| Column | Type | Notes |
|---|---|---|
| `paper_id` | TEXT PK | DOI-derived slug; fallback arXiv/bioRxiv ID |
| `doi` | TEXT | Nullable (some preprints/workshop papers lack one) |
| `title` | TEXT | |
| `authors` | TEXT[] | |
| `year` | INT | |
| `venue` | TEXT | Journal / conference / `preprint` |
| `venue_type` | TEXT | enum: `journal` `conference` `preprint` `workshop` `thesis` `other` |
| `abstract` | TEXT | **Free text.** Source for BM25 + embeddings |
| `url` | TEXT | |
| `preprint_of` | TEXT | FK → `paper.paper_id` — links preprint to journal version |
| `date_added` | DATE | |

> **Only open metadata is stored.** Abstracts from Europe PMC / Crossref /
> bioRxiv. No full text of paywalled work.

### 2.3 `entity_paper` — the join

| Column | Type | Notes |
|---|---|---|
| `entity_id` | TEXT FK | |
| `paper_id` | TEXT FK | |
| `role` | TEXT | enum below |
| `note` | TEXT | Optional, e.g. "Table 3 only" |

PK: (`entity_id`, `paper_id`, `role`)

**`role` vocabulary:**

| Value | Meaning |
|---|---|
| `primary` | The paper introducing this entity |
| `preprint` | Earlier preprint of the primary work |
| `benchmark` | Independently evaluates this entity |
| `critique` | Reports limitations/failure modes |
| `application` | Uses the entity to do biology |
| `extension` | Builds on or modifies it |
| `review` | Discusses it in a survey |

This table is the differentiator. `role IN ('benchmark','critique')` answers
"which models have independent external evaluation" — a query no existing list
in the landscape can serve.

### 2.4 `link`

Resources hang off entities, not off papers. One entity, many links.

| Column | Type | Notes |
|---|---|---|
| `entity_id` | TEXT FK | |
| `kind` | TEXT | enum: `code` `weights` `website` `dataset` `docs` `api` `supplementary` `demo` `container` |
| `url` | TEXT | |
| `label` | TEXT | Optional display override |
| `checked` | DATE | Last link-rot check |
| `alive` | BOOL | Set by QC script |

### 2.5 `vocab` (materialized from `vocab/*.yaml`)

| Column | Type | Notes |
|---|---|---|
| `facet` | TEXT | `organism` `cell_type` `assay` `task` |
| `term` | TEXT | Canonical |
| `ontology_id` | TEXT | Nullable: `CL:0002322`, `NCBITaxon:10090`, ... |
| `synonyms` | TEXT[] | Normalization targets |
| `n_records` | INT | Computed; drives promotion review |

---

## 3. Per-type extension tables

Each joins 1:1 to `entity` on `entity_id`.

### 3.1 `model_ext`

**Two orthogonal quality axes, per your spec.**

| Column | Type | Notes |
|---|---|---|
| `entity_id` | TEXT PK FK | |
| `evidence_tier` | TEXT | enum: `externally-benchmarked` · `self-reported` |
| `availability_tier` | TEXT | enum: `open-source` · `open-weights` · `api-only` |
| `model_family` | TEXT | **Controlled**: `interval-model` `dna-lm` `perturbation-model` `module-predictor` `other` |
| `architecture` | TEXT[] | **Controlled**: `cnn` `transformer` `ssm` `diffusion` `vae` `gan` `flow` `hybrid` |
| `input_type` | TEXT | **Controlled**: `genomic-interval` `sequence` `expression-matrix` `multimodal` |
| `input_context_bp` | INT | Nullable. Key discriminator for interval models |
| `output_type` | TEXT[] | **Controlled**: `coverage-track` `scalar` `embedding` `variant-effect` `sequence` `cell-state` |
| `output_resolution_bp` | INT | Nullable |
| `n_parameters` | INT | Nullable |
| `genome_build` | TEXT[] | `hg38`, `mm10`, ... |
| `training_data` | TEXT[] | Free text or FK-like refs to dataset entities |
| `license` | TEXT | SPDX where possible |
| `benchmarked_on` | TEXT[] | v0.2: promote to entity↔entity relation |

> `evidence_tier` is derived, not asserted: it is `externally-benchmarked` iff at
> least one `entity_paper` row has `role IN ('benchmark','critique')` **and** that
> paper shares no authors with the `primary` paper. QC computes and flags conflicts.

### 3.2 `benchmark_ext`

| Column | Type | Notes |
|---|---|---|
| `entity_id` | TEXT PK FK | |
| `n_tasks` | INT | |
| `n_models_evaluated` | INT | |
| `task_categories` | TEXT[] | **Controlled** → `vocab/task.yaml` |
| `evaluation_mode` | TEXT[] | `zero-shot` `probed` `fine-tuned` `full-train` |
| `has_leaderboard` | BOOL | |
| `leaderboard_url` | TEXT | |
| `submission_open` | BOOL | Can others submit models? |
| `baseline_included` | BOOL | Does it include ab initio / simple baselines? |

### 3.3 `dataset_ext`

| Column | Type | Notes |
|---|---|---|
| `entity_id` | TEXT PK FK | |
| `n_records` | INT | Intervals, cells, constructs — unit in `record_unit` |
| `record_unit` | TEXT | `intervals` `cells` `constructs` `variants` `sequences` |
| `modality` | TEXT[] | **Controlled**: `atac` `rna` `chip` `dnase` `cage` `hic` `methyl` `perturb-seq` |
| `accession` | TEXT[] | GEO / ENA / ArrayExpress / Zenodo |
| `genome_build` | TEXT[] | |
| `access` | TEXT | enum: `open` `registered` `controlled` |
| `license` | TEXT | |

### 3.4 `module_collection_ext`

CFCR catalogues module **collections**, not individual components — see §6 for the
decision and §6.1 for the table definition and worked example.

Individual DBD/ED/CR records remain in eCR_mod_lib with its existing schema
(`module_type`, `subtype`, `validation_level`, `uniprot_id`, `jaspar_id`,
`sequence`, `source_screen`) and are reached through `eCR_mod_lib.load()`.

### 3.5 `protocol_ext`

| Column | Type | Notes |
|---|---|---|
| `entity_id` | TEXT PK FK | |
| `validation_tier` | TEXT | enum: `published-peer-reviewed` · `lab-validated` · `use-with-caution` |
| `protocol_doi` | TEXT | protocols.io / Bio-protocol / STAR Protocols DOI |
| `canonical_host` | TEXT | Where the authoritative version lives |
| `version` | TEXT | |
| `duration_hours` | REAL | Nullable |
| `difficulty` | TEXT | `routine` `moderate` `demanding` |
| `category` | TEXT[] | **Controlled**: `cloning` `transfection` `reprogramming` `atac` `cutrun` `screening` `imaging` `qc` |
| `key_reagents` | TEXT[] | Free text; catalog numbers go stale, treat as advisory |
| `origin` | TEXT | enum: `external` `cfc-lab` |

> Canonical protocol text is hosted on protocols.io with a DOI; CFCR mirrors
> metadata only. Keeps versioning, citability, and maintenance burden bounded.

### 3.6 `database_ext`

For external resources catalogued as pointers (JASPAR, EpiFactors, ENCODE, ...).

| Column | Type | Notes |
|---|---|---|
| `entity_id` | TEXT PK FK | |
| `update_frequency` | TEXT | `continuous` `annual` `static` `unmaintained` |
| `last_release` | DATE | |
| `has_api` | BOOL | |
| `bulk_download` | BOOL | |

---

## 4. Controlled vocabulary files

```
vocab/
├── organism.yaml      # NCBITaxon IDs
├── cell_type.yaml     # Cell Ontology (CL) IDs
├── assay.yaml         # EFO/OBI where available
├── task.yaml          # local vocabulary, no good ontology exists
├── architecture.yaml  # local
└── modality.yaml      # local
```

Entry shape:

```yaml
- term: mouse embryonic stem cell
  ontology_id: CL:0002322
  synonyms: [mESC, mouse ESC, "embryonic stem cell (mouse)", ES cell mouse]
  facet: cell_type
```

**Promotion workflow:** QC counts `tags` frequency across all entities. Any tag on
≥10 records is emitted to `reports/vocab_candidates.md` for the curator to promote
or reject. Vocabulary grows from real records, never designed in advance.

Ontology IDs are attached only where they carry weight — `organism` and
`cell_type` first, `assay` second. `task` and `architecture` stay local.

---

## 5. The `fate_axis` facet

The organizing principle that makes CFCR distinct from every method-organized list.

| Value | Question answered | Typical entities |
|---|---|---|
| `where` | Where on the genome do I act? | Interval models: Enformer, Borzoi, AlphaGenome, ChromBPNet, scBasset |
| `what` | What do I perturb, with what cell-level effect? | Perturbation models: CellOT, GEARS, CellFlow |
| `how` | How do I represent and score sequence? | DNA LMs: NT, Evo 2, GPN-MSA, DNABERT |
| `with-what` | What do I build the actuator from? | Modules: DBD / ED / CR |

Multi-valued — an entity may sit on more than one axis. Datasets, benchmarks and
protocols inherit the axis of what they serve.

---

## 6. Module granularity — DECIDED

**Rationale:** CFCR users are looking for *resources*, not individual components.
Someone arrives wanting "a validated repressor-domain screen to draw from," not
`ZNF10-KRAB` specifically. Component-level lookup is what `eCR_mod_lib.load()` is
for, and that audience already knows to go there.

**Resolution — two tiers:**

- **Tier 1 (in CFCR `entity`):** module *collections* only — "AnimalTFDB 4.0 DBDs",
  "Tycko 2025 compact effectors", "DelRosso 2023 activation/repression domains",
  "EpiFactors 2.0 enzymatic CRs". Each is a first-class entity with full paper
  evidence, `fate_axis: [with-what]`, and a `link` of kind `dataset` pointing at
  the underlying records. Expect ~15–30 such entities.
- **Tier 2 (stays in eCR_mod_lib):** the ~10,800 individual DBD/ED/CR records,
  unchanged, queried through the existing `load()` API and surfaced on the site
  as a **separate browse interface** at `/modules`, not mixed into the main
  entity facets.

This keeps CFCR's entity count in the low thousands — which is what makes
client-side search instant — while preserving full component-level query power
where it belongs.

### 6.1 Consequence: `module_ext` is replaced by `module_collection_ext`

The per-component `module_ext` table in §3.4 is **not** part of CFCR v0.1. Use
instead:

| Column | Type | Notes |
|---|---|---|
| `entity_id` | TEXT PK FK | |
| `module_types` | TEXT[] | Which of `DBD` `ED` `CR` the collection contains |
| `n_records` | INT | Count contributed to eCR_mod_lib |
| `dominant_validation_level` | TEXT | enum (existing eCR_mod_lib vocabulary): `screen-validated` `ChIP-validated` `motif-only` `predicted` `structurally-resolved` |
| `assay_format` | TEXT | e.g. `HT-recruit`, `tAD-seq`, `Gal4-fusion`, `curated-annotation` |
| `organism_scope` | TEXT[] | **Controlled** → `vocab/organism.yaml` |
| `integrated_in_ecr_lib` | BOOL | Whether records are already ingested |
| `ecr_lib_source_key` | TEXT | Join key back to eCR_mod_lib, e.g. `Tycko_2025` |

`ecr_lib_source_key` matches the existing `source_screen` convention in
eCR_mod_lib, so the site can deep-link from a collection entity straight into a
filtered component view.

**Worked example:**

```yaml
# records/module_libraries.yaml
- entity_id: modlib:tycko-2025-compact-effectors
  type: module
  name: Tycko 2025 compact effector domains
  year: 2025
  description: >
    HT-recruit screen of compact activation and repression domains across
    multiple cellular contexts; 38 CD2 activation domains and 1,223 CD43
    repression domains.
  fate_axis: [with-what]
  organism: [human]
  assay: [HT-recruit]
  task: [effector-domain-discovery]
  status: active
  module_collection_ext:
    module_types: [ED]
    n_records: 1261
    dominant_validation_level: screen-validated
    assay_format: HT-recruit
    organism_scope: [human]
    integrated_in_ecr_lib: true
    ecr_lib_source_key: Tycko_2025
  links:
    - kind: supplementary
      url: https://www.nature.com/articles/s41587-024-02442-6
      label: Supplementary Table ST3
    - kind: dataset
      url: https://github.com/JimYuhaoWu/eCR_mod_lib
      label: integrated records (filter source_screen=Tycko_2025)
  papers:
    - paper_id: 10.1038/s41587-024-02442-6
      role: primary
```

---

## 7. Pipeline mapping (extends eCR_mod_lib pattern)

```
cfcr/
├── config/
│   └── sources.yaml              # external URLs, versions, DOIs  [same convention]
├── vocab/                        # NEW — controlled vocabularies
│   └── *.yaml
├── records/                      # NEW — human-curated source of truth, one file per type
│   ├── models.yaml
│   ├── benchmarks.yaml
│   ├── datasets.yaml
│   ├── protocols.yaml
│   ├── databases.yaml
│   └── module_libraries.yaml
├── literature/                   # SAME PATTERN as eCR_mod_lib
│   ├── papers.yaml               # master record of all assessed papers
│   ├── search_queries.yaml       # per-collection query configs
│   ├── 01_search.py              # PubMed + Semantic Scholar + bioRxiv + arXiv
│   ├── 02_triage.py              # score + emit review_YYYY-MM-DD.md
│   ├── 03_record.py              # validate review decisions
│   ├── candidates/               # git-ignored
│   └── reviews/                  # committed
├── scripts/
│   ├── schema.py                 # SQLite schema + CFCR class  [mirrors ModuleLibrary]
│   ├── 04_build.py               # assemble SQLite + exports
│   ├── 05_validate.py            # QC: enums, link rot, vocab candidates, tier derivation
│   ├── 06_embed.py               # NEW — sentence-transformers over title+abstract+description
│   └── 07_export_site.py         # NEW — flat JSON + embedding blob for GitHub Pages
├── db/
│   ├── cfcr.db                   # git-ignored
│   ├── entities.tsv              # committed snapshot — diffable
│   ├── papers.tsv                # committed snapshot
│   ├── entity_paper.tsv          # committed snapshot
│   ├── build_manifest.json       # provenance
│   └── qc_report.tsv
├── site/                         # GitHub Pages
│   ├── index.html
│   ├── data/entities.json        # flattened, denormalized
│   ├── data/embeddings.bin       # quantized float16
│   └── js/search.js              # BM25 + cosine + RRF, client-side
└── reports/
    └── vocab_candidates.md
```

**Weekly cadence** = `01_search` → `02_triage` → human review of
`reviews/review_YYYY-MM-DD.md` → `03_record` → `04_build` → `05_validate` →
`06_embed` → `07_export_site` → commit. Steps 4–7 run in CI on push.

---

## 8. Loader API (hides the schema)

```python
from cfcr import load, search

# Flat DataFrame, papers denormalized into a column
df = load(type="model")
df = load(type="model", organism="mouse", assay="ATAC-seq")
df = load(type="model", fate_axis="where", availability_tier="open-weights")

# The differentiating query
externally_validated = load(type="model", evidence_tier="externally-benchmarked")

# Protocols by trust level
protos = load(type="protocol", validation_tier="published-peer-reviewed")

# Evidence for one entity
load_papers("model:borzoi", role="critique")

# Hybrid search: BM25 + embeddings + RRF, with facet pre-filter
search("enhancer redundancy", type="model", organism="human", k=20)
```

---

## 9. Worked example records

```yaml
# records/models.yaml
- entity_id: model:borzoi
  type: model
  name: Borzoi
  aliases: [borzoi]
  year: 2023
  description: >
    Predicts RNA-seq coverage from DNA sequence as a unifying model of gene
    regulation; 524kb input context, successor to Enformer with higher
    resolution and RNA-seq output heads.
  fate_axis: [where]
  organism: [human, mouse]
  assay: [RNA-seq, DNase-seq, ChIP-seq, CAGE]
  task: [coverage-prediction, variant-effect-prediction]
  tags: [unet, calico, eqtl-prioritization]
  status: active
  supersedes: model:enformer
  model_ext:
    evidence_tier: externally-benchmarked   # derived; see §3.1
    availability_tier: open-source
    model_family: interval-model
    architecture: [cnn, transformer]
    input_type: genomic-interval
    input_context_bp: 524288
    output_type: [coverage-track, variant-effect]
    output_resolution_bp: 32
    n_parameters: 235000000
    genome_build: [hg38, mm10]
    license: Apache-2.0
  links:
    - kind: code
      url: https://github.com/calico/borzoi
    - kind: dataset
      url: https://huggingface.co/datasets/Genentech/borzoi-data
      label: training/val/test intervals
  papers:
    - paper_id: 10.1101/2023.08.30.555582
      role: preprint
    - paper_id: 10.1038/s41588-024-xxxxx
      role: primary
    - paper_id: 10.1101/2024.12.18.629121
      role: extension
      note: Flashzoi — see model:flashzoi
    - paper_id: 10.64898/2026.02.04.703796
      role: benchmark
      note: fine-mapping reproducibility vs GTEx/TOPMed/MAGE
```

```yaml
# records/protocols.yaml
- entity_id: protocol:lowinput-cutrun-v2
  type: protocol
  name: Low-input CUT&RUN for sorted MEF populations
  year: 2026
  description: >
    CUT&RUN adapted for 5,000–20,000 sorted cells, optimized for histone marks
    during MEF reprogramming timecourses.
  fate_axis: [where]
  organism: [mouse]
  cell_type: [mouse embryonic fibroblast]
  assay: [CUT&RUN]
  tags: [low-input, reprogramming, timecourse]
  status: active
  protocol_ext:
    validation_tier: lab-validated
    protocol_doi: 10.17504/protocols.io.xxxxx
    canonical_host: protocols.io
    version: "2.1"
    duration_hours: 30
    difficulty: moderate
    category: [cutrun, qc]
    origin: cfc-lab
```

---

## 10. QC checks for `05_validate.py`

- Every controlled column value resolves to a `vocab/` term or synonym
- Every `entity_paper.paper_id` exists in `papers.yaml`
- Every entity has ≥1 paper with `role='primary'` (exceptions whitelisted)
- `evidence_tier` derivation matches asserted value; flag author-overlap conflicts
- `supersedes` / `variant_of` resolve and contain no cycles
- Link rot sweep; update `link.alive` and `link.checked`
- Duplicate detection: fuzzy match on `name` + `aliases`
- Tag frequency → `reports/vocab_candidates.md`
- Orphan papers: in `papers.yaml`, attached to no entity

---

## 11. Deferred to v0.2

- `entity_relation` table (benchmark→evaluates→model, model→trained-on→dataset)
- Per-model benchmark *scores* (deliberately out of scope — index benchmarks,
  don't run them; GENEB owns evaluation)
- Contributor attribution table for collaborator credit
- Zenodo per-release DOI automation
- Multi-curator review workflow
