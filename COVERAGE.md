# Coverage — Santa Clara County

Updated 2026-10-01. What's loaded, what's still to source, and where the gaps are. How to add a map: [docs/adding-maps.md](docs/adding-maps.md).

## Complete, from Census data

County supervisorial, U.S. Congress, CA State Senate, CA State Assembly, all 15 cities and towns (official city limits), and every unified, elementary and high school district's overall boundary.

## City council districts

The `city` column covers all 15 cities and towns. `council_district` is filled in only for cities that elect by district:

- **Loaded:** San José, Santa Clara, Campbell, Morgan Hill, Sunnyvale, Gilroy, Los Altos
- **Los Altos** switched to district elections in 2024. Its map, "F2a", was adopted October 22, 2024, and the first district elections are November 3, 2026, for Districts 2 and 4. The loaded file agrees with the district the city's own GIS assigns each parcel, at every one of 349 sample points checked, 115 of them within 25 m of a district line.
- **At-large, so no council map needed:** Los Gatos, Milpitas, Mountain View, Los Altos Hills, Monte Sereno, Palo Alto, Cupertino, Saratoga

## School trustee areas

Of the 31 K-12 districts tracked here, 14 elect their boards by trustee area and need a map; the other 17 elect at-large, where the district boundary is the whole answer.

- **Loaded (6 of 14):** Campbell Union HSD, Fremont Union HSD, Los Gatos-Saratoga Joint Union HSD, Oak Grove SD, Alum Rock Union ESD, Gilroy USD
- **Still needed — first trustee-area election November 3, 2026:** East Side Union HSD, Mountain View-Los Altos Union HSD. These are the time-sensitive ones. East Side Union publishes its adopted map with its transition resolution (linked from esuhsd.org/By-District-Trustee-Elections); Mountain View-Los Altos likely does the same. Either is probably faster than going through the county.
- **Still needed — already electing by trustee area:** Morgan Hill USD, San José USD, Santa Clara USD, Campbell Union SD, Moreland SD, Sunnyvale SD
- **At-large, so no trustee map needed:** Milpitas USD, Palo Alto USD; Berryessa Union, Cambrian, Cupertino Union, Evergreen, Franklin-McKinley, Lakeside Joint, Loma Prieta Joint Union, Los Altos, Los Gatos Union, Luther Burbank, Mount Pleasant, Mountain View Whisman, Orchard, Saratoga Union and Union elementary districts

All four community college districts — Foothill-De Anza, San José-Evergreen, West Valley-Mission and Gavilan Joint — elect by trustee area; none are loaded yet.

## County Board of Education

- **Loaded:** Santa Clara County Board of Education trustee areas, written `TA1`–`TA7` — the map approved January 10, 2022, drawn from the 2020 Census. It matches SCCOE's own published map, "Santa Clara County Board of Education Trustee Areas (2022)" on ArcGIS Online, exactly.

  It covers the whole county except two stretches of mostly empty eastern hills, where the column is blank:
  - about 119 sq mi in Patterson Joint Unified, a school district run from Stanislaus County and so outside this board's territory;
  - about 80 sq mi east of Gilroy, out toward Pacheco Pass — the same land Gilroy USD's own trustee map leaves out (see Known gaps below).

## Special districts

- **Loaded:** Midpeninsula Regional Open Space District wards — the map adopted March 23, 2022 (Resolution 22-12, drawn from the 2020 Census), first used in the November 2022 election. It covers the county's northwest: all of Palo Alto, Los Altos, Los Altos Hills, Mountain View, Sunnyvale, Saratoga, Monte Sereno and Los Gatos, nearly all of Cupertino, plus neighboring unincorporated land. Everyone outside it gets a blank ward. Ward 7 lies entirely in San Mateo County, so only Wards 1–6 turn up here.

  Sourced from Midpen's own GIS (`Ward_Boundary_(public)` on services2.arcgis.com/qmhndvC947rDNl6t). That layer's description still says "adopted in 2011", but its features carry the 2022 adoption date. Older copies circulating on county open-data portals are the 2011 map, which puts about 59 sq mi of the county in a different ward. If you ever re-download the map, check that `CENSUSYEAR` is 2020 or later.

## Not started

- Santa Clara Valley Open Space Authority

It isn't in Census data; it will come from the agency's GIS portal or a records request, the same way the council and trustee maps have.

## Known gaps in loaded maps

People who fall in one of these are flagged for review rather than given a blank or wrong answer.

- **Gilroy USD** — the district's trustee-area map stops about 78 sq mi short of its eastern edge as the Census draws it: the rural land out toward Pacheco Pass. The County Board of Education's trustee map leaves out the same land, which suggests the Census boundary overreaches there rather than the district's map falling short. Worth asking the district for a map covering its full territory if anyone on your lists lives out that way.
- **San José** — about 1.3 sq mi inside the official city limits isn't covered by the city's own council map.
- **Other council maps** — a tenth of a square mile or less each; none in Sunnyvale or Los Altos.

## How election methods were verified

Checked 2026-09-15 against each district's page on the [Santa Clara County Registrar of Voters' site](https://vote.santaclaracounty.gov/school-districts), which states whether its board is "voted on at-large" or "voted on by trustee area/district". Read each page in full: the summary line can lag behind. Four districts had adopted a switch to trustee areas while that line still said "at-large", with the transition noted only further down the page — East Side Union was caught that way. Re-check the same way if this list is ever re-verified.
