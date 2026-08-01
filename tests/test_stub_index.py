"""
Tests for the StubIndex deriver.

Stubs are the one kind of content a vault search cannot reach. Every other listing
in the bible can be found by Obsidian because the things listed are pages; the
sync deliberately holds stubs back, since a stub is a name plus a one-line reason
and nothing else, so 33 near-empty notes would bury the pages that have content.
They exist only in the registry, which is why this is a deriver rather than a
query — the same shape as the Timeline: no DNA, no model, idempotent.
"""

import io
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.registry import DNARegistry  # noqa: E402
from layer5_dna_substrate.stub_index import StubIndex  # noqa: E402


@pytest.fixture
def registry():
    reg = DNARegistry()
    source = reg.register_element("location", "LOC{}", "body",
                                  name="The Null-Chamber", tags=["canonized"])

    def stub(name, ptype, gist):
        entity_id = reg.register_element(ptype, "", "", name=None, tags=["stub"])
        reg.get_element(entity_id)["gist"] = gist
        reg.get_element(entity_id)["stub_metadata"] = {
            "name": name, "description": gist, "source_id": source,
        }
        return entity_id

    stub("The Null-Pulse", "chronicle", "A corrupting force from the chamber.")
    stub("Thread-Keeper Vaelis", "npc", "An inquisitor hunting Corin.")
    stub("Master Kessik", "npc", "A scrap-broker who controls air contracts.")
    # An expanded entity must not appear.
    reg.register_element("npc", "NPC{}", "### **Done**\n\nBody.",
                         name="Already Written", tags=["expanded"])
    return reg


@pytest.fixture
def index(registry, tmp_path):
    return StubIndex(registry, str(tmp_path))


# --- gathering --------------------------------------------------------------

def test_only_stubs_are_listed(index):
    names = {row["name"] for row in index.pending()}
    assert names == {"The Null-Pulse", "Thread-Keeper Vaelis", "Master Kessik"}
    assert "Already Written" not in names


def test_each_row_carries_type_gist_and_source(index):
    row = next(r for r in index.pending() if r["name"] == "Thread-Keeper Vaelis")
    assert row["type"] == "npc"
    assert "inquisitor" in row["gist"]
    assert row["source"] == "The Null-Chamber"


def test_rows_are_grouped_and_sorted_by_name(index):
    grouped = index.group(index.pending())
    assert [r["name"] for r in grouped["npc"]] == ["Master Kessik", "Thread-Keeper Vaelis"]


# --- rendering --------------------------------------------------------------

def test_render_groups_under_readable_headings(index):
    out = index.render(index.pending())
    assert "### People (2)" in out
    assert "### Events (1)" in out


def test_render_links_the_implying_page(index):
    assert "[[The Null-Chamber]]" in index.render(index.pending())


def test_render_reports_the_total(index):
    assert "3 entities" in index.render(index.pending())


def test_render_handles_an_empty_world(registry, tmp_path):
    empty = StubIndex(DNARegistry(), str(tmp_path))
    assert "No pending stubs" in empty.render([])


def test_pipes_in_a_gist_cannot_break_the_table(registry, tmp_path):
    entity_id = registry.register_element("item", "", "", tags=["stub"])
    registry.get_element(entity_id)["stub_metadata"] = {
        "name": "The Bar | Pipe", "description": "A gist with | a pipe in it."}
    out = StubIndex(registry, str(tmp_path)).render(
        StubIndex(registry, str(tmp_path)).pending())
    assert r"\|" in out


# --- writing ----------------------------------------------------------------

def test_write_creates_the_page(index):
    report = index.write()
    assert report["created"] is True
    assert report["stubs"] == 3
    assert os.path.isfile(index.page_path)
    text = io.open(index.page_path, encoding="utf-8").read()
    assert "# Unmade Stubs" in text
    assert "## Pending" in text


def test_write_is_idempotent(index):
    index.write()
    first = io.open(index.page_path, encoding="utf-8").read()
    index.write()
    assert io.open(index.page_path, encoding="utf-8").read() == first


def test_regenerating_preserves_author_sections(index):
    """A deriver owns one section and must leave the rest of the page alone."""
    index.write()
    with io.open(index.page_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n## My notes\n\nExpand Vaelis first.\n")

    index.write()

    text = io.open(index.page_path, encoding="utf-8").read()
    assert "## My notes" in text
    assert "Expand Vaelis first." in text


def test_regenerating_reflects_an_expanded_stub(index, registry):
    """The point of the view: it shrinks as the world gets written."""
    index.write()
    assert "Master Kessik" in io.open(index.page_path, encoding="utf-8").read()

    kessik = next(r for r in index.pending() if r["name"] == "Master Kessik")
    record = registry.get_element(kessik["id"])
    record["tags"].remove("stub")
    record["tags"].append("expanded")

    report = index.write()

    text = io.open(index.page_path, encoding="utf-8").read()
    assert report["stubs"] == 2
    assert "Master Kessik" not in text
    assert "Thread-Keeper Vaelis" in text


def test_a_missing_pending_section_is_appended_not_overwritten(index):
    index.write()
    io.open(index.page_path, "w", encoding="utf-8", newline="\n").write(
        "---\ntype: meta\nstatus: canon\nupdated: 2026-01-01\n---\n\n"
        "# Unmade Stubs\n\nSomething the author wrote.\n")

    index.write()

    text = io.open(index.page_path, encoding="utf-8").read()
    assert "Something the author wrote." in text
    assert "## Pending" in text
