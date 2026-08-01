"""
Tests for the curated example-registry export.

The whole point of shipping example data is that a stranger can clone the repo
and have the derivers run. So the slice has to be *coherent*, not merely small:
a record whose edges point at entities that were left behind loads fine and then
breaks the first deriver that walks the graph. Every test here is about that
closure property, plus the guarantee that curation never edits the source.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.graph_view import build_graph  # noqa: E402
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402
from layer5_dna_substrate.showcase import (  # noqa: E402
    build_showcase, resolve_names, summarise,
)


@pytest.fixture
def data(tmp_path):
    reg = DNARegistry()
    world = reg.register_element("world", "W{}", "World prose.", name="Skarn",
                                 tags=["canonized"])
    region = reg.register_element("region", "R{}", "Region prose.",
                                  name="The Ash Wastes", tags=["canonized"])
    npc = reg.register_element("npc", "N{}", "NPC prose.", name="Corin")
    far = reg.register_element("item", "I{}", "Item prose.", name="Unrelated Relic")
    reg.link_elements(world, region, "parent", label="contains")
    reg.link_elements(region, npc, "peer", label="mentions_Corin")

    stub = reg.register_element("lore", "", "", name=None, tags=["stub", f"from_{npc}"])
    reg.get_element(stub)["stub_metadata"] = {
        "name": "Vow of the Blank Page", "description": "A creed.",
        "source_id": npc}

    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    return json.loads(path.read_text(encoding="utf-8")), {
        "world": world, "region": region, "npc": npc, "far": far, "stub": stub}


def test_only_the_named_entities_are_carried(data):
    raw, ids = data
    out = build_showcase(raw, ["Skarn", "The Ash Wastes"])

    assert set(out["records"]) == {ids["world"], ids["region"]}


def test_an_unknown_name_is_an_error_not_a_silent_omission(data):
    raw, _ = data
    with pytest.raises(KeyError, match="Nonexistent Place"):
        build_showcase(raw, ["Skarn", "Nonexistent Place"])


def test_edges_to_excluded_entities_are_pruned(data):
    """A dangling edge loads fine and then breaks every deriver that walks it."""
    raw, ids = data
    out = build_showcase(raw, ["The Ash Wastes"])
    targets = {i["id"] for rels in out["edges"].values()
               for items in rels.values() for i in items}

    assert targets <= set(out["records"])
    assert ids["npc"] not in targets


def test_neighbours_pulls_in_what_the_selection_points_at(data):
    raw, ids = data
    out = build_showcase(raw, ["The Ash Wastes"], include_neighbours=True)

    assert ids["world"] in out["records"], "its container"
    assert ids["npc"] in out["records"], "what it mentions"
    assert ids["far"] not in out["records"], "unrelated things stay out"


def test_a_stub_whose_source_is_gone_does_not_point_into_nothing(data):
    raw, ids = data
    out = build_showcase(raw, ["Vow of the Blank Page"])
    record = out["records"][ids["stub"]]

    assert record["stub_metadata"]["source_id"] is None
    assert not [t for t in record["tags"] if t.startswith("from_")]


def test_a_stub_whose_source_is_kept_retains_it(data):
    raw, ids = data
    out = build_showcase(raw, ["Vow of the Blank Page", "Corin"])
    record = out["records"][ids["stub"]]

    assert record["stub_metadata"]["source_id"] == ids["npc"]
    assert f"from_{ids['npc']}" in record["tags"]


def test_the_slice_loads_as_a_registry_and_derives(data):
    """The acceptance test: a stranger clones, and the derivers run."""
    raw, _ = data
    out = build_showcase(raw, ["Skarn"], include_neighbours=True)
    graph = build_graph(out)

    assert graph["nodes"]
    known = {n["id"] for n in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in known and edge["target"] in known


def test_dropping_fields_removes_the_prose(data):
    raw, _ = data
    out = build_showcase(raw, ["Skarn"], drop_fields={"phenotype"})

    assert summarise(out)["prose_chars"] == 0
    assert all("phenotype" not in r for r in out["records"].values())


def test_the_source_registry_is_never_mutated(data):
    raw, ids = data
    before = json.dumps(raw, sort_keys=True)
    build_showcase(raw, ["Vow of the Blank Page"], include_neighbours=True,
                   drop_fields={"phenotype"})

    assert json.dumps(raw, sort_keys=True) == before


def test_export_is_deterministic(data):
    raw, _ = data
    first = build_showcase(raw, ["Skarn"], include_neighbours=True)
    second = build_showcase(raw, ["Skarn"], include_neighbours=True)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_resolve_names_prefers_a_real_name_over_stub_metadata(data):
    raw, ids = data

    assert resolve_names(raw, ["Corin"])["Corin"] == ids["npc"]
    assert resolve_names(raw, ["Vow of the Blank Page"])[
        "Vow of the Blank Page"] == ids["stub"]
