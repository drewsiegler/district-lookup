# District Lookup

Give it a list of people and their addresses; it tells you every electoral district each person lives in — city council, county supervisor, Congress, State Senate and Assembly, school and community college districts and their trustee areas, County Board of Education, the two open space districts (Midpeninsula wards, Santa Clara Valley Open Space Authority districts), and Valley Water board districts — and hands the list back with those added as columns. A custom, growable version of what a registrar of voters' office uses internally, currently covering Santa Clara County.

## Your list stays private

Nothing is uploaded. The app runs on your own computer, and the page it opens is reachable only from that computer. The only thing that leaves the machine is the addresses themselves, sent to the free U.S. Census Bureau geocoder to turn them into map coordinates — no names, emails or phone numbers. When the app window opens it also asks GitHub whether a newer version is out; that check sends nothing about your list.

Results are never saved anywhere on their own: the app window hands them over only as downloads, and the command line writes them next to your list rather than inside this folder.

## Install

Download the version for your computer from the **[latest release](https://github.com/drewsiegler/district-lookup/releases/latest)**; the release page says which file is which. Everything it needs is inside, district maps included, so there's nothing else to install.

The apps aren't signed with paid developer certificates, so the first time you open one, your computer warns that it can't tell who made it. Here's how to get past that on each system. You only need to do it once per version.

### Mac

1. Open the `.dmg` file and drag **District Lookup** into the Applications folder.
2. Open it from Applications. macOS says it can't check it for malicious software.
3. On **macOS 15 or later**, click **Done**, open **System Settings → Privacy & Security**, scroll down to the message about District Lookup, click **Open Anyway** and confirm. On **macOS 14 or earlier**, right-click District Lookup in Applications, choose **Open**, then click **Open** again.

### Windows

1. Run the file ending `windows-setup.exe`.
2. If Windows says "Windows protected your PC", click **More info**, then **Run anyway**.
3. Click through the installer. It installs just for you, so it doesn't ask for an administrator password, and puts District Lookup in the Start menu.

### Chromebook

District Lookup runs in the Chromebook's built-in Linux, which is off until you turn it on. Some school- and work-managed Chromebooks don't allow it.

1. Turn on Linux: **Settings → About ChromeOS → Developers → Linux development environment → Set up**. It takes a few minutes.
2. Download the `.deb` file for your Chromebook, double-click it in the **Files** app, and choose **Install**.
3. Open **District Lookup** from the launcher's **Linux apps** folder. Your lookup page opens in Chrome.

### Linux

On Debian, Ubuntu and similar systems, install the `.deb` (double-click it, or run `sudo apt install ./district-lookup_*.deb`) and open District Lookup from your apps. On other systems, unpack the `.tar.gz` and run `district-lookup` inside it.

### From source

For developers, or anyone who'd rather run the code directly. Needs Python 3:

```bash
cd district-lookup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

That's about 58 MB, with nothing to compile. Then double-click **Start District Lookup.command** in Finder, or run `python src/web.py`. Instead of the small window the installed app shows, a Terminal window stays open while it runs; closing it shuts District Lookup down. If macOS won't open the launcher the first time, use the same steps as for the Mac app above.

## Look up a list

### The app window

Open **District Lookup**. A small window says it's running, and your lookup page opens in your web browser: drop a file on it, pick one from your computer, or paste a list straight in, then click Start. When it's done you get two download buttons.

Keep the small window open while you use it. Closing it, or clicking **Quit**, shuts District Lookup down; if you haven't downloaded your results yet, it asks first, since they aren't saved anywhere else. If you close the browser tab by mistake, click **Open the lookup page** in the small window to get it back.

Download before starting another lookup — the next one replaces the results.

### The command line

From source only:

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
- **Your columns are never overwritten.** If your list has its own `City` column, the official city is added beside it as `City (Lookup)`. A mailing city of "San Jose" can be unincorporated county land, so the two disagreeing is real information.

## What you get back

Every column of your list comes back in its original order and spelling, with the district columns added on the end. Each person lands in exactly one of two files:

- **results** — everyone placed inside the county, with the address as the Census found it, its map coordinates, and the district columns listed further down.
- **needs review** — everyone who needs a human look first, with a `Review Reason`, and `Address Searched` showing exactly what was looked up (which usually shows what went wrong). Fix the address and run again, and that person moves to results.

The reasons:

- `unmatched_address` — the address couldn't be found at all. Usually a typo, a PO box, or a landmark name instead of a street address.
- `outside_coverage_area` — it was found, but outside the county. Either the address is wrong, or the person belongs on a different list.
- `missing_council_district`, `missing_unified_trustee_area`, and the like — the person is inside a city or school district whose map is loaded, but that map has a gap right where they live, so the district needs looking up by hand. This is rare.

A blank district on its own isn't an error. At-large cities have no council districts, unincorporated land has no city, the two open space agencies split the county between them (Midpeninsula the northwest, the Santa Clara Valley Open Space Authority most of the rest, Gilroy neither), and school districts that elect their boards at-large have no trustee areas — see [COVERAGE.md](COVERAGE.md) for what's in and what's still to come.

The columns added, in order:

| Column | Written like | Notes |
|---|---|---|
| Matched Address | `1660 TULLY RD, SAN JOSE, CA, 95122` | the address as the Census found it |
| Lat, Lon | `37.3216`, `-121.8270` | its map coordinates |
| City | `San Jose` | the official city or town; blank on unincorporated land |
| Council District | `7` | Morgan Hill uses letters `A`–`D`; blank in at-large cities. Campbell's and Morgan Hill's come with the councilmember, like `3—Cm. Dan Furtado` |
| Supervisor District | `D2—Sup. Betty Duong` | |
| US Congress | `US-CA16—Rep. Sam Liccardo` | |
| CA State Senate | `SD15—Sen. Dave Cortese` | `SD10—Vacant` while that seat is empty |
| CA Assembly | `AD25—Asm. Ash Kalra` | |
| Unified School District | `Santa Clara Unified School District` | |
| Unified Trustee Area | `TA4` | |
| Elementary School District | `Evergreen Elementary School District` | |
| Primary Trustee Area | `TA5` | for the elementary school district |
| High School District | `East Side Union High School District` | |
| Secondary Trustee Area | `TA3` | for the high school district |
| Community College District | `Gavilan Joint Community College District` | |
| College Trustee Area | `TA4` | |
| County Board of Education | `TA7` | its trustee area |
| Open Space District | `Midpeninsula Regional Open Space District` | or `Santa Clara Valley Open Space Authority` |
| District/Ward | `Ward 1` | a Midpeninsula ward, or an Open Space Authority district like `D7` |
| SCV Water District | `D6` | Valley Water board district |

Boundaries change. Verify anything you'd act on against the county Registrar of Voters.

## Updating

When a new version is out, usually because district maps have changed, a banner at the top of the lookup page says so, with a link to download it. The version you have is shown at the bottom of the page.

Install the new version over the old one, the same way as the first time: on a Mac, drag it into Applications and choose **Replace**; on Windows, run the new installer; on a Chromebook or Linux, install the new `.deb`. Your earlier address lookups are kept, so the next lookup stays quick. Expect the first-open warning again, once, for each new version.

Running from source, update with `git pull` in the `district-lookup` folder, or, if you downloaded a ZIP from GitHub, download the new one and replace the folder (move out any list you keep inside it first).

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
