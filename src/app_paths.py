"""Where the app's files are, whether it runs from this project folder or as
an installed app.

The files it only reads (the prepared maps, the app window's page, the icon)
sit in the project folder when run from source. In an installed app they're
inside the app itself, where PyInstaller unpacks them to sys._MEIPASS.

The one file it writes, the geocode cache, stays in data/ when run from
source, as it always has. An installed app can't write inside itself, and an
update would replace it anyway, so there the cache goes in the usual per-user
place for app data and survives updates.
"""

import os
import sys
from pathlib import Path

INSTALLED = getattr(sys, "frozen", False)
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
DATA_DIR = ROOT / "data"


def user_data_dir(platform: str = sys.platform, env: dict = os.environ,
                  home: Path | None = None) -> Path:
    """Each system's usual folder for an app's own files."""
    home = home or Path.home()
    if platform == "darwin":
        return home / "Library" / "Application Support" / "District Lookup"
    if platform == "win32":
        return Path(env.get("LOCALAPPDATA") or home / "AppData" / "Local") / "District Lookup"
    return Path(env.get("XDG_DATA_HOME") or home / ".local" / "share") / "district-lookup"


def cache_path() -> Path:
    if INSTALLED:
        return user_data_dir() / "geocode_cache.sqlite"
    return DATA_DIR / "geocode_cache.sqlite"
