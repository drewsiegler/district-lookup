# Privacy policy

District Lookup runs on your own computer. It has no accounts, no analytics and no tracking, and its developer never receives your list or anything about it.

## What leaves your computer

Only two things, both over encrypted (HTTPS) connections:

1. **Addresses, to the U.S. Census Bureau.** To place each address on the map, District Lookup sends the address, and nothing else from your list, to the Census Bureau's free [geocoder](https://geocoding.geo.census.gov/geocoder/). Names, emails, phone numbers and your other columns never leave your computer. Addresses go in batches, and any a batch misses are retried one at a time. The Census Bureau's [privacy policy](https://www.census.gov/about/policies/privacy.html) covers what it does with them.
2. **An update check, to GitHub.** Each time District Lookup starts, it asks GitHub which version is the newest, so it can tell you when there's an update. That request carries nothing about your list. GitHub sees what any website sees when you visit it: your internet address and the time. GitHub's [privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement) covers it. If the check fails, nothing happens and the app works the same.

Links in the app, to a release, this project or the Ko-fi page, open in your web browser only when you click them.

## What stays on your computer

- **Your list and its results.** The lookup page is served from your own computer and can't be reached from any other. Results stay in memory until you download them. The command line writes them next to your list. District Lookup doesn't save them anywhere else.
- **Saved address lookups.** So the next lookup is faster, District Lookup remembers each address it has looked up, and where it is on the map, in a file called `geocode_cache.sqlite`. It holds addresses only, never names or anything else from your list. It's in this folder:
  - Mac: `~/Library/Application Support/District Lookup/`
  - Windows: `%LOCALAPPDATA%\District Lookup\`
  - Chromebook and Linux: `~/.local/share/district-lookup/`
  - Running from source: the project's `data` folder

  Delete that file to clear them; District Lookup starts a new, empty one next time. Uninstalling the app leaves it in place, so delete it yourself if you're removing District Lookup for good.

## Changes and questions

This page is updated whenever what District Lookup sends or keeps changes, and its history is on GitHub. Questions are welcome as an [issue on GitHub](https://github.com/drewsiegler/district-lookup/issues).

Updated October 13, 2026.
