# District Lookup

Give it a list of people and their addresses; it tells you every electoral district each person lives in — city council, county supervisor, Congress, State Senate and Assembly, school and community college districts and their trustee areas, County Board of Education, the two open space districts (Midpeninsula wards, Santa Clara Valley Open Space Authority districts), and Valley Water board districts — and hands the list back with those added as columns. A custom, growable version of what a registrar of voters' office uses internally, currently covering Santa Clara County.

## Your list stays private

Nothing is uploaded. The app runs on your own computer, and the page it opens is reachable only from that computer. The only thing that leaves the machine is the addresses themselves, sent to the free U.S. Census Bureau geocoder to turn them into map coordinates — no names, emails or phone numbers. When the app window opens it also asks GitHub whether a newer version is out; that check sends nothing about your list.

Results are never saved anywhere on their own: the app window hands them over only as downloads, and the command line writes them next to your list rather than inside this folder.

## Install

Needs Python 3:

```bash
cd district-lookup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

That's about 58 MB, with nothing to compile. The prepared district maps are included, so you can start straight away.

## Look up a list

### The app window

Double-click **Start District Lookup.command** in Finder, or run `python src/web.py`. It opens a page in your browser: drop a file on it, pick one from your computer, or paste a list straight in, then click Start. When it's done you get two download buttons. Leave the small Terminal window open while you use it; closing it shuts the app down.

Download before starting another lookup — the next one replaces the results.

The first time you open the launcher, macOS may say it can't verify the developer. On macOS 14 or earlier, right-click it, choose **Open**, then **Open** again. On macOS 15 or later, open **System Settings → Privacy & Security**, scroll down and click **Open Anyway**. You only need to do that once.

### The command line

```bash
python src/main.py path/to/list.csv
```

Results are written next to your list: `list.csv` produces `list.results.csv` and `list.needs_review.csv`.

## What your list can look like

Use whatever you already have — no need to reshape it. It reads `.csv` and `.txt`, comma, tab, semicolon or pipe separated, straight out of Excel ("CSV UTF-8"), Numbers, or Google Sheets.

**A contact export with the address split across columns** — the usual case. `data/people_contacts_example.csv` is a template:

```
First Name,Last Name,Street Address,Street Address 2,City,State,Zip,Email,Phone Number
Maria,Gonzalez,1660 Tully Rd,Apt 12,San Jose,CA,95122,maria@example.org,408-555-0101
```

It recognizes the usual names for each part of an address (`Street Address`, `Address`, `Address Line 1`, `Mailing Address`; `City`; `State`; `Zip`, `ZIP Code`, `Postal Code`) in any capitalization or spacing, and shows which columns it used when a run starts, so a wrong guess is obvious straight away.

**One address per line in a `.txt`**, optionally with a name before a `|`:

```
1660 Tully Rd, San Jose, CA 95122
Alex Lee | 70 N First St, Campbell, CA 95008
```

Two things worth knowing:

- **Apartment and unit numbers are kept but not searched.** The geocoder often fails on an address that carries one, and it isn't needed to place someone on a map. `Street Address 2` still comes back untouched.
- **Your columns are never overwritten.** If your list has its own `City` column, the official city is added beside it as `city_lookup`. A mailing city of "San Jose" can be unincorporated county land, so the two disagreeing is real information.

## What you get back

Every column of your list comes back in its original order and spelling, with the district columns added on the end. Each person lands in exactly one of two files:

- **results** — everyone placed inside the county, with `matched_address`, `lat`, `lon`, and a column per district type.
- **needs review** — everyone who needs a human look first, with a `review_reason`, and `address_searched` showing exactly what was looked up (which usually shows what went wrong). Fix the address and run again, and that person moves to results.

The reasons:

- `unmatched_address` — the address couldn't be found at all. Usually a typo, a PO box, or a landmark name instead of a street address.
- `outside_coverage_area` — it was found, but outside the county. Either the address is wrong, or the person belongs on a different list.
- `missing_council_district`, `missing_unified_trustee_area`, and the like — the person is inside a city or school district whose map is loaded, but that map has a gap right where they live, so the district needs looking up by hand. This is rare.

A blank district on its own isn't an error. At-large cities have no council districts, unincorporated land has no city, the two open space agencies split the county between them (Midpeninsula the northwest, the Santa Clara Valley Open Space Authority most of the rest, Gilroy neither), and school districts that elect their boards at-large have no trustee areas — see [COVERAGE.md](COVERAGE.md) for what's in and what's still to come.

How districts are written: `city` is the city or town; `council_district` is the bare district number (Morgan Hill uses letters `A`–`D`); county `D2—Sup. Betty Duong`, Congress `US-CA16`, State Senate `SD15`, Assembly `AD25`, school and community college districts by full name (`Gavilan Joint Community College District`), trustee areas `TA3` (County Board of Education too), Midpeninsula Open Space `Ward 1`, Santa Clara Valley Open Space Authority `D1`, Valley Water `D1`.

Boundaries change. Verify anything you'd act on against the county Registrar of Voters.

## Updating

When a new version is out, usually because district maps have changed, a banner at the top of the app window says so, with a link to download it. The version you have is shown at the bottom of the window.

If you got the project with git, update it by running `git pull` in the `district-lookup` folder. If you downloaded a ZIP from GitHub, download the new one and replace the folder; if you keep a list inside the folder, move it out first. The first lookup afterwards may take a little longer while it re-checks addresses with the Census.

## Support this project

District Lookup is free and always will be. If it saves you or your organization time and you'd like to chip in, you can leave a tip at **[ko-fi.com/andrewsiegler](https://ko-fi.com/andrewsiegler)**; you don't need an account. The same link is at the bottom of the app window.

Donations go to Drew Siegler (Andrew Siegler on Ko-fi), who builds and maintains the tool. They help cover time spent sourcing maps and keeping them current. It's a personal project, not a nonprofit, so donations aren't tax-deductible, and they're never required.

Not in a position to give? Telling other organizers about it, or [reporting a wrong district](https://github.com/drewsiegler/district-lookup/issues), helps just as much.

## Maintaining it

Adding or updating district maps, how it works under the hood, and running the tests: [docs/adding-maps.md](docs/adding-maps.md).

## License

Copyright © 2026 Drew Siegler. Licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0).

Free to download, free to use, and free to adapt for another county. Donations are gratefully accepted and never required. If you distribute a modified version — or run one as a service other people use over a network — you have to publish your source under this same license. It comes with no warranty, as the license spells out.

**The boundary data is not covered by that license.** The files in `data/raw_geojson/` come from public agencies, each with its own terms:

- Census TIGER/Line files (`us_congress`, `ca_state_senate`, `ca_state_assembly`, the three school district layers, `city`) are U.S. government works, in the public domain.
- City council, county supervisorial, trustee-area (including the County Board of Education's), Midpeninsula Open Space ward, Santa Clara Valley Open Space Authority district, and Valley Water board district maps come from each agency's GIS portal or public records request, and may carry their own attribution terms. Check with the source agency before redistributing.

## Trademark

"District Lookup" is a trademark of Drew Siegler. The AGPL covers the code; it does not grant rights to the name.

Forking this for your own county is encouraged — please give your version its own name, and don't use "District Lookup" in a way that suggests it's the official version or that it's maintained or endorsed by me. Referring to what your version is built from ("a fork of District Lookup", "based on District Lookup") is fine and welcome.
