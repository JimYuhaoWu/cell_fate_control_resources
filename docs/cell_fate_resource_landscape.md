# Landscape Research: Curated Resource Hubs for Genomic / Cell-Fate Models

**Compiled:** 2026-10-16
**Purpose:** Reusable reference for designing a community resource (papers, models,
benchmarks, databases, datasets) around cell fate regulators and controllers.
**Owner context:** Research in chromatin accessibility & cell fate; maintainer of
`JimYuhaoWu/eCR_mod_lib` (engineered cell-fate regulator module library).

---

## 1. The two exemplar projects (the model being copied)

### Peldom/papers_for_protein_design_using_DL
- ~2.0k stars, 220 forks, 154 watchers, ~392 commits.
- **Structure:** a single large `README.md`. No workflows, no scripts, no database.
  Repo contains only: `.gitignore`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`,
  `LICENSE` (GPL-3.0), `README.md`, `cover.jpg`.
- **Update model:** entirely manual. A *"Papers last week, updated on YYYY.MM.DD"*
  block is pinned at the top and rewritten each cycle.
- **Staleness check (2026-10-16):** header read `updated on 2026.08.02` — ~10 weeks
  behind. **Key lesson: even the flagship exemplar, with 2k stars and an active
  contributor base, slips. Manual markdown curation decays.**
- **Taxonomy:** 8 top-level sections — (0) Benchmarks and datasets, (1) Reviews,
  (2) Model-based design, (3) Function to Scaffold, (4) Scaffold to Sequence,
  (5) Function to Sequence, (6) Function to Structure, (7) Other. Subsections are
  largely *by model architecture* (GAN-based, VAE-based, Diffusion-based, ...).
  Section 0 further splits into sequence benchmarks / structure benchmarks /
  databases / similar lists / guides.
- **Entry format (worth copying verbatim):**
  ```
  **Title**
  Author, Author, Author
  [venue/preprint](url) • [code](url) • [website](url) • [dataset](url) • [Supplementary](url)
  ```
  The `•`-separated resource links are what make it more useful than a bibliography.
  Preprint→journal transitions shown as `[bioRxiv ...](url)/[Nature (2025)](url)`.

### yangkky/Machine-learning-for-proteins
- ~1.7k stars, 219 forks, ~239 commits. The project Peldom credits as inspiration.
- Slightly more built out: has `.github/workflows`, `environment.yml`, `style.csl`
  (suggests CSL-based citation rendering in CI).
- Same content model: reverse-chronological entries within hand-maintained categories.
- Categories are application/model-type hybrids: Reviews, Tools and datasets,
  ML-guided directed evolution, Representation learning, Unsupervised variant
  prediction, Generative models, Biophysics, Predicting stability, etc.
- Explicitly states the format rule: within each category, newest first, link where possible.

---

## 2. Competitor / adjacent landscape (genomics side)

### Direct competitors — all stale or shallow

| Project | Scope | Status |
|---|---|---|
| `HelloWorldLTY/Awesome-DNA-Language-Modelling` | **Closest match.** Sections literally named "Sequence-to-functions" and "Language Modelling" | **Abandoned.** ~35 entries, nothing past 2024. No AlphaGenome, no Evo 2. Header typo ("Seuqnece"). States "Papers are ranked randomly." Uses shields.io badges + Semantic Scholar dynamic citation-count badges + GitHub star badges — nice format, dead content. |
| `ML4GLand/awesome-dl4g` (adamklie) | DL for genomics; modeled on `awesome-single-cell` | Good skeleton (software packages, model zoos, interpretability, datasets, tutorials), but **Models section is unfilled stubs** — Transformer contains only "Enformer"; Recurrent/Autoencoder/Generative are empty. Strong on tooling: Kipoi, Janggu, EUGENe, GOPHER, Selene, DragoNN, DeepAccess, kipoiseq, fastISM, yuzu, TF-MoDISco. |
| `apeterswu/Awesome-Bio-Foundation-Models` | DNA, RNA, protein, gene, single-cell | Reasonably maintained but DNA is one section among many. Shallow per-domain. |
| `rajeshgangireddy/awesome-digital-biology` | Protein design + genomics + single-cell FMs | Claims active maintenance; does cover AlphaGenome incl. community PyTorch port. Table format. Genomics is a slice of a very wide list. |
| `inoue0426/awesome-computational-biology` | Compbio generally | Has a "Genomics Foundation Models" subsection (DNABERT, Enformer, Basenji, Caduceus, Sei, GPN) — ~a dozen entries. |
| `hussius/deeplearning-biology` | All DL in biology | ~2,130 stars, 10 years old. Legacy reference, not current index. |
| `gokceneraslan/awesome-deepbio`, `cgreene/awesome-deepbio` | DL in compbio | Historic/dead. ~34 commits, entries stop in the 2010s. |
| `kexinhuang12345/ml-genomics-resources` | Companion to Cell Patterns survey (Huang et al.) | Static artifact of one paper. |
| `COLA-Laboratory/Awesome-RNA-Foundation-Models` | RNA only | **Not a competitor — a format to copy.** Continuously updated, dated entries (`2025.06`), one-line "what this contributes" summaries, abs/GitHub/HuggingFace links. |

### Perturbation side — OCCUPIED, and occupied well

- **`interp-extrap-perturb.readthedocs.io`** — living catalogue of **>152 single-cell
  perturbation methods**, with browsable website, methods count badge, and an
  "Add your method" contribution path. Backed by a perspective paper:
  Dimitrov*, Schrod*, Rohbeck & Stegle, *Nat Rev Genet* (2026),
  doi:10.1038/s41576-025-00920-4. Includes an ontology for modelling alterations
  and response.
  **→ This is exactly the "living website + paper" model. Do not compete here; link out.**
- `theislab/sc-pert` — community-maintained summary of perturbation models and
  datasets; originally curated for a Cell Systems 2021 paper. Includes dataset tables.
- `xianglin226/Benchmarking-Single-Cell-Perturbation` — table of perturbation models
  by year/journal (scGEN, CellDrift, CellOT, scDisInFact, PertAdapt, X-Cell...).
- `OmicsML/awesome-deep-learning-single-cell-papers` and
  `OmicsML/awesome-foundation-model-single-cell-papers` — single-cell lists.

### Benchmarks — crowded and consolidating fast

- **GENEB** (`darlednik/GENEB`, ICML 2026) — 40 genomic foundation models ×
  100 tasks × 13 functional categories, unified probing protocol. HuggingFace Space
  leaderboard; leaderboard artifacts built by CI from reviewed submissions, not
  hand-edited. Headline finding: *aggregate leaderboards are unstable; rankings
  vary sharply across task categories; scale gives modest/inconsistent gains.*
- **BEND** (ICLR 2024, Marin et al.) — biologically meaningful genome-annotation
  tasks: chromatin accessibility, histone modification, CpG methylation, variant
  effects. Finding: DNA LM embeddings approach expert methods on some tasks but
  capture limited long-range information.
- **DART-Eval** (NeurIPS 2024 D&B, Patel/Singhal/Kundaje) — regulatory-DNA focused;
  zero-shot / probed / fine-tuned vs ab initio baselines; 1,443 TFs analyzed.
  Finding: annotation-agnostic DNALMs inconsistent, no compelling gain over baselines.
- Others: GUANinE, DNALongBench (Nat Commun 2025), Genomics Long-Range Benchmark (LRB),
  OmniGenBench, GUE (DNABERT-2), Genome-Factory (arXiv 2509.12266), GenomeHarness.
- **Implication: list benchmarks, do not run them.** Producing numbers is a different,
  far more expensive business, and GENEB already owns it.

### Model zoos / frameworks — occupy the "database of models" axis

- **Kipoi** — API + repository of ready-to-use trained genomics models.
- **gReLU** (Lal, Gunsalus, Nair, Biancalani, Eraslan; *Nature Methods* 2025) —
  comprehensive framework for DNA sequence modeling and design.
- **CREsted** — model zoo incl. ported Borzoi/Enformer weights with documented
  genome build, input/output shapes, parameter counts, licensing.
- HuggingFace collections (Nucleotide Transformer, SegmentNT, InstaDeep, etc.).
- `Genentech/enformer-data`, `Genentech/borzoi-data` on HF — the actual training/val/test
  genomic intervals as TSV (38,171 human / 33,521 mouse for Enformer;
  55,497 / 49,369 for Borzoi).

---

## 3. Key model families to cover (seed list for backfill)

**Sequence-to-function / sequence-to-omics (S2O):**
DeepBind, DeepSEA, Basset, Basenji, DanQ, Sei, Enformer, Borzoi, Flashzoi,
AlphaGenome, ChromBPNet, scBasset, EpiGePT, EPInformer, DeepMEL, DeepFlyBrain,
maxATAC, AtacWorks, SPACE.

**DNA/genome language models:**
DNABERT, DNABERT-2, DNABERT-S, Nucleotide Transformer (+SegmentNT), HyenaDNA,
Caduceus, GENA-LM, GPN, GPN-MSA, Evo / Evo 2, LucaOne, DNAGPT, MutBERT,
Omni-DNA, GenomeOcean, GROVER, species-aware DNA LM.

**Critical evaluation literature (the "does it actually work" thread):**
- "Current approaches to genomic deep learning struggle to fully capture human
  genetic variation" — Nat Genet
- "Benchmarking of deep neural networks for predicting personal gene expression
  from DNA sequence highlights shortcomings" — Nat Genet
- "Personal transcriptome variation is poorly explained by current genomic deep
  learning models" — Nat Genet
- "Interpreting cis-regulatory interactions from large-scale deep neural networks" — Nat Genet
- "Enformation Theory: A Blueprint for Evaluating Deep Learning Models in Genomics" — bioRxiv
- "Practical utility of sequence-to-omics models for improving the reproducibility
  of genetic fine-mapping" (AlphaGenome/Borzoi/Enformer/Sei vs GTEx/TOPMed/MAGE) — bioRxiv 2026

---

## 4. Conclusions carried forward

1. **The gap is real.** No actively maintained, current, deep index exists for
   sequence-to-function / genomic interval models. The one person who attempted
   that exact scope abandoned it circa 2024 — before AlphaGenome, Evo 2, and the
   current benchmark wave.
2. **The field is growing fast**, so a website + paper is justified, not premature.
3. **Perturbation modelling is taken** (Stegle group, Nat Rev Genet 2026).
   Include as a deliberately shallow adjacent section that points outward.
4. **Benchmarks: index, don't evaluate.**
5. **Do not hand-maintain markdown.** Structured records (YAML/SQLite) as source of
   truth; generate README + website from them. This is what makes weekly cadence
   survivable and what makes "database" an honest word.
6. **Automate discovery, not inclusion.** Candidates into a review queue; human
   approves. Curation *is* the product.
7. **Backfill is the dominant cost**, not the weekly cadence.

---

## 5. Existing internal asset: `JimYuhaoWu/eCR_mod_lib`

Already implements most of the recommended architecture — **reuse, don't rebuild.**

- **Content:** ~10,800 records (DBD ~3,250 / ED ~7,700 / CR ~540) for engineered
  transcription factor design. Snapshot date 2026-05-30.
- **Validation-level vocabulary** (directly reusable as a quality tier concept):
  `screen-validated`, `ChIP-validated`, `motif-only`, `predicted`, `structurally-resolved`.
- **Architecture already in place:**
  - `config/sources.yaml` — all external URLs, versions, DOIs
  - `literature/papers.yaml` — master record of all assessed papers (accept/reject decisions)
  - `literature/search_queries.yaml` — PubMed + Semantic Scholar queries
  - `literature/01_search.py` → `02_triage.py` (scores candidates, emits
    `reviews/review_YYYY-MM-DD.md`) → `03_record.py` (validates review decisions)
  - `scripts/schema.py` — SQLite schema + `ModuleLibrary` class
  - Build provenance: `build_manifest.json`, `download_manifest.json` (checksums),
    `qc_report.tsv`, timestamped logs
  - Dual output: SQLite (git-ignored) + committed TSV snapshot (enables `git diff`)
  - Installable as a Python package (`ecr_mod_lib`), `load()` with filters
- **Literature cadence:** currently every 1–3 months (not weekly).
- **Established rejection patterns** (auto-filtered by triage scorer): inhibitor/drug
  studies, cancer biology without domain characterization, synthetic lethality,
  non-human/mouse organisms, reviews & book chapters, assembly/stoichiometry screens,
  RAS/signaling effector domains.
- **Related:** `JimYuhaoWu/eCR_predictor` — predicts DBD binding candidates for a
  given DNA sequence; depends on this library.

**→ The paper-collection project should be a sibling collection under the same
pipeline pattern (sources.yaml → search → triage → papers.yaml → build → snapshot),
not a new codebase.**

---

## 6. Open design questions

- Final naming / umbrella brand (see naming discussion).
- Backfill start year and whether co-maintainers are recruited from day one.
- Whether to narrow to chromatin accessibility & regulatory elements (where domain
  judgment is strongest) vs. all of sequence-to-function.
- Search layer: metadata facets + BM25 + embeddings; client-side vs. hosted.
- Hosting/DOI strategy if pursuing a database paper (Zenodo per release).
