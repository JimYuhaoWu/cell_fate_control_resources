"""
literature/query_coverage.py
----------------------------
What the committed clauses in `literature/search_queries.yaml` reach, measured
against the records they are supposed to have found.

Not a pipeline step, so it carries no step number, and unlike
`literature/triage_eval.py` it needs no network: it reads the cached discovery
dumps under `literature/candidates/` and `records/`. That is the point. A
reviewer without an API key can recompute every number here, which is what
makes the clause file checkable rather than merely published.

Two numbers, and the second is the one that matters:

  reach         the published records whose primary paper is in the hit set.
                How much of the catalogue the clauses can find at all.
  discrimination the withdrawn records in the same hit set. A query reaches a
                literature, not a boundary; `docs/scope_criteria.md` is what
                separates the halves, and this says how much work that leaves.

Run from project root:
    python literature/query_coverage.py [--date YYYY-MM-DD]

Writes reports/query_coverage.md, which is committed for the same reason
reports/triage_eval.md is: a measurement nobody can reproduce reads the same as
a wrong one.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date as date_cls
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "literature" / "candidates"

# The keys a cached hit can carry an identifier under. `paper_id` is the one
# records/ uses -- arXiv hits already carry `arxiv:NNNN.NNNNN` there -- and the
# rest are kept because a Europe PMC hit can hold a PMCID and no DOI
# (01_search.py `_epmc_row`), and a record backfilled from one would match on
# nothing else.
ID_KEYS = ("paper_id", "doi", "europepmc_id")


def hit_ids(hit: dict) -> set[str]:
    return {str(hit[k]).lower() for k in ID_KEYS if hit.get(k)}


def primaries() -> tuple[dict[str, str], dict[str, str]]:
    """(published, withdrawn) entity_id -> primary paper id, lower-cased.

    `unreviewed` is neither: it means nobody has looked yet, so counting it
    against the clauses would score them on a decision not taken.
    """
    published: dict[str, str] = {}
    withdrawn: dict[str, str] = {}
    for f in sorted((ROOT / "records").glob("*.yaml")):
        for rec in yaml.safe_load(f.read_text(encoding="utf-8")) or []:
            state = rec.get("review_state")
            if state == "withdrawn":
                into = withdrawn
            elif state in (None, "reviewed"):
                into = published
            else:
                continue
            for p in rec.get("papers") or []:
                if p.get("role") == "primary":
                    into[rec["entity_id"]] = str(p.get("paper_id") or "").lower()
    return published, withdrawn


def load_run(run_date: str) -> tuple[dict[str, set[str]], dict[str, int]]:
    """clause id -> (the identifiers its cached hits carry, how many papers).

    Both, because they are not the same number and conflating them is a way to
    overstate a clause. A hit can carry a DOI, a `paper_id` and a PMCID at
    once, so the identifier set runs about twice the length of the hit list;
    matching needs every identifier, and reporting needs the paper count.
    """
    per_clause: dict[str, set[str]] = defaultdict(set)
    papers: dict[str, int] = defaultdict(int)
    prefix = f"discovery_{run_date}_"
    for f in sorted(CACHE.glob(f"{prefix}*.json")):
        # discovery_<date>_<clause id>_<source>.json, and a clause id holds
        # underscores of its own, so split from the right.
        clause = f.stem[len(prefix):].rsplit("_", 1)[0]
        hits = json.loads(f.read_text(encoding="utf-8"))
        for h in hits:
            per_clause[clause] |= hit_ids(h)
        papers[clause] += len(hits)
    return dict(per_clause), dict(papers)


def latest_run() -> str:
    dates = sorted({f.stem.split("_")[1] for f in CACHE.glob("discovery_*.json")})
    if not dates:
        sys.exit("no cached discovery dumps under literature/candidates/")
    return dates[-1]


def report(run_date: str) -> str:
    per_clause, papers = load_run(run_date)
    if not per_clause:
        sys.exit(f"no cached discovery dumps for {run_date}")
    union: set[str] = set().union(*per_clause.values())
    published, withdrawn = primaries()
    pub = {e: p for e, p in published.items() if p}

    reached = {e for e, p in pub.items() if p in union}
    missed = sorted(set(pub) - reached)
    also = {e for e, p in withdrawn.items() if p and p in union}

    out = [f"cached discovery run: {run_date}",
           f"clauses: {len(per_clause)}",
           f"papers fetched: {sum(papers.values())}",
           f"distinct identifiers they carry: {len(union)}", ""]

    out.append("reach, per clause:")
    for clause in sorted(per_clause):
        n = sum(1 for p in pub.values() if p in per_clause[clause])
        out.append(f"  {clause:24s} {papers[clause]:5d} papers -> "
                   f"{n:4d} published primaries")

    pct = 100 * len(reached) / len(pub) if pub else 0.0
    out += ["",
            f"published records carrying a primary paper: {len(pub)}",
            f"  reached by at least one clause: {len(reached)} ({pct:.1f}%)",
            f"  reached by none:                {len(missed)}", ""]

    out.append("unreached, by type:")
    by_type = Counter(e.split(":")[0] for e in missed)
    totals = Counter(e.split(":")[0] for e in pub)
    for t, n in by_type.most_common():
        out.append(f"  {t:10s} {n:3d} of {totals[t]:3d} published")

    out += ["", "unreached, named:"]
    out += [f"  {e:52s} {pub[e]}" for e in missed]

    wpct = 100 * len(also) / len(withdrawn) if withdrawn else 0.0
    out += ["",
            "discrimination:",
            f"  withdrawn records whose primary is in the same hit set: "
            f"{len(also)} of {len(withdrawn)} ({wpct:.1f}%)",
            "",
            f"  So the clauses return {len(reached)} in-scope and {len(also)} "
            f"out-of-scope primaries together. The clause file is the reach;",
            "  docs/scope_criteria.md is the admission, and these two numbers "
            "are the size of what it is still asked to do."]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="cached run to read (default: the newest)")
    args = ap.parse_args()

    run_date = args.date or latest_run()
    body = report(run_date)
    print(body)

    out = ROOT / "reports" / "query_coverage.md"
    out.write_text(
        "# Query coverage\n\n"
        f"Generated by `python literature/query_coverage.py` on "
        f"{date_cls.today().isoformat()}, from the cached discovery run of "
        f"{run_date}.\n\n"
        "Needs no network: every number here is recomputable from "
        "`literature/candidates/` and `records/` as committed. The clauses are "
        "in `literature/search_queries.yaml`, and ROADMAP M4 makes these two "
        "numbers its exit criterion.\n\n"
        "```\n" + body + "\n```\n",
        encoding="utf-8", newline="")
    print(f"\nwrote {out.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
