"""Addresses -> (lat, lon) via the free U.S. Census Bureau geocoder, with a
local SQLite cache so re-running a list never re-asks for an address that's
already been resolved.

New addresses go to the Census batch service, up to BATCH_SIZE per request:
about 13 ms each instead of ~620 ms asking one at a time. The batch service
can return spurious misses, so anything it doesn't match is retried one at a
time — the same lookup this tool always did. The worst case is the old speed,
never a lost match.
"""

import csv
import io
import sqlite3
import time

import requests

from app_paths import cache_path

ONE_ADDRESS_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
BATCH_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BENCHMARK = "Public_AR_Current"
CACHE_PATH = cache_path()
# Small enough that progress moves every few seconds; the service allows 10,000.
BATCH_SIZE = 250
REQUEST_DELAY_SECONDS = 0.2  # courtesy pause between one-at-a-time retries

UNMATCHED = {"matched": False, "matched_address": None, "lat": None, "lon": None}


def _get_cache_conn():
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS geocode_cache (
            address TEXT PRIMARY KEY,
            matched INTEGER NOT NULL,
            matched_address TEXT,
            lat REAL,
            lon REAL
        )"""
    )
    return conn


def _from_cache(conn, address: str) -> dict | None:
    row = conn.execute(
        "SELECT matched, matched_address, lat, lon FROM geocode_cache WHERE address = ?",
        (address,),
    ).fetchone()
    if row is None:
        return None
    matched, matched_address, lat, lon = row
    return {"matched": bool(matched), "matched_address": matched_address, "lat": lat, "lon": lon}


def _store(conn, address: str, result: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO geocode_cache (address, matched, matched_address, lat, lon) "
        "VALUES (?, ?, ?, ?, ?)",
        (address, int(result["matched"]), result["matched_address"], result["lat"], result["lon"]),
    )


def _batch_request(addresses: list[str]) -> dict[str, dict]:
    """Matches for one batch, keyed by address. Misses and ties are left out
    for the caller to retry one at a time."""
    upload = io.StringIO()
    # The whole address goes in the street column; the service parses it as
    # well as it does separate street/city/state/zip fields.
    csv.writer(upload).writerows([i, address, "", "", ""] for i, address in enumerate(addresses))
    response = requests.post(
        BATCH_URL,
        data={"benchmark": BENCHMARK},
        files={"addressFile": ("addresses.csv", upload.getvalue(), "text/csv")},
        timeout=300,
    )
    response.raise_for_status()
    found = {}
    # Rows: id, input, Match/No_Match/Tie, match type, matched address, "lon,lat", ...
    for row in csv.reader(io.StringIO(response.text)):
        if len(row) >= 6 and row[2] == "Match" and row[0].isdigit() and int(row[0]) < len(addresses):
            lon, lat = (float(v) for v in row[5].split(","))
            found[addresses[int(row[0])]] = {
                "matched": True, "matched_address": row[4], "lat": lat, "lon": lon,
            }
    return found


def _single_request(address: str) -> dict:
    response = requests.get(
        ONE_ADDRESS_URL,
        params={"address": address, "benchmark": BENCHMARK, "format": "json"},
        timeout=15,
    )
    response.raise_for_status()
    matches = response.json().get("result", {}).get("addressMatches", [])
    time.sleep(REQUEST_DELAY_SECONDS)
    if not matches:
        return dict(UNMATCHED)
    match = matches[0]
    return {
        "matched": True,
        "matched_address": match["matchedAddress"],
        "lat": match["coordinates"]["y"],
        "lon": match["coordinates"]["x"],
    }


def geocode_many(addresses: list[str], conn: sqlite3.Connection, on_progress=None) -> dict[str, dict]:
    """Returns {address: {matched, matched_address, lat, lon}} for every
    non-blank address given. on_progress(done, total) is called as batches
    finish, counting distinct addresses."""
    unique = list(dict.fromkeys(a for a in addresses if a))
    results = {}
    for address in unique:
        cached = _from_cache(conn, address)
        if cached is not None:
            results[address] = cached
    misses = [a for a in unique if a not in results]
    done = len(unique) - len(misses)
    if on_progress:
        on_progress(done, len(unique))

    for start in range(0, len(misses), BATCH_SIZE):
        chunk = misses[start:start + BATCH_SIZE]
        try:
            found = _batch_request(chunk)
        except requests.RequestException:
            found = {}  # the whole batch failed; every address gets retried below
        for address in chunk:
            result = found.get(address) or _single_request(address)
            _store(conn, address, result)
            results[address] = result
        conn.commit()  # once per batch, not per address
        done += len(chunk)
        if on_progress:
            on_progress(done, len(unique))
    return results
