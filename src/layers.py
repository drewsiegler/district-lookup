"""The layer registry: which boundary layers live in data/districts.gpkg,
which attribute column on each holds its district name, and how that value is
written in the output. scripts/build_gpkg.py adds new layers automatically;
set name_field (and optionally format/pattern) by hand.

Registry entry fields:
    id          layer name inside districts.gpkg (also the output column name)
    label       human-readable description
    name_field  column holding the district's name or number
    format      optional output template; "{}" is the value, "{:02d}" zero-pads
                a number to two digits (e.g. "SD{:02d}" turns "015" into "SD15")
    pattern     optional regex with named groups, for pulling pieces out of a
                longer value; format then refers to the groups by name
                (e.g. "D{num}—Sup. {name}")
    coverage    optional true: this layer's footprint is the whole area the
                tool covers (see main.py's outside_coverage_area check)
    same_city_as  optional id of an earlier layer (the city layer). A feature
                only counts if its "city" column equals that layer's value
                for the address, so a council district is left blank on
                unincorporated land and never borrowed from a neighboring
                city where two agencies' boundary lines disagree.
"""

import json
import math
import re
from pathlib import Path

import geopandas as gpd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GPKG_PATH = DATA_DIR / "districts.gpkg"
REGISTRY_PATH = DATA_DIR / "layers.json"
DISPLAY_COLUMN = "_display"


def read_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f).get("layers", [])


def write_registry(layers: list[dict]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump({"layers": layers}, f, indent=2, ensure_ascii=False)
        f.write("\n")


def clean_value(value) -> str | None:
    """Source value as trimmed text: 3.0 -> "3", blanks and NaN -> None."""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if value.is_integer():
            value = int(value)
    text = str(value).strip()
    return text or None


def format_value(value, fmt: str | None = None, pattern: str | None = None) -> str | None:
    text = clean_value(value)
    if text is None or fmt is None:
        return text
    if pattern:
        match = re.fullmatch(pattern, text)
        if not match:
            raise ValueError(f"{text!r} doesn't match pattern {pattern!r}")
        return fmt.format(**{k: v.strip() for k, v in match.groupdict().items()})
    return fmt.format(int(text) if text.isdigit() else text)


def load_layers() -> list[dict]:
    """Loads every registered layer's geometry into memory, reprojected to
    EPSG:4326 (plain lat/lon) so it matches the geocoder's coordinates, with
    each feature's output value pre-formatted and a spatial index built."""
    registry = read_registry()
    if not registry:
        return []
    if not GPKG_PATH.exists():
        raise FileNotFoundError(
            f"{GPKG_PATH} doesn't exist yet. Run scripts/build_gpkg.py after adding "
            "boundary files to data/raw_geojson/."
        )

    loaded = []
    for entry in registry:
        layer_id = entry["id"]
        name_field = entry.get("name_field")
        if not name_field:
            print(f"Skipping layer '{layer_id}': no name_field set in {REGISTRY_PATH.name} yet.")
            continue
        gdf = gpd.read_file(GPKG_PATH, layer=layer_id)
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        if name_field not in gdf.columns:
            raise ValueError(
                f"Layer '{layer_id}' has no column '{name_field}'. "
                f"Available columns: {list(gdf.columns)}"
            )
        fmt, pattern = entry.get("format"), entry.get("pattern")
        try:
            gdf[DISPLAY_COLUMN] = [format_value(v, fmt, pattern) for v in gdf[name_field]]
        except (ValueError, KeyError, IndexError) as err:
            raise ValueError(f"Layer '{layer_id}': can't apply format {fmt!r}: {err}") from err
        same_city_as = entry.get("same_city_as")
        if same_city_as:
            check_same_city(layer_id, gdf, same_city_as, loaded)
        gdf.sindex  # build the spatial index once, up front
        loaded.append({
            "id": layer_id,
            "label": entry.get("label", layer_id),
            "coverage": bool(entry.get("coverage")),
            "same_city_as": same_city_as,
            "cities": set(gdf["city"].dropna()) if same_city_as else set(),
            "gdf": gdf,
        })
    return loaded


def check_same_city(layer_id: str, gdf, city_layer_id: str, loaded: list[dict]) -> None:
    city_layer = next((layer for layer in loaded if layer["id"] == city_layer_id), None)
    if city_layer is None:
        raise ValueError(
            f"Layer '{layer_id}': same_city_as '{city_layer_id}' must be a layer listed "
            f"above it in {REGISTRY_PATH.name}."
        )
    if "city" not in gdf.columns:
        raise ValueError(f"Layer '{layer_id}' uses same_city_as but has no 'city' column.")
    known = set(city_layer["gdf"][DISPLAY_COLUMN].dropna())
    unknown = sorted(set(gdf["city"].dropna()) - known)
    if unknown:
        raise ValueError(
            f"Layer '{layer_id}': city {unknown} doesn't match any value in '{city_layer_id}' "
            f"(check spelling). Known cities: {sorted(known)}"
        )


def coverage_layer_ids(layers: list[dict]) -> list[str]:
    """IDs of layers marked "coverage": true in the registry — layers whose
    footprint defines the whole area this tool is meant to cover (e.g. the
    county), with no gaps. Used to flag addresses that geocoded successfully
    but fell outside every one of them, i.e. outside the area entirely."""
    return [layer["id"] for layer in layers if layer["coverage"]]
