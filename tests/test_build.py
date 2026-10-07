"""Helpers in the map-building script. That script needs the heavy mapping
toolchain (requirements-build.txt), so these skip when it isn't installed."""

import json
import re
import sys
from pathlib import Path

import pytest
from shapely.geometry import MultiPolygon, Point, Polygon, box, mapping, shape

gpd = pytest.importorskip("geopandas", reason="map-building tools not installed (requirements-build.txt)")
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


def _layer(*polygons):
    import geopandas as gpd
    from shapely.geometry import box
    return gpd.GeoDataFrame({"name": [str(i) for i in range(len(polygons))]},
                            geometry=[box(*p) for p in polygons], crs="EPSG:4326")


def _written_geometries(directory, layer_name):
    text = (directory / f"{layer_name}.json").read_text(encoding="utf-8")
    return text, [shape(f["geometry"]) for f in json.loads(text)["features"]]


def _raw_file(tmp_path, *geometries):
    path = tmp_path / "areas.geojson"
    features = [{"type": "Feature", "properties": {"AREA": i + 1}, "geometry": mapping(g)}
                for i, g in enumerate(geometries)]
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return path


def test_coordinates_are_written_to_six_decimal_places(tmp_path, monkeypatch):
    monkeypatch.setattr(build_gpkg, "RUNTIME_DIR", tmp_path)
    build_gpkg.write_runtime_data({"a": _layer((-121.123456789, 37.987654321, -121.0, 38.0))})
    text, [written] = _written_geometries(tmp_path, "a")
    assert (-121.123457, 37.987654) in written.exterior.coords
    assert not re.search(r"\.\d{7}", text)


def test_snapping_to_six_decimals_keeps_shapes_valid(tmp_path, monkeypatch):
    """A notch whose tip comes within 5 cm of the far edge. Rounding each point
    on its own puts the tip on that edge, so the outline touches itself, as
    happened in San José's council map. Snapping keeps it a valid shape."""
    notched = Polygon([(-121.60, 37.0), (-121.59, 37.0), (-121.59, 37.01), (-121.5949, 37.01),
                       (-121.595, 37.0000004), (-121.5951, 37.01), (-121.60, 37.01)])
    rounded = Polygon([(round(x, 6), round(y, 6)) for x, y in notched.exterior.coords])
    assert notched.is_valid and not rounded.is_valid

    monkeypatch.setattr(build_gpkg, "RUNTIME_DIR", tmp_path)
    frame = gpd.GeoDataFrame({"name": ["1"]}, geometry=[notched], crs="EPSG:4326")
    build_gpkg.write_runtime_data({"a": frame})
    text, [written] = _written_geometries(tmp_path, "a")
    assert written.is_valid
    assert written.area == pytest.approx(notched.area, rel=1e-4)
    assert not re.search(r"\.\d{7}", text)


def test_shapes_that_cross_themselves_are_repaired_on_load(tmp_path):
    """A bow tie, an outline crossing itself, becomes the two triangles it
    draws. Unrepaired, its area even comes out as zero."""
    bow_tie = Polygon([(-121.6, 37.0), (-121.5, 37.1), (-121.5, 37.0), (-121.6, 37.1)])
    square = box(-121.4, 37.0, -121.3, 37.1)
    assert bow_tie.area == 0

    gdf = build_gpkg.load_and_normalize(_raw_file(tmp_path, bow_tie, square))
    assert gdf.geometry.is_valid.all()
    repaired = gdf.geometry.iloc[0]
    assert repaired.geom_type == "MultiPolygon" and len(repaired.geoms) == 2
    assert repaired.area == pytest.approx(0.005)
    assert gdf.geometry.iloc[1].equals_exact(square, 0)   # valid shapes are left alone


@pytest.mark.parametrize("covered_twice", [
    # parts that overlap, as in San José Unified's trustee areas
    MultiPolygon([box(-121.6, 37.0, -121.5, 37.1), box(-121.57, 37.0, -121.47, 37.1)]),
    # one outline drawn as a five-pointed star, which goes around its middle twice
    Polygon([(-121.55, 37.1), (-121.579389, 37.009549), (-121.502447, 37.065451),
             (-121.597553, 37.065451), (-121.520611, 37.009549)]),
])
def test_ground_a_shape_covers_twice_stays_inside_it(tmp_path, covered_twice):
    """An address there is in the district. A repair that alternates inside and
    outside at every line would make the star's middle a hole."""
    assert not covered_twice.is_valid

    repaired = build_gpkg.load_and_normalize(_raw_file(tmp_path, covered_twice)).geometry.iloc[0]
    assert repaired.is_valid and repaired.geom_type == "Polygon"   # no stray lines
    assert repaired.contains(Point(-121.55, 37.05))


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


def test_district_outline_is_its_areas_together_without_the_slivers():
    import geopandas as gpd
    from shapely.geometry import box
    merged = gpd.GeoDataFrame(
        {"district_name": ["1", "2", "1"], "district": ["A", "A", "B"]},
        geometry=[box(-121.60, 37.0, -121.59, 37.01),
                  box(-121.58998, 37.0, -121.58, 37.01),   # ~2 m from area 1
                  box(-121.50, 37.0, -121.49, 37.01)],
        crs="EPSG:4326")
    outline = build_gpkg.build_outline_layer("college_trustee_area", merged)
    assert list(outline["district"]) == ["A", "B"]
    a = outline.geometry.iloc[0]
    assert a.geom_type == "Polygon"                      # the 2 m gap is closed...
    assert a.bounds == pytest.approx((-121.60, 37.0, -121.58, 37.01), abs=1e-7)   # ...the edge isn't moved


def test_district_outline_needs_every_file_to_name_its_district():
    import geopandas as gpd
    from shapely.geometry import box
    merged = gpd.GeoDataFrame({"district_name": ["1"], "district": [None]},
                              geometry=[box(0, 0, 1, 1)], crs="EPSG:4326")
    with pytest.raises(SystemExit, match="'college_trustee_area' needs a \"district\""):
        build_gpkg.build_outline_layer("college_trustee_area", merged)
