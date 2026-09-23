"""The registry's safety checks: a misconfigured layer should stop the run
with a clear message, never write wrong values partway through a batch."""

import json

import pytest

import layers as layers_module
from layers import check_must_match, load_layers, read_registry


@pytest.fixture
def registry(tmp_path, monkeypatch):
    """A copy of the real registry to break on purpose. Call it with a function
    that edits the list of entries; load_layers() then reads the edited copy."""
    def edit(change):
        entries = read_registry()
        change(entries)
        path = tmp_path / "layers.json"
        path.write_text(json.dumps({"layers": entries}), encoding="utf-8")
        monkeypatch.setattr(layers_module, "REGISTRY_PATH", path)
    return edit


def entry(entries, layer_id):
    return next(e for e in entries if e["id"] == layer_id)


def test_real_registry_is_consistent(layers):
    ids = [layer["id"] for layer in layers]
    assert len(ids) == len(set(ids))
    assert all(layer["geometries"] for layer in layers)
    assert any(layer["coverage"] for layer in layers)
    for layer in layers:
        if layer["id"].endswith("_trustee_area"):
            assert all(v is None or v.startswith("TA") for v in layer["display"])
            assert layer["must_match"], f"{layer['id']} should be tied to its school district"


def test_unknown_name_field_is_refused(registry):
    registry(lambda es: entry(es, "ca_state_senate").update(name_field="NOPE"))
    with pytest.raises(ValueError, match="'ca_state_senate' has no attribute 'NOPE'"):
        load_layers()


def test_format_that_does_not_fit_the_values_is_refused(registry):
    registry(lambda es: entry(es, "council_district").update(format="D{:02d}"))  # Morgan Hill uses letters
    with pytest.raises(ValueError, match="'council_district': can't apply format"):
        load_layers()


def test_must_match_layer_listed_below_is_refused(registry):
    def move_city_to_end(entries):
        city = entry(entries, "city")
        entries.remove(city)
        entries.append(city)
    registry(move_city_to_end)
    with pytest.raises(ValueError, match="has to be listed above it"):
        load_layers()


def test_layer_missing_from_built_data_asks_for_a_rebuild(registry):
    registry(lambda es: es.append({"id": "not_built_yet", "name_field": "X"}))
    with pytest.raises(ValueError, match="Re-run scripts/build_gpkg.py"):
        load_layers()


def test_misspelled_district_is_refused_with_the_valid_names(layers):
    school_districts = next(l for l in layers if l["id"] == "elementary_school_districts")
    attributes = [{"district": "Oak Grove School District"}]  # Census calls it "…Elementary School District"
    with pytest.raises(ValueError, match="doesn't match any value.*Oak Grove Elementary School District"):
        check_must_match("elementary_trustee_area", ["district"], attributes,
                         {"layer": "elementary_school_districts", "column": "district"},
                         [school_districts])
