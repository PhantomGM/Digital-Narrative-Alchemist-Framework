"""
Audit every genome for values meaning "there is no answer", and every decoder
for whether it anticipates them.

This is the recurring bug class in docs/PROJECT_STATE.md §4a, made repeatable.
It was found by hand in four decoders -- `culture` (55% of rolls carried one),
`text`, `creature`, `lore` -- each time because a generator emitted an absence
under an instruction demanding exactly the content the absence denied, so
inventing an answer was the compliant reading of the prompt.

The §4a recipe scans the GENERATOR's module-level vocabularies. That works for
the seven refined genomes, which name their values. It finds almost nothing in
the fourteen unrefined ones, because those emit bare integers and their value
meanings live in the DECODER's decoding key instead. So this audits both:

  1. String vocabularies the generator emits          (the §4a scan)
  2. Integer axes that can emit 0 or a documented low  (the unrefined case)
  3. Null-ish entries in the decoder's own value table (where the meaning lives)

and for each, whether the decoder says what to do about it.

Run from the repo root:
    .\\venv\\Scripts\\python.exe scripts/audit_null_values.py
    .\\venv\\Scripts\\python.exe scripts/audit_null_values.py --rolls 5000 --type wonder
"""

import argparse
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common.console import enable_safe_stdout  # noqa: E402
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402

DECODERS = os.path.join(os.path.dirname(__file__), "..", "src",
                        "layer5_dna_substrate", "decoders")

REFINED = {"npc", "faction", "creature", "culture", "lore", "text", "item"}

# A value whose meaning is "there is no answer".
#
# "barren" was in this list on the first run and reported at 49.7% of creature
# rolls. It is not an absence -- it is a descriptor from a Fecund/Barren pair,
# and a creature can be barren and still be fully specified. Words describing a
# STATE belong in the cross-field check below, not here; only words meaning the
# genome declined to answer belong here.
NULL_TOKEN = re.compile(
    r"^(none|none-\w+|no-\w+|\w+-none|unknown|nothing|never|never-\w+|"
    r"forgotten|lost|missing|absent|does-not-\w+|not-\w+|"
    r"\w+-unknown|no)$", re.IGNORECASE)

# A numbered entry in a decoder's value table: "| `GDN` | 0 none, 1 construct,"
TABLE_ENTRY = re.compile(r"(?:^|[|`\s(,])(\d+)\s+([^,|\n]{1,40})")


def is_null_phrase(phrase):
    """
    Does this table value mean "there is no answer"?

    The distinction that matters, and that the first version of this script got
    wrong: a null word MODIFYING a noun is content, not an absence. "lost
    super-weapons" and "lost knowledge" are treasures a party can find --
    reported as nulls on the first run, and both wrong. "location unknown" is a
    real absence and has to still be caught, so a trailing null word counts
    where a leading one does not.
    """
    p = " ".join(phrase.split()).strip(" .*`").lower()
    if p in {"none", "unknown", "nothing", "absent", "nil"}:
        return True
    if p.startswith(("no ", "never ", "does not ", "cannot ")):
        return True
    if p.endswith((" unknown", " lost", " forgotten", " none", " remaining")):
        return True
    return False

# Does the decoder tell the model what to do when a field has no answer?
HANDLES_ABSENCE = (
    "if none", "when none", "where none", "if it is none", "if the value is 0",
    "absence", "no answer", "nothing to", "says none", "reads none",
    "means none", "do not invent", "don't invent", "rather than inventing",
    "leave it", "say so", "no guardian", "unguarded", "if 0", "if zero",
    "none is a real answer", "an absence is",
)


def read_decoder(etype):
    path = os.path.join(DECODERS, f"{etype}.md")
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def roll(forge, etype, n):
    """Roll a genome n times, returning every DNA string."""
    out = []
    for _ in range(n):
        try:
            out.append(forge.synthesize_element(etype)["dna"])
        except Exception as exc:  # a generator that needs args
            return [], f"{type(exc).__name__}: {exc}"
    return out, None


def string_tokens(dnas):
    """Word-ish tokens the genome emits, for the §4a vocabulary scan."""
    counts = Counter()
    for dna in dnas:
        for tok in re.findall(r"[A-Za-z][A-Za-z'\-]{2,}", dna):
            counts[tok] += 1
    return counts


def axis_values(dnas):
    """
    axis -> Counter of integer values, across the common DNA shapes.

    Two traps, both hit on the first run of this script:

    A decimal modifier like `<AP:0.8,MR:1.5>` matched as AP:0, so the audit
    reported that `item`, `location`, `settlement`, `quest` and `trap` all
    emitted a zero on three axes in ~45% of rolls. Fifteen findings, every one
    of them a modifier between 0.1 and 0.9 and none of them an absence. Hence
    the negative lookahead for a decimal point.

    And a key ending in a digit, concatenated with its value, is genuinely
    ambiguous: establishment writes CH1 with value 0 as the string "CH10". No
    regex recovers that, and neither can a decoder -- see ambiguous_keys().
    """
    axes = defaultdict(Counter)
    for dna in dnas:
        # KEY:value -- unambiguous, but must not swallow the integer part of a
        # decimal.
        for key, val in re.findall(
                r"\b([A-Z][A-Z0-9_]{1,7})\s*:\s*(\d+)(?!\.\d)\b", dna):
            axes[key][int(val)] += 1
        # KEYvalue -- only safe when the key carries no trailing digit.
        for key, val in re.findall(r"\b([A-Z]{2,7})(\d{1,2})\b(?!\.\d)", dna):
            axes[key][int(val)] += 1
    return axes


GENERATORS = os.path.join(os.path.dirname(__file__), "..", "src",
                          "layer5_dna_substrate", "generators")


def digit_suffixed_keys(etype):
    """
    Gene names ending in a digit, read from the generator source.

    Gated on the source rather than inferred from the DNA, because inference
    cannot tell CU=10 from CU1=0. The first version of this check guessed, and
    reported `region` and `regional_poi` as ambiguous when neither defines a
    digit-suffixed gene at all -- CU10 is simply CU at 10. Only `establishment`
    genuinely does this.
    """
    path = os.path.join(GENERATORS, f"{etype}.py")
    if not os.path.isfile(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return set(re.findall(r'"([A-Z]{2,6}\d)"\s*:', fh.read()))


def ambiguous_keys(etype, dnas):
    """
    Keys ending in a digit, written straight against their value, so the
    boundary between key and value is unrecoverable. establishment writes CH1
    with value 0 as "CH10", and nothing in the string says which it is.
    """
    keys = digit_suffixed_keys(etype)
    if not keys:
        return Counter()
    found = Counter()
    for dna in dnas[:200]:
        for key in keys:
            for val in re.findall(rf"\b{key}(\d{{1,2}})\b", dna):
                found[f"{key}+{val}"] += 1
    return found


def audit(etype, forge, rolls):
    dnas, err = roll(forge, etype, rolls)
    decoder = read_decoder(etype)
    lowered = decoder.lower()
    findings = []

    if err:
        return [("SKIP", err, "")], decoder

    # 1 & 2 -- what the genome actually emits
    for tok, n in string_tokens(dnas).items():
        if NULL_TOKEN.match(tok):
            pct = 100.0 * sum(1 for d in dnas if tok in d) / len(dnas)
            addressed = tok.lower() in lowered
            findings.append(("VOCAB", f"{tok!r} in {pct:.1f}% of rolls",
                             "named in decoder" if addressed
                             else "NOT named in decoder"))

    for axis, counts in sorted(axis_values(dnas).items()):
        zeros = counts.get(0, 0)
        if zeros:
            pct = 100.0 * zeros / sum(counts.values())
            # Is the zero explained anywhere the axis is mentioned? Checking
            # only the FIRST mention reported wonder's GDN as undocumented,
            # because GDN appears first in a prose contradiction pair and its
            # value table sits fifty lines below. Check every occurrence.
            explained = any(
                re.search(r"\b0\b", decoder[m.start():m.start() + 220])
                for m in re.finditer(re.escape(axis), decoder))
            findings.append(("ZERO-AXIS", f"{axis} emits 0 in {pct:.1f}% of rolls",
                             "0 is documented" if explained
                             else "0 is NOT documented"))

    # 3 -- null entries in the decoder's own value table
    seen = set()
    for num, phrase in TABLE_ENTRY.findall(decoder):
        if not is_null_phrase(phrase):
            continue
        clean = " ".join(phrase.split()).strip(" .*`")[:28]
        if '"' in clean or "'" in clean:
            continue  # prose, not a table value: 'does not mean "eight copies"'
        if (num, clean) in seen:
            continue
        seen.add((num, clean))
        # NO VERDICT HERE, deliberately. Whether a decoder handles an absence is
        # a judgement about prose, and PROJECT_STATE §7 records that keyword
        # probes are unreliable for exactly that. This script asserted it anyway
        # on an earlier run and was wrong in both directions: it called wonder's
        # documented GDN 0 undocumented, and called regional_poi unhandled when
        # its INH-none case has an explicit replacement question. Probes find
        # candidates; a reader decides.
        findings.append(("TABLE-NULL", f"value {num} = {clean!r}",
                         "confirm by reading"))

    # 4 -- keys whose boundary with their value is unrecoverable
    amb = ambiguous_keys(etype, dnas)
    if amb:
        keys = sorted({k.split("+")[0] for k in amb})
        findings.append(("AMBIGUOUS-KEY",
                         f"{', '.join(keys)} run straight into their values",
                         "NOT separable"))

    return findings, decoder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rolls", type=int, default=3000)
    ap.add_argument("--type", help="audit a single genome")
    args = ap.parse_args()

    forge = ProceduralForge()
    types = [args.type] if args.type else sorted(forge.generators)

    print(f"Null-value audit -- {args.rolls} rolls per genome\n")
    total_unhandled = 0
    for etype in types:
        findings, decoder = audit(etype, forge, args.rolls)
        tag = "refined" if etype in REFINED else "UNREFINED"
        handles = any(p in decoder.lower() for p in HANDLES_ABSENCE)
        header = (f"{etype}  [{tag}]"
                  f"{'  (decoder discusses absence)' if handles else ''}")
        print(header)
        print("-" * len(header))
        if not findings:
            print("   no null-ish values emitted or documented\n")
            continue
        for kind, what, verdict in findings:
            bad = verdict.startswith(("NOT", "0 is NOT"))  # "confirm by reading" is not a failure
            total_unhandled += bad
            mark = "  <-- " if bad else "      "
            print(f"   {kind:11} {what:<44}{mark}{verdict}")
        print()

    print(f"\n{total_unhandled} finding(s) the decoder does not visibly address.")


if __name__ == "__main__":
    enable_safe_stdout()
    main()
