"""What the app says about itself: which version it is, where new versions are
published, and where donations go.

A release changes VERSION here and nowhere else, then is tagged on GitHub as
"v" + VERSION (v1.0.0). The app window compares its own VERSION with the
newest release there to tell people when an update is out.

The update check is the only network call besides the Census geocoder. It asks
GitHub's public API for the latest release's version number and sends nothing
about anyone's list. Offline, rate-limited or any other failure just means no
banner: the app works the same either way.
"""

import re

import requests

VERSION = "1.0.0"
REPO = "drewsiegler/district-lookup"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPO}/releases/latest"
DONATE_URL = None  # the app window's footer shows a "Support this project" link once this is set


def parse_version(text: str | None) -> tuple[int, int, int] | None:
    """ "v1.2.3" or "1.2.3" -> (1, 2, 3); anything else -> None."""
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (text or "").strip())
    return tuple(int(part) for part in match.groups()) if match else None


def check_for_update(current: str = VERSION) -> dict | None:
    """The newest published release, if it's newer than this copy:
    {"version": "1.1.0", "url": <its download page>, "title": <its name, if any>}.
    None when this copy is current, or when GitHub can't be reached."""
    try:
        response = requests.get(LATEST_RELEASE_API, timeout=5,
                                headers={"Accept": "application/vnd.github+json"})
        response.raise_for_status()
        release = response.json()
    except (requests.RequestException, ValueError):
        return None
    tag = release.get("tag_name")
    latest, ours = parse_version(tag), parse_version(current)
    if latest is None or ours is None or latest <= ours:
        return None
    title = (release.get("name") or "").strip()
    url = release.get("html_url") or ""
    return {
        "version": ".".join(map(str, latest)),
        # The page links to this, so only ever this repo's own release page.
        "url": url if url.startswith(f"https://github.com/{REPO}/releases/") else RELEASES_PAGE,
        "title": title if title and title != tag else None,
    }
