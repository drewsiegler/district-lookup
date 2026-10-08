# Coverage — Santa Clara County

Updated 2026-10-08. What's loaded, what's still to source, and where the gaps are. How to add a map: [docs/adding-maps.md](docs/adding-maps.md).

## Complete, from Census data

County supervisorial, U.S. Congress, CA State Senate, CA State Assembly, all 15 cities and towns (official city limits), and every unified, elementary and high school district's overall boundary.

Congress, State Senate and Assembly districts are written with whoever holds the seat, like the supervisors: `US-CA16—Rep. Sam Liccardo`, `SD15—Sen. Dave Cortese`, `AD25—Asm. Ash Kalra`. Senate District 10 is vacant, written `SD10—Vacant`. The Census maps don't name officeholders, so they're listed by hand under `names` in `data/layers.json` for the seats covering the county (Congress 16–19, Senate 10, 13 and 15, Assembly 23–26, 28 and 29), and need updating there when someone new takes office or a seat falls vacant. Other districts touch the county only in slivers along its edge, about a hundredth of a square mile each, where the Census draws the line slightly differently; an address there gets the district number alone.

## City council districts

The `City` column covers all 15 cities and towns. `Council District` is filled in only for cities that elect by district:

- **Loaded:** San José, Santa Clara, Campbell, Morgan Hill, Sunnyvale, Gilroy, Los Altos
- **Los Altos** switched to district elections in 2024. Its map, "F2a", was adopted October 22, 2024, and the first district elections are November 3, 2026, for Districts 2 and 4. The loaded file agrees with the district the city's own GIS assigns each parcel, at every one of 349 sample points checked, 115 of them within 25 m of a district line.
- **Councilmembers named:** Campbell (`3—Cm. Dan Furtado`), Morgan Hill (`C—Cm. Soraida Iwanaga`), San José (`7—Cm. Bien Doan`), Santa Clara (`2—Cm. Raj Chahal`). Other cities' districts are the bare number until their councilmembers are added under `names` in `data/layers.json`, and the names need updating there when a seat changes hands. Mayors aren't included: they're elected citywide, not by district.
- **At-large, so no council map needed:** Los Gatos, Milpitas, Mountain View, Los Altos Hills, Monte Sereno, Palo Alto, Cupertino, Saratoga

## School trustee areas

Of the 31 K-12 districts tracked here, 14 elect their boards by trustee area and need a map; the other 17 elect at-large, where the district boundary is the whole answer.

- **Loaded (14 of 14):** Campbell Union HSD, Fremont Union HSD, Los Gatos-Saratoga Joint Union HSD, Oak Grove SD, Alum Rock Union ESD, Gilroy USD, Mountain View-Los Altos Union HSD, San José USD, Campbell Union SD, East Side Union HSD, Santa Clara USD, Morgan Hill USD, Moreland SD, Sunnyvale SD
- **Mountain View-Los Altos Union HSD** holds its first trustee-area election November 3, 2026, for Areas 1, 2 and 3. The loaded map is "Map C1", adopted by the board 5–0 on April 21, 2025 (Resolution 24/25-39). It matches the board-approved C1 drawing on [MVLA's trustee area page](https://www.mvla.net/trustee-area-election-information) area for area, and covers the district's Census outline exactly, so no part of the district comes back without an area.
- **East Side Union HSD** holds its first trustee-area election November 3, 2026, for Areas 1 (a short term), 2 and 4; Areas 1, 3 and 5 follow in 2028. The loaded map is the "Revised Map" adopted October 3, 2025 (Resolution 2025/2026-10), from [the district's trustee election page](https://www.esuhsd.org/By-District-Trustee-Elections). It matches the adopted map area for area, with one exception: it leaves out the business park east of Highway 101 around Hellyer Ave, Silver Creek Valley Rd and Dove Hill Rd, about 0.9 sq mi with 427 residents as of 2020 (see Known gaps below). The adopted map shows no gap there.
- **San José USD** elects five trustee areas; Areas 2 and 4 are on the November 3, 2026 ballot. The loaded map is drawn from the 2020 Census: counting 2020 Census population block by block, its five areas come out within 1.5% of each other, about 53,500 people each. (A map drawn from the 2010 Census would be far more uneven after a decade of growth.) SJUSD's website doesn't link the map, so its adoption date isn't recorded here; the Registrar's [district page](https://vote.santaclaracounty.gov/san-jose-unified-school-district) lists the current trustee for each area.
- **Campbell Union SD** elects five trustee areas; Areas 1, 4 and 5 are on the November 3, 2026 ballot. Its areas were drawn in 2019 ("Purple" map, Resolution 2019-20-22, November 21, 2019) and kept unchanged after the 2020 Census (Resolution 26-12-02-21, December 2, 2021), when the district's demographer found them still within 5.94% of equal population.

  **One neighborhood is in doubt.** The loaded file puts the area west of Highway 17 and south of I-280, around S Daniel Way and S Genevieve Ln down to Moorpark Ave, in **Area 2**. The district's adopted map (the exhibit to its 2019 resolution, and the approved-map viewer on [its trustee area page](https://www.campbellusd.org/cvra)) shows it in **Area 1**. That's about 0.12 sq mi and 419 residents as of 2020. Area 1 is on this November's ballot and Area 2 isn't, so confirm with the Registrar before telling anyone there which race they vote in. Elsewhere the two maps agree, apart from unpopulated slivers.
- **Santa Clara USD** elects seven trustee areas; Areas 1, 3, 4 and 6 are on the November 3, 2026 ballot. The loaded map was redrawn from the 2020 Census: counting 2020 population block by block, its areas come out within 7.9% of each other. It also covers part of north Sunnyvale and north San José, which belong to the district.
- **Morgan Hill USD** elects seven trustee areas; Areas 1–4 are on the November 3, 2026 ballot. The loaded map's areas come out within 7.6% of each other on 2020 Census block counts, as a map drawn from the 2020 Census would. It stops about 29 sq mi short of the district's eastern edge as the Census draws it, in hills where nobody lived in 2020 (see Known gaps below).
- **Moreland SD** elects five trustee areas; Areas 1 (filling a partial term), 2, 3 and 4 are on the November 3, 2026 ballot. The loaded map's areas come out within 6.3% of each other on 2020 block counts, and it covers the district's Census outline.
- **Sunnyvale SD** elects five trustee areas; Areas 1, 3 and 5 are on the November 3, 2026 ballot. The loaded map's areas come out within 4.7% of each other on 2020 block counts. It leaves out north Sunnyvale around Lakewood Village, which is Santa Clara Unified, and about 1.5 sq mi of baylands where nobody lives.
- **At-large, so no trustee map needed:** Milpitas USD, Palo Alto USD; Berryessa Union, Cambrian, Cupertino Union, Evergreen, Franklin-McKinley, Lakeside Joint, Loma Prieta Joint Union, Los Altos, Los Gatos Union, Luther Burbank, Mount Pleasant, Mountain View Whisman, Orchard, Saratoga Union and Union elementary districts
- **Watch:** Los Altos SD. The Mountain View Voice [reported on September 14, 2026](https://www.mv-voice.com/election/2026/09/14/facing-legal-threat-los-altos-school-district-to-ditch-at-large-election-system/) that it plans to drop at-large elections after a legal threat. It will need a trustee map once it adopts one.

## Community college districts

All four community college districts — Foothill-De Anza, San José-Evergreen, West Valley-Mission and Gavilan Joint — elect by trustee area. The Census doesn't map community college districts, so the `Community College District` column is drawn from each college's own trustee map. All four are loaded. The only land left with no college named is about 120 sq mi of the eastern hills in Patterson Joint Unified, a district run from Stanislaus County and served by a college there, plus the Hellyer Ave pocket below.

- **Loaded (4 of 4):** Gavilan Joint CCD — the trustee areas adopted February 8, 2022, from the 2020 Census, for elections through 2030. In this county it covers Gilroy, Morgan Hill, San Martin and the southern end of San José around Coyote Valley: the same ground as the Gilroy and Morgan Hill unified districts, to within about a square mile. Trustee Areas 5 and 7 lie entirely in San Benito County, so only `TA1`–`TA4` and `TA6` turn up here.

  The loaded file matches San Benito County's published copy (`Gavilan_CC_District` on services2.arcgis.com/NjMFCzThTMQy3AJa) to within about 9 m, with identical populations: about 28,500 per area and 199,595 in all, which are 2020 Census figures. It also agrees with the adopted map on [Gavilan's redistricting page](https://www.gavilan.edu/administration/board/redistricting/redistricting_trustee_areas_2022.php).
- **Loaded:** Foothill-De Anza CCD — "Draft Map A", adopted February 14, 2022, which follows city limits wherever it can (from [the district's trustee area page](https://www.fhda.edu/trustee-areas/A-DraftMaps.html)). Areas 2 and 4 are on the November 3, 2026 ballot. It covers the Palo Alto Unified, Mountain View-Los Altos and Fremont Union districts: Palo Alto, Mountain View, Los Altos, Los Altos Hills, most of Sunnyvale and Cupertino, and parts of Saratoga, Santa Clara and west San José. The pocket of north Sunnyvale around Lakewood Village is Santa Clara Unified territory, so it belongs to West Valley-Mission and is correctly left out.
- **Loaded:** San José-Evergreen CCD — the plan adopted January 25, 2022 (Resolution 012522-1), from the 2020 Census. Areas 2, 4 and 6 are on the November 3, 2026 ballot. The loaded file matches the adopted plan on the district's board page: counting 2020 population block by block, only 105 of its 887,238 residents land in a different area, all in blocks split by an area line. It covers the Milpitas Unified, San José Unified and East Side Union districts: Milpitas and about 60% of San José. The college shows as "San Jose-Evergreen Community College District" in results, without the accent, like the other San José names.

  Its adopted plan leaves out the same Hellyer Ave pocket as East Side Union's map, so people there get no college named; they're already flagged for review by the high school column.
- **Loaded:** West Valley-Mission CCD — the post-2020 Census plan adopted February 15, 2022, for elections through 2030 (maps revised August 2, 2022), from [the district's redistricting page](https://www.wvm.edu/board/redistricting/index.html). Areas 3, 5 and 7 are on the November 3, 2026 ballot; Areas 5 and 7 reach into Santa Cruz County. It covers Campbell, Los Gatos, Saratoga, Monte Sereno, most of Santa Clara, north Sunnyvale around Lakewood Village, and parts of San José and Cupertino. The loaded file matches the adopted plan's layout. On 2020 block counts its areas come out 12.7% apart, because the plan's outer edge follows election precincts that split Census blocks, and the demographer estimated those blocks' population, which a block-by-block count can't reproduce.

## County Board of Education

- **Loaded:** Santa Clara County Board of Education trustee areas, written `TA1`–`TA7` — the map approved January 10, 2022, drawn from the 2020 Census. It matches SCCOE's own published map, "Santa Clara County Board of Education Trustee Areas (2022)" on ArcGIS Online, exactly.

  It covers the whole county except two stretches of mostly empty eastern hills, where the column is blank:
  - about 119 sq mi in Patterson Joint Unified, a school district run from Stanislaus County and so outside this board's territory;
  - about 80 sq mi east of Gilroy, out toward Pacheco Pass — the same land Gilroy USD's own trustee map leaves out (see Known gaps below).

## Special districts

- **Loaded:** Midpeninsula Regional Open Space District wards — the map adopted March 23, 2022 (Resolution 22-12, drawn from the 2020 Census), first used in the November 2022 election. It covers the county's northwest: all of Palo Alto, Los Altos, Los Altos Hills, Mountain View, Sunnyvale, Saratoga, Monte Sereno and Los Gatos, nearly all of Cupertino, plus neighboring unincorporated land. Everyone outside it gets a blank ward. Ward 7 lies entirely in San Mateo County, so only Wards 1–6 turn up here.

  Sourced from Midpen's own GIS (`Ward_Boundary_(public)` on services2.arcgis.com/qmhndvC947rDNl6t). That layer's description still says "adopted in 2011", but its features carry the 2022 adoption date. Older copies circulating on county open-data portals are the 2011 map, which puts about 59 sq mi of the county in a different ward. If you ever re-download the map, check that `CENSUSYEAR` is 2020 or later.

- **Loaded:** Santa Clara Valley Open Space Authority director districts, written `D1`–`D7` — the map adopted in 2022 from the 2020 Census, the Authority's "Final Plan (from C3)". The Authority covers most of the county outside Midpen: San José, Santa Clara, Campbell, Milpitas, Morgan Hill and most unincorporated land. So the two complement each other: an address gets a Midpen ward or an Open Space Authority district, almost never both. They share two columns in results: `Open Space District` names the agency, and `District/Ward` holds its ward or district. (Their maps overlap by about 0.04 sq mi along the line they share, so an address right on it could, rarely, get both. Then both are written, Midpen first, separated by a semicolon.)

  Sourced from the Authority's own GIS (the `Authority_Boundary` layer on services3.arcgis.com/kdBUV7ozB9Xo7h9c, which lists each district's current director). The loaded file matches it district for district: the same area to a thousandth of a square mile, and boundaries within about 1 m. It also matches the board-approved map on the Authority's [2022 redistricting page](https://news.openspaceauthority.org/redistricting2022).

  Both open space columns are blank in about 39 sq mi of the county, and that's correct, not a gap in the maps:
  - **the City of Gilroy**, about 16.5 sq mi, which the Authority's own map marks as outside its jurisdiction and which isn't in Midpen either;
  - **about 19 sq mi of the Santa Cruz Mountains around Mount Umunhum and Loma Prieta**, which is inside Midpen's sphere of influence (land it could annex someday) but not yet part of either agency;
  - thin slivers along the county line, about 3.6 sq mi in all, where the Authority's map and the county outline are drawn slightly differently.

- **Loaded:** Valley Water (Santa Clara Valley Water District) board districts, written `D1`–`D7` — the map adopted in 2022 from the 2020 Census, for the 2022–2030 elections. Valley Water covers the whole county, so every address in it gets a district, with no gaps.

  The loaded file is identical to Valley Water's own GIS layer (`SCVWD_Board_of_Directors_Boundaries` on services2.arcgis.com/9KdAx8qBsHiGXOEw, which lists each district's current director), district for district.

## Known gaps in loaded maps

People who fall in one of these are flagged for review rather than given a blank or wrong answer.

- **Gilroy USD** — the district's trustee-area map stops about 78 sq mi short of its eastern edge as the Census draws it: the rural land out toward Pacheco Pass. The County Board of Education's trustee map leaves out the same land too, but Gavilan College's trustee map includes it, as the Census does, so it's unclear which is right. Worth asking the district for a map covering its full territory if anyone on your lists lives out that way.
- **San José** — about 1.3 sq mi inside the official city limits isn't covered by the city's own council map.
- **San José USD** — about 0.3 sq mi inside the district, as the Census draws it, isn't covered by the district's trustee map: thin strips along its edges, the largest by the airport. About 480 people lived there in 2020.
- **East Side Union HSD** — the loaded map leaves out the business park east of Highway 101 around Hellyer Ave, Silver Creek Valley Rd and Dove Hill Rd, about 0.9 sq mi with 427 residents as of 2020. The Census and the district's adopted map both put it in the district, so people there are flagged `missing_high_school_trustee_area`; look up their area by hand. San José-Evergreen's trustee map leaves out the same pocket.
- **Morgan Hill USD** — the trustee map stops about 29 sq mi short of the district's eastern edge as the Census draws it, in the empty hills of Henry W. Coe State Park east of Morgan Hill. Nobody lived there in 2020; anyone who turns up there is flagged `missing_unified_trustee_area`.
- **Gavilan and West Valley-Mission** — their maps overlap by about 0.75 sq mi in the Loma Prieta hills, where 70 people lived in 2020. The app names Gavilan there, but the Census puts that land in Los Gatos-Saratoga Joint Union HSD, which belongs to West Valley-Mission, so West Valley-Mission is more likely right. Check with the Registrar for anyone on a list there.
- **Other council maps** — a tenth of a square mile or less each; none in Sunnyvale or Los Altos.

## How election methods were verified

Checked 2026-09-15 against each district's page on the [Santa Clara County Registrar of Voters' site](https://vote.santaclaracounty.gov/school-districts), which states whether its board is "voted on at-large" or "voted on by trustee area/district". Read each page in full: the summary line can lag behind. Four districts had adopted a switch to trustee areas while that line still said "at-large", with the transition noted only further down the page — East Side Union was caught that way. Re-check the same way if this list is ever re-verified.
