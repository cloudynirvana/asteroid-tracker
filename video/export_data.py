"""Export the numbers the film puts on screen, from live NeoWs data.

Every figure in the video comes from this file, so nothing on screen is typed
by hand. Run it, then render.

    NASA_API_KEY=... python3 export_data.py
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import neows  # noqa: E402

OUT = Path(__file__).parent / "public" / "data.json"
DAYS = 365          # a full year of close approaches
WEEK = 7            # the "this week" panel
MOON_KM = neows.LUNAR_DISTANCE_KM


def main() -> None:
    start = date.today()
    end = start + timedelta(days=DAYS - 1)
    print(f"fetching {DAYS} days of close approaches from NeoWs...", flush=True)
    df = neows.fetch_range(start, end)
    week = df[df.approach_date.dt.date <= start + timedelta(days=WEEK - 1)]

    mid = (df.diameter_min_m + df.diameter_max_m) / 2
    closest = df.loc[df.lunar_distances.idxmin()]
    biggest = df.loc[df.diameter_max_m.idxmax()]
    fastest = df.loc[df.speed_kmh.idxmax()]

    # size bands, on the mid estimate
    bands = [("under 10 m", 0, 10), ("10 to 50 m", 10, 50), ("50 to 140 m", 50, 140),
             ("140 to 500 m", 140, 500), ("over 500 m", 500, 1e9)]

    def row(r):
        return {
            "name": r["name"],
            "date": str(r.approach_date.date()),
            "diameter_min_m": round(float(r.diameter_min_m), 1),
            "diameter_max_m": round(float(r.diameter_max_m), 1),
            "lunar_distances": round(float(r.lunar_distances), 2),
            "miss_km": round(float(r.miss_km)),
            "speed_kmh": round(float(r.speed_kmh)),
            "hazardous": bool(r.hazardous),
        }

    data = {
        "generated": str(date.today()),
        "span": {"start": str(start), "end": str(end), "days": DAYS},
        "moon_km": MOON_KM,
        "total": int(len(df)),
        "hazardous": int(df.hazardous.sum()),
        "inside_moon": int((df.lunar_distances < 1).sum()),
        "inside_tenth_moon": int((df.lunar_distances < 0.1).sum()),
        "over_140m": int((mid >= 140).sum()),
        "week": {
            "days": WEEK,
            "count": int(len(week)),
            "hazardous": int(week.hazardous.sum()),
            "rows": [row(r) for _, r in week.sort_values("lunar_distances").head(8).iterrows()],
        },
        "closest": row(closest),
        "biggest": row(biggest),
        "fastest": row(fastest),
        "bands": [{"label": lab, "count": int(((mid >= lo) & (mid < hi)).sum())}
                  for lab, lo, hi in bands],
        "closest_ten": [row(r) for _, r in df.sort_values("lunar_distances").head(10).iterrows()],
        "by_month": [
            {"month": str(m)[:7], "count": int(n)}
            for m, n in df.groupby(df.approach_date.dt.to_period("M")).size().items()
        ],
        "ranges": [
            {"name": r["name"], "lo": round(float(r.diameter_min_m), 1),
             "hi": round(float(r.diameter_max_m), 1)}
            for _, r in df.assign(_m=mid).sort_values("_m")
                          .iloc[::max(1, len(df) // 40)].head(40).iterrows()
        ],
        "scatter": [
            {"ld": round(float(r.lunar_distances), 3), "d": round(float(mid[i]), 1),
             "h": bool(r.hazardous)}
            for i, r in df.iterrows()
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    print(f"{data['total']} approaches, {data['hazardous']} flagged, "
          f"{data['inside_moon']} closer than the Moon -> {OUT}")


if __name__ == "__main__":
    main()
