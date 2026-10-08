"""The layer registry: which boundary layers the app knows about, which
attribute on each holds its district name, and how that value is written in
the output.

Reads data/districts/<layer>.json, which scripts/build_gpkg.py writes from the
boundary files. Those hold plain GeoJSON geometry already in lat/lon, so
looking an address up needs only Shapely — no GeoPandas, GDAL or PROJ. Those
are the maintainer's tools for preparing maps, not the app's for using them,
which keeps the app small enough to hand to someone without Python installed.

Registry entry fields:
    id          layer name (also the output column name)
    label       human-readable description
    name_field  attribute holding the district's name or number
    format      optional output template; "{}" is the value, "{:02d}" zero-pads
                a number to two digits (e.g. "SD{:02d}" turns "015" into "SD15")
    pattern     optional regex with named groups, for pulling pieces out of a
                longer value; format then refers to the groups by name
                (e.g. "D{num}—Sup. {name}")
    coverage    optional true: this layer's footprint is the whole area the
                tool covers (see main.py's outside_coverage_area check)
    must_match  optional {"layer": <id of an earlier layer>, "column": <attribute
                on this layer>}. A feature only counts if that attribute equals
                the earlier layer's value for the address. Council districts
                must match the official city, trustee areas must match the
                school district, so an area is left blank outside the
                jurisdiction that drew it and never borrowed from a neighbor
                where two agencies' boundary lines disagree.
"""

import json
import math
import re

from shapely import STRtree
from shapely.geometry import shape

from app_paths import DATA_DIR

GPKG_PATH = DATA_DIR / "districts.gpkg"
RUNTIME_DIR = DATA_DIR / "districts"
REGISTRY_PATH = DATA_DIR / "layers.json"


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


def read_layer_features(layer_id: str) -> list[dict]:
    path = RUNTIME_DIR / f"{layer_id}.json"
    if not path.exists():
        raise ValueError(
            f"Layer '{layer_id}' is registered in {REGISTRY_PATH.name} but hasn't been "
            f"built into {RUNTIME_DIR.name}/ yet. Re-run scripts/build_gpkg.py."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)["features"]


def load_layers() -> list[dict]:
    """Loads every registered layer into memory with each feature's output
    value formatted and a spatial index built."""
    registry = read_registry()
    if not registry:
        return []

    loaded = []
    for entry in registry:
        layer_id = entry["id"]
        name_field = entry.get("name_field")
        if not name_field:
            print(f"Skipping layer '{layer_id}': no name_field set in {REGISTRY_PATH.name} yet.")
            continue

        features = read_layer_features(layer_id)
        attributes = [f["properties"] for f in features]
        available = sorted({key for props in attributes for key in props})
        if name_field not in available:
            raise ValueError(
                f"Layer '{layer_id}' has no attribute '{name_field}'. Available: {available}"
            )

        fmt, pattern = entry.get("format"), entry.get("pattern")
        try:
            display = [format_value(props.get(name_field), fmt, pattern) for props in attributes]
        except (ValueError, KeyError, IndexError) as err:
            raise ValueError(f"Layer '{layer_id}': can't apply format {fmt!r}: {err}") from err

        must_match = entry.get("must_match")
        scope = [None] * len(features)
        if must_match:
            check_must_match(layer_id, available, attributes, must_match, loaded)
            scope = [clean_value(props.get(must_match["column"])) for props in attributes]

        geometries = [shape(f["geometry"]) for f in features]
        loaded.append({
            "id": layer_id,
            "label": entry.get("label", layer_id),
            "coverage": bool(entry.get("coverage")),
            "must_match": must_match,
            # The jurisdictions this layer actually holds a map for, so main.py
            # can tell "no map for this district yet" from "map exists but has
            # a hole where this address falls".
            "mapped": {s for s in scope if s},
            "display": display,
            "scope": scope,
            "geometries": geometries,
            "tree": STRtree(geometries),
        })
    return loaded


def check_must_match(layer_id: str, available: list[str], attributes: list[dict],
                     must_match: dict, loaded: list[dict]) -> None:
    other_id, column = must_match["layer"], must_match["column"]
    other = next((layer for layer in loaded if layer["id"] == other_id), None)
    if other is None:
        raise ValueError(
            f"Layer '{layer_id}': must_match layer '{other_id}' has to be listed "
            f"above it in {REGISTRY_PATH.name}."
        )
    if column not in available:
        raise ValueError(f"Layer '{layer_id}' uses must_match but has no '{column}' attribute.")
    known = {value for value in other["display"] if value}
    unknown = sorted({clean_value(props.get(column)) for props in attributes} - known - {None})
    if unknown:
        raise ValueError(
            f"Layer '{layer_id}': {column} {unknown} doesn't match any value in "
            f"'{other_id}' (check spelling). Known values: {sorted(known)}"
        )


def coverage_layer_ids(layers: list[dict]) -> list[str]:
    """IDs of layers marked "coverage": true in the registry — layers whose
    footprint defines the whole area this tool is meant to cover (e.g. the
    county), with no gaps. Used to flag addresses that geocoded successfully
    but fell outside every one of them, i.e. outside the area entirely."""
    return [layer["id"] for layer in layers if layer["coverage"]]
