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

## Decisions on the boundary cases

The first pass left **86 labels `arguable`** — a reasonable curator could read
the criterion either way. Settled on 2026-10-28, because an unsettled boundary
case is not a small residue: those 86 were a sixth of the catalogue, and the
criteria could not be applied consistently to a new record while they stood.

They were not 86 questions. They were five, and the labels were **inconsistent**
on the largest of them before these decisions, which is the better argument for
making them than any of the individual records: *Early feature extraction drives
model performance* was labelled in while *a mechanistic finding about regulator
interactions* was labelled out, and nothing distinguished them.

### D1 — A paper whose product is a conclusion is not a resource

Settles 42 labels, and flipped 12 of them from in to out.

**The test: does something reusable ship with it?** Weights, inference code, a
task suite, a dataset, a compendium, a protocol. If what the paper delivers is
a conclusion — about architectures, about representations, about how robust or
private or attackable existing models are, about what the field should do next —
it is not an entity, whatever it is about.

This is not a new rule. `README.md` already says papers are *evidence attached
to entities, not the records themselves*, and `entity_paper` already carries
`critique`, `benchmark`, `review` and `application` for exactly this. D1 only
applies it to records that were admitted before anyone checked.

The consequence worth stating plainly: a **critique** entered as an entity is
the costly case, and `model:harrison-2026-do-gene-perturbation` and
`model:zhang-2026-disease-relevance-replicability` are both. As entities they
inflate the model count; as `entity_paper` rows they would feed `evidence_tier`
for the models they examine. The same mistake inflates the count and starves
the evidence layer, which is the one thing CFCR argues on. Withdrawing them is
half the fix; attaching them is the other half, and it is not done here.

What survives D1: a *method* is a resource even when it ships no weights, if
others can apply it. Augmentation recipes, a tokeniser, a scoring framework, a
replay harness — all in. A *finding about* methods is not.

### D2 — `how` is bounded by fate control, not by sequence design

Settles 4 labels, all confirmed out.

A DNA language model that designs plasmid backbones, biosynthetic assembly
lines, de novo genes, or a sequence optimised for antibody titre in CHO cells is
doing sequence design, and `how` is not "sequence design". Every `fate_axis` is
a verb about acting on **cell fate**; `how` is how I represent and score
sequence *I might design to that end*.

The model is in scope and its application is not — Evo is catalogued, and
Evo-designed biosynthetic pathways are not. Read the other way, `how` would
widen to all of generative genomics, and the tight boundary is the thing the
novelty argument rests on.

### D3 — The substrate must be read, not inferred

Settles 11 labels, all confirmed out.

C2 asks what the resource's primary input **is**. A TWAS-style model that
imputes expression from genotype never reads a base of sequence: it reads
variant calls and an expression reference. Likewise inferring the rest of a
transcriptome from landmark genes, and a general-purpose inference or
flow-matching framework whose genomic use is one illustration.

The same test keeps out actuators that act on RNA rather than on the genome —
SINEUPs, riboswitches, aptamer-ribozyme switches — and designed protein modules
whose function is protein association.

### D4 — A claimed capability, not an evaluated task

Settles 10 labels, 4 confirmed out and 1 flipped.

C5 admits a single-cell foundation model when it predicts a perturbation
response. The question was whose claim counts, since almost any such model can
be *evaluated* on perturbation prediction by someone else.

**The resource's own claim counts.** scGPT claims perturbation prediction among
its capabilities and is in; a model that claims representation quality,
reconstruction, or cross-species transfer is out even where a later benchmark
scores it on perturbations. Otherwise C5 is decided by whatever someone else
chose to measure, and every single-cell foundation model is one benchmark away
from being in scope.

By the same test, a resource whose output is a *representation of
perturbations* rather than a predicted *response* is out.

### D5 — Observation stays out, including when an in-scope model does the observing

Settles 19 labels, all confirmed out.

The hardest version of C3, and the one that recurs: a sequence-to-function model
used to study regulatory evolution, a DNA language model used to explain
double-strand break sensitivity, in-scope models used to infer a regulatory
network. The resource is in scope. The paper's product is an explanation.

D5 and D1 meet here and agree, which is the reason to trust both: whether you
ask "does it act?" or "does something reusable ship?", a paper that uses
Enformer to tell you something about human evolution answers no twice.

Also settled out under D5, for the same reading: assay-versus-assay
comparisons, data-processing and bias-correction benchmarks, annotation, gene
finding, sequence classification for diagnostics or surveillance, clinical
coding-variant interpretation, and multi-omics data infrastructure.

### What these decisions cost, measured

227 records were out before, 240 after: the five decisions moved 13 records, all
in the same direction, and left 250 in. No label flipped from out to in, which
is worth noticing — the first pass was not systematically harsh, it was
systematically unsure about one question, D1.

Every decision is reversible and `settled_by` in `literature/scope_labels.yaml`
says which labels rest on which, so disagreeing with D1 costs re-reading 42
labels rather than all 490.

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

**Demotion.** A record that fails a criterion today is not thereby withdrawn.
Labelling is the measurement; `literature/09_demote.py` is the correction, and
it defaults every record to `keep`. A failed criterion is an argument for
withdrawing a record, not the act of withdrawing it, and the two are kept apart
so that disagreeing with a label costs nothing.
