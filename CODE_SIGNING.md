# Code signing policy

Signing lets your computer confirm who made a program and that nobody has changed it since. This page says which District Lookup downloads are signed, by whom, and how they're made.

## What's signed

| Download | Signed? |
|---|---|
| Mac (`.dmg`) | Yes, from version 1.1.1: signed with the maintainer's Apple Developer ID certificate and notarized (checked for malware) by Apple. |
| Windows (`setup.exe`) | Not yet. Free signing for open-source projects is planned. |
| Chromebook and Linux (`.deb`, `.tar.gz`) | No. These systems don't ask for it; the checksums and attestations below let you check a download instead. |

## How the downloads are made

- Every download is built by GitHub Actions from the public source code at the release's version tag, using the [build workflow](.github/workflows/build-apps.yml). Nothing is built or signed on anyone's own computer.
- The Mac signing certificate and Apple sign-in are kept as encrypted GitHub secrets. Only that workflow uses them, and it runs only when the maintainer tags a release or starts a build by hand.
- Each build is installed and tested before it's kept. GitHub drafts the release, and the maintainer reviews it before publishing it.
- What goes in is open source: District Lookup's own code ([AGPL-3.0](LICENSE)), Python, and open-source libraries, plus district maps from public government sources.

## Team

- Committers and reviewers: Drew Siegler ([@drewsiegler](https://github.com/drewsiegler))
- Approvers: Drew Siegler ([@drewsiegler](https://github.com/drewsiegler))

District Lookup has one maintainer, who writes and reviews the code and approves each release. Changes from anyone else are reviewed before they're merged.

## Checking a download

- Each release lists every file's SHA-256 checksum in `SHA256SUMS.txt`.
- GitHub records where each file was built. With GitHub's command-line tool, `gh attestation verify <file> --repo drewsiegler/district-lookup` confirms it came from this project's workflow.
- On a Mac, `spctl --assess --verbose "/Applications/District Lookup.app"` should end with `source=Notarized Developer ID`.

## Privacy

District Lookup sends addresses to the U.S. Census geocoder and checks GitHub for updates, and nothing else. The [privacy policy](PRIVACY.md) has the details.

## Reporting a problem

If you think a District Lookup download has been tampered with, or wasn't built from this repository, please [open an issue](https://github.com/drewsiegler/district-lookup/issues).
