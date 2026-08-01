import os
import re
from datetime import date
from typing import Dict, Any, List
from .registry import DNARegistry
from .phenotype_meta import strip_phenotype_tail, strip_decoder_artifacts

class ObsidianSync:
    """
    Synchronizes the DNA Registry state with an Obsidian world-bible vault.

    The vault's canon model governs the sync:
      - every synced note carries `status: draft` — the pipeline proposes,
        only the author promotes to canon
      - existing pages whose frontmatter says `canon` or `deprecated` are
        NEVER overwritten
      - stub records are not synced (they aren't decoded entities yet)
    """

    # Folders follow the world-bible vault taxonomy (see the vault's CLAUDE.md);
    # unknown types land in Drafts for the author to sort.
    TYPE_FOLDER_MAP = {
        "npc": "Characters",
        # Atlas is subdivided by scale. Eight spatial types shared one folder,
        # which put a tavern and a continent side by side; each now has its own
        # room while still living under the Atlas.
        "realm": "Atlas/Realms",
        "region": "Atlas/Regions",
        "settlement": "Atlas/Settlements",
        "location": "Atlas/Locations",
        "regional_poi": "Atlas/Points of Interest",
        "establishment": "Atlas/Establishments",
        "wonder": "Atlas/Wonders",
        "travel": "Atlas/Routes",
        "item": "Artifacts",
        "faction": "Factions",
        "agency": "Factions",
        "world": "Cosmology",
        "chronicle": "History",
        # Languages belong with the peoples who speak them.
        "linguistic": "Cultures",
        # Peoples and societies, as distinct from institutions with goals (faction).
        "culture": "Cultures",
        # What the world BELIEVES, as distinct from what happened (chronicle):
        # myths, doctrines, prophecies. The vault's CLAUDE.md puts in-world texts
        # here too, so `text` shares the folder — but they are separate types: a
        # lore page is a claim, a text page is the document carrying it.
        "lore": "Lore",
        "text": "Lore",
        # Creatures and monsters. Sapient peoples belong in culture; a creature
        # page is ecology and threat.
        "creature": "Bestiary",
        # Play content, not world facts. Every other folder answers "what is true
        # about the world"; these answer "what happens at the table". Quest sat in
        # Drafts, which the vault defines as a holding pen for the not-yet-canon,
        # and trap was absent from this map entirely — so it fell through to the
        # same place while its stubs were being registered as npc.
        "trap": "Encounters/Traps",
        "quest": "Encounters/Quests",
    }
    DEFAULT_FOLDER = "Drafts"
    PROTECTED_STATUSES = {"canon", "deprecated"}

    _STATUS_RE = re.compile(r"^---\s*\n.*?^status:\s*(\S+).*?\n---\s*\n", re.DOTALL | re.MULTILINE)
    _CREATED_RE = re.compile(r"^---\s*\n.*?^created:\s*['\"]?(\d{4}-\d{2}-\d{2}).*?\n---\s*\n", re.DOTALL | re.MULTILINE)

    def __init__(self, registry: DNARegistry, vault_path: str):
        self.registry = registry
        self.vault_path = vault_path
        self._id_to_filename = {} # Map UUID to (folder, filename)

    def _get_entity_name(self, entity_id: str) -> str:
        record = self.registry.get_element(entity_id)
        if not record:
            return f"Unknown_{entity_id[:8]}"
        
        # 1. Check for explicit name field
        name = record.get("name")
        if name and name.lower() not in ["", "unknown", "stub"]:
            return name
            
        # 2. Try to extract from phenotype if it's not a stub
        phenotype = record.get("phenotype", "")
        clean_phenotype = phenotype
        if "STUB" not in record.get("dna", ""):
            # Clean phenotype of headers and sections we don't want to name from
            clean_phenotype = re.sub(r"###.*Unmade Connections.*", "", phenotype, flags=re.IGNORECASE | re.DOTALL)
            clean_phenotype = re.sub(r"###.*DNA Relations.*", "", clean_phenotype, flags=re.IGNORECASE | re.DOTALL)
            clean_phenotype = re.sub(r"###.*Behavioral Model.*", "", clean_phenotype, flags=re.IGNORECASE | re.DOTALL)
            clean_phenotype = re.sub(r"###.*Gamemaster.*", "", clean_phenotype, flags=re.IGNORECASE | re.DOTALL)

        name_patterns = [
            # Was \\[? — an escaped backslash followed by a class-opening "[",
            # which swallowed the capture group's "(" and made the trailing ")"
            # unbalanced, so this raised PatternError for every input.
            r"###\s+\*\*\[?([^\]\*\n]*)\]?\*\*",              # ### **[Name]** or ### **Name**
            r"###\s+([^#\n]*)",                             # ### Name
            r"##\s+(.*)",                                   # ## Name
            r"Name:\*\*\s+\*?([^\*\n]*)\*?$",                # **Name:** *Name*
            r"\*\*Name:\*\*\s+([^\n]*)$",                   # **Name:** Name
            r"Role:\s+([^\n]*)$"                            # Role: Name (fallback)
        ]
        for pattern in name_patterns:
            match = re.search(pattern, clean_phenotype, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                extracted = re.sub(r"^\d+\.\s+", "", extracted)
                # Remove type prefixes like [Faction] or Faction: from the name
                extracted = re.sub(r"^\[?(\w+)\]?:\s*", "", extracted, flags=re.IGNORECASE)
                extracted = extracted.replace("[", "").replace("]", "").replace("*", "")
                if extracted.lower() not in ["npc name", "faction name & symbol", "location name", "item name", "chronicle name", "phenotype", "profile"]:
                    if len(extracted) > 1:
                        return extracted

        # 3. Fallback to tags or ID
        tags = record.get("tags", [])
        for tag in tags:
            if tag not in ["expanded", "stub", "seed", "protagonist"] and "_" not in tag:
                return tag.replace("-", " ").title()
                
        return f"{record['type'].title()}_{entity_id[:8]}"

    def _sanitize_filename(self, name: str) -> str:
        # Remove invalid characters for filenames
        return re.sub(r'[<>:"/\\|?*]', '', name)

    def _prepare_file_map(self):
        """Builds a map of IDs to their final Obsidian paths."""
        for entity_id, record in self.registry._records.items():
            folder = self.TYPE_FOLDER_MAP.get(record["type"], self.DEFAULT_FOLDER)
            name = self._get_entity_name(entity_id)
            filename = self._sanitize_filename(name) + ".md"
            self._id_to_filename[entity_id] = (folder, filename)

    def _find_page_elsewhere(self, filename: str, expected_path: str) -> str:
        """
        Path of a page with this filename living somewhere other than expected.

        Obsidian resolves [[wikilinks]] by name rather than path, so a page can be
        moved freely without breaking links — which is exactly why one can drift
        away from where the type map expects it, and why the sync has to look.
        """
        expected = os.path.normcase(os.path.abspath(expected_path))
        for dirpath, dirnames, filenames in os.walk(self.vault_path):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            if filename in filenames:
                found = os.path.normcase(os.path.abspath(os.path.join(dirpath, filename)))
                if found != expected:
                    return os.path.join(dirpath, filename)
        return ""

    def _existing_file_meta(self, file_path: str) -> Dict[str, str]:
        """Reads status and created date from an existing note's frontmatter."""
        meta = {}
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                status_match = self._STATUS_RE.match(text)
                if status_match:
                    meta["status"] = status_match.group(1).strip().lower()
                created_match = self._CREATED_RE.match(text)
                if created_match:
                    meta["created"] = created_match.group(1)
            except OSError:
                pass
        return meta

    def sync(self) -> Dict[str, int]:
        """
        Syncs decoded entities into the vault as drafts.
        Returns counts: {"written", "skipped_protected", "skipped_stubs"}.
        """
        self._prepare_file_map()

        if not os.path.exists(self.vault_path):
            os.makedirs(self.vault_path, exist_ok=True)

        counts = {"written": 0, "skipped_protected": 0, "skipped_stubs": 0}
        for entity_id, record in self.registry._records.items():
            if "stub" in record.get("tags", []):
                counts["skipped_stubs"] += 1
                continue

            folder, filename = self._id_to_filename[entity_id]
            target_dir = os.path.join(self.vault_path, folder)
            file_path = os.path.join(target_dir, filename)

            existing = self._existing_file_meta(file_path)
            if existing.get("status") in self.PROTECTED_STATUSES:
                counts["skipped_protected"] += 1
                print(f"[ObsidianSync] SKIP (status: {existing['status']}): {os.path.join(folder, filename)}")
                continue

            # A page of this name may already live somewhere else — most often
            # because TYPE_FOLDER_MAP was changed, or the author moved it by hand.
            # Writing to the mapped path regardless would leave two pages for one
            # entity, and if the other copy is canon the vault would hold a canon
            # page and a fresh draft of the same thing. Refuse and say where it is.
            elsewhere = self._find_page_elsewhere(filename, file_path)
            if elsewhere:
                counts["skipped_moved"] = counts.get("skipped_moved", 0) + 1
                print(f"[ObsidianSync] SKIP (already at another path): "
                      f"{os.path.relpath(elsewhere, self.vault_path)} "
                      f"-> expected {os.path.join(folder, filename)}. "
                      f"Move it there, or delete it, to let the sync manage it.")
                continue

            os.makedirs(target_dir, exist_ok=True)
            content = self._format_note(entity_id, record, created=existing.get("created"))
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            counts["written"] += 1

        print(f"[ObsidianSync] Synced {counts['written']} drafts to {self.vault_path} "
              f"({counts['skipped_protected']} protected pages untouched, "
              f"{counts['skipped_stubs']} stubs held back)")
        return counts

    def _format_note(self, entity_id: str, record: Dict[str, Any], created: str = None) -> str:
        """Formats the DNA record into a draft note per the vault conventions."""
        name = self._get_entity_name(entity_id)
        phenotype = strip_decoder_artifacts(strip_phenotype_tail(record.get("phenotype", "")))
        tags = [t for t in record.get("tags", []) if t != "expanded"]
        today = date.today().isoformat()
        audit_status = record.get("audit", {}).get("status", "unaudited")

        # 1. Frontmatter (vault conventions: type, status, created, updated, tags)
        frontmatter = [
            "---",
            f"type: {record['type']}",
            "status: draft",
            f"created: {created or today}",
            f"updated: {today}",
            "tags:",
            "  - dna-generated",
            *[f"  - {tag}" for tag in tags],
            f"dna_id: {entity_id}",
            f"audit: {audit_status}",
            "---"
        ]
        
        # 2. Relationship Header (Dataview/Inline style)
        links = self.registry.get_links(entity_id)
        rel_lines = ["\n# 🧬 DNA Relations\n"]
        
        # Registry edge semantics: edges[X]["parent"] holds X's CHILDREN and
        # edges[X]["child"] holds X's PARENTS (link_elements(A, B, "parent")
        # makes A the parent of B). When an edge carries no custom label, its
        # label defaults to the raw rel_type, which reads inverted on the note —
        # translate those defaults to the direction as seen from this entity.
        default_label_display = {"parent": "Child", "child": "Parent", "peer": "Peer"}
        # Custom labels are written from the SOURCE's point of view, so on the
        # other end of the edge they read backwards ("Contains: [[Skarn]]" on a
        # page that is inside Skarn). Invert the ones we know; "child" edges are
        # the inbound direction, where the target is this entity's container.
        inverse_label_display = {"contains": "Within", "home_of": "Home", "controls": "Controlled By"}
        for rel_type in ["parent", "child", "peer"]:
            edges = links.get(rel_type, [])
            if edges:
                for edge in edges:
                    target_id = edge["id"]
                    label = edge.get("label", rel_type)
                    if label in default_label_display:
                        display = default_label_display[label]
                    elif rel_type == "child" and label in inverse_label_display:
                        display = inverse_label_display[label]
                    else:
                        display = label.title()
                    _, target_filename = self._id_to_filename.get(target_id, (None, None))
                    if target_filename:
                        target_note = target_filename.replace(".md", "")
                        rel_lines.append(f"- **{display}**: [[{target_note}]]")
        
        if len(rel_lines) == 1:
            rel_lines = [] # No links
            
        # 3. Assemble
        content = "\n".join(frontmatter)
        content += f"\n\n# {name}\n"
        if record.get("gist"):
            content += f"\n*{record['gist']}*\n"
        if rel_lines:
            content += "\n".join(rel_lines) + "\n"
        content += "\n---\n"
        content += phenotype
        
        return content
