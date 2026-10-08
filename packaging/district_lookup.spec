# PyInstaller recipe for the installed app, the same on every system:
#     python -m PyInstaller --noconfirm --clean packaging/district_lookup.spec
# It bundles Python, src/launcher.py and everything it imports, plus the files
# the app reads (the prepared maps, the page, the icon) into dist/District Lookup/,
# and on macOS into dist/District Lookup.app. The per-system scripts beside this
# file then wrap that in a .dmg, an installer or a .deb.
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
sys.path.insert(0, str(ROOT / "src"))
from about import VERSION  # noqa: E402

NAME = "District Lookup"
# Linux commands conventionally have no spaces or capitals.
EXE_NAME = "district-lookup" if sys.platform.startswith("linux") else NAME

a = Analysis(
    [str(ROOT / "src" / "launcher.py")],
    pathex=[str(ROOT / "src")],
    datas=[
        (str(ROOT / "data" / "districts"), "data/districts"),
        (str(ROOT / "data" / "layers.json"), "data"),
        (str(ROOT / "src" / "web_page.html"), "src"),
        (str(ROOT / "assets" / "AppIcon.png"), "assets"),
    ],
    # The map-building toolchain is never part of the app (see requirements-build.txt).
    excludes=["geopandas", "pyogrio", "pandas", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=EXE_NAME,
    console=False,  # the app shows its own small window instead of a terminal
    icon=str(ROOT / "assets" / ("AppIcon.icns" if sys.platform == "darwin" else "AppIcon.ico")),
)
coll = COLLECT(exe, a.binaries, a.datas, name=NAME)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{NAME}.app",
        icon=str(ROOT / "assets" / "AppIcon.icns"),
        bundle_identifier="io.github.drewsiegler.districtlookup",
        version=VERSION,
        info_plist={
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSApplicationCategoryType": "public.app-category.productivity",
        },
    )
