"""
Tests for WikiBridge markdown ingestion.

These lock in the fix for a structural mismatch that made wiki RAG a no-op:
ingest_wiki() required a single hardcoded "Concepts" subdirectory and listed it
non-recursively. No vault in this project has one, so every run returned zero
chunks regardless of how much lore was present.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer3_operations.wiki_bridge import WikiBridge, normalize_entity_id  # noqa: E402


def write(root, relpath, text):
    path = os.path.join(root, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


@pytest.fixture
def vault(tmp_path):
    root = str(tmp_path)
    write(root, "Factions/The Umbral Synod.md", """---
type: faction
status: canon
---

# The Umbral Synod

A conclave of shadow-brokers.

## Goals

- Control the flow of forgotten names.
- Outlive the Great Forgetting.

## Territory

They hold the lower vaults and nothing above them.
""")
    write(root, "Atlas/Deep Vault.md", """---
type: location
status: draft
---

# Deep Vault

An unreviewed draft location.
""")
    write(root, "NPCs/Arch-Librarian Kaelen.md", """# Arch-Librarian Kaelen

The aging keeper of the Archive.
""")
    return root


# --- the structural fix -----------------------------------------------------

def test_ingests_without_a_concepts_directory(vault):
    """The original bug: no Concepts/ folder meant zero chunks."""
    assert not os.path.exists(os.path.join(vault, "Concepts"))
    chunks = WikiBridge(vault).ingest_wiki()
    assert chunks, "a vault with lore must yield chunks"


def test_walks_nested_directories(vault):
    chunks = WikiBridge(vault).ingest_wiki()
    ids = {c.entity_id for c in chunks}
    assert "the_umbral_synod" in ids
    assert "arch_librarian_kaelen" in ids


def test_missing_root_returns_empty_without_raising(tmp_path):
    bridge = WikiBridge(str(tmp_path / "nope"))
    assert bridge.ingest_wiki() == []


def test_subdirs_restricts_scope(vault):
    chunks = WikiBridge(vault, subdirs=["Factions"]).ingest_wiki()
    assert {c.entity_id for c in chunks} == {"the_umbral_synod"}


def test_missing_subdir_is_reported_not_fatal(vault):
    chunks = WikiBridge(vault, subdirs=["Concepts", "Factions"]).ingest_wiki()
    assert {c.entity_id for c in chunks} == {"the_umbral_synod"}


# --- canon gating -----------------------------------------------------------

def test_drafts_are_skipped_by_default(vault):
    bridge = WikiBridge(vault)
    chunks = bridge.ingest_wiki()
    assert "deep_vault" not in {c.entity_id for c in chunks}
    assert bridge.stats["skipped_non_canon"] == 1


def test_drafts_included_when_canon_only_is_off(vault):
    chunks = WikiBridge(vault, canon_only=False).ingest_wiki()
    assert "deep_vault" in {c.entity_id for c in chunks}


def test_pages_without_status_are_ingested(vault):
    """Vaults that predate the canon convention must still work."""
    chunks = WikiBridge(vault).ingest_wiki()
    assert "arch_librarian_kaelen" in {c.entity_id for c in chunks}


def test_deprecated_is_not_treated_as_canon(tmp_path):
    write(str(tmp_path), "Lore/Old.md", "---\nstatus: deprecated\n---\n\n# Old\n\nSuperseded.\n")
    assert WikiBridge(str(tmp_path)).ingest_wiki() == []


# --- exclusions -------------------------------------------------------------

def test_scaffolding_files_and_dirs_are_excluded(tmp_path):
    root = str(tmp_path)
    write(root, "Log.md", "# Log\n\nOperation log entry.\n")
    write(root, "CLAUDE.md", "# Rules\n\nMaintainer rules.\n")
    write(root, "Templates/Faction.md", "# Template\n\nPlaceholder text.\n")
    write(root, ".obsidian/workspace.md", "# Config\n\nNot lore.\n")
    write(root, "Lore/Real.md", "# Real\n\nActual lore.\n")

    chunks = WikiBridge(root).ingest_wiki()
    assert {c.entity_id for c in chunks} == {"real"}


def test_file_named_only_md_is_skipped(tmp_path):
    """The Hermes vault contains a file literally named ".md"."""
    write(str(tmp_path), "NPCs/.md", "Some orphaned text.\n")
    write(str(tmp_path), "NPCs/Real.md", "# Real\n\nActual lore.\n")
    chunks = WikiBridge(str(tmp_path)).ingest_wiki()
    assert {c.entity_id for c in chunks} == {"real"}


# --- noise filtering --------------------------------------------------------

def test_generated_relation_bullets_are_dropped_but_prose_survives(tmp_path):
    """
    Stub pages put their only real description inside the generated relations
    block. Dropping the whole section discarded that description; dropping the
    bullets line by line keeps it.
    """
    write(str(tmp_path), "Atlas/The Weaving Chamber.md", """---
type: location
---

# The Weaving Chamber

# \U0001f9ec DNA Relations

- **Mentions_The Weaving Chamber**: [[Entity]]
- **Mentions_**: [[]]

---
[STUB] The Weaving Chamber: The hidden nexus behind the Veil.
""")
    chunks = WikiBridge(str(tmp_path)).ingest_wiki()
    facts = " | ".join(c.fact for c in chunks)

    assert "Mentions_" not in facts, "machine relation bullets must not become lore"
    assert "The hidden nexus behind the Veil." in facts, "stub description must survive"


def test_redundant_stub_title_is_not_repeated(tmp_path):
    """Facts are already prefixed with the page name; the marker would double it."""
    write(str(tmp_path), "NPCs/Kaelen.md", """# Kaelen

[STUB] Kaelen:: The aging leader of the Order.
""")
    chunks = WikiBridge(str(tmp_path)).ingest_wiki()
    assert chunks[0].fact == "Kaelen: The aging leader of the Order."


def test_h1_scaffolding_does_not_contaminate_the_intro(tmp_path):
    """
    Splitting on "##+" missed H1 headings, so "# DNA Relations" was swept into
    the intro chunk and its bullets were ingested at top importance.
    """
    write(str(tmp_path), "Atlas/Place.md", """# Place

A real description.

# \U0001f9ec DNA Relations

- **Mentions_Thing**: [[Thing]]
""")
    chunks = WikiBridge(str(tmp_path)).ingest_wiki()
    intro = [c for c in chunks if c.importance == 3]
    assert len(intro) == 1
    assert intro[0].fact == "Place: A real description."


def test_horizontal_rules_and_table_separators_are_dropped(tmp_path):
    write(str(tmp_path), "Atlas/Place.md", """# Place

## Detail

| Name | Role |
| :--- | :--- |
| Vault | Storage |

---
""")
    chunks = WikiBridge(str(tmp_path)).ingest_wiki()
    facts = [c.fact for c in chunks]
    assert not any(f.rstrip().endswith("---") for f in facts)
    assert any("Vault" in f for f in facts)


def test_unmade_connections_with_suffix_is_recognized(tmp_path):
    """The real heading is "Unmade Connections (DNA Stubs)"."""
    bridge = WikiBridge(str(tmp_path))
    assert bridge._is_machine_section("Unmade Connections (DNA Stubs)")
    assert bridge._is_machine_section("\U0001f9ec DNA Relations")
    assert not bridge._is_machine_section("Territory")


def test_bullets_become_individual_facts(vault):
    chunks = WikiBridge(vault).ingest_wiki()
    goals = [c.fact for c in chunks if "(Goals)" in c.fact]
    assert len(goals) == 2
    assert any("forgotten names" in f for f in goals)


def test_frontmatter_strip_is_anchored(tmp_path):
    """
    An unanchored "---.*?---" match eats the body between two horizontal rules.
    """
    write(str(tmp_path), "Lore/Doc.md", """# Doc

Intro line.

---

Body that must survive.

---
""")
    chunks = WikiBridge(str(tmp_path)).ingest_wiki()
    facts = " | ".join(c.fact for c in chunks)
    assert "Body that must survive." in facts


def test_clip_marks_only_real_truncation(tmp_path):
    write(str(tmp_path), "Lore/Short.md", "# Short\n\nBrief.\n")
    chunks = WikiBridge(str(tmp_path)).ingest_wiki()
    assert chunks[0].fact == "Short: Brief."


# --- entity ids -------------------------------------------------------------

def test_normalize_entity_id_collapses_punctuation():
    assert normalize_entity_id("Arch-Librarian Kaelen") == "arch_librarian_kaelen"
    assert normalize_entity_id("The Scrivener's Archives") == "the_scrivener_s_archives"
    assert normalize_entity_id("Void-Whisperer") == "void_whisperer"
    assert normalize_entity_id("  Spaced  Out  ") == "spaced_out"


def test_hyphenated_page_is_retrievable(vault):
    """
    The reason the query side had to change too: the old
    lower()/replace(" ", "_") transform produced "arch-librarian_kaelen",
    which matched nothing.
    """
    chunks = WikiBridge(vault).ingest_wiki()
    ids = {c.entity_id for c in chunks}
    assert normalize_entity_id("Arch-Librarian Kaelen") in ids
    assert "arch-librarian_kaelen" not in ids


def test_stats_report_counts(vault):
    bridge = WikiBridge(vault)
    bridge.ingest_wiki()
    assert bridge.stats["files_seen"] == 3
    assert bridge.stats["files_ingested"] == 2
    assert bridge.stats["skipped_non_canon"] == 1


def test_ingest_is_idempotent(vault):
    bridge = WikiBridge(vault)
    first = bridge.ingest_wiki()
    second = bridge.ingest_wiki()
    assert len(first) == len(second), "repeat ingestion must not accumulate"
