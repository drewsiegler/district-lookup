"""Helpers in the map-building script. That script needs the heavy mapping
toolchain (requirements-build.txt), so these skip when it isn't installed."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("geopandas", reason="map-building tools not installed (requirements-build.txt)")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_gpkg  # noqa: E402


@pytest.mark.parametrize("value, pattern, expected", [
    ("Trustee Area C1", r"Trustee Area C(\d+)", "1"),   # Oak Grove: C is the map's letter
    ("Area 3", r"Area (\d+)", "3"),
    (None, r"(\d+)", None),
])
def test_extract_number(value, pattern, expected):
    assert build_gpkg.extract_number(value, pattern, "file.geojson") == expected


def test_extract_number_stops_the_build_on_a_mismatch():
    with pytest.raises(SystemExit, match="file.geojson.*'Zone B'"):
        build_gpkg.extract_number("Zone B", r"Area (\d+)", "file.geojson")


def test_only_trustee_groups_default_to_ta_format():
    assert build_gpkg.default_format("elementary_trustee_area") == "TA{}"
    assert build_gpkg.default_format("council_district") is None


@pytest.mark.parametrize("value, expected", [
    (None, None), ("x", "x"), (True, True), (3, 3), (2.5, 2.5), (float("nan"), None),
])
def test_json_safe(value, expected):
    assert build_gpkg.json_safe(value) == expected


def test_json_safe_turns_timestamps_into_text():
    import pandas as pd
    assert build_gpkg.json_safe(pd.Timestamp("2024-01-02")) == "2024-01-02 00:00:00"


def test_round_coords_nested():
    assert build_gpkg.round_coords([[[-121.123456789, 37.987654321]]]) == [[[-121.123457, 37.987654]]]
