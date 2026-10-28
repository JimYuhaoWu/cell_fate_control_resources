# Scope audit

Computed from `literature/scope_labels.yaml` on 2026-10-28; the criteria applied
are `docs/scope_criteria.md`. This closes M4a: the admission error rate of the
catalogue is a number, every record is named, and the boundary cases are
decided rather than deferred.

The labels were assigned by Claude, not by the curator, and `ratified: false`
still says so. Each is reversible by deleting two lines from a record.

## The rate

Of **490** published records, **240 are out of scope (49.0%)** and 250 are in.

M4a was written on the assumption of ~2%, nine records found by eye. The real
figure is twenty-six times that.

The first pass reported 170 clearly out and 227 on a wider reading, with 86
labels `arguable`. Those 86 were then settled by five decisions
(`docs/scope_criteria.md`, *Decisions on the boundary cases*), which moved 13
records — all from in to out, none the other way. So the first pass was not
systematically harsh; it was systematically unsure about one question.

## Where it is

| type | records | out | % out | published now |
|---|---|---|---|---|
| `benchmark` | 91 | 67 | 74% | 24 |
| `database` | 7 | 0 | 0% | 7 |
| `dataset` | 9 | 0 | 0% | 9 |
| `model` | 320 | 131 | 41% | 189 |
| `module` | 58 | 42 | 72% | 16 |
| `protocol` | 5 | 0 | 0% | 5 |

`database`, `dataset` and `protocol` are clean: 21 records, not one out. They
are also the three smallest types and the only ones never expanded by a
backfill wave. `benchmark` and `module` are roughly three-quarters out, and
`model`, the type the novelty argument counts, is two in five.

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
| **C1** | a result, not a resource | 71 |
| **C2** | substrate is not the genome | 90 |
| **C3** | observes rather than acts | 61 |
| **C4** | no in-scope axis | 4 |
| **C5** | `what` embeds rather than predicts a response | 14 |

C2 is the largest single group and the cheapest to check. Two clusters are most
of it: 15 records are protein contact-map or protein-structure prediction, and
15 more predict expression from histology or tissue images.

C1 grew from 59 to 71 when the boundary cases were settled, which is D1 doing
the work it was written for.

## Which decision settled each boundary case

| decision | reading | labels settled |
|---|---|---|
| **D1** | a conclusion is not a resource | 42 |
| **D5** | observation stays out, even when an in-scope model observes | 19 |
| **D3** | the substrate must be read, not inferred | 11 |
| **D4** | a claimed capability, not an evaluated task | 10 |
| **D2** | `how` is bounded by fate control, not sequence design | 4 |

`settled_by` in the labels file names the decision behind each label, so
reversing one costs re-reading its group rather than all 490.

## A second kind of error

44 records carry a `type_defect`: in scope, and the wrong kind of thing. The
criteria pass them, correctly.

| defect | records |
|---|---|
| a benchmark typed as a model | 23 |
| a critique or evaluation entered as an entity | 8 |
| one resource entered twice | 6 |
| both a type error and a duplicate | 4 |
| a dataset or database typed as a model | 3 |

Two matter more than their count suggests.

**Critiques entered as entities.** A critique is evidence *about* a resource,
and CFCR has a place for it: an `entity_paper` row with `role: critique`, which
is what `evidence_tier` is derived from. Entered as an entity it does two kinds
of damage at once — it inflates the model count and withholds the evidence from
the model the critique is about. D1 withdrew those records; attaching them is
the other half of the fix and is not done.

**`model:dnabert-2` is not DNABERT-2.** Its `primary` paper is a colorectal
enhancer fine-tuning application, while the actual DNABERT-2 paper is attached
to `benchmark:dnabert-2`. So the best-known second-generation DNA language model
may have no model record at all.

## What the withdrawal left

239 records are `withdrawn` and **250 are published**: 189 models, 24
benchmarks, 16 modules, 9 datasets, 7 databases, 5 protocols. Per axis, counting
published records only and remembering a record can carry more than one:

| axis | estimated | published now |
|---|---|---|
| `where` | ~125-175 | 97 |
| `how` | ~60-80 | 45 |
| `what` | ~15-25 | **77** |
| `with-what` | ~15-30 | 19 |

**The catalogue is now smaller than its own target, not larger.** 250 against
~300-400, with `where` and `how` both under their ranges. That is the real cost
of a boundary this tight, and it is a content-scale question rather than a scope
one: `ROADMAP.md` records that content scale, not the website, gates the NAR
submission.

`what` is the one axis still over its range, at 77 against ~15-25. D4 is what
holds it there — perturbation-response prediction is a large and active
literature, and the axis was estimated as shallow when the catalogue held
twenty of them. That estimate is the number to revise, not the labels.

## What the sample said about the method

A seeded stratified random sample of 102 records was labelled first, blind to
the rest. It estimated 47.1% out; the full pass found 46.3% before the boundary
cases were settled and 49.0% after, and the clear-only figure of 34.7% sat
inside the sample's 95% interval of 28.5–46.9%.

So the sample was right, for a fiftieth of the work. The next audit — after the
next expansion, or to check a demote pass — does not need to be exhaustive.
