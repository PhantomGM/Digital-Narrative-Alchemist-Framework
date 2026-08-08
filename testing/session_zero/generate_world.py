"""
Session 0 -> contract -> world. The generation half of the Session 0 trial.

REWIRED after trial 1. This originally carried its own hand-rolled contract (a
list of type/count tuples) and its own hand-written safety block, and both are
now real machinery: `ContentContract` from Layer V and `SafetyRegister` from
Layer III. That is the point of trial 2 -- trial 1 proved the design on
scaffolding, this exercises the implementation.

The three defects trial 1 found, and where each is now handled:

  per-slot briefs   `Slot.brief`, which cannot be omitted. Trial 1 kept its
                    briefs in a print statement, so the one regional_poi
                    briefed as "the mine" generated a dimensional arch.
  ordering          `Slot.depends_on` + `contract.ordered()`. Trial 1 generated
                    `linguistic` sixth and `settlement` third, naming the town
                    before its language existed.
  tone              `Slot.tone`. Trial 1 asked for warmth in the shared block
                    and got a uniformly grim world, because every genome pulls
                    toward conflict and a count cannot argue with that.

Deliberately NOT wired to data/world_builder_registry.json. Output goes to
testing/session_zero/registry.json.

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
from layer3_operations.safety_register import (  # noqa: E402
    LINE, SETTING, VEIL, SafetyConstraint, SafetyRegister)
from layer5_dna_substrate.content_contract import (  # noqa: E402
    ContentContract, RuntimeDirectives, Slot)
from layer5_dna_substrate.decoder import DNADecoder  # noqa: E402
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY_OUT = os.path.join(HERE, "registry.json")
PAGES_OUT = os.path.join(HERE, "pages")

# ── The table's Lines and Veils, as the four players actually stated them ────
#
# Note what the structure now carries that a flat list could not: that the
# bigotry Line binds the SETTING, that the animal Line is about on-screen
# death, and that the claustrophobia Veil has a boundary a player supplied in
# his own words. Holders are recorded and never rendered.
SAFETY = SafetyRegister([
    SafetyConstraint("sexual violence of any kind", kind=LINE,
                     holders=("elias", "sarah", "chloe")),
    SafetyConstraint("harm or abuse involving children", kind=LINE,
                     holders=("elias",)),
    SafetyConstraint(
        "real-world bigotry: homophobia, transphobia, racism", kind=LINE,
        scope=SETTING,
        note="Factions and cultures may be cruel, but for reasons invented "
             "here, never as a mapped analogue of a real-world prejudice",
        holders=("sarah",)),
    SafetyConstraint(
        "animal cruelty", kind=LINE,
        note="No pet, familiar or companion creature dies on screen",
        holders=("marcus", "chloe")),
    SafetyConstraint("forced institutionalization", kind=LINE,
                     holders=("marcus",)),
    SafetyConstraint("graphic torture", kind=VEIL, holders=("elias", "sarah")),
    SafetyConstraint("detailed descriptions of gore", kind=VEIL,
                     holders=("elias",)),
    SafetyConstraint("visceral eye trauma", kind=VEIL, holders=("sarah",)),
    SafetyConstraint("romance or intimacy involving player characters",
                     kind=VEIL, note="Strict fade to black",
                     holders=("marcus", "chloe")),
    SafetyConstraint(
        "prolonged claustrophobia, or being buried alive", kind=VEIL,
        note="This world is built around a mine, so underground spaces are "
             "expected. What is forbidden is enclosure as a sustained "
             "experience: no air running out, no squeezing through a passage, "
             "nobody pinned or trapped under rubble, no tension whose source "
             "is whether they can get out. A tunnel is where a scene happens, "
             "never what it is about. A collapse may be reported, never "
             "experienced. When uncertain, cut early",
        holders=("marcus",)),
    SafetyConstraint("gaslighting or severe psychological manipulation",
                     kind=VEIL, holders=("chloe",)),
])

# ── What the table asked for that is not a constraint on content ────────────
TABLE_AGREEMENTS = """\
## WHAT THIS TABLE ASKED FOR (from Session 0 -- design constraints)

TONE: Warm and funny at the table, genuinely unsettling in the fiction. Not
grimdark. Dread accumulates; it does not shock. Horror here is "someone came
back subtly wrong", never blood.

STRUCTURE: A frontier mining town at the edge of a collapsed high-fantasy
empire, weird-western in texture. A fixed recurring cast above ground; a mine
below that goes deeper than the maps admit. The town and the deep alternate --
the town is where relationships and support play land, the deep is where
momentum lives. NEITHER is downtime.

DEATH: Possible and real. It must follow visibly from a choice the players
made, never from a single unforeseeable roll.

WHAT THE TABLE WILL NOT SIT THROUGH: combat as a foregone formality; plots on
rails where choices stop mattering; sessions of logistics without momentum;
relentless intensity with no room to breathe.

LEAVE ROOM: do not pre-resolve who in this town could be redeemed, and do not
write an NPC whose arc is visibly pre-assigned. The table wants to find that
themselves. Write people with reasons, not with destinies.
"""

# ── Session 0 output that shapes the GM, not the world ──────────────────────
DIRECTIVES = RuntimeDirectives(
    pacing=[
        "Alternate the town and the deep. Neither is downtime.",
        "Fewer, bigger fights, each with a social exit that grows out of the "
        "tactical layer rather than skipping it.",
    ],
    spotlight=[
        "The Loom Syndicate needs equal stage time or the three-way conflict "
        "collapses into a two-sided fight with a paperwork bystander.",
        "Recognise the support player socially -- someone notices aloud -- "
        "rather than mechanically. She does not want the numbers spotlight.",
    ],
    signals=[
        "Veils are pre-agreed; transition automatically and never make anyone "
        "ask for a fade in the moment.",
        "One player cannot raise a boundary aloud. Offer the private channel "
        "to the whole table, never attributed, and check in privately after "
        "session one.",
        "That player going quiet in a scene is NOT a distress signal. She "
        "said so herself: she is probably just listening.",
    ],
)

# ── The contract: a graph, with briefs and tone ─────────────────────────────
CONTRACT = ContentContract(
    deliverable="campaign pitch",
    directives=DIRECTIVES,
    slots=[
        Slot("world", key="world",
             brief="The collapsed high-fantasy empire and the frontier beyond "
                   "its edge. Its fall is why the frontier exists."),
        Slot("culture", key="culture", depends_on=("world",),
             brief="The people who came out to the frontier to escape "
                   "something, and who still move rather than settle."),
        # Ahead of every named thing, which is the ordering fix.
        Slot("linguistic", key="linguistic", depends_on=("culture",),
             brief="The naming rules of the frontier, so that every person and "
                   "place named after this point is consistent with one another."),
        Slot("region", key="region", depends_on=("world", "linguistic"),
             brief="The dust country the mining town sits in. Weird-western in "
                   "texture: distances, hard light, bad water."),
        Slot("settlement", key="town", depends_on=("region", "linguistic"),
             brief="THE TOWN: a frontier mining settlement grown up inside a "
                   "fortress that outlived its empire. It has a fixed cast the "
                   "players will meet every session."),
        Slot("regional_poi", key="mine", depends_on=("town",),
             brief="THE MINE beneath the town. A working extraction site whose "
                   "shafts descend further than any surviving survey admits. It "
                   "is the physical centre of the campaign. It is NOT a ruin, "
                   "an arch, a portal or a natural formation. It is a mine."),
        # The tonal slot. Trial 1 had no way to ask for this at all.
        Slot("establishment", key="haven", depends_on=("town",),
             brief="The one room in town where nothing is wrong. Where the "
                   "party eats, argues about nothing, and is known by name.",
             tone="WARM, and it must stay warm. This is the 'just breathe' "
                  "place a player explicitly asked for and trial 1 failed to "
                  "produce. It has no secret, no hidden agenda, no menace "
                  "under the floorboards, and nothing here is about to go "
                  "wrong. Its interest comes from the people in it and their "
                  "ordinary lives. Resist every pull toward making it "
                  "sinister -- that pull is the genome's default, not this "
                  "world's need."),
        Slot("faction", key="factions", count=3, depends_on=("mine", "town"),
             brief="Three powers with competing claims, ASYMMETRIC IN KIND and "
                   "not merely in motive: one wants what is below, one wants "
                   "the shaft sealed, one wants the town itself and is "
                   "indifferent to the mine. Same want for different reasons "
                   "is a coalition, not a conflict."),
        Slot("npc", key="cast", count=3, depends_on=("factions", "haven"),
             brief="The recurring town cast. People with reasons, not "
                   "destinies: no arc may be visibly pre-assigned."),
        Slot("creature", key="the-changed", depends_on=("mine",),
             brief="What the deep does to people who go too far down. Subtle "
                   "and cumulative, never gore."),
        Slot("lore", key="open-question", depends_on=("factions",),
             brief="The open question the campaign is about. Do NOT resolve "
                   "it; leave the load-bearing part contested."),
        Slot("quest", key="hook", depends_on=("cast", "mine"),
             brief="The opening hook that puts the party in the mine in the "
                   "first hour of the first session."),
    ],
)

SEEDABLE = {"npc", "faction", "creature", "culture", "lore", "text", "item"}


def build_context(prior_pages, brief=""):
    """
    Note what is NOT here any more: the safety block. It used to be pasted into
    this string by hand. It now rides ContextPackage.safety, so it reaches the
    auditor as well as the decoder -- which was the whole architectural
    argument, and which a hand-pasted block could never satisfy.
    """
    parts = [TABLE_AGREEMENTS]
    if brief:
        parts.append(brief)
    if prior_pages:
        parts.append("## ALREADY ESTABLISHED IN THIS WORLD\n"
                     "Reference these. Do not recreate them, do not rename "
                     "them, and do not contradict them.\n\n" +
                     "\n\n".join(prior_pages))
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Generate DNA and print the plan; make no model calls.")
    ap.add_argument("--seed", type=int, default=20260807)
    ap.add_argument("--out", default=PAGES_OUT)
    args = ap.parse_args()

    forge = ProceduralForge()
    CONTRACT.validate(known_types=list(forge.generators))

    os.makedirs(args.out, exist_ok=True)
    registry = DNARegistry()
    decoder = None if args.dry_run else DNADecoder()
    safety_block = SAFETY.render()

    order = CONTRACT.ordered()
    total = CONTRACT.total_entities()
    print(f"=== {CONTRACT.deliverable}: {total} entities across "
          f"{len(order)} slots ===")
    print(f"    order: {' -> '.join(s.name for s in order)}")
    print(f"    safety: {len(SAFETY.merged().lines())} Lines, "
          f"{len(SAFETY.merged().veils())} Veils\n")

    prior, made, index, counts = [], 0, [], {}
    for slot in order:
        for i in range(slot.count):
            made += 1
            kwargs = {"seed": args.seed + made} if slot.type in SEEDABLE else {}
            dna = forge.synthesize_element(
                slot.type, constraint_package=safety_block, **kwargs)

            label = slot.name + (f" {i + 1}/{slot.count}" if slot.count > 1 else "")
            print(f"[{made}/{total}] {label:<18} ({slot.type})")
            if args.dry_run:
                print(f"          DNA: {dna['dna'][:80]}...")
                continue

            # Each layer used for what it is: the constraints in `safety`
            # (both surfaces, uncapped), the world in `world_frame`, and this
            # slot's brief in `directives`, which is where per-generation
            # guidance belongs.
            from layer5_dna_substrate.context_assembler import ContextPackage
            package = ContextPackage(
                safety=safety_block,
                world_frame=build_context(prior),
                directives=CONTRACT.brief_for(slot, i))

            t0 = time.time()
            page = decoder.decode_element(dna, context=package)
            elapsed = time.time() - t0

            record_id = registry.register_element(
                element_type=slot.type, raw_dna=dna["dna"], decoded_profile=page,
                tags=["session_zero_trial2", f"slot_{slot.name}"])
            fname = (f"{made:02d}_{slot.name}"
                     f"{'_' + str(i + 1) if slot.count > 1 else ''}.md")
            with open(os.path.join(args.out, fname), "w",
                      encoding="utf-8", newline="\n") as fh:
                fh.write(page)

            head = page.strip().split("\n\n")[0][:600]
            prior.append(f"### [{slot.type}] {fname}\n{head}")
            counts[slot.name] = counts.get(slot.name, 0) + 1
            index.append({"n": made, "slot": slot.name, "type": slot.type,
                          "file": fname, "id": record_id, "chars": len(page),
                          "seconds": round(elapsed, 1)})
            print(f"          -> {fname}  ({len(page)} chars, {elapsed:.1f}s)")

    if args.dry_run:
        print("\nDry run complete. No model calls made.")
        return

    registry.save_to_json(REGISTRY_OUT)
    with open(os.path.join(HERE, "generation_index.json"), "w",
              encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)

    outstanding = CONTRACT.unfilled(counts)
    print(f"\n=== {made} entities -> {REGISTRY_OUT} ===")
    print("contract satisfied" if not outstanding
          else f"STILL OWED: {outstanding}")


if __name__ == "__main__":
    enable_safe_stdout()
    main()
