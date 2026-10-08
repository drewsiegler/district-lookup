# AGENTS.md

Guidance for AI coding agents working in this repo. The human docs are the source of truth, split by audience: [README.md](README.md) for people running lookups, [docs/adding-maps.md](docs/adding-maps.md) for how it works and how to add maps (read it before touching anything in `data/`), and [COVERAGE.md](COVERAGE.md) for what's loaded and what's still needed.

## What this is

A tool that runs on the user's own computer. It takes a list of people and addresses, geocodes each address with the free U.S. Census geocoder, and uses point-in-polygon matching to find every district the address falls in: council, supervisor, Congress, State Senate and Assembly, school and community college districts and their trustee areas, County Board of Education, Midpen wards, Open Space Authority districts and Valley Water board districts. It covers Santa Clara County. The users are community organizers, not developers, mostly on Macs. They use a browser page (`src/web.py`) or the command line (`src/main.py`).

`src/` is flat modules, not a package: each entry point puts `src/` on `sys.path` and imports siblings directly (`import pipeline`). The project layout is at the end of docs/adding-maps.md.

## Commands

Python 3.10 or newer. Work inside the repo's `.venv` (`source .venv/bin/activate`).

- Install the app: `pip install -r requirements.txt`
- Tests: `pip install -r requirements-dev.txt`, then `python -m pytest` (about 1.5 s, no network needed)
- One test file: `python -m pytest tests/test_lookup.py`
- Rebuild maps: `pip install -r requirements-build.txt`, then `python scripts/build_gpkg.py`. `tests/test_build.py` skips unless these build dependencies are installed.
- Run the app window: `python src/web.py` (serves on 127.0.0.1:8734). CLI: `python src/main.py path/to/list.csv`
- Build the installed app locally: `pip install -r requirements-package.txt`, then `python -m PyInstaller --noconfirm --clean packaging/district_lookup.spec`. Check it with `"dist/District Lookup.app/Contents/MacOS/District Lookup" --self-test` (macOS) or the equivalent executable elsewhere.

No linter or formatter is configured, so match the surrounding style: type hints on signatures, lines kept to about 100–110 characters, and module docstrings that explain why the code works the way it does.

Tests and the build must pass before a change counts as done.

## Privacy rules (the point of the app, so non-negotiable)

- **Never open, print, copy or commit a real contact list or its results.** `data/people.csv` and every other `.csv` except `data/people_contacts_example.csv` hold real people's details. For sample input, use the example file or made-up rows at public buildings.
- **Results never land in the project folder.** The app window keeps them in memory and hands them over only as downloads. The CLI writes them next to the input list. Keep it that way.
- **The only thing that leaves the machine is addresses**, sent to the Census geocoder, never names, emails or phones. The one other network call is the app window's update check (`src/about.py`): when it opens, it asks GitHub's API for the latest release's version number, sends nothing about the list, and shows nothing if it fails. Don't add other network calls, analytics, error reporting, or CDN scripts or fonts. `src/web_page.html` stays self-contained.
- The web server binds to `127.0.0.1` only.
- `data/geocode_cache.sqlite` (it holds addresses) and `*.gpkg` are gitignored. Don't force-add them.

## Dependencies

The runtime stays at `shapely` + `requests`: small pure wheels with nothing to compile, so PyInstaller can bundle it into apps for people who don't have Python. The installed app's small window uses Tk from the standard library (`tkinter`), imported only inside `src/launcher.py`. PyInstaller belongs only in `requirements-package.txt`. GeoPandas, GDAL, pyogrio and pandas belong only in `requirements-build.txt` and `scripts/`. Never import them from `src/`. **Ask before adding any dependency**, to any requirements file.

## Tests

- No test touches the network. `tests/conftest.py` makes any `requests.get`/`post` fail the test. Use the `fake_geocoder` fixture, with coordinates from `POINTS`.
- `POINTS` holds public buildings only (city halls, district offices, a campus), never private homes.
- Known-address tests assert exact districts at those points. When adding or updating a map, add an assertion to `tests/test_lookup.py` at a public building inside it. If the map replaces an older one, choose a point whose district changed, so the old map can't come back unnoticed (see the Cupertino City Hall / Midpen case).
- Rule tests (no council district on unincorporated land, no trustee area borrowed across a border, gaps get flagged) find their points from the map data and skip once the situation no longer exists. Follow that pattern rather than hardcoding points for them.

## Generated files

- `data/districts/*.json` is build output, committed so the app needs no GIS tools. Never hand-edit it; rebuild instead. The build is byte-for-byte deterministic, so after a rebuild `git status` should show changes only in the layers you touched. If other layers changed, stop and find out why.
- `data/layers.json` is only partly generated. The build adds and removes entries, but `header`, `name_field`, `format`, `pattern`, `coverage`, `must_match`, `agency` and `agency_header` are hand-set and preserved. Output column order and headings follow this file, and a layer with `must_match` has to come after the layer it references.

## Adding or updating a district map

The full procedure is in docs/adding-maps.md. In short:

1. Put the GeoJSON in `data/raw_geojson/`.
2. A council or trustee-area map gets an entry in `data/layer_sources.json`:
   - City names are spelled as in the `City` column (`"San Jose"`, no accent).
   - School district names are spelled the way Census TIGER spells them, which differs from common usage. For example, "Los Gatos-Saratoga Joint Union School District" has no "High".
   - A split district's trustee map goes in the elementary or the high school group, never both.
   - The Census doesn't map community college districts, so the `community_college_district` column is drawn from the college trustee maps themselves (`district_outlines`). A college's `"district"` is its name as it appears in results.
3. Run `python scripts/build_gpkg.py`. For a standalone layer, fill in `name_field`, `header` (and `format` if needed) in `data/layers.json`.
4. Add a known-address test (above) and run the tests.
5. Update COVERAGE.md, including its "Updated" date. For a new column, also update the README's district list and its table of columns.

**Check a map's vintage before using it.** Outdated copies circulate on open-data portals: the 2011 Midpen wards nearly shipped in place of the 2022 map, which would have put about 59 sq mi of the county in the wrong ward. Confirm the adoption date or Census year from the source agency, and record the source and adoption date in COVERAGE.md. When the agency doesn't publish its map, count 2020 Census population per area from the PL 94-171 block file (www2.census.gov, under programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171; the Census API now needs a key). Areas within a few percent of each other were drawn from the 2020 Census.

Boundary data comes from free public sources only: Census TIGER, agency GIS portals, and public records requests. Don't propose paid data.

To check whether a school board elects at-large or by trustee area, read that district's whole page on the Registrar of Voters site. The summary line can lag behind a transition noted further down (see COVERAGE.md).

## Behavior worth preserving

- A blank district is not an error. At-large cities, unincorporated land, each open space agency covering only part of the county, and trustee maps that aren't loaded yet all produce blanks. Only a gap inside a loaded map goes to review as `missing_<layer>`.
- Council districts and trustee areas are filled in only inside the city or school district that drew them (`must_match`). They are never borrowed from a neighbor across a slightly different border.
- The input's own columns are never overwritten. When a heading collides (ignoring case and punctuation), the added column gets a ` (Lookup)` suffix; a mailing city and the official city disagreeing is real information.
- Output rows are keyed internally (layer ids, `matched_address`), apart from the headings written to the file, which come from `header` in `data/layers.json`. Two agencies that split an area (the open space agencies) share an agency column and a district column, set by `agency`/`agency_header` in `data/layers.json`.
- Bad registry config stops the run at startup with an error naming the layer. It never writes bad values partway through a list.
- The Census batch service reports some spurious misses, so unmatched addresses are retried one at a time. Keep that fallback.
- Output CSVs are written `utf-8-sig` so Excel shows accents and the em dash correctly.
- Shapely takes `(lon, lat)`. `POINTS` and the geocoder use `(lat, lon)`.
- `Start District Lookup.command` must stay executable. Its Finder icon lives in a resource fork git doesn't carry, which is why `scripts/set_launcher_icon.sh` exists.

## Writing

README.md, COVERAGE.md, page text and error messages are read by organizers. Use plain language, no jargon, and say what to do next. When code changes, update whichever of the three docs covers it, and put new material in the doc for its audience.

## Installed apps

`.github/workflows/build-apps.yml` builds the Mac (Apple silicon and Intel), Windows, and Linux/Chromebook (x64 and ARM) apps on GitHub's machines with `packaging/district_lookup.spec`. It installs each one and runs `--self-test`, and for a `v*` tag it makes a draft release. The apps are unsigned on purpose (no paid certificates), so don't add signing steps without asking.

- The installed app starts at `src/launcher.py`: a small Tk window stands in for the Terminal, and closing it quits, after a warning if results haven't been downloaded. Running from source (`src/web.py`) keeps the Terminal behavior.
- `src/app_paths.py` decides where files are. Read-only files come from the project folder, or from inside the app when installed. The geocode cache stays in `data/` from source, but an installed app keeps it in the per-user app data folder, so updates don't wipe it.
- Anything the app reads at runtime must be listed in `datas` in the spec, or installed apps won't have it.
- A second launch finds the first copy on its port (`web.already_running`) and just opens its page.

## Versions and releases

`VERSION` in `src/about.py` is the app's version, shown in the app window's footer. A release bumps it there and nowhere else, and is published on GitHub tagged `v` + VERSION (`v1.1.0`), so the update check can compare numbers. The release's title is shown in the app's update banner, so make it say what changed in plain words ("New Los Altos SD trustee areas"). Ask before pushing a version tag or publishing a release, like any push. The steps are in docs/adding-maps.md.

## Commits and boundaries

- Commit subjects are a plain-English imperative sentence with no prefix, like "Add Midpeninsula Regional Open Space District wards". The body explains what changed and why, with concrete numbers where they matter: square miles, MB, seconds.
- The repo is public on GitHub. **Ask before pushing.**
- Also ask before:
  - adding dependencies
  - removing boundary files
  - changing output column names or how values are written (`TA3`, `SD15`, `US-CA16`), since people's spreadsheets depend on them
  - touching LICENSE or the README's License and Trademark sections. The code is AGPL-3.0, the boundary data isn't covered by that license, and "District Lookup" is a trademark.
