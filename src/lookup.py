"""Point-in-polygon matching: given a geocoded (lat, lon), find which
district each registered layer places it in."""

from shapely.geometry import Point


def lookup_point(layers: list[dict], lat: float, lon: float) -> dict:
    """Returns {layer_id: formatted_district_or_None} for every registered layer."""
    point = Point(lon, lat)  # shapely takes (x, y) = (lon, lat)
    results = {}
    for layer in layers:
        must_match = layer["must_match"]
        # e.g. the official city for a council district, or the school district
        # for a trustee area — whatever this layer's features have to agree with.
        required = results.get(must_match["layer"]) if must_match else None
        match = None
        if not must_match or required:
            for idx in layer["tree"].query(point):
                if required and layer["scope"][idx] != required:
                    continue
                if layer["geometries"][idx].contains(point):
                    match = layer["display"][idx]
                    break
        results[layer["id"]] = match
    return results
