"""
Tests for the auditor's canon slice: cited page text, and non-truncatable rulings.

Two defects made every audit on this world unreliable, and both are covered here.

1. The slice carried one gist per entity. Judging a claim against a one-line
   summary is not verification: a TRUE statement about Kaelen was patched away
   because his gist omitted it, and a page asserting proof about the First
   Architects passed because no gist contradicted it.

2. Worse, and found while fixing the first: the standing authorial rulings sit at
   the END of the World Overview, which is longer than the world-frame budget. The
   cap silently removed them from every prompt — decoder and auditor alike. The
   measured loss on the real vault was 4,000 characters including all three
   rulings. Rules absent from the prompt cannot be followed, which explains the
   canon violations better than the gist theory did.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.context_assembler import (  # noqa: E402
    AssemblyRequest, ContextAssembler, _CHARS_PER_TOKEN, _LAYER_BUDGET,
    _MAX_CITED_PAGES)
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402
from layer5_dna_substrate.vault_adapter import VaultAdapter  # noqa: E402

RULING = (
    '- **Who the "First Architects" were is unresolved and stays that way.** '
    'Nothing may prove their identity.'
)

# Deliberately longer than the world-frame cap, with the rulings last, exactly as
# the real World Overview is shaped.
OVERVIEW = (
    "# World Overview\n\n## Pillars\n\n"
    + ("- A pillar sentence that exists only to consume budget.\n" * 90)
    + "\n## Terminology rulings\n\n"
    + '- **"Temporal power" means worldly power** — never mastery over time.\n'
    + RULING + "\n\n## Themes\n\n- Grim.\n"
)

DEEP_FACT = "sections of the Litany are pre-Collapse machine operating instructions"

FIRST_TRUTH = (
    "# The First Truth\n\nAn opening paragraph of theology.\n\n"
    + ("Filler sentence establishing tone and taking up room.\n" * 60)
    + "\n**The hidden truth:** " + DEEP_FACT + ".\n"
)


def write(root, relpath, body, status="canon"):
    path = os.path.join(root, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"---\ntype: lore\nstatus: {status}\n---\n\n{body}")


@pytest.fixture
def vault(tmp_path):
    root = str(tmp_path)
    write(root, "World Overview.md", OVERVIEW)
    write(root, "Lore/The First Truth.md", FIRST_TRUTH)
    write(root, "Lore/The Litany.md", "# The Litany\n\nA sacred text of stone tablets.\n")
    write(root, "Characters/Archivist Kaelen.md", "# Archivist Kaelen\n\nThe Archivist who descended.\n")
    write(root, "Log.md", "# Log\n\n- Entries about technological drift and catalogues.\n")
    write(root, "Lore/Lore.md", "# Lore\n\nHub page.\n")
    write(root, "Index.md", "\n".join([
        "# Index",
        "",
        "- [[Lore]] - hub (canon)",
        "- [[The First Truth]] - the founding doctrine (canon)",
        "- [[The Litany]] - the sacred text (canon)",
        "- [[Archivist Kaelen]] - the Archivist (canon)",
        "- [[Log]] - the operation log (canon)",
        "- [[A Draft Place]] - somewhere unfinished (draft)",
    ]))
    return root


@pytest.fixture
def setup(vault):
    registry = DNARegistry()
    source_id = registry.register_element(
        "lore", "LORE{}", FIRST_TRUTH, name="The First Truth", tags=["canonized"])
    entity_id = registry.register_element(
        "text", "TEXT{}", "body", name="The Litany", tags=["expanded"])
    registry.get_element(entity_id)["stub_metadata"] = {
        "name": "The Litany", "description": "A sacred text.", "source_id": source_id,
    }
    assembler = ContextAssembler(registry, VaultAdapter(vault))
    return registry, assembler, entity_id, source_id


# --- the rulings must survive the cap ---------------------------------------

def test_overview_alone_exceeds_the_world_frame_cap(setup):
    """Establishes the precondition; without it the rest proves nothing."""
    _, assembler, _, _ = setup
    cap = int(3000 * _LAYER_BUDGET["world_frame"] * _CHARS_PER_TOKEN)
    assert len(assembler.vault.world_overview()) > cap


def test_rulings_are_lost_to_the_raw_cap(setup):
    """The bug: capping the frame discards the rulings, which sit at the end."""
    _, assembler, _, _ = setup
    capped = assembler._cap(assembler._build_world_frame([]), 3000,
                            _LAYER_BUDGET["world_frame"])
    assert RULING not in capped


def test_rulings_are_restored_after_the_cap(setup):
    _, assembler, _, _ = setup
    frame = assembler._with_rulings(
        assembler._cap(assembler._build_world_frame([]), 3000,
                       _LAYER_BUDGET["world_frame"]))
    assert RULING in frame
    assert "CANON RULINGS" in frame


def test_rulings_reach_the_decoder_context(setup):
    """Generation needs them as much as verification does."""
    _, assembler, entity_id, _ = setup
    context = assembler.assemble(AssemblyRequest(element_type="lore")).for_decoder()
    assert RULING in context


def test_rulings_reach_the_audit_slice(setup):
    _, assembler, entity_id, _ = setup
    slice_ = assembler.assemble(
        AssemblyRequest(element_type="text", anchor_id=entity_id,
                        passage="A page about The Litany.")).canon_slice()
    assert RULING in slice_


def test_rulings_are_not_duplicated(setup):
    _, assembler, _, _ = setup
    frame = assembler._with_rulings(assembler._build_world_frame([]))
    assert frame.count(RULING) == 1


def test_no_vault_does_not_crash(tmp_path):
    registry = DNARegistry()
    assembler = ContextAssembler(registry, None)
    package = assembler.assemble(AssemblyRequest(element_type="lore", passage="text"))
    assert package.citations == ""
    assert isinstance(package.canon_slice(), str)


# --- citations --------------------------------------------------------------

def test_no_passage_means_no_citations(setup):
    """Citations are evidence for a passage; the decode path must not pay for them."""
    _, assembler, entity_id, _ = setup
    package = assembler.assemble(
        AssemblyRequest(element_type="text", anchor_id=entity_id))
    assert package.citations == ""


def test_passage_named_page_is_cited_in_full(setup):
    _, assembler, entity_id, _ = setup
    package = assembler.assemble(AssemblyRequest(
        element_type="text", anchor_id=entity_id,
        passage="A study of Archivist Kaelen and his work."))
    assert "Archivist Kaelen" in package.citations
    assert "The Archivist who descended" in package.citations


def test_the_source_page_is_cited_even_when_unnamed(setup):
    """
    The decisive case. The Litany's canon description and the deep reveal live on
    its SOURCE page, which its own prose never names.
    """
    _, assembler, entity_id, _ = setup
    passage = "The Litany is a collection of stone tablets in a pictogram cipher."
    assert "First Truth" not in passage

    package = assembler.assemble(AssemblyRequest(
        element_type="text", anchor_id=entity_id, passage=passage))
    assert "The First Truth" in package.citations
    assert DEEP_FACT in package.citations, "the deep fact must survive excerpting"


def test_the_deep_fact_is_absent_from_the_gist_roster(setup):
    """Confirms the citation is doing the work, not the roster."""
    _, assembler, entity_id, _ = setup
    package = assembler.assemble(AssemblyRequest(
        element_type="text", anchor_id=entity_id, passage="The Litany."))
    assert DEEP_FACT not in package.roster


def test_citations_precede_the_roster_in_the_slice(setup):
    _, assembler, entity_id, _ = setup
    slice_ = assembler.assemble(AssemblyRequest(
        element_type="text", anchor_id=entity_id,
        passage="Archivist Kaelen.")).canon_slice()
    assert "SUMMARY DIRECTORY" in slice_
    assert slice_.index("FULL TEXT") < slice_.index("SUMMARY DIRECTORY")


def test_roster_is_labelled_as_non_evidence(setup):
    """An omission from a one-line directory must not read as a contradiction."""
    _, assembler, entity_id, _ = setup
    slice_ = assembler.assemble(AssemblyRequest(
        element_type="text", anchor_id=entity_id, passage="The Litany.")).canon_slice()
    assert "not evidence" in slice_


# --- what must NOT be cited -------------------------------------------------

def test_operation_log_is_never_cited(setup):
    """
    Substring matching let "Log" match on "technological". The log is vault
    machinery and on the real vault is 35KB of maintenance chatter.
    """
    _, assembler, entity_id, _ = setup
    names = assembler._cited_page_names(
        "A technological catalogue of prologue fragments.", entity_id)
    assert "Log" not in names


def test_word_boundaries_are_respected(setup):
    _, assembler, _, _ = setup
    assert assembler._cited_page_names("The Litanys of old", None) == []
    assert "The Litany" in assembler._cited_page_names("Behold The Litany.", None)


def test_hub_pages_are_not_cited(setup):
    _, assembler, _, _ = setup
    assert "Lore" not in assembler._cited_page_names("A page about Lore.", None)


def test_draft_pages_are_not_cited(setup):
    """The slice is the authoritative record; a draft is not authoritative."""
    _, assembler, _, _ = setup
    assert assembler._cited_page_names("Set in A Draft Place.", None) == []


def test_citation_count_is_bounded(setup):
    _, assembler, entity_id, _ = setup
    passage = "The First Truth, The Litany, Archivist Kaelen, all at once."
    assert len(assembler._cited_page_names(passage, entity_id)) <= _MAX_CITED_PAGES


def test_ordering_is_by_relevance_not_name_length(setup):
    """
    Ranking by name length as a specificity proxy crowded out short but central
    names: "Archivist Kaelen" lost its citation slot to eight longer names on the
    very page whose disputed claim was about him. Mention count decides now.
    """
    _, assembler, _, _ = setup
    passage = (
        "Archivist Kaelen founded it. Archivist Kaelen wrote of it. "
        "Archivist Kaelen is remembered still. A passing nod to The First Truth."
    )
    names = assembler._cited_page_names(passage, None)
    assert names[0] == "Archivist Kaelen", names


def test_a_shorter_contained_name_does_not_take_a_second_slot(setup):
    """"Kaelen" must not be cited separately from "Archivist Kaelen"."""
    _, assembler, _, _ = setup
    names = assembler._cited_page_names("Archivist Kaelen walked.", None)
    assert names == ["Archivist Kaelen"]
