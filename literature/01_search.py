#!/usr/bin/env python
"""
literature/01_search.py
-----------------------
Fetch candidate papers for review. Writes literature/candidates/YYYY-MM-DD.json
and nothing else; inclusion is 02_triage.py's output and a human's decision.

Two fetches, because docs/triage_design.md establishes that they are different
problems:

  discovery   the eight queries in search_queries.yaml, over Europe PMC and
              arXiv. Finds resources -- models, benchmarks, datasets.
  citing      every work citing a catalogued entity's `primary` paper, from
              OpenAlex. Finds the `benchmark` and `critique` papers that
              evidence_tier is derived from, which no keyword query finds.

Adapted from eCR_mod_lib's literature/01_search.py, with two deliberate
departures: its sources were PubMed and Semantic Scholar (see
config/sources.yaml for why CFCR's are not), and its `_get` returns None when
every retry fails. That silence is how a dropped request nulls an author list,
and evidence_tier is derived from author lists -- so this one raises.

Both halves are cached under literature/candidates/ as they are fetched, so a
run that dies partway through is resumed by running it again rather than
started over. To force a fresh fetch, delete the caches:

    rm literature/candidates/discovery_*.json literature/candidates/sweep_*.json

Deleting one of them re-fetches just that query or that paper.

Run from project root (needs the [literature] extra and network):
    python literature/01_search.py [--config literature/search_queries.yaml]
                                   [--dry-run] [--discovery-only]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
LIT_DIR = ROOT / "literature"
CANDIDATES_DIR = LIT_DIR / "candidates"

def _contact_email() -> str:
    """
    The address external services are given, read from the file that declares
    those services. config/sources.yaml is its one home on purpose: a copy in
    a script means changing or withdrawing the address needs every copy found.
    """
    sources = yaml.safe_load(
        (ROOT / "config" / "sources.yaml").read_text(encoding="utf-8"))
    for api in sources["metadata_apis"]:
        if api.get("contact_email"):
            return api["contact_email"]
    raise SystemExit("no contact_email in config/sources.yaml")


MAILTO = _contact_email()
UA = f"cfcr-literature/0.1 (mailto:{MAILTO})"

EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ARXIV = "https://export.arxiv.org/api/query"
OPENALEX = "https://api.openalex.org/works"

# Read from the environment and stored nowhere, for the same reason 07_enrich.py
# reaches GitHub through `gh` instead of holding a token: a key written into the
# repository is a key in its history, and this history is public and permanent.
# Absent is a supported state -- discovery needs no key, and the keyless budget
# answers a few hundred citation calls -- so run_sweep says so and carries on
# rather than exiting. The warning lives there and not here because 07_enrich.py
# imports this module for its `_get` and touches OpenAlex never.
OPENALEX_KEY = os.environ.get("OPENALEX_API_KEY") or None

# What 02_triage.py scores a citing work on (docs/triage_design.md §2.2):
# title, abstract, type, and the reference list the model-count signal reads.
# `authorships` is here for display only: docs/triage_design.md §2.4 wants the
# review file to show author overlap with the primary paper as context, while
# the score ignores it -- scoring it would make the derived evidence_tier
# measure triage's own filter instead of the literature.
OA_SELECT = ("id,doi,title,publication_year,type,primary_location,authorships,"
             "referenced_works,referenced_works_count,abstract_inverted_index")

ATOM = {"a": "http://www.w3.org/2005/Atom",
        "o": "http://a9.com/-/spec/opensearch/1.1/"}


# ── HTTP ─────────────────────────────────────────────────────────────────────

class FetchError(RuntimeError):
    """One source gave up after its retries. Recorded, not fatal."""


# The longest `Retry-After` this will sit through. A per-second 429 asks for a
# few seconds and is worth waiting out; OpenAlex's daily-budget 429 sends the
# seconds until midnight UTC -- 58,069 of them when this was found -- and
# sleeping on that parks the process for sixteen hours having printed one line.
# Above the cap the wait becomes a FetchError, which is the exit this module is
# already built around: `cached_citing` writes each paper's citing set as it
# arrives so that a failed run is resumed by running it again.
MAX_RETRY_AFTER = 60


def _get(url: str, params: dict, parse: str = "json"):
    """
    Four attempts, then give up loudly. Honours Retry-After up to
    MAX_RETRY_AFTER when the server sends one; otherwise backs off 3s, 6s, 9s
    -- arXiv asks for a few seconds between calls and OpenAlex charges nothing
    for a per-second 429.
    """
    for attempt in range(4):
        try:
            # The key goes in a header, not the query string, and only to
            # OpenAlex: `_get` also serves Europe PMC and arXiv, and a query
            # string is the part of a request that gets logged.
            headers = {"User-Agent": UA}
            if url == OPENALEX and OPENALEX_KEY:
                headers["Authorization"] = f"Bearer {OPENALEX_KEY}"
            r = requests.get(url, params=params, headers=headers, timeout=60)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 10))
                if wait > MAX_RETRY_AFTER:
                    raise FetchError(
                        f"rate limited for {wait}s, longer than the "
                        f"{MAX_RETRY_AFTER}s this will wait -- a quota rather "
                        f"than a burst. Nothing already fetched is lost; run "
                        f"again once it resets. {url} {params}")
                print(f"    rate limited, waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json() if parse == "json" else ET.fromstring(r.content)
        except FetchError:
            # Not retryable, and `except Exception` below would swallow it
            # back into the loop.
            raise
        except Exception as exc:                        # noqa: BLE001
            print(f"    retry {attempt + 1}: {exc}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise FetchError(f"no answer from {url} after 4 attempts: {params}")


# ── Europe PMC ───────────────────────────────────────────────────────────────

def search_europepmc(query: str, min_year: int, max_results: int) -> list[dict]:
    """resultType=core, because triage scores abstracts and QC needs authors."""
    window = f"(FIRST_PDATE:[{min_year}-01-01 TO {date.today().isoformat()}])"
    data = _get(EUROPEPMC, {
        "query": f"{' '.join(query.split())} AND {window}",
        "format": "json", "resultType": "core", "pageSize": min(max_results, 100),
    })
    out = []
    for r in data.get("resultList", {}).get("result", []):
        doi = (r.get("doi") or "").lower() or None
        authors = [a["fullName"] for a
                   in (r.get("authorList") or {}).get("author", [])
                   if a.get("fullName")]
        out.append({
            "source": "europepmc",
            "paper_id": doi,
            "doi": doi,
            # Kept because 2 of 326 hits in the first real run were PMC records
            # carrying a PMCID and nothing else -- no DOI, journal, abstract or
            # authors. They cannot become `paper_id` (records/ take a DOI or an
            # arxiv: id) and triage has nothing to score, so this is the only
            # handle a curator has for looking one up.
            "europepmc_id": r.get("id"),
            "title": (r.get("title") or "").rstrip("."),
            "abstract": r.get("abstractText") or None,
            "authors": authors or None,
            "year": int(r["pubYear"]) if (r.get("pubYear") or "").isdigit() else None,
            "venue": r.get("journalTitle") or None,
            # SRC:PPR is Europe PMC's own marker for a preprint record.
            "venue_type": "preprint" if r.get("source") == "PPR" else "journal",
        })
    return out


# ── arXiv ────────────────────────────────────────────────────────────────────

def search_arxiv(query: str, min_year: int, max_results: int) -> list[dict]:
    """
    No date filter in the query: arXiv's API has no usable publication-date
    range, so min_year is applied after the fetch.
    """
    root = _get(ARXIV, {"search_query": query, "max_results": max_results},
                parse="xml")
    out = []
    for e in root.findall("a:entry", ATOM):
        published = (e.findtext("a:published", default="", namespaces=ATOM))[:4]
        year = int(published) if published.isdigit() else None
        if year and year < min_year:
            continue
        # http://arxiv.org/abs/2311.12570v1 -> arxiv:2311.12570, the paper_id
        # form records/ and db/papers.tsv already use.
        raw = e.findtext("a:id", default="", namespaces=ATOM).rsplit("/", 1)[-1]
        out.append({
            "source": "arxiv",
            "paper_id": "arxiv:" + raw.split("v")[0],
            "doi": None,
            "title": " ".join(e.findtext("a:title", "", ATOM).split()),
            "abstract": " ".join(e.findtext("a:summary", "", ATOM).split()) or None,
            "authors": [" ".join(a.findtext("a:name", "", ATOM).split())
                        for a in e.findall("a:author", ATOM)] or None,
            "year": year,
            "venue": "arXiv",
            "venue_type": "preprint",
        })
    return out


# ── OpenAlex citation sweep ──────────────────────────────────────────────────

def openalex_doi(paper_id: str) -> str:
    """
    The DOI to resolve a catalogued paper_id by.

    arXiv mints `10.48550/arXiv.<id>` for every submission and OpenAlex indexes
    it, so an arXiv id resolves exactly and in the same call shape as any other
    -- 111 of the 471 primary papers are arXiv ids, and each used to cost a
    fuzzy title search of its own. OpenAlex echoes the DOI lower-cased, so
    anything keyed on the value it returns has to fold case.
    """
    return ("10.48550/arXiv." + paper_id.split(":", 1)[1]
            if paper_id.startswith("arxiv:") else paper_id)


def resolve_openalex(paper_id: str, title: str | None) -> str | None:
    """
    paper_id -> OpenAlex short id, by DOI.

    The title search is the fallback for a paper OpenAlex does not hold under
    its DOI. It used to be the arXiv path, on the premise that arXiv ids carry
    no DOI; they do, and a title search is both a request each and a best guess
    rather than the paper.

    Asked as a `filter` rather than as `/works/doi:<doi>`, because the
    single-entity form 404s on a DOI OpenAlex does not have -- which `_get`
    turns into a FetchError after four attempts, so the fallback below could
    never run. A filter answers an absent DOI with an empty result set.
    """
    hits = _get(OPENALEX, {"filter": f"doi:{openalex_doi(paper_id)}",
                           "select": "id", "per-page": 1,
                           "mailto": MAILTO}).get("results")
    if hits:
        return hits[0]["id"].rsplit("/", 1)[-1]
    if not title:
        return None
    hits = _get(OPENALEX, {"filter": f"title.search:{title}",
                           "select": "id", "per-page": 1,
                           "mailto": MAILTO}).get("results")
    return hits[0]["id"].rsplit("/", 1)[-1] if hits else None


def citing_works(short_id: str) -> list[dict]:
    """Every work citing `short_id`, paged. Enformer alone has ~1,300."""
    out, page = [], 1
    while True:
        d = _get(OPENALEX, {"filter": f"cites:{short_id}", "per-page": 200,
                            "page": page, "select": OA_SELECT, "mailto": MAILTO})
        out += d["results"]
        total = d["meta"]["count"]
        print(f"    page {page}: {len(out)}/{total}", file=sys.stderr)
        if len(out) >= total or not d["results"] or page >= 50:
            return out
        page += 1
        time.sleep(0.2)


def cached_citing(short_id: str) -> list[dict]:
    """
    `citing_works`, through a per-paper cache under literature/candidates/.

    The sweep is ~38 OpenAlex pages over four minutes and `_get` raises when a
    request exhausts its retries, which used to throw away everything fetched
    so far -- including the discovery half, which had already succeeded. Each
    paper's citing set is written as soon as it arrives, so a failed run is
    resumed by running the script again and only the paper in flight is lost.

    The cache is keyed on the OpenAlex id, not the date: the citing set of a
    2021 paper does not change meaningfully between two runs an hour apart, and
    a cycle that wants it fresh deletes literature/candidates/sweep_*.json.
    """
    f = CANDIDATES_DIR / f"sweep_{short_id}.json"
    if f.exists():
        cached = json.loads(f.read_text(encoding="utf-8"))
        print(f"    cached: {len(cached['citing'])} works", file=sys.stderr)
        return cached["citing"]
    works = citing_works(short_id)
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"root": short_id,
                             "fetched": datetime.now(timezone.utc).isoformat(),
                             "citing": works}, ensure_ascii=False),
                 encoding="utf-8")
    return works


def flatten_abstract(work: dict) -> str | None:
    """
    OpenAlex ships abstracts as a word -> positions index. Reconstructed here
    rather than in triage, so the candidates file holds plain text and nothing
    downstream needs to know the wire format.
    """
    inv = work.get("abstract_inverted_index")
    if not inv:
        return None
    return " ".join(w for _, w in sorted((i, w) for w, ixs in inv.items()
                                         for i in ixs)) or None


# ── Repository state ─────────────────────────────────────────────────────────

def read_repo() -> tuple[set[str], dict[str, str], dict[str, str], set[tuple[str, str]]]:
    """
    Known paper ids, each entity's `primary` paper, titles, and the
    (entity, paper) pairs already joined -- the only thing the sweep may skip.
    """
    def rows(path: str) -> list[dict]:
        with (ROOT / path).open(encoding="utf-8") as fh:
            return list(csv.DictReader(fh, delimiter="\t"))

    known = set()
    for p in yaml.safe_load((LIT_DIR / "papers.yaml").read_text(encoding="utf-8")):
        known.add(p["paper_id"].lower())
        if p.get("doi"):
            known.add(p["doi"].lower())

    titles = {r["paper_id"]: r["title"] for r in rows("db/papers.tsv")}
    primary, linked = {}, set()
    for ep in rows("db/entity_paper.tsv"):
        linked.add((ep["entity_id"], ep["paper_id"]))
        if ep["role"] == "primary":
            primary[ep["entity_id"]] = ep["paper_id"]
    return known, primary, titles, linked


# ── Main ─────────────────────────────────────────────────────────────────────

def _fetch_europepmc(q, min_year, cap, exclude):
    query = f"{' '.join(q['europepmc'].split())} {exclude}".strip()
    return search_europepmc(query, min_year, cap)


def _fetch_arxiv(q, min_year, cap, exclude):
    got = search_arxiv(q["arxiv"], min_year, cap)
    time.sleep(3)                           # arXiv asks for a few seconds
    return got


def run_discovery(cfg: dict, known: set[str], dry_run: bool,
                  failures: list) -> list[dict]:
    """
    The eight queries, cached one file per query.

    Per query rather than per run, because that is where it actually broke: a
    cold run died 5m44 in when arXiv refused the `accessibility` query four
    times, and a whole-run cache would have thrown away the two queries that
    had already succeeded. Now a failure costs the query in flight and nothing
    else, and running the script again picks up where it stopped.
    """
    min_year = cfg["min_year"]
    cap = cfg["max_results_per_query"]
    exclude = cfg.get("europepmc_exclude", "")
    stamp = date.today().isoformat()

    seen: set[str] = set()
    out: list[dict] = []
    for q in cfg["queries"]:
        print(f"\n[{q['id']}] expect_type={q['expect_type']}")
        if dry_run:
            if q.get("europepmc"):
                print("  europepmc:", " ".join(q["europepmc"].split())[:90])
            if q.get("arxiv"):
                print("  arxiv    :", q["arxiv"])
            continue

        hits = []
        for source, fetch in (("europepmc", _fetch_europepmc),
                              ("arxiv", _fetch_arxiv)):
            if not q.get(source):
                continue
            cache = CANDIDATES_DIR / f"discovery_{stamp}_{q['id']}_{source}.json"
            if cache.exists():
                got = json.loads(cache.read_text(encoding="utf-8"))
                print(f"  {source}: {len(got)} (cached)")
            else:
                try:
                    got = fetch(q, min_year, cap, exclude)
                except FetchError as exc:
                    # Recorded and carried in the output rather than aborting:
                    # arXiv refused twice in one afternoon, and each time it
                    # discarded minutes of Europe PMC results that had already
                    # arrived. The gap is printed, listed in the candidates
                    # file and reflected in the exit status, so it is still
                    # loud -- it just is not destructive.
                    print(f"  {source}: FAILED -- {exc}")
                    failures.append({"query_id": q["id"], "source": source,
                                     "error": str(exc)})
                    continue
                print(f"  {source}: {len(got)}")
                CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps(got, ensure_ascii=False),
                                 encoding="utf-8")
            hits += got

        for h in hits:
            key = (h["paper_id"] or h["title"].lower()[:80])
            if key in seen or key in known:
                continue
            seen.add(key)
            out.append(dict(h, query_id=q["id"], expect_type=q["expect_type"],
                            fate_axis=q["fate_axis"]))
    return out


def run_sweep(cfg: dict, primary: dict, titles: dict, linked: set,
              dry_run: bool, failures: list) -> list[dict]:
    wanted = cfg["citation_sweep"]["entities"]
    entities = sorted(primary) if wanted == "all" else [
        e for e in sorted(primary) if e in wanted]

    if dry_run:
        print(f"\n[citation_sweep] {len(entities)} entities with a primary paper")
        return []

    if not OPENALEX_KEY:
        print("[citation_sweep] no OPENALEX_API_KEY -- running on the keyless "
              "budget, $0.10 a day shared by every user of this network's IP. "
              "See config/sources.yaml.", file=sys.stderr)

    # Fetched per primary paper, not per entity: a model and the dataset it was
    # trained on routinely share one. The first full run fetched Enformer's
    # 1,298 citing works twice, once for `model:enformer` and once for
    # `dataset:enformer-data`, and Borzoi's 263 twice as well -- a fifth of the
    # whole sweep spent asking OpenAlex the same question.
    by_paper: dict[str, list[str]] = {}
    for entity in entities:
        by_paper.setdefault(primary[entity], []).append(entity)

    out = []
    for paper_id, sharers in by_paper.items():
        print(f"\n[citation_sweep] {paper_id} -> {', '.join(sharers)}")
        try:
            short_id = resolve_openalex(paper_id, titles.get(paper_id))
            works = cached_citing(short_id) if short_id else None
        except FetchError as exc:
            print(f"  FAILED -- {exc}")
            failures.append({"paper_id": paper_id, "source": "openalex",
                             "error": str(exc)})
            continue
        if not works:
            print("  unresolved in OpenAlex; skipped")
            continue
        for w in works:
            doi = (w.get("doi") or "").replace("https://doi.org/", "").lower() or None
            source = (w.get("primary_location") or {}).get("source") or {}
            for entity in sharers:
                if doi and (entity, doi) in linked:
                    continue            # already carries a role on this entity
                out.append({
                    "cites_entity": entity,
                    "cites_paper_id": paper_id,
                    # The id the sweep queried. Recorded so triage can match
                    # reference lists against catalogued primaries without
                    # resolving every DOI again.
                    "cites_openalex_id": short_id,
                    "openalex_id": (w.get("id") or "").rsplit("/", 1)[-1],
                    "doi": doi,
                    "title": w.get("title"),
                    "abstract": flatten_abstract(w),
                    "authors": [a["author"]["display_name"]
                                for a in (w.get("authorships") or [])
                                if (a.get("author") or {}).get("display_name")],
                    "year": w.get("publication_year"),
                    "oa_type": w.get("type"),
                    "venue": source.get("display_name"),
                    "referenced_works": w.get("referenced_works") or [],
                    "referenced_works_count": w.get("referenced_works_count"),
                })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="literature/search_queries.yaml")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the query plan, make no API calls")
    parser.add_argument("--discovery-only", action="store_true",
                        help="skip the citation sweep, which is the slow half")
    args = parser.parse_args()

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    known, primary, titles, linked = read_repo()
    print(f"known papers: {len(known)} ids; "
          f"{len(primary)} entities carry a primary paper")

    failures: list[dict] = []
    discovery = run_discovery(cfg, known, args.dry_run, failures)
    citing = ([] if args.discovery_only
              else run_sweep(cfg, primary, titles, linked, args.dry_run,
                             failures))
    if args.discovery_only:
        print("\n[citation_sweep] skipped (--discovery-only)")

    if args.dry_run:
        print("\n[dry-run] no API calls made, nothing written")
        return 0

    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CANDIDATES_DIR / f"{date.today().isoformat()}.json"
    out_path.write_text(json.dumps({
        "run_date": datetime.now(timezone.utc).isoformat(),
        "config": args.config,
        "counts": {"discovery": len(discovery), "citing": len(citing)},
        "failures": failures,
        "discovery": discovery,
        "citing": citing,
    }, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"\n{len(discovery)} new discovery candidates, "
          f"{len(citing)} citing works")
    print(f"wrote {out_path.relative_to(ROOT)}")
    if failures:
        print(f"\n{len(failures)} source fetch(es) failed and are recorded in "
              f"the file:")
        for f in failures:
            print(f"  {f.get('query_id') or f.get('paper_id')} / {f['source']}")
        print("Re-run to fill the gaps; everything already fetched is cached.")
        print("next: python literature/02_triage.py (on an incomplete set)")
        return 1
    print("next: python literature/02_triage.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
