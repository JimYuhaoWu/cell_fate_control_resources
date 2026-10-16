# Seed data flags — v0.1

Every field below was checked against Crossref / Europe PMC / the HuggingFace
API. Items here are **unverified and left null**, not guessed.

## Corrections to the design docs

| Doc | Says | Verified |
|---|---|---|
| schema §9 | Borzoi primary `10.1038/s41588-024-xxxxx` (placeholder) | `10.1038/s41588-024-02053-6`, Nat Genet, issue year **2025** |
| landscape §3 | "Enformer" | Primary DOI is `10.1038/s41592-021-01252-x` (ends **-x**; `-w` does not resolve) |
| schema §6.1 | Tycko collection, paper year 2025 | Nature Biotechnology, issue year **2024**. Entity `year` and paper `year` will differ; `ecr_lib_source_key: Tycko_2025` is kept unchanged because it is a join key into eCR_mod_lib |
| schema §9 | `10.64898/2026.02.04.703796` cited as a Borzoi `benchmark` | **Does not resolve.** Prefix `10.64898` is not a registrant I can confirm. Omitted from the seed |
| schema §9 | Flashzoi cited only as a bioRxiv `extension` | Journal version now exists: `10.1093/bioinformatics/btaf467`, Bioinformatics 2025 |

## Nulled fields

| Entity | Field | Why |
|---|---|---|
| `model:enformer` | `n_parameters` | Not in the abstract; no API source |
| `model:borzoi` | `n_parameters` | schema §9 asserts 235,000,000 — not verifiable from open metadata |
| `model:flashzoi` | `n_parameters` | Not in the abstract |
| `10.1038/s41588-023-01517-5` | `abstract` | Nature Genetics correspondence; no abstract released by Crossref or Europe PMC |
| `10.52202/079017-1981` | `abstract` | NeurIPS proceedings record carries no abstract |

`input_context_bp` / `output_resolution_bp` are filled from the design docs and
established field knowledge, **not** from an API — they are the key
discriminator for interval models so leaving them null would gut the facet.
Treat them as curator-asserted rather than verified.

## Dropped link

`https://huggingface.co/google/enformer-official-rough` — the HF API response is
ambiguous about whether this repo exists. No `weights` link is recorded for
`model:enformer`; the link-rot sweep should not be given a URL that may 404.

**Note for the link checker:** HuggingFace returns `401` to anonymous requests
for some real repos (`datasets/Genentech/borzoi-data` is live but 401s). The QC
sweep must treat 401/403 as *unknown*, not dead, or it will mark live links rotten.
