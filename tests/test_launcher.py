"""The installed app's starting point. Its window needs a screen, so only the
parts that don't are tested here; the build runs the self-test on every
finished app."""

import pytest

import launcher


def test_self_test_passes_with_the_real_maps(layers, monkeypatch):
    monkeypatch.setattr(launcher, "load_layers", lambda: layers)  # already loaded once for the session
    assert launcher.self_test() == 0


def test_self_test_reports_a_problem_without_crashing(monkeypatch):
    def broken(*args):
        raise RuntimeError("maps missing")
    monkeypatch.setattr(launcher, "load_layers", broken)
    assert launcher.self_test() == 1


def test_self_test_flag_exits_with_its_result(monkeypatch):
    monkeypatch.setattr(launcher, "self_test", lambda: 0)
    monkeypatch.setattr(launcher.sys, "argv", ["launcher.py", "--self-test"])
    with pytest.raises(SystemExit) as exited:
        launcher.main()
    assert exited.value.code == 0
