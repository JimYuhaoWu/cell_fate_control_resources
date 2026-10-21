#!/usr/bin/env python
"""
literature/03_record.py
-----------------------
Read a worked-through review file and write its decisions into the repository.

Reads:
    literature/reviews/review_YYYY-MM-DD.md   the ticked decisions
    literature/candidates/<date>.json         the metadata behind them, named
                                              in the review file's own header

Writes:
    records/*.yaml            new entity records, and new rows on the join
    literature/papers.yaml    open metadata for every newly attached paper
    literature/decisions.yaml the ledger -- every decision, including the noes

Three things this script must not do.

**It never writes `evidence_tier`.** The tier is derived in
`scripts/05_validate.py` from author overlap between a model's `primary` paper
and the papers whose role is `benchmark` or `critique` (docs/triage_design.md
§0, §2.4). This script writes the role and stops. A new record therefore
carries no `model_ext` block at all, not one with a null tier: QC derives
`self-reported` for a model with no evaluations, so a null in the block is a
disagreement, and inventing `self-reported` to match would be this script
asserting the one number the catalogue is not allowed to assert.

**It never drops a decision.** Accepted, rejected, deferred and vetoed all land
in `literature/decisions.yaml`, keyed by paper id, so a rejection is recorded
once and is not re-proposed from scratch next cycle. `02_triage.py` reads the
rejections back; deferrals are deliberately not suppressed, because the review
file promises they return if the scoring changes.

**It never invents a field.** A record gets what the candidate actually
carries -- id, title, year, the query's `fate_axis` -- and nothing else. In
particular `description` is left empty rather than filled with the publisher's
abstract, which describes a paper and not a resource. The guessed part is the
entity's *name*, taken from the title, and that is what `review_state:
unreviewed` is for: the record is in `db/` and checked by QC, and
`07_export_site.py` keeps it off the site until a human has looked at it.

The five decision shapes `02_triage.py` writes, and what each does here:

    `[x] accepted` / `[ ] rejected`              discovery -> a new record
    deferred -- `[x] promote`                    discovery -> a new record
    `[x] accepted as <role>` / ... / `[ ] rejected`   list A -> a join row
    recorded as `<role>` -- `[ ] veto`           list A/B -> a join row
    `[x] accepted as <role> for: <entity_id>`    list B -> a join row

A block whose decision line matches none of them is a parse failure, reported
with its line number: a decision this script cannot read must not look like a
decision nobody made.

Run from project root:
    python literature/03_record.py [--review PATH] [--candidates PATH]
                                   [--curator NAME]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage_rules as rules                            # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REVIEWS_DIR = ROOT / "literature" / "reviews"
PAPERS_YAML = ROOT / "literature" / "papers.yaml"
RECORDS_DIR = ROOT / "records"

# entity type -> the record file that owns it. Not derived from the file names:
# `module` lives in module_libraries.yaml, so the mapping has to be written
# down somewhere, and a wrong guess would quietly start a seventh record file.
RECORD_FILES = {
    "model": "models.yaml",
    "benchmark": "benchmarks.yaml",
    "dataset": "datasets.yaml",
    "module": "module_libraries.yaml",
    "protocol": "protocols.yaml",
    "database": "databases.yaml",
}

# OpenAlex `type` -> `venue_type`, for the values that map without a guess.
# `article` is left out on purpose: it covers journal articles and much else,
# and schema.py's VENUE_TYPES distinguishes them.
OA_VENUE_TYPE = {
    "preprint": "preprint",
    "conference-paper": "conference",
    "dissertation": "thesis",
}


class Fail(Exception):
    """A parse or consistency failure, reported with a line number."""


# ══ Review parsing ═══════════════════════════════════════════════════════════

RE_SOURCE = re.compile(r"^From `([^`]+)`", re.M)
RE_BLOCK = re.compile(r"^#### \[([+-]?\d+(?:\.\d+)?)\] (.+)$")
RE_ENTITY_HEAD = re.compile(r"^#### ([a-z_]+:[A-Za-z0-9._-]+) — tier now: ")
RE_ID = re.compile(r"\*\*id:\*\* `([^`]+)`")
RE_OPENALEX = re.compile(r"\*\*openalex:\*\* `([^`]+)`")
RE_PRIMARIES = re.compile(r"\*\*cites catalogued primaries:\*\* (.+)$")
RE_BACKTICKED = re.compile(r"`([a-z_]+:[A-Za-z0-9._-]+)`")

BOX = r"\[([ xX])\]"
SHAPES = {
    "discovery": re.compile(
        rf"^\*\*Decision:\*\* `{BOX} accepted` / `{BOX} rejected`$"),
    "deferred": re.compile(
        rf"^\*\*Decision:\*\* deferred — `{BOX} promote` if this should be a "
        rf"record after all$"),
    "role": re.compile(
        rf"^\*\*Decision:\*\* `{BOX} accepted as (.+?)` / "
        rf"`{BOX} accepted as other role` / `{BOX} rejected`$"),
    "role_for": re.compile(
        rf"^\*\*Decision:\*\* `{BOX} accepted as (.+?) for: (.+?)` / "
        rf"`{BOX} rejected`$"),
    "veto": re.compile(
        rf"^\*\*Decision:\*\* recorded as `(.+?)`"
        rf"(?: for the entities above)? — `{BOX} veto` only if that is wrong$"),
}


def ticked(box: str) -> bool:
    return box.lower() == "x"


def parse_review(path: Path) -> tuple[str, list[dict]]:
    """
    The candidates file the review was built from, and one dict per block.

    Sections are tracked for the two things the decision line does not carry:
    which list a block is in, and -- in list A -- which entity the proposal is
    about, which is the `#### <entity_id> — tier now:` heading above it.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    source = None
    blocks: list[dict] = []
    section, entity, cur = None, None, None

    for n, line in enumerate(lines, 1):
        if source is None:
            m = RE_SOURCE.match(line)
            if m:
                source = m.group(1)
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
                   "title": start.group(2).strip(), "section": section,
                   "entity": entity, "meta": [], "decision": None,
                   "decision_line": None, "notes": ""}
            blocks.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith("- **"):
            cur["meta"].append(line)
        elif line.startswith("**Decision:**"):
            cur["decision"], cur["decision_line"] = line.rstrip(), n
        elif line.startswith("**Notes:**"):
            note = line[len("**Notes:**"):].strip()
            cur["notes"] = "" if note.startswith("_(") else note
        elif line.strip() == "---":
            cur = None

    if source is None:
        raise Fail(f"{path.name}: no `From \\`...\\`` header naming the "
                   f"candidates file this review was built from")
    return source, blocks


def meta_value(block: dict, pattern: re.Pattern) -> str | None:
    for line in block["meta"]:
        m = pattern.search(line)
        if m:
            return m.group(1)
    return None


def note_field(notes: str, key: str) -> str | None:
    m = re.search(rf"\b{key}:\s*([^;]+)", notes)
    return m.group(1).strip() if m else None


def prose(notes: str) -> str:
    """
    The curator's note with the `name:` and `role:` directives removed.

    They are instructions to this script, not commentary on the paper, and
    `note:` on the join is what a reader of records/*.yaml sees.
    """
    kept = [seg.strip() for seg in notes.split(";")
            if not re.match(r"\s*(name|role):", seg)]
    return "; ".join(s for s in kept if s)


def classify(block: dict) -> dict:
    """
    One block's decision line -> {verdict, role?, targets?}.

    `verdict` is one of accepted / rejected / promoted / deferred / recorded /
    vetoed / pending. `pending` is a block with nothing ticked: it is not a
    decision and nothing is written for it, which is how a curator works
    through 340 candidates over several sittings.
    """
    line, n = block["decision"], block["decision_line"]
    if line is None:
        raise Fail(f"line {block['line']}: block \"{block['title'][:60]}\" has "
                   f"no **Decision:** line")

    m = SHAPES["discovery"].match(line)
    if m:
        yes, no = ticked(m.group(1)), ticked(m.group(2))
        if yes and no:
            raise Fail(f"line {n}: both `accepted` and `rejected` are ticked")
        return {"verdict": "accepted" if yes else "rejected" if no
                else "pending"}

    m = SHAPES["deferred"].match(line)
    if m:
        return {"verdict": "promoted" if ticked(m.group(1)) else "deferred"}

    m = SHAPES["role"].match(line)
    if m:
        as_role, other, no = (ticked(m.group(1)), ticked(m.group(3)),
                              ticked(m.group(4)))
        if sum((as_role, other, no)) > 1:
            raise Fail(f"line {n}: more than one box is ticked")
        if no:
            return {"verdict": "rejected"}
        if other:
            role = note_field(block["notes"], "role")
            if not role:
                raise Fail(
                    f"line {n}: `accepted as other role` is ticked but the "
                    f"role is not named. Write `role: <role>` in the "
                    f"**Notes:** line, or replace `other role` in the decision "
                    f"line with the role itself")
            return {"verdict": "accepted", "role": role}
        if as_role:
            return {"verdict": "accepted", "role": m.group(2).strip()}
        return {"verdict": "pending"}

    m = SHAPES["role_for"].match(line)
    if m:
        yes, no = ticked(m.group(1)), ticked(m.group(4))
        if yes and no:
            raise Fail(f"line {n}: both `accepted` and `rejected` are ticked")
        if no:
            return {"verdict": "rejected"}
        if not yes:
            return {"verdict": "pending"}
        targets = [t.strip().strip("`") for t in m.group(3).split(",")]
        targets = [t for t in targets if t]
        if any(t.startswith("<") for t in targets) or not targets:
            raise Fail(f"line {n}: accepted, but the target entity is still "
                       f"the `<entity_id>` placeholder. Replace it with the "
                       f"entity this paper evaluates")
        return {"verdict": "accepted", "role": m.group(2).strip(),
                "targets": targets}

    m = SHAPES["veto"].match(line)
    if m:
        return {"verdict": "vetoed" if ticked(m.group(2)) else "recorded",
                "role": m.group(1).strip()}

    raise Fail(f"line {n}: decision line matches none of the five shapes "
               f"02_triage.py writes:\n    {line}")


# ══ Repository state ═════════════════════════════════════════════════════════

def read_records() -> tuple[dict, dict, set]:
    """
    entity_id -> its record file, entity_id -> has a `primary` paper, and the
    (entity_id, paper_id, role) triples already on the join.

    Read from `records/*.yaml` rather than `db/*.tsv`: the YAML is the source
    of truth, and the snapshots are one build behind any uncommitted curation.
    """
    homes, has_primary, joined = {}, {}, set()
    for path in sorted(RECORDS_DIR.glob("*.yaml")):
        for rec in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            eid = rec["entity_id"]
            homes[eid] = path
            roles = set()
            for paper in rec.get("papers") or []:
                roles.add(paper["role"])
                joined.add((eid, paper["paper_id"], paper["role"]))
            has_primary[eid] = "primary" in roles
    return homes, has_primary, joined


def read_papers() -> set[str]:
    return {p["paper_id"] for p
            in yaml.safe_load(PAPERS_YAML.read_text(encoding="utf-8")) or []}


# ══ YAML emission ════════════════════════════════════════════════════════════
#
# Hand-formatted rather than yaml.safe_dump'd, because both targets are curated
# files a human reads and diffs: papers.yaml quotes its scalars and folds its
# abstracts, and a dumper would reflow the file's existing style on the first
# write. json.dumps is used for the quoting -- a JSON string is a valid YAML
# double-quoted scalar, with the same escapes.


def _q(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _scalar(value: str) -> str:
    """
    Plain where plain is safe, quoted otherwise.

    `records/*.yaml` writes `paper_id: arxiv:2311.12570` and `name: Enformer`
    unquoted while `papers.yaml` quotes everything, so the two emitters differ
    on purpose: each new block should read like the file it lands in.
    """
    if (re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._/:+-]*", value)
            and ": " not in value and " #" not in value
            and not value.endswith(" ")):
        return value
    return _q(value)


def _folded(value: str, indent: int) -> list[str]:
    """
    A `>-` folded scalar. Whitespace is collapsed first so the value reads back
    byte-identical: folding joins the wrapped lines with single spaces.
    """
    pad = " " * indent
    text = " ".join(value.split())
    return [">-"] + [pad + line for line
                     in textwrap.wrap(text, width=76 - indent)]


def paper_entry(paper: dict) -> list[str]:
    """One `literature/papers.yaml` block, in that file's own style."""
    out = [f"- paper_id: {_q(paper['paper_id'])}"]
    for key in ("doi", "title"):
        out.append(f"  {key}: {_q(paper[key])}" if paper.get(key)
                   else f"  {key}: null")
    if paper.get("authors"):
        out.append("  authors:")
        out += [f"    - {_q(a)}" for a in paper["authors"]]
    else:
        out.append("  authors: null")
    out.append(f"  year: {paper['year']}" if paper.get("year")
               else "  year: null")
    for key in ("venue", "venue_type"):
        out.append(f"  {key}: {_q(paper[key])}" if paper.get(key)
                   else f"  {key}: null")
    if paper.get("abstract"):
        folded = _folded(paper["abstract"], 4)
        out.append(f"  abstract: {folded[0]}")
        out += folded[1:]
    else:
        out.append("  abstract: null")
    out.append(f"  url: {_q(paper['url'])}" if paper.get("url")
               else "  url: null")
    out.append("  preprint_of: null")
    out.append(f"  metadata_source: {_q(paper['metadata_source'])}")
    out.append(f"  date_added: {paper['date_added']}")
    return out


def record_entry(rec: dict) -> list[str]:
    """One `records/*.yaml` block for a newly admitted entity."""
    out = [f"- entity_id: {rec['entity_id']}",
           f"  type: {rec['type']}",
           f"  name: {_scalar(rec['name'])}"]
    if rec.get("year"):
        out.append(f"  year: {rec['year']}")
    if rec.get("fate_axis"):
        out.append(f"  fate_axis: [{', '.join(rec['fate_axis'])}]")
    out += [f"  review_state: {rec['review_state']}",
            f"  curator: {rec['curator']}",
            f"  date_added: {rec['date_added']}",
            f"  date_updated: {rec['date_updated']}",
            "  papers:"]
    for paper in rec["papers"]:
        out += join_entry(paper, indent=4)
    return out


def join_entry(row: dict, indent: int) -> list[str]:
    pad = " " * indent
    out = [f"{pad}- paper_id: {_scalar(row['paper_id'])}",
           f"{pad}  role: {row['role']}"]
    if row.get("note"):
        folded = _folded(row["note"], indent + 4)
        out.append(f"{pad}  note: {folded[0]}")
        out += folded[1:]
    return out


# ══ Record file surgery ══════════════════════════════════════════════════════

def append_join_rows(path: Path, by_entity: dict[str, list[dict]]) -> None:
    """
    Append rows to each named record's `papers:` sequence, in place.

    Text surgery, not a YAML round-trip: records/*.yaml carries the curation
    commentary -- file headers, `>` descriptions, FLAG comments on unverified
    fields -- and safe_dump would silently delete all of it and reflow
    everything else into one unreadable diff.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    # Latest first, so an insertion never moves an index not yet used.
    found = {}
    for i, line in enumerate(lines):
        m = re.match(r"^- entity_id: (\S+)\s*$", line)
        if m and m.group(1) in by_entity:
            found[m.group(1)] = i
    missing = set(by_entity) - set(found)
    if missing:
        raise Fail(f"{path.name}: no `- entity_id:` line for "
                   f"{', '.join(sorted(missing))}")

    for entity in sorted(found, key=lambda e: -found[e]):
        start = found[entity]
        end = next((j for j in range(start + 1, len(lines))
                    if lines[j].startswith("- ")), len(lines))
        papers = next((j for j in range(start, end)
                       if lines[j].rstrip() == "  papers:"), None)
        rows = [r for row in by_entity[entity]
                for r in join_entry(row, indent=4)]
        if papers is None:
            at = end
            while at > start and not lines[at - 1].strip():
                at -= 1
            rows = ["  papers:"] + rows
        else:
            at = papers + 1
            while at < end and (not lines[at].strip()
                                or lines[at].startswith("    ")):
                at += 1
            while at > papers + 1 and not lines[at - 1].strip():
                at -= 1
        lines[at:at] = rows
    path.write_text("\n".join(lines), encoding="utf-8", newline="")


def append_blocks(path: Path, blocks: list[list[str]]) -> None:
    """Append whole YAML blocks to the end of a curated file."""
    text = path.read_text(encoding="utf-8").rstrip("\n")
    for block in blocks:
        text += "\n\n" + "\n".join(block)
    path.write_text(text + "\n", encoding="utf-8", newline="")


# ══ Candidate -> record ══════════════════════════════════════════════════════

def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


def entity_name(candidate: dict, notes: str) -> str:
    """
    The resource's name, which is the one thing a paper title does not state.

    `name:` in the notes wins. Otherwise the text before the first colon, which
    is where a tool paper conventionally puts the tool -- "VariantFormer: A
    hierarchical transformer ..." -- and only when it is short enough to be a
    name rather than the first clause of a sentence. Failing that, the whole
    title, which is wrong but visibly wrong, and `review_state: unreviewed`
    keeps it off the site until someone fixes it.
    """
    named = note_field(notes, "name")
    if named:
        return named
    head = candidate["title"].split(":", 1)[0].strip()
    if head != candidate["title"].strip() and len(head.split()) <= 5:
        return head
    return candidate["title"].strip()


def discovery_paper(candidate: dict, today: str) -> dict:
    return {
        "paper_id": candidate["paper_id"],
        "doi": candidate.get("doi"),
        "title": candidate["title"],
        "authors": candidate.get("authors"),
        "year": candidate.get("year"),
        "venue": candidate.get("venue"),
        "venue_type": candidate.get("venue_type"),
        "abstract": candidate.get("abstract"),
        "url": (f"https://doi.org/{candidate['doi']}"
                if candidate.get("doi") else None),
        "metadata_source": candidate["source"],
        "date_added": today,
    }


def citing_paper(candidate: dict, today: str) -> dict:
    return {
        "paper_id": candidate["doi"],
        "doi": candidate["doi"],
        "title": candidate.get("title"),
        "authors": candidate.get("authors"),
        "year": candidate.get("year"),
        "venue": candidate.get("venue"),
        "venue_type": OA_VENUE_TYPE.get(candidate.get("oa_type") or ""),
        "abstract": candidate.get("abstract"),
        "url": f"https://doi.org/{candidate['doi']}",
        "metadata_source": "openalex",
        "date_added": today,
    }


# ══ Main ═════════════════════════════════════════════════════════════════════

def latest_review() -> Path:
    files = sorted(f for f in REVIEWS_DIR.glob("review_*.md")
                   if re.fullmatch(r"review_\d{4}-\d{2}-\d{2}", f.stem))
    if not files:
        raise SystemExit("no review file; run literature/02_triage.py first")
    return files[-1]


def default_curator(homes: dict) -> str:
    """
    Whoever curates this catalogue, read off the catalogue.

    Not a constant: a curator identity belongs in `records/`, which is the
    bibliographic metadata, and not in a second copy inside a script.
    """
    from collections import Counter
    names = Counter()
    for path in sorted(set(homes.values())):
        for rec in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            if rec.get("curator"):
                names[rec["curator"]] += 1
    if not names:
        raise Fail("no record carries a `curator`; pass --curator")
    return names.most_common(1)[0][0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--review", default=None,
                    help="review file (default: the most recent)")
    ap.add_argument("--candidates", default=None,
                    help="candidates JSON (default: the one the review names)")
    ap.add_argument("--curator", default=None,
                    help="curator for new records (default: the catalogue's)")
    args = ap.parse_args()

    today = date.today().isoformat()
    review = Path(args.review).resolve() if args.review else latest_review()

    try:
        source, blocks = parse_review(review)
    except Fail as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"reading {review.name}: {len(blocks)} blocks")

    cand_path = (Path(args.candidates).resolve() if args.candidates
                 else (ROOT / source))
    if not cand_path.exists():
        print(f"error: {cand_path} not found. literature/candidates/ is "
              f"git-ignored, so the metadata behind a review file does not "
              f"survive a fresh clone; re-run literature/01_search.py, or "
              f"pass --candidates.", file=sys.stderr)
        return 1
    data = json.loads(cand_path.read_text(encoding="utf-8"))

    discovery = {(c.get("paper_id") or c.get("europepmc_id")): c
                 for c in data["discovery"]}
    citing_by_oa: dict[str, dict] = {}
    for c in data["citing"]:
        citing_by_oa.setdefault(c["openalex_id"], c)

    homes, has_primary, joined = read_records()
    known_papers = read_papers()
    decided = rules.read_decisions()
    curator = args.curator or default_curator(homes)

    errors: list[str] = []
    ledger: dict[str, dict] = {}
    new_papers: dict[str, dict] = {}
    new_records: dict[str, dict] = {}          # entity_id -> record
    new_joins: dict[str, list[dict]] = {}      # entity_id -> rows
    counts = {k: 0 for k in ("accepted", "promoted", "recorded", "rejected",
                             "deferred", "vetoed", "pending", "unclear",
                             "already")}

    def note(key: str, block: dict, verdict: str, **extra) -> list:
        # The title's whitespace is collapsed because yaml.safe_dump folds a
        # long scalar and the fold reads back joined by single spaces: two
        # Europe PMC titles in this run carry a double space, and without this
        # they would differ from themselves on every run forever.
        entry = {"decision": verdict, "date": today, "score": block["score"],
                 "list": block["section"],
                 "title": " ".join(block["title"].split()), **extra}
        if prose(block["notes"]):
            entry["reason"] = prose(block["notes"])
        # One paper can carry several decisions -- it reaches discovery as a
        # candidate and list A as a role proposal for two different entities,
        # which really happens in this run -- so a paper's value is a list and
        # a decision is appended to it. A scalar here dropped the earlier
        # decision on the floor, which is the one thing the ledger exists to
        # prevent.
        #
        # An unchanged decision keeps the date it was first made. A curator
        # works through several hundred candidates over several sittings and
        # re-runs this script each time, so most decisions are re-read on
        # every run; restamping them would turn the ledger's date from "when
        # this was decided" into "when it was last re-read".
        entries = ledger.setdefault(key, list(decided.get(key) or []))
        bare = {k: v for k, v in entry.items() if k != "date"}
        for existing in entries:
            if {k: v for k, v in existing.items() if k != "date"} == bare:
                return entries
        entries.append(entry)
        return entries

    for block in blocks:
        try:
            got = classify(block)
        except Fail as exc:
            errors.append(str(exc))
            continue
        verdict, role = got["verdict"], got.get("role")

        # ── discovery ────────────────────────────────────────────────────────
        if block["section"] == "discovery":
            ident = meta_value(block, RE_ID)
            candidate = discovery.get(ident)
            if candidate is None:
                errors.append(f"line {block['line']}: id `{ident}` is not in "
                              f"{cand_path.name}")
                continue
            key = rules.ledger_key(candidate)
            if verdict == "pending":
                counts["pending"] += 1
                continue
            if verdict in ("rejected", "deferred"):
                counts[verdict] += 1
                note(key, block, verdict)
                continue

            # accepted or promoted: a new entity record.
            if not candidate.get("paper_id"):
                errors.append(
                    f"line {block['line']}: accepted, but the candidate has no "
                    f"DOI -- only `{candidate.get('europepmc_id')}`. "
                    f"schema.py keys a paper on a DOI or an `arxiv:` id, so "
                    f"this one needs its DOI found by hand and added to "
                    f"literature/papers.yaml")
                continue
            etype = candidate["expect_type"]
            if etype not in RECORD_FILES:
                errors.append(f"line {block['line']}: expect_type "
                              f"'{etype}' is not an entity type")
                continue
            name = entity_name(candidate, block["notes"])
            entity_id = f"{etype}:{slugify(name)}"
            if any(d.get("entity_id") == entity_id
                   for d in decided.get(key) or []):
                # Already admitted by an earlier run over this review file,
                # which is the normal case: a curator ticks a few more
                # candidates each sitting and runs this script again.
                counts["already"] += 1
                continue
            if entity_id in homes or entity_id in new_records:
                errors.append(
                    f"line {block['line']}: `{entity_id}` already exists. "
                    f"Name the entity in the **Notes:** line "
                    f"(`name: <name>`) if this is a different resource, or "
                    f"reject the candidate as a duplicate")
                continue
            new_records[entity_id] = {
                "entity_id": entity_id, "type": etype, "name": name,
                "year": candidate.get("year"),
                "fate_axis": ([candidate["fate_axis"]]
                              if candidate.get("fate_axis") else None),
                "review_state": "unreviewed", "curator": curator,
                "date_added": today, "date_updated": today,
                "papers": [{"paper_id": candidate["paper_id"],
                            "role": "primary"}],
            }
            if candidate["paper_id"] not in known_papers:
                new_papers[candidate["paper_id"]] = discovery_paper(candidate,
                                                                    today)
            counts[verdict] += 1
            note(key, block, verdict, entity_id=entity_id)
            continue

        # ── list A and list B: a role proposal ───────────────────────────────
        oa = meta_value(block, RE_OPENALEX)
        candidate = citing_by_oa.get(oa)
        if candidate is None:
            errors.append(f"line {block['line']}: openalex id `{oa}` is not "
                          f"in {cand_path.name}")
            continue
        key = rules.ledger_key(candidate)
        if verdict == "pending":
            counts["pending"] += 1
            continue
        if verdict in ("rejected", "vetoed"):
            counts[verdict] += 1
            note(key, block, verdict, role=role)
            continue

        if block["section"] == "A":
            targets = [block["entity"]] if block["entity"] else []
            if not targets:
                errors.append(f"line {block['line']}: list A block is not "
                              f"under an entity heading")
                continue
        elif got.get("targets"):
            targets = got["targets"]
        else:
            # The vetoable list B shape says "for the entities above", which is
            # the catalogued primaries the paper cites -- narrowed to the ones
            # that actually carry a primary paper, since those are the only
            # tiers a role row can reach.
            cited = RE_BACKTICKED.findall(
                meta_value(block, RE_PRIMARIES) or "")
            targets = [e for e in cited if has_primary.get(e)]
            if not targets:
                errors.append(f"line {block['line']}: recorded for \"the "
                              f"entities above\", but none of the cited "
                              f"primaries is a catalogued entity with a "
                              f"primary paper")
                continue

        if role not in rules.PAPER_ROLES:
            if role == "unclear" and verdict == "recorded":
                # 02_triage proposes `unclear` when neither lexicon fires. It
                # is not an entity_paper role, and guessing one here would be
                # this script deciding what a paper does. Recorded in the
                # ledger so the next cycle can see it was seen.
                counts["unclear"] += 1
                note(key, block, "needs-role", role=None, entities=targets)
                continue
            errors.append(
                f"line {block['line']}: role '{role}' is not one of "
                f"{', '.join(rules.PAPER_ROLES)}")
            continue
        if not candidate.get("doi"):
            errors.append(
                f"line {block['line']}: accepted, but the candidate carries no "
                f"DOI -- only `{oa}`. schema.py keys a paper on a DOI or an "
                f"`arxiv:` id, so this one needs its DOI added by hand")
            continue

        paper_id = candidate["doi"]
        attached = []
        for entity in targets:
            if entity not in homes:
                errors.append(f"line {block['line']}: `{entity}` is not a "
                              f"catalogued entity")
                continue
            if (entity, paper_id, role) in joined:
                counts["already"] += 1
                continue
            new_joins.setdefault(entity, []).append(
                {"paper_id": paper_id, "role": role,
                 "note": prose(block["notes"]) or None})
            joined.add((entity, paper_id, role))
            attached.append(entity)
        if attached and paper_id not in known_papers:
            new_papers[paper_id] = citing_paper(candidate, today)
        if attached:
            counts[verdict] += 1
            note(key, block, verdict, role=role, entities=attached)

    if errors:
        print(f"\n{len(errors)} unreadable decision(s); nothing written:",
              file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    # ── write ────────────────────────────────────────────────────────────────
    by_file: dict[Path, dict] = {}
    for entity, rows in new_joins.items():
        by_file.setdefault(homes[entity], {})[entity] = rows
    for path, grouped in sorted(by_file.items()):
        append_join_rows(path, grouped)

    added_records: dict[Path, list] = {}
    for rec in new_records.values():
        path = RECORDS_DIR / RECORD_FILES[rec["type"]]
        added_records.setdefault(path, []).append(record_entry(rec))
    for path, entries in sorted(added_records.items()):
        append_blocks(path, entries)

    if new_papers:
        append_blocks(PAPERS_YAML,
                      [paper_entry(p) for p in new_papers.values()])

    # Only the papers whose decision list actually changed, so a re-run over a
    # review file a curator has added two ticks to writes two entries.
    changed = {k: v for k, v in ledger.items() if (decided.get(k) or []) != v}
    if changed:
        rules.write_decisions(changed)

    print(f"  new records           {len(new_records)}"
          f" ({', '.join(sorted(new_records)) or '—'})")
    print(f"  new join rows         "
          f"{sum(len(v) for v in new_joins.values())}")
    print(f"  new papers            {len(new_papers)}")
    print(f"  ledger entries        {len(changed)}")
    for key in ("accepted", "promoted", "recorded", "rejected", "deferred",
                "vetoed", "already", "unclear", "pending"):
        print(f"  {key:21} {counts[key]}")
    if counts["unclear"]:
        print(f"  {counts['unclear']} proposal(s) had role `unclear` and were "
              f"recorded in the ledger as needs-role, not attached")
    if new_records:
        print("next: python scripts/04_build.py && "
              "python scripts/05_validate.py")
        print("      new records are `unreviewed`, so 07_export_site.py holds "
              "them off the site until a human clears them")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fail as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
