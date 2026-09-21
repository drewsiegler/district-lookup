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
        required_city = results.get(layer["same_city_as"]) if layer["same_city_as"] else None
        match = None
        if not layer["same_city_as"] or required_city:
            for idx in gdf.sindex.query(point, predicate="intersects"):
                row = gdf.iloc[idx]
                if required_city and row["city"] != required_city:
                    continue
                if row.geometry.contains(point):
                    match = row[DISPLAY_COLUMN]
                    break
        results[layer["id"]] = match
    return results
