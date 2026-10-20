#!/usr/bin/env python
"""
literature/02_triage.py
-----------------------
Score the candidates from 01_search.py and write
literature/reviews/review_YYYY-MM-DD.md for a human to work through.

Triage ranks. It does not include, and it does not tier:

  * A role (`benchmark` / `critique`) is *proposed*; the curator accepts or
    rejects it in the review file, and 03_record.py reads those decisions.
  * `evidence_tier` is never touched. It is derived in scripts/05_validate.py
    from author overlap between a model's `primary` paper and the papers whose
    role is `benchmark` or `critique`. Author overlap is therefore displayed
    here and deliberately absent from the scoring -- see triage_rules.py and
    docs/triage_design.md §2.4.

Three lists, because they are three different questions:

  discovery  "is this resource in scope?"  -- scored per expect_type, §1.4
  list A     "does this paper evaluate <entity>, which it names?"  -- §2.3
  list B     "does this paper evaluate a class of models, naming none?"  -- §2.3

Nothing is dropped for scoring low. A threshold decides which *section* a
candidate lands in, and the whole set is written down: a rejection that is not
recorded comes back as a candidate next cycle, which is why
literature/reviews/ is committed while literature/candidates/ is not.

Run from project root:
    python literature/02_triage.py [--candidates PATH] [--min-score 3.0]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage_rules as rules                            # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_DIR = ROOT / "literature" / "candidates"
REVIEWS_DIR = ROOT / "literature" / "reviews"


def latest_candidates() -> Path:
    files = sorted(CANDIDATES_DIR.glob("*.json"))
    files = [f for f in files if not f.name.startswith("triage_eval_")]
    if not files:
        raise SystemExit("no candidates file; run literature/01_search.py first")
    return files[-1]


def author_overlap(rec: dict, primary_authors: list[str]) -> str:
    """
    Shown, never scored. Uses 05_validate.py's own `lastname|first-initial`
    normalization so the number a curator reads is the number QC will derive
    the tier from.
    """
    if not rec.get("authors") or not primary_authors:
        return "unknown"
    theirs = {norm_author(a) for a in rec["authors"]} - {""}
    ours = {norm_author(a) for a in primary_authors} - {""}
    shared = theirs & ours
    return f"{len(shared)}/{len(ours)} of the primary authors"


def norm_author(name: str) -> str:
    """Kept in step with scripts/05_validate.py:norm_author."""
    import re
    import unicodedata
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c)).lower()
    parts = [p for p in re.split(r"[\s.\-,]+", n) if p]
    return f"{parts[-1]}|{parts[0][0]}" if parts else ""


def fmt_parts(parts: dict) -> str:
    return " ".join(f"{k}={v:+.2f}" for k, v in parts.items() if v)


def block(lines: list[str], title: str, meta: list[str], abstract: str | None,
          decision: str) -> None:
    lines.append(f"#### {title}")
    lines.append("")
    for m in meta:
        lines.append(f"- {m}")
    if abstract:
        lines += ["", f"> {abstract[:400].strip()}…" if len(abstract) > 400
                  else f"> {abstract.strip()}"]
    lines += ["", decision,
              "**Notes:** _(why, and anything 03_record.py needs: supplementary"
              " files, which models are actually in the results table)_",
              "", "---", ""]


def render_discovery(cands: list[dict], min_score: float) -> list[str]:
    scored = []
    for c in cands:
        score, parts = rules.score_discovery(c)
        scored.append((score, parts, c))
    scored.sort(key=lambda t: -t[0])

    lines = [f"## Discovery candidates ({len(scored)})", "",
             "New resources from the eight queries in `search_queries.yaml`. "
             "Scored for scope, with the table chosen by the query's "
             "`expect_type` — a database and a sequence model cannot share one "
             "(design §1.4).", ""]
    for label, keep in (("Above threshold", True), ("Below threshold", False)):
        group = [t for t in scored if (t[0] >= min_score) == keep]
        if not group:
            continue
        lines += [f"### {label} — score "
                  f"{'≥' if keep else '<'} {min_score} ({len(group)})", ""]
        if not keep:
            lines += ["Listed, not discarded. At every useful threshold a "
                      "filter drops more known-good papers than noise "
                      "(design §1.5), and an unrecorded rejection returns next "
                      "cycle.", ""]
        for score, parts, c in group:
            ident = c.get("paper_id") or c.get("europepmc_id") or "no id"
            block(lines, f"[{score:+.2f}] {c['title']}", [
                f"**id:** `{ident}`  **source:** {c['source']}  "
                f"**year:** {c.get('year')}",
                f"**query:** `{c['query_id']}`  **expect_type:** "
                f"{c['expect_type']}  **fate_axis:** {c.get('fate_axis')}",
                f"**score:** {fmt_parts(parts) or 'nothing matched'}",
            ], c.get("abstract"),
                "**Decision:** `[ ] accepted` / `[ ] rejected`")
    return lines


def render_list_a(citing: list[dict], primaries, model_forms, all_forms,
                  primary_authors, min_score: float) -> list[str]:
    by_entity: dict[str, list] = {}
    for rec in citing:
        got = rules.score_named(rec, rec["cites_entity"], primaries,
                                model_forms, all_forms)
        if not got:
            continue
        score, role, parts = got
        if score < min_score:
            continue
        by_entity.setdefault(rec["cites_entity"], []).append(
            (score, role, parts, rec))

    total = sum(len(v) for v in by_entity.values())
    lines = [f"## List A — names the entity ({total})", "",
             "Papers citing a catalogued `primary` paper *and* naming the "
             "entity. Read these first: tight, per entity, high confidence. "
             "The two lexicon sub-scores are printed next to every proposed "
             "role, because the split is sometimes a coin-flip (design §2.6.4).",
             ""]
    for entity in sorted(by_entity):
        group = sorted(by_entity[entity], key=lambda t: -t[0])
        lines += [f"### {entity} ({len(group)})", ""]
        for score, role, parts, rec in group:
            block(lines, f"[{score:+.2f}] {rec['title']}", [
                f"**doi:** `{rec.get('doi') or '—'}`  **year:** "
                f"{rec.get('year')}  **venue:** {rec.get('venue') or '—'}",
                f"**proposed role:** `{role}`  "
                f"(benchmark {parts.get('bench_lex', 0):.2f} vs critique "
                f"{parts.get('crit_lex', 0):.2f})",
                f"**author overlap:** "
                f"{author_overlap(rec, primary_authors.get(entity, []))} "
                f"— shown only; the score ignores it (§2.4)",
                f"**score:** {fmt_parts(parts)}",
            ], rec.get("abstract"),
                f"**Decision:** `[ ] accepted as {role}` / "
                f"`[ ] accepted as other role` / `[ ] rejected`")
    return lines


def render_list_b(citing: list[dict], primaries, model_forms,
                  min_score: float) -> list[str]:
    seen: dict[str, tuple] = {}
    for rec in citing:
        key = rec.get("doi") or rec["openalex_id"]
        if key in seen:
            continue
        got = rules.score_class(rec, primaries, model_forms)
        if not got:
            continue
        score, role, cited, has_abstract = got
        if score < min_score:
            continue
        seen[key] = (score, role, cited, has_abstract, rec)

    rows = sorted(seen.values(), key=lambda t: -t[0])
    with_abs = [r for r in rows if r[3]]
    title_only = [r for r in rows if not r[3]]

    lines = [f"## List B — names a class, no catalogued model ({len(rows)})", "",
             "Deduplicated and global, because one such paper is evidence for "
             "several entities at once. This list exists because the gate that "
             "ranks named cases well discards **both** catalogued critiques of "
             "Enformer: neither names it (design §2.3). Each entry lists the "
             "catalogued primary papers it cites, so a curator can see which "
             "entities it might attach to.", ""]
    for label, group, note in (
        ("With an abstract", with_abs, None),
        ("Title only", title_only,
         "No abstract in OpenAlex, so only the title was scored. One of "
         "Enformer's two catalogued critiques lands here — the gap is not "
         "backfillable from any source in `config/sources.yaml` (§2.6.2)."),
    ):
        if not group:
            continue
        lines += [f"### {label} ({len(group)})", ""]
        if note:
            lines += [note, ""]
        for score, role, cited, _, rec in group:
            block(lines, f"[{score:+.2f}] {rec['title']}", [
                f"**doi:** `{rec.get('doi') or '—'}`  **year:** "
                f"{rec.get('year')}  **venue:** {rec.get('venue') or '—'}",
                f"**proposed role:** `{role}`",
                f"**cites catalogued primaries:** "
                f"{', '.join(f'`{e}`' for e in cited) if cited else 'none matched'}",
                f"**reached via:** `{rec['cites_entity']}`",
            ], rec.get("abstract"),
                f"**Decision:** `[ ] accepted as {role} for: "
                f"<entity_id>` / `[ ] rejected`")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", default=None,
                        help="candidates JSON (default: the most recent)")
    parser.add_argument("--min-score", type=float, default=3.0,
                        help="section boundary, not a filter (default: 3.0)")
    args = parser.parse_args()

    path = Path(args.candidates) if args.candidates else latest_candidates()
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"reading {path.name}: {data['counts']}")

    titles, all_forms, model_forms, primary, linked, _ = rules.read_repo()

    # score_named / score_class match reference lists against the OpenAlex ids
    # of catalogued primary papers. 01_search.py resolved each one when it ran
    # the sweep and records it on every citing row, so nothing is resolved
    # twice. OpenAlex merges a preprint with its journal version into one work
    # (design §2.1), so one id per entity is right.
    primaries_oa = {rec["cites_entity"]: rec["cites_openalex_id"]
                    for rec in data["citing"] if rec.get("cites_openalex_id")}

    primary_authors = _primary_authors(primary)

    lines = [f"# Candidate review — {date.today().isoformat()}", "",
             f"From `{path.relative_to(ROOT).as_posix()}` "
             f"({data['counts']['discovery']} discovery, "
             f"{data['counts']['citing']} citing). Section boundary at "
             f"`--min-score {args.min_score}`.", "",
             "Tick one decision per candidate and fill in the notes, then run "
             "`python literature/03_record.py`. Accepting a citing paper "
             "proposes an `entity_paper` role; the `evidence_tier` that follows "
             "is derived by `scripts/05_validate.py`, never set here.", "",
             "---", ""]

    lines += render_discovery(data["discovery"], args.min_score)
    lines += render_list_a(data["citing"], primaries_oa, model_forms, all_forms,
                           primary_authors, args.min_score)
    lines += render_list_b(data["citing"], primaries_oa, model_forms,
                           args.min_score)

    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    out = REVIEWS_DIR / f"review_{date.today().isoformat()}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    print("next: work through it, then python literature/03_record.py")
    return 0


def _primary_authors(primary: dict) -> dict:
    import csv
    rows = {}
    with (ROOT / "db" / "papers.tsv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            rows[r["paper_id"]] = json.loads(r["authors"] or "[]")
    return {e: rows.get(p, []) for e, p in primary.items()}


if __name__ == "__main__":
    sys.exit(main())
