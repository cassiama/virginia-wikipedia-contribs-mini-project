# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
