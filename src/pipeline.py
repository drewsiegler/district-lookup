"""The lookup itself, shared by the command line (main.py) and the app
window (web.py): geocode each person's address, find their districts, and
sort them into results / needs-review.
"""

import csv
import io
from pathlib import Path

from geocode import UNMATCHED, _get_cache_conn, geocode_many
from input_table import build_address, normalize
from layers import coverage_layer_ids
from lookup import lookup_point


def unique_headers(keys: list[str], source_columns: list[str]) -> dict[str, str]:
    """Output headers for the columns this tool adds, suffixed where the input
    file already uses that name. Ignores case and punctuation when comparing,
    so a contact list's "City" column doesn't sit next to a bare "city"."""
    taken = {normalize(header) for header in source_columns}
    mapping = {}
    for key in keys:
        header = key
        while normalize(header) in taken:
            header += "_lookup"
        mapping[key] = header
        taken.add(normalize(header))
    return mapping


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
    layer_columns = [layer["id"] for layer in layers]
    coverage_ids = coverage_layer_ids(layers)
    # The input's own columns come through untouched; anything this tool adds
    # gets a "_lookup" suffix where the input already uses that name, so a
    # contact list's own "city" column and the official city both survive.
    added = unique_headers(["matched_address", "lat", "lon"] + layer_columns, source_columns)
    fieldnames = source_columns + list(added.values())

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
        row[added["matched_address"]] = geo["matched_address"]
        row[added["lat"]] = geo["lat"]
        row[added["lon"]] = geo["lon"]

        if not geo["matched"]:
            reason, districts = "unmatched_address", {}
        else:
            districts = lookup_point(layers, geo["lat"], geo["lon"]) if layers else {}
            reason = review_reason_for(layers, coverage_ids, districts)

        for col in layer_columns:
            row[added[col]] = districts.get(col)

        if reason:
            review.append({"review_reason": reason, "address_searched": address, **row})
        else:
            results.append(row)

    return {
        "fieldnames": fieldnames,
        "review_fieldnames": ["review_reason", "address_searched"] + fieldnames,
        "results": results,
        "review": review,
    }


def csv_text(outcome: dict, which: str) -> str:
    """One output file as text. The app window keeps results in memory and
    hands them over as a download, so a list of real people's addresses is
    never written anywhere on its own."""
    fields = outcome["fieldnames"] if which == "results" else outcome["review_fieldnames"]
    rows = outcome[which]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def write_outputs(outcome: dict, results_path: Path, review_path: Path) -> tuple[Path, Path]:
    for path, which in ((results_path, "results"), (review_path, "review")):
        path.parent.mkdir(parents=True, exist_ok=True)
        # utf-8-sig so Excel reads accented names and the em dash correctly
        path.write_text(csv_text(outcome, which), encoding="utf-8-sig", newline="")
    return results_path, review_path
