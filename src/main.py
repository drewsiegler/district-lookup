"""CLI entry point: reads the input list (see input_table.py for the shapes it
accepts), geocodes each address, and looks it up against every registered
district layer. Every column of the input comes through to the output
untouched, with the district columns added on the end. Each person lands in
exactly one output file:

- output/results.csv — everyone who geocoded to somewhere inside the area.
- output/needs_review.csv — everyone who needs a human look first:
  - unmatched_address: the address failed to geocode.
  - outside_coverage_area: it geocoded to somewhere outside every layer
    marked "coverage": true in data/layers.json (e.g. the county). Either the
    address needs correcting, or the person belongs on a different list.
  - missing_<layer> (e.g. missing_council_district): it's inside a city that
    layer has a map for, but no district was found — a gap between the city's
    own map and its official limits, so the district has to be looked up by
    hand.

Usage:
    python src/main.py [path/to/people.csv]

Defaults to data/people.csv if no path is given.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geocode import geocode, _get_cache_conn
from input_table import build_address, build_label, describe_roles, normalize, read_people
from layers import coverage_layer_ids, load_layers
from lookup import lookup_point

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


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


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR / "people.csv"
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        people, source_columns, roles = read_people(input_path)
    except ValueError as err:
        print(err)
        sys.exit(1)
    print(f"Read {len(people)} row(s) from {input_path} — {describe_roles(roles)}\n")

    layers = load_layers()
    if not layers:
        print(
            "No usable layers registered yet. Add boundary files to data/raw_geojson/, "
            "run scripts/build_gpkg.py, then set each layer's name_field in data/layers.json."
        )

    layer_columns = [layer["id"] for layer in layers]
    coverage_ids = coverage_layer_ids(layers)
    # The input's own columns come through untouched; anything this tool adds
    # gets a "_lookup" suffix where the input already uses that name, so a
    # contact list's own "city" column and the official city both survive.
    added = unique_headers(["matched_address", "lat", "lon"] + layer_columns, source_columns)
    fieldnames = source_columns + list(added.values())
    review_fieldnames = ["review_reason", "address_searched"] + fieldnames

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "results.csv"
    review_path = OUTPUT_DIR / "needs_review.csv"

    result_count = 0
    review_rows = []
    cache_conn = _get_cache_conn()
    try:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i, person in enumerate(people, start=1):
                address = build_address(person, roles)
                print(f"[{i}/{len(people)}] {build_label(person, roles) or '(no name)'} — {address}")
                geo = geocode(address, conn=cache_conn) if address else {
                    "matched": False, "matched_address": None, "lat": None, "lon": None,
                }

                row = dict(person)
                row[added["matched_address"]] = geo["matched_address"]
                row[added["lat"]] = geo["lat"]
                row[added["lon"]] = geo["lon"]

                review_reason = None
                if not geo["matched"]:
                    review_reason = "unmatched_address"
                    districts = {}
                else:
                    districts = lookup_point(layers, geo["lat"], geo["lon"]) if layers else {}
                    if coverage_ids and not any(districts.get(cid) for cid in coverage_ids):
                        review_reason = "outside_coverage_area"
                    else:
                        review_reason = next((
                            f"missing_{layer['id']}" for layer in layers
                            if layer["must_match"]
                            and districts.get(layer["must_match"]["layer"]) in layer["mapped"]
                            and not districts.get(layer["id"])
                        ), None)

                for col in layer_columns:
                    row[added[col]] = districts.get(col)

                if review_reason:
                    review_rows.append({"review_reason": review_reason, "address_searched": address, **row})
                else:
                    writer.writerow(row)
                    result_count += 1
    finally:
        cache_conn.close()

    with open(review_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=review_fieldnames)
        writer.writeheader()
        writer.writerows(review_rows)

    print(f"\nWrote {result_count} row(s) to {output_path}")
    print(f"Flagged {len(review_rows)} row(s) for follow-up in {review_path}")


if __name__ == "__main__":
    main()
