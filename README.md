# How many Wikipedia contributors are from Virginia?

A mini data science project answering a question sparked by a random
[YouTube comment](https://www.youtube.com/watch?v=aFHxsS6uv5g&lc=UgzPMAPWOXq9htO8tOZ4AaABAg.ACssRWZFXwJACuJMHlcyQe):
how many of the people who write Wikipedia are actually from Virginia?

## Why this is a trickier question than it sounds

You can't just geolocate edits by IP address. Northern Virginia hosts the
largest concentration of data centers on Earth (AWS `us-east-1`, much of the
commercial internet), so naive IP geolocation massively over-attributes
internet activity to Virginia — traffic from VPNs, cloud servers, and bots all
"lives" there. The Wikimedia Foundation's own
[geoeditors dataset](https://dumps.wikimedia.org/other/geoeditors/) is only
published at country level for privacy reasons, so there is no official
state-level editor count.

The honest, real-data way to answer the question is **self-identification**:
English Wikipedia editors voluntarily place their user pages in
`Category:Wikipedians in Virginia` (and city-level subcategories like
`Category:Wikipedians in Richmond, Virginia`). Every US state has an
equivalent category, which lets us compare Virginia against the other 49
states + DC and normalize by population.

## Data sources (100% real, no synthetic data)

| Dataset | Source | What it gives us |
|---|---|---|
| Category members | [English Wikipedia MediaWiki Action API](https://www.mediawiki.org/wiki/API:Categorymembers) | Self-identified editors per state (category tree walked recursively) |
| Editor activity | MediaWiki API [`list=users`](https://www.mediawiki.org/wiki/API:Users) | Real lifetime edit counts + registration dates for every Virginia editor |
| State populations | [US Census Bureau NST-EST2024](https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/state/totals/) | 2024 population estimates for per-capita normalization |

Raw API responses are preserved under `data/raw/` and the collection run is
timestamped in `data/collection_metadata.json` for reproducibility.

## Stack

Python 3 managed with [`uv`](https://docs.astral.sh/uv/), `requests` for
collection, `pandas` for wrangling, `matplotlib`/`seaborn` for visuals,
`statsmodels` for the population-vs-editors regression, Jupyter for analysis.

## How to run

```bash
uv sync                                   # install dependencies
uv run python src/collect.py              # re-collect data from live APIs (~5 min)
uv run jupyter lab notebooks/             # open the analysis notebook
```

To execute the notebook headlessly:

```bash
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_analysis.ipynb
```

## Repository layout

- `src/collect.py` — data collection (Wikipedia API + Census), writes `data/`
- `data/` — committed snapshot of collected data (tidy CSVs + raw responses)
- `notebooks/01_analysis.ipynb` — the analysis and findings

## Caveats

Self-identified categories undercount real editors (most editors never tag
their user page), include dormant accounts, and reflect en-wiki only. The
numbers answer "how many editors *publicly say* they're from Virginia" — the
best available real proxy for a question Wikimedia deliberately doesn't
publish state-level data on.
