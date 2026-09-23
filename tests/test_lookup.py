"""Point-in-polygon lookups against the real boundary data in
data/districts.json.gz."""

import pytest
from shapely import union_all

from conftest import POINTS, layer_features as features
from lookup import lookup_point


def at(layers, name):
    lat, lon = POINTS[name]
    return lookup_point(layers, lat, lon)


# --- Known addresses -------------------------------------------------------

def test_tully_road_the_original_example(layers):
    d = at(layers, "tully_rd_san_jose")
    assert d["city"] == "San Jose"
    assert d["council_district"] == "7"
    assert d["santa_clara_county_supervisorial"] == "D2—Sup. Betty Duong"
    assert d["us_congress"] == "US-CA16"
    assert d["ca_state_senate"] == "SD15"
    assert d["ca_state_assembly"] == "AD25"
    assert d["elementary_school_districts"] == "Evergreen Elementary School District"
    assert d["secondary_school_districts"] == "East Side Union High School District"


@pytest.mark.parametrize("point, column, expected", [
    ("campbell_city_hall", "council_district", "3"),
    ("campbell_city_hall", "high_school_trustee_area", "TA3"),
    ("gilroy_rosanna_st", "council_district", "5"),
    ("gilroy_rosanna_st", "unified_trustee_area", "TA7"),
    ("morgan_hill_peak_ave", "council_district", "C"),
    ("cupertino_city_hall", "high_school_trustee_area", "TA1"),
    ("oak_grove_district_office", "elementary_trustee_area", "TA5"),
])
def test_known_districts(layers, point, column, expected):
    assert at(layers, point)[column] == expected


def test_at_large_city_has_a_city_but_no_council_district(layers):
    d = at(layers, "cupertino_city_hall")
    assert d["city"] == "Cupertino"
    assert d["council_district"] is None


def test_unincorporated_land_has_no_city_or_council_district(layers):
    d = at(layers, "stanford_campus")
    assert d["city"] is None and d["council_district"] is None
    assert d["santa_clara_county_supervisorial"] == "D5—Sup. Margaret Abe-Koga"


def test_outside_the_county_nothing_matches(layers):
    assert not any(at(layers, "san_francisco_city_hall").values())


def test_district_without_a_trustee_map_yet_is_blank(layers):
    # East Side Union HSD's map hasn't been loaded; Tully Rd is in it.
    assert at(layers, "tully_rd_san_jose")["high_school_trustee_area"] is None


# --- The must-match rule ---------------------------------------------------

def test_council_map_over_unincorporated_land_is_ignored(layers):
    """San José's council map extends over unincorporated county pockets. There,
    the official city is blank, so the council district must be too."""
    sj_map = union_all([g for _, scope, g in features(layers, "council_district") if scope == "San Jose"])
    sj_city = union_all([g for name, _, g in features(layers, "city") if name == "San Jose"])
    for piece in sorted(getattr(sj_map.difference(sj_city), "geoms", []), key=lambda g: -g.area):
        point = piece.representative_point()
        d = lookup_point(layers, point.y, point.x)
        if d["city"] is None:
            assert d["council_district"] is None
            return
    pytest.skip("San José's council map no longer extends past its city limits")


def test_trustee_area_is_never_borrowed_across_a_district_border(layers):
    """Where two districts' maps overlap along a shared border, only the area
    belonging to the district named in the column beside it is used."""
    by_district = {}
    for name, scope, geom in features(layers, "high_school_trustee_area"):
        by_district.setdefault(scope, []).append((name, geom))
    districts = list(by_district)
    for i, a in enumerate(districts):
        for b in districts[i + 1:]:
            overlap = union_all([g for _, g in by_district[a]]).intersection(
                union_all([g for _, g in by_district[b]]))
            for piece in getattr(overlap, "geoms", [overlap]):
                if piece.is_empty or piece.area == 0:
                    continue
                point = piece.representative_point()
                claims = {scope: name for scope in (a, b) for name, g in by_district[scope]
                          if g.contains(point)}
                if len(claims) == 2 and claims[a] != claims[b]:
                    d = lookup_point(layers, point.y, point.x)
                    assert d["high_school_trustee_area"] == claims[d["secondary_school_districts"]]
                    return
    pytest.skip("no overlapping trustee maps with different area numbers in current data")


def test_hole_in_a_loaded_trustee_map_leaves_the_area_blank(layers, gilroy_gap):
    """Gilroy USD's map stops short of the district's eastern edge. Inside that
    gap the district is known but the trustee area isn't."""
    d = lookup_point(layers, *gilroy_gap)
    assert d["unified_school_districts"] == "Gilroy Unified School District"
    assert d["unified_trustee_area"] is None
