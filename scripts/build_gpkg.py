"""Rebuilds data/districts.gpkg from everything in data/raw_geojson/, and keeps
data/layers.json in sync: new layers are registered, and layers that no longer
come out of the build are removed.

Two ways a GeoJSON file becomes a layer:

1. On its own — the default. A file already containing every feature of one
   district type (e.g. all 5 county supervisorial districts in one file)
   becomes a layer named after the file (minus the extension). Its registry
   entry starts with name_field blank for you to fill in.

2. Merged with others — for one kind of district where each agency's map is
   its own file but they all share an output column: city council districts
   (one file per city) and trustee areas (one file per school district). List
   the group in data/layer_sources.json, saying for each file which column
   holds its district number:

       {
         "merge_groups": {
           "council_district": [
             {"file": "san_jose_council.geojson", "name_field": "DISTRICT", "city": "San Jose"}
           ],
           "high_school_trustee_area": [
             {"file": "campbell_union_hsd_trustee_areas.geojson", "name_field": "TRUSTEEARE"}
           ]
         }
       }

   The group becomes one layer with a single "district_name" column holding
   the number, however each agency named its own field, plus "source_file"
   (and "city" or "district", if the entries give one — see "must_match" in
   src/layers.py). Its registry entry is filled in automatically; groups named
   "*_trustee_area" also get format "TA{}" (area 3 is written "TA3"). Files
   listed in a group are skipped by the one-file-one-layer pass. Only group
   boundaries that never overlap each other (districts of the same type do
   not), since an address takes the first match.

Safe to re-run any time you add, replace, or remove files. Existing registry
entries keep their label, name_field, and order.

Usage:
    python scripts/build_gpkg.py
"""

import json
import re
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from layers import DATA_DIR, GPKG_PATH, REGISTRY_PATH, clean_value, read_registry, write_registry

RAW_DIR = DATA_DIR / "raw_geojson"
SOURCES_PATH = DATA_DIR / "layer_sources.json"
MERGED_NAME_FIELD = "district_name"


def default_format(group_name: str) -> str | None:
    return "TA{}" if group_name.endswith("_trustee_area") else None


def load_and_normalize(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)  # assume plain lat/lon if the file doesn't say
    else:
        gdf = gdf.to_crs(epsg=4326)
    # GeoPackage reserves "fid" for its own feature ID; ArcGIS exports often carry one.
    reserved = {c: f"source_{c.lower()}" for c in gdf.columns if c.lower() == "fid"}
    return gdf.rename(columns=reserved)


def read_merge_groups() -> dict:
    if not SOURCES_PATH.exists():
        return {}
    with open(SOURCES_PATH, encoding="utf-8") as f:
        return json.load(f).get("merge_groups", {})


def extract_number(text: str | None, regex: str, filename: str) -> str | None:
    """Pulls the district number out of a longer value, e.g. "Trustee Area C1" -> "1"."""
    if text is None:
        return None
    match = re.search(regex, text)
    if not match:
        sys.exit(f"{filename}: value {text!r} doesn't match extract pattern {regex!r}")
    return match.group(1) if match.groups() else match.group(0)


def build_merged_layer(group_name: str, entries: list[dict]) -> gpd.GeoDataFrame | None:
    parts = []
    for entry in entries:
        path = RAW_DIR / entry["file"]
        if not path.exists():
            print(f"Warning: {path.name} listed in merge group '{group_name}' but not found, skipping.")
            continue
        gdf = load_and_normalize(path)
        if entry["name_field"] not in gdf.columns:
            sys.exit(
                f"{path.name} (merge group '{group_name}') has no column '{entry['name_field']}'. "
                f"Available columns: {[c for c in gdf.columns if c != 'geometry']}"
            )
        values = [clean_value(v) for v in gdf[entry["name_field"]]]
        if "extract" in entry:
            values = [extract_number(v, entry["extract"], entry["file"]) for v in values]
        columns = {MERGED_NAME_FIELD: values, "source_file": entry["file"]}
        # Whichever jurisdiction the file belongs to, checked at lookup time
        # against the column beside it (see must_match in src/layers.py).
        for scope in ("city", "district"):
            if scope in entry:
                columns[scope] = entry[scope]
        parts.append(gpd.GeoDataFrame({**columns, "geometry": gdf.geometry}, crs="EPSG:4326"))
    if not parts:
        return None
    return gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs="EPSG:4326")


def main():
    if not RAW_DIR.exists() or not any(RAW_DIR.glob("*.geojson")):
        print(f"No .geojson files found in {RAW_DIR}. Add some boundary files first.")
        sys.exit(1)

    merge_groups = read_merge_groups()
    grouped_files = {entry["file"] for entries in merge_groups.values() for entry in entries}

    layer_frames = {}  # layer_name -> GeoDataFrame

    for path in sorted(RAW_DIR.glob("*.geojson")):
        if path.name not in grouped_files:
            layer_frames[path.stem] = load_and_normalize(path)

    merged_layers = set()
    for group_name, entries in merge_groups.items():
        gdf = build_merged_layer(group_name, entries)
        if gdf is not None:
            layer_frames[group_name] = gdf
            merged_layers.add(group_name)

    if not layer_frames:
        print("Nothing to build.")
        sys.exit(1)

    # Build into a fresh file and swap it in, so layers whose source was removed
    # or moved into a merge group don't linger, and a failed build leaves the
    # previous districts.gpkg untouched.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = DATA_DIR / "districts.building.gpkg"
    tmp_path.unlink(missing_ok=True)
    for layer_name, gdf in layer_frames.items():
        gdf.to_file(tmp_path, layer=layer_name, driver="GPKG")
        print(f"  {layer_name}: {len(gdf)} feature(s), columns: {[c for c in gdf.columns if c != 'geometry']}")
    tmp_path.replace(GPKG_PATH)

    registry = read_registry()
    removed = [e["id"] for e in registry if e["id"] not in layer_frames]
    registry = [e for e in registry if e["id"] in layer_frames]
    existing_ids = {e["id"] for e in registry}
    added, needs_field = [], []
    for layer_name in layer_frames:
        if layer_name in existing_ids:
            continue
        is_merged = layer_name in merged_layers
        entry = {"id": layer_name, "label": layer_name.replace("_", " ").title()}
        entry["name_field"] = MERGED_NAME_FIELD if is_merged else None
        if is_merged and default_format(layer_name):
            entry["format"] = default_format(layer_name)
        registry.append(entry)
        added.append(layer_name)
        if not is_merged:
            needs_field.append(layer_name)
    write_registry(registry)

    print(f"\nWrote {len(layer_frames)} layer(s) to {GPKG_PATH}")
    if added:
        print(f"Added to {REGISTRY_PATH.name}: {', '.join(added)}")
    if removed:
        print(f"Removed from {REGISTRY_PATH.name} (no longer built): {', '.join(removed)}")
    if needs_field:
        print(f"\nStill need a name_field in {REGISTRY_PATH.name}: {', '.join(needs_field)}")
        print("Fill in which column holds each layer's district name (see the columns printed above).")


if __name__ == "__main__":
    main()
