"""
The first heading of a decoded page must be the entity's NAME, not a field label.

Found by indexing the Session 0 trial rather than by reading it: three decoders
printed a template label where the name belongs. `world` opened its page with
"World Overview", `region` with "Region Name: The Saltspire Marches", and `quest`
with "1. Quest Title" followed by the actual title on the line beneath.

Why it matters beyond tidiness. `ExpansionManager._extract_name` walks heading
patterns in order and takes the first that is not in its exclude list, so it
would name a world "World Overview". The structured YAML tail is the primary
path and saves this in practice -- all fifteen trial pages emitted a valid tail
-- but the regex fallback exists precisely for decoders that omit the tail, and
on these three it returned a template label.

The fix is the convention the seven refined decoders already share: open the
output template with a bracketed placeholder heading (`### **\\[Faction Name]**`)
so the bracket signals substitution, rather than a numbered label that reads like
a heading to reproduce verbatim.

These tests assert a PROPERTY of the prompts, not their wording -- per the
project rule that a decoder is a prompt and pinning phrasing breaks the moment
someone rewrites a section better than it was.
"""

import glob
import os
import re

import pytest

DECODER_DIR = os.path.join(os.path.dirname(__file__), "..", "src",
                           "layer5_dna_substrate", "decoders")
FILES = sorted(glob.glob(os.path.join(DECODER_DIR, "*.md")))
NAMES = sorted(os.path.basename(f)[:-3] for f in FILES)

# Decoders that still lack a name-placeholder heading. Now empty: all twenty-one
# ask for the entity's name as a heading. The set is kept rather than deleted
# because it is the mechanism, not a leftover -- it is asserted to be EXACTLY the
# gap, so a decoder added or rewritten without a name placeholder fails
# test_the_known_gap_is_exactly_what_it_claims rather than passing silently.
#
# It held {"settlement", "travel"} for one commit. settlement carried region's
# defect character for character ("1. **Settlement Name:** Create an evocative
# name...") and rendered correctly in the Session 0 trial by luck; travel had
# numbered headings like quest and no name slot at all, like world.
KNOWN_MISSING = set()

HEADING = re.compile(r"^#{2,6}\s+(.*)$")
# A heading that opens with a number: "### **1. Quest Title**", "## 3. Encounters",
# and the decimal form travel used, "## 4.5 Journey Narrative Integration".
NUMBERED_HEADING = re.compile(r"^#{2,6}\s+\**\s*\d+(\.\d+)*\.?\s+\S")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read().replace("\r\n", "\n")


def headings(text):
    return [m.group(1).strip() for m in
            (HEADING.match(line) for line in text.split("\n")) if m]


def placeholder_headings(text):
    """Headings whose visible text is a bracketed placeholder, escaped or not."""
    found = []
    for body in headings(text):
        body = body.strip("*").strip()
        if body.startswith("\\["):
            body = body[1:]
        if body.startswith("[") and body.endswith("]"):
            found.append(body[1:-1])
    return found


def name_placeholders(text):
    return [h for h in placeholder_headings(text)
            if re.search(r"name|title", h, re.IGNORECASE)]


# --- the property ------------------------------------------------------------

@pytest.mark.parametrize("path", FILES, ids=NAMES)
def test_decoder_asks_for_the_name_as_a_heading(path):
    """
    The output template must carry a bracketed name placeholder as a heading,
    so the model substitutes rather than reproduces.
    """
    stem = os.path.basename(path)[:-3]
    found = name_placeholders(read(path))
    if stem in KNOWN_MISSING:
        pytest.skip(f"{stem} is a recorded gap; see KNOWN_MISSING")
    assert found, (
        f"{stem} has no bracketed name placeholder heading, so the first "
        f"heading of its page will be whatever label the template offers")


def test_the_known_gap_is_exactly_what_it_claims():
    """
    Fixing a decoder must fail this until KNOWN_MISSING is updated, and
    regressing one must fail it too. A stale exemption list hides the bug it
    was written to record.
    """
    actual = {os.path.basename(p)[:-3] for p in FILES
              if not name_placeholders(read(p))}
    assert actual == KNOWN_MISSING, (
        f"KNOWN_MISSING is stale. Decoders without a name placeholder are "
        f"{sorted(actual)}; the set says {sorted(KNOWN_MISSING)}")


@pytest.mark.parametrize("path", FILES, ids=NAMES)
def test_no_numbered_headings_in_the_output_template(path):
    """
    "### **1. Quest Title**" is a heading the model reproduces verbatim, number
    and all. Numbering belongs in the decoding INSTRUCTIONS, which the page
    never shows, not in the output template it copies.
    """
    stem = os.path.basename(path)[:-3]
    if stem in KNOWN_MISSING:
        pytest.skip(f"{stem} is a recorded gap; see KNOWN_MISSING")
    text = read(path)
    # Only the output template matters; instructions above it may number freely.
    marker = re.search(r"(?i)^#{1,4}.*(structured )?output format", text, re.M)
    template = text[marker.start():] if marker else text
    offenders = [h for h in headings(template)
                 if NUMBERED_HEADING.match("### " + h)]
    assert not offenders, \
        f"{stem} numbers its output headings, which the model copies: {offenders}"


# --- the three that were fixed -----------------------------------------------

# Ways a decoder can say "substitute this, do not reproduce it". Kept as a set
# of markers rather than one sentence: the first version of this test demanded
# the exact phrase "must not appear" and failed `quest`, which says "never print
# the bracket text itself" and means the same thing. That is the phrasing trap
# PROJECT_STATE §7 records -- eleven tests once broke because the author reworded
# a section better than the original.
_SUBSTITUTION_MARKERS = (
    "must not appear", "never print", "do not print", "must not be printed",
    "replace the bracket", "replace the placeholder", "not appear in the output",
)


@pytest.mark.parametrize("stem,banned", [
    ("world", "World Name"),
    ("region", "Region Name"),
    ("quest", "Quest Title"),
    ("settlement", "Settlement Name"),
    ("travel", "Route Name"),
])
def test_the_fixed_decoders_forbid_printing_the_label(stem, banned):
    """
    Each of the three offers the label as a bracketed placeholder AND tells the
    model to substitute rather than reproduce it. Both halves matter: the
    bracket alone was not enough for these three, which is why they leaked.
    """
    text = read(os.path.join(DECODER_DIR, f"{stem}.md"))
    assert f"\\[{banned}]" in text or f"[{banned}]" in text, \
        f"{stem} no longer offers a [{banned}] placeholder"
    lowered = text.lower()
    assert any(marker in lowered for marker in _SUBSTITUTION_MARKERS), \
        (f"{stem} offers the placeholder but never says to substitute it. "
         f"Expected one of {_SUBSTITUTION_MARKERS}")
