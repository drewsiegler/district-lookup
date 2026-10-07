"""Shared test setup.

No test talks to the Census geocoder. Real lookups are slow on purpose (an HTTP
round trip plus a 0.2s courtesy pause each) and fail whenever the network does,
so tests hand the app fixed coordinates instead — and any stray real request
fails the test rather than quietly making the suite slow and flaky.
"""

import sys
from pathlib import Path

import pytest
import requests
from shapely import union_all

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

import pipeline  # noqa: E402
from layers import load_layers  # noqa: E402

# Public buildings, geocoded once by the real Census service. Coordinates are
# what that service returned, so these exercise the same points real use does.
POINTS = {
    "tully_rd_san_jose": (37.32155542358, -121.82696202627),
    "campbell_city_hall": (37.288195597821, -121.944759236182),
    "gilroy_rosanna_st": (37.004937716141, -121.572038269657),
    "morgan_hill_peak_ave": (37.12590150574, -121.661881922298),
    "cupertino_city_hall": (37.31923968861, -122.029158712914),
    "los_altos_city_hall": (37.381396700712, -122.113976377067),
    "mountain_view_city_hall": (37.390033272844, -122.081436311181),
    "oak_grove_district_office": (37.232465839659, -121.786098911989),
    "san_jose_city_hall": (37.338163163635, -121.886224209159),
    "san_jose_usd_district_office": (37.334527255176, -121.912415657398),
    "san_francisco_city_hall": (37.778532096981, -122.418308756397),
    "stanford_campus": (37.4275, -122.1697),
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("A test tried to reach the network; use fake_geocoder instead.")
    monkeypatch.setattr(requests, "get", refuse)
    monkeypatch.setattr(requests, "post", refuse)


@pytest.fixture(scope="session")
def layers():
    """Every registered layer, loaded once for the whole run (~0.2s)."""
    return load_layers()


def layer_features(layers, layer_id):
    """(display value, must-match scope, geometry) for each feature of a layer."""
    layer = next(l for l in layers if l["id"] == layer_id)
    return list(zip(layer["display"], layer["scope"], layer["geometries"]))


def largest_piece(geometry):
    return max(getattr(geometry, "geoms", [geometry]), key=lambda g: g.area)


@pytest.fixture(scope="session")
def gilroy_gap(layers):
    """(lat, lon) inside Gilroy USD but outside its trustee-area map — the known
    hole at the district's eastern edge. Found from the data rather than
    hardcoded, so the test follows the maps; skips once the hole is fixed."""
    district = union_all([g for name, _, g in layer_features(layers, "unified_school_districts")
                          if name == "Gilroy Unified School District"])
    mapped = union_all([g for _, scope, g in layer_features(layers, "unified_trustee_area")
                        if scope == "Gilroy Unified School District"])
    gap = district.difference(mapped)
    if gap.is_empty:
        pytest.skip("Gilroy USD's trustee map now covers the whole district")
    point = largest_piece(gap).representative_point()
    return point.y, point.x


class _NoCache:
    def close(self):
        pass


@pytest.fixture
def fake_geocoder(monkeypatch):
    """Stands in for the Census geocoder. Register addresses on the returned
    dict as {address: (lat, lon)}; anything unregistered comes back unmatched,
    exactly as a real miss would. Also keeps tests away from the real
    geocode cache on disk."""
    known = {}

    def fake(addresses, conn, on_progress=None):
        results = {}
        for address in dict.fromkeys(a for a in addresses if a):
            if address in known:
                lat, lon = known[address]
                results[address] = {"matched": True, "matched_address": address.upper(),
                                    "lat": lat, "lon": lon}
            else:
                results[address] = {"matched": False, "matched_address": None,
                                    "lat": None, "lon": None}
        if on_progress:
            on_progress(len(results), len(results))
        return results

    monkeypatch.setattr(pipeline, "geocode_many", fake)
    monkeypatch.setattr(pipeline, "_get_cache_conn", _NoCache)
    return known
