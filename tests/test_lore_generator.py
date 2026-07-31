"""
Tests for the lore genome and its decoder contract.

Lore previously had no type of its own: beliefs were generated with the
chronicle generator and retyped. That forced a claim into an event's shape — the
canon page for The First Truth of the Unbroken Thread still carries a "Time
Period", a "Historical Essence" and a "Turning Point" for what is a theological
doctrine, and the prose strains visibly against them.

The keystone is Veracity, and its essential property is independence from
Reach: how true a claim is must have no bearing on how widely it is held.
RESOLVE is its companion, and exists so a claim can be marked unknowable and
stay that way — the decoder must not quietly settle a question the author left
open, which is exactly what the chronicle decoder did twice.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.generators.lore import generate_lore_dna  # noqa: E402
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402
from layer5_dna_substrate.phenotype_meta import VALID_STUB_TYPES  # noqa: E402

DECODER = os.path.join(os.path.dirname(__file__), '..', 'src',
                       'layer5_dna_substrate', 'decoders', 'lore.md')

TOP_LINE = re.compile(r"^LORE\{v1\.0\[(\d)/(\d)/(\d)\]\} #([\w'-]+) #([\w'-]+)$")

BLOCKS = ("CLAIM", "TRUTH", "KEEP", "PRACTICE", "DRIFT", "TITLE", "TENSION")


def field(dna, key):
    match = re.search(rf"{key}:([^;}}]+)", dna)
    return match.group(1) if match else None


# --- shape ------------------------------------------------------------------

def test_top_line_shape():
    top = generate_lore_dna(seed=1).splitlines()[0]
    match = TOP_LINE.match(top)
    assert match, f"unexpected top line: {top!r}"
    for score in match.groups()[:3]:
        assert 1 <= int(score) <= 9


def test_all_blocks_present():
    dna = generate_lore_dna(seed=2)
    for block in BLOCKS:
        assert re.search(rf"^{block}\{{", dna, re.MULTILINE), f"missing {block}"


def test_every_field_is_populated():
    dna = generate_lore_dna(seed=3)
    for key in ("SUBJ", "SHAPE", "STAKE", "KERNEL", "PROOF", "RESOLVE",
                "KEEPER", "RIVAL", "GRANTS", "ZEAL", "OBSERVE", "SANCTION",
                "VARIANT", "CORRUPT"):
        value = field(dna, key)
        assert value and value.strip(), f"{key} empty"


def test_no_placeholder_or_none_values():
    for seed in range(40):
        dna = generate_lore_dna(seed=seed)
        assert "None" not in dna
        assert "{}" not in dna
        assert ";;" not in dna


# --- reproducibility --------------------------------------------------------

def test_same_seed_reproduces():
    assert generate_lore_dna(seed=99) == generate_lore_dna(seed=99)


def test_different_seeds_differ():
    assert generate_lore_dna(seed=1) != generate_lore_dna(seed=2)


def test_unseeded_calls_vary():
    """Random by default, so a batch must not collapse to one string."""
    assert len({generate_lore_dna() for _ in range(20)}) > 1


# --- the keystone: veracity is independent of reach --------------------------

def test_veracity_and_reach_are_uncorrelated():
    """
    The drama of lore is that truth and belief come apart. If these axes moved
    together the genome could not produce a universally held falsehood.
    """
    pairs = []
    for seed in range(3000):
        match = TOP_LINE.match(generate_lore_dna(seed=seed).splitlines()[0])
        pairs.append((int(match.group(1)), int(match.group(2))))

    n = len(pairs)
    mean_v = sum(v for v, _ in pairs) / n
    mean_r = sum(r for _, r in pairs) / n
    cov = sum((v - mean_v) * (r - mean_r) for v, r in pairs) / n
    sd_v = (sum((v - mean_v) ** 2 for v, _ in pairs) / n) ** 0.5
    sd_r = (sum((r - mean_r) ** 2 for _, r in pairs) / n) ** 0.5
    correlation = cov / (sd_v * sd_r)

    assert abs(correlation) < 0.06, f"veracity/reach correlated: {correlation:+.4f}"


def test_both_dramatic_corners_occur():
    """A universal lie and an ignored truth must both be reachable."""
    false_universal = true_ignored = 0
    for seed in range(3000):
        match = TOP_LINE.match(generate_lore_dna(seed=seed).splitlines()[0])
        veracity, reach = int(match.group(1)), int(match.group(2))
        if veracity <= 2 and reach >= 8:
            false_universal += 1
        if veracity >= 8 and reach <= 2:
            true_ignored += 1

    assert false_universal > 20, "a universally held falsehood never occurs"
    assert true_ignored > 20, "an accurate but disbelieved claim never occurs"


def test_unknowable_is_reachable_and_common():
    """Canon's open questions need this state to be ordinary, not rare."""
    counts = {}
    for seed in range(600):
        value = field(generate_lore_dna(seed=seed), "RESOLVE")
        counts[value] = counts.get(value, 0) + 1

    assert set(counts) == {"resolvable", "contested", "unknowable"}
    assert counts["unknowable"] > 100


# --- pins -------------------------------------------------------------------

def test_pins_are_honoured():
    dna = generate_lore_dna(
        seed=5, kind="doctrine", medium="written-scripture", veracity=1, reach=9,
        resolve="unknowable", keeper="a-priesthood", grants="control-of-technology")
    top = dna.splitlines()[0]
    assert "#doctrine" in top and "#written-scripture" in top
    assert top.startswith("LORE{v1.0[1/9/")
    assert field(dna, "RESOLVE") == "unknowable"
    assert field(dna, "KEEPER") == "a-priesthood"
    assert field(dna, "GRANTS") == "control-of-technology"


def test_pinning_leaves_other_axes_free():
    """Pinning a known belief must not freeze the rest of the genome."""
    variants = {generate_lore_dna(seed=s, kind="prophecy") for s in range(15)}
    assert len(variants) > 1


@pytest.mark.parametrize("bad", [
    {"kind": "not-a-kind"},
    {"medium": "telepathy"},
    {"resolve": "maybe"},
    {"veracity": 0},
    {"veracity": 10},
    {"veracity": "high"},
    {"reach": 4.5},
    {"unknown_axis": "x"},
])
def test_invalid_pins_are_rejected(bad):
    with pytest.raises(ValueError):
        generate_lore_dna(seed=1, **bad)


def test_boolean_is_not_accepted_as_a_score():
    """bool is an int subclass; a True veracity would be a silent 1."""
    with pytest.raises(ValueError):
        generate_lore_dna(seed=1, veracity=True)


# --- wiring -----------------------------------------------------------------

def test_forge_registers_lore():
    forge = ProceduralForge()
    assert "lore" in forge.generators
    result = forge.synthesize_element("lore", seed=11)
    assert result["type"] == "lore"
    assert result["dna"].startswith("LORE{")


def test_lore_is_a_valid_stub_type():
    """So "[Lore] The Litany" in decoder output resolves instead of falling back."""
    assert "lore" in VALID_STUB_TYPES


def test_decoder_file_exists():
    assert os.path.exists(DECODER)


# --- decoder contract -------------------------------------------------------
# The decoder is a prompt, so these assert that the rules which prevent known
# failure modes are actually present in it.

@pytest.fixture(scope="module")
def decoder_text():
    with open(DECODER, encoding="utf-8") as handle:
        return handle.read()


def test_decoder_forbids_stating_claims_as_facts(decoder_text):
    lowered = decoder_text.lower()
    assert "claims as claims" in lowered or "never as facts" in lowered
    assert "attribute" in lowered


def test_decoder_carries_the_canon_override_rule(decoder_text):
    assert "Established canon overrides the DNA" in decoder_text


def test_decoder_forbids_renaming_a_named_entity(decoder_text):
    """
    A live decode renamed the canon-referenced "The Divine Breath" to "The
    Ninefold Breath", coining a title from the TITLE convention. Canon pages
    link by the original name, so a rename orphans them.
    """
    assert "Keep the name you were given" in decoder_text
    title_rule = decoder_text.split("`TITLE{}`")[-1]
    assert "only when the context gives you no name" in decoder_text
    assert "ignored" in title_rule.lower()


def test_decoder_forbids_resolving_open_questions(decoder_text):
    """
    The failure this exists to prevent: a generated page answering a question
    the author deliberately left open, which happened twice via chronicle.
    """
    lowered = decoder_text.lower()
    assert "never resolve" in lowered
    assert "unresolved" in lowered
    assert "unknowable" in lowered


def test_decoder_states_veracity_and_reach_are_independent(decoder_text):
    assert "independent" in decoder_text.lower()
    assert "Veracity" in decoder_text and "Reach" in decoder_text


def test_decoder_separates_the_belief_from_its_carrier(decoder_text):
    """A doctrine and the scripture carrying it are different entities."""
    lowered = decoder_text.lower()
    assert "separate entity" in lowered


def test_decoder_refuses_moral_alignment(decoder_text):
    assert "no moral alignment" in decoder_text.lower()


def test_decoder_keeps_claim_and_truth_in_separate_sections(decoder_text):
    assert "What Is Claimed" in decoder_text
    assert "What Is Actually True" in decoder_text
    assert decoder_text.index("What Is Claimed") < decoder_text.index("What Is Actually True")


def test_decoder_documents_every_block_the_generator_emits(decoder_text):
    for block in BLOCKS:
        assert f"`{block}{{" in decoder_text or f"{block}{{}}" in decoder_text, \
            f"decoder does not document the {block} block"


def test_decoder_requests_stubs_and_a_verbatim_line(decoder_text):
    assert "Unmade Connections" in decoder_text
    assert "verbatim" in decoder_text.lower()
