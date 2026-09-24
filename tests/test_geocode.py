"""Batch geocoding: cache first, then the Census batch service, then one at a
time for anything the batch didn't match. HTTP is faked throughout."""

import csv
import io

import pytest
import requests

import geocode


class FakeCensus:
    """Answers both Census endpoints from a table of {address: (lon, lat)}.
    Addresses in batch_misses come back No_Match from the batch service but
    still match one at a time, like the service's spurious misses."""

    def __init__(self, known, batch_misses=(), batch_fails=False):
        self.known, self.batch_misses, self.batch_fails = known, set(batch_misses), batch_fails
        self.batch_calls, self.single_calls = [], []

    def post(self, url, data=None, files=None, timeout=None):
        assert url == geocode.BATCH_URL
        rows = list(csv.reader(io.StringIO(files["addressFile"][1])))
        self.batch_calls.append([r[1] for r in rows])
        if self.batch_fails:
            raise requests.ConnectionError("service down")
        out = io.StringIO()
        writer = csv.writer(out)
        for row_id, address, *_ in rows:
            if address in self.known and address not in self.batch_misses:
                lon, lat = self.known[address]
                writer.writerow([row_id, address, "Match", "Exact", address.upper(), f"{lon},{lat}", "1", "L"])
            else:
                writer.writerow([row_id, address, "No_Match"])
        return _Response(text=out.getvalue())

    def get(self, url, params=None, timeout=None):
        assert url == geocode.ONE_ADDRESS_URL
        address = params["address"]
        self.single_calls.append(address)
        matches = []
        if address in self.known:
            lon, lat = self.known[address]
            matches = [{"matchedAddress": address.upper(), "coordinates": {"x": lon, "y": lat}}]
        return _Response(payload={"result": {"addressMatches": matches}})


class _Response:
    def __init__(self, text="", payload=None):
        self.text, self._payload = text, payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def census(monkeypatch):
    def install(known, **kwargs):
        fake = FakeCensus(known, **kwargs)
        monkeypatch.setattr(requests, "post", fake.post)
        monkeypatch.setattr(requests, "get", fake.get)
        return fake
    monkeypatch.setattr(geocode, "REQUEST_DELAY_SECONDS", 0)
    return install


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(geocode, "CACHE_PATH", tmp_path / "cache.sqlite")
    connection = geocode._get_cache_conn()
    yield connection
    connection.close()


A, B, C = "1 A St, San Jose, CA", "2 B St, San Jose, CA", "3 C St, San Jose, CA"
KNOWN = {A: (-121.1, 37.1), B: (-121.2, 37.2), C: (-121.3, 37.3)}


def test_new_addresses_go_out_as_one_batch(census, conn):
    fake = census(KNOWN)
    results = geocode.geocode_many([A, B, C], conn)
    assert len(fake.batch_calls) == 1 and not fake.single_calls
    assert results[B] == {"matched": True, "matched_address": B.upper(), "lat": 37.2, "lon": -121.2}


def test_cached_addresses_never_reach_the_network(census, conn):
    census(KNOWN)
    geocode.geocode_many([A, B], conn)
    fake = census(KNOWN)  # a fresh fake records only what the second run asks for
    geocode.geocode_many([A, B], conn)
    assert not fake.batch_calls and not fake.single_calls


def test_batch_misses_are_retried_one_at_a_time(census, conn):
    fake = census(KNOWN, batch_misses={B})
    results = geocode.geocode_many([A, B], conn)
    assert fake.single_calls == [B]
    assert results[B]["matched"]


def test_a_failed_batch_falls_back_to_one_at_a_time(census, conn):
    fake = census(KNOWN, batch_fails=True)
    results = geocode.geocode_many([A, B], conn)
    assert sorted(fake.single_calls) == sorted([A, B])
    assert all(r["matched"] for r in results.values())


def test_genuine_misses_are_cached_so_they_are_asked_about_once(census, conn):
    census(KNOWN)
    assert not geocode.geocode_many(["nowhere"], conn)["nowhere"]["matched"]
    fake = census(KNOWN)
    geocode.geocode_many(["nowhere"], conn)
    assert not fake.batch_calls and not fake.single_calls


def test_large_lists_are_split_into_batches(census, conn, monkeypatch):
    monkeypatch.setattr(geocode, "BATCH_SIZE", 2)
    fake = census(KNOWN)
    geocode.geocode_many([A, B, C], conn)
    assert [len(call) for call in fake.batch_calls] == [2, 1]


def test_duplicates_and_blanks_are_not_sent(census, conn):
    fake = census(KNOWN)
    results = geocode.geocode_many([A, "", A, B, None, B], conn)
    assert fake.batch_calls == [[A, B]]
    assert set(results) == {A, B}


def test_progress_counts_distinct_addresses_up_to_the_total(census, conn, monkeypatch):
    monkeypatch.setattr(geocode, "BATCH_SIZE", 2)
    census(KNOWN)
    geocode.geocode_many([A], conn)  # cached before the run being measured
    seen = []
    geocode.geocode_many([A, B, C, C], conn, on_progress=lambda done, total: seen.append((done, total)))
    assert seen == [(1, 3), (3, 3)]
