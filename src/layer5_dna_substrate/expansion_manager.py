import re
from typing import List, Dict, Any
from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.forge import ProceduralForge
from layer5_dna_substrate.inheritance import InheritanceEngine
from layer5_dna_substrate.phenotype_meta import parse_phenotype_tail, VALID_STUB_TYPES

# Comprehensive type map for fuzzy matching of loosely-typed stub mentions
FUZZY_TYPE_MAP = {
    "npc": "npc", "person": "npc", "character": "npc", "individual": "npc", "librarian": "npc",
    "archivist": "npc", "confidante": "npc", "scribe": "npc", "guardian": "npc", "noble": "npc",
    "location": "location", "place": "location", "structure": "location", "realm": "location",
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
    "culture": "culture", "people": "culture", "peoples": "culture", "tribe": "culture",
    "society": "culture",
    # Living (or unliving) things that are not people.
    "creature": "creature", "beast": "creature", "monster": "creature", "fauna": "creature",
    "swarm": "creature", "predator": "creature", "vermin": "creature",
    # In-world documents: the object carrying a claim, as opposed to the claim
    # (lore) or a mere possession (item). Deliberately last, because matching is
    # by substring in insertion order: "scroll" and "book" already resolve to
    # item and "scripture" to lore, and re-routing those would move existing
    # entities. Retype deliberately instead (DNARegistry.retype_element).
    "text": "text", "document": "text", "codex": "text", "tome": "text",
    "manual": "text", "ledger": "text", "letter": "text", "treatise": "text",
    "journal": "text", "diary": "text", "logbook": "text", "hymnal": "text",
    "inscription": "text",
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
                 assembler=None):
        self.registry = registry
        self.forge = forge
        self.inheritance = inheritance
        self.decoder = decoder
        # Optional ContextAssembler; when present, it replaces the legacy
        # inheritance-constraints + notes-dict context path in expand_stub.
        self.assembler = assembler

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
            r"###\s+\*\*\\[?([^\\]\*\n]*)\\]?\*\*",           # ### **[Name]** or ### **Name**
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

    def expand_stub(self, stub_id: str, extra_context: str = "") -> str:
        """
        Takes a Stub ID, generates its DNA, decodes it with context from its parent/source,
        and updates the registry record.
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
        dna_data = self.forge.synthesize_element(e_type, constraint_package=constraints)

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
