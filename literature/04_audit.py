#!/usr/bin/env python
"""
literature/04_audit.py
----------------------
Draw a reproducible sample of the decisions no human made, and -- on a second
run over the filled-in file -- measure how often they were wrong.

Reads:
    literature/reviews/review_YYYY-MM-DD.md   the decisions, in context
    literature/decisions.yaml                 the ledger, as the authority on
                                              which of them were recorded

Writes:
    literature/audits/audit_YYYY-MM-DD.md     the sample, for a curator
    reports/audit_history.md                  one appended section per cycle

Why this exists. A cycle now records a few hundred things without asking: a
role proposal whose entity is already at a tier the row cannot move
(`02_triage.py`, "Recorded without a decision"), and a discovery candidate
below `--min-score` (recorded as deferred). Both are justified by argument --
the tier is saturated, the score is low -- and an argument is not a measurement.
A Nucleic Acids Research reviewer will ask how the roles are assigned, and "the
code does not make mistakes" is not an answer; a precision with an interval on
it is. This script produces that number and commits its history, so a later
change to the weights in `literature/triage_rules.py` has a cost that shows up
in `git diff`.

**It measures the pipeline and must not change it.** Nothing here writes
`records/`, `literature/papers.yaml` or `literature/decisions.yaml`, and
nothing reads an audit back into triage. A `no` in an audit file is a finding
for a curator to act on by hand, not an input to the next cycle's scoring --
see the "Re-opening" note written into every audit file, and docs/triage_design.md
§0: triage ranks, it does not include, and it does not tier. Author overlap
appears in a sampled block because the review file displays it as context; it is
not scored here any more than it is there (§2.4).

**What is sampled, and what is not.** Only the two classes no human touched.
The role proposals a curator accepted by hand are not sampled: they are a
measurement of a human against themself, they double the reading, and they
answer a different question than the one a reviewer will ask. Vetoed proposals
and promoted deferrals are likewise out of the frame -- a human already looked
at those, and the look is the thing being measured. `needs-role` entries are
out too: the role came out `unclear`, so nothing was attached and there is no
wrong row to find.

Run from project root:
    python literature/04_audit.py [--review PATH] [-n 35] [--force]
    python literature/04_audit.py --score [--audit PATH]
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import random
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage_rules as rules                            # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REVIEWS_DIR = ROOT / "literature" / "reviews"
AUDITS_DIR = ROOT / "literature" / "audits"
HISTORY = ROOT / "reports" / "audit_history.md"

DEFAULT_N = 35

# The two classes, in the order they are reported. The label is what goes in
# the audit file and the history; the key is what the code carries around.
CLASSES = {
    "auto-role": "auto-recorded role",
    "auto-defer": "deferred candidate",
}
WHAT_WRONG = {
    "auto-role": "a role row attached to an entity that the paper does not "
                 "play that role for",
    "auto-defer": "a resource that belongs in the catalogue, left out of the "
                  "review file's own ask",
}


# ══ The decision grammar, borrowed rather than copied ════════════════════════
# 03_record.py owns the five decision shapes `02_triage.py` writes. A second
# copy of that grammar here would drift the first time the wording changes, and
# a drifted copy fails in the direction that flatters the pipeline: a shape
# this script stops recognising silently leaves its class out of the frame, and
# a smaller frame reads as a cleaner one. The module name starts with a digit,
# so it cannot be imported by name.

def _load_record_module():
    path = ROOT / "literature" / "03_record.py"
    spec = importlib.util.spec_from_file_location("cfcr_record", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


record = _load_record_module()

RE_BLOCK = record.RE_BLOCK
RE_ENTITY_HEAD = record.RE_ENTITY_HEAD
RE_ID = record.RE_ID
RE_OPENALEX = record.RE_OPENALEX
RE_DOI = re.compile(r"\*\*doi:\*\* `([^`]+)`")
RE_TIER_EFFECT = re.compile(r"\*\*tier effect:\*\* (.+)$")
RE_OVERLAP = re.compile(r"\*\*author overlap:\*\* (.+?) — routes")
RE_PROPOSED = re.compile(r"\*\*proposed role:\*\* `([^`]+)`")
RE_SCORE_LINE = re.compile(r"\*\*score:\*\* (.+)$")

RE_AUDIT_CLASS = re.compile(r"^- \*\*class:\*\* (.+)$")
RE_AUDIT_KEY = re.compile(r"^- \*\*ledger key:\*\* `([^`]+)`")
RE_AUDIT_VERDICT = re.compile(
    r"^\*\*Correct\?\*\* `\[([ xX])\] yes` / `\[([ xX])\] no`$")
RE_AUDIT_HEADER = re.compile(r"^- \*\*(cycle|seed|frame|sampled):\*\* (.+)$")


class Fail(Exception):
    """A parse or consistency failure, reported with a line number."""


# ══ Statistics ═══════════════════════════════════════════════════════════════

def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """
    95% Wilson score interval for k errors in n draws.

    Wilson rather than the textbook normal interval because the whole point of
    this audit is that the counts are small and the error rate is expected to
    be near zero, which is exactly where `p ± z·sqrt(p(1-p)/n)` returns the
    interval [0, 0] and claims certainty from a single clean sample.
    """
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z / denom * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


# ══ Pass 1: draw the sample ══════════════════════════════════════════════════

def latest_review() -> Path:
    files = sorted(f for f in REVIEWS_DIR.glob("review_*.md")
                   if re.fullmatch(r"review_\d{4}-\d{2}-\d{2}", f.stem))
    if not files:
        raise SystemExit("no review file; run literature/02_triage.py first")
    return files[-1]


def split_blocks(path: Path) -> list[dict]:
    """
    One dict per candidate block in a review file, with its raw lines.

    `03_record.py:parse_review` keeps the meta and decision lines and discards
    the abstract, which is the one thing a curator judging a sampled decision
    most needs. So the block is kept whole here and read with 03_record's own
    regexes.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    blocks: list[dict] = []
    section, entity, cur = None, None, None

    for n, line in enumerate(lines, 1):
        if line.startswith("## "):
            section = ("discovery" if "Discovery" in line else
                       "A" if line.startswith("## List A") else
                       "B" if line.startswith("## List B") else None)
            entity, cur = None, None
            continue
        head = RE_ENTITY_HEAD.match(line)
        if head:
            entity, cur = head.group(1), None
            continue
        start = RE_BLOCK.match(line)
        if start:
            cur = {"line": n, "score": float(start.group(1)),
                   "title": " ".join(start.group(2).split()),
                   "section": section, "entity": entity,
                   "meta": [], "abstract": "", "decision": None}
            blocks.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith("- **"):
            cur["meta"].append(line)
        elif line.startswith("> "):
            cur["abstract"] = line[2:].strip()
        elif line.startswith("**Decision:**"):
            cur["decision"] = line.rstrip()
        elif line.strip() == "---":
            cur = None
    return blocks


def meta(block: dict, pattern: re.Pattern) -> str | None:
    for line in block["meta"]:
        m = pattern.search(line)
        if m:
            return m.group(1)
    return None


def ledger_key(block: dict) -> str | None:
    """
    The key `03_record.py` filed this block's decision under.

    Recomputed from the block's own metadata rather than matched on the title:
    1626 of the citing works in the 2026-10-21 run share a title with another
    work in the same run, which is why the review file prints the OpenAlex id
    in the first place.
    """
    if block["section"] == "discovery":
        ident = meta(block, RE_ID)
        if not ident or ident == "no id":
            return None
        # `02_triage.py` prints the paper_id where there is one and the Europe
        # PMC id otherwise, and `rules.ledger_key` prefixes the latter.
        return ident if "/" in ident or ident.startswith("arxiv:") \
            else f"europepmc:{ident}"
    doi = meta(block, RE_DOI)
    if doi and doi != "—":
        return doi
    oa = meta(block, RE_OPENALEX)
    return f"openalex:{oa}" if oa else None


def frame(blocks: list[dict],
          decided: dict) -> tuple[list[dict], list[str], int]:
    """
    The sampling frame: the auto-decided blocks the ledger confirms it recorded.

    A block whose decision shape is automatic but which carries no matching
    ledger entry is not in the frame and is reported, not skipped. It means
    `03_record.py` has not been run over this review file yet, or refused it --
    and a frame that silently shrinks when the ledger is stale would report a
    sample of 12 as if it were a sample of 35.

    The one expected absence is counted rather than reported: a proposal whose
    role came out `unclear` is filed as `needs-role` and nothing is attached,
    so there is no wrong row to find.
    """
    items: list[dict] = []
    missing: list[str] = []
    unclear = 0

    for block in blocks:
        if not block["decision"]:
            continue
        veto = record.SHAPES["veto"].match(block["decision"])
        defer = record.SHAPES["deferred"].match(block["decision"])
        if veto:
            # A ticked veto is a human decision -- and a found error, not an
            # unmeasured one. Out of the frame either way.
            if record.ticked(veto.group(2)):
                continue
            cls, want, role = "auto-role", "recorded", veto.group(1)
        elif defer:
            if record.ticked(defer.group(1)):
                continue
            cls, want, role = "auto-defer", "deferred", None
        else:
            continue

        key = ledger_key(block)
        if key is None:
            missing.append(f"line {block['line']}: no id in the block, so the "
                           f"ledger entry behind it cannot be found")
            continue
        entries = [d for d in decided.get(key) or []
                   if d.get("decision") == want
                   and d.get("list") == block["section"]]
        if not entries:
            if any(d.get("decision") == "needs-role"
                   for d in decided.get(key) or []):
                unclear += 1
                continue
            missing.append(f"line {block['line']}: `{key}` carries no "
                           f"`{want}` entry for list {block['section']} in "
                           f"literature/decisions.yaml")
            continue

        items.append({
            "class": cls, "key": key, "role": role,
            "title": block["title"], "score": block["score"],
            "section": block["section"], "entity": block["entity"],
            "entities": entries[0].get("entities") or
            ([block["entity"]] if block["entity"] else []),
            "why": meta(block, RE_TIER_EFFECT) or "—",
            "overlap": meta(block, RE_OVERLAP),
            "proposed": meta(block, RE_PROPOSED) or role,
            "score_parts": meta(block, RE_SCORE_LINE),
            "abstract": block["abstract"],
            "line": block["line"],
        })
    return items, missing, unclear


def allocate(sizes: dict[str, int], n: int) -> dict[str, int]:
    """
    Split a sample of n evenly between the classes that have anything in them.

    Evenly, not in proportion to the classes' sizes: the output is one error
    rate per class, so what matters is that neither class ends up with a
    handful. A class smaller than its share gives the remainder back.
    """
    live = {c: s for c, s in sizes.items() if s}
    out = {c: 0 for c in sizes}
    left = n
    while left > 0 and any(out[c] < live[c] for c in live):
        room = [c for c in live if out[c] < live[c]]
        share = max(1, left // len(room))
        for c in room:
            take = min(share, live[c] - out[c], left)
            out[c] += take
            left -= take
            if left == 0:
                break
    return out


def draw(items: list[dict], n: int, seed: int) -> dict[str, list[dict]]:
    """
    The sample, per class, reproducibly.

    Sorted before the draw and seeded off the cycle date, so re-running this
    on the same review file and ledger returns the same items in the same
    order and a curator's answers can be checked against a fresh draw.
    """
    by_class: dict[str, list[dict]] = {c: [] for c in CLASSES}
    for it in items:
        by_class[it["class"]].append(it)
    for c in by_class:
        by_class[c].sort(key=lambda it: (it["key"], it["entity"] or "",
                                         it["role"] or "", it["line"]))

    want = allocate({c: len(v) for c, v in by_class.items()}, n)
    rng = random.Random(seed)
    return {c: sorted(rng.sample(by_class[c], want[c]),
                      key=lambda it: -it["score"])
            for c in CLASSES}


def ci_note(n: int) -> str:
    """What a sample of n buys, at a few plausible error rates."""
    rows = [f"| errors in {n} | observed rate | 95% CI (Wilson) |",
            "|---|---|---|"]
    for k in (0, 1, 2, 4):
        if k > n:
            continue
        lo, hi = wilson(k, n)
        rows.append(f"| {k} | {pct(k / n)} | {pct(lo)} – {pct(hi)} |")
    return "\n".join(rows)


def render(sample: dict[str, list[dict]], sizes: dict[str, int],
           cycle: str, seed: int, review: Path, missing: list[str],
           unclear: int) -> str:
    total = sum(len(v) for v in sample.values())
    lines = [
        f"# Sampled audit — {cycle}", "",
        f"Generated by `python literature/04_audit.py` on "
        f"{date.today().isoformat()} from "
        f"`{review.relative_to(ROOT).as_posix()}` and "
        f"`literature/decisions.yaml`.", "",
        "- **cycle:** " + cycle,
        f"- **seed:** `{seed}` (the cycle date, so the same sample can be "
        f"re-drawn and checked)",
        "- **frame:** " + ", ".join(
            f"{CLASSES[c]} {sizes[c]}" for c in CLASSES),
        "- **sampled:** " + ", ".join(
            f"{CLASSES[c]} {len(sample[c])}" for c in CLASSES),
        "",
        "## What this measures", "",
        "Every block below was decided by `02_triage.py` and recorded by "
        "`03_record.py` without a human in the loop. Two classes, because a "
        "wrong one costs something different in each:", "",
        f"- **{CLASSES['auto-role']}** — the entity is already at an "
        f"`evidence_tier` this row cannot move, so the review file recorded "
        f"the proposed role instead of asking. A wrong one is "
        f"{WHAT_WRONG['auto-role']}.",
        f"- **{CLASSES['auto-defer']}** — the candidate scored below "
        f"`--min-score`, so it was recorded as deferred instead of asked "
        f"about. A wrong one is {WHAT_WRONG['auto-defer']}.", "",
        "The two are counted separately and never pooled. Pooling them would "
        "average a missing row into a missing record, and the catalogue is not "
        "judged on those equally.", "",
    ]
    if unclear:
        lines += [f"{unclear} further auto-decided block(s) are outside the "
                  f"frame: the proposed role came out `unclear`, so "
                  f"`03_record.py` filed a `needs-role` entry and attached "
                  f"nothing. There is no wrong row to find in those, only an "
                  f"unmade decision.", ""]
    lines += [
        f"**What {total} items buy.** Not three significant figures. At "
        f"{len(sample['auto-role'])} items in the larger class:", "",
        ci_note(max(len(v) for v in sample.values()) or 1), "",
        "So a clean sample does not show that the error rate is zero; it shows "
        "it is probably under a tenth. That is worth having and worth stating "
        "as such. A tighter interval needs a bigger sample, and the sample "
        "size was chosen to be finishable in a sitting — which is the "
        "constraint the whole pipeline exists to respect.", "",
        "## How to work through it", "",
        "Tick exactly one box per block, then run "
        "`python literature/04_audit.py --score`. **Correct** means the "
        "decision the pipeline made is the one you would have made: for a "
        "role, that the paper really plays that role for that entity; for a "
        "deferral, that the resource really does not belong in the catalogue.",
        "",
        "**Re-opening is deliberately manual.** A `no` here is not fed back "
        "into the next review file. This script measures the pipeline and does "
        "not change what it decides (docs/triage_design.md §0), and an audit "
        "that re-opened its own findings would make the next cycle's numbers a "
        "measurement of the audit. Fix the row by hand in `records/`, or "
        "reject the ledger entry, and say so in the notes.", "",
        "---", "",
    ]

    if missing:
        lines += [f"**{len(missing)} auto-decided block(s) are not in the "
                  f"frame**, because the ledger carries no entry for them. Run "
                  f"`python literature/03_record.py` over this review file "
                  f"first if that is unexpected.", ""]
        lines += [f"- {m}" for m in missing] + ["", "---", ""]

    for cls, label in CLASSES.items():
        group = sample[cls]
        lines += [f"## {label} — {len(group)} of {sizes[cls]}", ""]
        if not group:
            lines += ["Nothing in this class this cycle.", "", "---", ""]
            continue
        for it in group:
            lines += [f"#### [{it['score']:+.2f}] {it['title']}", "",
                      f"- **class:** {label}",
                      f"- **ledger key:** `{it['key']}`",
                      f"- **list:** {it['section']}"
                      + (f" → {', '.join(f'`{e}`' for e in it['entities'])}"
                         if it["entities"] else "")]
            if cls == "auto-role":
                lines += [f"- **recorded as:** `{it['role']}`"
                          f" (proposed `{it['proposed']}`)",
                          f"- **why it was not asked about:** {it['why']}"]
                if it["overlap"]:
                    lines.append(f"- **author overlap:** {it['overlap']} — "
                                 f"context only, never scored (§2.4)")
            else:
                lines.append(f"- **why it was not asked about:** scored "
                             f"{it['score']:+.2f}, below the section boundary")
            if it["score_parts"]:
                lines.append(f"- **score:** {it['score_parts']}")
            if it["abstract"]:
                lines += ["", f"> {it['abstract']}"]
            lines += ["", "**Correct?** `[ ] yes` / `[ ] no`",
                      "**Notes:** _(if no: what the right answer is, and "
                      "whether you fixed it)_", "", "---", ""]

    return "\n".join(lines)


# ══ Pass 2: score a filled-in audit file ═════════════════════════════════════

def read_audit(path: Path) -> tuple[dict, dict[str, dict]]:
    """
    The audit file's header, and per-class yes/no/blank counts.

    Reads the header back rather than recomputing it, so a history line always
    describes the file the curator actually answered -- not a frame that has
    moved since, which it will have the moment 03_record.py runs again.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    header: dict[str, str] = {}
    label_to_class = {v: k for k, v in CLASSES.items()}
    tally = {c: {"yes": 0, "no": 0, "blank": 0, "wrong": []} for c in CLASSES}
    cur_class, cur_title, errors = None, None, []

    for n, line in enumerate(lines, 1):
        h = RE_AUDIT_HEADER.match(line)
        if h and h.group(1) not in header:
            header[h.group(1)] = h.group(2)
            continue
        start = RE_BLOCK.match(line)
        if start:
            cur_class, cur_title = None, " ".join(start.group(2).split())
            continue
        c = RE_AUDIT_CLASS.match(line)
        if c:
            cur_class = label_to_class.get(c.group(1).strip())
            if cur_class is None:
                errors.append(f"line {n}: unknown class "
                              f"'{c.group(1).strip()}'")
            continue
        v = RE_AUDIT_VERDICT.match(line)
        if v:
            if cur_class is None:
                errors.append(f"line {n}: a **Correct?** line with no "
                              f"`- **class:**` above it")
                continue
            yes, no = record.ticked(v.group(1)), record.ticked(v.group(2))
            if yes and no:
                errors.append(f"line {n}: both yes and no are ticked")
            elif yes:
                tally[cur_class]["yes"] += 1
            elif no:
                tally[cur_class]["no"] += 1
                tally[cur_class]["wrong"].append(cur_title)
            else:
                tally[cur_class]["blank"] += 1

    for key in ("cycle", "seed", "frame", "sampled"):
        if key not in header:
            errors.append(f"no `- **{key}:**` line in the header")
    if errors:
        raise Fail(f"{path.name}:\n  " + "\n  ".join(errors))
    return header, tally


def score_lines(header: dict, tally: dict) -> list[str]:
    out = [f"cycle {header['cycle']}, "
           f"seed {header['seed'].split()[0].strip('`')}",
           f"frame:   {header['frame']}",
           f"sampled: {header['sampled']}", ""]
    for cls, label in CLASSES.items():
        t = tally[cls]
        answered = t["yes"] + t["no"]
        if not answered:
            out.append(f"{label:22s} no answers "
                       f"({t['blank']} block(s) left blank)")
            continue
        lo, hi = wilson(t["no"], answered)
        out.append(f"{label:22s} {t['no']}/{answered} wrong "
                   f"= {pct(t['no'] / answered):>4s}   "
                   f"95% CI {pct(lo)}–{pct(hi)}"
                   + (f"   ({t['blank']} blank)" if t["blank"] else ""))
        for title in t["wrong"]:
            out.append(f"  wrong: {title[:88]}")
    return out


HISTORY_HEADER = """\
# Sampled-audit history

Written by `python literature/04_audit.py --score`, one section per cycle,
appended. Committed for the same reason `reports/triage_eval.md` is: the claim
that CFCR's automated decisions are good enough to be made automatically is a
quantitative claim, and this is the only artifact that carries the number. A
change to the weights in `literature/triage_rules.py` should move these rates,
and `git diff` on this file is what says whether it did.

The two classes are never pooled. A wrong auto-recorded role puts a row in the
catalogue that does not belong there; a wrongly deferred candidate leaves a
resource out of the review file's own ask. Both are errors, neither is the same
error, and an average of the two describes nothing.

The intervals are Wilson, at 95%, on samples of a few dozen. They are wide on
purpose. A clean sample of 18 is consistent with a true error rate up to about
18%, and reporting it as "0%" would be the one dishonest number in the
repository.
"""


def append_history(header: dict, tally: dict) -> None:
    body = "\n".join(score_lines(header, tally))
    section = (f"## {header['cycle']}\n\n"
               f"Scored on {date.today().isoformat()}.\n\n"
               f"```\n{body.strip(chr(10))}\n```\n")
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    if HISTORY.exists():
        old = HISTORY.read_text(encoding="utf-8")
        # Re-scoring a cycle replaces its section rather than appending a
        # second one: a curator answers an audit file over several sittings and
        # re-runs this, and two sections for one cycle would make the trend
        # read as two cycles.
        pattern = re.compile(rf"^## {re.escape(header['cycle'])}\n.*?"
                             rf"(?=^## |\Z)", re.S | re.M)
        new = (pattern.sub(section, old) if pattern.search(old)
               else old.rstrip("\n") + "\n\n" + section)
    else:
        new = HISTORY_HEADER + "\n" + section
    HISTORY.write_text(new, encoding="utf-8", newline="")


# ══ Entry point ══════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", default=None,
                        help="review file to audit (default: the most recent)")
    parser.add_argument("-n", "--sample-size", type=int, default=DEFAULT_N,
                        help=f"items to sample in total (default: {DEFAULT_N})")
    parser.add_argument("--force", action="store_true",
                        help="overwrite an audit file that carries answers")
    parser.add_argument("--score", action="store_true",
                        help="second pass: read a filled-in audit file and "
                             "write reports/audit_history.md")
    parser.add_argument("--audit", default=None,
                        help="with --score: the audit file (default: the one "
                             "for the review file's cycle)")
    args = parser.parse_args()

    review = (Path(args.review).resolve() if args.review else latest_review())
    cycle = review.stem[len("review_"):]
    out = (Path(args.audit).resolve() if args.audit
           else AUDITS_DIR / f"audit_{cycle}.md")

    if args.score:
        if not out.exists():
            print(f"error: {out} not found; draw a sample first",
                  file=sys.stderr)
            return 1
        header, tally = read_audit(out)
        body = "\n".join(score_lines(header, tally))
        print(body)
        append_history(header, tally)
        print(f"\nwrote {HISTORY.relative_to(ROOT).as_posix()}")
        return 0

    blocks = split_blocks(review)
    items, missing, unclear = frame(blocks, rules.read_decisions())
    sizes = {c: sum(1 for it in items if it["class"] == c) for c in CLASSES}
    print(f"reading {review.name}: {len(blocks)} blocks, "
          f"{sum(sizes.values())} auto-decided and recorded")
    for c, label in CLASSES.items():
        print(f"  {label:22s} {sizes[c]}")
    if unclear:
        print(f"  {unclear:21d} outside the frame: role `unclear`, "
              f"nothing attached")
    if missing:
        print(f"  {len(missing)} auto-decided block(s) have no ledger entry")
    if not sum(sizes.values()):
        print("nothing to audit: the ledger confirms no recorded role or "
              "deferral for this cycle."
              + (f" {len(missing)} block(s) in the review file were decided "
                 f"automatically but are not in literature/decisions.yaml, so "
                 f"run `python literature/03_record.py` first."
                 if missing else ""), file=sys.stderr)
        return 1

    # Same guard as 02_triage.py's: the file is named after the cycle, so a
    # second run would silently replace a curator's answers with blank boxes.
    if out.exists() and not args.force:
        text = out.read_text(encoding="utf-8")
        if re.search(r"\*\*Correct\?\*\* `\[[xX]\]", text):
            raise SystemExit(
                f"{out.relative_to(ROOT).as_posix()} already carries answers; "
                f"refusing to overwrite them.\nRun "
                f"`04_audit.py --score` on it first, move it aside, or pass "
                f"--force.")

    seed = int(cycle.replace("-", ""))
    sample = draw(items, min(args.sample_size, sum(sizes.values())), seed)
    AUDITS_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(render(sample, sizes, cycle, seed, review, missing,
                          unclear), encoding="utf-8", newline="")
    print(f"wrote {out.relative_to(ROOT).as_posix()}: "
          f"{sum(len(v) for v in sample.values())} items, seed {seed}")
    print("next: tick one box per block, then "
          "python literature/04_audit.py --score")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fail as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
