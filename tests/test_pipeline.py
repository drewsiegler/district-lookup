"""Sorting people into results vs. needs-review, and what the output files
look like."""

import csv
import io
import re
import sys

import pytest
from shapely import union_all

import pipeline
from conftest import POINTS, largest_piece, layer_features

ADDRESS_ROLES = {"street": "address"}


def run(rows, layers, columns=("name", "address"), roles=ADDRESS_ROLES):
    return pipeline.run([dict(r) for r in rows], list(columns), roles, layers)


def by_name(rows):
    return {r["name"]: r for r in rows}


def written(outcome, which="results"):
    """The file as people see it, each row as {heading: value}."""
    reader = csv.reader(io.StringIO(pipeline.csv_text(outcome, which)))
    headings = next(reader)
    return [dict(zip(headings, row)) for row in reader]


def test_everyone_lands_in_exactly_one_file_with_the_right_reason(layers, fake_geocoder, gilroy_gap):
    fake_geocoder.update({
        "in county": POINTS["tully_rd_san_jose"],
        "out of county": POINTS["san_francisco_city_hall"],
        "gilroy gap": gilroy_gap,
    })
    outcome = run([
        {"name": "Clean", "address": "in county"},
        {"name": "Typo", "address": "not a real address"},
        {"name": "Moved away", "address": "out of county"},
        {"name": "Rural Gilroy", "address": "gilroy gap"},
    ], layers)

    assert set(by_name(outcome["results"])) == {"Clean"}
    reasons = {r["name"]: r["review_reason"] for r in outcome["review"]}
    assert reasons == {
        "Typo": "unmatched_address",
        "Moved away": "outside_coverage_area",
        "Rural Gilroy": "missing_unified_trustee_area",
    }


def test_district_with_no_map_loaded_yet_is_not_flagged(layers, fake_geocoder):
    # Tully Rd is in East Side Union HSD, whose trustee map isn't loaded — a
    # blank trustee area there is correct, not a gap to review.
    fake_geocoder["tully"] = POINTS["tully_rd_san_jose"]
    outcome = run([{"name": "A", "address": "tully"}], layers)
    assert len(outcome["results"]) == 1 and not outcome["review"]


def test_at_large_and_unincorporated_are_not_flagged(layers, fake_geocoder):
    fake_geocoder.update({"cupertino": POINTS["cupertino_city_hall"],
                          "stanford": POINTS["stanford_campus"]})
    outcome = run([{"name": "At-large", "address": "cupertino"},
                   {"name": "Unincorporated", "address": "stanford"}], layers)
    assert not outcome["review"]


def test_review_rows_show_exactly_what_was_searched(layers, fake_geocoder):
    outcome = run([{"name": "Typo", "address": "1 Nowhere Ln, Xyz, CA"}], layers)
    assert written(outcome, "review")[0]["Address Searched"] == "1 Nowhere Ln, Xyz, CA"


def test_input_columns_come_through_untouched_and_first(layers, fake_geocoder):
    fake_geocoder["1660 Tully Rd, San Jose, CA 95122"] = POINTS["tully_rd_san_jose"]
    columns = ["First Name", "Street Address", "City", "State", "Zip", "Email"]
    roles = {"street": "Street Address", "city": "City", "state": "State", "zip": "Zip"}
    row = {"First Name": "Maria", "Street Address": "1660 Tully Rd", "City": "San Jose",
           "State": "CA", "Zip": "95122", "Email": "maria@example.org"}
    outcome = run([row], layers, columns, roles)

    assert outcome["headers"][:len(columns)] == columns
    result = written(outcome)[0]
    assert {k: result[k] for k in columns} == row
    # Their own "City" survives; the official city is written beside it.
    assert outcome["headers"].count("City") == 1
    assert result["City (Lookup)"] == "San Jose"


def test_added_columns_are_named_apart_from_the_inputs_own():
    named = pipeline.name_added_columns({"city": "City", "lat": "Lat", "lon": "Lon"},
                                        ["CITY", "lat", "Email"])
    assert named == {
        "city": ("city", "City (Lookup)"),     # heading clashes, ignoring case
        "lat": ("lat_lookup", "Lat (Lookup)"),  # the key would overwrite theirs too
        "lon": ("lon", "Lon"),
    }


def test_output_headings(layers, fake_geocoder):
    # People's spreadsheets and mail merges depend on these, so a change here
    # should be deliberate.
    fake_geocoder["tully"] = POINTS["tully_rd_san_jose"]
    outcome = run([{"name": "A", "address": "tully"}, {"name": "B", "address": "nowhere"}], layers)
    results = pipeline.csv_text(outcome, "results").splitlines()[0].split(",")
    assert results == [
        "name", "address", "Matched Address", "Lat", "Lon", "City", "Council District",
        "Supervisor District", "US Congress", "CA State Senate", "CA Assembly",
        "Unified School District", "Unified Trustee Area",
        "Elementary School District", "Primary Trustee Area",
        "High School District", "Secondary Trustee Area",
        "Community College District", "College Trustee Area",
        "County Board of Education", "Open Space District", "District/Ward", "SCV Water District",
    ]
    review = pipeline.csv_text(outcome, "review").splitlines()[0].split(",")
    assert review == ["Review Reason", "Address Searched"] + results


def test_each_trustee_area_is_written_under_its_own_heading(layers, fake_geocoder):
    fake_geocoder["tully"] = POINTS["tully_rd_san_jose"]
    row = written(run([{"name": "A", "address": "tully"}], layers))[0]
    assert {h: v for h, v in row.items() if h.endswith("Trustee Area")} == {
        "Unified Trustee Area": "",  # no unified district here
        "Primary Trustee Area": "",  # Evergreen Elementary elects at-large
        "Secondary Trustee Area": "TA3",
        "College Trustee Area": "TA4",
    }


def test_open_space_agencies_share_two_columns(layers, fake_geocoder):
    fake_geocoder.update({"cupertino": POINTS["cupertino_city_hall"],
                          "tully": POINTS["tully_rd_san_jose"],
                          "gilroy": POINTS["gilroy_rosanna_st"]})
    outcome = run([{"name": "Midpen", "address": "cupertino"},
                   {"name": "Authority", "address": "tully"},
                   {"name": "Neither", "address": "gilroy"}], layers)
    rows = by_name(written(outcome))
    assert {name: (r["Open Space District"], r["District/Ward"]) for name, r in rows.items()} == {
        "Midpen": ("Midpeninsula Regional Open Space District", "Ward 1—Dir. Craig Gleason"),
        "Authority": ("Santa Clara Valley Open Space Authority", "D7"),
        "Neither": ("", ""),
    }


def test_address_on_the_line_between_open_space_agencies_gets_both(layers, fake_geocoder):
    """The two open space maps overlap by a sliver along the line they share.
    An address there is written with both agencies rather than losing one."""
    midpen = union_all([g for _, _, g in
                        layer_features(layers, "midpeninsula_regional_open_space_district")])
    authority = union_all([g for _, _, g in layer_features(layers, "scvosa_director_districts")])
    overlap = midpen.intersection(authority)
    if overlap.area == 0:
        pytest.skip("the open space maps no longer overlap")
    point = largest_piece(overlap).representative_point()
    fake_geocoder["on the line"] = (point.y, point.x)
    row = written(run([{"name": "A", "address": "on the line"}], layers))[0]
    assert row["Open Space District"] == \
        "Midpeninsula Regional Open Space District; Santa Clara Valley Open Space Authority"
    assert re.fullmatch(r"Ward \d—Dir\. [^;]+; D\d", row["District/Ward"])


def test_rerunning_a_needs_review_file_gives_fresh_reasons(layers, fake_geocoder):
    # Fixing addresses in the needs-review file and running it again is the
    # usual next step. Its old reason stays as it was, under this version's
    # heading or 1.0.0's lowercase one; the new reason is written beside it.
    for old_heading in ("Review Reason", "review_reason"):
        row = {old_heading: "outside_coverage_area", "name": "A", "address": "still a typo"}
        outcome = run([row], layers, [old_heading, "name", "address"])
        assert outcome["reasons"] == ["unmatched_address"]
        written_row = written(outcome, "review")[0]
        assert written_row["Review Reason (Lookup)"] == "unmatched_address"
        assert written_row[old_heading] == "outside_coverage_area"


def test_written_files_open_correctly_in_excel(tmp_path, layers, fake_geocoder):
    fake_geocoder["tully"] = POINTS["tully_rd_san_jose"]
    outcome = run([{"name": "A", "address": "tully"}], layers)
    results, review = pipeline.write_outputs(outcome, tmp_path / "r.csv", tmp_path / "n.csv")
    raw = results.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")         # the marker Excel needs for UTF-8
    assert "D2—Sup. Betty Duong".encode("utf-8") in raw
    assert review.exists()


def test_command_line_writes_results_beside_the_input_not_the_project(tmp_path, monkeypatch,
                                                                       layers, fake_geocoder):
    import main
    fake_geocoder["1660 Tully Rd, San Jose, CA 95122"] = POINTS["tully_rd_san_jose"]
    listing = tmp_path / "my list.csv"
    listing.write_text('name,address\nA,"1660 Tully Rd, San Jose, CA 95122"\n', encoding="utf-8")
    monkeypatch.setattr(main, "load_layers", lambda: layers)
    monkeypatch.setattr(sys, "argv", ["main.py", str(listing)])

    main.main()

    assert (tmp_path / "my list.results.csv").exists()
    assert (tmp_path / "my list.needs_review.csv").exists()
