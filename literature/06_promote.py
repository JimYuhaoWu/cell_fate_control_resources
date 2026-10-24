#!/usr/bin/env python
"""
literature/06_promote.py
------------------------
Move a staged record onto the site. Writes `literature/promotions/
promote_YYYY-MM-DD.md` for a human to work, and `--apply` reads it back.

`03_record.py` admits a candidate as `review_state: unreviewed`: the record is
in `records/`, QC checks it, and `07_export_site.py` holds it off the site.
That is the only safe thing to do with a bulk accept, and it means the staging
area now holds far more than the catalogue. This script is how a record leaves
staging.

**Nothing here rejects anything, and that is the design.** `02_triage.py`
filters every future review file against the ledger, and only `rejected` is
suppressed -- a rejection is permanent, while a record left staged costs a row
in `db/` and nothing else. Measured on the 2026-10-21 cycle: a rule that
discarded staged records with no name in the title would have thrown away
roughly 45 named resources out of 283, because a title like "CAPRA predicts
single-cell transcriptional responses…" names its model without the colon the
slug rule looks for. So the file has two decisions, `promote` and
`leave staged`, and the second is the default that happens by doing nothing.

The ordering is a convenience and not a filter. Every staged record is in the
file; the ones whose paper appears to name something are listed first and in
full, the rest compactly, and no record is left out of either.

One refusal: a record whose `entity_id` is still slugged from its title cannot
be promoted without a name. `03_record.py` falls back to the title when no
model name is in it, which is visibly wrong on purpose -- one such id is 243
characters -- and publishing that is worse than leaving the record staged.
Write `name: <name>` in the **Notes:** line and the record is renamed as it is
promoted.

Run from project root:
    python literature/06_promote.py                 # write the file
    python literature/06_promote.py --apply         # read it back
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RECORDS_DIR = ROOT / "records"
PROMOTIONS_DIR = ROOT / "literature" / "promotions"

# Whether a record is named is decided by comparing its name with its paper's
# title, not by how long the id is. Slug length was a proxy for that question
# and a poor one: it missed a resource named in prose rather than before a
# colon -- CAPRA, trVAE -- and it now misreads a citation name
# ("Kelley 2018 sequential regulatory activity", 44 characters) as a title.


def _module(filename: str, name: str):
    """03_record.py starts with a digit, so it is not importable by name."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "literature" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


record = _module("03_record.py", "cfcr_record")

BOX = r"\[([ xX])\]"
DECISION = re.compile(rf"^\*\*Decision:\*\* `{BOX} promote` / `{BOX} leave staged`$")
HEADING = re.compile(r"^#### `([^`]+)`")


def _rel(path: Path) -> str:
    """Repo-relative and forward-slashed, so the file reads the same on both."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def staged() -> list[dict]:
    """Every `unreviewed` record, with the file and line its block starts on."""
    out = []
    for path in sorted(RECORDS_DIR.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        starts = {}
        for n, line in enumerate(text.split("\n"), 1):
            m = re.match(r"^- entity_id: (\S+)", line)
            if m:
                starts[m.group(1)] = n
        for rec in yaml.safe_load(text) or []:
            if rec.get("review_state") == "unreviewed":
                out.append({"rec": rec, "path": path,
                            "line": starts.get(rec["entity_id"])})
    return out


def primary_titles() -> dict[str, str]:
    """entity_id -> the title of its `primary` paper, normalised."""
    papers = {p["paper_id"]: p for p in yaml.safe_load(
        (ROOT / "literature" / "papers.yaml").read_text(encoding="utf-8")) or []}
    out = {}
    for item in staged():
        rec = item["rec"]
        pid = next((p["paper_id"] for p in rec.get("papers") or []
                    if p["role"] == "primary"), None)
        title = (papers.get(pid) or {}).get("title") or ""
        out[rec["entity_id"]] = " ".join(title.lower().split())
    return out


def is_named(rec: dict, titles: dict[str, str]) -> bool:
    """
    True when the record's name is something other than its paper's title.

    A record whose name *is* the title is one 03_record.py could find no name
    in, and publishing it puts a sentence where a resource's name belongs.
    Anything else -- a real name, or the citation that script now falls back to
    -- is a name a card can carry.
    """
    name = " ".join(str(rec.get("name") or "").lower().split())
    return bool(name) and name != titles.get(rec["entity_id"], "")


def block(item: dict, papers: dict) -> list[str]:
    """One full block, for a record whose paper looks to have named something."""
    rec = item["rec"]
    primary = next((p["paper_id"] for p in rec.get("papers") or []
                    if p["role"] == "primary"), None)
    paper = papers.get(primary, {})
    lines = [f"#### `{rec['entity_id']}`",
             "",
             f"- **name:** {rec.get('name')}",
             f"- **type:** `{rec['type']}`"
             + (f"  **fate_axis:** {', '.join(rec['fate_axis'])}"
                if rec.get("fate_axis") else "")
             + (f"  **year:** {rec['year']}" if rec.get("year") else ""),
             f"- **primary:** `{primary}`"
             + (f"  {paper.get('venue')}" if paper.get("venue") else ""),
             f"- **in:** `{_rel(item['path'])}`"
             + (f" line {item['line']}" if item["line"] else ""),
             ""]
    if paper.get("abstract"):
        lines += ["> " + paper["abstract"][:400].replace("\n", " ") + "…", ""]
    # The hint for **Notes:** lives in the section intro rather than on every
    # block: repeated 179 times it is noise, and a hint that itself spells a
    # `name:` directive is a placeholder waiting to be read as a real one.
    lines += ["**Decision:** `[ ] promote` / `[ ] leave staged`",
              "**Notes:**",
              "", "---", ""]
    return lines


def write_file(out: Path) -> int:
    papers = {p["paper_id"]: p for p
              in yaml.safe_load((ROOT / "literature" / "papers.yaml")
                                .read_text(encoding="utf-8")) or []}
    items = staged()
    titles = primary_titles()
    named = [i for i in items if is_named(i["rec"], titles)]
    titled = [i for i in items if not is_named(i["rec"], titles)]

    lines = [f"# Staging review — {date.today().isoformat()}",
             "",
             f"{len(items)} record(s) are `review_state: unreviewed`: in "
             f"`records/` and in `db/`, held off the site by "
             f"`scripts/07_export_site.py`. Tick `promote` to publish one, then "
             f"run `python literature/06_promote.py --apply`.",
             "",
             "**Nothing in this file rejects anything.** Leaving a record "
             "staged is free and reversible; a rejection in "
             "`literature/decisions.yaml` is permanent, because `02_triage.py` "
             "filters every later cycle against it. So the second box says "
             "`leave staged`, and doing nothing at all has the same effect.",
             "",
             "The two sections are an ordering, not a filter. Every staged "
             "record is here.",
             "", "---", "",
             f"## Carries a name ({len(named)})",
             "",
             "Its name is something other than its paper's title: either a "
             "resource name `03_record.py` found, or the citation it falls "
             "back to for a paper that named nothing "
             "(\"Kelley 2018 sequential regulatory activity\"). Both are "
             "names a card can carry, so both can be promoted as they "
             "stand.",
             "",
             "Write `name: <the name>` on a block's **Notes:** line to rename "
             "the record as it is promoted. A record whose id is slugged from "
             "its title cannot be promoted without one.",
             ""]
    for item in sorted(named, key=lambda i: i["rec"]["entity_id"]):
        lines += block(item, papers)

    lines += [f"## Still named after the paper's title ({len(titled)})",
              "",
              "Listed compactly because promoting one needs a `name:` first. "
              "Full blocks are above; to promote one of these, add it there by "
              "hand or write its own block in the same shape.",
              ""]
    for item in sorted(titled, key=lambda i: i["rec"]["entity_id"]):
        rec = item["rec"]
        lines.append(f"- `{rec['entity_id']}` — {rec.get('name')}")
    lines.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8", newline="")
    print(f"wrote {_rel(out)}: {len(items)} staged, {len(named)} named, "
          f"{len(titled)} title-slugged")
    return 0


def parse(path: Path) -> list[dict]:
    """(entity_id, promote?, name override) for every block carrying a tick."""
    out, current, pending = [], None, None
    for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        m = HEADING.match(line)
        if m:
            current, pending = m.group(1), None
            continue
        # The **Notes:** line sits *below* its decision in every block, so a
        # ticked decision waits for it rather than reading the one above.
        if line.startswith("**Notes:**") and pending is not None:
            name = record.note_field(line[len("**Notes:**"):], "name")
            # A `<…>` reads as a placeholder somebody did not fill in, never a
            # name, and a record is left staged rather than published under one.
            pending["name"] = None if (name or "").startswith("<") else name
            pending = None
            continue
        m = DECISION.match(line)
        if not m:
            continue
        yes, no = m.group(1).strip().lower() == "x", m.group(2).strip().lower() == "x"
        if yes and no:
            raise SystemExit(f"line {n}: both boxes are ticked for {current}")
        if yes:
            pending = {"entity_id": current, "name": None, "line": n}
            out.append(pending)
    return out


def promote(path: Path, decisions: list[dict]) -> int:
    """
    Edit the record's own lines rather than re-dumping the file: `records/*.yaml`
    is hand-formatted and carries comments that a yaml dumper would discard.
    """
    by_file: dict[Path, list[dict]] = {}
    index = {i["rec"]["entity_id"]: i for i in staged()}
    titles = primary_titles()
    errors = []
    for decision in decisions:
        item = index.get(decision["entity_id"])
        if not item:
            errors.append(f"line {decision['line']}: `{decision['entity_id']}` "
                          f"is not a staged record")
            continue
        if not is_named(item["rec"], titles) and not decision["name"]:
            errors.append(f"line {decision['line']}: `{decision['entity_id']}` "
                          f"is slugged from its title. Write `name: <name>` in "
                          f"the **Notes:** line, or leave it staged")
            continue
        by_file.setdefault(item["path"], []).append(dict(decision, item=item))

    if errors:
        print(f"{len(errors)} unusable decision(s); nothing written:")
        for line in errors:
            print(f"  {line}")
        return 1

    promoted = renamed = 0
    for path_, group in sorted(by_file.items()):
        lines = path_.read_text(encoding="utf-8").split("\n")
        for decision in group:
            old_id = decision["entity_id"]
            start = next(i for i, line in enumerate(lines)
                         if line == f"- entity_id: {old_id}")
            end = next((i for i in range(start + 1, len(lines))
                        if lines[i].startswith("- ")), len(lines))
            new_id = old_id
            if decision["name"]:
                etype = old_id.split(":", 1)[0]
                new_id = f"{etype}:{record.slugify(decision['name'])}"
                lines[start] = f"- entity_id: {new_id}"
            kept = []
            for i in range(start + 1, end):
                line = lines[i]
                # The promotion itself: `upsert_entities` defaults a missing
                # `review_state` to `reviewed`, so the line goes rather than
                # being rewritten, and the record reads like a curated one.
                if line.strip() == "review_state: unreviewed":
                    continue
                if decision["name"] and re.match(r"^  name: ", line):
                    line = f"  name: {record._scalar(decision['name'])}"
                kept.append(line)
            lines[start + 1:end] = kept
            promoted += 1
            renamed += new_id != old_id
            print(f"  promoted {new_id}"
                  + (f" (was `{old_id}`)" if new_id != old_id else ""))
        path_.write_text("\n".join(lines), encoding="utf-8", newline="")

    print(f"  promoted              {promoted}")
    if renamed:
        # scripts/schema.py creates its tables `IF NOT EXISTS` and upserts into
        # them, so db/cfcr.db never loses a row that left records/*.yaml. A
        # rename therefore leaves the old entity_id behind in the snapshots,
        # still `reviewed`, and 07_export_site.py puts that ghost on the site.
        # The database is derived and gitignored, so deleting it is the whole
        # fix here; making the build drop what records/ no longer has is a
        # change to 04_build.py and is not made from this script.
        print(f"  {renamed} record(s) were renamed, so db/cfcr.db now holds "
              f"the id(s) they had before.")
        print("next: rm db/cfcr.db && python scripts/04_build.py "
              "&& python scripts/05_validate.py && python scripts/07_export_site.py")
    elif promoted:
        print("next: python scripts/04_build.py && python scripts/05_validate.py "
              "&& python scripts/07_export_site.py")
    return 0


def latest() -> Path:
    files = sorted(PROMOTIONS_DIR.glob("promote_*.md"))
    if not files:
        raise SystemExit("no promotion file; run without --apply first")
    return files[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="read a worked file back and promote its ticks")
    parser.add_argument("--file")
    args = parser.parse_args()

    if not args.apply:
        out = Path(args.file) if args.file else (
            PROMOTIONS_DIR / f"promote_{date.today().isoformat()}.md")
        if out.exists():
            raise SystemExit(f"{_rel(out)} already exists; it may carry "
                             f"decisions. Move it aside or pass --file")
        return write_file(out)

    path = Path(args.file) if args.file else latest()
    decisions = parse(path)
    print(f"reading {_rel(path)}: {len(decisions)} promotion(s)")
    if not decisions:
        return 0
    return promote(path, decisions)


if __name__ == "__main__":
    sys.exit(main())
