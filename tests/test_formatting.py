"""How district values are written in the output."""

import pytest

from layers import clean_value, format_value


@pytest.mark.parametrize("value, expected", [
    (3, "3"), (3.0, "3"), (" 3 ", "3"), ("B", "B"),
    (None, None), (float("nan"), None), ("", None), ("   ", None),
])
def test_clean_value(value, expected):
    assert clean_value(value) == expected


@pytest.mark.parametrize("value, fmt, expected", [
    ("16", "US-CA{:02d}", "US-CA16"),
    ("015", "SD{:02d}", "SD15"),   # TIGER stores state districts zero-padded to 3
    ("004", "SD{:02d}", "SD04"),   # "##" means two digits, per the output conventions
    ("025", "AD{:02d}", "AD25"),
    ("3", "TA{}", "TA3"),
    (3.0, "TA{}", "TA3"),
    ("C", None, "C"),              # Morgan Hill council districts are letters
])
def test_formats(value, fmt, expected):
    assert format_value(value, fmt) == expected


def test_county_supervisor_pattern():
    pattern = r"District (?P<num>\d+)\s*[—–-]\s*Supervisor (?P<name>.+)"
    assert format_value("District 2 — Supervisor Betty Duong", "D{num}—Sup. {name}", pattern) \
        == "D2—Sup. Betty Duong"


def test_blank_values_stay_blank_even_with_a_format():
    assert format_value(None, "TA{}") is None
    assert format_value("", "SD{:02d}") is None


def test_value_that_does_not_fit_its_format_raises():
    with pytest.raises(ValueError):
        format_value("B", "SD{:02d}")


def test_value_that_does_not_match_its_pattern_raises():
    with pytest.raises(ValueError, match="doesn't match pattern"):
        format_value("Area 2", "D{num}", r"District (?P<num>\d+)")
