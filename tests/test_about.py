"""The update check, with GitHub faked: no test reaches the network."""

import pytest
import requests

import about


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status = payload, status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(f"{self.status}")

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


@pytest.fixture
def github(monkeypatch):
    """Set .reply to what GitHub's latest-release API should answer."""
    class GitHub:
        reply = None
        asked = []

    def fake_get(url, **kwargs):
        GitHub.asked.append(url)
        if isinstance(GitHub.reply, Exception):
            raise GitHub.reply
        return GitHub.reply

    monkeypatch.setattr(requests, "get", fake_get)
    return GitHub


def release(tag, name=None, url=None):
    return FakeResponse({"tag_name": tag, "name": name,
                         "html_url": url or f"https://github.com/{about.REPO}/releases/tag/{tag}"})


@pytest.mark.parametrize("text, expected", [
    ("v1.2.3", (1, 2, 3)), ("1.10.0", (1, 10, 0)), (" v2.0.0 ", (2, 0, 0)),
    ("v1.2", None), ("latest", None), ("", None), (None, None),
])
def test_parse_version(text, expected):
    assert about.parse_version(text) == expected


def test_newer_release_is_offered(github):
    github.reply = release("v1.1.0", name="New Los Altos SD trustee areas")
    found = about.check_for_update("1.0.0")
    assert found == {"version": "1.1.0", "title": "New Los Altos SD trustee areas",
                     "url": f"https://github.com/{about.REPO}/releases/tag/v1.1.0"}
    assert github.asked == [about.LATEST_RELEASE_API]


def test_numbers_compare_as_numbers_not_text(github):
    github.reply = release("v1.10.0")
    assert about.check_for_update("1.9.0")["version"] == "1.10.0"


@pytest.mark.parametrize("tag", ["v1.0.0", "v0.9.0", "nightly"])
def test_same_older_or_unreadable_release_is_not_offered(github, tag):
    github.reply = release(tag)
    assert about.check_for_update("1.0.0") is None


@pytest.mark.parametrize("reply", [
    requests.ConnectionError("offline"),
    FakeResponse({}, status=403),          # rate-limited
    FakeResponse(ValueError("not JSON")),
])
def test_any_failure_means_no_banner(github, reply):
    github.reply = reply
    assert about.check_for_update("1.0.0") is None


def test_a_title_that_just_repeats_the_tag_is_dropped(github):
    github.reply = release("v1.1.0", name="v1.1.0")
    assert about.check_for_update("1.0.0")["title"] is None


def test_link_only_ever_points_at_this_repo(github):
    github.reply = release("v1.1.0", url="javascript:alert(1)")
    assert about.check_for_update("1.0.0")["url"] == about.RELEASES_PAGE
