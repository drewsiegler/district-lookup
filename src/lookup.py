"""Point-in-polygon matching: given a geocoded (lat, lon), find which
district each registered layer places it in."""

from shapely.geometry import Point

from layers import DISPLAY_COLUMN


def lookup_point(layers: list[dict], lat: float, lon: float) -> dict:
    """Returns {layer_id: formatted_district_or_None} for every registered layer."""
    point = Point(lon, lat)  # shapely takes (x, y) = (lon, lat)
    results = {}
    for layer in layers:
        gdf = layer["gdf"]
        must_match = layer["must_match"]
        # e.g. the official city for a council district, or the school district
        # for a trustee area — whatever this layer's features have to agree with.
        required = results.get(must_match["layer"]) if must_match else None
        match = None
        if not must_match or required:
            for idx in gdf.sindex.query(point, predicate="intersects"):
                row = gdf.iloc[idx]
                if required and row[must_match["column"]] != required:
                    continue
                if row.geometry.contains(point):
                    match = row[DISPLAY_COLUMN]
                    break
        results[layer["id"]] = match
    return results
