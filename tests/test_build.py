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


def _layer(*polygons):
    import geopandas as gpd
    from shapely.geometry import box
    return gpd.GeoDataFrame({"name": [str(i) for i in range(len(polygons))]},
                            geometry=[box(*p) for p in polygons], crs="EPSG:4326")


def test_layers_are_trimmed_to_the_county_plus_a_margin():
    county = _layer((-122.0, 37.0, -121.5, 37.5))
    statewide = _layer((-123.0, 36.0, -121.0, 38.0),    # straddles the county
                       (-118.0, 34.0, -117.5, 34.5))    # Los Angeles: nowhere near it
    registry = [{"id": "county", "coverage": True}]
    clipped = build_gpkg.clip_to_coverage({"county": county, "statewide": statewide}, registry)

    kept = clipped["statewide"]
    assert list(kept["name"]) == ["0"]                  # the far-away feature is dropped
    minx, miny, maxx, maxy = kept.total_bounds
    assert -122.02 < minx < -122.0 and 37.5 < maxy < 37.52   # county edge + ~1 km, no more


def test_without_a_coverage_layer_nothing_is_trimmed():
    layer = _layer((-123.0, 36.0, -121.0, 38.0))
    assert build_gpkg.clip_to_coverage({"x": layer}, [])["x"] is layer


def test_output_is_identical_for_identical_input(tmp_path, monkeypatch):
    monkeypatch.setattr(build_gpkg, "RUNTIME_DIR", tmp_path)
    frames = {"a": _layer((-122.0, 37.0, -121.5, 37.5))}
    build_gpkg.write_runtime_data(frames)
    first = (tmp_path / "a.json").read_bytes()
    build_gpkg.write_runtime_data(frames)
    assert (tmp_path / "a.json").read_bytes() == first


def test_layers_no_longer_built_are_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(build_gpkg, "RUNTIME_DIR", tmp_path)
    (tmp_path / "gone.json").write_text("{}")
    build_gpkg.write_runtime_data({"kept": _layer((0, 0, 1, 1))})
    assert sorted(p.name for p in tmp_path.iterdir()) == ["kept.json"]
