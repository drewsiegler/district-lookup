"""The app window's server, driven over HTTP the way the page drives it."""

import json
import threading
import time
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

import pytest

import web
from conftest import POINTS


@pytest.fixture
def server(layers, fake_geocoder, monkeypatch):
    monkeypatch.setattr(web, "layers_cache", layers)
    monkeypatch.setattr(web, "last_outcome", {"results": None, "review": None})
    monkeypatch.setitem(web.state, "status", "idle")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)  # any free port
    # serve_forever only checks for shutdown every poll_interval (0.5s by
    # default), so each teardown would otherwise stall for up to half a second.
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def get(url):
    with urlopen(url, timeout=5) as response:
        return response.status, response.headers, response.read()


def run_and_wait(base, filename, text):
    body = json.dumps({"filename": filename, "text": text}).encode()
    urlopen(Request(f"{base}/run", data=body, method="POST"), timeout=5).read()
    for _ in range(100):
        state = json.loads(get(f"{base}/status")[2])
        if state["status"] in ("done", "error"):
            return state
        time.sleep(0.02)
    raise AssertionError("lookup never finished")


def test_page_and_icon_are_served(server):
    status, _, page = get(f"{server}/")
    assert status == 200 and b"District Lookup" in page
    status, headers, _ = get(f"{server}/icon.png")
    assert status == 200 and headers["Content-Type"] == "image/png"


def test_pasted_list_runs_and_downloads_from_memory(server, fake_geocoder, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # anything written to the working directory would show up here
    fake_geocoder["1660 Tully Rd, San Jose, CA 95122"] = POINTS["tully_rd_san_jose"]
    state = run_and_wait(server, "pasted list",
                         "1660 Tully Rd, San Jose, CA 95122\nnot a real address\n")

    assert state["status"] == "done"
    assert state["summary"]["results"] == 1 and state["summary"]["review"] == 1

    _, headers, body = get(f"{server}/download/results")
    assert 'filename="results.csv"' in headers["Content-Disposition"]
    assert "D2—Sup. Betty Duong" in body.decode("utf-8-sig")
    _, _, review = get(f"{server}/download/review")
    assert "unmatched_address" in review.decode("utf-8-sig")
    assert list(tmp_path.iterdir()) == []


def test_error_names_their_file_not_a_temp_path(server):
    state = run_and_wait(server, "my-contacts.csv", "Nickname,Phone\nJo,555-1234\n")
    assert state["status"] == "error"
    assert state["error"].startswith("my-contacts.csv:")
    assert "/tmp" not in state["error"] and "/var/" not in state["error"]


def test_nothing_to_download_before_a_run(server):
    with pytest.raises(Exception) as caught:
        get(f"{server}/download/results")
    assert "404" in str(caught.value)


def test_about_reports_the_version_and_any_newer_release(server, monkeypatch):
    newer = {"version": "9.9.9", "url": "https://github.com/x/releases/tag/v9.9.9", "title": None}
    monkeypatch.setattr(web, "update_info", {"checked": True, "update": newer})
    about = json.loads(get(f"{server}/about")[2])
    assert about["version"] == web.about.VERSION
    assert about["donate_url"] == web.about.DONATE_URL
    assert about["checked"] and about["update"] == newer


def test_update_check_records_its_answer(monkeypatch):
    monkeypatch.setattr(web, "update_info", {"checked": False, "update": None})
    monkeypatch.setattr(web.about, "check_for_update", lambda: None)  # offline, or already current
    web.check_for_update()
    assert web.update_info == {"checked": True, "update": None}


def test_a_second_copy_finds_the_first_instead_of_starting(server):
    port = int(server.rsplit(":", 1)[1])
    assert web.already_running(port)
    assert web.start(port) is None  # the caller then just opens the running copy's page


def test_nothing_running_on_a_free_port():
    import socket
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]
    assert not web.already_running(free_port)


def test_quitting_warns_only_until_results_are_downloaded(server, fake_geocoder, monkeypatch):
    monkeypatch.setattr(web, "downloaded", set())
    assert not web.unsaved_results()
    fake_geocoder["1660 Tully Rd, San Jose, CA 95122"] = POINTS["tully_rd_san_jose"]
    run_and_wait(server, "pasted list", "1660 Tully Rd, San Jose, CA 95122\n")
    assert web.unsaved_results()
    get(f"{server}/download/results")
    assert not web.unsaved_results()
