# Coding principles

No features beyond what was asked. No speculative abstractions, configurability,
or error handling for impossible scenarios.

* Surgical changes. Touch only what the task requires. Don't improve adjacent
  code, comments, or formatting. Match existing style.
* Surface tradeoffs before coding. If multiple interpretations exist, present
  them — don't pick silently. If something is unclear, ask.
* If you notice unrelated dead code or issues, mention them — don't silently
  fix them.

# Reviewing for exposure

This repository is public and its history is permanent, so every code or
documentation review ends with one question: did this change publish something
personal? Rewriting history afterwards does not retract what was already cloned.

**Check the diff, never the tree.** The cost has to scale with the change, not
with the repository, or the check gets skipped once CFCR is at 300 entities.
One pipeline answers it:

```bash
git diff "$(git merge-base HEAD origin/main)" -U0 | grep '^+' | grep -inEf .github/exposure-patterns.txt
```

Added lines only, and that is the point: an address that was already public is
not news, and a check that re-reports it every time teaches you to ignore it.
Exit status 1 with no output means the diff is clean.

The patterns live in `.github/exposure-patterns.txt` so this file does not have
to contain the strings it is looking for. That file holds **one extended regex
per line and nothing else** — `grep -f` has no comment syntax, so a `#` line is
a pattern and a blank line is a pattern that matches everything.

**Known and deliberate, so not findings:**

* The maintainer contact address in `config/sources.yaml` — Crossref and
  OpenAlex both want one for their polite pool, and that file is where external
  services are declared along with the reason.
* The same address in `site/index.html` — NAR requires a working contact on the
  database itself.
* The git author identity on every commit.

Everything else that matches is a finding. In particular:

* A **second home for the contact address** instead of a read of
  `config/sources.yaml`. `literature/01_search.py` and `literature/triage_eval.py`
  each hardcode their own copy today; four copies mean changing or withdrawing
  the address requires finding all four.
* An **absolute path carrying a username** — a Windows user directory, a
  Unix home directory, a macOS user directory — in code, a docstring, or
  a commit message. Described rather than spelled out, so this file stays
  clean under its own check.
* A **token or key** of any shape.
* A **real person's name, institution or affiliation** written into a comment or
  a commit message rather than into `records/` as curated bibliographic
  metadata. Co-maintainers and curators are named in `records/`, which is the
  catalogue; a review should not leak them into prose.

**Third-party data is a separate question from exposure.**
`literature/papers.yaml` and `literature/reviews/` carry author lists and
abstracts fetched from Crossref, Europe PMC, OpenAlex and arXiv. The standing
rule is open metadata only — publisher-released abstracts, never the full text
of paywalled work. Say so plainly in a review if a change starts storing more
than that, or starts storing a great deal more of it: one review file holds
several hundred abstracts, which is a difference in scale from the thirty in
`papers.yaml` even though every one of them is individually permitted.
