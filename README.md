# Cell Fate Control Resources (CFCR)

A curated index of the **models, benchmarks, datasets, module collections,
protocols and databases** you need to control cell fate — organized not by
method, but by *what each resource lets you do*.

**Status: v0.1 skeleton.** 20 seed records chosen to stress the schema, not to
be comprehensive. The backfill has not started.

Sibling project to [`eCR_mod_lib`](https://github.com/JimYuhaoWu/eCR_mod_lib),
whose pipeline pattern this follows: structured records as the source of truth,
SQLite as a build artifact, committed TSV snapshots so every curation change is
reviewable in a `git diff`.

---

## The organizing principle: `fate_axis`

Every list in this space is organized by model architecture — "GAN-based",
"Transformer-based" — which is the wrong index for someone trying to get
something done. CFCR files each resource under the question it answers:

| `fate_axis` | Question | Typical entities |
|---|---|---|
| `where` | Where on the genome do I act? | Enformer, Borzoi, AlphaGenome, ChromBPNet |
| `what` | What do I perturb, with what cell-level effect? | GEARS, perturbation models |
| `how` | How do I represent and score sequence? | Nucleotide Transformer, Evo 2 |
| `with-what` | What do I build the actuator from? | DBD / ED / CR module collections |

The axis is multi-valued, and datasets, benchmarks and protocols inherit the
axis of whatever they serve.

**`what` is deliberately shallow.** Perturbation modelling is covered properly
by the Stegle group's
[living catalogue](https://interp-extrap-perturb.readthedocs.io) of >152
methods. CFCR points outward rather than competing.

## What makes it a database rather than a list

Papers are **evidence attached to entities**, not the records themselves. A
single `entity_paper` join carries a `role` — `primary`, `preprint`,
`benchmark`, `critique`, `application`, `extension`, `review` — which makes one
query possible that no existing list can serve:

> *Which models has anyone outside the originating group actually checked?*

```python
from cfcr import load

load(type="model", evidence_tier="externally-benchmarked")
```

`evidence_tier` is **derived, never asserted.** QC recomputes it from the
attached evaluation papers and their author overlap with the primary paper, and
fails the build if a record claims otherwise. It measures *independence only*:
a model is not promoted for being evaluated repeatedly by the same group.

| tier | meaning |
|---|---|
| `externally-benchmarked` | at least one evaluation shares no authors with the primary paper |
| `partially-independent` | an evaluation shares some authors, but under half of its own author list |
| `self-reported` | every evaluation comes from substantially the same group, or there is none |

Two further decisions worth knowing before you use the data:

- **Availability and evidence are orthogonal.** `availability_tier` is
  `open-source` / `open-weights` / `api-only`. A well-validated model can be
  unusable in your setting; a permissive one can be unchecked. They are
  separate columns because they are separate questions.
- **Benchmarks are indexed, never run.** CFCR stores no per-model scores.
  [GENEB](https://github.com/darlednik/GENEB) owns evaluation, and its own
  headline finding — that aggregate leaderboards are unstable and rankings
  vary sharply by task category — is the reason copying numbers here would
  mislead within a release cycle.

## Quickstart

```bash
conda env create -f environment.yml
conda activate cfcr
pip install -e .
```

Reading the catalogue needs nothing but the committed snapshots in `db/`:

```python
from cfcr import load, load_papers, load_links, facets

load(type="model")                                     # all models, flat frame
load(type="model", fate_axis="where", organism="mouse")
load(type="model", availability_tier="open-weights")   # check the licence!
load(type="protocol", validation_tier="published-peer-reviewed")

load_papers("model:enformer", role="critique")         # the evidence trail
load_links("model:enformer")                           # code, weights, docs
facets("model")                                        # what filters accept
```

List-valued columns (`organism`, `assay`, `task`, `fate_axis`, `architecture`,
…) filter by membership; everything else by equality, and any filter accepts a
list to mean "any of".

### Rebuilding from source

```bash
python scripts/04_build.py        # records/ + vocab/ + papers.yaml -> SQLite -> TSV
python scripts/05_validate.py     # QC; exits 1 on any ERROR
python scripts/05_validate.py --check-links   # adds the link-rot sweep
```

`db/cfcr.db` is git-ignored; `db/entities.tsv`, `db/papers.tsv`,
`db/entity_paper.tsv` and `db/links.tsv` are committed, and are what the loader
reads.

## Repository layout

```
config/      external sources, QC whitelist
vocab/       controlled vocabularies, one file per facet
records/     curated entities, one file per type  <- the source of truth
literature/  papers.yaml: harvested open paper metadata
scripts/     schema.py, 04_build.py, 05_validate.py
db/          SQLite (ignored) + committed TSV snapshots + manifests
reports/     QC output for the curator
site/        GitHub Pages front-end (not yet built)
```

## Contributing

Curation *is* the product, so inclusion is a human decision. Discovery will be
automated; approval will not.

1. **Open an issue** naming the resource, what it lets someone do, and its
   `fate_axis`. For a model, say whether anyone outside the authoring group has
   evaluated it — that is the hardest field to fill and the most valuable.
2. **Add a record** to the right `records/*.yaml`. Follow a neighbouring entry;
   the file headers state the conventions that QC enforces.
3. **Add its papers** to `literature/papers.yaml`. Verify every DOI against
   Crossref or Europe PMC. Do not write identifiers from memory — leave a field
   null rather than guessing, and the flag will be picked up in review.
4. **Run the build and QC**, and include the output:
   ```bash
   python scripts/04_build.py && python scripts/05_validate.py
   ```
   `05_validate.py` checks vocabulary membership, paper existence, reference
   cycles, duplicates and the `evidence_tier` derivation, and its messages say
   what to change.

Vocabularies grow bottom-up: put a new term in free-text `tags`, and QC
promotes it to `reports/vocab_candidates.md` once enough records share it.
Don't design vocabulary in advance.

### Entity granularity

One entity per *named, independently citable artifact*.

- Replicate checkpoints of one model are **one** entity.
- A re-implementation or port under its own name is a **separate** entity with
  `variant_of` set (Flashzoi → Borzoi).
- A successor with its own paper is a **separate** entity with `supersedes` set
  (Borzoi → Enformer). Succession is a claim made by the follower; it does not
  change the precedent's `status`.

## Licences

Deliberately split:

- **Code** — MIT. See [`LICENSE`](LICENSE).
- **Curated metadata** — CC-BY-4.0. See [`LICENSE-DATA`](LICENSE-DATA).

Neither covers the resources being catalogued, which keep their own licences
(recorded per record where verifiable), nor the paper abstracts, which remain
under their publishers' terms. CFCR stores only open metadata and no full text
of paywalled work.
