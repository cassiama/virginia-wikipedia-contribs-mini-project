# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A fact-check of a specific YouTube comment claim — that "80+% of Wikipedia
contributors have addresses in Virginia" (quoted verbatim in README.md). The
finding, documented in the README and the notebook's conclusion cell: false by
a factor of ~30 (405 self-identified Virginian editors = 2.8% of US editors,
#23 per capita, +14% vs population prediction). The claim's kernel of truth is
that Wikipedia's *servers* are in Virginia (Wikimedia's primary data center is
in Ashburn, VA). Keep README, notebook prose, and any new analysis consistent
with this framing: test the claim fairly, don't dunk on the commenter.

## Hard constraint

**Never create synthetic/fake data.** Every number in this project must come from a real source (MediaWiki API, US Census). If a data source is unavailable, fail loudly — do not fabricate, interpolate, or stub values.

## Commands

```bash
uv sync                                   # install dependencies (uv-managed venv)
uv run python src/collect.py              # re-collect from live APIs (~5 min, writes data/)
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_analysis.ipynb
uv run jupyter lab notebooks/             # interactive work
```

There are no tests or linters configured.

## Architecture

Two-stage pipeline, decoupled by CSVs committed under `data/`:

1. **`src/collect.py`** answers "who self-identifies as a Wikipedian per US state". For each of the 50 states + DC it walks `Category:Wikipedians in <state>` recursively (city subcategories, depth ≤ 3, deduped usernames), then fetches real lifetime edit counts for Virginia editors via `list=users`. It also downloads Census NST-EST2024 population estimates. Raw API responses are preserved in `data/raw/` and every run stamps `data/collection_metadata.json`.
2. **`notebooks/01_analysis.ipynb`** reads only from `data/` (never the network) and produces the findings: headline count, raw/per-capita state rankings, log-log OLS of editors vs population (statsmodels), and edit-activity distribution for Virginia editors.

Things that will bite you if you touch the collector:

- Category naming quirks are mapped in `CATEGORY_TO_CENSUS_NAME` in `src/collect.py`: `Georgia (U.S. state)`, `New York (state)`, `Washington (state)`, and `Washington, D.C.` ↔ Census `District of Columbia`. The Census merge fails hard if any state doesn't match — keep it that way.
- The MediaWiki API requires the descriptive `User-Agent` set in `collect.py` and respects `maxlag`; keep the pause between requests.
- Why self-identified categories and not IP geolocation: Northern Virginia's data-center corridor (AWS us-east-1) makes IP-based state attribution meaningless, and Wikimedia's geoeditors dataset is country-level only. This methodological choice is the core of the project — don't "improve" it with IP-based counts.
- `data/` is a committed snapshot (collection date in `data/collection_metadata.json`), and the README/notebook quote its exact numbers (405 editors, 2.8%, ranks, +14%). Re-running `src/collect.py` produces fresh live numbers — if you re-collect, re-execute the notebook **and** update the hardcoded figures in README.md and the notebook's intro/conclusion markdown cells, or don't re-collect at all.

Notebook workflow: `notebooks/01_analysis.ipynb` is committed *with executed outputs* (~260 KB, embedded charts). For markdown-only edits, modify cell sources via a small `nbformat` script (see git history) without re-executing; after any code-cell change, re-execute the whole notebook with the nbconvert command above so committed outputs never go stale.

## Roadmap

Future scope expansions are deliberately documented in README.md under
"Expanding the scope" (seven legal data avenues, ordered by effort). The
agreed natural v2 is user-page text mining via the MediaWiki API search —
start there if asked to extend the project.
