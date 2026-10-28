"""
literature/triage_rules.py
--------------------------
The scoring tables and scorers from docs/triage_design.md, in one place.

Carries no step number because it is not a step, the same way scripts/schema.py
is not one. It exists because two callers need identical scoring:
`02_triage.py` applies it, and `triage_eval.py` measures it against the
`benchmark`/`critique` rows in db/entity_paper.tsv. The eval's whole promise --
"whenever the scoring changes, this says what the change cost" -- is only true
while both read the same numbers, and that is not true of two copies.

Records come in normalized, not as API payloads: `title`, `abstract` (plain
text, already flattened), `referenced_works`, `oa_type`. 01_search.py writes
that shape; triage_eval.py converts OpenAlex works into it.

Every weight here is from docs/triage_design.md. Change them there first: the
doc records what each one was measured against, which is the only reason to
trust any of them.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "scripts"))
# The tier arithmetic is imported, never reimplemented: scripts/schema.py is the
# one definition, and scripts/05_validate.py derives the committed tiers from
# the same three functions. A second copy here would let the number a curator is
# shown drift from the number QC will compute.
from schema import (PAPER_ROLES, classify_overlap, derive_tier,  # noqa: E402,F401
                    norm_author)


# ══ Part 1: discovery hits, scored for scope (design §1.2) ═══════════════════

# The README scope rule is a rule about *input* -- "models that take DNA
# sequence or chromatin state as their primary input" -- so these carry the
# heaviest positive weights in the whole table. They are the scope rule itself.
INPUT_GATE = {
    "dna sequence": 2.0, "genomic sequence": 2.0, "sequence-to-function": 3.0,
    "sequence to function": 3.0, "chromatin state": 2.0, "regulatory dna": 2.5,
    "cis-regulatory": 2.5, "noncoding dna": 2.0, "non-coding dna": 2.0,
}

# vocab/task.yaml, terms and synonyms. `regulatory element design` is 3.0:
# nothing out of scope uses that phrase.
TASK = {
    "coverage prediction": 2.0, "track prediction": 1.5, "profile prediction": 1.5,
    "signal prediction": 1.5,
    "variant effect prediction": 2.5, "variant scoring": 1.5,
    "variant impact prediction": 2.0,
    "contact map prediction": 2.5, "chromatin contact prediction": 2.5,
    "hi-c prediction": 2.5, "3d genome prediction": 2.5, "tad prediction": 2.0,
    "chromatin folding prediction": 2.5,
    "enhancer-promoter linking": 2.5, "enhancer-promoter interaction": 2.0,
    "regulatory linking": 2.0,
    "chromatin accessibility prediction": 2.5, "accessibility prediction": 2.0,
    "atac prediction": 2.0, "dhs prediction": 2.0,
    "splice site prediction": 2.0, "isoform prediction": 1.5,
    "polyadenylation prediction": 2.0, "polya prediction": 2.0,
    "gene expression prediction": 2.5, "expression prediction": 2.0,
    "eqtl prediction": 1.5,
    "tf binding prediction": 2.0, "tf binding": 1.5,
    "motif occupancy prediction": 2.0, "binding site prediction": 1.5,
    "motif discovery": 2.0, "de novo motif discovery": 2.0,
    "syntax discovery": 2.0,
    "sequence generation": 1.5, "sequence design": 2.0,
    "generative design": 1.5, "regulatory element design": 3.0,
    "perturbation response prediction": 2.5, "perturbation prediction": 2.0,
    "genetic perturbation response": 2.0,
    "effector domain discovery": 2.5, "effector domain screening": 2.5,
    "activation domain discovery": 2.5, "repression domain discovery": 2.5,
    "representation learning": 1.5, "self-supervised representation": 1.5,
    "histone modification prediction": 2.0, "histone mark prediction": 2.0,
    "chromatin mark prediction": 2.0,
}

# vocab/architecture.yaml. Deliberately low: architecture answers *how*, not
# *whether it is in scope*. A transformer paper is not in scope for being one.
ARCHITECTURE = {
    "convolutional neural network": 0.75, "dilated convolution": 0.75,
    "convolutional": 0.5, "resnet": 0.5,
    "transformer": 0.5, "self-attention": 0.5, "multi-head attention": 0.5,
    "state space model": 0.75, "mamba": 0.5, "hyena": 0.75,
    "denoising diffusion": 0.5, "variational autoencoder": 0.5,
    "generative adversarial network": 0.5, "normalizing flow": 0.5,
    "flow matching": 0.5, "graph neural network": 0.5,
    "graph convolutional network": 0.5, "message passing": 0.5,
}

# vocab/output_type.yaml.
OUTPUT_TYPE = {
    "coverage track": 1.5, "signal track": 1.5, "bigwig": 2.0,
    "contact matrix": 2.0, "hi-c map": 2.0, "chromatin contact": 1.5,
    "interaction matrix": 1.0, "tad map": 1.5,
    "regression output": 0.5,
    "latent vector": 0.5, "feature vector": 0.5,
    "variant score": 1.5, "effect size": 0.5, "delta prediction": 1.5,
    "generated sequence": 1.5, "designed sequence": 1.5,
    "nucleotide output": 1.0,
    "cell embedding": 1.0, "expression profile": 1.0,
    "perturbation response": 1.5,
}

# The README's own exclusions, plus observation-not-control and
# plainly-other-field. Uncapped on purpose: these are exclusions, not
# preferences.
OUT_OF_SCOPE = {
    "trajectory inference": -4.0, "rna velocity": -4.0, "pseudotime": -3.0,
    "lineage tracing": -3.0, "optimal transport": -2.5,
    "batch correction": -2.5, "cell type annotation": -2.0,
    "cell-type annotation": -2.0, "clustering": -1.5,
    "histopathology": -4.0, "whole-slide": -3.0, "radiomics": -3.0,
    "electronic health record": -4.0, "protein folding": -3.0,
    "protein structure prediction": -3.0, "drug discovery": -2.0,
    "genomic selection": -3.0, "bibliometric": -4.0,
}

# Replaces eCR_mod_lib's flat organism penalty, which would have discarded the
# multi-species DNA language models that are squarely in scope. The whole table
# is waived when a multi-species marker is present -- see score_discovery.
SINGLE_CLADE = {
    "arabidopsis": -3.0, "plant genom": -3.0, "crop": -2.5, "rice": -2.0,
    "maize": -2.0, "wheat": -2.0, "soybean": -2.0, "tomato": -2.0,
    "yeast": -2.0, "saccharomyces": -2.0, "drosophila": -2.0,
    "zebrafish": -2.0, "caenorhabditis": -2.0, "xenopus": -2.0,
    "prophage": -3.0, "plasmid": -2.0, "bacteriophage": -3.0,
}
MULTI_SPECIES = ["multi-species", "multispecies", "cross-species",
                 "all domains of life", "across species", "pan-genome"]

CLADE_FLOOR = -4.0

# eCR_mod_lib's DBD/ED/CR vocabulary, kept for the one query it still serves.
# The `with-what` axis is the only place CFCR reaches that literature.
MODULE_TERMS = {
    "effector domain": 2.0, "activation domain": 2.0, "repression domain": 2.0,
    "dna-binding domain": 2.0, "chromatin regulator": 2.0,
    "transcriptional activator": 1.5, "transcriptional repressor": 1.5,
    "krab": 2.0, "zinc finger": 1.5, "homeodomain": 1.5,
    "histone acetyltransferase": 2.0, "histone deacetylase": 2.0,
    "histone methyltransferase": 2.0, "chromatin remodel": 2.0,
    "high-throughput": 2.0, "tiling": 2.0, "massively parallel": 2.0,
    "compendium": 1.5, "screen": 1.0,
    "synthetic transcription factor": 2.0, "crispra": 1.5, "crispri": 1.5,
}

# The `how` axis -- DNA and genome language models -- has its own vocabulary and
# the interval-model tables cannot see it. Measured on five of them: under the
# `model` table Evo 2 and GROVER score 2.00 and DNABERT-2 scores 0.00, because a
# language-model paper talks about pretraining and context length, not about
# gene expression prediction. Only 2 of 5 cleared 3.0.
#
# The weights are low and the cap is 2.0 on purpose, and that is the whole
# difficulty of this table: the vocabulary is shared with everything else the
# query returns -- surveys, security papers, plant and plasmid models -- so
# raising it buys recall and spends precision almost one for one:
#
#   current (no `how` table)   2 of 5 positives    16 of 93 candidates >= 3.0
#   cap 2.0                    4 of 5              35
#   cap 3.0                    5 of 5              61
#   cap 6.0                    5 of 5              63
#
# 2.0 is the balanced point and it is a choice, not a fact. Its measured cost is
# DNABERT-2 at +2.00, which lands in the review file's deferred section rather
# than its decision section -- recorded, and it returns if these weights change.
# Nothing is left out either way.
#
# One idea that does not work, so nobody retries it: adding a table for
# "introduces a resource" (`we introduce`, `we release`, `we pretrain`) against
# one for "uses or surveys a resource" (`survey`, `we apply`, `explainable ai`).
# It reads like the right discriminator and measures worse -- DNABERT-2 falls to
# +1.00 and candidates rise to 68 of 93, because a paper introducing a model
# describes applying it too.
DNA_LM = {
    "language model": 1.0, "foundation model": 1.0,
    "genome modeling": 1.5, "genomic modeling": 1.5, "sequence modeling": 1.0,
    "pretrain": 0.75, "pre-train": 0.75, "pretrained": 0.75,
    "pre-trained": 0.75, "self-supervised": 0.75, "masked language": 1.0,
    "autoregressive": 0.75, "tokeniz": 0.75, "byte-pair": 1.0,
    "nucleotide-level": 1.0, "single-nucleotide resolution": 1.0,
    "zero-shot": 1.0, "downstream task": 1.0, "context length": 1.0,
    "long-context": 1.0, "perplexity": 1.0, "scaling law": 1.0,
}

# A benchmark paper is scored on evaluation language, not model language:
# docs/triage_design.md §1.4 measured that one table cannot serve six types.
EVALUATION_TERMS = {
    "benchmark": 2.0, "benchmarking": 2.0, "evaluation suite": 2.5,
    "systematic evaluation": 2.5, "head-to-head": 2.0, "leaderboard": 2.5,
    "baseline": 1.0, "comparative evaluation": 2.0,
    "zero-shot": 1.0, "fine-tuned": 1.0, "probing": 1.0,
}

# `dataset`, `protocol` and `database` had no table at all and fell back to the
# model one, which is why six of the nineteen catalogued entities score below
# 3.0 on their own primary paper: the Replogle Perturb-seq atlas, GEARS,
# EpiFactors, the CUT&RUN protocol and JASPAR all at 0.00-1.50. A dataset paper
# describes a resource's extent, a protocol paper describes a bench procedure,
# and a database paper describes a release -- none of them use
# sequence-model vocabulary, and no amount of tuning the model table reaches
# them. These three tables are docs/triage_design.md §1.4 finished rather than
# restated.
#
# Built from the catalogued papers' own text, not from imagination, and
# weighted so a paper needs two or three of these words rather than one: every
# term here appears in ordinary methods papers too.
DATASET_TERMS = {
    "atlas": 2.0, "genome-scale": 2.0, "genome-wide": 1.0,
    "resource": 1.0, "compendium": 2.0, "catalogue": 1.5, "catalog": 1.5,
    "landscape": 1.5, "genotype-phenotype": 2.0,
    "screen": 1.5, "screens": 1.5, "perturb-seq": 2.5,
    "single-cell": 1.0, "profiling": 1.0, "measurements": 1.0,
    "publicly available": 1.5, "accession": 2.0, "deposited": 1.5,
    "million cells": 2.0, "training data": 1.5, "held-out": 1.5,
}
PROTOCOL_TERMS = {
    "protocol": 2.5, "step-by-step": 2.5, "procedure": 1.5,
    "in situ": 1.5, "antibody": 1.5, "nuclease": 1.5, "bead": 1.0,
    "incubat": 1.0, "buffer": 1.0, "reagent": 1.5, "titrat": 1.0,
    "troubleshoot": 2.0, "hands-on": 2.0, "bench": 1.0,
    "high efficiency": 1.0, "low cell number": 2.0, "input material": 1.5,
}
DATABASE_TERMS = {
    "database": 2.5, "open-access": 2.0, "web server": 2.0,
    "web interface": 2.0, "release": 1.5, "update": 1.5, "updated": 1.0,
    "curated": 2.0, "manually curated": 2.5, "annotation": 1.0,
    "api": 1.5, "rest api": 2.0, "bulk download": 2.0,
    "profiles": 1.0, "collection": 1.0, "anniversary": 1.5,
    "track hub": 2.0, "browser": 1.0,
}

# The `what` axis -- perturbation-response models -- is the third case of the
# same finding. GEARS scores 0.00 on its own primary paper, "Predicting
# transcriptional outcomes of novel multigene perturbations", because TASK holds
# the phrases `perturbation-response-prediction` and `genetic perturbation
# response` and that title uses none of them. README keeps this axis
# deliberately shallow -- a single-cell foundation model counts when it predicts
# a perturbation response, not when it only embeds cells -- so the table leads
# on the prediction and gives the embedding nothing.
PERTURBATION_TERMS = {
    "transcriptional outcome": 2.5, "transcriptional response": 2.0,
    "perturbation response": 2.5, "perturbation effect": 2.0,
    "multigene": 2.0, "combinatorial perturbation": 2.5,
    "genetic perturbation": 2.0, "gene knockout": 1.5, "knockdown": 1.0,
    "crispri": 1.5, "crispra": 1.5, "crispr screen": 1.5,
    "unseen perturbation": 2.5, "novel perturbation": 2.5,
    "dose": 1.0, "drug response": 1.5, "chemical perturbation": 2.0,
    "cell state": 1.5, "post-perturbation": 2.0,
}

# (expect_type, fate_axis) -> the tables that score it, each with its cap. Both
# fields are declared by every query in search_queries.yaml already (design
# §1.4: the triage hint becomes the table selector). The axis is part of the key
# because `model` covers an interval model and a DNA language model, and those
# two do not share a vocabulary -- see DNA_LM above.
TABLES: dict[tuple[str, str | None], list[tuple[str, dict, float]]] = {
    ("model", None): [("input", INPUT_GATE, 6.0), ("task", TASK, 8.0),
                      ("arch", ARCHITECTURE, 2.5), ("output", OUTPUT_TYPE, 3.0)],
    ("model", "how"): [("dna_lm", DNA_LM, 2.0), ("input", INPUT_GATE, 6.0),
                       ("task", TASK, 8.0), ("output", OUTPUT_TYPE, 3.0)],
    ("model", "what"): [("perturbation", PERTURBATION_TERMS, 6.0),
                        ("task", TASK, 6.0), ("output", OUTPUT_TYPE, 3.0)],
    ("benchmark", None): [("eval", EVALUATION_TERMS, 6.0),
                          ("input", INPUT_GATE, 6.0), ("task", TASK, 4.0)],
    ("module", None): [("module", MODULE_TERMS, 8.0), ("input", INPUT_GATE, 2.0)],
    ("dataset", None): [("dataset", DATASET_TERMS, 8.0), ("task", TASK, 4.0),
                        ("input", INPUT_GATE, 4.0)],
    ("protocol", None): [("protocol", PROTOCOL_TERMS, 8.0),
                         ("assay", MODULE_TERMS, 2.0)],
    ("database", None): [("database", DATABASE_TERMS, 8.0),
                         ("input", INPUT_GATE, 4.0), ("task", TASK, 4.0)],
}


def tables_for(expect_type, fate_axis):
    """Most specific first: (type, axis), then (type, None), then the model table."""
    return (TABLES.get((expect_type, fate_axis))
            or TABLES.get((expect_type, None))
            or TABLES[("model", None)])


# ══ Part 2: citing works, scored for what they do to a catalogued model ══════

# "Names a model class rather than a model" is the whole reason list B exists:
# the two catalogued critiques of Enformer never write the word "Enformer".
CLASS_TERMS = [
    "genomic deep learning", "sequence-to-function", "sequence to function",
    "dna language model", "genomic language model", "genome language model",
    "genomic foundation model", "dna foundation model", "foundation model",
    "state-of-the-art model", "current model", "current approaches",
    "deep learning model", "sequence model",
]
BENCH_TITLE = [
    "benchmark", "benchmarking", "evaluation", "evaluating", "evaluate",
    "comparison", "comparative", "compare", "assessment", "assessing", "assess",
    "baseline", "leaderboard", "head-to-head", "systematic",
]
BENCH_ABSTRACT = BENCH_TITLE + [
    "we evaluate", "we compare", "we benchmark", "we assess", "across models",
    "evaluated on", "four state-of-the-art", "three state-of-the-art",
]
CRIT_TITLE = [
    "fail", "fails", "struggle", "struggles", "poorly", "overestimat",
    "underestimat", "limitation", "caveat", "cannot", "pitfall", "overstate",
    "illusion", "spurious", "confound", "underperform", "inflated",
    "misleading", "hard to compare", "not generalize", "questioning",
    "reassess", "overlooked",
]
CRIT_ABSTRACT = CRIT_TITLE + [
    "fails to", "struggle to", "poorly explained", "limited performance",
    "no better than", "worse than", "artifact", "remains unexplored",
    "often fail", "incorrect direction",
]
# `review` is a legitimate entity_paper role, so these demote rather than
# exclude: a review that evaluates models is still worth a curator's glance.
DEMOTE_TITLE = ["review", "perspective", "primer", "roadmap", "erratum",
                "correction", "retraction"]


# ══ Matching ════════════════════════════════════════════════════════════════

def hits(terms, text: str) -> list[str]:
    """Terms present in `text`, left-anchored on a word boundary."""
    return [t for t in terms if re.search(r"(?<![a-z])" + re.escape(t), text)]


def names(forms: set[str], text: str) -> bool:
    return any(re.search(r"(?<![a-z0-9])" + re.escape(f.lower()) + r"(?![a-z0-9])", text)
               for f in forms)


def _table(table: dict, title: str, abstract: str, cap: float) -> float:
    """A term in the title counts double (design §1.2); the total is capped."""
    total = sum(w for t, w in table.items()
                if re.search(r"(?<![a-z])" + re.escape(t), title)) * 2
    total += sum(w for t, w in table.items()
                 if re.search(r"(?<![a-z])" + re.escape(t), abstract))
    return min(total, cap) if cap else total


def score_discovery(rec: dict) -> tuple[float, dict]:
    """
    Scope score for one discovery hit, and the per-table breakdown the review
    file prints so a curator can see what moved it.
    """
    title = (rec.get("title") or "").lower()
    abstract = (rec.get("abstract") or "").lower()
    tables = tables_for(rec.get("expect_type"), rec.get("fate_axis"))

    parts = {name: _table(tbl, title, abstract, cap)
             for name, tbl, cap in tables}
    parts = {k: v for k, v in parts.items() if v}

    both = f"{title} || {abstract}"
    off = _table(OUT_OF_SCOPE, title, abstract, 0.0)
    if off:
        parts["out_of_scope"] = off
    if not hits(MULTI_SPECIES, both):
        clade = _table(SINGLE_CLADE, title, abstract, 0.0)
        if clade:
            # Floored, not uncapped: one stray "yeast" in a comparison should
            # not sink an in-scope human model. Design §1.6.1 records what that
            # choice costs -- a genuine Arabidopsis model scores back over 3.0.
            parts["single_clade"] = max(clade, CLADE_FLOOR)
    return round(sum(parts.values()), 2), parts


# ══ Citing-work scorers (design §2.2, §2.3) ═════════════════════════════════

def lexicon(title: str, abstract: str) -> tuple[float, float]:
    bench = (min(2.0 * len(hits(BENCH_TITLE, title)), 4.0)
             + min(0.5 * len(hits(BENCH_ABSTRACT, abstract)), 2.0))
    crit = (min(2.5 * len(hits(CRIT_TITLE, title)), 5.0)
            + min(0.75 * len(hits(CRIT_ABSTRACT, abstract)), 3.0))
    return bench, crit


def propose_role(bench: float, crit: float) -> str:
    if crit > bench:
        return "critique"
    return "benchmark" if bench > 0 else "unclear"


def _context(rec: dict, primaries: dict, entity: str | None):
    title = (rec.get("title") or "").lower()
    abstract = (rec.get("abstract") or "").lower()
    refs = {r.rsplit("/", 1)[-1] for r in (rec.get("referenced_works") or [])}
    own = primaries.get(entity) if entity else None
    cited = sorted(e for e, oa in primaries.items() if oa and oa in refs)
    n_shared = len({primaries[e] for e in cited if primaries[e] != own})
    return title, abstract, f"{title} || {abstract}", cited, n_shared


def score_named(rec, entity, primaries, model_forms, all_forms):
    """
    List A: the citing paper cites this entity's `primary` paper.

    Gated on the reference list, not on the entity's name. Measured over the
    7,002 cached citing rows of 2026-10-21, against the curated
    `benchmark`/`critique` rows as truth: the name gate reached 110 of the 283
    present in that corpus, and this gate reaches all 283. The swept primary
    appears in `referenced_works` for 7,002 of 7,002, so the match is exact
    and costs no request -- every citing row already carries the list.

    The name gate could not have been fixed by widening it. A record whose
    paper introduces no named resource is named after its citation since
    `fec702d` -- `Wang 2025 Benchmarking translational potential` -- and no
    paper writes that in prose, so 392 of the 472 records holding only a
    primary paper were unreachable by any name match.

    The name still *scores* where it appears, because a paper that names the
    resource is more likely to be about it than one that only cites it: on the
    reference gate alone the threshold keeps 269 of the 283, and the name bonus
    carries the last 14 over it.

    This gate admits every swept row, so it decides nothing on its own and the
    threshold in 02_triage.py is what holds the list to a readable size.
    """
    title, abstract, both, cited, n_shared = _context(rec, primaries, entity)
    if entity not in cited:
        return None
    parts = {"ref_primary": 3.0}
    if names(all_forms.get(entity, set()), title):
        parts["name_title"] = 3.0
    elif names(all_forms.get(entity, set()), abstract):
        parts["name_abstract"] = 1.5
    bench, crit = lexicon(title, abstract)
    parts["bench_lex"], parts["crit_lex"] = bench, crit
    others = sum(1 for e, f in model_forms.items() if e != entity and names(f, both))
    parts["multi_model"] = {0: 0.0, 1: 0.5, 2: 1.5}.get(others, 3.0)
    parts["ref_overlap"] = min(0.75 * n_shared, 3.0)
    if hits(DEMOTE_TITLE, title):
        parts["demote_title"] = -3.0
    if (rec.get("oa_type") or "") == "review":
        parts["demote_type"] = -3.0
    return round(sum(parts.values()), 2), propose_role(bench, crit), parts


def score_class(rec, primaries, model_forms):
    """List B: names no catalogued model, but talks like an evaluation of a class."""
    title, abstract, both, cited, n_shared = _context(rec, primaries, None)
    if any(names(f, both) for f in model_forms.values()):
        return None
    if not hits(CLASS_TERMS, both):
        return None
    bench, crit = lexicon(title, abstract)
    if bench + crit < 2.0:
        return None
    parts = {"class_term": 1.0, "bench_lex": bench, "crit_lex": crit,
             "ref_overlap": min(0.75 * n_shared, 4.5)}
    if hits(DEMOTE_TITLE, title):
        parts["demote_title"] = -3.0
    if (rec.get("oa_type") or "") == "review":
        parts["demote_type"] = -3.0
    return round(sum(parts.values()), 2), propose_role(bench, crit), cited, bool(abstract)


# ══ Repository inputs ═══════════════════════════════════════════════════════

def read_repo():
    """
    What both callers need from the committed snapshots: paper titles, the name
    forms each entity answers to, each entity's `primary` paper, the
    (entity, paper) pairs already joined, and the ground-truth
    `benchmark`/`critique` rows the eval measures against.
    """
    def rows(path: str) -> list[dict]:
        with (ROOT / path).open(encoding="utf-8") as fh:
            return list(csv.DictReader(fh, delimiter="\t"))

    titles = {r["paper_id"]: r["title"] for r in rows("db/papers.tsv")}
    all_forms, model_forms = {}, {}
    for r in rows("db/entities.tsv"):
        forms = {r["name"]}
        try:
            forms |= set(json.loads(r["aliases"] or "[]"))
        except (ValueError, TypeError):
            pass
        # Aliases under four characters are dropped: "NT" matches every abstract.
        forms = {f for f in forms if len(f) >= 4}
        if forms:
            all_forms[r["entity_id"]] = forms
            if r["entity_id"].startswith("model:"):
                model_forms[r["entity_id"]] = forms

    primary, linked, truth = {}, set(), []
    for ep in rows("db/entity_paper.tsv"):
        linked.add((ep["entity_id"], ep["paper_id"]))
        if ep["role"] == "primary":
            primary[ep["entity_id"]] = ep["paper_id"]
        elif ep["role"] in ("benchmark", "critique"):
            truth.append((ep["entity_id"], ep["paper_id"], ep["role"]))
    return titles, all_forms, model_forms, primary, linked, truth


# ══ Routing: which role proposals can change a derived tier ═════════════════
#
# The point of this section is to cut what a human must decide without deciding
# anything for them. `evidence_tier` is derived from the `benchmark` and
# `critique` rows attached to an entity, and the derivation saturates: once one
# independent evaluation exists, the tier is `externally-benchmarked` and no
# further row can move it. A proposal that cannot move the tier still gets
# recorded -- leaving out related work is not the goal and never has been -- it
# just does not need to interrupt anyone.
#
# Author overlap is what decides this, and it is still absent from every score
# in this module. It routes the question; it does not answer it. The difference
# matters, because a score that used overlap would pre-filter the rows reaching
# QC and the derived tier would then measure this file instead of the
# literature (design §2.4).


def read_tier_state() -> dict[str, dict]:
    """
    entity -> {primary_authors, evaluations, tier} from the committed snapshots.

    `tier` is None for an entity that carries no evaluation yet: there is no
    tier to preserve, so the first accepted evaluation always changes something.

    It is also None when evaluations exist but `derive_tier` cannot classify
    any of them. Both mean "no tier to preserve", which is why one value covers
    them, and `tier_effect` sends either to a human.
    """
    def rows(path: str) -> list[dict]:
        with (ROOT / path).open(encoding="utf-8") as fh:
            return list(csv.DictReader(fh, delimiter="\t"))

    authors = {}
    for r in rows("db/papers.tsv"):
        authors[r["paper_id"]] = {norm_author(a) for a
                                  in json.loads(r["authors"] or "[]")} - {""}

    primary, evals = {}, {}
    for j in rows("db/entity_paper.tsv"):
        if j["role"] == "primary":
            primary[j["entity_id"]] = j["paper_id"]
        elif j["role"] in ("benchmark", "critique"):
            evals.setdefault(j["entity_id"], []).append(j["paper_id"])

    state = {}
    for entity, pid in primary.items():
        evaluations = [(x, authors.get(x, set())) for x in evals.get(entity, [])]
        state[entity] = {
            "primary_authors": authors.get(pid, set()),
            "evaluations": evaluations,
            "tier": (derive_tier(authors.get(pid, set()), evaluations)[0]
                     if evaluations else None),
        }
    return state


def tier_effect(state: dict, candidate_authors: list[str] | None) -> tuple[str, str]:
    """
    What accepting this proposal would do to the entity's tier.

    Returns (verdict, explanation) where verdict is:
      "needs-human"  the tier would change, or cannot be computed
      "no-effect"    the tier is already what it would be afterwards

    An author list we do not have is **never** treated as no-effect. Those go
    to a human.

    That guard was written to compensate for a defect: `classify_overlap` used
    to return "independent" for an empty author list, because its `if not
    shared` test ran before its `if not evaluating` test and made the "unknown"
    branch unreachable -- the strongest possible evidence read off the weakest
    possible data. `whochecked.overlap` fixes it, so the guard now agrees with
    the classifier instead of working around it.

    It stays, for the reason it would have been written anyway: this function
    answers "would accepting this move the tier", and for a candidate with no
    authors the honest answer is that nobody can say. Returning no-effect on an
    "unknown" verdict would hide the proposal from the curator precisely when
    the evidence is weakest.
    """
    if not candidate_authors:
        return "needs-human", "no author list; independence cannot be computed"

    theirs = {norm_author(a) for a in candidate_authors} - {""}
    if not theirs:
        return "needs-human", "author list did not normalize to anything"

    before = state["tier"]
    after = derive_tier(state["primary_authors"],
                        state["evaluations"] + [("candidate", theirs)])[0]
    kind = classify_overlap(state["primary_authors"], theirs)[0]
    if after is None:
        # `derive_tier` returns None when every evaluation classifies as
        # `unknown`, which here means the entity's own primary paper has no
        # author list. Nothing can be said about what accepting this would do,
        # and this is the case the old defect hid: the classifier used to call
        # it `independent`, so `after` came back `externally-benchmarked` and
        # the row reached a human by accident rather than on purpose.
        return "needs-human", ("no tier can be derived; the primary paper has "
                               "no author list")
    if before is None:
        return "needs-human", f"first evaluation; would set tier to {after}"
    if after != before:
        return "needs-human", f"would move {before} to {after}"
    return "no-effect", f"{kind}; tier stays {before}"


# ══ The decision ledger ═════════════════════════════════════════════════════
#
# literature/decisions.yaml: every decision a curator made in a review file,
# keyed by paper. It lives here beside read_repo() and read_tier_state()
# because two scripts need it and neither may keep its own copy of the key --
# 03_record.py writes the ledger, 02_triage.py reads the rejections back so a
# recorded no is not re-proposed from scratch next cycle.
#
# Deferrals are deliberately NOT suppressed: the review file promises they
# return if the scoring changes or a vocabulary grows, and that promise is the
# reason a low score defers rather than rejects.

DECISIONS_FILE = ROOT / "literature" / "decisions.yaml"

DECISIONS_HEADER = """\
# literature/decisions.yaml
#
# The ledger. Every decision made in a review file, keyed by paper, written by
# literature/03_record.py and read back by literature/02_triage.py.
#
# It exists so a rejection is recorded once. An unrecorded no comes back as a
# candidate every cycle, and the curator pays for it again -- which is why
# `rejected` entries are suppressed from the next review file and the count is
# printed in its header. `deferred` entries are not suppressed: a low score is
# not a no, and the review file promises they return if the scoring changes.
#
# The key is the paper's `paper_id` (a DOI) where it has one, else
# `europepmc:<PMCID>` or `openalex:<W-id>`. Those two prefixes are ledger keys
# only -- schema.py keys a paper on a DOI or an `arxiv:` id, and a candidate
# with neither cannot become a record until someone finds its DOI.
#
# The value is a LIST, because one paper carries more than one decision: it
# reaches discovery as a candidate and list A as a role proposal for each
# entity it names. Each entry says which list it came from and, for a role
# decision, which entities it was attached to.
"""


def ledger_key(rec: dict) -> str:
    """The ledger's key for a discovery hit or a citing work."""
    if rec.get("paper_id"):
        return rec["paper_id"]
    if rec.get("doi"):
        return rec["doi"]
    if rec.get("europepmc_id"):
        return f"europepmc:{rec['europepmc_id']}"
    return f"openalex:{rec['openalex_id']}"


def read_decisions() -> dict[str, dict]:
    if not DECISIONS_FILE.exists():
        return {}
    import yaml
    return yaml.safe_load(DECISIONS_FILE.read_text(encoding="utf-8")) or {}


def write_decisions(new: dict[str, dict]) -> int:
    """
    Merge entries into the ledger, newest wins, sorted by key.

    Sorted so the file's diff shows what a cycle decided rather than where it
    appended, and rewritten whole because a mapping cannot be appended to.
    """
    import yaml
    merged = read_decisions()
    merged.update(new)
    body = yaml.safe_dump(merged, sort_keys=True, allow_unicode=True,
                          default_flow_style=False, width=76)
    DECISIONS_FILE.write_text(DECISIONS_HEADER + "\n" + body, encoding="utf-8",
                              newline="")
    return len(merged)
