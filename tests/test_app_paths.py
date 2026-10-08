"""Where the app keeps its files, run from source or installed."""

from pathlib import Path

import app_paths


def test_from_source_the_cache_stays_in_the_project_data_folder():
    assert not app_paths.INSTALLED
    assert app_paths.cache_path() == app_paths.DATA_DIR / "geocode_cache.sqlite"
    assert (app_paths.DATA_DIR / "layers.json").exists()


def test_installed_apps_keep_the_cache_where_each_system_expects():
    home = Path("/home/organizer")
    assert app_paths.user_data_dir("darwin", {}, home) == \
        home / "Library" / "Application Support" / "District Lookup"
    assert app_paths.user_data_dir("win32", {"LOCALAPPDATA": r"C:\Users\o\AppData\Local"}, home) == \
        Path(r"C:\Users\o\AppData\Local") / "District Lookup"
    assert app_paths.user_data_dir("linux", {}, home) == home / ".local" / "share" / "district-lookup"
    assert app_paths.user_data_dir("linux", {"XDG_DATA_HOME": "/xdg"}, home) == \
        Path("/xdg") / "district-lookup"


def test_installed_app_uses_its_user_data_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(app_paths, "INSTALLED", True)
    monkeypatch.setattr(app_paths, "user_data_dir", lambda: tmp_path)
    assert app_paths.cache_path() == tmp_path / "geocode_cache.sqlite"
