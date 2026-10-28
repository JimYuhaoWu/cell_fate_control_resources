#!/usr/bin/env python
"""
literature/09_demote.py
-----------------------
Take a published record off the site. Writes `literature/demotions/
demote_YYYY-MM-DD.md` for a human to work, and `--apply` reads it back.

The mirror of 06_promote.py, and the missing half of M4a. Promotion deletes a
record's `review_state: unreviewed` line; until now there was no way back
except editing one in by hand, which is how the catalogue came to hold 170
records that `docs/scope_criteria.md` says do not belong in it.

**A demotion is not a return to staging.** `unreviewed` means nobody has looked
yet, and 06_promote.py collects every one of those into the queue of records
awaiting a decision. Demoting an out-of-scope record there would park it in
that queue for good. So a demoted record gets `review_state: withdrawn` and a
`withdrawn_reason`, which `scripts/07_export_site.py` already holds off the
site -- it publishes `reviewed` and nothing else -- and which 06_promote.py
never offers for promotion, because it looks for `unreviewed`.

**Nothing here deletes anything.** The record stays in `records/`, in `db/` and
in the committed snapshots, with the criterion that took it off the site
written beside it. That is what makes the decision reviewable later, and what
lets a curator who disagrees restore it by deleting two lines. A withdrawal
also writes a `rejected` entry into `literature/decisions.yaml` against the
record's primary paper, because without one the next discovery cycle proposes
that paper again -- and 03_record.py's refusal to reuse an existing
`entity_id` does not help when the new slug differs, which is how
`model:grover-2025-early-feature-extraction` and
`model:grover-2026-early-feature-extraction` both exist.

The file is written from `literature/scope_labels.yaml`: every published record
that labels as out of scope, the `clear` ones first and the `arguable` ones
after, each carrying the criterion it failed. Those labels are a measurement,
not a decision -- the default here is `keep`, and doing nothing keeps
everything.

Run from project root:
    python literature/09_demote.py                  # write the file
    python literature/09_demote.py --apply          # read it back
    python literature/09_demote.py --apply --dry-run
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
DEMOTIONS_DIR = ROOT / "literature" / "demotions"
LABELS_FILE = ROOT / "literature" / "scope_labels.yaml"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage_rules as rules                        # noqa: E402


def _module(filename: str, name: str):
    """03_record.py starts with a digit, so it is not importable by name."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "literature" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


record = _module("03_record.py", "cfcr_record")

BOX = r"\[([ xX])\]"
DECISION = re.compile(rf"^\*\*Decision:\*\* `{BOX} withdraw` / `{BOX} keep`$")
HEADING = re.compile(r"^#### `([^`]+)`")


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def published() -> dict[str, dict]:
    """
    Every record that is on the site, with the file and line its block starts on.

    On the site means `review_state` absent: schema.py defaults a missing one to
    `reviewed`, which is what promotion leaves behind. A record already
    `withdrawn` or still `unreviewed` is not a candidate for demotion, and
    saying so is how a second --apply over the same file reports nothing to do
    rather than rewriting what it did the first time.
    """
    out = {}
    for path in sorted(RECORDS_DIR.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        starts = {}
        for n, line in enumerate(text.split("\n"), 1):
            m = re.match(r"^- entity_id: (\S+)", line)
            if m:
                starts[m.group(1)] = n
        for rec in yaml.safe_load(text) or []:
            if (rec.get("review_state") or "reviewed") == "reviewed":
                out[rec["entity_id"]] = {"rec": rec, "path": path,
                                         "line": starts.get(rec["entity_id"])}
    return out


def labels() -> list[dict]:
    """The `out` rows of literature/scope_labels.yaml, in file order."""
    if not LABELS_FILE.exists():
        raise SystemExit(f"{_rel(LABELS_FILE)} does not exist; the file this "
                         f"script writes is built from it")
    loaded = yaml.safe_load(LABELS_FILE.read_text(encoding="utf-8")) or {}
    return [row for row in (loaded.get("labels") or [])
            if row.get("label") == "out"]


def reason_text(row: dict) -> str:
    """`C2: protein contact map prediction` -- the criterion, then why."""
    crit = row.get("failed_criterion")
    return f"{crit}: {row['reason']}" if crit else row["reason"]


def block(row: dict, item: dict) -> list[str]:
    rec = item["rec"]
    primary = next((p["paper_id"] for p in rec.get("papers") or []
                    if p["role"] == "primary"), None)
    return [f"#### `{rec['entity_id']}`",
            "",
            f"- **name:** {rec.get('name')}",
            f"- **type:** `{rec['type']}`"
            + (f"  **fate_axis:** {', '.join(rec['fate_axis'])}"
               if rec.get("fate_axis") else "  **fate_axis:** *(none)*"),
            f"- **failed:** `{row.get('failed_criterion', '-')}` — {row['reason']}",
            f"- **primary:** `{primary}`",
            f"- **in:** `{_rel(item['path'])}`"
            + (f" line {item['line']}" if item["line"] else ""),
            ""]


def write_file(out: Path) -> int:
    on_site = published()
    rows = [r for r in labels() if r["entity_id"] in on_site]
    clear = [r for r in rows if r.get("certainty") == "clear"]
    arguable = [r for r in rows if r.get("certainty") != "clear"]
    skipped = len(labels()) - len(rows)

    lines = [f"# Demotion review — {date.today().isoformat()}",
             "",
             f"{len(rows)} published record(s) are labelled out of scope in "
             f"`literature/scope_labels.yaml`: {len(clear)} `clear` and "
             f"{len(arguable)} `arguable`. Tick `withdraw` to take one off the "
             f"site, then run `python literature/09_demote.py --apply`.",
             ""]
    if skipped:
        lines += [f"{skipped} further labelled-out record(s) are not listed: "
                  f"they are already withdrawn, or still staged, so there is "
                  f"nothing to demote.", ""]
    lines += ["**The default is `keep`, and doing nothing keeps everything.** "
              "A tick sets `review_state: withdrawn` and writes the criterion "
              "into `withdrawn_reason`; the record stays in `records/`, in "
              "`db/` and in the snapshots, and deleting those two lines puts "
              "it back. A tick also records the primary paper as `rejected` in "
              "`literature/decisions.yaml`, without which the next discovery "
              "cycle proposes it again under a new slug.",
              "",
              "Write `reason: <text>` on a block's **Notes:** line to override "
              "the one from the labels.",
              "",
              "The two sections are an ordering, not a filter.",
              "", "---", "",
              f"## Clearly out of scope ({len(clear)})",
              "",
              "The criterion decides these outright.",
              ""]
    for row in sorted(clear, key=lambda r: r["entity_id"]):
        lines += block(row, on_site[row["entity_id"]])
        lines += ["**Decision:** `[ ] withdraw` / `[ ] keep`",
                  "**Notes:**",
                  "", "---", ""]

    lines += [f"## Arguable ({len(arguable)})",
              "",
              "A reasonable curator could read the criterion the other way. "
              "Each one settled is a decision about the boundary itself, not "
              "just about this record, so it is worth saying why in the "
              "**Notes:** line whichever way it goes.",
              ""]
    for row in sorted(arguable, key=lambda r: r["entity_id"]):
        lines += block(row, on_site[row["entity_id"]])
        lines += ["**Decision:** `[ ] withdraw` / `[ ] keep`",
                  "**Notes:**",
                  "", "---", ""]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8", newline="")
    print(f"wrote {_rel(out)}: {len(rows)} published and labelled out "
          f"({len(clear)} clear, {len(arguable)} arguable)")
    return 0


def parse(path: Path) -> list[dict]:
    """(entity_id, reason override) for every block ticked `withdraw`."""
    out, current, pending = [], None, None
    for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        m = HEADING.match(line)
        if m:
            current, pending = m.group(1), None
            continue
        # **Notes:** sits below its decision in every block, so a ticked
        # decision waits for it rather than reading the one above.
        if line.startswith("**Notes:**") and pending is not None:
            reason = record.note_field(line[len("**Notes:**"):], "reason")
            pending["reason"] = None if (reason or "").startswith("<") else reason
            pending = None
            continue
        m = DECISION.match(line)
        if not m:
            continue
        yes, no = m.group(1).strip().lower() == "x", m.group(2).strip().lower() == "x"
        if yes and no:
            raise SystemExit(f"line {n}: both boxes are ticked for {current}")
        if yes:
            pending = {"entity_id": current, "reason": None, "line": n}
            out.append(pending)
    return out


def demote(decisions: list[dict], dry_run: bool) -> int:
    """
    Edit the record's own lines rather than re-dumping the file: `records/*.yaml`
    is hand-formatted and carries comments a yaml dumper would discard.
    """
    on_site = published()
    by_label = {r["entity_id"]: r for r in labels()}
    errors, work = [], {}
    for decision in decisions:
        eid = decision["entity_id"]
        item = on_site.get(eid)
        if not item:
            errors.append(f"line {decision['line']}: `{eid}` is not a "
                          f"published record -- already withdrawn, still "
                          f"staged, or not in records/ at all")
            continue
        reason = decision["reason"] or (
            reason_text(by_label[eid]) if eid in by_label else None)
        if not reason:
            errors.append(f"line {decision['line']}: `{eid}` has no label in "
                          f"scope_labels.yaml, so write `reason: <text>` in "
                          f"its **Notes:** line")
            continue
        work.setdefault(item["path"], []).append(
            dict(decision, item=item, reason=reason))

    if errors:
        print(f"{len(errors)} unusable decision(s); nothing written:")
        for line in errors:
            print(f"  {line}")
        return 1

    withdrawn, ledger = 0, {}
    existing = rules.read_decisions()
    for path_, group in sorted(work.items()):
        lines = path_.read_text(encoding="utf-8").split("\n")
        for decision in group:
            eid = decision["entity_id"]
            rec = decision["item"]["rec"]
            start = next(i for i, line in enumerate(lines)
                         if line == f"- entity_id: {eid}")
            end = next((i for i in range(start + 1, len(lines))
                        if lines[i].startswith("- ")), len(lines))
            # Written where promotion removed it, which is after `type` and
            # before the fields a reader scans for, so the state is visible
            # without scrolling the block.
            at = next((i for i in range(start + 1, end)
                       if re.match(r"^  name: ", lines[i])), start + 1)
            lines[at:at] = [
                "  review_state: withdrawn",
                f"  withdrawn_reason: {record._scalar(decision['reason'])}"]
            withdrawn += 1
            print(f"  withdrew {eid} -- {decision['reason']}")

            primary = next((p["paper_id"] for p in rec.get("papers") or []
                            if p["role"] == "primary"), None)
            if primary:
                # Appended to whatever the paper already carries, not written
                # over it: triage_rules.write_decisions merges by key, so a
                # bare dict here would discard the decisions that admitted it.
                entries = list(existing.get(primary) or [])
                entries.append({"date": date.today().isoformat(),
                                "decision": "rejected",
                                "entity_id": eid,
                                "list": "withdrawal",
                                "reason": decision["reason"],
                                "title": rec.get("name")})
                ledger[primary] = entries
        if not dry_run:
            path_.write_text("\n".join(lines), encoding="utf-8", newline="")

    no_primary = withdrawn - len(ledger)
    if dry_run:
        print(f"\ndry run: {withdrawn} record(s) would be withdrawn, "
              f"{len(ledger)} ledger entr(ies) written. Nothing changed.")
        return 0

    if ledger:
        rules.write_decisions(ledger)
    print(f"  withdrew              {withdrawn}")
    print(f"  ledger entries        {len(ledger)}")
    if no_primary:
        # A record with no primary paper cannot be suppressed by paper id, so
        # the only thing stopping its return is the entity_id it keeps.
        print(f"  {no_primary} had no primary paper, so nothing was recorded "
              f"against them in literature/decisions.yaml")
    print("next: python scripts/04_build.py && python scripts/05_validate.py "
          "&& python scripts/07_export_site.py")
    return 0


def latest() -> Path:
    files = sorted(DEMOTIONS_DIR.glob("demote_*.md"))
    if not files:
        raise SystemExit("no demotion file; run without --apply first")
    return files[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="read a worked file back and withdraw its ticks")
    parser.add_argument("--dry-run", action="store_true",
                        help="with --apply, report what would change and write nothing")
    parser.add_argument("--file")
    args = parser.parse_args()

    if not args.apply:
        out = Path(args.file) if args.file else (
            DEMOTIONS_DIR / f"demote_{date.today().isoformat()}.md")
        if out.exists():
            raise SystemExit(f"{_rel(out)} already exists; it may carry "
                             f"decisions. Move it aside or pass --file")
        return write_file(out)

    path = Path(args.file) if args.file else latest()
    decisions = parse(path)
    print(f"reading {_rel(path)}: {len(decisions)} withdrawal(s)")
    if not decisions:
        return 0
    return demote(decisions, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
