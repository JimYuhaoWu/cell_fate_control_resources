"""
literature/triage_eval.py
-------------------------
Measure the citation-sweep half of 02_triage.py against the `benchmark` and
`critique` rows already in db/entity_paper.tsv.

Not a pipeline step, so it carries no step number. It exists because the claim
the NAR novelty argument rests on -- that CFCR can find the papers which
evaluate a model, and that no keyword search can -- is a quantitative claim, and
db/entity_paper.tsv is the only ground truth there is. Whenever the scoring in
docs/triage_design.md changes, this says what the change cost.

Run from project root (needs the [literature] extra and network):
    python literature/triage_eval.py

Writes nothing to the repo except cached API dumps under literature/candidates/,
which .gitignore excludes.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "literature" / "candidates"
MAILTO = "yuhaow9412@gmail.com"
UA = f"cfcr-triage-eval (mailto:{MAILTO})"
OA = "https://api.openalex.org/works"
SELECT = ("id,doi,title,publication_year,type,primary_location,referenced_works,"
          "referenced_works_count,abstract_inverted_index")

# Scoring thresholds. Both lists are ranked proposals, so these only decide how
# much a curator is asked to read -- nothing is discarded by QC on this basis.
MIN_A = 3.0
MIN_B = 3.0


# ── vocabularies ─────────────────────────────────────────────────────────────
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


# ── OpenAlex ─────────────────────────────────────────────────────────────────

def _get(url: str, params: dict) -> dict:
    params = dict(params, mailto=MAILTO)
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 -- retry anything the API throws
            print(f"    retry {attempt + 1}: {exc}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"OpenAlex did not answer: {url} {params}")


def resolve(paper_id: str, title: str | None) -> str | None:
    """paper_id -> OpenAlex short id. arXiv ids have no DOI, so fall back to title."""
    if paper_id.startswith("arxiv:"):
        if not title:
            return None
        res = _get(OA, {"filter": f"title.search:{title}", "select": "id"}).get("results")
        if not res:
            return None
        return res[0]["id"].rsplit("/", 1)[-1]
    work = _get(f"{OA}/doi:{paper_id}", {"select": "id"})
    wid = work.get("id")
    return wid.rsplit("/", 1)[-1] if wid else None


def citing(short_id: str) -> list[dict]:
    """Every work citing `short_id`. Paged, because a popular model has thousands."""
    out, page = [], 1
    while True:
        d = _get(OA, {"filter": f"cites:{short_id}", "per-page": 200,
                      "page": page, "select": SELECT})
        out += d["results"]
        total = d["meta"]["count"]
        print(f"    page {page}: {len(out)}/{total}", file=sys.stderr)
        if len(out) >= total or not d["results"] or page >= 50:
            return out
        page += 1
        time.sleep(0.2)


def cached_citing(label: str, short_id: str) -> list[dict]:
    f = CACHE / f"triage_eval_{label}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))["citing"]
    print(f"  fetching citations of {short_id}", file=sys.stderr)
    works = citing(short_id)
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"root": short_id, "citing": works}), encoding="utf-8")
    return works


# ── scoring ──────────────────────────────────────────────────────────────────

def abstract_of(work: dict) -> str:
    inv = work.get("abstract_inverted_index")
    if not inv:
        return ""
    return " ".join(w for _, w in sorted((i, w) for w, idx in inv.items() for i in idx))


def hits(terms: list[str], text: str) -> list[str]:
    return [t for t in terms if re.search(r"(?<![a-z])" + re.escape(t), text)]


def names(forms: set[str], text: str) -> bool:
    return any(re.search(r"(?<![a-z0-9])" + re.escape(f.lower()) + r"(?![a-z0-9])", text)
               for f in forms)


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


def _context(work: dict, primaries: dict, entity: str | None):
    title = (work.get("title") or "").lower()
    abstract = abstract_of(work).lower()
    refs = {r.rsplit("/", 1)[-1] for r in (work.get("referenced_works") or [])}
    own = primaries.get(entity) if entity else None
    cited = sorted(e for e, oa in primaries.items() if oa and oa in refs)
    n_shared = len({primaries[e] for e in cited if primaries[e] != own})
    return title, abstract, f"{title} || {abstract}", cited, n_shared


def score_named(work, entity, primaries, model_forms, all_forms):
    """List A: the citing paper names this entity."""
    title, abstract, both, _, n_shared = _context(work, primaries, entity)
    parts = {}
    if names(all_forms.get(entity, set()), title):
        parts["name_title"] = 3.0
    elif names(all_forms.get(entity, set()), abstract):
        parts["name_abstract"] = 1.5
    else:
        return None
    bench, crit = lexicon(title, abstract)
    parts["bench_lex"], parts["crit_lex"] = bench, crit
    others = sum(1 for e, f in model_forms.items() if e != entity and names(f, both))
    parts["multi_model"] = {0: 0.0, 1: 0.5, 2: 1.5}.get(others, 3.0)
    parts["ref_overlap"] = min(0.75 * n_shared, 3.0)
    if hits(DEMOTE_TITLE, title):
        parts["demote_title"] = -3.0
    if (work.get("type") or "") == "review":
        parts["demote_type"] = -3.0
    return round(sum(parts.values()), 2), propose_role(bench, crit), parts


def score_class(work, primaries, model_forms):
    """List B: names no catalogued model, but talks like an evaluation of a class."""
    title, abstract, both, cited, n_shared = _context(work, primaries, None)
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
    if (work.get("type") or "") == "review":
        parts["demote_type"] = -3.0
    return round(sum(parts.values()), 2), propose_role(bench, crit), cited, bool(abstract)


# ── repository inputs ────────────────────────────────────────────────────────

def read_repo():
    rows = lambda p: list(csv.DictReader(open(ROOT / p, encoding="utf-8"), delimiter="\t"))
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
    primary, truth = {}, []
    for ep in rows("db/entity_paper.tsv"):
        if ep["role"] == "primary":
            primary[ep["entity_id"]] = ep["paper_id"]
        elif ep["role"] in ("benchmark", "critique"):
            truth.append((ep["entity_id"], ep["paper_id"], ep["role"]))
    return titles, all_forms, model_forms, primary, truth


def main():
    titles, all_forms, model_forms, primary_paper, truth = read_repo()
    print(f"ground truth: {len(truth)} benchmark/critique rows in db/entity_paper.tsv")

    oa_cache = CACHE / "triage_eval_openalex_ids.json"
    ids = json.loads(oa_cache.read_text(encoding="utf-8")) if oa_cache.exists() else {}
    wanted = set(primary_paper.values()) | {pid for _, pid, _ in truth}
    for pid in sorted(wanted):
        if pid not in ids:
            ids[pid] = resolve(pid, titles.get(pid))
            time.sleep(0.15)
    CACHE.mkdir(parents=True, exist_ok=True)
    oa_cache.write_text(json.dumps(ids, indent=1), encoding="utf-8")

    primaries = {e: ids.get(p) for e, p in primary_paper.items()}
    swept = sorted({e for e, _, _ in truth})

    list_a, list_b, present = {}, {}, {}
    for entity in swept:
        oid = primaries.get(entity)
        if not oid:
            continue
        works = cached_citing(entity.replace(":", "_"), oid)
        present[entity] = {w["id"].rsplit("/", 1)[-1] for w in works}
        rows = []
        for w in works:
            wid = w["id"].rsplit("/", 1)[-1]
            a = score_named(w, entity, primaries, model_forms, all_forms)
            if a and a[0] >= MIN_A:
                rows.append((a[0], a[1], wid, w.get("title") or ""))
            b = score_class(w, primaries, model_forms)
            if b and b[0] >= MIN_B and wid not in list_b:
                list_b[wid] = (b[0], b[1], wid, w.get("title") or "", b[2], b[3])
        rows.sort(key=lambda r: -r[0])
        list_a[entity] = (len(works), rows)

    # List B is split on abstract availability, not scored on it. OpenAlex -- and
    # Europe PMC -- hold no abstract for 10.1038/s41588-023-01517-5, a catalogued
    # critique, so an additive score buries it under papers that have one.
    b_abs = sorted((r for r in list_b.values() if r[5]), key=lambda r: -r[0])
    b_noabs = sorted((r for r in list_b.values() if not r[5]), key=lambda r: -r[0])

    print(f"\nlist A (names the model), min_score {MIN_A}:")
    for entity, (total, rows) in list_a.items():
        print(f"  {entity:32s} {total:5d} citing -> {len(rows):4d} proposed")
    print(f"list B (class-level), min_score {MIN_B}: "
          f"{len(b_abs)} with abstract, {len(b_noabs)} title-only")

    print("\nwhere each ground-truth row lands:")
    found = 0
    for entity, pid, role in sorted(truth):
        wid = ids.get(pid)
        if entity not in present:
            print(f"  {entity:32s} {pid:28s} {role:9s} NOT SWEPT (no primary resolved)")
            continue
        if wid not in present[entity]:
            print(f"  {entity:32s} {pid:28s} {role:9s} NO CITATION EDGE in OpenAlex")
            continue
        rows = list_a[entity][1]
        pos = next((i for i, r in enumerate(rows, 1) if r[2] == wid), None)
        if pos:
            found += 1
            print(f"  {entity:32s} {pid:28s} {role:9s} "
                  f"A {pos}/{len(rows)}  score {rows[pos-1][0]:5.2f}  "
                  f"proposed {rows[pos-1][1]}")
            continue
        for name, pool in (("B-abs", b_abs), ("B-title-only", b_noabs)):
            pos = next((i for i, r in enumerate(pool, 1) if r[2] == wid), None)
            if pos:
                found += 1
                print(f"  {entity:32s} {pid:28s} {role:9s} "
                      f"{name} {pos}/{len(pool)}  score {pool[pos-1][0]:5.2f}  "
                      f"proposed {pool[pos-1][1]}")
                break
        else:
            print(f"  {entity:32s} {pid:28s} {role:9s} DROPPED below threshold")

    print(f"\nrecovered {found}/{len(truth)} ground-truth rows into a ranked proposal")


if __name__ == "__main__":
    main()
