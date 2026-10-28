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

import contextlib
import io
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage_rules as rules                      # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "literature" / "candidates"
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
UA = f"cfcr-triage-eval (mailto:{MAILTO})"

# Same source as 01_search.OPENALEX_KEY, read again rather than imported: a
# module whose name starts with a digit cannot be imported by name, which is
# why _contact_email is a second copy here too. Absent is supported -- this
# harness fits in the keyless budget on a warm cache.
OPENALEX_KEY = os.environ.get("OPENALEX_API_KEY") or None
OA = "https://api.openalex.org/works"
SELECT = ("id,doi,title,publication_year,type,primary_location,referenced_works,"
          "referenced_works_count,abstract_inverted_index")

# Scoring thresholds. Both lists are ranked proposals, so these only decide how
# much a curator is asked to read -- nothing is discarded by QC on this basis.
#
# MIN_A tracks 02_triage.LIST_A_MIN and has to: list A is gated on the citing
# paper's reference list, which every swept work satisfies, so an eval run at a
# threshold the pipeline does not use would measure neither.
MIN_A = 5.0
MIN_B = 3.0


# ── OpenAlex ─────────────────────────────────────────────────────────────────

def _get(url: str, params: dict) -> dict:
    params = dict(params, mailto=MAILTO)
    for attempt in range(4):
        try:
            headers = {"User-Agent": UA}
            if OPENALEX_KEY:
                headers["Authorization"] = f"Bearer {OPENALEX_KEY}"
            r = requests.get(url, params=params, headers=headers, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 -- retry anything the API throws
            print(f"    retry {attempt + 1}: {exc}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"OpenAlex did not answer: {url} {params}")


def resolve(paper_id: str, title: str | None) -> str | None:
    """
    paper_id -> OpenAlex short id, by DOI; title search only as the fallback.

    Same fix as 01_search.resolve_openalex and for the same reason: arXiv mints
    `10.48550/arXiv.<id>`, so the arXiv branch was spending a fuzzy title
    search per paper on a DOI that resolves exactly. Two copies of a wrong
    premise meant fixing it in one place would have left the other.
    """
    doi = ("10.48550/arXiv." + paper_id.split(":", 1)[1]
           if paper_id.startswith("arxiv:") else paper_id)
    res = _get(OA, {"filter": f"doi:{doi}", "select": "id",
                    "per-page": 1}).get("results")
    if res:
        return res[0]["id"].rsplit("/", 1)[-1]
    if not title:
        return None
    res = _get(OA, {"filter": f"title.search:{title}", "select": "id",
                    "per-page": 1}).get("results")
    return res[0]["id"].rsplit("/", 1)[-1] if res else None


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


# ── shared scoring ───────────────────────────────────────────────
# The tables and scorers live in triage_rules.py, which 02_triage.py also
# imports. They were duplicated here first; two copies make this script's whole
# promise -- that it says what a scoring change cost -- false the moment one
# copy moves.

def as_record(work: dict) -> dict:
    """OpenAlex work -> the normalized shape triage_rules scores."""
    inv = work.get("abstract_inverted_index")
    abstract = ("" if not inv else
                " ".join(w for _, w in sorted((i, w) for w, ixs in inv.items()
                                              for i in ixs)))
    return {"title": work.get("title") or "", "abstract": abstract,
            "referenced_works": work.get("referenced_works") or [],
            "oa_type": work.get("type") or ""}


def score_named(work, entity, primaries, model_forms, all_forms):
    return rules.score_named(as_record(work), entity, primaries, model_forms,
                             all_forms)


def score_class(work, primaries, model_forms):
    return rules.score_class(as_record(work), primaries, model_forms)


def read_repo():
    """Drops `linked`, which this script does not use."""
    titles, all_forms, model_forms, primary, _linked, truth = rules.read_repo()
    return titles, all_forms, model_forms, primary, truth


def report():
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

    print(f"\nlist A (cites the primary), min_score {MIN_A}:")
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


def main() -> int:
    """
    Run the measurement, print it, and write it to reports/triage_eval.md.

    The report is committed, like reports/seed_flags.md and
    reports/vocab_candidates.md, because every measured number in
    docs/triage_design.md \u00a72.5 comes from here and this script needs network --
    OpenAlex, specifically. A reviewer without it (a sandbox, CI) could not
    check any of those numbers, and "unverified" is indistinguishable from
    "wrong" when there is nothing committed to compare against. Now there is a
    dated artifact, and `git diff` says whether a scoring change moved it.
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        report()
    body = buf.getvalue()
    print(body, end="")

    out = ROOT / "reports" / "triage_eval.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "# Triage citation-sweep measurement\n\n"
        f"Generated by `python literature/triage_eval.py` on "
        f"{date.today().isoformat()}.\n\n"
        "Needs network (OpenAlex), so it cannot be regenerated in a sandbox "
        "without one. The numbers quoted in `docs/triage_design.md` \u00a72.5 are "
        "these numbers; re-run after any change to the weights in "
        "`literature/triage_rules.py` and commit the diff \u2014 it is the only "
        "thing that says what the change cost.\n\n"
        "```\n" + body.strip("\n") + "\n```\n",
        encoding="utf-8", newline="")
    print(f"\nwrote {out.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
