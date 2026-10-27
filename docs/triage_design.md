# Triage design — scoring and role proposal for `literature/02_triage.py`

**Status:** design, 2026-10-20. Written before `01_search.py`, `02_triage.py` and
`03_record.py`, because the critique-detection design decides what the search
step has to fetch.

**Which numbers here can be checked, and how.** The scheduled review of
2026-10-21 could verify none of the citation-half figures, because its sandbox
had no network — the proxy refused OpenAlex — and an unverifiable number reads
the same as a wrong one. So each kind now says what it rests on:

| numbers | source | offline? |
|---|---|---|
| §1.3 discovery scores | `db/papers.tsv` through `literature/triage_rules.py` | yes |
| §2.5 recall and ranks | `reports/triage_eval.md`, committed and dated | the artifact, yes; re-running it, no |
| §1.6, §2.6 live query counts | Europe PMC, arXiv and OpenAlex at a stated date | no |

The §1.3 figures are reproducible from committed data alone, so a reviewer
without network can recompute them. The §2.5 figures need OpenAlex, which is
why `literature/triage_eval.py` now writes `reports/triage_eval.md` and that
file is committed: the measurement itself is in the repository, dated, and
`git diff` on it says whether a scoring change moved the recall. The live query
counts cannot be made offline at all, and are dated wherever they appear so a
reader knows how stale they are rather than assuming they still hold.

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

**Re-measured against the committed implementation, 2026-10-20.** The tables
above were specified here before they were written; `literature/triage_rules.py`
is their first committed form, and it is a reimplementation from this section
rather than the prototype the numbers above came from. It does not reproduce
them exactly, and the difference is recorded rather than smoothed over:

| | n | min | median | max |
|---|---|---|---|---|
| catalogued papers, prototype | 30 | 0.00 | 5.50 | 14.50 |
| catalogued papers, committed | 30 | 0.00 | 4.50 | 13.50 |

Same shape, slightly flatter, and 7 zeros instead of 5. The separation that
matters survives: AlphaGenome 13.50, Enformer 12.00, and on the 463 candidates
of the first real `01_search.py` run the floor is **CloneOT**, a
clone-specific perturbation model using lineage tracing and optimal transport,
at −7.50, followed by a protein-structure-prediction review at −6.50 and two
single-clade language models at −4.00. The exclusion tables are doing the work
they were written for.

Per-query medians from that run, which is what a curator actually faces:

| query | n | median | ≥ 3.0 |
|---|---|---|---|
| `accessibility` | 16 | 8.00 | 14 |
| `benchmarks` | 89 | 6.00 | 83 |
| `interval_models` | 51 | 6.00 | 43 |
| `module_collections` | 48 | 5.00 | 39 |
| `variant_effect` | 42 | 5.00 | 24 |
| `perturbation_response` | 70 | 3.50 | 40 |
| `genome_3d` | 52 | 3.00 | 27 |
| `dna_language_models` | 95 | 2.00 | 21 |

`dna_language_models` is the one to watch: a median of 2.00 against 95 hits
means the query is pulling in plant, plasmid and phage language models that the
single-clade table then sinks. That is the scoring working and the query being
lazy, and the cheaper fix is in the query.

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
| **cites this entity's primary paper** | +3.0, and it is the gate | Since 1f4ab1f this is what admits a row to list A at all. Exact: the swept primary is in `referenced_works` for 7,002 of 7,002 cached citing rows, so OpenAlex's `cites:` index and the stored reference lists agree completely, and it costs no request. |
| **names this entity, in the title** | +3.0 | Still the strongest evidence that a citing paper is *about* this model rather than merely citing it — but a bonus now, not a requirement. |
| **names this entity, in the abstract** | +1.5 | Same signal, weaker position. |
| **several catalogued models named together** | 0 / +0.5 / +1.5 / +3.0 for 0/1/2/3+ | The benchmark signature. A paper naming three catalogued models is comparing them. |
| **cites several catalogued primary papers** | +0.75 each, capped +3.0 | A benchmark's reference list contains the models it evaluates. Counts primaries *other* than this entity's, which the gate has already established. |
| **benchmark lexicon** | title +2.0 each (cap 4.0), abstract +0.5 each (cap 2.0) | `benchmark`, `evaluation`, `comparison`, `assessment`, `baseline`, `systematic`, `leaderboard`, `head-to-head`. |
| **critique lexicon** | title +2.5 each (cap 5.0), abstract +0.75 each (cap 3.0) | `fail`, `struggle`, `poorly`, `overestimat`, `limitation`, `pitfall`, `spurious`, `confound`, `misleading`, `not generalize`. Weighted above the benchmark lexicon because critiques are rarer and are what the novelty claim rests on. |
| **demotion** | −3.0 | `review`, `perspective`, `primer`, `erratum`, `retraction` in the title, or OpenAlex `type: review`. Demotes, never excludes: `review` is a real role. |

Aliases shorter than four characters are dropped. `vocab`-adjacent alias lists
contain `"NT"` for `model:nucleotide-transformer`, which matches almost every
abstract; all matching is word-boundary anchored and case-insensitive.

### 2.3 Two lists, because one ranking was measurably wrong

**Superseded in part by 2.3a. The name gate described here was replaced on
2026-10-27; the reasoning is kept because it is why list B exists and why the
replacement went the way it did.**

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

### 2.3a The gate is the reference list, not the name

The name gate above fixed its own problem twice over and then met one it could
not. `fec702d` gave a record whose paper introduces no named resource a
*citation* name — `Wang 2025 Benchmarking translational potential` — which was
right for the catalogue and fatal here: nobody writes that in prose, so **392
of the 472 records holding only a primary paper were unreachable by any name
match.** The two decisions were each sound and could not both stand.

Measured over the 7,002 cached citing rows of 2026-10-21, against the curated
`benchmark`/`critique` rows as truth:

| route | of the 283 curated rows present |
|---|---|
| list A, name gate | 110 |
| list B | 82 |
| either | 192 |
| **neither** | **91** |
| list A, reference gate | **283** |

So list A now admits a row when the entity's primary paper is in the citing
paper's reference list, and the name scores where it appears rather than
gating. On the reference gate alone the threshold keeps 269 of 283; the name
bonus carries the last 14 over.

**The gate admits every swept row**, so it decides nothing by itself and
`02_triage.LIST_A_MIN` does the work. 5.0 is the highest threshold at which all
283 survive — 5.5 keeps 264, 7.0 keeps 174 — and below it recall is already
total. It is a filter, not the section boundary `--min-score` draws in
discovery, and on a different scale, since every list A score now carries the
+3.0 gate term.

**Three outcomes, not two.** Recording a role unread rests on the name, which
is the only evidence in a row that the paper is about the entity rather than
citing it for one of many reasons; asking about a row that cannot move a
saturated tier spends a curator on a foregone conclusion. A row with neither
property satisfies neither condition, so it is listed under *Cited, not
proposed* — no role recorded, no question asked. On the cached corpus:

| | tier cannot move | tier could move |
|---|---|---|
| names the entity | 190 → recorded unread | 0 |
| cites only | **1,867 → listed only** | 12 → asked |

Sending those 1,867 to a human was the alternative and the arithmetic refused
it: 1,879 decisions of which 1,867 cannot change any tier, which rebuilds the
wall 1.5 spent four changes climbing down from.

**Lists A and B are no longer disjoint**, where they used to be by
construction — A required the name, B required that no catalogued model be
named. A paper citing a primary and naming nothing now qualifies for both, so
list B skips what A reported, the listed rows included; letting them return as
B questions would move the wall rather than remove it. On the cached corpus
that empties list B entirely — all 172 of its rows cite a catalogued primary.
**Whether list B still earns a second scorer is therefore open**: it is not
dead in principle, since a class-level paper citing no catalogued primary has
no reference-list anchor and still lands there, but that case did not occur
once in 7,002 rows.

**What this does not settle.** The 471 primaries behind the one-paper records
carry 61,897 citing works, 53,351 of them behind just 19 papers — ENCODE at
18,053, ATAC-seq at 6,415, Roadmap at 6,351. Citing ENCODE's primary means "we
used ENCODE data", not "we evaluated ENCODE", so the gate's one signal means
something different for a foundational resource paper than for a model's own.
And none of those 472 records holds an evaluation yet, so neither cheaper
outcome applies and every row is a real decision: roughly 18,000 of them at the
29.6% that cleared 5.0 here. Sweeping them is a per-record decision about which
primaries are worth asking about, not a cycle to run. Tracked in #8.

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

**Historical.** This is the name gate measured when the catalogue held eight
evaluation rows; it now holds 291, and 2.3a supersedes the placements below.
Kept because the title-only finding at the end of it is still load-bearing.
`triage_eval.py` reproduces the current numbers, not these.

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
   gap: the mitigation is to keep the `benchmarks` discovery query rather than
   letting the citation sweep replace it, and `search_queries.yaml` floated
   exactly that replacement as an option for fixing the query's breadth, so this
   measurement argues against it.
   **Narrowed on 2026-10-20, and the mitigation is arXiv's half, not Europe
   PMC's.** Checked while implementing `01_search.py`: DART-Eval is absent from
   Europe PMC entirely — 0 hits for its own title — so only the query's `arxiv`
   key can reach it, at rank 11 of 50. The Europe PMC side was narrowed from
   2,326 hits to 61 on §1.6.2; the arXiv side was deliberately left alone,
   because tightening it to the DNA-language-model phrasings puts DART-Eval at
   rank 1 but drops the query to 3 hits.
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
OpenAlex dumps under `literature/candidates/` (git-ignored), prints where every
committed `benchmark`/`critique` row lands, and writes the same report to
`reports/triage_eval.md`.

**Commit that file with the change.** It is the only thing that says what a
change to the weights in §2.2 cost, and because the script needs OpenAlex it is
also the only form in which the §2.5 numbers can be checked by a reviewer
without network — which is how these numbers went unverified in the first
place. Run it after any scoring change and read the diff.

The discovery half of the scoring has no such dependency. It can be recomputed
from `db/papers.tsv` with no network at all:

```bash
python - <<'EOF'
import csv, statistics, sys
sys.path.insert(0, "literature")
import triage_rules as rules

def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))

# expect_type has to come from the entity the paper is attached to. Scoring all
# 30 with the `model` table instead gives median 2.00, not 4.50 -- which is
# §1.4's finding restated as a reproduction trap.
etype = {r["entity_id"]: r["type"] for r in rows("db/entities.tsv")}
of_paper = {}
for j in rows("db/entity_paper.tsv"):
    of_paper.setdefault(j["paper_id"], etype.get(j["entity_id"], "model"))

v = sorted(rules.score_discovery({"title": r["title"], "abstract": r["abstract"],
                                  "expect_type": of_paper.get(r["paper_id"], "model")})[0]
           for r in rows("db/papers.tsv"))
print(len(v), min(v), statistics.median(v), max(v))   # 30 0.0 4.5 13.5
EOF
```
