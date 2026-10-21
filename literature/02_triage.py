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
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage_rules as rules                            # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_DIR = ROOT / "literature" / "candidates"
REVIEWS_DIR = ROOT / "literature" / "reviews"


def _rel(path: Path) -> str:
    """Repo-relative for display, falling back to the full path outside it."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _has_decisions(path: Path) -> bool:
    """
    Whether a review file has been worked on. Re-running triage on an untouched
    file is harmless and routine -- a second 01_search run the same day, or a
    different --min-score -- but the write is to a date-stamped name, so without
    this check the second run silently replaces a curator's ticks with blank
    boxes. A rejection that is not recorded comes back next cycle, which is the
    whole reason literature/reviews/ is committed.
    """
    if not path.exists():
        return False
    return "[x]" in path.read_text(encoding="utf-8").lower()


def latest_candidates() -> Path:
    """
    The most recent run file, selected by name shape rather than by excluding
    the prefixes known today.

    literature/candidates/ holds three other kinds of file -- 01_search.py's
    per-day `discovery_*` and per-paper `sweep_*` caches, and triage_eval.py's
    `triage_eval_*` dumps -- and the old exclusion list took the lexically last
    *.json, so `sweep_W3203588026.json` sorting after `2026-10-21.json` would
    silently become "the most recent candidates". A run file is a date and
    nothing else.
    """
    files = sorted(f for f in CANDIDATES_DIR.glob("*.json")
                   if re.fullmatch(r"\d{4}-\d{2}-\d{2}", f.stem))
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
                  primary_authors, state, min_score: float) -> list[str]:
    """
    List A, split by whether a decision can change a derived tier.

    Both halves are written out in full. The split is about whose attention a
    proposal needs, not about what gets kept: a `benchmark` row on a model that
    is already `externally-benchmarked` is still related work worth recording,
    it just cannot move the one number the catalogue is judged on, so asking a
    human about it spends the scarcest thing in the project on a foregone
    conclusion.
    """
    buckets: dict[str, dict[str, list]] = {"needs-human": {}, "no-effect": {}}
    for rec in citing:
        got = rules.score_named(rec, rec["cites_entity"], primaries,
                                model_forms, all_forms)
        if not got:
            continue
        score, role, parts = got
        if score < min_score:
            continue
        entity = rec["cites_entity"]
        if entity in state:
            verdict, why = rules.tier_effect(state[entity], rec.get("authors"))
        else:
            verdict, why = "needs-human", "entity carries no primary paper"
        buckets[verdict].setdefault(entity, []).append(
            (score, role, parts, rec, why))

    n_human = sum(len(v) for v in buckets["needs-human"].values())
    n_auto = sum(len(v) for v in buckets["no-effect"].values())

    lines = [f"## List A — names the entity ({n_human + n_auto})", "",
             "Papers citing a catalogued `primary` paper *and* naming the "
             "entity. The two lexicon sub-scores are printed next to every "
             "proposed role, because the split is sometimes a coin-flip "
             "(design §2.6.4).", "",
             f"**{n_human} need a decision. {n_auto} do not** — "
             "`evidence_tier` saturates, so once an entity has one independent "
             "evaluation no further row can move it. Author overlap decides "
             "which half a proposal lands in; it is still not an input to any "
             "score (§2.4). A proposal with no author list always needs a "
             "human, because independence cannot be computed from nothing.", ""]

    lines += [f"### Needs a decision ({n_human})", ""]
    for entity in sorted(buckets["needs-human"]):
        group = sorted(buckets["needs-human"][entity], key=lambda t: -t[0])
        tier = state.get(entity, {}).get("tier")
        lines += [f"#### {entity} — tier now: "
                  f"{tier or 'none yet, so the first evaluation sets it'} "
                  f"({len(group)})", ""]
        for score, role, parts, rec, why in group:
            _block_a(lines, score, role, parts, rec, entity, primary_authors,
                     why, auto=False)

    lines += [f"### Recorded without a decision ({n_auto})", "",
              "Nothing here is dropped — each is recorded as the role shown, "
              "and `03_record.py` will attach it. They appear so the catalogue "
              "stays complete and so a curator can veto one, not so one has to "
              "be approved.", ""]
    for entity in sorted(buckets["no-effect"]):
        group = sorted(buckets["no-effect"][entity], key=lambda t: -t[0])
        tier = state.get(entity, {}).get("tier")
        lines += [f"#### {entity} — tier now: {tier} ({len(group)})", ""]
        for score, role, parts, rec, why in group:
            _block_a(lines, score, role, parts, rec, entity, primary_authors,
                     why, auto=True)
    return lines


def _block_a(lines, score, role, parts, rec, entity, primary_authors, why,
             auto: bool) -> None:
    decision = (f"**Decision:** recorded as `{role}` — "
                f"`[ ] veto` only if that is wrong"
                if auto else
                f"**Decision:** `[ ] accepted as {role}` / "
                f"`[ ] accepted as other role` / `[ ] rejected`")
    block(lines, f"[{score:+.2f}] {rec['title']}", [
        f"**doi:** `{rec.get('doi') or '—'}`  **year:** "
        f"{rec.get('year')}  **venue:** {rec.get('venue') or '—'}",
        f"**proposed role:** `{role}`  "
        f"(benchmark {parts.get('bench_lex', 0):.2f} vs critique "
        f"{parts.get('crit_lex', 0):.2f})",
        f"**tier effect:** {why}",
        f"**author overlap:** "
        f"{author_overlap(rec, primary_authors.get(entity, []))} "
        f"— routes this decision; never scored (§2.4)",
        f"**score:** {fmt_parts(parts)}",
    ], rec.get("abstract"), decision)


def render_list_b(citing: list[dict], primaries, model_forms, state,
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
        # Same saturation test as list A, over every entity this paper could
        # attach to: if none of their tiers can move, the proposal is recorded
        # rather than asked about.
        targets = [e for e in cited if e in state]
        whys = [(e, *rules.tier_effect(state[e], rec.get("authors")))
                for e in targets]
        needs = (not targets) or any(v == "needs-human" for _, v, _ in whys)
        seen[key] = (score, role, cited, has_abstract, rec, needs, whys)

    rows = sorted(seen.values(), key=lambda t: -t[0])
    human = [r for r in rows if r[5]]
    auto = [r for r in rows if not r[5]]

    lines = [f"## List B — names a class, no catalogued model ({len(rows)})", "",
             "Deduplicated and global, because one such paper is evidence for "
             "several entities at once. This list exists because the gate that "
             "ranks named cases well discards **both** catalogued critiques of "
             "Enformer: neither names it (design §2.3). Each entry lists the "
             "catalogued primary papers it cites, so a curator can see which "
             "entities it might attach to.", "",
             f"**{len(human)} need a decision. {len(auto)} do not** — the same "
             "saturation test as list A, applied across every entity the paper "
             "could attach to. One target whose tier could move is enough to "
             "need a human.", ""]

    for label, group, note in (
        ("Needs a decision", human, None),
        ("Recorded without a decision", auto,
         "Every target entity is already at a tier this paper cannot move. "
         "Recorded, not dropped — veto one if the proposed role is wrong."),
    ):
        if not group:
            continue
        lines += [f"### {label} ({len(group)})", ""]
        if note:
            lines += [note, ""]
        with_abs = [r for r in group if r[3]]
        title_only = [r for r in group if not r[3]]
        for sub, subgroup, subnote in (
            ("With an abstract", with_abs, None),
            ("Title only", title_only,
             "No abstract in OpenAlex, so only the title was scored. One of "
             "Enformer's two catalogued critiques lands here — the gap is not "
             "backfillable from any source in `config/sources.yaml` (§2.6.2)."),
        ):
            if not subgroup:
                continue
            lines += [f"#### {sub} ({len(subgroup)})", ""]
            if subnote:
                lines += [subnote, ""]
            for score, role, cited, _abs, rec, needs, whys in subgroup:
                effect = ("; ".join(f"{e}: {why}" for e, _v, why in whys)
                          or "cites no catalogued primary")
                decision = (f"**Decision:** `[ ] accepted as {role} for: "
                            f"<entity_id>` / `[ ] rejected`" if needs else
                            f"**Decision:** recorded as `{role}` for the "
                            f"entities above — `[ ] veto` only if that is wrong")
                block(lines, f"[{score:+.2f}] {rec['title']}", [
                    f"**doi:** `{rec.get('doi') or '—'}`  **year:** "
                    f"{rec.get('year')}  **venue:** {rec.get('venue') or '—'}",
                    f"**proposed role:** `{role}`",
                    f"**cites catalogued primaries:** "
                    f"{', '.join(f'`{e}`' for e in cited) if cited else 'none matched'}",
                    f"**tier effect:** {effect}",
                    f"**reached via:** `{rec['cites_entity']}`",
                ], rec.get("abstract"), decision)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", default=None,
                        help="candidates JSON (default: the most recent)")
    parser.add_argument("--min-score", type=float, default=3.0,
                        help="section boundary, not a filter (default: 3.0)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite today's review file even if it carries "
                             "ticked decisions")
    args = parser.parse_args()

    # Resolved, because `--candidates literature/candidates/2026-10-20.json`
    # is the natural way to type it and relative_to() below rejects a relative
    # path outright. Same defect as issue #6 in 07_export_site.py, reintroduced
    # here in a new file.
    path = (Path(args.candidates).resolve() if args.candidates
            else latest_candidates())
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
             f"From `{_rel(path)}` "
             f"({data['counts']['discovery']} discovery, "
             f"{data['counts']['citing']} citing). Section boundary at "
             f"`--min-score {args.min_score}`.", "",
             "Tick one decision per candidate and fill in the notes, then run "
             "`python literature/03_record.py`. Accepting a citing paper "
             "proposes an `entity_paper` role; the `evidence_tier` that follows "
             "is derived by `scripts/05_validate.py`, never set here.", "",
             "---", ""]

    lines += render_discovery(data["discovery"], args.min_score)
    tier_state = rules.read_tier_state()
    lines += render_list_a(data["citing"], primaries_oa, model_forms, all_forms,
                           primary_authors, tier_state, args.min_score)
    lines += render_list_b(data["citing"], primaries_oa, model_forms,
                           tier_state, args.min_score)

    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    out = REVIEWS_DIR / f"review_{date.today().isoformat()}.md"
    if not args.force and _has_decisions(out):
        raise SystemExit(
            f"{_rel(out)} already carries ticked decisions; refusing to "
            f"overwrite them.\nRun 03_record.py on it first, move it aside, "
            f"or pass --force to discard them.")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {_rel(out)}")
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
