# Maintaining District Lookup

For whoever adds district maps and keeps the tool running. Using it is covered in the [README](../README.md); what's covered so far is in [COVERAGE.md](../COVERAGE.md).

## How it works

- **Geocoding** — the free [U.S. Census Bureau geocoder](https://geocoding.geo.census.gov/) turns each address into lat/lon, U.S. addresses only. New addresses go to its batch service, 250 per request, at about 13 ms each; anything the batch doesn't match is retried one at a time, since the batch service occasionally reports spurious misses. Results are cached in `data/geocode_cache.sqlite`, so re-running a list never re-asks for an address already resolved.
- **Boundary storage** — each district map is a layer. `data/layers.json` is the registry: for each layer, which attribute holds its district name and how to write it.
- **Point-in-polygon matching** — Shapely checks each geocoded point against every registered layer, using each layer's spatial index; about 0.1 ms per person.

The build step (`scripts/build_gpkg.py`) turns the source files in `data/raw_geojson/` into two things:

- `data/districts/` — one plain GeoJSON file per layer in lat/lon, trimmed to the county plus a 1 km margin. Coordinates are snapped to 6 decimal places (about 10 cm) in a way that keeps every shape valid, and a source shape that isn't (an outline that crosses itself, or parts that overlap) is repaired first; the build names any file it repaired. This is what the app reads, so a lookup needs only Shapely and the standard library; loading all layers takes about 0.15 seconds. The files are deliberately uncompressed and rebuild byte-for-byte identically, so git stores only the layers that actually changed — adding a trustee map adds roughly its own compressed size to the repo's history, tens of KB.
- `data/districts.gpkg` — the same layers as a GeoPackage, for opening in QGIS to eyeball boundaries. Not committed.

## Setup for adding maps

The app itself needs only `requirements.txt`. Preparing maps also needs the mapping toolchain, which is far heavier (~250 MB, carries GDAL and PROJ):

```bash
pip install -r requirements-build.txt
python scripts/build_gpkg.py
```

The split is deliberate: the lookup only ever needs Shapely, so the app can be bundled for people who don't have Python installed, while GDAL stays on the machine where maps are prepared.

## Adding a district map

1. Drop the boundary file as GeoJSON into `data/raw_geojson/`.
2. Decide whether it's its own column or part of a shared one:
   - **Its own column** (the default) — a file covering one whole boundary type across the county, like the county supervisorial districts. Nothing to configure; it becomes a layer named after the file.
   - **A shared column** — anything where each agency's map is a separate file but they belong in one column. Add an entry to the right group in `data/layer_sources.json`, naming the file and the attribute holding the district number:
     - **City council maps** go in `council_district`, and also say which city they're for, spelled exactly as in the `City` column (e.g. `"San Jose"`, no accent):
       ```json
       {"file": "los_altos_council.geojson", "name_field": "DISTRICT", "city": "Los Altos"}
       ```
       A council district is only filled in when the address is inside that same city's official limits. So unincorporated county land gets a blank city *and* a blank council district, even where a city's map extends over it. It also stops a district number being borrowed from a neighboring city where two agencies draw a shared border a little differently. (San José's council map and the official city limits disagree by about a square mile in total, mostly along unincorporated pockets.)
     - **Trustee-area maps** go in one column per district type (`unified_trustee_area`, `elementary_trustee_area`, `high_school_trustee_area`, `community_college_trustee_area`), headed `Unified Trustee Area`, `Primary Trustee Area`, `Secondary Trustee Area` and `College Trustee Area` in results and written as `TA3` etc. — the district itself is already named in the column just before it. Say which district the file is for, spelled exactly as the Census names it in that column:
       ```json
       {"file": "campbell_union_hsd_trustee_areas.geojson", "name_field": "TRUSTEEARE",
        "district": "Campbell Union High School District"}
       ```
       Like council maps, an area is only filled in when the address is in that same district — so it's left blank outside it, never borrowed from a neighboring district where two agencies draw their shared border differently, and someone inside a district whose map has a hole is flagged for review instead of silently coming out blank. A new group name creates that column the first time it has a file, already set to the `TA#` format; give it a `"header"` in `data/layers.json`.
     - **Community college trustee-area maps** go in `community_college_trustee_area`. The Census doesn't map community college districts, so the `community_college_district` column before it is drawn from these same files: each college's outline is all of its trustee areas together, named by the entry's `"district"`, with the hairline gaps where neighboring areas don't quite meet closed. (`"district_outlines"` in `layer_sources.json` sets that up.) Spell the college's name the way you want it to appear in results:
       ```json
       {"file": "gavilan_jccd_trustee_areas.geojson", "name_field": "DISTRICT",
        "district": "Gavilan Joint Community College District"}
       ```
       So a college only gets named once its trustee map is in; until then both columns are blank for its residents.

     If a file spells its districts out in a longer string rather than a bare number, add `extract` — a regex whose first group is the number. Oak Grove's file says "Trustee Area C1" (the C is the adopted map's letter, not part of the area name), so:
     ```json
     {"file": "oak_grove_school_district_trustee_areas.geojson", "name_field": "AREA", "extract": "Trustee Area C(\\d+)"}
     ```
     A value that doesn't match stops the build and names the file and value.
3. Run `python scripts/build_gpkg.py`. It rebuilds `data/districts/` and `data/districts.gpkg` from scratch and syncs `data/layers.json` — new layers are added, layers whose file is gone are removed.
4. For a standalone layer, open `data/layers.json` and fill in its `name_field` — the attribute holding the district's name or number (the build prints each layer's attributes to help) — and its `header`, the column's heading in results. Shared columns are filled in automatically. New entries land at the end of the file; move them next to related entries if you want the output columns grouped, since output column order follows this file.

Re-run the build any time you add, replace, or remove a boundary file — existing registry entries keep their settings and order. Then run the tests and update [COVERAGE.md](../COVERAGE.md).

Some California districts are unified (K-12 in one district); others are split into separate elementary and high school districts covering the same ground. That's why those are separate columns, and why a split district's trustee map goes in the elementary or high school group, never both.

## How values are written

By default a column shows the `name_field` value as-is, under the layer's `label`. A layer's entry in `data/layers.json` can change both:

- `"header"` — the column's heading in results, like `"CA Assembly"`.
- `"agency"` and `"agency_header"`, set together — for agencies that split an area between them, each with its own map. Layers with the same `agency_header` share two columns instead of one each: `agency_header` heads a column naming which agency covers the address (its `agency`), and `header` the column with its district. The two open space agencies are set up this way: `Open Space District` says `Midpeninsula Regional Open Space District` or `Santa Clara Valley Open Space Authority`, and `District/Ward` says `Ward 1—Dir. Craig Gleason` or `D7`. An address where their maps overlap gets both, separated by a semicolon.

- `"format"` — a template where `{}` is the value, and `{:02d}` zero-pads a number to two digits. `"SD{:02d}"` turns TIGER's `"015"` into `SD15`.
- `"pattern"` — a regex with named groups, for when the pieces you want are buried in a longer value. The county layer uses one to turn "District 2 — Supervisor Betty Duong" into `D2—Sup. Betty Duong`.
- `"names"` — for a map that doesn't carry who holds each seat: a name for each value, keyed by the value as written, added after an em dash. Congress, State Senate and Assembly use it, turning `US-CA16` into `US-CA16—Rep. Sam Liccardo` and `SD10` into `SD10—Vacant`. A value with no name listed is written as it is, and a name for a value the map doesn't have stops the run. Council districts list names under each city, since every city numbers its districts from 1: `{"Campbell": {"3": "Cm. Dan Furtado"}}`. Update these after an election, when the new officeholders take office.
- `"coverage": true` — this layer's footprint is the whole area the tool covers (the county). Addresses outside it go to review as `outside_coverage_area`, and the build trims every other layer to it.
- `"must_match"` — ties a layer to the one beside it (council districts to `city`, trustee areas to their school district); see above.

A setting that doesn't fit a layer's values — a format, a pattern, an unknown attribute, a misspelled city or district, a shared column with mismatched headings — stops the run at startup with an error naming the layer, rather than writing bad values partway through a list.

## Where the Census layers come from

`unified_school_districts`, `elementary_school_districts`, `secondary_school_districts`, `us_congress`, `ca_state_senate`, `ca_state_assembly` and `city` aren't hand-sourced. They're the Census Bureau's [TIGER/Line shapefiles](https://www2.census.gov/geo/tiger/TIGER2025/) (2025 vintage, 119th Congress), downloaded statewide for California and cut down to the features that touch Santa Clara County before being added to `data/raw_geojson/`. A future vintage — after the next redistricting, say — needs the same treatment; statewide files are too large to commit as they are.

TIGER names some districts differently from common usage — "Los Altos Elementary School District" rather than "Los Altos School District", and it drops "High" from "Los Gatos-Saratoga Joint Union School District" and "Mountain View-Los Altos Union School District". Trustee-area entries have to use the TIGER spelling.

TIGER has only whole-district boundaries, never trustee areas: every school district is exactly one feature. Trustee areas are sourced district by district, like city council maps — see [COVERAGE.md](../COVERAGE.md).

## Running the tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

About 1.5 seconds, and no test touches the network: each one hands the app fixed coordinates for public buildings (city halls, a district office) instead of calling the Census geocoder, and any stray real request fails the test. The known-address tests assert the full district breakdown at each point, so a rebuilt map that moves someone into the wrong district shows up here. The rule tests — no council district on unincorporated land, no trustee area borrowed across a district border, a hole in a loaded map getting flagged — find their test points from the map data itself, so they follow the maps as they change, and skip with a note if the situation they test no longer exists. The map-building tests need `requirements-build.txt` and skip without it.

## Odds and ends

- The command line defaults to `data/people.csv` if you don't give it a path. Every `.csv` in the project is gitignored, with `data/people_contacts_example.csv` deliberately allowed back in, so a real list can't be committed by accident.
- If the launcher shows a generic script icon rather than the app icon, run `scripts/set_launcher_icon.sh` once. A custom file icon lives in the file's resource fork, which git doesn't carry across a clone.

## Releasing a new version

After adding or changing maps:

1. Bump `VERSION` in `src/about.py` (1.0.0 → 1.1.0), commit, and push.
2. Tag that commit with the same number plus a `v`, and push the tag:
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```
3. GitHub builds the apps for Mac (Apple silicon and Intel), Windows, and Linux/Chromebook (x64 and ARM), installs each one and runs its self-test, then makes a **draft** release with all of them attached. That takes about 15 minutes; watch it on the repo's **Actions** tab. If the tag doesn't match `VERSION`, the build stops and says so.
4. On the **Releases** page, open the draft, give it a plain-words title like "New Los Altos SD trustee areas", add a line about what changed above the download notes, and publish it.

Everyone running an older copy sees that title in a banner at the top of the lookup page the next time they open it, with a link to the release. Nobody sees a draft, so nothing reaches anyone until step 4.

To try a build without releasing anything, open **Actions → Build the apps → Run workflow**. The finished files are under that run's **Artifacts**.

The builds are set up in `packaging/` and `.github/workflows/build-apps.yml`. They're unsigned: there's no Apple Developer or Windows code-signing certificate, which is why the README walks people past the first-open warnings. If a file the app reads at runtime is ever added, list it in `datas` in `packaging/district_lookup.spec` too, or the installed apps won't have it; the self-test catches a missing map, page or icon.

## Project layout

```
district-lookup/
├── Start District Lookup.command   # double-click in Finder to open the app window
├── assets/
│   ├── AppIcon.icns         # every size, 16–1024 px: for the Mac app bundle and the launcher's Finder icon
│   ├── AppIcon.ico          # the same for Windows, 16–256 px
│   └── AppIcon.png          # 256 px, for the lookup page's header, browser tab, and Linux
├── data/
│   ├── raw_geojson/          # source boundary files, one .geojson per map
│   ├── layer_sources.json    # which council / trustee-area files feed each shared column, and which columns are drawn from their outlines
│   ├── layers.json           # registry: layer id -> label, column heading, name_field, and output settings
│   ├── districts/            # what the app reads: one GeoJSON file per layer
│   ├── districts.gpkg        # same layers as a GeoPackage, for QGIS (not committed)
│   ├── geocode_cache.sqlite  # cached address -> lat/lon lookups (not committed)
│   └── people_contacts_example.csv   # input template
├── docs/adding-maps.md      # this file
├── packaging/
│   ├── district_lookup.spec  # PyInstaller recipe for the installed app, every system
│   ├── macos/                # .dmg script and its "opening it the first time" note
│   ├── windows/              # Inno Setup installer script
│   ├── linux/                # .deb and .tar.gz script, desktop entry
│   └── release-notes.md      # "which file do I download?" text for each release
├── scripts/
│   ├── build_gpkg.py         # raw_geojson/ -> districts/ + .gpkg + registry
│   └── set_launcher_icon.sh  # puts the app icon on the launcher in Finder
├── src/
│   ├── launcher.py           # the installed app's start: its small window, and the build's self-test
│   ├── web.py                # the lookup page, served to your browser
│   ├── web_page.html         # that page
│   ├── about.py              # version number, update check, donation link
│   ├── app_paths.py          # where files are, from source or installed
│   ├── main.py               # the command line
│   ├── pipeline.py           # the lookup itself, shared by the window and the command line
│   ├── input_table.py        # reads the input list in whatever shape it arrives
│   ├── geocode.py            # addresses -> lat/lon in batches, with caching
│   ├── layers.py             # loads the registered layers from data/districts/
│   └── lookup.py             # point-in-polygon matching
├── tests/                   # python -m pytest; no network needed
├── COVERAGE.md              # which maps are in, which are still needed
├── .github/
│   ├── FUNDING.yml           # puts a Ko-fi "Sponsor" button on the GitHub page
│   └── workflows/build-apps.yml  # builds the apps and drafts a release for each version tag
├── AGENTS.md                # guidance for AI coding agents working on this repo
├── CLAUDE.md                # points Claude at AGENTS.md
├── requirements.txt         # what the app needs: shapely, requests
├── requirements-build.txt   # what adding maps needs: geopandas, GDAL, pandas
├── requirements-dev.txt     # what running the tests needs: pytest
└── requirements-package.txt # what building the apps needs: PyInstaller
```
