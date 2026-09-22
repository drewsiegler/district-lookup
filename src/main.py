"""Command-line entry point. For the app window instead, run src/web.py.

Reads the input list (see input_table.py for the shapes it accepts), geocodes
each address, and looks it up against every registered district layer. Every
column of the input comes through to the output untouched, with the district
columns added on the end.

Two files are written next to your input list — never inside this folder,
since they carry the same names and addresses it does. For list.csv you get
list.results.csv and list.needs_review.csv. Each person lands in exactly one:

- .results.csv — everyone who geocoded to somewhere inside the area.
- .needs_review.csv — everyone who needs a human look first:
  - unmatched_address: the address failed to geocode.
  - outside_coverage_area: it geocoded to somewhere outside every layer
    marked "coverage": true in data/layers.json (e.g. the county). Either the
    address needs correcting, or the person belongs on a different list.
  - missing_<layer> (e.g. missing_council_district): it's inside a city or
    district whose map is loaded, but no area was found — a gap between that
    agency's own map and its official boundary, so it has to be looked up by
    hand.

Usage:
    python src/main.py [path/to/people.csv]

Defaults to data/people.csv if no path is given.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pipeline
from input_table import describe_roles, read_people
from layers import load_layers

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


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

    def report(i, total, label, address):
        print(f"[{i}/{total}] {label or '(no name)'} — {address}")

    outcome = pipeline.run(people, source_columns, roles, layers, on_row=report)
    # Written beside your list, not inside this folder — results carry the same
    # names and addresses as the input, and shouldn't sit in a git repo.
    results_path, review_path = pipeline.write_outputs(
        outcome,
        input_path.with_name(f"{input_path.stem}.results.csv"),
        input_path.with_name(f"{input_path.stem}.needs_review.csv"),
    )

    print(f"\nWrote {len(outcome['results'])} row(s) to {results_path}")
    print(f"Flagged {len(outcome['review'])} row(s) for follow-up in {review_path}")


if __name__ == "__main__":
    main()
