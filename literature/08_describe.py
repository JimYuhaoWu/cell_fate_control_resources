#!/usr/bin/env python
"""
literature/08_describe.py
-------------------------
Give a record the one-line description its card is missing, taken from the
sentence in which its own paper says what it built.

197 published entities have no description, and a card without one shows a
name, a type and a year. A description cannot be invented, but it does not have
to be: an abstract almost always contains "Here we present X, a …", and that
sentence is the paper's own account of the resource, publisher-released like
the rest of the abstract already in `literature/papers.yaml`.

    description     the `we present/introduce/describe/propose/report`
                    sentence of the primary abstract, cleaned of markup

What it refuses to do matters as much:

  A sentence that does not come out whole is **skipped, not trimmed.** An
  abstract broken at "i.e." or at an initial yields half a thought, and half a
  description on a card is worse than none -- it reads as though a human wrote
  it badly. Bounds on length do the same job: a 20-character match is not a
  description and a 400-character one is a paragraph.

  An existing description is never touched, so the hand-written twenty stay
  exactly as curated.

  `tags` are still not generated, for the reason they never were: a tag becomes
  vocabulary once ten records share it, and a generator filling that column
  would make the vocabulary mechanism measure the generator.

Every record it writes is listed in `reports/described.tsv`. A description
drawn from an abstract sits in the same column as one a curator wrote, with
nothing in the schema to tell them apart, so the audit trail is that file and
this script's own output rather than a marker inside the text.

Run from project root:
    python literature/08_describe.py [--dry-run] [--limit N] [--staged]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RECORDS_DIR = ROOT / "records"
PAPERS_YAML = ROOT / "literature" / "papers.yaml"

MIN_LEN, MAX_LEN = 60, 320

# Europe PMC returns structured abstracts with the section headings inline.
TAGS = re.compile(r"<[^>]+>")

CLAIM = re.compile(
    r"^(?:here(?:in)?[,:]?\s+)?we\s+"
    r"(?:present|introduce|describe|propose|report|develop(?:ed)?|"
    r"build|built)\b", re.I)

# Full stops that do not end a sentence. Split on the rest. Without this an
# abstract breaks at "i.e." or at an author's initial and the extraction is a
# fragment -- which is the one outcome worse than no description at all.
ABBREV = re.compile(
    r"\b(?:e\.g|i\.e|et\sal|vs|cf|approx|ca|Fig|Figs|Eq|Ref|Refs|No|Dr|Prof|"
    r"St|Inc|Ltd|Jr|Sr|[A-Z])\.", re.I)
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
HOLD = "\x00"


def sentences(text: str) -> list[str]:
    """Sentence split with abbreviations held out of the way."""
    kept: list[str] = []

    def stash(match: re.Match) -> str:
        kept.append(match.group(0))
        return HOLD + str(len(kept) - 1) + HOLD

    masked = ABBREV.sub(stash, text)
    out = []
    for part in SPLIT.split(masked):
        for i, original in enumerate(kept):
            part = part.replace(f"{HOLD}{i}{HOLD}", original)
        out.append(part.strip())
    return out


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def claim_sentence(abstract: str) -> str | None:
    """
    The sentence in which the authors say what they made, or None.

    Returned whole or not at all. The lookbehinds keep the match from ending on
    an abbreviation's full stop -- "i.e.", "et al.", a bare initial -- which is
    what turns an extraction into a fragment.
    """
    text = " ".join(TAGS.sub(" ", abstract or "").split())
    for sentence in sentences(text):
        if not CLAIM.match(sentence):
            continue
        if not sentence.endswith("."):
            continue                      # cut by the abstract's own truncation
        if not MIN_LEN <= len(sentence) <= MAX_LEN:
            continue
        return sentence[0].upper() + sentence[1:]
    return None


def fold(value: str, indent: int) -> list[str]:
    """
    A folded scalar in the style records/*.yaml already uses, so a description
    diffs as prose rather than as one very long line.
    """
    pad = " " * indent
    words, lines, row = value.split(), [">-"], ""
    for word in words:
        if row and len(row) + len(word) + 1 > 74:
            lines.append(pad + row)
            row = word
        else:
            row = f"{row} {word}".strip()
    if row:
        lines.append(pad + row)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--staged", action="store_true",
                        help="also describe records still held off the site")
    args = parser.parse_args()

    papers = {p["paper_id"]: p for p
              in yaml.safe_load(PAPERS_YAML.read_text(encoding="utf-8")) or []}

    considered = written = 0
    no_claim: list[str] = []
    rows: list[str] = []

    for path in sorted(RECORDS_DIR.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        changed = False

        for rec in yaml.safe_load(text) or []:
            if rec.get("description"):
                continue
            if rec.get("review_state") == "withdrawn":
                # Never, not even with --staged: a withdrawn record is off the
                # site for good, and a description is written for a card.
                continue
            if rec.get("review_state") == "unreviewed" and not args.staged:
                continue
            if args.limit and considered >= args.limit:
                break
            considered += 1

            primary = next((p["paper_id"] for p in rec.get("papers") or []
                            if p["role"] == "primary"), None)
            sentence = claim_sentence((papers.get(primary) or {}).get("abstract"))
            if not sentence:
                no_claim.append(rec["entity_id"])
                continue

            print(f"  {rec['entity_id'][:44]:44s} {sentence[:86]}")
            rows.append(f"{rec['entity_id']}\t{primary}\t{sentence}")
            written += 1
            if args.dry_run:
                continue

            start = lines.index(f"- entity_id: {rec['entity_id']}")
            end = next((i for i in range(start + 1, len(lines))
                        if lines[i].startswith("- ")), len(lines))
            at = next((i for i in range(start, end)
                       if lines[i] == "  papers:"), end)
            block = fold(sentence, 4)
            lines[at:at] = [f"  description: {block[0]}"] + block[1:]
            changed = True

        if changed and not args.dry_run:
            path.write_text("\n".join(lines), encoding="utf-8", newline="")

    print(f"\n  records with no description       {considered}")
    print(f"  described from the abstract       {written}")
    print(f"  no usable claim sentence          {len(no_claim)}")

    if rows and not args.dry_run:
        out = ROOT / "reports" / "described.tsv"
        header = "entity_id\tprimary_paper\tdescription_taken_from_the_abstract"
        existing = {}
        if out.exists():
            for line in out.read_text(encoding="utf-8").split("\n")[1:]:
                if line.strip():
                    existing[line.split("\t", 1)[0]] = line
        for row in rows:
            existing[row.split("\t", 1)[0]] = row
        out.write_text(header + "\n"
                       + "\n".join(v for _, v in sorted(existing.items())) + "\n",
                       encoding="utf-8", newline="")
        print(f"  wrote {_rel(out)} -- which cards these came from")
    if written:
        print("next: python scripts/04_build.py && python scripts/05_validate.py "
              "&& python scripts/07_export_site.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
