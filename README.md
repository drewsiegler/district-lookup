# District Lookup

Give it a CSV of names and addresses; it geocodes each address, checks it against every custom boundary map you've loaded (city council districts, school districts, anything you have a GeoJSON for), and writes one row per person with a column per district type. A custom, growable version of what a registrar of voters' office uses internally.

Built as a Python CLI, following the plan from [this design conversation](https://claude.ai/share/442797d6-ffc8-4d31-883f-d9cd4b18fd5c):

- **Geocoding** — the free [U.S. Census Bureau geocoder](https://geocoding.geo.census.gov/) turns each address into lat/lon, U.S. addresses only. Results are cached in `data/geocode_cache.sqlite` so re-running a batch never re-hits the API for an address you've already resolved.
- **Boundary storage** — every district map lives as its own layer inside `data/districts.gpkg`, a single GeoPackage file (SQLite under the hood) that GeoPandas reads and writes natively, and that you can open in QGIS to eyeball boundaries. `data/layers.json` is the registry: for each layer, which column holds its district name.
- **Point-in-polygon matching** — Shapely checks each geocoded point against every registered layer at once, using each layer's spatial index.

The same build step also writes `data/districts.json.gz` — the same boundaries as plain GeoJSON in lat/lon. That's what the app actually reads, so a lookup needs only Shapely and the standard library. Loading all 12 layers takes about 0.2 seconds.

## Setup

Needs Python 3. To **run** lookups, that's all you need:

```bash
cd district-lookup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

That installs Shapely and requests, about 58 MB, nothing that has to be compiled. The prepared boundary data (`data/districts.json.gz`, 2.2 MB) is in the repo, so you can look addresses up straight away.

To **add or update boundary maps** you also need the mapping toolchain, which is far heavier (~250 MB, carries GDAL and PROJ):

```bash
pip install -r requirements-build.txt
python scripts/build_gpkg.py
```

The split is deliberate: the lookup itself only ever needs Shapely, so the app can be bundled for people who don't have Python installed, while GDAL stays on the maintainer's machine where the maps are prepared.

## Adding a district map

1. Drop the boundary file as GeoJSON into `data/raw_geojson/`.
2. Decide whether it's its own column or part of a shared one:
   - **Its own column** (the default) — a file covering one whole boundary type across the county, like the county supervisorial districts. Nothing to configure; it becomes a layer named after the file.
   - **A shared column** — anything where each agency's map is a separate file but they belong in one column. Add an entry to the right group in `data/layer_sources.json`, naming the file and the column holding the district number:
     - **City council maps** go in `council_district`, and also say which city they're for, spelled exactly as in the `city` column (e.g. `"San Jose"`, no accent):
       ```json
       {"file": "los_altos_council.geojson", "name_field": "DISTRICT", "city": "Los Altos"}
       ```
       A council district is only filled in when the address is inside that same city's official limits. So unincorporated county land gets a blank city *and* a blank council district, even where a city's map extends over it. It also stops a district number from being borrowed from a neighboring city where two agencies draw the shared border a little differently. (San José's council map and the official city limits disagree by about a square mile in total, mostly along unincorporated pockets.)
     - **Trustee-area maps** go in one column per district type (`unified_trustee_area`, `elementary_trustee_area`, `high_school_trustee_area`, and later `community_college_trustee_area`), written as `TA3` etc. — the district itself is already named in the school district column just before it. Say which district the file is for, spelled exactly as the Census names it in that column:
       ```json
       {"file": "campbell_union_hsd_trustee_areas.geojson", "name_field": "TRUSTEEARE",
        "district": "Campbell Union High School District"}
       ```
       Like the council maps, an area is only filled in when the address is in that same district — so it's left blank outside it, never borrowed from a neighboring district where two agencies draw their shared border differently, and someone inside a district whose map has a hole is flagged for review instead of silently coming out blank.
       A new group name (e.g. `unified_trustee_area`) creates that column the first time it has a file, already set to the `TA#` format.

     If a file spells its districts out in a longer string rather than a bare number, add `extract` — a regex whose first group is the number. Oak Grove's file says "Trustee Area C1" (the C is the adopted map's letter, not part of the area name), so:
     ```json
     {"file": "oak_grove_school_district_trustee_areas.geojson", "name_field": "AREA", "extract": "Trustee Area C(\\d+)"}
     ```
     A value that doesn't match stops the build and names the file and value.
3. Run:
   ```bash
   python scripts/build_gpkg.py
   ```
   This rebuilds `data/districts.gpkg` and `data/districts.json.gz` from scratch and syncs `data/layers.json` — new layers are added, layers whose file is gone are removed.
4. For a standalone layer, open `data/layers.json` and fill in its `name_field` — the column holding the district's name or number (the build script prints each layer's columns to help). Shared trustee-area columns are filled in automatically. New entries land at the end of the file; move them next to related entries if you want the output columns grouped, since output column order follows this file.

Re-run `scripts/build_gpkg.py` any time you add, replace, or remove a boundary file — existing registry entries keep their settings and order.

### How values are written in the output

By default a column shows the `name_field` value as-is. A layer's entry in `data/layers.json` can reshape it:

- `"format"` — a template where `{}` is the value, and `{:02d}` zero-pads a number to two digits. `"SD{:02d}"` turns TIGER's `"015"` into `SD15`.
- `"pattern"` — a regex with named groups, for when the pieces you want are buried in a longer value. The county layer uses one to turn "District 2 — Supervisor Betty Duong" into `D2—Sup. Betty Duong`.

Current conventions: `city` is the city/town name and `council_district` is the bare district number (Morgan Hill uses letters `A`–`D`); county `D2—Sup. Betty Duong`, Congress `US-CA16`, State Senate `SD15`, Assembly `AD25`, trustee areas `TA3`. A format that doesn't fit a layer's values stops the run at startup with an error naming the layer, rather than writing bad values partway through a batch.

## Running a lookup

Two ways: the app window, or the command line. Both do exactly the same work and write the same files.

### The app window

Double-click **Start District Lookup.command** in Finder, or run:

```bash
python src/web.py
```

It opens a page in your browser where you can drop a file, pick one from Finder, or paste a list straight in, then click Start. It shows progress as it goes and gives you download buttons at the end. Leave the small Terminal window open while you're using it; closing it shuts the app down.

**Results are never written to disk here.** They're held in memory and handed over only when you click Download, so a list of real people's names and addresses can't be left sitting in the project folder — or committed by accident. Download before starting another lookup; the next one replaces them.

Nothing is uploaded anywhere. The page is served by your own computer, reachable only from it, and your list never leaves the machine — the only thing that goes out is one address at a time to the Census geocoder, exactly as the command line does.

The first time you double-click the launcher, macOS may say it can't verify the developer. Right-click it and choose **Open** instead, then **Open** again to confirm. You only need to do that once.

If the launcher shows a generic script icon rather than the app icon, run `scripts/set_launcher_icon.sh` once. A custom file icon lives in the file's resource fork, which git doesn't carry across a clone.

### The command line

```bash
python src/main.py data/people.csv
```

### What the input can look like

Point it at whatever list you already have — no need to reshape it first. It reads `.csv` and `.txt`, comma, tab, semicolon or pipe separated, straight out of Excel ("CSV UTF-8"), Numbers, or Google Sheets.

**A contact export with the address split across columns** — the usual case. See `data/people_contacts_example.csv`:

```
First Name,Last Name,Street Address,Street Address 2,City,State,Zip,Email,Phone Number
Maria,Gonzalez,1660 Tully Rd,Apt 12,San Jose,CA,95122,maria@example.org,408-555-0101
```

Those get stitched into "1660 Tully Rd, San Jose, CA 95122" for the lookup. It recognizes the usual names for each part (`Street Address`, `Address`, `Address Line 1`, `Mailing Address`; `City`; `State`; `Zip`, `ZIP Code`, `Postal Code`; and `Name` or `First Name`/`Last Name`), in any capitalization or spacing. When the run starts it prints which columns it used, so a wrong guess is obvious immediately.

**One address per line in a `.txt`**, optionally with a name before a `|`:

```
1660 Tully Rd, San Jose, CA 95122
Alex Lee | 70 N First St, Campbell, CA 95008
```

**A simple `name,address` sheet** — what `data/people.csv` uses.

Two things worth knowing:

- **Apartment and unit lines are kept but not searched.** The Census geocoder often fails to match an address carrying one, and it isn't needed to place a point on a map. `Street Address 2` still comes through to the output untouched.
- **Your columns are never overwritten.** If your file has its own `City` column, the official city this tool looks up is written as `city_lookup` beside it. That's deliberate: a mailing city of "San Jose" can be unincorporated county land, and the two columns disagreeing is real information.

### What comes out

Every column of your input comes back in the output, in its original order and spelling, with the lookup columns added on the end. So the name, email and phone stay in their own fields and the file is ready to work from. Each person lands in exactly one of two files:

- **results** — everyone whose address resolved to somewhere inside the county, with `matched_address`, `lat`, `lon`, and one column per registered layer.
- **needs review** — everyone who needs a human look first, with the same columns plus a `review_reason` and `address_searched` (exactly what was sent to the geocoder, which usually shows why it failed). Once an address is corrected, re-run and that person moves over to the results file.

From the app window these come as downloads. From the command line they're written next to your input list — `list.csv` produces `list.results.csv` and `list.needs_review.csv` — so they land wherever your list lives rather than inside this folder. Every `.csv` in the project is gitignored as a backstop, with the one example template deliberately allowed back in.

The outputs are written so Excel shows characters like the em dash in `D2—Sup.` correctly.

The reasons:

- `unmatched_address` — the geocoder couldn't resolve the address at all. Usually a typo, a PO box, or a landmark name instead of a street address.
- `outside_coverage_area` — it geocoded fine, but landed outside every layer marked `"coverage": true` in `data/layers.json` (currently the county supervisorial layer, since it covers the whole county with no gaps). Either the address is wrong, or that person genuinely lives outside the area and belongs on a different list.
- `missing_council_district`, `missing_unified_trustee_area`, and the like — the address is inside a city or school district whose map is loaded, but that map doesn't cover the spot, so the district needs looking up by hand. These are gaps between an agency's own map and its official boundary: about 1.3 sq mi in San José, a tenth of a square mile or less in each other city, and about 78 sq mi at the eastern edge of Gilroy USD. Places with no map loaded at all — at-large cities, districts whose trustee map you don't have yet, unincorporated land — are *not* flagged; blank is the right answer there.

Defaults to `data/people.csv` if you don't pass a path.

## Project layout

```
district-lookup/
├── Start District Lookup.command   # double-click in Finder to open the app window
├── assets/
│   ├── AppIcon.icns         # for the Mac app bundle, and the launcher's Finder icon
│   └── AppIcon.appiconset/  # the same icon at every size; the app window uses the 256px one
├── data/
│   ├── raw_geojson/          # boundary files you add, one .geojson at a time
│   ├── layer_sources.json    # which council / trustee-area files feed each shared column
│   ├── layers.json           # registry: layer id -> label, name_field, optional format/pattern/coverage
│   ├── districts.json.gz     # what the app reads: boundaries as plain GeoJSON
│   ├── districts.gpkg        # same layers as a GeoPackage, for QGIS (not in the repo)
│   ├── geocode_cache.sqlite  # cached address -> lat/lon lookups
│   ├── people.csv            # your input list (any of the shapes above)
│   └── people_contacts_example.csv   # template: address split across columns
├── scripts/
│   ├── build_gpkg.py         # raw_geojson/ -> districts.json.gz + .gpkg + registry
│   └── set_launcher_icon.sh  # puts the app icon on the launcher in Finder
├── src/
│   ├── web.py                # the app window (a page served to your browser)
│   ├── web_page.html         # that page
│   ├── pipeline.py           # the lookup itself, shared by the window and the CLI
│   ├── input_table.py        # reads the input list in whatever shape it arrives
│   ├── geocode.py            # address -> lat/lon, with caching
│   ├── layers.py             # loads registered layers from the .gpkg
│   ├── lookup.py             # point-in-polygon matching
│   └── main.py               # reads the input list, writes results beside it
├── requirements.txt         # what the app needs: shapely, requests
└── requirements-build.txt   # what adding maps needs: geopandas, GDAL, pandas
```

## A note on split school districts

Some California districts are unified (K-12 in one district); others split into separate elementary and high school districts covering the same ground. Give those two separate layers (e.g. `elementary_districts` and `high_school_districts`) rather than one, so an address correctly returns both instead of colliding on a single column.

## Where the school/Congress/Senate/Assembly layers come from

`unified_school_districts`, `elementary_school_districts`, `secondary_school_districts`, `us_congress`, `ca_state_senate`, and `ca_state_assembly` aren't hand-sourced — they're the U.S. Census Bureau's [TIGER/Line shapefiles](https://www2.census.gov/geo/tiger/TIGER2025/) (2025 vintage, 119th Congress), which already contain every one of these as complete, authoritative, national-coverage datasets. Each was downloaded statewide for California and filtered down to the features that intersect Santa Clara County. Re-run that filter (see git history / ask for the snippet) if a future TIGER vintage needs pulling in, e.g. after the next redistricting cycle.

TIGER names some districts slightly differently than common usage — e.g. "Los Altos Elementary School District" instead of "Los Altos School District", and it drops "High" from "Los Gatos-Saratoga Joint Union School District" / "Mountain View-Los Altos Union School District". Same districts, just their TIGER-registered names.

**TIGER only gives the whole-district boundary, not trustee areas.** Confirmed by checking: all 16 unified, 25 elementary, and 7 high school district features are exactly one polygon per district — no internal subdivisions. Many CA school boards (particularly larger districts, post-CVRA) elect board members by trustee area rather than at-large, and those sub-district boundaries aren't part of Census geography at all — same category as city council districts and community college districts below: needs sourcing per district (the district's own site, county Board of Education, or Registrar of Voters).

## Coverage (Santa Clara County, updated 2026-09-15)

**Countywide, from Census TIGER (no manual sourcing needed):** county supervisorial, U.S. Congress, CA State Senate, CA State Assembly, unified/elementary/high-school districts.

**Municipal council districts, sourced by hand so far:** San José, Santa Clara, Campbell, Morgan Hill, Sunnyvale, Gilroy — all feeding the `council_district` column. The `city` column covers all 15 cities/towns in the county (official Census city limits); for the at-large cities below, `city` is the whole story and `council_district` stays blank.

- **Has a district layer:** San José, Santa Clara, Campbell, Morgan Hill, Sunnyvale, Gilroy
- **Pending — recently switched to districts, map requested by email:** Los Altos
- **At-large — `city` is the whole story:** Los Gatos, Milpitas, Mountain View, Los Altos Hills, Monte Sereno, Palo Alto, Cupertino, Saratoga

**Still need hand-sourcing — not part of Census TIGER:**
- Special districts: Midpeninsula Regional Open Space District, Santa Clara Valley Open Space Authority
- Santa Clara County Board of Education (SCCOE) trustee areas
- Trustee-area maps for the districts below (checked against the [Santa Clara County Registrar of Voters' district pages](https://vote.santaclaracounty.gov/school-districts), 2026-09-15 — each district page states whether it's "voted on at-large" or "voted on by trustee area/district")

**All 4 community college districts elect by trustee area** — Foothill-De Anza, San José-Evergreen, West Valley-Mission, and Gavilan Joint all need trustee-area maps.

**K-12 districts that elect by trustee area (need a map) — 14 of the 31 on the original list.** The Registrar's top-line "Election:" field only tells part of the story — 4 of these districts recently adopted a transition resolution and that field still says "at-large" even though their *first* trustee-area election is already scheduled. Caught this because a district you flagged (East Side Union) turned out to have a transition note further down its page that a first pass checking only the summary line had missed — worth being aware that a same pattern could apply elsewhere if this list is ever re-verified.

- **Trustee-area maps loaded (6 of 14):** Campbell Union HSD, Fremont Union HSD and Los Gatos-Saratoga Joint Union HSD (in `high_school_trustee_area`); Oak Grove SD and Alum Rock Union ESD (in `elementary_trustee_area`); Gilroy USD (in `unified_trustee_area`)
- **Already electing by trustee area, map still needed:** Morgan Hill USD, San José USD, Santa Clara USD, Campbell Union SD, Moreland SD, Sunnyvale SD

Known data gap: Gilroy USD's trustee-area map stops about 78 sq mi short of the district's eastern edge as the Census draws it — the rural land out toward Pacheco Pass. Addresses there get the district but a blank trustee area. Worth asking the district for a map covering its full territory if anyone on your lists lives out that way.
- **Mid-transition — first trustee-area election is November 3, 2026:** Los Gatos-Saratoga Joint Union HSD and Alum Rock Union ESD are loaded. Still needed: East Side Union HSD and Mountain View-Los Altos Union HSD. Sourcing those two is the time-sensitive part if you want coverage in place before that election.

**K-12 districts confirmed at-large (no trustee-area map needed) — the other 17:**
- Unified: Milpitas, Palo Alto
- Elementary: Berryessa Union, Cambrian, Cupertino Union, Evergreen, Franklin-McKinley, Lakeside Joint, Loma Prieta Joint Union, Los Altos, Los Gatos Union, Luther Burbank, Mount Pleasant, Mountain View Whisman, Orchard, Saratoga Union, Union

Checked against the [Santa Clara County Registrar of Voters' district pages](https://vote.santaclaracounty.gov/school-districts), 2026-09-15, reading each page in full rather than just its summary line.

These are all genuinely agency-specific GIS data — trustee-area maps are usually on the district's own site (often under "Board of Trustees" or a CVRA/redistricting page) or from the county Registrar of Voters / Board of Education, the same sourcing approach you've been using for city council maps. The four mid-transition districts above all publish their adopted trustee-area map as a PDF alongside their transition resolution (e.g. ESUHSD's is linked from esuhsd.org/By-District-Trustee-Elections) — likely your fastest source for those four specifically, ahead of county channels.

## License

Copyright © 2026 Drew Siegler. Licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0).

Free to download, free to use, and free to adapt for another county. Donations are gratefully accepted and never required. If you distribute a modified version — or run one as a service other people use over a network — you have to publish your source under this same license.

**The boundary data is not covered by that license.** The files in `data/raw_geojson/` come from public agencies, each with its own terms:

- Census TIGER/Line files (`us_congress`, `ca_state_senate`, `ca_state_assembly`, the three school district layers, `city`) are U.S. government works, in the public domain.
- City council, county supervisorial, and trustee-area maps come from each agency's GIS portal or public records request, and may carry their own attribution terms. Check with the source agency before redistributing.

Boundaries change. Verify anything you'd act on against the county Registrar of Voters — this tool comes with no warranty, as the license spells out.

## Trademark

"District Lookup" is a trademark of Drew Siegler. The AGPL covers the code; it does not grant rights to the name.

Forking this for your own county is encouraged — please give your version its own name, and don't use "District Lookup" in a way that suggests it's the official version or that it's maintained or endorsed by me. Referring to what your version is built from ("a fork of District Lookup", "based on District Lookup") is fine and welcome.
