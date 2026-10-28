# Scope audit

Generated from `literature/scope_labels.yaml` on 2026-10-28; the
criteria applied are `docs/scope_criteria.md`. This closes M4a's third item: the
admission error rate of the catalogue is a number.

The labels are unratified and were assigned by Claude, not by the curator. They
are a measurement offered for review. Nothing here withdraws a record — M4a's
fourth item, a demote path, does not exist yet.

## The rate

Of **490** published records, **170 are clearly out of scope
(34.7%)** and **227 are out including the
arguable cases (46.3%)**.

M4a was written on the assumption of ~2%, nine records found by eye. The real
figure is between seventeen and twenty-three times that.

## Where it is

| type | records | clearly out | out incl. arguable | % out |
|---|---|---|---|---|
| `benchmark` | 91 | 59 | 67 | 74% |
| `database` | 7 | 0 | 0 | 0% |
| `dataset` | 9 | 0 | 0 | 0% |
| `model` | 320 | 80 | 118 | 37% |
| `module` | 58 | 31 | 42 | 72% |
| `protocol` | 5 | 0 | 0 | 0% |

`database`, `dataset` and `protocol` are clean: 21 records, not one out. They
are also the three smallest types and the only ones never expanded by a
backfill wave. `benchmark` and `module` are roughly three-quarters out, and
`model`, the type the novelty argument counts, is over a third.

The two bad types failed differently:

* **`benchmark` came in on keywords.** The discovery queries match *benchmark*,
  *foundation model*, *sequence* and *expression*. A video question-answering
  benchmark matches all four, and so do benchmarks for polymers, MRI, materials
  phase-field models, precipitation downscaling and Lasso hyperparameters.
* **`module` came in on subject matter.** The `with-what` backfill admitted
  chromatin- and cancer-biology **findings** about regulators instead of
  **collections** of them: prognostic signatures, single-gene mechanisms,
  unrelated uses of the phrase *effector domain*. That is a C1 failure, and no
  keyword list would have caught it.

## Which criterion decided

| criterion | reading | records out |
|---|---|---|
| **C1** | a result, not a resource | 59 |
| **C2** | substrate is not the genome | 90 |
| **C3** | observes rather than acts | 61 |
| **C4** | no in-scope axis | 4 |
| **C5** | `what` embeds rather than predicts a response | 13 |

C2 is the largest single group and the cheapest to check. Two clusters are
most of it: 15 records are protein contact-map or protein-structure prediction,
and 15 more predict expression from histology or tissue images.

## A second kind of error

44 records carry a `type_defect`: in scope,
and the wrong kind of thing. The criteria pass them, correctly.

| defect | records |
|---|---|
| a benchmark typed as a model | 23 |
| a critique or evaluation entered as an entity | 8 |
| one resource entered twice | 6 |
| both a type error and a duplicate | 4 |
| a dataset or database typed as a model | 3 |

Two of these matter more than their count suggests.

**Critiques entered as entities.** A critique is evidence *about* a resource,
and CFCR has a place for it: an `entity_paper` row with `role: critique`, which
is what `evidence_tier` is derived from. Entered as an entity it does two kinds
of damage at once — it inflates the model count and withholds the evidence from
the model the critique is about. The count is inflated and the evidence
understated by one mistake.

**`model:dnabert-2` is not DNABERT-2.** Its `primary` paper is a colorectal
enhancer fine-tuning application, while the actual DNABERT-2 paper is attached
to `benchmark:dnabert-2`. So the best-known DNA language model in the field may
have no model record at all, and a benchmark record stands in for it.

## What is still a judgement call

57 records are out and 29 are in on an
`arguable` label — 86 decisions a
reasonable curator could reverse. They cluster:

* **DNA language models applied to design that is not fate control** — plasmid
  backbones, biosynthetic assembly lines, de novo genes, CHO antibody titres.
  Labelled out on C4: the tool is in scope and the target is not. If C4 is read
  the other way, the `how` axis widens to all of sequence design.
* **In-scope models used to produce a finding** — regulatory evolution,
  positive selection, genome stability. Labelled out on C3. The resource is in
  scope; what the paper delivers is an explanation.
* **TWAS-style expression imputation from genotype** — labelled out on C2,
  because the substrate is genotype rather than sequence or chromatin state.
* **Single-cell foundation models** — C5 turns on whether perturbation response
  is among the evaluated tasks, which the abstract does not always say.

Settling these four questions settles most of the 86.

## What the sample says about the method

A seeded stratified random sample of 102 records was labelled first, before any
of this pass. It estimated **47.1%** out; the full pass found **46.3%**,
and the clear-only figure of 34.7% sits inside the
sample's 95% interval of 28.5–46.9%.

So the sample was right, for a fiftieth of the work. The next audit — after the
next backfill wave, or to check whether a demote pass worked — does not need to
be exhaustive.
