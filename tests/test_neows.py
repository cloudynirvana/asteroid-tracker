"""Offline tests. The fixture below is a hand-made response in the NeoWs
format, used only to test the parsing code; it is not real data."""
from datetime import date

import pytest

import neows

FAKE_FEED = {
    "near_earth_objects": {
        "2026-10-12": [{
            "id": "1", "name": "(2026 AA)", "nasa_jpl_url": "https://example.org/1",
            "is_potentially_hazardous_asteroid": True,
            "estimated_diameter": {"meters": {"estimated_diameter_min": 150.0,
                                              "estimated_diameter_max": 335.4}},
            "close_approach_data": [{
                "close_approach_date": "2026-10-12",
                "miss_distance": {"kilometers": "768800.0"},
                "relative_velocity": {"kilometers_per_hour": "54000.5"},
            }],
        }],
        "2026-10-13": [{
            "id": "2", "name": "2026 BB", "nasa_jpl_url": "",
            "is_potentially_hazardous_asteroid": False,
            "estimated_diameter": {"meters": {"estimated_diameter_min": 10.0,
                                              "estimated_diameter_max": 22.4}},
            "close_approach_data": [{
                "close_approach_date": "2026-10-13",
                "miss_distance": {"kilometers": "192200"},
                "relative_velocity": {"kilometers_per_hour": "30000"},
            }],
        }],
    }
}


def test_week_chunks_split_long_ranges():
    chunks = neows.week_chunks(date(2026, 10, 1), date(2026, 10, 31))
    assert chunks[0] == (date(2026, 10, 1), date(2026, 10, 7))
    assert chunks[-1] == (date(2026, 10, 29), date(2026, 10, 31))
    assert all((b - a).days < 7 for a, b in chunks)
    # no gaps or overlaps
    for (_, b), (c, _) in zip(chunks, chunks[1:]):
        assert (c - b).days == 1


def test_week_chunks_rejects_backwards_range():
    with pytest.raises(ValueError):
        neows.week_chunks(date(2026, 10, 5), date(2026, 10, 1))


def test_flatten_converts_strings_and_units():
    df = neows.flatten(FAKE_FEED)
    assert len(df) == 2
    a = df.set_index("neo_id").loc["1"]
    assert a["name"] == "2026 AA"
    assert a.miss_km == 768800.0 and a.speed_kmh == 54000.5
    assert a.lunar_distances == pytest.approx(2.0)
    assert a.hazardous
    assert df.set_index("neo_id").loc["2"].lunar_distances == pytest.approx(0.5)


def test_fetch_range_loops_week_by_week(monkeypatch, tmp_path):
    calls = []

    class Resp:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return FAKE_FEED

    def fake_get(url, params, timeout):
        calls.append((params["start_date"], params["end_date"]))
        return Resp()

    monkeypatch.setattr(neows.requests, "get", fake_get)
    monkeypatch.setattr(neows, "CACHE_DIR", tmp_path)
    df = neows.fetch_range(date(2026, 10, 1), date(2026, 10, 20), key="x", use_cache=False)
    assert calls == [("2026-10-01", "2026-10-07"), ("2026-10-08", "2026-10-14"),
                     ("2026-10-15", "2026-10-20")]
    # same objects in every fake chunk are de-duplicated
    assert len(df) == 2
    assert df.diameter_max_m.is_monotonic_decreasing


def test_bad_key_gives_clear_message(monkeypatch):
    class Resp:
        status_code = 403
    monkeypatch.setattr(neows.requests, "get", lambda *a, **k: Resp())
    with pytest.raises(RuntimeError, match="API key"):
        neows.fetch_chunk(date(2026, 10, 1), date(2026, 10, 2), "bad", use_cache=False)


def test_same_asteroid_listed_twice_is_kept_once():
    import copy
    feed = copy.deepcopy(FAKE_FEED)
    twin = copy.deepcopy(feed["near_earth_objects"]["2026-10-13"][0])
    twin.update(id="3", name="679786 (2026 BB)")
    feed["near_earth_objects"]["2026-10-13"].append(twin)
    df = neows.flatten(feed)
    assert len(df) == 2
    assert "679786 (2026 BB)" in set(df["name"]) and "2026 BB" not in set(df["name"])
