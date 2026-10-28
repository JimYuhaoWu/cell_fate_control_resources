# Scope criteria

`README.md` states the boundary as a sentence — *CFCR indexes resources you act
with, not resources you observe with* — and that sentence is the right one. What
it is not is a procedure. Two curators reading it can disagree about a protein
contact-map predictor without either misreading it, and nothing in the
repository records which of them was right.

This file is the procedure. It exists because M4a cannot be closed without it:
the catalogue has an *intensional* boundary and no *extensional* one, and that
single absence is why admission cannot be automated and why drift cannot be
detected.

Each criterion is written to be decidable from the title and abstract of the
entity's `primary` paper and nothing else. That constraint is not a
simplification, it is the data: 304 of 490 records carry no `description`, so
the primary paper's abstract is all a curator or a script has to go on. A
criterion that needs the full text, the repository, or the curator's background
knowledge cannot be applied to the catalogue as it actually stands.

`literature/scope_labels.yaml` is the labelled set these criteria were written
against, and the one they are measured on.

## The procedure

A record is in scope when **C1 through C4 all hold**. C5 refines C1–C4 for one
axis rather than adding a gate. Order matters only for reporting: the first
criterion that fails is the one recorded, because "out on C2" and "out on C3"
are different mistakes with different fixes.

### C1 — It is a resource, not a result

The record must name something a third party can pick up and use: model weights
or inference code, a benchmark or task suite, a dataset, a database, a protocol,
or a module collection.

Out by C1: a paper whose product is a **biological finding** (*Condensates of
the chromatin regulator ANKRD11 restrict hypertranscribed genes*), a **review**
(*Improving understanding of chromatin regulatory proteins*), a **position or
metric argument** (*AUC-PR is a More Informative Metric*). These are papers, and
CFCR already has a place for papers: `entity_paper`, attached to the entity they
bear on. Admitting one as an entity of its own is the error — it claims the
paper is a resource.

This is the criterion the backfill broke most often, and it is also the one a
score cannot see: "we identify X" and "we present X" are one word apart.

### C2 — Its substrate is the genome

The primary input or content must be **genomic DNA sequence or chromatin state**.
On the `with-what` axis, protein domains **that act on the genome** qualify, which
is what makes a transcriptional effector-domain compendium in scope and an
antibody fitness benchmark not.

Out by C2, with the cases actually found in the catalogue:

| substrate | example |
|---|---|
| protein structure | protein contact-map prediction |
| protein fitness | antibody fitness benchmarks |
| RNA sequence and RNA-binding | RBP binding atlases, RNA foundation models |
| protein sequence → protein expression | heterologous expression optimisation |
| histological images | spatial expression predicted from H&E slides |
| medical images | MRI foundation-model benchmarks |
| natural language and video | video question answering, LLM agent benchmarks |
| non-biological | phase-field materials, polymers, hyperparameter optimisation |
| population surveillance | SARS-CoV-2 lineage abundance in wastewater |

C2 is the cheapest criterion to apply and catches most of the drift. It is also
the one a keyword gate can approximate, which is why these records got in: they
match *benchmark*, *foundation model*, *sequence*, *expression*.

### C3 — It acts rather than observes

The resource must answer one of the four `fate_axis` verbs: **where** do I act,
**what** do I perturb, **how** do I represent and score sequence I might design,
**what** do I build the actuator from.

Out by C3: trajectory inference and RNA velocity (named in `README.md`), and the
same distinction applied consistently — batch integration, imputation,
deconvolution, cell-type annotation, clustering, phylogenetic reconstruction,
selection scans, sequence identification for diagnostics or surveillance, and
assay-versus-assay comparisons whose question is how well a measurement
characterises a genome.

Variant effect prediction **on regulatory sequence** is in scope and is not an
exception to this: it scores a sequence you might design. Prioritising coding
disease variants in a patient is out — the object is a diagnosis, not a design.

### C4 — Its axis is nameable, and in scope

At least one `fate_axis` value must be assignable from the abstract. For a
benchmark, dataset, protocol or database, the axis it **serves** must itself be
in scope; `README.md` already says these inherit that axis, which means an
inherited axis is a precondition for admission and not a label applied
afterwards.

C4 is where the catalogue's own records contradict it. **85 of 91 `benchmark`
records carry an empty `fate_axis`** — every other type fills it, 405 records
without exception. The field that records admissibility under the project's own
rule was never filled for the type where admission went wrong, so C4 was in
force on paper and unapplied in fact. An empty `fate_axis` is not itself
evidence that a record is out of scope — `benchmark:regdesign-bench` is plainly
in — but it does mean no one ever asked.

### C5 — `what` is deliberately shallow

Within the `what` axis, a resource is in scope when it **predicts a perturbation
response**, and out when it only **embeds or integrates** cells. A single-cell
foundation model evaluated on representation quality is out; the same model
asked what happens when a gene is knocked down is in.

This is `README.md`'s rule unchanged. It is written out here because it is the
only criterion that turns on what a resource is *used for* rather than what it
*is*, and because the `what` axis is at 105 records against an estimate of
15–30 — four times its ceiling, and the place where C5 is doing the most work.

## What the criteria do not decide

**Type, as distinct from scope.** Several records are in scope and typed wrongly:
a benchmark entered as a `model`, a critique entered as an entity rather than
attached as a paper. `model:dart-eval` and `benchmark:dart-eval` are the same
resource entered twice under two types. These are not admission errors and the
criteria above will pass them. They need their own pass, and the labelled set
flags them with `type_defect` rather than labelling them out.

**Quality.** Nothing here asks whether a resource is any good. That is what the
evidence layer is for, and conflating the two would make `evidence_tier`
circular.

**Demotion.** A record that fails a criterion today is not thereby withdrawn:
`literature/06_promote.py` has no demote path, which is M4a's fourth item.
Labelling is the measurement, not the correction.
