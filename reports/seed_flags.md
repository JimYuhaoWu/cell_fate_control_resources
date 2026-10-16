# Seed data flags — v0.1

Every DOI, URL, licence and ontology id in the seed was checked against an API
(Crossref, Europe PMC, arXiv, EBI OLS4, HuggingFace) or against the
repository's own `LICENSE` file. Items here are **unverified and left null**,
not guessed.

## Corrections to the design docs

| Doc | Says | Verified |
|---|---|---|
| landscape §3 | "Enformer" | Primary DOI is `10.1038/s41592-021-01252-x`, ending **-x**. `-w` does not resolve |
| schema §9 | Borzoi primary `10.1038/s41588-024-xxxxx` (placeholder) | `10.1038/s41588-024-02053-6`, Nat Genet, issue year **2025** (entity `year: 2023` = first public release) |
| schema §9 | Flashzoi cited only as a bioRxiv `extension` | Journal version exists: `10.1093/bioinformatics/btaf467`, Bioinformatics 2025 |
| schema §6.1 | Tycko collection, 2025 | Nature Biotechnology issue year **2024**. Entity `year` and paper `year` differ by design; `ecr_lib_source_key: Tycko_2025` is unchanged because it is the join key into eCR_mod_lib |
| schema §6.1 | `modlib:tycko-2025-compact-effectors` | Uses `module:` — QC enforces that the id prefix equals `type`, so the type can be read from the id |
| database:jaspar-2024 | release branded "JASPAR 2024" | NAR issue year is **2023**. Release name and publication year disagree; normal for the NAR database issue and a recurring citation trap |

### Correction to an earlier version of this file

An earlier draft recorded `10.64898/2026.02.04.703796` (schema §9's Borzoi
benchmark paper) as not resolving, on the grounds that `10.64898` was not a
registrant I could confirm. **That was wrong, and it was asserted without
being tested.** The DOI resolves through Crossref to "Practical utility of
sequence-to-omics models for improving the reproducibility of genetic
fine-mapping", Sweeney & Kang, 2026. It is now attached as a `benchmark` paper
to `model:enformer`, `model:borzoi` and `model:alphagenome`, and it is what
lifts Borzoi to `externally-benchmarked`.

## Nulled fields

| Entity / paper | Field | Why |
|---|---|---|
| all 8 models | `n_parameters` | Not in any abstract. Borzoi's 235M (schema §9) is unverifiable from open metadata; NT spans 50M–2.5B and Evo 2 ships 7B and 40B, which one INT column cannot hold at all |
| `model:alphagenome` | `license` | API terms of use, not an SPDX licence |
| `model:gears` | `license` | No `LICENSE` file found in the repository |
| `benchmark:geneb` | `leaderboard_url` | A HuggingFace Space is reported but the URL was not confirmed |
| `benchmark:bend`, `benchmark:dart-eval` | `n_tasks` / `n_models_evaluated` | Not in open metadata |
| `dataset:*` | `n_records` | Each is split per organism (e.g. 55,497 human / 49,369 mouse for Borzoi), which is two numbers and one column |
| `dataset:replogle-2022-perturb-seq` | `accession`, `license` | GEO accession not confirmed |
| `protocol:cutrun-janssens-henikoff` | `version`, `duration_hours` | Not in the retrieved protocols.io metadata |
| `protocol:lowinput-cutrun-v2` | `protocol_doi` | schema §9's value is a literal placeholder; no DOI minted |
| `10.1038/s41588-023-01517-5` | `abstract` | Nat Genet correspondence; no abstract released by Crossref or Europe PMC |
| `10.52202/079017-1981` | `abstract` | NeurIPS proceedings record carries none |

**Curator-asserted, not API-verified:** `input_context_bp` and
`output_resolution_bp`. AlphaGenome (1 Mb) and Evo 2 (1M tokens) are stated in
their abstracts; Enformer 196,608, Borzoi/Flashzoi 524,288 and ChromBPNet 2,114
come from the design docs and field knowledge. Leaving them null would gut the
key interval-model discriminator, so they are filled and flagged here instead.

## Spec gaps found while building

1. **`vocab.facet` cannot be a DDL enum.** Facets grew from four to six during
   the draft itself, and a SQLite `CHECK` cannot be altered without rebuilding
   the table. A facet now exists iff `vocab/<facet>.yaml` exists.
2. **`architecture` had no term for a GNN**, which is the dominant architecture
   on the `what` axis. Added bottom-up for `model:gears`.
3. **`protocol_ext.category` is called controlled but ships no vocabulary.**
   `05_validate.py` reports it as unvalidated rather than inventing
   `vocab/protocol_category.yaml`.
4. **`cell_type` cannot be CL-only.** CL does not model immortalized cell
   lines, so K562 — the most common context in the effector-domain screens —
   needs EFO. The `ontology_id` column carries mixed prefixes for that facet.
5. **`n_parameters INT` cannot represent a model family.** Three of eight seed
   models ship multiple sizes under one name.

## Link checking

- **HuggingFace returns 401 to anonymous requests for some live repos**
  (`datasets/Genentech/borzoi-data` is real and 401s). 401/403/405 leave
  `alive` unknown.
- **PeiLab2 has partial outbound access** — it reaches `api.crossref.org` but
  times out on `github.com`. A connection-level failure therefore leaves
  `alive` unknown rather than false; only a server answering 404/410 counts as
  rot. The last sweep from PeiLab2: 20 alive, 9 unknown, 0 dead. Re-run from an
  unrestricted host before trusting the unknowns.
