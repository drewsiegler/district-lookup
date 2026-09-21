"""Address -> (lat, lon) via the free U.S. Census Bureau geocoder, with a local
SQLite cache so re-running a batch never re-hits the API for an address
that's already been resolved."""

import sqlite3
import time
from pathlib import Path

import requests

CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "geocode_cache.sqlite"
REQUEST_DELAY_SECONDS = 0.2  # be polite to the free API on cache misses


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


def geocode(address: str, conn: sqlite3.Connection | None = None) -> dict:
    """Returns {input, matched, matched_address, lat, lon}. Uses/populates the
    on-disk cache; pass an open sqlite3 connection to reuse it across a batch
    instead of opening one per call."""
    owns_conn = conn is None
    conn = conn or _get_cache_conn()
    try:
        row = conn.execute(
            "SELECT matched, matched_address, lat, lon FROM geocode_cache WHERE address = ?",
            (address,),
        ).fetchone()
        if row is not None:
            matched, matched_address, lat, lon = row
            return {
                "input": address,
                "matched": bool(matched),
                "matched_address": matched_address,
                "lat": lat,
                "lon": lon,
            }

        response = requests.get(
            CENSUS_URL,
            params={
                "address": address,
                "benchmark": "Public_AR_Current",
                "format": "json",
            },
            timeout=15,
        )
        response.raise_for_status()
        matches = response.json().get("result", {}).get("addressMatches", [])
        time.sleep(REQUEST_DELAY_SECONDS)

        if not matches:
            conn.execute(
                "INSERT OR REPLACE INTO geocode_cache (address, matched, matched_address, lat, lon) "
                "VALUES (?, 0, NULL, NULL, NULL)",
                (address,),
            )
            conn.commit()
            return {"input": address, "matched": False, "matched_address": None, "lat": None, "lon": None}

        match = matches[0]
        matched_address = match["matchedAddress"]
        lon = match["coordinates"]["x"]
        lat = match["coordinates"]["y"]
        conn.execute(
            "INSERT OR REPLACE INTO geocode_cache (address, matched, matched_address, lat, lon) "
            "VALUES (?, 1, ?, ?, ?)",
            (address, matched_address, lat, lon),
        )
        conn.commit()
        return {"input": address, "matched": True, "matched_address": matched_address, "lat": lat, "lon": lon}
    finally:
        if owns_conn:
            conn.close()
