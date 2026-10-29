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

## M2 — public website on GitHub Pages ✅ done, live

Merged to `main` as PR #1 (`0ae3c73`); the first deploy went green and the site
has been live at <https://cellfatecontrol.com> since. The workflow re-runs the
exporter on every push and fails if the result differs from what is committed,
so a curation change that forgets `scripts/07_export_site.py` cannot keep
serving the previous export silently.

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

## M3 — literature pipeline ✅ built, one real cycle run

Adapted from `eCR_mod_lib` rather than written fresh.

- [x] `literature/01_search.py` — Europe PMC + arXiv for discovery, OpenAlex for citations
- [x] `literature/02_triage.py` — score candidates, emit `literature/reviews/review_YYYY-MM-DD.md`
- [x] `literature/03_record.py` — validate review decisions back into `papers.yaml`
- [x] `literature/search_queries.yaml` per collection, every query run against the live APIs
- [x] Retry-with-backoff on every API call
- [x] `literature/04_audit.py` — sample what the pipeline decided alone and measure it

**Exit:** one cycle runs end to end and a human approves or rejects a real
candidate list. Discovery is automated; inclusion stays a human decision.
**Met mechanically** — a cycle produced 464 discovery candidates and 6,994
citing works, triage wrote a review file, and recording four ticked decisions
took the catalogue to 22 entities and 155 papers with QC still at 0 errors. The
human half is not met until someone works a real review file through, which is
M4's first task rather than this one's.

**What a cycle costs a human, which is the number that mattered.** The first
review file asked for **769 decisions**, which is not a review, it is a wall.
Four changes brought that down, each measured rather than argued:

| | asked | recorded without a decision |
|---|---|---|
| first cycle | 769 | 0 |
| ask only where a tier can move | 620 | 149 |
| query fixes, cap 100, defer low scorers | 478 | 351 |
| tables for the four blind entity types | 518 | 351 |

The last row goes up on purpose: covering `dataset`, `protocol`, `database` and
the `what` axis took catalogued entities scoring below 3.0 on their own primary
paper from 6 of 19 to 1 of 19, and found 21 perturbation-model candidates that
had been falling below the line. Recall bought with questions.

**The limit, measured so it is not re-argued.** A score cannot decide admission
at any threshold: at ≥ 3.0 it retains 17 of 29 curated resources, at ≥ 8.0 nine
of them. It ranks; it does not classify, and scope has no ground truth to
classify against — the rule is prose in `README.md`. The one judgement that is
safely automatable is the one with a derivation behind it: `evidence_tier`, from
author overlap. That is why role proposals are routed by whether they can move
a tier and nothing else is decided for the curator, and why `04_audit.py`
exists — automating more has to be earned with a measured error rate rather
than asserted.

**Already learned the hard way, the second time:** `arXiv` 429s for longer than
four retries, and a source that fails must not take the run with it. One
exhausted request used to discard a whole cycle; both halves now cache as they
fetch and a failed source is recorded in the candidates file instead of fatal.

**Sources — decided.** Four APIs, one job each, recorded with their reasons in
`config/sources.yaml`. Europe PMC and arXiv do discovery, OpenAlex supplies the
citation graph, Crossref resolves DOIs. This replaces the PubMed + Semantic
Scholar + bioRxiv + arXiv list this milestone was first written with, for three
measured reasons:

- **PubMed and bioRxiv are subsumed.** Europe PMC holds every PubMed/MEDLINE
  abstract and indexes 31+ preprint servers including bioRxiv and medRxiv. More
  decisively, bioRxiv's API has no keyword search endpoint — date-range listing
  only, 30 records a call — so searching it directly means crawling a window
  and filtering locally.
- **arXiv is not subsumed.** BEND (arXiv:2311.12570, ICLR 2024) is already a
  `benchmark` record here and returns no match in Europe PMC. The ML venues are
  where the `how` axis lives, so this is a standing gap, not an edge case.
- **Semantic Scholar loses to OpenAlex at the one job it was there for.** Asked
  for the two catalogued critiques of Enformer, OpenAlex returned each in one
  filtered call; keyless Semantic Scholar gave a null citation count, found one
  of the two inside the first 1,000 of 1,325 citations, and did not have BEND.

**Settled with it.** Three things M3 could not start without:

- **`requests`, in an extra rather than the package.** eCR_mod_lib's pipeline
  already retries on a plain `requests.Session` — three attempts, `Retry-After`
  honoured, `2**n` backoff — so matching it beats porting to `httpx` or a retry
  library. It is `pip install -e ".[literature]"`, not a runtime dependency of
  `cfcr`, because querying the committed snapshots touches no network and the
  README says so. Worth fixing while adapting: that `_get` returns `None` on
  total failure, which is precisely how a dropped request nulls an author list.
- **`literature/reviews/` is committed; `literature/candidates/*.json` is not.**
  The raw dumps are bulky and reproducible. The review file is neither: it is
  the only record of which candidates a human rejected and why, and a rejection
  that is not written down returns as a candidate every cycle. The roadmap said
  `reviews/` and `.gitignore` said `literature/candidates/`; both now agree with
  eCR_mod_lib's layout.
- **`literature/search_queries.yaml` exists**, eight collection queries keyed to
  Europe PMC and arXiv instead of the sibling's PubMed and Semantic Scholar. All
  fifteen were run against the live APIs before being committed, and the
  measured breadth is recorded in the file — including the two queries that are
  visibly mistuned and are left that way until `02_triage.py` can say what good
  looks like.

The reason a citation source is on the list at all: **no keyword query finds a
paper that criticises a model.** `critique` is the role the whole evidence layer
rests on, and it is discovered by walking the citations of the primary paper.
That makes `02_triage.py`'s hardest decision — which citing papers are
evaluations — the thing to design before writing `01_search.py`, because it
determines what the search step has to fetch.

**Already learned the hard way:** a single dropped request silently nulls an
author list, and `evidence_tier` is derived from author lists. Retries are not
optional. arXiv rate-limits; Crossref omits abstracts for Nature-family journals
where Europe PMC has them.

## M4 — backfill wave 1 ⚠️ breadth met threefold, depth not met

The dominant cost of the whole project.

- [x] Interval models: the Basenji→Enformer→Borzoi line, Sei, ChromBPNet, scBasset, EpiGePT
- [x] DNA LMs: DNABERT family, HyenaDNA, Caduceus, GENA-LM, GPN/GPN-MSA, Evo, GROVER
- [x] The critical-evaluation thread — the `critique` papers are the differentiator, so backfill them *with* the models, not after
- [x] Benchmarks: GUANinE, DNALongBench, LRB, OmniGenBench, GUE
- [x] Module collections to ~15–30 entities, each keyed back to `eCR_mod_lib` — 58, above the range
- [ ] First vocabulary promotion pass once tags clear the ≥10-record threshold

**Exit:** ~150 entities, and `reports/vocab_candidates.md` fires for the first
time, which means the bottom-up vocabulary mechanism has actually been exercised.

**Half met, and the unmet half is the one that mattered.** 489 entities
published — 319 models, 91 benchmarks, 58 module collections, 9 datasets, 7
databases, 5 protocols — against a ~150 target and a ~300-400 ceiling, so the
entity count is not the open question any more. `vocab_candidates.md` still
does not fire: a tag needs ≥10 records and only the 20 hand-curated seeds carry
tags at all, because `07_enrich.py` deliberately refuses to generate them. The
vocabulary mechanism is therefore still unexercised, which is what this
milestone was actually for.

**Measured on 2026-10-26, and the reason M4 does not close:** the backfill
bought breadth by spending depth, and the fields it left empty are the ones the
NAR argument rests on.

| field | populated |
|---|---|
| year | 489/489 |
| `fate_axis` | 404/489 |
| description | 186/489 |
| license | 37/489 |
| tags | 20/489 |
| **`evidence_tier`** | **8/489** |
| `availability_tier` | 8/489 |

472 of the 489 hold only their own primary paper; all 291 `benchmark`/`critique`
papers sit on 16 records. Median populated fields per card is 11, against 32 for
the 20 seeds curated by hand. So the evidence layer — named below as the
differentiator and the general-interest claim — exists on 16 records, and the
faceted query M2's exit criterion promises ("which interval models has anyone
outside the authoring group evaluated, and can I legally use the weights") is
answerable for the handful of cards that carry both fields.

**The next phase is depth on 489, not more breadth.** Kipoi already holds
2,000+ and the Stegle catalogue 156; breadth does not win the argument and
never did. See **M4a** for what has to happen first.

## M4a — the boundary, before any further expansion

**Decided 2026-10-27.** Expanding the corpus further is on hold until the
boundary is written down as criteria rather than prose, because two facts are
the same fact:

- A score cannot decide admission at any threshold — at ≥3.0 the discovery
  score retains 17 of 29 curated resources, at ≥8.0 nine of them.
- Nobody could say how far the backfill drifted. The 9 published records that
  were known to be out of scope — video question answering, MRI, wastewater,
  protein contact maps — were found by eye, not by a check.

CFCR has an *intensional* boundary (the prose rule in `README.md`, plus the
per-axis table below) and no *extensional* one: no labelled set of in/out
decisions that any rule, human or scored, could be measured against. That
absence is why scope cannot be automated **and** why drift cannot be detected.

**Measured 2026-10-28, and it is not 9 records.** `docs/scope_criteria.md`
states the boundary as five criteria decidable from a title and an abstract;
`literature/scope_labels.yaml` labels **all 490 records** against them, and
`reports/scope_audit.md` is the summary. **170 records are clearly out of scope
and 227 are out including the arguable cases: 34.7% and 46.3%.**

So the estimate the hold was placed on was wrong in the reassuring direction.
A ~2% admission error was the assumption and nine records were the evidence;
the real figure is seventeen to twenty-three times that. The differentiator
CFCR argues for publication is precisely that its boundary is tighter than a
count-driven list's.

Three things the labelled set says that the prose rule could not:

- **The drift is concentrated in `benchmark` and `module`, and they drifted for
  different reasons.** Out of scope: 67 of 91 benchmarks (74%), 42 of 58
  modules (72%), 118 of 320 models (37%), and **none** of the 21 datasets,
  databases and protocols. Benchmarks came in on keywords — the discovery
  queries match *benchmark*, *foundation model*, *sequence* and *expression*,
  and a video question-answering benchmark matches all four. Modules came in on
  subject matter: the `with-what` backfill admitted chromatin- and
  cancer-biology **findings** about regulators instead of **collections** of
  them, which is a C1 failure, not a C2 one, and no keyword list would have
  caught it.
- **85 of the 91 `benchmark` records carry an empty `fate_axis`** — while all
  405 records of every other type carry one. `README.md` already says a
  benchmark is in scope only when it serves an axis that is in scope and
  inherits that axis, so the field that records admissibility was never filled
  for the one type where admission went wrong. The rule was in force on paper
  and unapplied in fact.
- **A second kind of error the criteria deliberately do not catch:** 44 records
  are in scope and entered under the wrong type — 23 benchmarks typed as
  `model`, 8 critiques entered as entities rather than as `entity_paper` rows,
  10 resources entered twice, 3 datasets or databases typed as models.
  Critiques are the costly case: entered as an entity, one mistake inflates the
  model count *and* withholds the evaluation from the model it is about, which
  is the evidence layer the whole argument rests on. And `model:dnabert-2` is
  not DNABERT-2 — its primary paper is a colorectal enhancer application, while
  the real DNABERT-2 paper sits under `benchmark:dnabert-2`.

At 490 entities a 35% admission error is 170 records, found in a day. At
several thousand it is invisible and uncorrectable.

- [x] Inclusion and exclusion criteria, written as criteria — needed for
      publication regardless, since a database on a narrow topic has to argue
      its boundary to the wider readership. `docs/scope_criteria.md`: C1 a
      resource not a result, C2 a genomic substrate, C3 acting not observing,
      C4 a nameable in-scope axis, C5 `what` stays shallow
- [x] A labelled in/out set to measure them against —
      `literature/scope_labels.yaml`, now all 490 records. A seeded random
      sample of 102 was labelled first, blind to the rest, and is kept: it
      estimated 47.1% out where the full pass found 46.3%, so the next audit
      need not be exhaustive. The labels are unratified, since a scope decision
      is the curator's to make
- [x] Measure the current 490 against the criteria, and record the drift rate —
      `reports/scope_audit.md`. 170 clearly out, 227 including arguable cases,
      and every record named. 86 labels are `arguable`, and they cluster into
      four questions: whether `how` covers sequence design that is not fate
      control, whether an in-scope model used to produce a finding is a
      resource, whether genotype-based expression imputation has a genomic
      substrate, and when a single-cell foundation model counts as predicting a
      response. Settling those four settles most of the 86
- [x] A demote path — `literature/09_demote.py`, the mirror of 06_promote.py:
      it writes a review file from the labels, and `--apply` reads the ticks
      back. Not to `review_state: unreviewed`, which is what this item
      originally said: `unreviewed` means nobody has looked yet, and
      06_promote.py collects every one of those into the queue of records
      awaiting a decision, so demoting 170 records there would park them in
      that queue for good. They get a third state, `withdrawn`, with the
      criterion in `withdrawn_reason`. The record stays in `records/`, in `db/`
      and in the snapshots, so a curator who disagrees restores it by deleting
      two lines, and a withdrawal also writes `rejected` against the primary
      paper in `literature/decisions.yaml` — without which the next discovery
      cycle proposes it again under a new slug, which is how both Grover 2025
      and Grover 2026 came to exist

**Exit:** the criteria exist, and the admission error rate of the current
catalogue is a number rather than an impression. Both hold: the number is 34.7%
clear and 46.3% wide, with every record named in
`literature/scope_labels.yaml`, and all four items are done.

**Done, including the withdrawal and the boundary cases.** On 2026-10-28 the 170
`clear` records were withdrawn, then the 86 `arguable` labels were settled by
five decisions (`docs/scope_criteria.md`) and the 69 further records they
confirmed were withdrawn too — `demote_2026-10-28.md` and
`demote_2026-10-28_settled.md` are the worked files. **239 withdrawn, 250
published.** QC holds at 0 errors and the warning count fell from 98 to 31.

Nothing was deleted: all 490 records remain in `records/`, in `db/` and in the
snapshots, each carrying the criterion that took it off the site, and deleting
two lines puts one back.

No label is `arguable` any more. The five decisions are D1 a conclusion is not a
resource (42 labels), D5 observation stays out even when an in-scope model does
the observing (19), D3 the substrate must be read rather than inferred (11), D4
a claimed capability rather than an evaluated task (10), and D2 `how` is bounded
by fate control rather than by sequence design (4). Each is reversible, and
`settled_by` in the labels file names which labels rest on which, so disagreeing
with D1 costs re-reading 42 of them rather than all 490.

D1 withdrew records that are evidence rather than resources, including two
critiques. Attaching those as `entity_paper` rows is the other half of that fix
and is **not done** — tracked in the type-defect issue, and it matters because a
critique entered as an entity inflated the model count and starved the evidence
layer with one mistake.

**Tradeoff, decided.** A tighter boundary sharpens the novelty argument; a wider
one narrows the gap with Kipoi's count. Tight was chosen, because the
differentiator is the evidence layer and Kipoi already won on count and lost on
evidence.

**Scope — decided.** CFCR indexes resources you act with, not resources you
observe with; see the scope section in `README.md` for the full rule. In
practice: `where` and `how` deep (including 3D genome contact prediction),
`what` shallow and pointing outward (a single-cell foundation model qualifies
when it predicts a perturbation response, not when it only embeds cells),
trajectory inference and RNA velocity out.

**The ~300-400 target below was the original estimate. The catalogue passed it,
and then M4a's withdrawals took it under.** 489 were published; 239 out-of-scope
records were withdrawn on 2026-10-28, leaving **250**. A record can carry more
than one axis, so the column sums above the total:

| axis | estimated | at 489 | published now |
|---|---|---|---|
| `where` | ~125-175 | 166 | 97 |
| `how` | ~60-80 | 78 | 45 |
| `what` | ~15-25 | **105** | **77** |
| `with-what` | ~15-30 | 61 | 19 |

So the overshoot at 489 was mostly drift, which the labels say plainly: 74% of
benchmarks and 72% of modules were out of scope, against 41% of models.

**But the catalogue is now under its target, not over it.** 250 against
~300-400, with `where` at 97 and `how` at 45, both below their ranges. That is
the cost of a boundary this tight, and it is the next real problem: this file
records that content scale, not the website, gates the NAR submission. M4a held
expansion until the boundary existed. It exists, so the hold has done its work,
and what the catalogue needs now is growth measured against criteria rather than
against a keyword.

`what` is the one axis still over its range, at 77 against ~15-25, and D4 is
what holds it there rather than any looseness: perturbation-response prediction
turned out to be a large and active literature, and the axis was called shallow
when the catalogue held twenty of them. **That estimate is the number to revise,
not the labels.**

The original estimate, for reference:

| | |
|---|---|
| `where` | sequence-to-function ~80-120 · 3D genome ~15-25 · accessibility ~30 |
| `how` | DNA language models ~60-80 |
| `what` | ~15-25, shallow |
| `with-what` | module collections ~15-30 |
| serving them | benchmarks ~25-40 · datasets ~40-60 · protocols ~10-20 · databases ~15-25 |

The differentiator is the evidence layer, not the taxonomy: no other resource
records whether a genomic/epigenomic deep-learning model has been
independently evaluated, or whether its weights can legally be reused.

**Hold lifted 2026-10-29, and the first cycle says the queries are spent.** A
discovery-only run under the encoded criteria returned 222 candidates new to
`papers.yaml` and **17 new to the pipeline**: 172 of the 191 in the review file
had been deferred by an earlier cycle, 31 more were suppressed as rejected.
Five cleared the boundary and all five are out of scope on
`docs/scope_criteria.md` — promoter design for gut commensals, metagenomic
taxonomy, expression from H&E images, a domain-agnostic active-learning method,
and a cis-regulatory evolution map built with AlphaGenome.

So the gap to ~300-400 does not close by re-running the eight queries, and the
corpus they have not reached is measured rather than guessed: Europe PMC holds
**298 hits past the 100-result fetch cap**, 287 of them on `interval_models`
(`where`, 164 unreached) and `dna_language_models` (`how`, 123) — the two axes
below their ranges. The other five Europe PMC queries reach their corpus
completely. Paging past the cap was rejected on 2026-10-21 because the scoring
would have handed a curator noise at that volume; §1.7 of
`docs/triage_design.md` is what changed, and §1.8 carries both measurements.

**Paged on 2026-10-29, same day, and the tail held the founding papers.**
`search_europepmc` now pages with `cursorMark` and the cap is 300, so the 298
were fetched. The review file went from 5 decisions to 97, and banding each
candidate by its rank in its own query gives 4 above the boundary in ranks
1-100 against 92 in ranks 101+. After removing 10 preprint DOIs of papers
already catalogued, 8 title duplicates and 1 already in the ledger, **73
genuinely new papers clear the boundary and 24 of them are in scope**, against
0 of the 4 the first 100 ranks produced.

The head is picked over, which is why its rate is low -- 29 of its 178 are
suppressed as already rejected against 2 of the tail's 250 -- so this is a
backlog draining and not a rate the next cycle inherits. Two of the 24 settle
the question on their own: Basenji2 and GROVER, at ranks 236 and 219, neither
of which has a paper in `papers.yaml` or a record, on two lines M4 ticks as
done. §1.9 of `docs/triage_design.md` carries the measurement.

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

**`entity_relation` is what a relationship map needs, and the map is what the
table is for.** Raised 2026-10-27: a graph of citing/cited, benchmarked-on and
database-used relationships, as navigation over the catalogue. It is blocked
here rather than on any drawing library, because the edges do not exist —
`benchmarked_on` is populated on **0 of 490** records, `training_data` on 1,
`supersedes` on 1, `variant_of` on 1. Entity↔entity relationships in CFCR are
not thin, they are absent; the only populated graph is entity↔paper, 799 edges
of which 291 are `benchmark`/`critique`. Designing the table against a
visualization that has to be drawn beats designing it in the abstract, so the
two should be done together.

**Graph indicators are deferred on purpose, not forgotten.** A clustering
coefficient or any centrality measure computed on this catalogue would measure
the catalogue's sampling, not the field: with 472 of 489 entities holding one
paper and 16 holding every evidence edge, centrality reports that Enformer is
the centre of regulatory genomics — true of the sweep order, false about the
world. That is the M2 evidence-badge failure again, where two code paths
re-derived one thing and the card contradicted the claim it advertised as
auditable. A number that is real and whose interpretation is false is worse
than no number, because it looks like a finding. **Gate: no graph indicators
until the evidence edges stop being concentrated on 3% of records.** What can
be drawn trustworthily at any coverage is the evidence layer alone — resource,
its evaluators, independent or not — which is also a candidate for the
graphical abstract M7 requires.

## M7 — citable release and database paper

Target venue: the **Nucleic Acids Research Database Issue**.

- [ ] Archival DOI per release — see the Figshare/Zenodo question below
- [ ] CITATION.cff
- [ ] Co-maintainer recruitment
- [ ] Database paper draft

**Exit:** CFCR is citable, and someone other than its author has merged a record.

### The NAR timeline

These are the only dates in this file, and they are not an exception to the
rule at the top: they are **imposed from outside**, not estimates of our own
throughput. Verified from NAR's author pages on 2026-10-20.

Submission is **by invitation only**, on a yearly cycle:

| When | What |
|---|---|
| **1 July** | Pre-submission inquiry to Prof. Daniel J. Rigden, Executive Editor — the hard gate |
| 1 June | Earliest a manuscript may be submitted |
| **15 August** | New-database manuscript deadline |
| January | The issue publishes |

1 July 2026 has passed, so the realistic target is the **1 July 2027 inquiry
for the January 2028 issue**. No 2027-specific call was findable; confirm with
the editor. An invitation does not guarantee acceptance — everything is peer
reviewed.

The inquiry must carry a URL to a *fully functional* database and explain how
it is "different from, and substantially better than, all similar resources".
That argument is drafted; it is what the backfill should be shaped around,
because the editor will open the site.

### What must be true before the inquiry

- **M4 is done.** 20 entities will not survive comparison with Kipoi's 2,000+
  or the Stegle catalogue's 156. This, not the website, is what gates the
  submission.
- **At least one co-maintainer.** NAR states that "retirement or graduation of
  developers is not a valid reason to terminate the database", which turns the
  checkbox above into part of the case rather than a nicety.
- **The domain is held through ~2033.** The database must stay at the same URL
  for five years after publication — the reason cellfatecontrol.com exists
  rather than a `github.io` address.
- **An archival DOI.** NAR's data page names **Figshare** and rules out GitHub
  as a primary archive; this roadmap said Zenodo. Mint both, or settle it in
  the inquiry.

### Easy to forget at submission time

- A **graphical abstract is mandatory**: 5:2 ratio, min 127×50 mm, TIF/EPS or
  editable PDF, 300–600 dpi, landscape, sans-serif, no trademarked logos.
- **Six suggested referees**, independent of the authors and not from the same
  institution or city.
- 4–5 typeset pages; database name first in the title; a working URL in the
  abstract.
- A narrow topic must be argued to benefit the wider NAR readership — the
  evidence-independence mechanism is the general-interest claim.

**Already satisfied:** free with no login or registration, HTTPS enforced, bulk
download in open formats with licence terms stated, mobile support (worth
mentioning in the manuscript — NAR asks for it), and no new experimental or
computational results, which the Database Issue does not accept.

### A second venue, considered and declined for CFCR itself

Considered 2026-10-27: the **NAR Web Server Issue**, whose gate is far easier —
no invitation, a one-page proposal taken year-round from November 2026, the
manuscript due two months after the approval email, and acceptance by ~1 May
for that year's issue. Fixed deadlines were abolished in the 2026 editorial.
Verified from <https://academic.oup.com/nar/pages/submission_webserver>.

**CFCR cannot go there, and cannot go to both.** Three of that issue's
exclusions are decisive, and the third rule is the one that settles sequencing:

- "Aggregators or assemblers of existing third-party tools" are not eligible.
- "Query-only data resources" are directed to the Database Issue — which is
  what a browsable catalogue is.
- The server must let users analyse their own data; "mere portals for static
  data" are excluded.
- **Similar tools need a two-year interval after any previous publication.** So
  a CFCR-shaped server following a January 2028 Database Issue paper is blocked
  until 2030.

What *is* eligible is the derivation rather than the catalogue: a server that
takes a resource and its paper as user-submitted input and reports who
evaluated it, whether those evaluators were independent, and on what terms it
can be reused. That is field-agnostic by construction — author names and
citation graphs carry no discipline — and a prior-art survey the same day found
nothing that does it: scite classifies citation statements rather than
evaluators, OpenEBench hosts benchmarks without recording evaluator
independence, the replication databases mean independent *samples*, and the
ML-licence tools stop at the licence.

That is now a separate project, [WhoChecked](https://github.com/JimYuhaoWu/WhoChecked),
deliberately not a mode of CFCR — which is what keeps the two-year rule from
biting. **The derivation they share (`classify_overlap`, `derive_tier`,
`norm_author` in `scripts/05_validate.py`) should become a library both import
rather than a copy in each**; this file's own review discipline treats a second
home for a shared thing as a defect, and it is the function both papers would
claim as novel. Undecided, and tracked as WhoChecked's M1 first item.

**The honest argument against starting it:** M7 still needs a co-maintainer,
NAR states that retirement or graduation of developers is not a valid reason to
terminate a resource, and a second project doubles that gap rather than sharing
it.

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
