"""Sorting people into results vs. needs-review, and what the output files
look like."""

import sys

import pipeline
from conftest import POINTS

ADDRESS_ROLES = {"street": "address", "name": "name"}


def run(rows, layers, columns=("name", "address"), roles=ADDRESS_ROLES):
    return pipeline.run([dict(r) for r in rows], list(columns), roles, layers)


def by_name(rows):
    return {r["name"]: r for r in rows}


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
    assert outcome["review"][0]["address_searched"] == "1 Nowhere Ln, Xyz, CA"
    assert outcome["review_fieldnames"][:2] == ["review_reason", "address_searched"]


def test_input_columns_come_through_untouched_and_first(layers, fake_geocoder):
    fake_geocoder["1660 Tully Rd, San Jose, CA 95122"] = POINTS["tully_rd_san_jose"]
    columns = ["First Name", "Street Address", "City", "State", "Zip", "Email"]
    roles = {"street": "Street Address", "city": "City", "state": "State", "zip": "Zip", "first": "First Name"}
    row = {"First Name": "Maria", "Street Address": "1660 Tully Rd", "City": "San Jose",
           "State": "CA", "Zip": "95122", "Email": "maria@example.org"}
    outcome = run([row], layers, columns, roles)

    assert outcome["fieldnames"][:len(columns)] == columns
    result = outcome["results"][0]
    assert {k: result[k] for k in columns} == row
    # Their own "City" survives; the official city is written beside it.
    assert "city" not in outcome["fieldnames"]
    assert result["city_lookup"] == "San Jose"


def test_unique_headers_ignores_case_and_punctuation():
    mapping = pipeline.unique_headers(["city", "lat"], ["City", "LAT", "Email"])
    assert mapping == {"city": "city_lookup", "lat": "lat_lookup"}


def test_csv_text_has_header_and_rows(layers, fake_geocoder):
    fake_geocoder["tully"] = POINTS["tully_rd_san_jose"]
    text = pipeline.csv_text(run([{"name": "A", "address": "tully"}], layers), "results")
    lines = text.splitlines()
    assert lines[0].startswith("name,address,matched_address")
    assert len(lines) == 2


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
