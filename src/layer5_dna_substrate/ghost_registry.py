"""
Ghosts: what an unmade entity is guaranteed to have, purely by being its type.

The architecture report proposed a pre-seeded "Ghost Registry" of generic
taxonomies to absorb implied stubs, and gave the mechanism as anchoring "the
vector embedding deduplication registry". There is no such registry.
`DNARegistry.find_by_name` is normalised string matching -- case-insensitive,
ignoring a leading article -- and `ContinuityArchivist.retrieve_context`
returns a hardcoded string above the comment "Placeholder for Semantic Search".
A ghost called *local tavern* would never match a stub called *The Broken
Wheel*, because decoders emit proper nouns.

So the routing is by TYPE. That also makes the ghost's real value clear, since
it is not deduplication: a stub already dedupes by name. A ghost is worth having
because it is **usable at the table without a model call**. A stub is a name and
one line. A ghost is a name, that line, and the affordances its type guarantees
-- a tavern has a door, a proprietor, and something served; a route has two ends
and a way to go wrong. An AI GM whose player walks into an unexpanded tavern has
something structured to run rather than a one-liner.

What a ghost must never do is invent world content. Every shape below describes
what the TYPE is, in the project's own words where those exist, and everything
specific to this world is listed as open rather than answered. That is the
CLAUDE.md rule about undefined vocabularies applied to a different surface: a
plausible invention is indistinguishable from the real thing and poisons
whatever is generated next.

A ghost therefore stays a stub. It keeps the `stub` tag, so:
  - `context_assembler.py:314` still excludes it from retrieval, and it cannot
    leak into a prompt as though it were established;
  - `CanonComposer` still cannot compose from it, since that reads only
    `canonized` records -- composing from a ghost would be inventing from an
    invention;
  - `StubIndex` still lists it as owed a real page.
It gains a body, a `ghost` tag, and nothing else.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

GHOST_DNA = "GHOST"


@dataclass(frozen=True)
class GhostShape:
    """What being this type guarantees, and what it leaves open."""

    what_it_is: str
    guaranteed: List[str]     # true of every instance, by definition of the type
    open_questions: List[str]  # what only generation or the author can settle


# Definitions follow the project's own, where it has stated them: the
# establishment line is quoted from decoders/establishment.md, and the
# culture/lore/text/creature distinctions from ObsidianSync.TYPE_FOLDER_MAP.
SHAPES: Dict[str, GhostShape] = {
    "establishment": GhostShape(
        "A room you can walk into — the smallest unit of place in the system. "
        "Somewhere with a door, a proprietor and a reason to come back.",
        ["A way in, and someone behind the counter.",
         "Something served, sold, or offered.",
         "Regulars who are there most days.",
         "A reason it survives where it stands."],
        ["Who the proprietor is and what they want.",
         "What is actually on offer, and at what price.",
         "Who else is usually in the room.",
         "What the place is hiding, if anything."]),
    "npc": GhostShape(
        "A person, with somewhere to be and a reason to be there.",
        ["A name, and a way of speaking.",
         "Somewhere they are usually found.",
         "Something they want.",
         "Something they will not do."],
        ["Their history and who they are loyal to.",
         "What they want that they will not say.",
         "How they behave under pressure."]),
    "settlement": GhostShape(
        "A place people live, large enough to have its own affairs.",
        ["Somewhere to arrive, and somewhere to stay.",
         "Someone who speaks for it.",
         "Work that keeps it alive.",
         "A reason it is where it is."],
        ["Its size, its politics, and who really decides.",
         "What it trades and what it lacks.",
         "What it is afraid of."]),
    "location": GhostShape(
        "A place with edges, that can be arrived at and left.",
        ["A way in and a way out.",
         "Something that makes it worth naming."],
        ["What is there, and who else knows about it.",
         "Why it matters to anyone."]),
    "regional_poi": GhostShape(
        "A site you travel to and go into: larger than a room, smaller than a "
        "settlement.",
        ["A way in, and a reason the way in is not simple.",
         "Something inside worth the trip.",
         "A reason locals have an opinion about it."],
        ["What made it, and when.",
         "What lives there now.",
         "What it is hiding, and what that costs to reach."]),
    "faction": GhostShape(
        "An institution with goals, as distinct from a people.",
        ["Something it wants that it does not have.",
         "Someone who speaks for it.",
         "A way it recognises its own.",
         "Someone it is in the way of."],
        ["Its real aim, where that differs from its stated one.",
         "Its reach, and where that reach stops.",
         "What would split it."]),
    "culture": GhostShape(
        "A people and a society, as distinct from an institution with goals.",
        ["A way of living, and a way of eating.",
         "Something held sacred and something forbidden.",
         "A way of naming their own."],
        ["Their history and how they tell it.",
         "How they treat outsiders.",
         "What is straining between generations."]),
    "creature": GhostShape(
        "Ecology and threat: a living thing that is not a people.",
        ["Somewhere it lives and something it eats.",
         "A reason to avoid it, or a reason it avoids you.",
         "Something that kills it."],
        ["What it actually does when it meets someone.",
         "Whether it is rare or everywhere.",
         "Whether anything intends it."]),
    "item": GhostShape(
        "An object that can be carried, owned, lost and wanted.",
        ["A shape, a material, and a condition.",
         "Someone who made it or someone who wants it."],
        ["What it does, and what that costs.",
         "Who owned it before.",
         "Why it is worth taking."]),
    "text": GhostShape(
        "The document carrying a claim, as distinct from the claim itself.",
        ["A physical form and a state of repair.",
         "Someone who wrote it and someone who keeps it."],
        ["What it says, and whether that is true.",
         "Who wants it destroyed."]),
    "lore": GhostShape(
        "What the world believes, as distinct from what happened.",
        ["Someone who holds it and someone who disputes it.",
         "A reason it is believed."],
        ["What is actually true, and what must stay open.",
         "What it costs to doubt it aloud."]),
    "travel": GhostShape(
        "A route: what the journey along it costs.",
        ["Two ends, and time between them.",
         "A way it goes wrong.",
         "Somewhere to stop."],
        ["How long it really takes and in what season.",
         "Who else uses it.",
         "What is worth seeing on the way."]),
    "quest": GhostShape(
        "Play content: something that happens at the table, not a world fact.",
        ["Someone who wants it done.",
         "A reason it is not done already.",
         "Something gained by doing it."],
        ["What the asker is not saying.",
         "What goes wrong partway.",
         "Who else wants it to fail."]),
    "trap": GhostShape(
        "An obstacle: play content rather than a world fact.",
        ["A trigger and a consequence.",
         "A way to notice it, and a way past it."],
        ["Who built it and what they were protecting.",
         "Whether it still works."]),
    "agency": GhostShape(
        "An institution of state, as distinct from a faction with its own agenda.",
        ["A remit, and someone it answers to.",
         "A way it makes itself felt."],
        ["How competent it actually is.",
         "Where its remit is ignored."]),
    "chronicle": GhostShape(
        "Something that happened, as distinct from what is believed about it.",
        ["A time it happened and somewhere it happened.",
         "Someone it happened to."],
        ["What it changed.",
         "Who disagrees about it."]),
}

# Types deliberately left without a shape, so the omission reads as a decision
# rather than an oversight:
#
#   linguistic  A language's whole value is its specifics -- the phonetics, the
#               taboos, the roster of names already in use. A generic placeholder
#               would feed the naming pipe nothing while looking like an answer,
#               and PROJECT_STATE §5 records that the naming pipe is the single
#               easiest thing here to break silently. Defer instead.
#   world       Nothing above it can imply one, and a placeholder world is not a
#               thing a table can use.
#   realm, region, wonder, linguistic and the rest simply have no shape yet; add
#               one when a real frontier turns up wanting it, not before.
NO_GHOST_BY_DESIGN = {"linguistic", "world"}


class GhostRegistry:
    """Type-level placeholder pages, assembled with no DNA and no model call."""

    def __init__(self, shapes: Optional[Dict[str, GhostShape]] = None):
        self.shapes = shapes if shapes is not None else SHAPES

    def can_ghost(self, element_type: str) -> bool:
        return element_type in self.shapes

    def ghost(self, stub: dict) -> Optional[str]:
        """
        A page body for an unmade entity, or None when the type has no shape.

        Everything specific to this world appears under Open, never answered.
        The header says outright that nothing here was authored, because a
        reader who mistakes a ghost for content has been handed an invention.
        """
        shape = self.shapes.get(stub.get("type") or "")
        if shape is None:
            return None
        name = (stub.get("name") or "").strip() or "Unnamed"
        gist = ((stub.get("gist") or "")
                or (stub.get("stub_metadata") or {}).get("description") or "").strip()

        lines = [
            f"### {name}",
            "",
            "> [!warning] Placeholder — not authored, not canon",
            "> Nothing here was written about *this* entity. It records what "
            "being "
            f"{'an' if (stub.get('type') or 'x')[0] in 'aeiou' else 'a'} "
            f"`{stub.get('type')}` guarantees, so the entity can be referred to "
            "and used before anyone has made it. Expand it to replace this "
            "page. Do not cite it as evidence for anything.",
            "",
            f"*{shape.what_it_is}*",
            "",
        ]
        if gist:
            lines += ["### What the world has said so far", "",
                      f"- {gist}", ""]
        lines += ["### What it has by being what it is", ""]
        lines += [f"- {g}" for g in shape.guaranteed]
        lines += ["", "### Open — nothing below has been decided", ""]
        lines += [f"- {q}" for q in shape.open_questions]
        lines += ["",
                  "*Anything a scene needs beyond the list above should be "
                  "invented at the table and written back, or the entity should "
                  "be expanded properly first.*", ""]
        return "\n".join(lines)

    def ghost_into_record(self, registry, stub_id: str) -> bool:
        """
        Give a stub a body in place. Returns False when the type has no shape.

        The record KEEPS its `stub` tag deliberately: a ghost is still owed a
        real page, must stay out of retrieval, and must never be composed from.
        """
        record = registry.get_element(stub_id)
        if not record:
            return False
        body = self.ghost(record)
        if body is None:
            return False
        record["phenotype"] = body
        record["dna"] = GHOST_DNA
        tags = list(record.get("tags") or [])
        if "ghost" not in tags:
            tags.append("ghost")
        record["tags"] = tags
        record["audit"] = "ghost"
        return True
