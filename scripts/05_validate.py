#!/usr/bin/env python
"""
scripts/05_validate.py
----------------------
QC for the built catalogue (schema §10). Reads db/cfcr.db, writes
db/qc_report.tsv and reports/vocab_candidates.md.

Checks
------
  prefix          entity_id prefix matches entity.type
  vocab           controlled column values resolve to a vocab term or synonym
  paper-exists    every entity_paper.paper_id is a known paper
  primary-paper   every entity has a role='primary' paper (whitelist in config/)
  evidence-tier   asserted model_ext.evidence_tier matches the derivation
  refs            supersedes / variant_of / preprint_of resolve, no cycles
  duplicates      fuzzy name+alias collisions
  orphan-papers   papers attached to no entity
  link-rot        (--check-links only) HTTP sweep over link.url
  tags            tag frequency -> reports/vocab_candidates.md

Exit status is 1 if any ERROR was reported, else 0. WARNINGs do not fail the
build; they are curation debt.

Usage:
    python scripts/05_validate.py [--repo-root PATH] [--db PATH]
                                  [--check-links] [--promote-at N]
"""

from __future__ import annotations

import argparse
import csv
import difflib
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema import (CFCR, EXT_TABLES, PARTIAL_MAX,   # noqa: E402
                    REVIEW_STATES, VOCAB_FACETS, classify_overlap,
                    derive_tier, norm_author)

ERROR, WARNING, INFO = "ERROR", "WARNING", "INFO"

# Controlled column -> vocabulary facet. A column is validated only if
# vocab/<facet>.yaml supplied terms; see the `vocab-coverage` check for the
# columns schema §3 calls controlled but ships no vocabulary for.
CONTROLLED: dict[tuple[str, str], str] = {
    ("entity", "organism"): "organism",
    ("entity", "cell_type"): "cell_type",
    ("entity", "assay"): "assay",
    ("entity", "task"): "task",
    ("model_ext", "architecture"): "architecture",
    ("model_ext", "output_type"): "output_type",
    ("dataset_ext", "modality"): "modality",
    ("benchmark_ext", "task_categories"): "task",
    ("module_collection_ext", "organism_scope"): "organism",
    ("protocol_ext", "category"): "protocol_category",
}

# Similarity above which two entity names are reported as possible duplicates.
DUPLICATE_RATIO = 0.90


class Report:
    """Collects findings and renders them for the terminal and qc_report.tsv."""

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, severity: str, check: str, subject: str, message: str,
            fix: str = "") -> None:
        # Collapse whitespace: reasons read out of YAML folded scalars arrive
        # with embedded newlines, which would make qc_report.tsv rows span
        # lines and defeat grep/awk over it.
        flat = lambda s: " ".join(str(s).split())      # noqa: E731
        self.rows.append({"severity": severity, "check": check,
                          "subject": flat(subject), "message": flat(message),
                          "fix": flat(fix)})

    @property
    def n_errors(self) -> int:
        return sum(1 for r in self.rows if r["severity"] == ERROR)

    @property
    def n_warnings(self) -> int:
        return sum(1 for r in self.rows if r["severity"] == WARNING)

    def write_tsv(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as fh:
            w = csv.DictWriter(
                fh, fieldnames=["severity", "check", "subject", "message", "fix"],
                delimiter="\t")
            w.writeheader()
            order = {ERROR: 0, WARNING: 1, INFO: 2}
            for row in sorted(self.rows,
                              key=lambda r: (order[r["severity"]], r["check"],
                                             r["subject"])):
                w.writerow(row)

    def print(self) -> None:
        order = {ERROR: 0, WARNING: 1, INFO: 2}
        for row in sorted(self.rows,
                          key=lambda r: (order[r["severity"]], r["check"],
                                         r["subject"])):
            print(f"{row['severity']:7} [{row['check']}] {row['subject']}")
            print(f"        {row['message']}")
            if row["fix"]:
                print(f"        fix: {row['fix']}")


# ── helpers ──────────────────────────────────────────────────────────────────

def norm_name(name: str) -> str:
    """Fold a display name for duplicate detection."""
    n = unicodedata.normalize("NFKD", name or "")
    n = "".join(c for c in n if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "", n)


def find_cycle(edges: dict[str, str]) -> list[str] | None:
    """Return one cycle in a functional graph (node -> single successor)."""
    state: dict[str, int] = {}
    for start in edges:
        if state.get(start):
            continue
        path: list[str] = []
        node = start
        while node in edges and not state.get(node):
            state[node] = 1
            path.append(node)
            node = edges[node]
        if node in path:
            return path[path.index(node):] + [node]
        for n in path:
            state[n] = 2
    return None


# ── checks ───────────────────────────────────────────────────────────────────

def check_prefix(entities, rep):
    for e in entities:
        eid, etype = e["entity_id"], e["type"]
        prefix = eid.split(":", 1)[0] if ":" in eid else ""
        if prefix != etype:
            rep.add(ERROR, "prefix", eid,
                    f"entity_id prefix '{prefix or '(none)'}' does not match "
                    f"type '{etype}'",
                    f"rename to '{etype}:{eid.split(':', 1)[-1]}' so type can "
                    f"be read from the id")


def check_vocab(db, entities, rep):
    terms = defaultdict(dict)       # facet -> normalized form -> canonical term
    for row in db.fetch("vocab"):
        facet, term = row["facet"], row["term"]
        terms[facet][term.lower()] = term
        for syn in row["synonyms"] or []:
            terms[facet][str(syn).lower()] = term

    missing_vocab = set()
    by_id = {e["entity_id"]: e for e in entities}

    for (table, column), facet in sorted(CONTROLLED.items()):
        rows = db.fetch(table) if table != "entity" else entities
        if facet not in terms:
            if any(r.get(column) for r in rows):
                missing_vocab.add((table, column, facet))
            continue
        for row in rows:
            values = row.get(column) or []
            if isinstance(values, str):
                values = [values]
            subject = row.get("entity_id", "?")
            for value in values:
                if str(value).lower() in terms[facet]:
                    canonical = terms[facet][str(value).lower()]
                    if canonical != value:
                        rep.add(WARNING, "vocab", subject,
                                f"{table}.{column} uses synonym '{value}'",
                                f"replace with the canonical term "
                                f"'{canonical}'")
                    continue
                near = difflib.get_close_matches(
                    str(value).lower(), list(terms[facet]), n=5, cutoff=0.6)
                # A term and its own synonyms both match and both resolve to
                # the same canonical, so dedupe before suggesting -- otherwise
                # the fix reads "did you mean 'contact-map', 'contact-map'?".
                seen, canonical = set(), []
                for n in near:
                    term = terms[facet][n]
                    if term not in seen:
                        seen.add(term)
                        canonical.append(term)
                suggestion = (
                    "did you mean " + ", ".join(
                        f"'{t}'" for t in canonical[:3]) + "?"
                    if canonical else
                    f"add it to vocab/{facet}.yaml, or correct the record")
                rep.add(ERROR, "vocab", subject,
                        f"{table}.{column} value '{value}' is not a term or "
                        f"synonym in vocab/{facet}.yaml",
                        suggestion)

    for table, column, facet in sorted(missing_vocab):
        rep.add(INFO, "vocab-coverage", f"{table}.{column}",
                f"schema §3 calls this column controlled, but no "
                f"vocab/{facet}.yaml exists, so its values are unvalidated",
                f"create vocab/{facet}.yaml to validate it, or accept the "
                f"column as free text and remove it from CONTROLLED")
    return by_id


def check_papers(db, entities, rep, whitelist):
    papers = {p["paper_id"]: p for p in db.fetch("paper")}
    eps = db.fetch("entity_paper")
    by_entity = defaultdict(list)
    for ep in eps:
        by_entity[ep["entity_id"]].append(ep)
        if ep["paper_id"] not in papers:
            rep.add(ERROR, "paper-exists", ep["entity_id"],
                    f"entity_paper references unknown paper "
                    f"'{ep['paper_id']}' (role={ep['role']})",
                    "add it to literature/papers.yaml, or fix the paper_id in "
                    "the record")

    for e in entities:
        eid = e["entity_id"]
        roles = {ep["role"] for ep in by_entity.get(eid, [])}
        if "primary" in roles:
            continue
        if eid in whitelist:
            rep.add(INFO, "primary-paper", eid,
                    f"no primary paper; whitelisted ({whitelist[eid]})")
        else:
            rep.add(ERROR, "primary-paper", eid,
                    "no attached paper with role='primary'",
                    "attach the introducing paper, or whitelist the entity in "
                    "config/qc_whitelist.yaml with a reason")

    # A preprint reached through preprint_of from an attached paper is not an
    # orphan: it is evidence for the same entity, recorded at its earlier
    # version. Flagging it would push the curator to attach both versions of
    # every paper, which duplicates the evidence rather than clarifying it.
    attached = {ep["paper_id"] for ep in eps}
    reachable = set(attached)
    for p in papers.values():
        if p.get("preprint_of") in attached:
            reachable.add(p["paper_id"])
    for pid in sorted(set(papers) - reachable):
        rep.add(WARNING, "orphan-papers", pid,
                "paper is in papers.yaml, attached to no entity, and not the "
                "preprint of an attached paper",
                "attach it to an entity, or remove it from papers.yaml")

    for p in db.fetch("paper"):
        ref = p.get("preprint_of")
        if ref and ref not in papers:
            rep.add(ERROR, "refs", p["paper_id"],
                    f"preprint_of references unknown paper '{ref}'",
                    "add the journal version to papers.yaml, or null the field")
    return papers, by_entity


def check_evidence_tier(db, papers, by_entity, rep):
    authors = {pid: {norm_author(a) for a in (p["authors"] or [])}
               for pid, p in papers.items()}
    for ext in db.fetch("model_ext"):
        eid = ext["entity_id"]
        claimed = ext.get("evidence_tier")
        eps = by_entity.get(eid, [])
        primary = set()
        for ep in eps:
            if ep["role"] == "primary":
                primary |= authors.get(ep["paper_id"], set())
        evaluations = [(ep["paper_id"], authors.get(ep["paper_id"], set()))
                       for ep in eps
                       if ep["role"] in ("benchmark", "critique")]
        derived, verdicts = derive_tier(primary, evaluations)

        if not primary and evaluations:
            rep.add(WARNING, "evidence-tier", eid,
                    "primary paper has no author list, so overlap cannot be "
                    "computed; every evaluation counted as independent",
                    "repair the primary paper's authors in papers.yaml")

        detail = "; ".join(
            f"{pid} -> {kind}" + (f" (shares {', '.join(sorted(shared))})"
                                  if shared else "")
            for pid, kind, shared in verdicts) or "no benchmark/critique papers"

        if claimed != derived:
            rep.add(ERROR, "evidence-tier", eid,
                    f"asserted evidence_tier '{claimed}' but derivation gives "
                    f"'{derived}' [{detail}]",
                    f"set evidence_tier to '{derived}' in the record, or "
                    f"attach the evaluation paper that justifies '{claimed}'")
        else:
            rep.add(INFO, "evidence-tier", eid,
                    f"{derived} [{detail}]")


def check_refs(entities, rep):
    ids = {e["entity_id"] for e in entities}
    for field in ("supersedes", "variant_of"):
        edges = {}
        for e in entities:
            ref = e.get(field)
            if not ref:
                continue
            if ref not in ids:
                rep.add(ERROR, "refs", e["entity_id"],
                        f"{field} references unknown entity '{ref}'",
                        "add the referenced entity, or correct the id")
                continue
            if ref == e["entity_id"]:
                rep.add(ERROR, "refs", e["entity_id"],
                        f"{field} points at itself")
                continue
            edges[e["entity_id"]] = ref
        cycle = find_cycle(edges)
        if cycle:
            rep.add(ERROR, "refs", cycle[0],
                    f"{field} cycle: {' -> '.join(cycle)}",
                    f"break the cycle; {field} must form a DAG")


def check_duplicates(entities, rep):
    names: list[tuple[str, str, str]] = []     # (normalized, label, entity_id)
    for e in entities:
        names.append((norm_name(e["name"]), e["name"], e["entity_id"]))
        for alias in e.get("aliases") or []:
            names.append((norm_name(alias), f"alias '{alias}'", e["entity_id"]))
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            na, la, ia = names[i]
            nb, lb, ib = names[j]
            if ia == ib or not na or not nb:
                continue
            ratio = difflib.SequenceMatcher(None, na, nb).ratio()
            if ratio >= DUPLICATE_RATIO:
                rep.add(WARNING, "duplicates", f"{ia} / {ib}",
                        f"{la} and {lb} are {ratio:.0%} similar",
                        "confirm these are distinct artifacts; if one is a "
                        "port or replicate, set variant_of instead")


def check_links(db, rep, do_sweep, timeout=8.0):
    links = db.fetch("link")
    if not do_sweep:
        rep.add(INFO, "link-rot", "-",
                f"{len(links)} links not checked (pass --check-links to sweep)")
        return
    import urllib.error
    import urllib.request
    today = date.today().isoformat()
    updates = []
    for link in links:
        url = link["url"]
        alive = None
        try:
            req = urllib.request.Request(
                url, method="HEAD",
                headers={"User-Agent": "CFCR-linkcheck/0.1"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                alive = 200 <= resp.status < 400
        except urllib.error.HTTPError as exc:
            # 401/403 means "exists but will not answer an anonymous HEAD".
            # HuggingFace does this for live repos, so treating it as dead
            # would mark working links rotten.
            if exc.code in (401, 403, 405):
                alive = None
                rep.add(INFO, "link-rot", link["entity_id"],
                        f"{url} returned {exc.code}; alive left unknown")
            elif exc.code in (404, 410):
                # The server answered and said it is gone. This is link rot.
                alive = False
                rep.add(WARNING, "link-rot", link["entity_id"],
                        f"{url} returned HTTP {exc.code}",
                        "update or remove the link")
            else:
                alive = None
                rep.add(INFO, "link-rot", link["entity_id"],
                        f"{url} returned HTTP {exc.code}; alive left unknown")
        except Exception as exc:                  # noqa: BLE001
            # Connection-level failure: timeout, DNS, refused. This says
            # nothing about the link -- it says the sweep could not reach it
            # from here. A host behind a restrictive network may resolve one
            # domain and time out on another, so marking these dead would
            # write alive=0 for every link to the blocked domain and churn the
            # snapshot with false deaths. Only a server that answers 404/410 is
            # evidence of rot, so `alive` stays unknown.
            alive = None
            rep.add(WARNING, "link-rot", link["entity_id"],
                    f"{url} unreachable from this host "
                    f"({type(exc).__name__}); alive left unknown",
                    "re-run the sweep from a host with unrestricted outbound "
                    "access before treating this as link rot")
        updates.append({"entity_id": link["entity_id"], "kind": link["kind"],
                        "url": url, "checked": today,
                        "alive": None if alive is None else int(alive)})
    if updates:
        db.upsert_links(updates)


def check_tags(db, entities, rep, root, promote_at):
    counts = Counter()
    for e in entities:
        for tag in e.get("tags") or []:
            counts[str(tag)] += 1

    # vocab.n_records: how many entities use each controlled term, which is
    # what drives promotion review in the other direction.
    usage = Counter()
    for e in entities:
        for facet in ("organism", "cell_type", "assay", "task"):
            for value in e.get(facet) or []:
                usage[(facet, str(value))] += 1
    vocab_rows = []
    for row in db.fetch("vocab"):
        vocab_rows.append({"facet": row["facet"], "term": row["term"],
                           "n_records": usage.get((row["facet"], row["term"]), 0)})
    if vocab_rows:
        db.upsert_vocab(vocab_rows)

    candidates = [(t, n) for t, n in counts.most_common() if n >= promote_at]
    out = root / "reports" / "vocab_candidates.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Vocabulary promotion candidates",
        "",
        f"Generated by `scripts/05_validate.py` on {date.today().isoformat()}.",
        "",
        f"Free-text `tags` are a staging area. A tag on **>= {promote_at} "
        f"records** is a candidate for promotion into `vocab/` with synonyms "
        f"and, where it carries weight, an ontology id.",
        "",
    ]
    if candidates:
        lines += ["| tag | records |", "|---|---|"]
        lines += [f"| {t} | {n} |" for t, n in candidates]
        for tag, n in candidates:
            rep.add(INFO, "tags", tag,
                    f"tag on {n} records, at or above the promotion threshold "
                    f"of {promote_at}",
                    "promote it into the matching vocab/*.yaml, or reject it")
    else:
        lines.append(f"No tag yet reaches {promote_at} records. "
                     f"Current catalogue is too small for the threshold to "
                     f"fire; the most frequent tags are listed below for "
                     f"context only.")
        lines += ["", "| tag | records |", "|---|---|"]
        lines += [f"| {t} | {n} |" for t, n in counts.most_common(15)]
    lines.append("")
    out.write_text("\n".join(lines), newline="")
    return out


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=Path(__file__).resolve().parent.parent,
                    type=Path)
    ap.add_argument("--db", default=None, type=Path)
    ap.add_argument("--check-links", action="store_true",
                    help="sweep every link.url and update link.alive")
    ap.add_argument("--link-timeout", type=float, default=8.0,
                    help="per-link HTTP timeout in seconds (default 8)")
    ap.add_argument("--promote-at", type=int, default=10,
                    help="tag frequency at which promotion is suggested")
    args = ap.parse_args()

    root: Path = args.repo_root
    db_path: Path = args.db or (root / "db" / "cfcr.db")
    if not db_path.exists():
        print(f"error: {db_path} not found -- run scripts/04_build.py first",
              file=sys.stderr)
        return 1

    wl_path = root / "config" / "qc_whitelist.yaml"
    whitelist = {}
    if wl_path.exists():
        loaded = yaml.safe_load(wl_path.read_text(encoding="utf-8")) or {}
        whitelist = (loaded.get("no_primary_paper") or {})

    rep = Report()
    with CFCR(db_path) as db:
        entities = db.fetch("entity")
        if not entities:
            print("error: no entities in the database", file=sys.stderr)
            return 1

        check_prefix(entities, rep)
        check_vocab(db, entities, rep)
        papers, by_entity = check_papers(db, entities, rep, whitelist)
        check_evidence_tier(db, papers, by_entity, rep)
        check_refs(entities, rep)
        check_duplicates(entities, rep)
        check_links(db, rep, args.check_links, args.link_timeout)
        cand_path = check_tags(db, entities, rep, root, args.promote_at)

        tsv = root / "db" / "qc_report.tsv"
        rep.write_tsv(tsv)

    rep.print()
    print()
    print(f"{len(entities)} entities, {len(papers)} papers checked")
    print(f"{rep.n_errors} error(s), {rep.n_warnings} warning(s)")
    print(f"wrote {tsv.relative_to(root)} and {cand_path.relative_to(root)}")
    if VOCAB_FACETS and not set(VOCAB_FACETS) <= {
            p.stem for p in (root / "vocab").glob("*.yaml")}:
        missing = sorted(set(VOCAB_FACETS)
                         - {p.stem for p in (root / "vocab").glob("*.yaml")})
        print(f"note: VOCAB_FACETS lists facets with no file: {missing}")
    return 1 if rep.n_errors else 0


if __name__ == "__main__":
    sys.exit(main())
