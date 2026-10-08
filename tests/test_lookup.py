"""Point-in-polygon lookups against the real boundary data in
data/districts/."""

import pytest
from shapely import union_all

from conftest import POINTS, largest_piece, layer_features as features
from layers import coverage_layer_ids
from lookup import lookup_point
from pipeline import review_reason_for


def at(layers, name):
    lat, lon = POINTS[name]
    return lookup_point(layers, lat, lon)


# --- Known addresses -------------------------------------------------------

def test_tully_road_the_original_example(layers):
    d = at(layers, "tully_rd_san_jose")
    assert d["city"] == "San Jose"
    assert d["council_district"] == "7"
    assert d["santa_clara_county_supervisorial"] == "D2—Sup. Betty Duong"
    assert d["us_congress"] == "US-CA16—Rep. Sam Liccardo"
    assert d["ca_state_senate"] == "SD15"
    assert d["ca_state_assembly"] == "AD25"
    assert d["elementary_school_districts"] == "Evergreen Elementary School District"
    assert d["secondary_school_districts"] == "East Side Union High School District"
    assert d["scc_board_of_education_trustee_areas"] == "TA7"
    assert d["midpeninsula_regional_open_space_district"] is None  # east of Midpen's boundary
    assert d["scvosa_director_districts"] == "D7"
    assert d["scv_water_board_districts"] == "D6"
    assert d["high_school_trustee_area"] == "TA3"
    assert d["community_college_district"] == "San Jose-Evergreen Community College District"
    assert d["community_college_trustee_area"] == "TA4"


@pytest.mark.parametrize("point, column, expected", [
    ("campbell_city_hall", "council_district", "3"),
    ("campbell_city_hall", "high_school_trustee_area", "TA3"),
    ("gilroy_rosanna_st", "council_district", "5"),
    ("gilroy_rosanna_st", "unified_trustee_area", "TA7"),
    ("san_jose_city_hall", "council_district", "3"),
    ("san_jose_city_hall", "unified_trustee_area", "TA3"),
    ("san_jose_usd_district_office", "unified_trustee_area", "TA2"),
    ("santa_clara_city_hall", "unified_trustee_area", "TA4"),
    ("morgan_hill_peak_ave", "unified_trustee_area", "TA3"),
    ("sunnyvale_city_hall", "elementary_trustee_area", "TA1"),
    ("moreland_district_office", "elementary_trustee_area", "TA3"),
    ("campbell_city_hall", "community_college_district", "West Valley-Mission Community College District"),
    ("campbell_city_hall", "community_college_trustee_area", "TA6"),
    ("oak_grove_district_office", "high_school_trustee_area", "TA2"),
    ("cupertino_city_hall", "community_college_district", "Foothill-De Anza Community College District"),
    ("cupertino_city_hall", "community_college_trustee_area", "TA4"),
    ("san_jose_city_hall", "community_college_trustee_area", "TA7"),
    ("morgan_hill_peak_ave", "council_district", "C"),
    ("los_altos_city_hall", "council_district", "4"),
    ("cupertino_city_hall", "high_school_trustee_area", "TA1"),
    ("mountain_view_city_hall", "high_school_trustee_area", "TA3"),
    ("los_altos_city_hall", "high_school_trustee_area", "TA4"),
    ("oak_grove_district_office", "elementary_trustee_area", "TA5"),
    ("campbell_city_hall", "elementary_trustee_area", "TA3"),
    ("campbell_city_hall", "scc_board_of_education_trustee_areas", "TA3"),
    ("oak_grove_district_office", "scc_board_of_education_trustee_areas", "TA4"),
    ("stanford_campus", "scc_board_of_education_trustee_areas", "TA1"),
    # Ward 2 on Midpen's 2011 map; the 2022 redistricting moved it to Ward 1.
    ("cupertino_city_hall", "midpeninsula_regional_open_space_district", "Ward 1"),
    ("stanford_campus", "midpeninsula_regional_open_space_district", "Ward 2"),
    ("campbell_city_hall", "scvosa_director_districts", "D4"),
    ("morgan_hill_peak_ave", "scvosa_director_districts", "D1"),
    ("gilroy_rosanna_st", "community_college_district", "Gavilan Joint Community College District"),
    ("gilroy_rosanna_st", "community_college_trustee_area", "TA4"),
    ("morgan_hill_peak_ave", "community_college_trustee_area", "TA2"),
    ("campbell_city_hall", "scv_water_board_districts", "D4"),
    ("santa_clara_city_hall", "us_congress", "US-CA17—Rep. Ro Khanna"),
    ("san_jose_city_hall", "us_congress", "US-CA18—Rep. Zoe Lofgren"),
    ("oak_grove_district_office", "us_congress", "US-CA19—Rep. Jimmy Panetta"),
    ("cupertino_city_hall", "scv_water_board_districts", "D5"),
    ("stanford_campus", "scv_water_board_districts", "D7"),
])
def test_known_districts(layers, point, column, expected):
    assert at(layers, point)[column] == expected


def test_open_space_agencies_split_the_county(layers):
    """Midpen covers the northwest and the Open Space Authority most of the
    rest, so an address gets one or the other. The City of Gilroy is outside
    both."""
    cupertino = at(layers, "cupertino_city_hall")
    assert cupertino["midpeninsula_regional_open_space_district"] == "Ward 1"
    assert cupertino["scvosa_director_districts"] is None
    gilroy = at(layers, "gilroy_rosanna_st")
    assert gilroy["midpeninsula_regional_open_space_district"] is None
    assert gilroy["scvosa_director_districts"] is None


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


def test_at_large_school_district_has_no_trustee_area(layers):
    # Cupertino Union and Palo Alto Unified elect their boards at-large.
    d = at(layers, "cupertino_city_hall")
    assert d["elementary_school_districts"] == "Cupertino Union Elementary School District"
    assert d["elementary_trustee_area"] is None
    d = at(layers, "stanford_campus")
    assert d["unified_school_districts"] == "Palo Alto Unified School District"
    assert d["unified_trustee_area"] is None


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


def test_gap_between_college_trustee_areas_is_flagged(layers):
    """The college district column is drawn from the colleges' own trustee
    maps, with the hairline gaps between neighboring areas closed. An address
    in one of those gaps has its college but no area, and goes to review
    rather than coming back with neither."""
    county = union_all([g for _, _, g in features(layers, "santa_clara_county_supervisorial")])
    colleges = union_all([g for _, _, g in features(layers, "community_college_district")])
    areas = union_all([g for _, _, g in features(layers, "community_college_trustee_area")])
    gap = colleges.difference(areas).intersection(county)
    if gap.is_empty:
        pytest.skip("no gaps between college trustee areas in current data")
    point = largest_piece(gap).representative_point()
    d = lookup_point(layers, point.y, point.x)
    assert d["community_college_district"] and d["community_college_trustee_area"] is None
    assert review_reason_for(layers, coverage_layer_ids(layers), d) == \
        "missing_community_college_trustee_area"
