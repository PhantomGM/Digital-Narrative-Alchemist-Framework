import os
import re
import sys
from typing import List

# Add src to path for direct execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from layer1_core.contracts import LoreChunk

class WikiBridge:
    """
    Bridges the Obsidian Wiki (static world knowledge) with the DNA Framework's
    live RAG system (Chronicler / Lore Store).
    """
    
    def __init__(self, wiki_root: str):
        self.wiki_root = wiki_root
        self.lore_chunks: List[LoreChunk] = []

    def ingest_wiki(self) -> List[LoreChunk]:
        """
        Scans the Wiki directory and converts markdown content into LoreChunks.
        """
        print(f"[WikiBridge] Ingesting wiki from: {self.wiki_root}")
        
        concepts_dir = os.path.join(self.wiki_root, "Concepts")
        if not os.path.exists(concepts_dir):
            print(f"[WikiBridge] Concepts directory not found at {concepts_dir}")
            return []

        for filename in os.listdir(concepts_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(concepts_dir, filename)
                self._parse_file(file_path)

        print(f"[WikiBridge] Ingested {len(self.lore_chunks)} lore chunks from wiki.")
        return self.lore_chunks

    def _parse_file(self, path: str):
        """
        Parses a single markdown file into discrete facts.
        """
        entity_name = os.path.basename(path).replace(".md", "").replace("-", " ").title()
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove frontmatter
        content = re.sub(r"---.*?---", "", content, flags=re.DOTALL)
        
        # Split by headers
        sections = re.split(r"\n##\s+", content)
        
        # The first section is usually the intro
        intro = sections[0].strip()
        if intro:
            # Remove the main # title if present
            intro = re.sub(r"^#\s+.*?\n", "", intro).strip()
            if intro:
                self.lore_chunks.append(LoreChunk(
                    fact=f"{entity_name}: {intro[:300]}...",
                    entity_id=entity_name.lower().replace(" ", "_"),
                    importance=3,
                    source_turn=0 # 0 indicates static world knowledge
                ))

        # Parse subsequent sections
        for section in sections[1:]:
            lines = section.split("\n")
            header = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            
            if body:
                # Handle bullet points as individual facts
                bullets = re.findall(r"^\s*[-*]\s+(.*)", body, re.MULTILINE)
                if bullets:
                    for bullet in bullets:
                        self.lore_chunks.append(LoreChunk(
                            fact=f"{entity_name} ({header}): {bullet}",
                            entity_id=entity_name.lower().replace(" ", "_"),
                            importance=2,
                            source_turn=0
                        ))
                else:
                    # Treat the whole section body as a fact
                    self.lore_chunks.append(LoreChunk(
                        fact=f"{entity_name} ({header}): {body[:400]}...",
                        entity_id=entity_name.lower().replace(" ", "_"),
                        importance=2,
                        source_turn=0
                    ))

if __name__ == "__main__":
    import argparse
    import sys

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from common.paths import PathConfigError, resolve_wiki_path

    ap = argparse.ArgumentParser(description="Test wiki ingestion.")
    ap.add_argument("--wiki", default=None,
                    help="Wiki directory to ingest (or set OBSIDIAN_WIKI_PATH)")
    args = ap.parse_args()

    try:
        wiki_path = resolve_wiki_path(args.wiki)
    except PathConfigError as exc:
        raise SystemExit(f"{exc}\n  (pass --wiki PATH)")

    chunks = WikiBridge(wiki_path).ingest_wiki()
    print(f"Ingested {len(chunks)} chunks from {wiki_path}")
    for chunk in chunks[:5]:
        print(f"[{chunk.importance}] {chunk.fact}")
