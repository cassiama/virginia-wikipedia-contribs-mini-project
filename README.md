# How many Wikipedia contributors are from Virginia?

A mini data science project fact-checking a
YouTube comment
(a reply on TREY the Explainer's *"The Rarest Signature"*, under a comment
praising Wikipedia's citations) that claimed:

> *"Plus, can anyone answer why the large majority (80+%) of 'Contributors'
> have addresses in Virginia? 😂😂"*

That's a concrete, falsifiable claim — so instead of arguing, we test it
with real data.

**Verdict: false by a factor of ~30.** Self-identified Virginian editors are
**2.8%** of self-identified US editors (405 people), ranked #12 of 51 states
by raw count and #23 per capita. Virginia over-indexes modestly (+14% vs its
population's prediction) — real, but nothing like 80%. The claim's kernel of
truth: Wikipedia's *servers* are in Virginia (Wikimedia's primary data center
is in Ashburn, VA), so IP lookups of wikipedia.org or raw traffic really do
say "Virginia" — about the infrastructure, not the people.

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

## Expanding the scope

Other legal data avenues for a future v2, roughly in order of effort:

1. **User-page text mining** — search the User namespace for location
   userboxes and free-text statements ("I live in Richmond, VA") via the
   MediaWiki API. Catches self-identifiers who never used the category;
   the most natural NLP extension of the current pipeline and would likely
   raise the 405 figure meaningfully.
2. **WikiProject Virginia + meetup pages** — participant lists for
   [WikiProject Virginia](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Virginia)
   and DC/Virginia meetup and edit-a-thon pages are public records of
   engaged local editors.
3. **Wikimedia Geoeditors dataset** —
   [official monthly active-editor counts by country](https://dumps.wikimedia.org/other/geoeditors/).
   Country-level only (state-level is withheld for privacy) but useful for
   calibration: what share of US editors does self-identification capture?
4. **Anonymous-edit IP geolocation** — IPs of unregistered editors are
   public in page histories; geolocate with MaxMind GeoLite2 and filter
   known cloud/data-center ASNs to reduce the Northern-Virginia bias.
   A closing window: Wikipedia's rollout of temporary accounts masks IPs
   going forward.
5. **Behavioral inference ("locals edit local")** — academic literature
   shows editors disproportionately edit geotagged articles near them.
   Modeling editors of Virginia-local articles (small towns, schools,
   highways) gives a model-based estimate rather than a count — the most
   interesting ML direction.
6. **Wikimedia Community Insights survey** — published aggregate editor
   demographics, useful for framing (country-level only).
7. **Formal WMF research collaboration** — the
   [Wikimedia Research team](https://research.wikimedia.org/) grants
   vetted researchers access to non-public data under privacy agreements;
   the only route to a true state-level number.

## Caveats

Self-identified categories undercount real editors (most editors never tag
their user page), include dormant accounts, and reflect en-wiki only. The
numbers answer "how many editors *publicly say* they're from Virginia" — the
best available real proxy for a question Wikimedia deliberately doesn't
publish state-level data on.

## License

The code and notebook are released under the [MIT License](LICENSE).

The data under `data/` keeps its original terms: the Wikipedia-derived files
(`data/raw/category_members/`, `data/virginia_wikipedians.csv`,
`data/wikipedians_by_state.csv`) come from English Wikipedia via the MediaWiki
API and are available under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); the US Census
Bureau files are public domain.
