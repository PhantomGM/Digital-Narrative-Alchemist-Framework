"""
Unit tests for the Graph-Augmented Registry (Bucket D).
Tests named relationship labels, graph traversal, and contextual briefs.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.layer2_dna.registry import DNARegistry


def test_register_and_link_with_labels():
    """Elements can be linked with named relationship labels."""
    reg = DNARegistry()

    faction_id = reg.register_element("faction", "DNA_STRING_1", "A fierce desert guild.", tags=["iron_guild", "desert"])
    npc_id = reg.register_element("npc", "DNA_STRING_2", "A burly blacksmith.", tags=["blacksmith", "desert"])

    reg.link_elements(faction_id, npc_id, "parent", label="faction_of")

    faction_links = reg.get_links(faction_id)
    assert len(faction_links["parent"]) == 1
    assert faction_links["parent"][0]["id"] == npc_id
    assert faction_links["parent"][0]["label"] == "faction_of"

    # Check reciprocal
    npc_links = reg.get_links(npc_id)
    assert len(npc_links["child"]) == 1
    assert npc_links["child"][0]["id"] == faction_id
    print("✓ test_register_and_link_with_labels passed")


def test_get_link_ids_legacy():
    """get_link_ids() returns plain ID lists for backward compatibility."""
    reg = DNARegistry()

    a = reg.register_element("npc", "DNA_A", "NPC A", tags=["warrior"])
    b = reg.register_element("npc", "DNA_B", "NPC B", tags=["mage"])

    reg.link_elements(a, b, "peer", label="rivals")

    link_ids = reg.get_link_ids(a)
    assert b in link_ids["peer"]
    assert isinstance(link_ids["peer"][0], str)  # Just a string, not a dict
    print("✓ test_get_link_ids_legacy passed")


def test_query_graph_depth_1():
    """query_graph returns relational facts at depth 1."""
    reg = DNARegistry()

    king = reg.register_element("npc", "DNA_K", "The brooding king.", tags=["King Aldric"])
    court = reg.register_element("faction", "DNA_C", "The elven court.", tags=["Elven Court"])

    reg.link_elements(king, court, "peer", label="hates")

    facts = reg.query_graph(king, depth=1)
    assert len(facts) > 0
    assert any("hates" in f for f in facts)
    assert any("Elven Court" in f for f in facts)
    print("✓ test_query_graph_depth_1 passed")


def test_query_graph_depth_2():
    """query_graph traverses 2 hops to find transitive relationships."""
    reg = DNARegistry()

    a = reg.register_element("faction", "DNA_A", "Guild A", tags=["guild_a"])
    b = reg.register_element("npc", "DNA_B", "NPC B", tags=["npc_b"])
    c = reg.register_element("location", "DNA_C", "Loc C", tags=["loc_c"])

    reg.link_elements(a, b, "parent", label="controls")
    reg.link_elements(b, c, "peer", label="guards")

    # From A at depth 2, we should see both B and C
    facts = reg.query_graph(a, depth=2)
    assert any("controls" in f for f in facts)
    assert any("guards" in f for f in facts)
    print("✓ test_query_graph_depth_2 passed")


def test_contextual_brief():
    """get_contextual_brief produces a combined graph + phenotype block."""
    reg = DNARegistry()

    npc = reg.register_element("npc", "DNA_N", "A scarred veteran with a mysterious past." * 20, tags=["veteran"])
    faction = reg.register_element("faction", "DNA_F", "The Iron Brotherhood.", tags=["iron_brotherhood"])

    reg.link_elements(faction, npc, "parent", label="member_of")

    brief = reg.get_contextual_brief(npc, phenotype_chars=100)
    assert "ENTITY BRIEF" in brief
    assert "Deterministic Relationships" in brief
    assert "Phenotype Excerpt" in brief
    assert "member_of" in brief
    assert len(brief) > 100  # Not empty
    assert "..." in brief  # Phenotype was truncated
    print("✓ test_contextual_brief passed")


def test_link_without_label_defaults():
    """Links without explicit labels default to the relationship type."""
    reg = DNARegistry()

    a = reg.register_element("npc", "DNA_A", "NPC A", tags=["a"])
    b = reg.register_element("npc", "DNA_B", "NPC B", tags=["b"])

    reg.link_elements(a, b, "parent")  # No label

    links = reg.get_links(a)
    assert links["parent"][0]["label"] == "parent"  # Defaults to rel type
    print("✓ test_link_without_label_defaults passed")


if __name__ == "__main__":
    test_register_and_link_with_labels()
    test_get_link_ids_legacy()
    test_query_graph_depth_1()
    test_query_graph_depth_2()
    test_contextual_brief()
    test_link_without_label_defaults()
    print("\n✅ All Registry Graph tests passed!")
