"""
Tests for the text genome and its decoder contract.

A text is not lore. Lore is a claim; a text is the physical object carrying one,
with properties a belief does not have: a form that can burn, a script that may
be unreadable, a number of surviving copies, a custodian, a worsening condition.
Decoding a document with the lore decoder yields a page about what it teaches
and nothing about what it is — yet whether a scripture exists as one sealed
original or ten thousand recited copies decides every story available with it.

The keystone is Legibility, and its force comes from pairing with PURPORT vs
ACTUAL: a document can be universally revered and wholly unread. ATTRIB is the
canon-safety hook, mirroring lore's RESOLVE, so authorship the author left open
cannot be quietly supplied.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.generators.text import generate_text_dna  # noqa: E402
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402
from layer5_dna_substrate.expansion_manager import _resolve_stub_type  # noqa: E402
from layer5_dna_substrate.obsidian_sync import ObsidianSync  # noqa: E402
from layer5_dna_substrate.phenotype_meta import VALID_STUB_TYPES  # noqa: E402

DECODER = os.path.join(os.path.dirname(__file__), '..', 'src',
                       'layer5_dna_substrate', 'decoders', 'text.md')

TOP_LINE = re.compile(r"^TEXT\{v1\.0\[(\d)/(\d)/(\d)\]\} #([\w'-]+) #([\w'-]+)$")
BLOCKS = ("PURPORT", "ORIGIN", "CUSTODY", "STATE", "USE", "PERIL", "TENSION")


def field(dna, key):
    match = re.search(rf"{key}:([^;}}]+)", dna)
    return match.group(1) if match else None


def scores(seed):
    match = TOP_LINE.match(generate_text_dna(seed=seed).splitlines()[0])
    return tuple(int(g) for g in match.groups()[:3])


# --- shape ------------------------------------------------------------------

def test_top_line_shape():
    top = generate_text_dna(seed=1).splitlines()[0]
    match = TOP_LINE.match(top)
    assert match, f"unexpected top line: {top!r}"
    for score in match.groups()[:3]:
        assert 1 <= int(score) <= 9


def test_all_blocks_present():
    dna = generate_text_dna(seed=2)
    for block in BLOCKS:
        assert re.search(rf"^{block}\{{", dna, re.MULTILINE), f"missing {block}"


def test_every_field_is_populated():
    dna = generate_text_dna(seed=3)
    for key in ("BELIEVED", "ACTUAL", "GAP", "AUTHOR", "ATTRIB", "AGE",
                "HOLDER", "PLACE", "ACCESS", "COND", "SCRIPT", "DECAY",
                "FUNC", "RITE", "HAZARD", "SANCTION"):
        value = field(dna, key)
        assert value and value.strip(), f"{key} empty"


def test_no_placeholder_values():
    for seed in range(40):
        dna = generate_text_dna(seed=seed)
        assert "None" not in dna and "{}" not in dna and ";;" not in dna


# --- reproducibility --------------------------------------------------------

def test_same_seed_reproduces():
    assert generate_text_dna(seed=42) == generate_text_dna(seed=42)


def test_different_seeds_differ():
    assert generate_text_dna(seed=1) != generate_text_dna(seed=2)


def test_unseeded_calls_vary():
    assert len({generate_text_dna() for _ in range(20)}) > 1


# --- the keystone: legibility is independent of how widely it is held --------

def test_legibility_and_copies_are_uncorrelated():
    """
    A document can be everywhere and unreadable — the Litany's exact situation.
    If these axes moved together that case would be unreachable.
    """
    pairs = [scores(seed)[:2] for seed in range(3000)]
    n = len(pairs)
    mean_l = sum(a for a, _ in pairs) / n
    mean_c = sum(b for _, b in pairs) / n
    cov = sum((a - mean_l) * (b - mean_c) for a, b in pairs) / n
    sd_l = (sum((a - mean_l) ** 2 for a, _ in pairs) / n) ** 0.5
    sd_c = (sum((b - mean_c) ** 2 for _, b in pairs) / n) ** 0.5
    correlation = cov / (sd_l * sd_c)

    assert abs(correlation) < 0.06, f"legibility/copies correlated: {correlation:+.4f}"


def test_the_unreadable_but_ubiquitous_corner_occurs():
    """The revered-and-unread document must be reachable."""
    hits = sum(1 for seed in range(3000)
               if scores(seed)[0] <= 2 and scores(seed)[1] >= 8)
    assert hits > 20, "an unreadable yet ubiquitous text never occurs"


def test_unique_and_fragmentary_corner_occurs():
    """So must the single surviving scrap."""
    hits = sum(1 for seed in range(3000)
               if scores(seed)[1] <= 2 and scores(seed)[2] <= 2)
    assert hits > 20, "a unique fragment never occurs"


def test_unknown_attribution_is_reachable_and_common():
    """Canon leaves some authorship open; the state must be ordinary."""
    counts = {}
    for seed in range(600):
        value = field(generate_text_dna(seed=seed), "ATTRIB")
        counts[value] = counts.get(value, 0) + 1

    assert set(counts) == {"known", "disputed", "falsely-attributed", "unknown"}
    assert counts["unknown"] > 60


# --- pins -------------------------------------------------------------------

def test_pins_are_honoured():
    dna = generate_text_dna(
        seed=5, form="vellum-codex", genre="technical-manual", legibility=1,
        copies=9, purport="holy-writ", actual="machine-operating-instructions",
        gap="no-one-can-read-it", attrib="unknown")
    top = dna.splitlines()[0]
    assert "#vellum-codex" in top and "#technical-manual" in top
    assert top.startswith("TEXT{v1.0[1/9/")
    assert field(dna, "BELIEVED") == "holy-writ"
    assert field(dna, "ACTUAL") == "machine-operating-instructions"
    assert field(dna, "GAP") == "no-one-can-read-it"
    assert field(dna, "ATTRIB") == "unknown"


def test_pinning_leaves_other_axes_free():
    variants = {generate_text_dna(seed=s, genre="scripture") for s in range(15)}
    assert len(variants) > 1


@pytest.mark.parametrize("bad", [
    {"form": "hologram"},
    {"genre": "novel"},
    {"attrib": "probably"},
    {"legibility": 0},
    {"legibility": 10},
    {"copies": "many"},
    {"unknown_axis": "x"},
])
def test_invalid_pins_are_rejected(bad):
    with pytest.raises(ValueError):
        generate_text_dna(seed=1, **bad)


def test_boolean_is_not_accepted_as_a_score():
    """bool is an int subclass; True would be written into the DNA literally."""
    with pytest.raises(ValueError):
        generate_text_dna(seed=1, legibility=True)


# --- wiring -----------------------------------------------------------------

def test_forge_registers_text():
    forge = ProceduralForge()
    assert "text" in forge.generators
    result = forge.synthesize_element("text", seed=11)
    assert result["type"] == "text"
    assert result["dna"].startswith("TEXT{")


def test_text_is_a_valid_stub_type():
    assert "text" in VALID_STUB_TYPES


def test_text_files_alongside_lore():
    """The vault's CLAUDE.md puts in-world texts in Lore/."""
    assert ObsidianSync.TYPE_FOLDER_MAP["text"] == "Lore"
    assert ObsidianSync.TYPE_FOLDER_MAP["lore"] == "Lore"


@pytest.mark.parametrize("label,expected", [
    ("text", "text"), ("document", "text"), ("codex", "text"), ("tome", "text"),
    ("manual", "text"), ("ledger", "text"), ("letter", "text"),
])
def test_document_labels_resolve_to_text(label, expected):
    assert _resolve_stub_type(label) == expected


@pytest.mark.parametrize("label,expected", [
    ("scripture", "lore"),   # the belief, not the book
    ("scroll", "item"),      # pre-existing mapping, must not be re-routed
    ("book", "item"),
    ("doctrine", "lore"),
    ("creature", "creature"),
])
def test_existing_mappings_are_not_reroutedgeneric(label, expected):
    """
    Matching is by substring in insertion order, so adding keys can hijack
    existing labels and silently move entities. These must be unchanged.
    """
    assert _resolve_stub_type(label) == expected


def test_decoder_file_exists():
    assert os.path.exists(DECODER)


# --- decoder contract -------------------------------------------------------

@pytest.fixture(scope="module")
def decoder_text():
    with open(DECODER, encoding="utf-8") as handle:
        return handle.read()


def test_decoder_demands_the_object_not_the_doctrine(decoder_text):
    lowered = decoder_text.lower()
    assert "write the object, not the sermon" in lowered
    assert "separate entity" in lowered


def test_decoder_gates_on_legibility(decoder_text):
    """
    The central failure of this type: quoting fluently from a document nobody
    can read.
    """
    assert "Legibility gates everything" in decoder_text
    lowered = decoder_text.lower()
    assert "tradition, not reading" in lowered


def test_decoder_forbids_printing_scores(decoder_text):
    """
    A live decode wrote "(Legibility 2)", "3/9 complete" and "Age 1" into the
    prose. A score is an instruction to the writer, not a world fact.
    """
    lowered = decoder_text.lower()
    assert "includes its **numbers**" in lowered
    assert "never a fact about the world" in lowered


def test_decoder_says_copies_is_a_band_not_a_tally(decoder_text):
    """The same decode read a COPIES score of 8 as "eight copies"."""
    assert "A band, not a tally" in decoder_text
    assert 'does not mean "eight copies"' in decoder_text


def test_decoder_documents_the_age_direction(decoder_text):
    """
    AGE had no bands, so the decode inverted it — rendering a deliberately
    recent document as predating the Collapse by millennia.
    """
    assert "which runs from recent to ancient" in decoder_text
    assert "within living memory" in decoder_text
    assert "is *young*" in decoder_text


def test_decoder_requires_the_gap_mechanism(decoder_text):
    lowered = decoder_text.lower()
    assert "how the gap survives" in lowered or "gap survives" in lowered
    assert "mechanism" in lowered


def test_decoder_forbids_resolving_authorship(decoder_text):
    assert "Never resolve authorship" in decoder_text
    lowered = decoder_text.lower()
    assert "unresolved" in lowered and "credited" in lowered


def test_decoder_carries_canon_override_and_naming_rules(decoder_text):
    assert "Established canon overrides the DNA" in decoder_text
    assert "Keep the name you were given" in decoder_text


def test_decoder_treats_copy_count_as_load_bearing(decoder_text):
    lowered = decoder_text.lower()
    assert "cannot be recalled" in lowered
    assert "unique original" in lowered


def test_decoder_keeps_purport_and_actual_separate(decoder_text):
    assert "What It Is Taken For" in decoder_text
    assert "What It Actually Is" in decoder_text
    assert decoder_text.index("What It Is Taken For") < \
        decoder_text.index("What It Actually Is")


def test_decoder_refuses_moral_alignment(decoder_text):
    assert "no moral alignment" in decoder_text.lower()


def test_decoder_documents_every_block(decoder_text):
    for block in BLOCKS:
        assert f"`{block}{{" in decoder_text, f"{block} block undocumented"


def test_decoder_requests_stubs(decoder_text):
    assert "Unmade Connections" in decoder_text
