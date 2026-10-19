# CFCR roadmap

Milestones are defined by **exit criteria, not dates** — the backfill is the
dominant cost and its rate is unknown until it starts, so a date on M4 would be
invented. Add due dates once M3 has run a few cycles and the real throughput is
visible.

Each milestone is also a GitHub milestone, so issues can be filed against it.

---

## M1 — v0.1 skeleton ✅ done

The data model, proved against enough real records to find its own gaps.

- [x] SQLite schema + `CFCR` class mirroring `eCR_mod_lib`'s `ModuleLibrary`
- [x] Six controlled vocabularies, ontology ids verified against EBI OLS4
- [x] 20 seed entities across all six types; 30 papers, every DOI API-verified
- [x] `04_build.py`, `05_validate.py`, `cfcr.load()` / `load_papers()`
- [x] Packaging, MIT code licence, CC-BY-4.0 metadata licence
- [x] Reproducible build: migrated and fresh databases emit byte-identical snapshots

**What it cost to learn:** five spec gaps, all recorded in
[`reports/seed_flags.md`](reports/seed_flags.md) — the `architecture` enum had
no GNN term, `cell_type` cannot be CL-only, `n_parameters` could not represent
a model family, `protocol_ext.category` ships no vocabulary, and `vocab.facet`
cannot be a DDL enum at all.

## M2 — public website on GitHub Pages ✅ merged, first deploy pending

Merged to `main` as PR #1 (`0ae3c73`). Pages is enabled and set to build from
Actions, but no deploy has gone green yet — the first run failed because Pages
had not been enabled when it fired, and the re-run is the one step left.

- [x] `scripts/07_export_site.py` → `site/data/{entities,facets,papers}.json`
- [x] `fate_axis` as primary navigation, not a sidebar filter
- [x] `evidence_tier` badge on every model card, evaluating papers listed under it
- [x] `availability_tier` shown as orthogonal to evidence, with the licence visible
- [x] Faceted filtering; works at phone width
- [x] Client-side BM25, ranker written so a second scorer can slot in
- [x] GitHub Actions deploy from `site/` — *not* `/docs`, which holds the design docs

**Exit:** a stranger can answer "which interval models has anyone outside the
authoring group evaluated, and can I legally use the weights" without reading
any YAML. Met in the page itself; it stops being theoretical once the deploy
goes green.

**What it cost to learn:** the evidence badge and the list under it were built
from different sets of paper roles. The list accepted `review` and `extension`
alongside `benchmark` and `critique`, while `05_validate.py` derives the tier
from the latter two alone, so `model:gears` rendered a `self-reported` badge
directly above a review captioned "Evaluated by:", and `model:borzoi` counted
Flashzoi — its own derivative — as an outside check. The site contradicted the
one question CFCR exists to answer, on the card that advertises the derivation
as auditable. Fixed in `1348156` by reading both from one constant; the two
roles stay in the evidence trail, where they are related work rather than
evaluations. A derived field is only as trustworthy as the least careful place
that re-derives it.

### Blocker found while building M2: entity links were not exported ✅ resolved

`04_build.py` wrote all 29 `link` rows into the SQLite `link` table, but the
committed snapshots were only `entities.tsv`, `papers.tsv` and
`entity_paper.tsv` — so the loader could not see links at all, and the site
could link to papers but not to a single resource. Affected: 11 `code`,
6 `dataset`, 4 `website`, 2 `weights`, 2 `api`, 2 `supplementary`,
1 `container`, 1 `docs`.

This mattered more than its size suggested: those links are what make such an
index more useful than a bibliography — without them CFCR *is* the
bibliography it set out not to be. It was a gap in the original
spec, which named three snapshots, not a slip in the build.

Two ways to fix, and the choice was not obvious:

- **A fourth snapshot, `db/links.tsv`.** Consistent with `entity_paper.tsv`,
  keeps the per-link `checked` and `alive` columns where the link-rot sweep
  writes them, and gives one diff line per link. Costs the loader a join.
- **Inline into `entities.tsv` as a JSON `links` column.** One file, no join,
  one fetch for the site. But it duplicates the `link` table's shape, and
  `alive`/`checked` churn would then rewrite entity rows on every sweep.

Taken: the fourth snapshot, on the link-rot argument — the sweep rewrites link
state on a schedule, and that should not touch entity rows. `c35a985` added
`db/links.tsv` and `cfcr.load_links()`; `690a435` put the links on the cards,
where 19 of the 20 entities now carry at least one. `checked` and `alive` are
deliberately not exported to the site: the sweep has never run, so every value
would be unknown. Closed as issue #2.

## M3 — literature pipeline

Adapted from `eCR_mod_lib` rather than written fresh.

- [ ] `literature/01_search.py` — PubMed + Semantic Scholar + bioRxiv + arXiv
- [ ] `literature/02_triage.py` — score candidates, emit `reviews/review_YYYY-MM-DD.md`
- [ ] `literature/03_record.py` — validate review decisions back into `papers.yaml`
- [ ] `search_queries.yaml` per collection; reuse the established rejection patterns
- [ ] Retry-with-backoff on every API call

**Exit:** one cycle runs end to end and a human approves or rejects a real
candidate list. Discovery is automated; inclusion stays a human decision.

**Already learned the hard way:** a single dropped request silently nulls an
author list, and `evidence_tier` is derived from author lists. Retries are not
optional. arXiv rate-limits; Crossref omits abstracts for Nature-family journals
where Europe PMC has them.

## M4 — backfill wave 1

The dominant cost of the whole project.

- [ ] Interval models: the Basenji→Enformer→Borzoi line, Sei, ChromBPNet, scBasset, EpiGePT
- [ ] DNA LMs: DNABERT family, HyenaDNA, Caduceus, GENA-LM, GPN/GPN-MSA, Evo, GROVER
- [ ] The critical-evaluation thread — the `critique` papers are the differentiator, so backfill them *with* the models, not after
- [ ] Benchmarks: GUANinE, DNALongBench, LRB, OmniGenBench, GUE
- [ ] Module collections to ~15–30 entities, each keyed back to `eCR_mod_lib`
- [ ] First vocabulary promotion pass once tags clear the ≥10-record threshold

**Exit:** ~150 entities, and `reports/vocab_candidates.md` fires for the first
time, which means the bottom-up vocabulary mechanism has actually been exercised.

**Scope decision still open:** narrow to chromatin accessibility
and regulatory elements, where domain judgment is strongest, or cover all of
sequence-to-function. Worth settling before this milestone, not during it.

## M5 — hybrid search

Deliberately gated on M4. Deferred from M2 on purpose: with 20 records there is
no way to measure whether embeddings beat BM25, and the dependency plus a
shipped binary blob are not yet earned.

- [ ] `scripts/06_embed.py` — `sentence-transformers` over title + abstract + description
- [ ] Quantized float16 blob in `site/data/embeddings.bin`
- [ ] Reciprocal rank fusion against the existing BM25 ranker
- [ ] A/B the two rankers on real queries before keeping both

**Exit:** a query like *"enhancer redundancy"* surfaces a relevant record that
uses none of those words, and the comparison against BM25 alone is written down.

## M6 — v0.2 schema

Everything schema §11 deferred, plus what M1 and M4 turn up.

- [ ] `entity_relation` table (benchmark→evaluates→model, model→trained-on→dataset),
      replacing the `benchmarked_on` and `training_data` free-text columns
- [ ] `model_variant` child table — one row per checkpoint. The `n_parameters`
      min/max range is a stopgap; NT's 50M and 2.5B checkpoints differ in what
      they are good for, and a range cannot say that
- [ ] Decide `protocol_ext.category`: give it a vocabulary or demote it to free text
- [ ] Contributor attribution table, for crediting co-maintainers
- [ ] Per-paper curator override on the `evidence_tier` author-overlap threshold,
      if the backfill shows the global 50% rule misfiring

## M7 — citable release and database paper

- [ ] Zenodo integration, DOI per release
- [ ] CITATION.cff
- [ ] Co-maintainer recruitment
- [ ] Database paper draft

**Exit:** CFCR is citable, and someone other than its author has merged a record.

---

## Building locally

```bash
git clone <this repository>
cd cell_fate_control_resources
conda env create -f environment.yml && conda activate cfcr
pip install -e .
python -c "from cfcr import load; print(load(type='model')[['entity_id','evidence_tier']])"
```

Querying needs nothing but the committed TSVs in `db/`. Rebuilding them needs
no network:

```bash
python scripts/04_build.py        # records/ + vocab/ + papers.yaml -> SQLite -> TSV
python scripts/05_validate.py     # QC; exits 1 on any ERROR
python scripts/07_export_site.py  # site/data/*.json for the published site
```

`scripts/05_validate.py --check-links` additionally sweeps every catalogued URL.
Run it from a host with unrestricted outbound access: a connection-level
failure leaves a link's `alive` unknown rather than false, precisely so a
restricted network does not record false link rot.
