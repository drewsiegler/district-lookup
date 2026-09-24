# Coverage — Santa Clara County

Updated 2026-09-23. What's loaded, what's still to source, and where the gaps are. How to add a map: [docs/adding-maps.md](docs/adding-maps.md).

## Complete, from Census data

County supervisorial, U.S. Congress, CA State Senate, CA State Assembly, all 15 cities and towns (official city limits), and every unified, elementary and high school district's overall boundary.

## City council districts

The `city` column covers all 15 cities and towns. `council_district` is filled in only for cities that elect by district:

- **Loaded:** San José, Santa Clara, Campbell, Morgan Hill, Sunnyvale, Gilroy
- **Still needed:** Los Altos — recently switched to district elections; map requested by email
- **At-large, so no council map needed:** Los Gatos, Milpitas, Mountain View, Los Altos Hills, Monte Sereno, Palo Alto, Cupertino, Saratoga

## School trustee areas

Of the 31 K-12 districts tracked here, 14 elect their boards by trustee area and need a map; the other 17 elect at-large, where the district boundary is the whole answer.

- **Loaded (6 of 14):** Campbell Union HSD, Fremont Union HSD, Los Gatos-Saratoga Joint Union HSD, Oak Grove SD, Alum Rock Union ESD, Gilroy USD
- **Still needed — first trustee-area election November 3, 2026:** East Side Union HSD, Mountain View-Los Altos Union HSD. These are the time-sensitive ones. East Side Union publishes its adopted map with its transition resolution (linked from esuhsd.org/By-District-Trustee-Elections); Mountain View-Los Altos likely does the same. Either is probably faster than going through the county.
- **Still needed — already electing by trustee area:** Morgan Hill USD, San José USD, Santa Clara USD, Campbell Union SD, Moreland SD, Sunnyvale SD
- **At-large, so no trustee map needed:** Milpitas USD, Palo Alto USD; Berryessa Union, Cambrian, Cupertino Union, Evergreen, Franklin-McKinley, Lakeside Joint, Loma Prieta Joint Union, Los Altos, Los Gatos Union, Luther Burbank, Mount Pleasant, Mountain View Whisman, Orchard, Saratoga Union and Union elementary districts

All four community college districts — Foothill-De Anza, San José-Evergreen, West Valley-Mission and Gavilan Joint — elect by trustee area; none are loaded yet.

## Not started

- Midpeninsula Regional Open Space District
- Santa Clara Valley Open Space Authority
- Santa Clara County Board of Education (SCCOE) trustee areas

None of these are in Census data; they come from each agency's GIS portal or a records request, the same way the council and trustee maps have.

## Known gaps in loaded maps

People who fall in one of these are flagged for review rather than given a blank or wrong answer.

- **Gilroy USD** — the district's trustee-area map stops about 78 sq mi short of its eastern edge as the Census draws it: the rural land out toward Pacheco Pass. Worth asking the district for a map covering its full territory if anyone on your lists lives out that way.
- **San José** — about 1.3 sq mi inside the official city limits isn't covered by the city's own council map.
- **Other council maps** — a tenth of a square mile or less each; none in Sunnyvale.

## How election methods were verified

Checked 2026-09-15 against each district's page on the [Santa Clara County Registrar of Voters' site](https://vote.santaclaracounty.gov/school-districts), which states whether its board is "voted on at-large" or "voted on by trustee area/district". Read each page in full: the summary line can lag behind. Four districts had adopted a switch to trustee areas while that line still said "at-large", with the transition noted only further down the page — East Side Union was caught that way. Re-check the same way if this list is ever re-verified.
