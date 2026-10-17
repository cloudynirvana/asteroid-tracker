"""Fetch and tidy near-Earth object data from NASA's NeoWs feed.

The feed only accepts date ranges of up to 7 days, so longer ranges are
split into weekly chunks. Each chunk is cached as a CSV in data/ so a
page refresh does not hit the API again.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

FEED_URL = "https://api.nasa.gov/neo/rest/v1/feed"
LUNAR_DISTANCE_KM = 384_400
MAX_DAYS_PER_CALL = 7
CACHE_DIR = Path(__file__).parent / "data"

COLUMNS = [
    "name", "neo_id", "approach_date", "diameter_min_m", "diameter_max_m",
    "miss_km", "lunar_distances", "speed_kmh", "hazardous", "jpl_url",
]


def api_key() -> str:
    """Read the key from the environment (or a local .env file)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    key = os.environ.get("NASA_API_KEY")
    if not key:
        raise RuntimeError(
            "NASA_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return key


def week_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into inclusive ranges of at most 7 days."""
    if end < start:
        raise ValueError("end date is before start date")
    chunks = []
    cur = start
    while cur <= end:
        stop = min(cur + timedelta(days=MAX_DAYS_PER_CALL - 1), end)
        chunks.append((cur, stop))
        cur = stop + timedelta(days=1)
    return chunks


def flatten(feed: dict) -> pd.DataFrame:
    """Turn one NeoWs feed response into one row per close approach."""
    rows = []
    for day, objects in feed["near_earth_objects"].items():
        for o in objects:
            d = o["estimated_diameter"]["meters"]
            # one entry per approach; the feed lists the one in the requested range
            for ca in o["close_approach_data"]:
                if ca["close_approach_date"] != day:
                    continue
                miss_km = float(ca["miss_distance"]["kilometers"])
                rows.append({
                    "name": o["name"][1:-1] if o["name"].startswith("(") else o["name"],
                    "neo_id": o["id"],
                    "approach_date": day,
                    "diameter_min_m": float(d["estimated_diameter_min"]),
                    "diameter_max_m": float(d["estimated_diameter_max"]),
                    "miss_km": miss_km,
                    "lunar_distances": miss_km / LUNAR_DISTANCE_KM,
                    "speed_kmh": float(ca["relative_velocity"]["kilometers_per_hour"]),
                    "hazardous": bool(o["is_potentially_hazardous_asteroid"]),
                    "jpl_url": o.get("nasa_jpl_url", ""),
                })
    df = pd.DataFrame(rows, columns=COLUMNS)
    df["approach_date"] = pd.to_datetime(df["approach_date"])
    # NeoWs sometimes lists one asteroid twice: once as "2020 QG3" and once, after it was
    # numbered, as "679786 (2020 QG3)". Keep the numbered entry.
    designation = df["name"].str.extract(r"\((.+)\)$")[0].fillna(df["name"])
    df = (df.assign(_d=designation, _numbered=df["name"].str.contains(r"\(", regex=True))
            .sort_values("_numbered", ascending=False)
            .drop_duplicates(["_d", "approach_date"])
            .drop(columns=["_d", "_numbered"])
            .sort_index()
            .reset_index(drop=True))
    return df


def fetch_chunk(start: date, end: date, key: str, use_cache: bool = True) -> pd.DataFrame:
    cache = CACHE_DIR / f"neo_{start}_{end}.csv"
    # only trust the cache for ranges that are fully in the past
    if use_cache and cache.exists() and end < date.today():
        return pd.read_csv(cache, parse_dates=["approach_date"])
    r = requests.get(
        FEED_URL,
        params={"start_date": str(start), "end_date": str(end), "api_key": key},
        timeout=30,
    )
    if r.status_code == 403:
        raise RuntimeError("NASA rejected the API key (403). Check NASA_API_KEY.")
    if r.status_code == 429:
        raise RuntimeError("Hourly NASA API limit reached (429). Try again later.")
    r.raise_for_status()
    df = flatten(r.json())
    if use_cache:
        CACHE_DIR.mkdir(exist_ok=True)
        df.to_csv(cache, index=False)
    return df


def fetch_range(start: date, end: date, key: str | None = None, use_cache: bool = True) -> pd.DataFrame:
    """All close approaches between start and end, any length of range."""
    key = key or api_key()
    parts = [fetch_chunk(a, b, key, use_cache) for a, b in week_chunks(start, end)]
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=COLUMNS)
    return df.drop_duplicates(["neo_id", "approach_date"]).sort_values(
        "diameter_max_m", ascending=False, ignore_index=True
    )


if __name__ == "__main__":
    today = date.today()
    df = fetch_range(today, today + timedelta(days=6))
    print(f"{len(df)} close approaches, {df.hazardous.sum()} flagged potentially hazardous")
    print(df[["name", "approach_date", "diameter_min_m", "diameter_max_m",
              "lunar_distances", "speed_kmh", "hazardous"]].head(10).to_string(index=False))
