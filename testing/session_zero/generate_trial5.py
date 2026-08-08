"""
Trial 5: the full pipeline, with everything the previous four trials built.

Trial 2 exercised ContentContract and ContextPackage.safety. Trial 5 adds the
two pieces built since -- ExpansionPolicy and GhostRegistry -- so the frontier
is advanced as well as generated, which no trial has done end to end.

Two things here are deliberately awkward, because the interviews made them so:

  The animal-cruelty Line is registered TWICE, with the two incompatible
  readings the same player gave across trials 4 and 5. That is not a mistake in
  the fixture. It is the contested case, and the run should demonstrate
  merged() dropping the narrowing, keeping the strict unqualified form, and
  raising it to the author through conflicts().

  The signalling directive says nobody will speak up. All four players said so
  when asked directly in trial 5, including the ten-year veteran who had
  volunteered the opposite twice under a looser questionnaire.

    .\\venv\\Scripts\\python.exe testing/session_zero/generate_trial5.py --dry-run
    .\\venv\\Scripts\\python.exe testing/session_zero/generate_trial5.py
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
from layer5_dna_substrate.canon_composer import CanonComposer  # noqa: E402
from layer5_dna_substrate.content_contract import (  # noqa: E402
    ContentContract, RuntimeDirectives, Slot)
from layer5_dna_substrate.context_assembler import (
    AssemblyRequest, ContextAssembler, ContextPackage)  # noqa: E402
from layer5_dna_substrate.decoder import DNADecoder  # noqa: E402
from layer5_dna_substrate.expansion_manager import ExpansionManager  # noqa: E402
from layer5_dna_substrate.expansion_policy import (  # noqa: E402
    ExpansionPolicy, measure_branching, summarise)
from layer5_dna_substrate.forge import ProceduralForge  # noqa: E402
from layer5_dna_substrate.ghost_registry import GhostRegistry  # noqa: E402
from layer5_dna_substrate.registry import DNARegistry  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(HERE, "pages_trial5")   # default; --out overrides

SAFETY = SafetyRegister([
    SafetyConstraint("sexual violence", kind=LINE,
                     holders=("elias", "sarah", "chloe")),
    SafetyConstraint("harm or abuse involving children", kind=LINE,
                     holders=("elias",)),
    SafetyConstraint(
        "real-world bigotry: homophobia, transphobia, racism", kind=LINE,
        scope=SETTING,
        note="Not as texture in a culture or faction either, even where no "
             "character encounters it. Societies may be unjust for reasons "
             "invented here",
        holders=("sarah",)),
    # The contested one. Two readings, deliberately both present.
    SafetyConstraint("animal cruelty", kind=LINE, narrows=True,
                     note="Only on-screen; as backdrop it is fine",
                     holders=("marcus",)),
    SafetyConstraint("animal cruelty", kind=LINE,
                     note="Even off screen is too much; I would rather not "
                          "know it happened",
                     holders=("marcus",)),
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
        note="The player who holds this named it a live wire in exactly this "
             "genre and asked for the genre anyway. Enclosed places are "
             "expected; enclosure as a sustained experience is not. No air "
             "running out, nobody pinned or sealed in, no scene whose tension "
             "is whether they can get out. A corridor is where a scene "
             "happens, never what it is about. When uncertain, cut early",
        holders=("marcus",)),
    SafetyConstraint("gaslighting or severe psychological manipulation",
                     kind=VEIL, holders=("chloe",)),
])

TABLE_AGREEMENTS = """\
## WHAT THIS TABLE ASKED FOR (from Session 0 -- design constraints)

TONE: Warmer than grimdark, and funny even when it is serious. Dread
accumulates in the dark places; the crew is not cruel to each other. Horror
here is "something is wrong with this hull", never gore.

STRUCTURE: A salvage tender working a dead corridor of space. A fixed crew who
return to the same station and the same galley; derelict hulks they board and
leave. The station and the hulks alternate -- the station is where trust is
earned and support play lands, the hulks are where momentum lives. NEITHER is
downtime.

SUPPLY IS THE SPINE: distance costs. Fuel, air, parts and time are finite and
tracked, and a route is a decision with consequences rather than a transition.
A player asked specifically for the quartermaster problem to be real.

DEATH: possible and real. It must follow visibly from a choice, never from a
single unforeseeable roll, and it should be remembered afterwards by the world.

WHAT THIS TABLE WILL NOT SIT THROUGH: combat as a foregone formality; plots on
rails; sessions of logistics with no mystery underneath; relentless intensity
with no room to breathe.

LEAVE ROOM: do not pre-resolve who could be trusted or redeemed. One player
wants to earn a crew's trust in fiction rather than by table consensus. Write
people with reasons, not destinies.
"""

DIRECTIVES = RuntimeDirectives(
    pacing=["Alternate the station and the hulks. Neither is downtime.",
            "Fewer, bigger fights, each with a non-combat exit that grows out "
            "of the tactical layer rather than skipping it."],
    spotlight=["Supply and attrition must actually bite, or the player who "
               "asked for the quartermaster problem is being humoured.",
               "Recognise the support player socially -- someone notices "
               "aloud -- rather than mechanically.",
               "If a character dies, the world must remember it by name."],
    signals=["ALL FOUR PLAYERS SAID THEY WOULD NOT RAISE A VEIL OUT LOUD, "
             "including the veteran. Do not rely on anyone speaking up.",
             "Provide a card or hand signal that needs no words, and an "
             "in-fiction safeword a player can drop into dialogue.",
             "Offer a private channel during play and an after-session one. "
             "Check in privately after session one and periodically.",
             "Silence is not consent and not a signal. Ask."],
)

INVARIANTS = [
    # Trial 5's pitch drew objections from two of four players on pacing. The
    # agreements block had asked for room to breathe; the hook's brief asked
    # for danger within the hour, and the brief won because it was the more
    # specific instruction. So the pacing rule now rides inside every brief.
    "This table asked for room to breathe and for relationships before stakes. "
    "Nothing you write may open on a countdown, and no entity may make itself "
    "urgent before the party has had a reason to care about anyone. Where "
    "something needs urgency, make it DISCOVERABLE rather than imposed: a "
    "situation that becomes urgent once they understand it, not a clock "
    "already running when they walk in.",
    # "No pre-assigned arcs" was in the NPC brief for trial 5 and still failed
    # -- an NPC arrived with three erased names and stained fingers, and a
    # player said it "feels like the GM's already picked who I'm supposed to
    # suspect". It failed because it was a prohibition with nothing to do
    # instead, which is the §4a lesson: an absence needs a replacement.
    "Write people with reasons, not destinies. Do NOT load a character's first "
    "description with the evidence of what they are hiding -- that tells the "
    "reader who to suspect before the table has met them. Instead give every "
    "person a want they will state, a competence they are known for, and one "
    "ordinary detail that has nothing to do with any plot. What they conceal "
    "should be reachable by asking, never visible on sight.",
]

CONTRACT = ContentContract(
    deliverable="campaign pitch",
    directives=DIRECTIVES,
    invariants=INVARIANTS,
    slots=[
        Slot("world", key="world",
             brief="The collapse that emptied this corridor of space and left "
                   "it full of drifting hulks. Why nobody came back for them."),
        Slot("culture", key="crews", depends_on=("world",),
             brief="The long-haul salvage crews: a people who live between "
                   "places and treat a ship as a home rather than a vehicle."),
        Slot("linguistic", key="linguistic", depends_on=("crews",),
             brief="How salvagers name ships, places and each other, so every "
                   "name after this point is consistent."),
        Slot("region", key="corridor", depends_on=("world", "linguistic"),
             brief="THE DEAD CORRIDOR: the stretch of space the crews work. "
                   "Distances, hazards, and why it is worth the trip."),
        Slot("settlement", key="station", depends_on=("corridor", "linguistic"),
             brief="THE STATION the crew returns to. Not a city -- a working "
                   "waypoint with a fixed cast they see every time."),
        Slot("travel", key="run", depends_on=("station", "corridor"),
             brief="THE RUN between station and salvage. A route whose cost is "
                   "the point: fuel, air, parts and time, and what it means to "
                   "arrive short. A player asked for supply lines that "
                   "genuinely bite, so this must be a decision, not a fade."),
        Slot("regional_poi", key="hulk", depends_on=("corridor", "run"),
             brief="THE HULK they are working now. A derelict ship large "
                   "enough to get lost in, with something wrong aboard it. It "
                   "is a ship, not a station, a ruin or a natural formation."),
        Slot("establishment", key="galley", depends_on=("station",),
             brief="The galley aboard the station. Where the crew eats, argues "
                   "about nothing, and is known by name.",
             tone="WARM, and it must stay warm. A player asked for somewhere "
                  "warmer than grimdark and another for a place to just be "
                  "with people. Nothing is wrong here, nothing is about to go "
                  "wrong, there is no secret under the deckplates. Its "
                  "interest is the people in it and their ordinary lives. "
                  "Resist every pull toward making it sinister; that pull is "
                  "the genome's default, not this world's need."),
        Slot("faction", key="powers", count=3, depends_on=("station", "hulk"),
             brief="Three powers with competing claims on the corridor, "
                   "ASYMMETRIC IN KIND rather than merely in motive: one wants "
                   "what is aboard the hulks, one wants the corridor closed, "
                   "one wants the station's trade and is indifferent to the "
                   "hulks. Same want for different reasons is a coalition, not "
                   "a conflict."),
        Slot("npc", key="crew", count=3, depends_on=("powers", "galley"),
             brief="The fixed cast at the station. People with reasons, not "
                   "destinies -- no arc may be visibly pre-assigned, and none "
                   "of them may be written as obviously trustworthy."),
        Slot("creature", key="the-wrong", depends_on=("hulk",),
             brief="What is aboard the hulks. Subtle and cumulative, never "
                   "gore. Something wrong with a hull and eventually with a "
                   "person."),
        Slot("lore", key="open-question", depends_on=("powers",),
             brief="The open question the campaign is about. Do NOT resolve "
                   "it; leave the load-bearing part contested."),
        Slot("quest", key="hook", depends_on=("crew", "hulk", "run"),
             brief="The opening hook that puts the crew aboard a hulk in the "
                   "first hour of the first session."),
    ],
)

SEEDABLE = {"npc", "faction", "creature", "culture", "lore", "text", "item"}


def build_context(prior):
    parts = [TABLE_AGREEMENTS]
    if prior:
        parts.append("## ALREADY ESTABLISHED IN THIS WORLD\n"
                     "Reference these. Do not recreate them, do not rename "
                     "them, and do not contradict them.\n\n" + "\n\n".join(prior))
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", type=int, default=20260807)
    ap.add_argument("--out", default=PAGES,
                    help="pages directory; registry and index follow it")
    ap.add_argument("--free-depth", type=int, default=0,
                    help="0 = pitch phase: generate the contract, expand no "
                         "stubs, and let ghosts and canon carry the frontier.")
    args = ap.parse_args()

    forge = ProceduralForge()
    CONTRACT.validate(known_types=list(forge.generators))
    out_dir = os.path.abspath(args.out)
    suffix = os.path.basename(out_dir).replace("pages_", "")
    registry_out = os.path.join(HERE, f"registry_{suffix}.json")
    index_out = os.path.join(HERE, f"generation_index_{suffix}.json")
    os.makedirs(out_dir, exist_ok=True)

    registry = DNARegistry()
    assembler = ContextAssembler(registry)
    decoder = None if args.dry_run else DNADecoder()
    safety_block = SAFETY.render()
    conflicts = SAFETY.conflicts()

    order = CONTRACT.ordered()
    total = CONTRACT.total_entities()
    merged = SAFETY.merged()
    print(f"=== trial 5: {total} entities across {len(order)} slots ===")
    print(f"    order  : {' -> '.join(s.name for s in order)}")
    print(f"    safety : {len(merged.lines())} Lines, {len(merged.veils())} Veils")
    if conflicts:
        print(f"    CONTESTED (for the author, never the prompt): "
              f"{[c.text for c in conflicts]}")
    print()

    prior, made, index, counts = [], 0, [], {}
    for slot in order:
        for i in range(slot.count):
            made += 1
            kwargs = {"seed": args.seed + made} if slot.type in SEEDABLE else {}
            dna = forge.synthesize_element(
                slot.type, constraint_package=safety_block, **kwargs)
            label = slot.name + (f" {i+1}/{slot.count}" if slot.count > 1 else "")
            print(f"[{made}/{total}] {label:<16} ({slot.type})")
            if args.dry_run:
                continue

            # The naming rules, from whatever linguistic entity this run has
            # already generated. Omitting this was the trial 5 defect: the
            # linguistic slot produced 3,000 characters of naming conventions
            # with worked examples, and every one of the fourteen entities
            # generated after it got none of them -- the page went into `prior`
            # truncated to its first paragraph, which is phonetics, and phonetics
            # name nothing. PROJECT_STATE §5 records this exact failure once
            # already: the rules must ride their own uncapped field, not the
            # world frame. ContextAssembler reads the anchor from the REGISTRY,
            # so it finds an entity made moments ago in this same run.
            naming, naming_is_canon = assembler._naming_conventions([])
            # The roster is the other half of naming: "reference, don't
            # recreate". Without it the model has no list of names already
            # spent, so it reaches for whatever is nearest -- which in the
            # first test after wiring `naming` was one of the block's own
            # worked example names, reused verbatim despite the disclaimer.
            req = AssemblyRequest(element_type=slot.type, safety=safety_block)
            roster = assembler._build_roster(req, [])
            package = ContextPackage(safety=safety_block,
                                     naming=naming,
                                     naming_is_canon=naming_is_canon,
                                     roster=roster,
                                     world_frame=build_context(prior),
                                     directives=CONTRACT.brief_for(slot, i))
            t0 = time.time()
            page = decoder.decode_element(dna, context=package)
            elapsed = time.time() - t0

            rid = registry.register_element(
                element_type=slot.type, raw_dna=dna["dna"], decoded_profile=page,
                tags=["trial5", f"slot_{slot.name}"])
            registry.get_element(rid)["depth"] = 0
            fname = f"{suffix}_{made:02d}_{slot.name}" \
                    f"{'_' + str(i+1) if slot.count > 1 else ''}.md"
            with open(os.path.join(out_dir, fname), "w",
                      encoding="utf-8", newline="\n") as fh:
                fh.write(page)
            prior.append(f"### [{slot.type}] {fname}\n"
                         + page.strip().split("\n\n")[0][:600])
            counts[slot.name] = counts.get(slot.name, 0) + 1
            index.append({"n": made, "slot": slot.name, "type": slot.type,
                          "file": fname, "id": rid, "chars": len(page),
                          "seconds": round(elapsed, 1)})
            print(f"          -> {fname}  ({len(page)} chars, {elapsed:.1f}s)")

    if args.dry_run:
        print("\nDry run complete. No model calls made.")
        return

    # ── the frontier, which no earlier trial advanced ──────────────────────
    manager = ExpansionManager(registry, forge, None, decoder,
                               policy=ExpansionPolicy(free_depth=args.free_depth),
                               composer=CanonComposer(registry),
                               ghosts=GhostRegistry())
    for rid in [i for i in registry._records]:
        rec = registry.get_element(rid)
        if "stub" not in (rec.get("tags") or []):
            manager.parse_and_register_stubs(rid, rec["phenotype"])

    stubs = [i for i, r in registry._records.items()
             if "stub" in (r.get("tags") or [])]
    print(f"\n=== frontier: {len(stubs)} stubs implied "
          f"(branching {measure_branching(registry):.2f}) ===")
    plan = manager.policy.plan(registry, manager.composer, stubs, manager.ghosts)
    print(f"    plan: {summarise(plan)}")
    results = manager.advance_frontier(stubs)
    print(f"    done: " + ", ".join(f"{k} {len(v)}" for k, v in results.items()))

    registry.save_to_json(registry_out)
    with open(index_out, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)
    print(f"\ncontract satisfied: {CONTRACT.is_satisfied(counts)}")


if __name__ == "__main__":
    enable_safe_stdout()
    main()
