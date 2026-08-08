import re
from typing import List, Dict, Any
from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.forge import ProceduralForge
from layer5_dna_substrate.inheritance import InheritanceEngine
from layer5_dna_substrate.expansion_policy import (
    COMPOSE, DEFER, EXPAND, GHOST, ExpansionPolicy, order_cheapest_first,
    stub_depth)
from layer5_dna_substrate.phenotype_meta import parse_phenotype_tail, VALID_STUB_TYPES

# Comprehensive type map for fuzzy matching of loosely-typed stub mentions
FUZZY_TYPE_MAP = {
    "npc": "npc", "person": "npc", "character": "npc", "individual": "npc", "librarian": "npc",
    "archivist": "npc", "confidante": "npc", "scribe": "npc", "guardian": "npc", "noble": "npc",
    # A bishop is a person. Named here, early, because "bishop" contains "shop"
    # and the establishment block below would otherwise make one into a store.
    "bishop": "npc", "priest": "npc",
    # "realm" used to resolve here. A realm has its own generator, decoder and
    # Atlas subfolder, so routing it to location gave it the wrong prompt as
    # well as the wrong shelf — the one mis-route in this map rather than a
    # plain omission. "temple" stays a location deliberately: an establishment
    # is a room with a proprietor, and re-routing a key that already resolves
    # would split the corpus. Retype deliberately instead (retype_element).
    "location": "location", "place": "location", "structure": "location",
    "area": "location", "void": "location", "pass": "location", "peaks": "location", "temple": "location",
    "faction": "faction", "organization": "faction", "group": "faction", "guild": "faction",
    "order": "faction", "family": "faction", "civilization": "faction", "lineage": "faction", "council": "faction",
    "item": "item", "relic": "item", "artifact": "item", "object": "item", "scroll": "item", "book": "item",
    "chronicle": "chronicle", "event": "chronicle", "history": "chronicle", "concept": "chronicle",
    "phenomenon": "chronicle", "veil": "chronicle", "era": "chronicle", "epoch": "chronicle",
    # What the world believes, as opposed to what happened to it.
    "lore": "lore", "doctrine": "lore", "myth": "lore", "legend": "lore", "scripture": "lore",
    "prophecy": "lore", "creed": "lore", "tenet": "lore", "gospel": "lore",
    # Peoples and societies, as opposed to institutions with goals.
    # "community" was written by a decoder during the Session 0 trial and fell
    # through to the npc default, because nothing claimed it.
    "culture": "culture", "people": "culture", "peoples": "culture", "tribe": "culture",
    "society": "culture", "community": "culture", "commune": "culture",
    # Living (or unliving) things that are not people.
    "creature": "creature", "beast": "creature", "monster": "creature", "fauna": "creature",
    "swarm": "creature", "predator": "creature", "vermin": "creature",
    # Play content: an obstacle or an adventure, not a thing in the world.
    "trap": "trap", "snare": "trap", "hazard": "trap", "pitfall": "trap",
    "deadfall": "trap", "ward": "trap",
    "quest": "quest", "adventure": "quest", "mission": "quest", "job": "quest",
    "contract": "quest", "errand": "quest",
    # In-world documents: the object carrying a claim, as opposed to the claim
    # (lore) or a mere possession (item). Deliberately placed after item and
    # lore, because matching is by substring in insertion order: "scroll" and
    # "book" already resolve to item and "scripture" to lore, and re-routing
    # those would split existing entities from new ones. Retype deliberately
    # instead (DNARegistry.retype_element).
    # "logbook" was listed here and could never fire: "book" is an earlier key,
    # so every label containing it resolved to item first. Removing the dead
    # key changes no behaviour and stops the map claiming a route it lacks.
    # A logbook is therefore an item, which is the same accepted tradeoff as
    # "book" and "scroll" — retype deliberately if that ever needs to change.
    "text": "text", "document": "text", "codex": "text", "tome": "text",
    "manual": "text", "ledger": "text", "letter": "text", "treatise": "text",
    "journal": "text", "diary": "text", "hymnal": "text",
    "inscription": "text",

    # ── Six types that had a generator, a decoder and a folder but no way in ──
    #
    # Everything below is appended rather than interleaved, and that placement
    # is the safety argument: matching is by substring in insertion order, so a
    # key added at the end can only capture labels that previously fell through
    # to the "npc" default. No label that already resolved can be hijacked.
    #
    # Somewhere you can walk into, with a door and someone behind the counter.
    # "shop" is a substring of "bishop", who is a person; the npc block above
    # names bishops explicitly so the earlier match wins. "forge" and "stall"
    # were considered and dropped — they are substrings of "forgery" and
    # "install" and buy nothing that "smithy" and "market" do not.
    "establishment": "establishment", "tavern": "establishment",
    "inn": "establishment", "alehouse": "establishment", "shop": "establishment",
    "store": "establishment", "smithy": "establishment",
    "apothecary": "establishment", "market": "establishment",
    "shrine": "establishment", "parlour": "establishment",
    # A site you travel to and go inside: the adventure locale, larger than a
    # room and smaller than a settlement.
    "regional_poi": "regional_poi", "point of interest": "regional_poi",
    "dungeon": "regional_poi", "ruin": "regional_poi", "tower": "regional_poi",
    "lair": "regional_poi", "landmark": "regional_poi", "monument": "regional_poi",
    "anomaly": "regional_poi", "crypt": "regional_poi", "barrow": "regional_poi",
    # Settlement had only its own name; the words a decoder actually writes for
    # one did not resolve, so a village became a villager.
    # Bare "port" is a substring of "portal", which is not a town.
    "city": "settlement", "town": "settlement", "village": "settlement",
    "hamlet": "settlement", "outpost": "settlement", "metropolis": "settlement",
    "port-city": "settlement", "harbour": "settlement", "harbor": "settlement",
    # Polities above the settlement, restored from the location mis-route.
    # Bare "nation" is a substring of "abomination", which is a creature.
    "realm": "realm", "kingdom": "realm", "empire": "realm",
    "principality": "realm", "dominion": "realm",
    # An institution of state, as distinct from a faction with its own agenda.
    "agency": "agency", "bureau": "agency", "ministry": "agency",
    "constabulary": "agency", "authority": "agency", "department": "agency",
    # A route rather than a place: what the journey along it costs.
    "travel": "travel", "route": "travel", "journey": "travel",
    "voyage": "travel", "expedition": "travel",
    # World-scale singular features.
    "wonder": "wonder", "marvel": "wonder",
    # "cult" MUST stay below the culture block. Placed above it, the substring
    # test would read "culture" as containing "cult" and route every people in
    # the world to faction.
    "cult": "faction", "syndicate": "faction", "cabal": "faction",
}


def _resolve_stub_type(e_type_raw: str) -> str:
    """Maps a raw type mention to a canonical element type (default: npc)."""
    e_type_raw = (e_type_raw or "").lower().strip()
    if e_type_raw in VALID_STUB_TYPES:
        return e_type_raw
    for key, val in FUZZY_TYPE_MAP.items():
        if key in e_type_raw:
            return val
    return "npc"


class ExpansionManager:
    """
    Orchestrates the 'Seed-to-Bible' workflow.
    Parses decoded phenotypes for 'Unmade Connections' (Stubs) and
    manages their expansion into full DNA-backed entities.
    """
    def __init__(self, registry: DNARegistry, forge: ProceduralForge, inheritance: InheritanceEngine, decoder,
                 assembler=None, policy=None, composer=None, ghosts=None):
        self.registry = registry
        self.forge = forge
        self.inheritance = inheritance
        self.decoder = decoder
        # Optional ContextAssembler; when present, it replaces the legacy
        # inheritance-constraints + notes-dict context path in expand_stub.
        self.assembler = assembler
        # Optional depth policy and canon composer. Both default to None so
        # every existing caller keeps unbounded expand_stub behaviour: the
        # brake is opt-in via advance_stub, never applied behind a caller's
        # back. A policy that silently refused to expand would look like a
        # generation failure rather than a budget decision.
        self.policy = policy
        self.composer = composer
        self.ghosts = ghosts

    def _composer(self):
        """Lazily build a CanonComposer if one was not supplied."""
        if self.composer is None:
            from layer5_dna_substrate.canon_composer import CanonComposer
            self.composer = CanonComposer(self.registry)
        return self.composer

    def _ghosts(self):
        """Lazily build a GhostRegistry if one was not supplied."""
        if self.ghosts is None:
            from layer5_dna_substrate.ghost_registry import GhostRegistry
            self.ghosts = GhostRegistry()
        return self.ghosts

    def _locale_for(self, entity_id: str):
        """The spatial entity an expansion should be grounded in, if any."""
        from layer5_dna_substrate.context_assembler import resolve_locale
        return resolve_locale(self.registry, entity_id)

    def _extract_name(self, phenotype: str) -> str:
        """Attempts to extract the entity name from the phenotype markdown."""
        # Clean phenotype of headers and sections we don't want to name from
        clean_phenotype = re.sub(r"###.*Unmade Connections.*", "", phenotype, flags=re.IGNORECASE | re.DOTALL)
        clean_phenotype = re.sub(r"###.*DNA Relations.*", "", clean_phenotype, flags=re.IGNORECASE | re.DOTALL)
        clean_phenotype = re.sub(r"###.*Behavioral Model.*", "", clean_phenotype, flags=re.IGNORECASE | re.DOTALL)
        clean_phenotype = re.sub(r"###.*Gamemaster.*", "", clean_phenotype, flags=re.IGNORECASE | re.DOTALL)
        
        name_patterns = [
            # Was \\[? — an escaped backslash followed by a class-opening "[",
            # which swallowed the capture group's "(" and made the trailing ")"
            # unbalanced, so this raised PatternError for every input. That made
            # the whole name fallback dead: expansion crashed instead of falling
            # back whenever a decoder omitted the structured tail.
            r"###\s+\*\*\[?([^\]\*\n]*)\]?\*\*",              # ### **[Name]** or ### **Name**
            r"###\s+([^#\n]*)",                             # ### Name
            r"##\s+(.*)",                                   # ## Name
            r"Name:\*\*\s+\*?([^\*\n]*)\*?$",                # **Name:** *Name* (at line end)
            r"\*\*Name:\*\*\s+([^\n]*)$",                   # **Name:** Name (at line end)
            r"Role:\s+([^\n]*)$"                            # Role: Name (fallback)
        ]
        
        exclude_list = [
            "npc name", "faction name & symbol", "location name", "item name", 
            "settlement name", "world name", "region name", "unmade connections", 
            "dna stubs", "dna relations", "phenotype", "narrative essence", "role",
            "profile", "structured output format", "decoding instructions"
        ]

        for pattern in name_patterns:
            match = re.search(pattern, clean_phenotype, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = re.sub(r"^\d+\.\s+", "", name)
                name = name.replace("[", "").replace("]", "").replace("*", "")
                if name.lower() not in exclude_list and len(name) > 1:
                    return name
        return None

    def _register_stub(self, source_id: str, e_type_raw: str, e_name: str, e_desc: str) -> str:
        """
        Registers a single stub (or links to an existing entity of the same name).
        Returns the stub ID, or None when the mention resolved to an existing entity.
        """
        e_name = e_name.strip().replace("*", "").replace("[", "").replace("]", "").rstrip(":").strip()
        e_type = _resolve_stub_type(e_type_raw)

        # Dedupe: if an entity with this name already exists, link instead of re-creating it
        existing = self.registry.find_by_name(e_name)
        if existing:
            self.registry.link_elements(source_id, existing["id"], "peer", f"mentions_{e_name}")
            return None

        stub_id = self.registry.register_element(
            element_type=e_type,
            raw_dna="STUB",
            decoded_profile=f"[STUB] {e_name}: {e_desc}",
            name=e_name,
            gist=e_desc,
            tags=["stub", f"from_{source_id}", e_name.replace(" ", "_").lower()]
        )
        self.registry._records[stub_id]["stub_metadata"] = {"name": e_name, "description": e_desc, "source_id": source_id}
        # Hops from a seed, recorded at registration rather than derived later.
        # ExpansionPolicy needs it to decide invent-versus-compose, and walking
        # the source chain on every decision is both slower and fragile once a
        # parent has been retyped or merged.
        self.registry._records[stub_id]["depth"] = stub_depth(
            self.registry, source_id) + 1 if source_id else 1
        self.registry.link_elements(source_id, stub_id, "peer", f"mentions_{e_name}")
        return stub_id

    def parse_and_register_stubs(self, source_id: str, phenotype: str) -> List[str]:
        """
        Registers the phenotype's stubs ('Unmade Connections') in the registry.

        Primary path: the structured YAML tail emitted by every decoder.
        Fallback: legacy regex parsing of the prose section, for phenotypes
        generated before the tail existed or when the tail is malformed.
        """
        # Structured path
        meta = parse_phenotype_tail(phenotype)
        if meta and meta["stubs"]:
            stub_ids = []
            for stub in meta["stubs"]:
                stub_id = self._register_stub(source_id, stub["type"], stub["name"], stub["gist"])
                if stub_id:
                    stub_ids.append(stub_id)
            return stub_ids

        # Legacy regex path
        stub_ids = []
        section_pattern = r"###[^\n]*Unmade Connections[^\n]*(.*?)(?:---|Let me know if|$)"
        section_match = re.search(section_pattern, phenotype, re.DOTALL | re.IGNORECASE)

        if not section_match:
            return []

        section_text = section_match.group(1)

        # Multi-stage regex matching
        lines = section_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line.startswith("*") and not line.startswith("-"):
                continue
                
            e_type_raw, e_name, e_desc = None, None, None
            
            # Pattern 1: * **[Type] Name:** Description (Brackets)
            m1 = re.match(r"(?:\*|-)\s*(?:\*\*)?\s*\[(.*?)\]\s+(.*?)(?::|\*\*)\s+(.*)", line)
            if m1:
                e_type_raw, e_name, e_desc = m1.group(1), m1.group(2), m1.group(3)
            else:
                # Pattern 2: * **Type: Name:** Description (Colons)
                m2 = re.match(r"(?:\*|-)\s*(?:\*\*)?\s*(.*?):\s+(.*?)(?::|\*\*)\s+(.*)", line)
                if m2:
                    e_type_raw, e_name, e_desc = m2.group(1), m2.group(2), m2.group(3)
                else:
                    # Pattern 3: * **Type:** Description (No Name)
                    m3 = re.match(r"(?:\*|-)\s*(?:\*\*)?\s*(.*?)(?::|\*\*)\s+(.*)", line)
                    if m3:
                        e_type_raw, e_desc = m3.group(1), m3.group(2)
                        # Extract name from first 3-4 words if it looks like a title
                        words = e_desc.split()
                        e_name = " ".join(words[:min(len(words), 3)]).replace(".", "").replace(",", "").strip()
                    else:
                        continue

            if e_name and e_desc:
                e_type_raw = e_type_raw.lower().strip().replace("[", "").replace("]", "").replace("*", "")
                stub_id = self._register_stub(source_id, e_type_raw, e_name, e_desc)
                if stub_id:
                    stub_ids.append(stub_id)

        return stub_ids

    def advance_stub(self, stub_id: str, extra_context: str = "",
                     **gen_kwargs) -> dict:
        """
        Advance a stub as far as the policy allows, and no further.

        The bounded counterpart to expand_stub. Returns
        {"decision", "stub_id", "phenotype"} where phenotype is None for a
        DEFER -- which is an outcome, not an error. A deferred stub costs one
        registry row, cannot leak into a prompt, and is still there when
        something actually needs it.

        With no policy set this is just expand_stub, so wiring it in changes
        nothing until a budget is chosen.
        """
        record = self.registry.get_element(stub_id)
        if not record or "stub" not in (record.get("tags") or []):
            raise ValueError(f"ID {stub_id} is not a valid expansion stub.")

        if self.policy is None:
            return {"decision": EXPAND, "stub_id": stub_id,
                    "phenotype": self.expand_stub(stub_id, extra_context,
                                                  **gen_kwargs)}

        composer, ghosts = self._composer(), self._ghosts()
        decision = self.policy.plan(
            self.registry, composer, [stub_id], ghosts)[stub_id]

        if decision == EXPAND:
            return {"decision": EXPAND, "stub_id": stub_id,
                    "phenotype": self.expand_stub(stub_id, extra_context,
                                                  **gen_kwargs)}
        if decision == COMPOSE:
            # No DNA and no model call: the page is assembled from canon that
            # already describes this entity. Falls through if canon turns out
            # thinner than assess() judged, so a compose can never quietly
            # become an invention.
            if composer.compose_into_record(stub_id):
                return {"decision": COMPOSE, "stub_id": stub_id,
                        "phenotype": self.registry.get_element(stub_id)["phenotype"]}
            decision = (GHOST if self.policy.use_ghosts and ghosts.can_ghost(
                record.get("type") or "") else DEFER)

        if decision == GHOST:
            # Nothing about this entity; only what its type guarantees. Stays
            # tagged `stub`, so it is still owed a page, still excluded from
            # retrieval, and still cannot be composed from.
            if ghosts.ghost_into_record(self.registry, stub_id):
                return {"decision": GHOST, "stub_id": stub_id,
                        "phenotype": self.registry.get_element(stub_id)["phenotype"]}

        return {"decision": DEFER, "stub_id": stub_id, "phenotype": None}

    def advance_frontier(self, stub_ids=None, extra_context: str = "") -> dict:
        """
        Advance every pending stub under the policy, cheapest first.

        Composes before it expands, deliberately. Every composed page is canon
        the next expansion can see, so doing the free work first makes the paid
        work better informed -- and if a budget runs out mid-run, what was
        skipped is the expensive half.
        """
        if stub_ids is None:
            stub_ids = [i for i, r in self.registry._records.items()
                        if "stub" in (r.get("tags") or [])]
        plan = (self.policy.plan(self.registry, self._composer(), stub_ids,
                                 self._ghosts())
                if self.policy else {i: EXPAND for i in stub_ids})

        results = {EXPAND: [], COMPOSE: [], GHOST: [], DEFER: []}
        for stub_id in order_cheapest_first(plan):
            outcome = self.advance_stub(stub_id, extra_context)
            results[outcome["decision"]].append(stub_id)
        return results

    def expand_stub(self, stub_id: str, extra_context: str = "", **gen_kwargs) -> str:
        """
        Takes a Stub ID, generates its DNA, decodes it with context from its parent/source,
        and updates the registry record.

        gen_kwargs are forwarded to the generator, for the types that accept a
        seed and axis pins. This matters when canon already fixes something about
        the entity: rolling those axes at random produces DNA that contradicts
        the established world, and while the decoder is told canon outranks the
        DNA, it is better not to hand it a conflict at all. Pin what canon
        states and leave the rest to vary.
        """
        stub_record = self.registry.get_element(stub_id)
        if not stub_record or "stub" not in stub_record.get("tags", []):
            raise ValueError(f"ID {stub_id} is not a valid expansion stub.")

        metadata = stub_record.get("stub_metadata", {})
        source_id = metadata.get("source_id")
        source_record = self.registry.get_element(source_id)
        source_name = source_record.get("name", "the source") if source_record else "the source"
        source_type = source_record.get("type", "entity") if source_record else "entity"
        
        e_type = stub_record["type"]
        e_name = metadata.get("name")

        # 1. The "Imprint": what the source entity said this stub is
        imprint = f"The entity being generated is named '{e_name}'. "
        imprint += f"It was first mentioned by {source_name} ({source_type}) with the following description: '{metadata.get('description')}'. "
        imprint += f"Use this description as the primary guidance for its role, personality, and relationship to {source_name}. "

        # 2. Build context: assembler (layered world-fit package) when present,
        #    otherwise the legacy inheritance-constraints path
        if self.assembler:
            from layer5_dna_substrate.context_assembler import AssemblyRequest
            package = self.assembler.assemble(AssemblyRequest(
                element_type=e_type,
                anchor_id=source_id,
                locale_id=self._locale_for(source_id) if source_id else None,
                imprint=imprint,
                directives=extra_context,
            ))
            constraints = ""  # lineage lives in the package; avoid double injection
            context = package
        else:
            parent_ids = [source_id] if source_id else []
            # Legacy linguistic anchor for phonetic consistency
            linguistic_elements = [id for id, rec in self.registry._records.items() if rec.get("type") == "linguistic"]
            if linguistic_elements:
                parent_ids.append(linguistic_elements[0])
            constraints = self.inheritance.compile_constraints(parent_ids)
            specific_context = imprint
            if extra_context:
                specific_context += f"\n\nSpecialist Guidance: {extra_context}"
            context = {"additional_notes": specific_context}

        # 3. Synthesize DNA
        dna_data = self.forge.synthesize_element(
            e_type, constraint_package=constraints, **gen_kwargs)

        # 4. Decode with full context
        full_phenotype = self.decoder.decode_element(dna_data, context=context)
        
        # 5. Extract structured metadata (tail-first, regex fallback for the name)
        meta = parse_phenotype_tail(full_phenotype) or {}
        actual_name = meta.get("name") or self._extract_name(full_phenotype) or e_name

        # 6. Update Registry
        stub_record["dna"] = dna_data["dna"]
        stub_record["phenotype"] = full_phenotype
        stub_record["name"] = actual_name
        stub_record["gist"] = meta.get("gist") or stub_record.get("gist")
        stub_record["summary"] = meta.get("summary")
        if "stub" in stub_record["tags"]:
            stub_record["tags"].remove("stub")
        stub_record["tags"].append("expanded")
        
        # 6. Recursive parsing: Does the NEW entity have its own stubs?
        new_stubs = self.parse_and_register_stubs(stub_id, full_phenotype)
        
        return full_phenotype
