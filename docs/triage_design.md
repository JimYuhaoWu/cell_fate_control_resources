# Triage design — scoring and role proposal for `literature/02_triage.py`

**Status:** design, 2026-10-20. Written before `01_search.py`, `02_triage.py` and
`03_record.py`, because the critique-detection design decides what the search
step has to fetch. Every number below was measured on 2026-10-20 against
committed repository data or a live API call; the citation half is reproducible
with `python literature/triage_eval.py`.

---

## 0. What triage decides, and what it must not

Triage ranks. It does not include, and it does not tier.

- **It proposes a role** (`benchmark`, `critique`, or neither) for each
  candidate, writes the proposal into `literature/reviews/review_YYYY-MM-DD.md`,
  and a human accepts or rejects it. This is M3's exit criterion: *discovery is
  automated; inclusion stays a human decision.*
- **It never touches `evidence_tier`.** The tier is derived in
  `scripts/05_validate.py` (`check_evidence_tier`) from author overlap between a
  model's `primary` paper and the papers whose role is `benchmark` or `critique`.
  Triage's job ends at proposing the role; QC computes the tier from it. Section
  2.4 explains why author overlap is therefore deliberately absent from the
  scoring, even though it is the single most predictive signal available.

There are two distinct scoring problems, and they share almost nothing.
Discovery hits arrive from a keyword query and are scored for *scope*. Citing
papers arrive from the citation graph and are scored for *what they do to a
model that is already catalogued*.

---

## 1. Keyword scoring for discovery hits

### 1.1 Why `eCR_mod_lib`'s table does not transfer

`eCR_mod_lib`'s `SCORE_WEIGHTS` is a good table for a different catalogue. Two
of its entries are actively wrong here, and both would silently delete the
records CFCR exists to hold:

| eCR entry | Why it breaks CFCR |
|---|---|
| `"review": -1.0` | `review` is a legitimate `entity_paper` role — `model:gears` carries one (`10.1038/s41576-025-00920-4`, the Nature Reviews Genetics perturbation catalogue). A review that evaluates models is evidence, not noise. |
| `"yeast"/"plant"/"drosophila"/"arabidopsis": -2.0 … -3.0` | `vocab/organism.yaml` admits `multi-species`, and `model:evo2` is trained *across all domains of life*. A flat organism penalty throws away the DNA language models that are squarely in scope — the same reason `search_queries.yaml` filters on publication type rather than organism. |

The rest of eCR's table is about DBD/ED/CR domain characterisation, which CFCR
reaches through the `with-what` axis only, so it is kept for the
`module_collections` query and replaced everywhere else.

### 1.2 The tables

Built from `vocab/task.yaml`, `vocab/architecture.yaml`,
`vocab/output_type.yaml` and the README scope rule. A term matched in the title
counts double; each table is capped so no single table can dominate.

| table | cap | what it is, and why that weight |
|---|---|---|
| **input gate** | +6.0 | The README scope rule is a rule about *input*: "models that take DNA sequence or chromatin state as their primary input". So `dna sequence`, `genomic sequence`, `sequence-to-function`, `chromatin state`, `regulatory dna`, `cis-regulatory` carry +2.0 to +3.0 — the heaviest positive weights in the table, because they are the scope rule itself. |
| **task** | +8.0 | Every term and synonym in `vocab/task.yaml`, at +1.5 to +2.5. `regulatory element design` is +3.0: nothing out of scope uses that phrase. |
| **architecture** | +2.5 | `vocab/architecture.yaml` terms at +0.5 to +0.75. Deliberately low — architecture answers *how*, not *whether it is in scope*. A transformer paper is not in scope for being a transformer paper. |
| **output type** | +3.0 | `vocab/output_type.yaml` terms at +0.5 to +2.0. |
| **out of scope** | uncapped | The README's own exclusions at −1.5 to −4.0: `trajectory inference`, `rna velocity`, `pseudotime`, `lineage tracing`, `optimal transport`, plus the observation-not-control cluster (`batch correction`, `cell type annotation`, `clustering`) and the plainly-other-field cluster (`histopathology`, `electronic health record`, `protein folding`). Uncapped on purpose: these are exclusions, not preferences. |
| **single clade** | −4.0 | Replaces eCR's flat organism penalty. `arabidopsis`, `plant genom`, `crop`, `rice`, `yeast`, `drosophila`, `prophage`, `plasmid` and the rest at −2.0 to −3.0 — **but the whole table is waived** when a multi-species marker is present (`multi-species`, `cross-species`, `all domains of life`, `across species`). This is the entry eCR gets wrong and CFCR cannot afford to. |

### 1.3 What it measures

Scored against the 30 papers in `db/papers.tsv` — all in scope by construction,
since each is attached to a catalogued entity — and against the first 50 live
Europe PMC hits for the `benchmarks` query in `search_queries.yaml`, the broadest
of the eight at 2,326 hits.

|  | n | min | median | max |
|---|---|---|---|---|
| catalogued papers | 30 | 0.00 | 5.50 | 14.50 |
| live `benchmarks` query, first 50 | 50 | −3.50 | 2.50 | 13.50 |

The separation is real at the top and the bottom. Enformer's paper scores 14.50
and AlphaGenome's 12.00; the broad query's floor is a plant-breeding
genomic-selection paper at −3.50 and a plant-growth-promoting-rhizobacteria
paper at −2.25. The clade waiver works as intended: Evo 2 keeps its 4.25 because
its title says "across all domains of life", while `BOTANIC-1: a series of
long-context plant genomic foundation models` is pushed below every in-scope hit.

### 1.4 The finding that changes the design: one table cannot serve six types

Five of the 30 catalogued papers score **exactly 0.00**:

- `JASPAR 2024` (`database:jaspar-2024`)
- `EpiFactors 2022` (`module:epifactors-2022-chromatin-regulators`)
- the Replogle Perturb-seq atlas, both versions (`dataset:replogle-2022-perturb-seq`)
- the CUT&RUN protocol (`protocol:cutrun-janssens-henikoff`)

and GEARS scores 0.50. These are not scoring failures — a database of
transcription-factor binding profiles genuinely contains none of the language of
sequence-to-function modelling. They are evidence that the sequence-model
vocabulary cannot score a database, a protocol, or a perturbation model, and that
a single global table plus a global `--min-score` would delete a sixth of the
existing catalogue on sight.

`search_queries.yaml` already carries the fix, as a field it currently describes
only as a triage hint: every query declares `expect_type` and `fate_axis`.
**02_triage.py should select its table per query from `expect_type`**, so the
`module_collections` query is scored with eCR's DBD/ED/CR vocabulary, the
`where`/`how` queries with the tables above, and `benchmarks` with a table that
expects evaluation language rather than model language. The hint becomes the
table selector.

### 1.5 Threshold: rank, do not drop

eCR drops candidates below `--min-score 2.0`. Measured here, a global threshold
costs more than it saves:

| threshold | keeps, broad query | keeps, catalogued |
|---|---|---|
| 3.0 | 23/50 | 20/30 |
| 5.0 | 15/50 | 16/30 |
| 6.0 | 8/50 | 13/30 |
| 8.0 | 4/50 | 7/30 |

At every useful threshold the filter discards more known-good papers than
plausible noise. So `02_triage.py` should **rank the whole result set and
section it**, with a threshold that only decides which section a candidate lands
in, not whether it appears. A rejected candidate that is never written down comes
back next cycle — the reason `.gitignore` commits `literature/reviews/` in full.

### 1.6 Tradeoffs left open

1. **The clade cap costs a true negative.** Capping the clade penalty at −4.0
   (so one stray "yeast" in a comparison cannot sink an in-scope human model)
   lets `Dbert2_LR`, a genuine *Arabidopsis*/crop cis-regulatory model, back over
   the 3.0 line at 3.75. Uncapped it scored −0.25. The cap is the safer error for
   a catalogue whose recall matters more than a curator's reading time, but it is
   a choice, not a fact.
2. **The `benchmarks` query should still be narrowed.** `search_queries.yaml`
   already flags it as too broad and defers the fix to this scoring work. The
   measurement supports narrowing: the first 50 hits have a median of 2.50 and
   include toxicology, breast-cancer imaging, bibliometrics and crop breeding.
   Narrowing the query is cheaper than scoring the noise, but that edit belongs
   with `01_search.py`.
3. **Title doubling is uncalibrated.** Counting a title match twice is
   defensible and was not tuned; nothing here measures what a different factor
   would do.

---

## 2. Proposing roles from the citing set

### 2.1 The problem

`evidence_tier` is derived only from `entity_paper` rows whose role is
`benchmark` or `critique`. Those papers cannot be found by keyword search —
asking Europe PMC for "fail" AND "enformer" returns three hits, and neither of
Enformer's two catalogued critiques is among them. They are reached by walking
the primary paper's citations through OpenAlex (`filter=cites:<id>`).

The pool is large. For the five catalogued models that have evaluations:

| entity | citing works |
|---|---|
| `model:enformer` | 1,298 |
| `model:nucleotide-transformer` | 656 |
| `model:alphagenome` | 374 |
| `model:borzoi` | 263 |
| `model:chrombpnet` | 138 |
| **total** | **2,729** |

One free finding, measured: **OpenAlex merges a preprint with its journal
version into a single work.** All four catalogued preprint/primary pairs resolve
to the same OpenAlex id — the Enformer preprint and the Nature Methods paper are
both `W3203588026`. The sweep therefore runs once per entity, not once per
attached paper, and `citation_sweep.entities` in `search_queries.yaml` needs no
preprint handling.

### 2.2 Signals, and what each is worth

| signal | weight | why |
|---|---|---|
| **names this entity, in the title** | +3.0 | The strongest available evidence that a citing paper is *about* this model rather than merely citing it. |
| **names this entity, in the abstract** | +1.5 | Same signal, weaker position. |
| **several catalogued models named together** | 0 / +0.5 / +1.5 / +3.0 for 0/1/2/3+ | The benchmark signature. A paper naming three catalogued models is comparing them. |
| **cites several catalogued primary papers** | +0.75 each, capped +3.0 | A benchmark's reference list contains the models it evaluates. Weaker than it looks today — see 2.5. |
| **benchmark lexicon** | title +2.0 each (cap 4.0), abstract +0.5 each (cap 2.0) | `benchmark`, `evaluation`, `comparison`, `assessment`, `baseline`, `systematic`, `leaderboard`, `head-to-head`. |
| **critique lexicon** | title +2.5 each (cap 5.0), abstract +0.75 each (cap 3.0) | `fail`, `struggle`, `poorly`, `overestimat`, `limitation`, `pitfall`, `spurious`, `confound`, `misleading`, `not generalize`. Weighted above the benchmark lexicon because critiques are rarer and are what the novelty claim rests on. |
| **demotion** | −3.0 | `review`, `perspective`, `primer`, `erratum`, `retraction` in the title, or OpenAlex `type: review`. Demotes, never excludes: `review` is a real role. |

Aliases shorter than four characters are dropped. `vocab`-adjacent alias lists
contain `"NT"` for `model:nucleotide-transformer`, which matches almost every
abstract; all matching is word-boundary anchored and case-insensitive.

### 2.3 Two lists, because one ranking was measurably wrong

The first design gated candidacy on naming the model: a citing paper that never
writes "Enformer" is not an evaluation of Enformer. That gate ranks the named
cases well — and **discards both catalogued critiques of Enformer.** Neither
names it:

- *"Personal transcriptome variation is poorly explained by current genomic deep
  learning models"* evaluates **four state-of-the-art models** and names none of
  them in its abstract.
- *"Current approaches to genomic deep learning struggle to fully capture human
  genetic variation"* names none either, and has **no abstract at all** in
  OpenAlex.

Critiques describe a *class*. So candidacy has two tracks:

- **List A — names this entity.** Per entity, tight, high confidence.
- **List B — names no catalogued model, but names a model class and talks like
  an evaluation.** Global and deduplicated, because one such paper is evidence
  for several entities at once, and annotated with which catalogued primary
  papers it cites so the curator can see which entities it might attach to.

Merging the two into one ranking was tried and measured: the class track floods
the list, and the Enformer benchmark falls from rank 2 to rank 13 while the pool
grows from 47 to 144. The lists are kept separate and the curator reads A first.

### 2.4 Author overlap is deliberately not scored

Author overlap with the primary paper is the most predictive signal in the pool
and is excluded on purpose.

`05_validate.py` derives `evidence_tier` from exactly that overlap. If triage
used it to demote same-group papers, the `benchmark` rows reaching QC would be
pre-filtered toward independent ones, and the derived tier would measure
*triage's own filter* rather than the literature. A model would drift toward
`externally-benchmarked` because the self-benchmarks were never proposed. That
would hollow out the one query CFCR exists to answer.

A self-benchmark is a legitimate `benchmark` row; it yields `self-reported`, and
that is the correct answer, not a missing one. So the review file should
**display** author overlap as context next to each candidate — it is useful to a
human deciding what to read — and the score must ignore it.

### 2.5 Measured against the eight committed rows

`db/entity_paper.tsv` holds 6 `benchmark` and 2 `critique` rows. Reproduce with
`python literature/triage_eval.py`.

| entity | evaluation paper | truth | where it lands | score | proposed |
|---|---|---|---|---|---|
| `model:enformer` | `10.64898/2026.02.04.703796` | benchmark | **A 2/31** | 7.75 | benchmark ✔ |
| `model:borzoi` | `10.64898/2026.02.04.703796` | benchmark | **A 3/23** | 7.75 | benchmark ✔ |
| `model:alphagenome` | `10.64898/2026.02.04.703796` | benchmark | **A 4/24** | 7.75 | benchmark ✔ |
| `model:enformer` | `10.1038/s41588-023-01574-w` | critique | **B 13/124** | 8.00 | critique ✔ |
| `model:nucleotide-transformer` | `arxiv:2311.12570` (BEND) | benchmark | **B 20/124** | 7.50 | benchmark ✔ |
| `model:enformer` | `10.1038/s41588-023-01517-5` | critique | **B title-only 6/8** | 4.25 | critique ✔ |
| `model:chrombpnet` | `10.52202/079017-1981` (DART-Eval) | benchmark | *no citation edge* | — | — |
| `model:nucleotide-transformer` | `10.52202/079017-1981` (DART-Eval) | benchmark | *no citation edge* | — | — |

**6 of 8 recovered. Of the 6, the proposed role is correct 6 times out of 6.**

Review burden: 2,729 citing works reduce to 109 list-A rows across five entities
plus 132 unique list-B items — about 9% of the pool, worst case 31 list-A rows
for Enformer's 1,298 citations.

The title-only split in list B is what makes the sixth recovery work. OpenAlex
holds no abstract for `10.1038/s41588-023-01517-5`, so an additive score buries
it under every candidate that has one: ranked among all 132 list-B items it sits
at 102/132. Segregating the 8 abstract-less candidates into their own section
puts it at 6/8, where a curator will actually see it. It is a structural fix, not
a weight.

### 2.6 Where this fails

1. **A missing reference list is unrecoverable.** DART-Eval accounts for both
   misses. Its OpenAlex record (`W4405899019`, the NeurIPS proceedings DOI) has
   `referenced_works_count: 1` — essentially no reference list deposited — so it
   can never appear in any `cites:` result, whatever the scoring does. This caps
   recall at 6/8 (75%) on today's ground truth, and the cap is a property of the
   citation graph, not of this design. Conference proceedings are the systematic
   gap: the mitigation is to keep the `benchmarks` discovery query, which found
   DART-Eval by keyword, rather than letting the citation sweep replace it.
   `search_queries.yaml` currently floats exactly that replacement as an option
   for fixing the query's breadth; this measurement argues against it.
2. **A missing abstract cannot be backfilled.** Checked, not assumed: Europe PMC
   returns the title of `10.1038/s41588-023-01517-5` and no `abstractText`,
   despite being the source `config/sources.yaml` relies on for the abstracts
   Crossref omits from Nature-family journals. No source in the list supplies
   it. Section 2.5's title-only section is the whole mitigation, and it works
   only because such papers are rare (8 of 132).
3. **Reference overlap is nearly dead at the current catalogue size.** It scores
   0.0 for *both* Enformer critiques. They are from 2023, and every other
   catalogued model — Borzoi (2025), AlphaGenome (2026), Nucleotide Transformer
   (2024), ChromBPNet (2024) — postdates them, so there is nothing for their
   reference lists to overlap with. The signal only works once the catalogue
   contains a citing paper's contemporaries, which makes it a signal that gets
   stronger through M4's backfill to ~150 entities and should not be tuned
   against 20.
4. **The benchmark/critique split is decided by a 1.00-vs-0.75 margin in one
   case.** The fine-mapping paper is proposed `benchmark` because its benchmark
   lexicon scores 1.00 against a critique lexicon of 0.75. The role is right,
   and the margin is noise. Triage proposes; the curator decides; the review file
   should print both sub-scores so a curator can see when the proposal was a
   coin-flip.
5. **Precision is not measurable against this ground truth, and is not claimed
   here.** The 8 rows are not an exhaustive labelling of 2,729 citing works —
   they are what a curator has catalogued so far. A top-ranked candidate that is
   not among the 8 is more likely an uncatalogued true evaluation than a false
   positive: list A's top entries for `model:alphagenome` are *"Causal variant
   underestimation is a major overlooked driver of sequence-to-function model
   error"* and *"Assessing large-scale genomic language models in predicting
   personal gene expression"*, and a top-ranked list-B item (*"mRNABench"*)
   cites nine catalogued primary papers. Those look like M4 records, not errors.
   What is measurable is
   recall-at-rank and review burden, and only those are reported above.
6. **Which models a class-level benchmark actually evaluates cannot be decided
   automatically.** BEND is the clean case: it benchmarks the Nucleotide
   Transformer and never names it, saying "current DNA LMs" instead. The citation
   edge proves BEND cites NT's primary paper; nothing in the title or abstract
   says NT is in the results table. Triage can propose *"this paper benchmarks
   some set of catalogued models, and cites these"*; a human must open the paper
   to learn which. Given M3's exit criterion this is the correct place to stop,
   and it is the reason the deliverable is a ranked proposal rather than a
   classifier.

---

## 3. Decisions this leaves to the implementation

1. **Per-query scoring tables keyed on `expect_type`** (§1.4) — the one
   structural change to eCR's single-table design.
2. **Section, do not filter** (§1.5) — `--min-score` moves a candidate between
   sections of the review file rather than out of it.
3. **Two candidate lists with separate rankings, and a title-only subsection in
   list B** (§2.3, §2.5).
4. **Display author overlap, never score it** (§2.4).
5. **Print both lexicon sub-scores** next to every proposed role (§2.6.4).
6. **Keep the `benchmarks` discovery query** rather than letting the citation
   sweep replace it (§2.6.1).

## 4. Re-measuring

```bash
python literature/triage_eval.py
```

Reads `db/entity_paper.tsv`, `db/entities.tsv` and `db/papers.tsv`, caches the
OpenAlex dumps under `literature/candidates/` (git-ignored), and prints where
every committed `benchmark`/`critique` row lands. Run it after any change to the
weights in §2.2: it is the only thing that says what the change cost.
