"""Collect real data on self-identified Wikipedia editors per US state.

Sources (no synthetic data anywhere):
  1. English Wikipedia MediaWiki Action API -- members of
     "Category:Wikipedians in <state>" and its subcategories (city-level
     categories such as "Category:Wikipedians in Richmond, Virginia").
  2. US Census Bureau NST-EST2024 state population estimates CSV.

Outputs (under data/):
  raw/category_members/<state>.json   raw member lists per state, per category
  raw/NST-EST2024-ALLDATA.csv         Census population file as downloaded
  wikipedians_by_state.csv            one row per state with editor counts
  virginia_wikipedians.csv            per-user edit counts for Virginia editors
  state_population.csv                tidy state -> population table
  collection_metadata.json            timestamps and endpoint info
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://en.wikipedia.org/w/api.php"
CENSUS_URL = (
    "https://www2.census.gov/programs-surveys/popest/datasets/"
    "2020-2024/state/totals/NST-EST2024-ALLDATA.csv"
)
USER_AGENT = (
    "VirginiaWikipediansResearch/0.1 "
    "(https://github.com/cassiama; assiamah.ch@gmail.com) "
    "python-requests"
)
REQUEST_PAUSE_S = 0.15
MAX_CATEGORY_DEPTH = 3

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
MEMBERS_DIR = RAW_DIR / "category_members"

STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia (U.S. state)", "Hawaii",
    "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York (state)",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington (state)",
    "Washington, D.C.", "West Virginia", "Wisconsin", "Wyoming",
]

# Map category naming quirks back to Census NAME values.
CATEGORY_TO_CENSUS_NAME = {
    "Georgia (U.S. state)": "Georgia",
    "New York (state)": "New York",
    "Washington (state)": "Washington",
    "Washington, D.C.": "District of Columbia",
}

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT


def api_get(params: dict) -> dict:
    params = {"format": "json", "maxlag": 5, **params}
    for attempt in range(5):
        resp = session.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        if "error" in payload and payload["error"].get("code") == "maxlag":
            time.sleep(2 ** attempt)
            continue
        if "error" in payload:
            raise RuntimeError(f"API error: {payload['error']}")
        time.sleep(REQUEST_PAUSE_S)
        return payload
    raise RuntimeError("API kept reporting maxlag after 5 attempts")


def category_members(category: str) -> tuple[list[dict], list[str]]:
    """Return (user page members, subcategory titles) for a category."""
    users: list[dict] = []
    subcats: list[str] = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": 500,
        "cmprop": "title|ns",
    }
    while True:
        payload = api_get(params)
        for member in payload["query"]["categorymembers"]:
            if member["ns"] == 14:
                subcats.append(member["title"])
            elif member["ns"] in (2, 3):  # User / User talk namespaces
                users.append(member)
        if "continue" not in payload:
            return users, subcats
        params.update(payload["continue"])


def username_from_title(title: str) -> str:
    name = title.split(":", 1)[1]
    return name.split("/", 1)[0].strip()


def collect_state(state: str) -> dict:
    """Walk the category tree for one state; return usernames + raw records."""
    root = f"Category:Wikipedians in {state}"
    queue: list[tuple[str, int]] = [(root, 0)]
    visited: set[str] = set()
    usernames: set[str] = set()
    raw: dict[str, list[dict]] = {}
    while queue:
        category, depth = queue.pop(0)
        if category in visited or depth > MAX_CATEGORY_DEPTH:
            continue
        visited.add(category)
        members, subcats = category_members(category)
        raw[category] = members
        usernames.update(username_from_title(m["title"]) for m in members)
        queue.extend((sub, depth + 1) for sub in subcats)
    return {"usernames": sorted(usernames), "categories": raw}


def fetch_user_info(usernames: list[str]) -> pd.DataFrame:
    """Fetch real edit counts and registration dates in batches of 50."""
    rows = []
    for i in range(0, len(usernames), 50):
        batch = usernames[i : i + 50]
        payload = api_get(
            {
                "action": "query",
                "list": "users",
                "ususers": "|".join(batch),
                "usprop": "editcount|registration",
            }
        )
        for user in payload["query"]["users"]:
            rows.append(
                {
                    "username": user.get("name"),
                    "editcount": user.get("editcount"),
                    "registration": user.get("registration"),
                    "missing": "missing" in user or "invalid" in user,
                }
            )
    return pd.DataFrame(rows)


def collect_population() -> pd.DataFrame:
    raw_path = RAW_DIR / "NST-EST2024-ALLDATA.csv"
    if not raw_path.exists():
        resp = session.get(CENSUS_URL, timeout=60)
        resp.raise_for_status()
        raw_path.write_bytes(resp.content)
    census = pd.read_csv(raw_path)
    states = census[census["SUMLEV"] == 40][["NAME", "POPESTIMATE2024"]]
    return states.rename(columns={"NAME": "state", "POPESTIMATE2024": "population_2024"})


def main() -> None:
    MEMBERS_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()

    state_rows = []
    virginia_usernames: list[str] = []
    for state in STATES:
        result = collect_state(state)
        census_name = CATEGORY_TO_CENSUS_NAME.get(state, state)
        slug = census_name.lower().replace(" ", "_").replace(".", "")
        (MEMBERS_DIR / f"{slug}.json").write_text(json.dumps(result["categories"], indent=1))
        state_rows.append(
            {
                "state": census_name,
                "n_wikipedians": len(result["usernames"]),
                "n_categories": len(result["categories"]),
            }
        )
        if census_name == "Virginia":
            virginia_usernames = result["usernames"]
        print(f"{census_name:25s} {len(result['usernames']):5d} editors "
              f"({len(result['categories'])} categories)", flush=True)

    by_state = pd.DataFrame(state_rows)
    population = collect_population()
    by_state = by_state.merge(population, on="state", how="left")
    if by_state["population_2024"].isna().any():
        missing = by_state[by_state["population_2024"].isna()]["state"].tolist()
        sys.exit(f"Census merge failed for: {missing}")
    by_state.to_csv(DATA_DIR / "wikipedians_by_state.csv", index=False)
    population.to_csv(DATA_DIR / "state_population.csv", index=False)

    print(f"\nFetching edit counts for {len(virginia_usernames)} Virginia editors...")
    va_users = fetch_user_info(virginia_usernames)
    va_users.to_csv(DATA_DIR / "virginia_wikipedians.csv", index=False)

    (DATA_DIR / "collection_metadata.json").write_text(
        json.dumps(
            {
                "collected_started_utc": started,
                "collected_finished_utc": datetime.now(timezone.utc).isoformat(),
                "wikipedia_api": API_URL,
                "census_file": CENSUS_URL,
                "user_agent": USER_AGENT,
                "n_states": len(STATES),
                "max_category_depth": MAX_CATEGORY_DEPTH,
            },
            indent=2,
        )
    )
    print("Done. Outputs written to data/")


if __name__ == "__main__":
    main()
