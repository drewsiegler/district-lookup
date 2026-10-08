"""The lookup itself, shared by the command line (main.py) and the app
window (web.py): geocode each person's address, find their districts, and
sort them into results / needs-review.

Each row is a dict keyed by column: the input's own column names, then a key
for each column this tool adds (a layer id, "matched_address"). The headings
written to the file are kept apart from those keys. They're set in
data/layers.json, so rewording one changes the file and nothing else.
"""

import csv
import io
from pathlib import Path

from geocode import UNMATCHED, _get_cache_conn, geocode_many
from input_table import build_address, normalize
from layers import coverage_layer_ids
from lookup import lookup_point

# Headings for the columns added besides the districts, by key.
MATCH_COLUMNS = {"matched_address": "Matched Address", "lat": "Lat", "lon": "Lon"}
REVIEW_COLUMNS = {"review_reason": "Review Reason", "address_searched": "Address Searched"}


def shared_keys(layer: dict) -> tuple[str, str]:
    """Keys of the two columns a layer shares with the other agencies under its
    agency_header: which agency, then its district."""
    return f"agency:{layer['agency_header']}", f"district:{layer['agency_header']}"


def district_columns(layers: list[dict]) -> dict[str, str]:
    """{key: heading} for the district columns, in registry order. Each layer
    gets its own column, keyed by its id, except agencies that split an area
    between them (the two open space agencies): they share two columns."""
    columns = {}
    for layer in layers:
        if layer["agency"]:
            agency_key, district_key = shared_keys(layer)
            columns.setdefault(agency_key, layer["agency_header"])
            columns.setdefault(district_key, layer["header"])
        else:
            columns[layer["id"]] = layer["header"]
    return columns


def district_values(layers: list[dict], districts: dict) -> dict:
    """{key: value} for one address's district columns."""
    values = {}
    for layer in layers:
        value = districts.get(layer["id"])
        if not layer["agency"]:
            values[layer["id"]] = value
            continue
        agency_key, district_key = shared_keys(layer)
        values.setdefault(agency_key, None)
        values.setdefault(district_key, None)
        if value:
            # Neighboring agencies' maps can overlap by a sliver along the line
            # they share (the open space maps by about 0.04 sq mi). An address
            # right on it gets both, in registry order, rather than one dropped.
            values[agency_key] = "; ".join(filter(None, [values[agency_key], layer["agency"]]))
            values[district_key] = "; ".join(filter(None, [values[district_key], value]))
    return values


def name_added_columns(columns: dict[str, str],
                       source_columns: list[str]) -> dict[str, tuple[str, str]]:
    """{column: (key, heading)} for the columns this tool adds, kept apart from
    the input's own. A heading gets " (Lookup)" where the input already uses
    that name, ignoring case and punctuation, so a contact list's "City" column
    and the official city both survive under names that tell them apart. A key
    gets "_lookup" where it's exactly an input column's name, so neither value
    overwrites the other."""
    taken_keys = set(source_columns)
    taken_headings = {normalize(header) for header in source_columns}
    named = {}
    for column, heading in columns.items():
        key = column
        while key in taken_keys:
            key += "_lookup"
        taken_keys.add(key)
        while normalize(heading) in taken_headings:
            heading += " (Lookup)"
        named[column] = (key, heading)
    return named


def review_reason_for(layers: list[dict], coverage_ids: list[str], districts: dict) -> str | None:
    if coverage_ids and not any(districts.get(cid) for cid in coverage_ids):
        return "outside_coverage_area"
    return next((
        f"missing_{layer['id']}" for layer in layers
        if layer["must_match"]
        and districts.get(layer["must_match"]["layer"]) in layer["mapped"]
        and not districts.get(layer["id"])
    ), None)


def run(people: list[dict], source_columns: list[str], roles: dict, layers: list[dict],
        on_progress=None) -> dict:
    """Looks up every person. on_progress(done, total) reports geocoding
    progress in distinct addresses — the only slow step; the district lookups
    that follow take a fraction of a millisecond each. Returns the rows and
    headers for both output files."""
    coverage_ids = coverage_layer_ids(layers)
    # The input's own columns come through untouched; anything this tool adds
    # is named so it can't collide with them (see name_added_columns).
    added_columns = MATCH_COLUMNS | district_columns(layers)
    named = name_added_columns(REVIEW_COLUMNS | added_columns, source_columns)
    key = {column: named_key for column, (named_key, _) in named.items()}
    fieldnames = source_columns + [key[column] for column in added_columns]
    headers = source_columns + [named[column][1] for column in added_columns]

    addresses = [build_address(person, roles) for person in people]
    cache_conn = _get_cache_conn()
    try:
        geocoded = geocode_many(addresses, cache_conn, on_progress=on_progress)
    finally:
        cache_conn.close()

    results, review = [], []
    for person, address in zip(people, addresses):
        geo = geocoded.get(address, UNMATCHED)
        row = dict(person)
        row[key["matched_address"]] = geo["matched_address"]
        row[key["lat"]] = geo["lat"]
        row[key["lon"]] = geo["lon"]

        if not geo["matched"]:
            reason, districts = "unmatched_address", {}
        else:
            districts = lookup_point(layers, geo["lat"], geo["lon"]) if layers else {}
            reason = review_reason_for(layers, coverage_ids, districts)

        for column, value in district_values(layers, districts).items():
            row[key[column]] = value

        if reason:
            review.append({key["review_reason"]: reason, key["address_searched"]: address, **row})
        else:
            results.append(row)

    return {
        "fieldnames": fieldnames,
        "headers": headers,
        "review_fieldnames": [key[column] for column in REVIEW_COLUMNS] + fieldnames,
        "review_headers": [named[column][1] for column in REVIEW_COLUMNS] + headers,
        "results": results,
        "review": review,
        "reasons": sorted({row[key["review_reason"]] for row in review}),
    }


def csv_text(outcome: dict, which: str) -> str:
    """One output file as text. The app window keeps results in memory and
    hands them over as a download, so a list of real people's addresses is
    never written anywhere on its own."""
    prefix = "" if which == "results" else "review_"
    fields, headers = outcome[f"{prefix}fieldnames"], outcome[f"{prefix}headers"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\r\n")
    writer.writerow(dict(zip(fields, headers)))  # headings, not the keys behind them
    writer.writerows(outcome[which])
    return buffer.getvalue()


def write_outputs(outcome: dict, results_path: Path, review_path: Path) -> tuple[Path, Path]:
    for path, which in ((results_path, "results"), (review_path, "review")):
        path.parent.mkdir(parents=True, exist_ok=True)
        # utf-8-sig so Excel reads accented names and the em dash correctly
        path.write_text(csv_text(outcome, which), encoding="utf-8-sig", newline="")
    return results_path, review_path
