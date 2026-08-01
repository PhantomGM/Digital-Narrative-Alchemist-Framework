"""
Structural guarantees every decoder must meet.

A decoder is a prompt: its text is its implementation, and nothing type-checks
it. Five of the twenty-one were found carrying literal line-number gutters
("   42|Summarize terrain...") on ~90% of their lines, pasted in from a viewer.
Markdown headings inside them were dead text, so the model received an
unstructured wall and the framework's own tooling could not find their output
sections either. One more (quest) had every newline stripped out of its system
instruction, leaving a 2,000-character single line.

None of that is visible in a diff you skim, and none of it fails loudly at
runtime — the decode just comes back worse. These assertions are cheap and
catch the whole class.
"""

import glob
import os
import re

import pytest

DECODERS = os.path.join(os.path.dirname(__file__), "..", "src",
                        "layer5_dna_substrate", "decoders")
FILES = sorted(glob.glob(os.path.join(DECODERS, "*.md")))
NAMES = [os.path.basename(p)[:-3] for p in FILES]

# Matches the decoder's own output-format heading, in any of the house spellings
# the twenty-one have accumulated.
OUTPUT_HEADING = re.compile(
    r"^#{1,3}\s.*(OUTPUT FORMAT|OUTPUT STRUCTURE|STRUCTURED OUTPUT|"
    r"SCENARIO COMPONENTS|PROFILE FORMAT)", re.M | re.I)


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def test_there_are_twenty_one_decoders():
    assert len(FILES) == 21, NAMES


@pytest.mark.parametrize("path", FILES, ids=NAMES)
def test_no_line_number_gutters(path):
    """'   42|text' -- a paste artifact that kills every heading below it."""
    bad = [l for l in read(path).splitlines() if re.match(r"^\s*\d+\|", l)]

    assert not bad, f"{len(bad)} gutter-prefixed line(s), first: {bad[0][:60]!r}"


@pytest.mark.parametrize("path", FILES, ids=NAMES)
def test_headings_actually_parse_as_markdown(path):
    """A decoder with no headings has no structure the model can navigate."""
    heads = re.findall(r"^#{1,4}\s+\S", read(path), re.M)

    assert len(heads) >= 3, f"only {len(heads)} markdown heading(s)"


@pytest.mark.parametrize("path", FILES, ids=NAMES)
def test_no_run_together_wall_of_text(path):
    """quest.md had its whole preamble collapsed onto one 2,015-char line."""
    longest = max((len(l) for l in read(path).splitlines()), default=0)

    assert longest < 1500, f"longest line is {longest} chars; newlines lost?"


@pytest.mark.parametrize("path", FILES, ids=NAMES)
def test_every_decoder_declares_an_output_format(path):
    """The format is the contract with ObsidianSync and with the reader."""
    assert OUTPUT_HEADING.search(read(path)), \
        "no output-format heading found"


@pytest.mark.parametrize("path", FILES, ids=NAMES)
def test_every_decoder_forbids_leaking_its_scaffolding(path):
    """A profile that cites its own DNA tells the reader it was generated."""
    text = read(path).lower()

    assert any(p in text for p in
               ("do not** display", "do not display", "not appear in the final",
                "no scaffolding", "internal processing only",
                "never list dna values", "never print", "never reference the dna",
                "do not reference the dna")), \
        "no rule against printing the DNA in the output"


@pytest.mark.parametrize("path", FILES, ids=NAMES)
def test_every_decoder_asks_for_unmade_connections(path):
    """Stub harvesting is how the world expands; all 21 already do this."""
    assert "Unmade Connections" in read(path)


def test_no_decoder_still_prompts_the_user_for_input():
    """
    There is no user at decode time -- context is injected. travel.md opened by
    asking the reader to supply terrain and party details, so a decode could
    come back as a question instead of a scenario.
    """
    offenders = [n for n, p in zip(NAMES, FILES)
                 if re.search(r"prompt (?:the )?user", read(p), re.I)]

    assert not offenders, offenders
