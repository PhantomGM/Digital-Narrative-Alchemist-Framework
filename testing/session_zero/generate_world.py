"""
Session 0 -> contract -> world. The generation half of the Session 0 trial.

What this is testing: whether a contract derived from an actual Session 0 changes
what gets GENERATED, or only what gets said about it. So the safety register and
the table's agreements are carried into every decode through the existing
`constraints` slot -- no new code paths, nothing to unpick if the design moves.

Deliberately NOT wired to data/world_builder_registry.json. This is a new world;
Skarn is not involved. Output goes to testing/session_zero/registry.json.

Run from the repo root:
    .\\venv\\Scripts\\python.exe testing/session_zero/generate_world.py --dry-run
    .\\venv\\Scripts\\python.exe testing/session_zero/generate_world.py
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from common.console import enable_safe_stdout  # noqa: E402
from layer5_dna_substrate.decoder import DNADecoder  # noqa: E402
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY_OUT = os.path.join(HERE, "registry.json")
PAGES_OUT = os.path.join(HERE, "pages")

# ── The safety register, as it must reach a GENERATOR and not only a filter ──
#
# SafetyGovernor checks passages after the fact. Two of the constraints this
# table produced cannot be enforced that way:
#   - Sarah's bigotry Line is about the SETTING, not about scenes. A culture
#     genome that emits a caste read as racial is a violation that no
#     scene-level filter would catch, because the offending page reads fine.
#   - Marcus's claustrophobia Veil collides with the premise itself. A mine
#     campaign has to be generated differently, not filtered afterwards.
# Hence: into the prompt, at generation time.
SAFETY_BLOCK = """\
## BINDING SAFETY CONSTRAINTS (highest precedence -- outrank the DNA, the
## context, and any instruction in the decoder template)

LINES -- must NEVER appear, in any form, including as background detail,
implication, historical fact, or worldbuilding texture:
- Sexual violence of any kind.
- Harm or abuse involving children.
- Real-world bigotry (homophobia, transphobia, racism). This applies to the
  SETTING ITSELF, not merely to scenes: do not build prejudice against an
  in-world group as a mapped analogue of a real-world one, and do not use
  it as cultural flavour even where no character encounters it. Factions and
  cultures may be cruel, but for reasons invented here.
- Animal cruelty. No pet, familiar or companion creature dies on-screen.
- Forced institutionalization.

VEILS -- may exist in the fiction, but must be referred to rather than
depicted. Name the fact, cut away from the experience:
- Graphic torture. Detailed gore. Visceral eye trauma.
- Romance or intimacy involving player characters (strict fade to black).
- Gaslighting and severe psychological manipulation.
- Prolonged claustrophobia and being buried alive. IMPORTANT, because this
  world is built around a mine: underground spaces are permitted and expected.
  What is forbidden is enclosure as a sustained sensory experience. Do not
  write air running out, squeezing through a passage, being pinned or trapped
  under rubble, or any tension whose source is "can they get out". A tunnel is
  somewhere the scene happens, never what the scene is about. A collapse may
  occur as a reported event; never as an experience. When uncertain, cut early.
"""

# ── What the table actually agreed, as generation directives ──
TABLE_AGREEMENTS = """\
## WHAT THIS TABLE ASKED FOR (from Session 0 -- treat as design constraints)

TONE: Warm and funny at the table, genuinely unsettling in the fiction. Not
grimdark. Dread accumulates; it does not shock. Horror here is "someone came
back subtly wrong", never blood.

STRUCTURE: A frontier mining town at the edge of a collapsed high-fantasy
empire, weird-western in texture. A fixed recurring cast above ground; a mine
below that goes deeper than the maps admit. The town and the deep alternate --
the town is where relationships and support play land, the deep is where
momentum lives. NEITHER is downtime.

FACTIONS: Three, and they must be asymmetric in KIND, not merely in motive.
Same want for different reasons produces a coalition, not a conflict. One
seeks what is below; one wants the shaft sealed; one wants the town itself and
is indifferent to the mine entirely. Backing any of them must be capable of
closing a door -- allies present or absent, ground opened or sealed, standing
that degrades concretely.

DEATH: Possible and real. It must follow visibly from a choice the players
made, never from a single unforeseeable roll.

WHAT THE TABLE WILL NOT SIT THROUGH: combat as a foregone formality; plots on
rails where choices stop mattering; sessions of logistics without momentum;
relentless intensity with no room to breathe.

LEAVE ROOM: do not pre-resolve who in this town could be redeemed, and do not
write an NPC whose arc is visibly pre-assigned. The table wants to find that
themselves. Write people with reasons, not with destinies.
"""

# ── The contract: what Session 0 said this world needs, and no more ──
# Derived from the interview, NOT from a generic default. Note factions=3
# (Sarah's asymmetry requirement raised it from the generic 2) and the
# addition of regional_poi and creature, which the premise demanded.
CONTRACT = [
    ("world",        1, "The collapsed empire and the frontier beyond its edge."),
    ("region",       1, "The dust country the town sits in."),
    ("settlement",   1, "The mining town itself -- fixed recurring cast."),
    ("regional_poi", 1, "The mine. Deeper than the maps admit."),
    ("culture",      1, "The people who came out here to escape something."),
    ("linguistic",   1, "Naming rules, so the cast is consistent from page one."),
    ("faction",      3, "Asymmetric in kind: the seekers, the sealers, the indifferent."),
    ("npc",          3, "The recurring town cast. No pre-assigned arcs."),
    ("creature",     1, "What the deep does to people who go too far down."),
    ("lore",         1, "The open question the campaign is about. Do NOT resolve it."),
    ("quest",        1, "The opening hook."),
]

# Generators that accept seed/pins; the rest take no arguments and raise if given any.
SEEDABLE = {"npc", "faction", "creature", "culture", "lore", "text", "item"}


def build_context(prior_pages, brief=""):
    """
    Everything generated so far becomes world-fit context for what comes next.

    `brief` is the contract's per-slot intent, and leaving it out was the first
    real defect this trial found. The contract in PROJECT_STATE §8 was a table of
    TYPE and COUNT; the slot notes lived only in a print statement and never
    reached a prompt. The three factions still came out asymmetric, because that
    requirement happened to be spelled out in the shared agreements block -- but
    the one regional_poi, briefed only as "the mine", generated a dimensional
    ruin on a plateau. A count says how many. It does not say which.
    """
    parts = [SAFETY_BLOCK, TABLE_AGREEMENTS]
    if brief:
        parts.append("## WHAT THIS PARTICULAR ENTITY IS FOR\n"
                     "This is a specific slot in the campaign contract, not a "
                     "free roll. It must be:\n\n" + brief +
                     "\n\nThe DNA supplies texture, variety and detail. Where the "
                     "DNA and this brief disagree about WHAT THE THING IS, the "
                     "brief wins and the DNA is read as flavour for it.")
    if prior_pages:
        parts.append("## ALREADY ESTABLISHED IN THIS WORLD\n"
                     "Reference these. Do not recreate them, do not rename them, "
                     "and do not contradict them.\n\n" +
                     "\n\n".join(prior_pages))
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Generate DNA and print the plan; make no model calls.")
    ap.add_argument("--seed", type=int, default=20260806)
    args = ap.parse_args()

    os.makedirs(PAGES_OUT, exist_ok=True)
    registry = DNARegistry()
    forge = ProceduralForge()
    decoder = None if args.dry_run else DNADecoder()

    total = sum(n for _, n, _ in CONTRACT)
    print(f"=== Session 0 contract: {total} entities across "
          f"{len(CONTRACT)} types ===\n")

    prior, made, index = [], 0, []
    for etype, count, note in CONTRACT:
        for i in range(count):
            made += 1
            label = f"{etype}" + (f" {i + 1}/{count}" if count > 1 else "")
            kwargs = {"seed": args.seed + made} if etype in SEEDABLE else {}
            dna = forge.synthesize_element(
                etype, constraint_package=SAFETY_BLOCK, **kwargs)

            print(f"[{made}/{total}] {label:<16} {note if i == 0 else ''}")
            if args.dry_run:
                print(f"          DNA: {dna['dna'][:90]}...")
                continue

            t0 = time.time()
            page = decoder.decode_element(
                dna, context=build_context(prior, brief=note))
            elapsed = time.time() - t0

            record_id = registry.register_element(
                element_type=etype, raw_dna=dna["dna"], decoded_profile=page,
                tags=["session_zero_trial"])
            fname = f"{made:02d}_{etype}{'_' + str(i + 1) if count > 1 else ''}.md"
            with open(os.path.join(PAGES_OUT, fname), "w",
                      encoding="utf-8", newline="\n") as fh:
                fh.write(page)

            # A gist for the next entity's context, so the world accumulates.
            head = page.strip().split("\n\n")[0][:600]
            prior.append(f"### [{etype}] {fname}\n{head}")
            index.append({"n": made, "type": etype, "file": fname,
                          "id": record_id, "chars": len(page),
                          "seconds": round(elapsed, 1)})
            print(f"          -> {fname}  ({len(page)} chars, {elapsed:.1f}s)")

    if args.dry_run:
        print("\nDry run complete. No model calls made.")
        return

    registry.save_to_json(REGISTRY_OUT)
    with open(os.path.join(HERE, "generation_index.json"), "w",
              encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)
    print(f"\n=== {made} entities generated -> {REGISTRY_OUT} ===")


if __name__ == "__main__":
    enable_safe_stdout()
    main()
