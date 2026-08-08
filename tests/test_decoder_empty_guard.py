"""
An empty decode must fail loudly rather than be registered as an entity.

Found by the trial 5 run, not by a test. A `culture` decode returned an empty
string after 39 seconds. The harness registered it, wrote a zero-byte page, fed
that page forward as context for the sixteen entities generated after it, and
printed `contract satisfied: True`. The world was short one contracted entity
and nothing in the pipeline said so.

Silence is the worst failure mode available here, because every downstream
consumer treats a phenotype as content: the registry stores it, ObsidianSync
would write it, ContextAssembler would carry it, and the contract counts it.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.decoder import DNADecoder  # noqa: E402


class _FakeChain:
    """
    Stands in for `prompt | llm | parser`.

    decode_element builds the chain with two `|` operations, so this absorbs
    both and then answers invoke() with a fixed result. Substituting the whole
    prompt is steadier than patching the operator on LangChain's type.
    """

    def __init__(self, result):
        self.result = result

    def __or__(self, other):
        return self

    def invoke(self, _):
        return self.result


@pytest.fixture
def decoder():
    return DNADecoder()


def _decode_returning(decoder, value):
    element = {"type": "culture", "dna": "CULTURE{}", "constraints": ""}
    original = decoder.prompts["culture"]
    decoder.prompts["culture"] = _FakeChain(value)
    try:
        return decoder.decode_element(element)
    finally:
        decoder.prompts["culture"] = original


@pytest.mark.parametrize("blank", ["", "   ", "\n\n", "\t \n "])
def test_an_empty_decode_raises(decoder, blank):
    with pytest.raises(ValueError, match="empty phenotype"):
        _decode_returning(decoder, blank)


def test_the_error_names_the_type_and_says_what_to_do(decoder):
    with pytest.raises(ValueError) as exc:
        _decode_returning(decoder, "")
    message = str(exc.value)
    assert "culture" in message
    assert "do not register this" in message


def test_a_real_decode_passes_through_untouched(decoder):
    page = "### **The Shifting Communes**\n\nA people who wander."
    assert _decode_returning(decoder, page) == page


def test_whitespace_around_real_content_is_not_stripped(decoder):
    """The guard tests for emptiness; it must not reformat a real page."""
    page = "\n### **A People**\n\nBody.\n"
    assert _decode_returning(decoder, page) == page
