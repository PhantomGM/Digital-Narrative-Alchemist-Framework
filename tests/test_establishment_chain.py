"""
No gene name may run into its value ambiguously.

`establishment` wrote every gene as name-then-value with no separator. That is
fine for a three-letter name -- `ATM5` can only be ATM at 5 -- but its CHAIN
links are called `CH1`, `CH2`, `CH3`, and they are valued 0-4. So `CH1` at `0`
rendered as the string `CH10`, which reads equally well as a gene called CH10.
The decoder carried a parsing note telling the model to take the last character
as the value, which is a workaround at the reading end for a defect at the
writing end.

Found by `scripts/audit_null_values.py` while auditing for null values, not by
looking for it: `CH1:0` is an absence (0 means no link) that the audit could not
even see, because its own regex could not separate the key from the value
either. A format a script cannot parse is a format a model has to guess at.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.generators.establishment import (  # noqa: E402
    generate_establishment_dna)

DECODER = os.path.join(os.path.dirname(__file__), "..", "src",
                       "layer5_dna_substrate", "decoders", "establishment.md")


def chain_block(dna):
    match = re.search(r"CHAIN\{([^}]*)\}", dna)
    assert match, f"no CHAIN block in DNA:\n{dna}"
    return match.group(1)


# --- the fix ----------------------------------------------------------------

@pytest.mark.parametrize("seed", range(25))
def test_chain_genes_carry_a_separator(seed):
    """Every CHAIN entry must be name:value, never name-run-into-value."""
    for entry in chain_block(generate_establishment_dna(seed=seed)).split(","):
        assert re.fullmatch(r"CH[123]:\d", entry.strip()), \
            f"CHAIN entry {entry!r} is not in CH<n>:<value> form"


@pytest.mark.parametrize("seed", range(25))
def test_a_zero_link_is_unambiguous(seed):
    """
    The whole point. CH1 at 0 must not be able to render as "CH10".
    """
    block = chain_block(generate_establishment_dna(seed=seed))
    assert "CH10" not in block.replace(":", "!"), \
        "a zero-valued link still collapses into the gene name"


def test_zero_links_do_actually_occur():
    """
    A guard for a value that never appears is not a guard. Each link is
    randint(0, 4), so a zero should turn up in well under 25 rolls.
    """
    seen = any("0" in entry.split(":")[1]
               for seed in range(25)
               for entry in chain_block(
                   generate_establishment_dna(seed=seed)).split(","))
    assert seen, "no CHAIN link rolled 0 in 25 seeds; the case is untested"


# --- the rest of the genome is deliberately NOT changed ---------------------

@pytest.mark.parametrize("block", ["ATMOS", "OFFERINGS", "PERSONNEL",
                                   "SECRETS", "EVO"])
def test_other_blocks_keep_the_bare_form(block):
    """
    Only CHAIN needed a separator, because only CHAIN has digit-suffixed names.
    Changing the others would alter the DNA of every establishment gene for no
    gain, so this asserts they were left alone.
    """
    dna = generate_establishment_dna(seed=7)
    body = re.search(rf"{block}\{{([^}}]*)\}}", dna).group(1)
    assert ":" not in body, \
        f"{block} gained a separator it does not need: {body!r}"
    for entry in body.split(","):
        assert re.fullmatch(r"[A-Z]{3}\d+", entry.strip()), entry


# --- the decoder must describe the format it is actually given ---------------

def test_decoder_documents_the_separated_form():
    with open(DECODER, encoding="utf-8") as fh:
        text = fh.read()
    assert "CH1:0" in text, \
        "the decoder does not show the separated form it will now receive"


def test_decoder_still_explains_the_legacy_shape():
    """
    No establishment entity exists in any registry, so nothing needs migrating
    -- but the old shape may survive in notes or an older App copy, and a
    decoder that cannot read it would fail silently rather than loudly.
    """
    with open(DECODER, encoding="utf-8") as fh:
        text = fh.read().lower()
    assert "ch10" in text and ("older" in text or "legacy" in text), \
        "the decoder no longer explains how to read pre-separator DNA"
