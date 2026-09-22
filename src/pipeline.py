"""The lookup itself, shared by the command line (main.py) and the app
window (web.py): geocode each person's address, find their districts, and
sort them into results / needs-review.
"""

import csv
from pathlib import Path

from geocode import geocode, _get_cache_conn
from input_table import build_address, build_label, normalize
from layers import coverage_layer_ids
from lookup import lookup_point

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
RESULTS_PATH = OUTPUT_DIR / "results.csv"
REVIEW_PATH = OUTPUT_DIR / "needs_review.csv"


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
        on_row=None) -> dict:
    """Looks up every person. on_row(index, total, label, address) is called
    before each lookup, for progress reporting. Returns the rows and headers
    for both output files."""
    layer_columns = [layer["id"] for layer in layers]
    coverage_ids = coverage_layer_ids(layers)
    # The input's own columns come through untouched; anything this tool adds
    # gets a "_lookup" suffix where the input already uses that name, so a
    # contact list's own "city" column and the official city both survive.
    added = unique_headers(["matched_address", "lat", "lon"] + layer_columns, source_columns)
    fieldnames = source_columns + list(added.values())

    results, review = [], []
    cache_conn = _get_cache_conn()
    try:
        for i, person in enumerate(people, start=1):
            address = build_address(person, roles)
            if on_row:
                on_row(i, len(people), build_label(person, roles), address)
            geo = geocode(address, conn=cache_conn) if address else {
                "matched": False, "matched_address": None, "lat": None, "lon": None,
            }

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
    finally:
        cache_conn.close()

    return {
        "fieldnames": fieldnames,
        "review_fieldnames": ["review_reason", "address_searched"] + fieldnames,
        "results": results,
        "review": review,
    }


def write_outputs(outcome: dict) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, fields, rows in (
        (RESULTS_PATH, outcome["fieldnames"], outcome["results"]),
        (REVIEW_PATH, outcome["review_fieldnames"], outcome["review"]),
    ):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return RESULTS_PATH, REVIEW_PATH
