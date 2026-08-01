"""
Tests for the world-graph deriver.

Two properties of the registry's edge store make this worth pinning down, because
getting either wrong produces a page that looks plausible and is wrong:

  * peer edges are written to BOTH endpoints, so every relationship appears twice
    in the store and must collapse to one line on the page;
  * containment is inverted from how it reads — link_elements(A, B, "parent")
    means A is the parent OF B and lands in edges[A]["parent"], so that list holds
    what A contains, not what contains A.

The rest guards the page itself: self-contained (no network of any kind), and
safe to embed the registry into, since gists are authored prose that may hold
anything including a literal </script>.
"""

import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.graph_view import (  # noqa: E402
    build_graph, render_html, write_html,
)
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402


@pytest.fixture
def registry():
    reg = DNARegistry()
    realm = reg.register_element("realm", "REALM{}", "body",
                                 name="The Sundered Reach", tags=["canonized"])
    city = reg.register_element("settlement", "SET{}", "body",
                                name="Emberhold", tags=["canonized"])
    npc = reg.register_element("npc", "NPC{}", "body", name="Archivist Kaelen")
    reg.get_element(npc)["gist"] = "Keeper of the deep stacks."

    reg.link_elements(realm, city, "parent", label="contains")
    reg.link_elements(city, npc, "peer", label="mentions_Archivist_Kaelen")

    stub = reg.register_element("lore", "", "", name=None, tags=["stub"])
    reg.get_element(stub)["stub_metadata"] = {
        "name": "The Litany of Ash", "description": "A doctrine sung at pyres.",
        "source_id": npc,
    }
    return reg, {"realm": realm, "city": city, "npc": npc, "stub": stub}


def test_every_record_becomes_a_node(registry, tmp_path):
    reg, ids = registry
    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    graph = build_graph(json.loads(path.read_text(encoding="utf-8")))

    assert len(graph["nodes"]) == 4
    assert {n["id"] for n in graph["nodes"]} == set(ids.values())


def test_peer_edges_are_not_drawn_twice(registry, tmp_path):
    """The store holds the peer link on both endpoints; the page must show one."""
    reg, ids = registry
    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    graph = build_graph(json.loads(path.read_text(encoding="utf-8")))

    peers = [e for e in graph["edges"] if e["kind"] == "peer"]
    assert len(peers) == 1
    assert {peers[0]["source"], peers[0]["target"]} == {ids["city"], ids["npc"]}
    assert peers[0]["label"] == "mentions_Archivist_Kaelen"


def test_containment_points_from_container_to_contained(registry, tmp_path):
    """edges[X]['parent'] lists what X CONTAINS -- the direction is easy to flip."""
    reg, ids = registry
    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    graph = build_graph(json.loads(path.read_text(encoding="utf-8")))

    contains = [e for e in graph["edges"] if e["kind"] == "contains"]
    assert len(contains) == 1, "the mirrored child entry must not add a second edge"
    assert contains[0]["source"] == ids["realm"]
    assert contains[0]["target"] == ids["city"]
    assert contains[0]["label"] == "contains"


def test_status_separates_canon_draft_and_stub(registry, tmp_path):
    reg, ids = registry
    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    by_id = {n["id"]: n for n in build_graph(
        json.loads(path.read_text(encoding="utf-8")))["nodes"]}

    assert by_id[ids["realm"]]["status"] == "canon"
    assert by_id[ids["npc"]]["status"] == "draft"
    assert by_id[ids["stub"]]["status"] == "stub"


def test_stubs_are_named_from_their_metadata(registry, tmp_path):
    """A stub's record has no name field -- only stub_metadata carries it."""
    reg, ids = registry
    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    by_id = {n["id"]: n for n in build_graph(
        json.loads(path.read_text(encoding="utf-8")))["nodes"]}

    assert by_id[ids["stub"]]["name"] == "The Litany of Ash"
    assert by_id[ids["stub"]]["gist"] == "A doctrine sung at pyres."


def test_degree_counts_both_directions(registry, tmp_path):
    reg, ids = registry
    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    by_id = {n["id"]: n for n in build_graph(
        json.loads(path.read_text(encoding="utf-8")))["nodes"]}

    assert by_id[ids["city"]]["degree"] == 2   # contained by realm, mentions npc
    assert by_id[ids["realm"]]["degree"] == 1
    assert by_id[ids["stub"]]["degree"] == 0


def test_edges_to_unknown_ids_are_dropped():
    """A dangling edge would put an undefined node in the JS and break the page."""
    data = {
        "records": {"a": {"id": "a", "type": "npc", "name": "A"}},
        "edges": {"a": {"peer": [{"id": "ghost", "label": "mentions_Ghost"}]}},
    }
    assert build_graph(data)["edges"] == []


def test_self_edges_are_dropped():
    data = {
        "records": {"a": {"id": "a", "type": "npc", "name": "A"}},
        "edges": {"a": {"peer": [{"id": "a", "label": "mentions_A"}]}},
    }
    assert build_graph(data)["edges"] == []


def test_empty_registry_renders():
    graph = build_graph({})
    assert graph == {"nodes": [], "edges": []}
    assert "<canvas" in render_html(graph)


def test_page_is_deterministic(registry, tmp_path):
    """A deriver that churns would make every regeneration a diff."""
    reg, _ = registry
    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    graph = build_graph(data)
    assert render_html(graph) == render_html(build_graph(data))


def test_page_makes_no_network_requests(registry, tmp_path):
    """Self-contained is the whole point: no CDN, no fonts, no fetch."""
    reg, _ = registry
    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    out = tmp_path / "graph.html"
    write_html(json.loads(path.read_text(encoding="utf-8")), str(out))
    page = out.read_text(encoding="utf-8")

    for forbidden in ("http://", "https://", "//cdn", "fetch(",
                      "XMLHttpRequest", "import(", "<link", "<img"):
        assert forbidden not in page, f"page reaches outside itself: {forbidden}"


def test_gist_containing_a_script_tag_cannot_break_out():
    """Gists are authored prose. A literal </script> in one must stay inert."""
    data = {
        "records": {"a": {"id": "a", "type": "lore", "name": "Bad",
                          "gist": "</script><script>alert(1)</script>"}},
        "edges": {},
    }
    page = render_html(build_graph(data))
    payload = re.search(r"const DATA = (.*?);\n", page, re.S).group(1)
    assert "</script>" not in payload
    assert json.loads(payload.replace("<\\/", "</"))["nodes"][0]["gist"] == (
        "</script><script>alert(1)</script>")


def test_write_html_reports_what_it_wrote(registry, tmp_path):
    reg, _ = registry
    path = tmp_path / "reg.json"
    reg.save_to_json(str(path))
    out = tmp_path / "sub" / "graph.html"
    out.parent.mkdir()
    report = write_html(json.loads(path.read_text(encoding="utf-8")), str(out))

    assert report == {"nodes": 4, "edges": 2, "path": str(out)}
    assert out.exists()
