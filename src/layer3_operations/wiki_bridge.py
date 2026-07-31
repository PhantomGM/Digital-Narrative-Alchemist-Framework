import os
import re
import sys
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

# Add src to path for direct execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from layer1_core.contracts import LoreChunk

# Frontmatter must be anchored to the start of the file. An unanchored
# "---.*?---" match will happily eat the body between two horizontal rules.
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.DOTALL)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)[ \t]*$", re.MULTILINE)

# A generated relation line: a bolded label whose whole value is a wikilink,
# e.g. "- **Mentions_Order Of The Scroll:**: [[Order of the Scroll]]".
# The registry graph already holds these; as prose they are noise.
# The wikilink body may be empty ("- **Mentions_**: [[]]") when the generator
# had no target to name; that is noise too.
_RELATION_BULLET_RE = re.compile(
    r"^\s*[-*]\s*\*\*[^*]*\*\*\s*:?\s*:?\s*(?:\[\[[^\]]*\]\][,;\s]*)+$")


def normalize_entity_id(name: str) -> str:
    """
    Reduce a page title or search term to a stable lookup id.

    Chronicler.query_lore() matches entity_id exactly, so ingestion and
    retrieval must agree on the form. Collapsing every run of non-alphanumeric
    characters means "Void-Whisperer", "void whisperer" and "Void Whisperer"
    all reach the same chunks.
    """
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


class WikiBridge:
    """
    Bridges the Obsidian Wiki (static world knowledge) with the DNA Framework's
    live RAG system (Chronicler / Lore Store).

    Ingestion walks the vault recursively. It previously required a single
    hardcoded "Concepts" subdirectory and listed it non-recursively, which no
    vault in this project actually has — so ingestion always returned zero
    chunks. Pass `subdirs` to restrict which top-level folders are read.
    """

    # Vault machinery and scaffolding, not world knowledge. Ingesting the
    # operations log or a template would pollute the lore store with
    # maintenance chatter and placeholder text.
    DEFAULT_EXCLUDED_DIRS = frozenset({
        ".obsidian", ".git", ".trash", "__pycache__", "Templates", "scripts",
    })
    DEFAULT_EXCLUDED_FILES = frozenset({
        "CLAUDE.md", "Log.md", "Index.md", "Home.md", "README.md",
    })

    # Sections written by the pipeline for the author's benefit, not world
    # knowledge: ObsidianSync emits "# DNA Relations" as wikilink bullets, and
    # older decoder output left "Unmade Connections" and tail headings behind.
    # Compared after _normalize_header(), so emoji and markup do not matter.
    EXCLUDED_SECTIONS = frozenset({
        "dna relations",
        "relations",
        "unmade connections",
        "machine readable tail",
        "metadata",
    })

    def __init__(
        self,
        wiki_root: str,
        subdirs: Optional[Sequence[str]] = None,
        canon_only: bool = True,
        excluded_dirs: Optional[Sequence[str]] = None,
        excluded_files: Optional[Sequence[str]] = None,
    ):
        """
        Args:
            wiki_root: Vault root to ingest.
            subdirs: Restrict ingestion to these top-level folders. None reads
                the whole vault.
            canon_only: Skip pages whose frontmatter marks them as anything
                other than canon. Pages with no status field are ingested, so
                vaults that do not use the convention still work.
            excluded_dirs / excluded_files: Override the defaults.
        """
        self.wiki_root = wiki_root
        self.subdirs = list(subdirs) if subdirs else None
        self.canon_only = canon_only
        self.excluded_dirs = frozenset(
            excluded_dirs if excluded_dirs is not None else self.DEFAULT_EXCLUDED_DIRS)
        self.excluded_files = frozenset(
            excluded_files if excluded_files is not None else self.DEFAULT_EXCLUDED_FILES)

        self.lore_chunks: List[LoreChunk] = []
        self.stats: Dict[str, int] = {}

    # --- ingestion ----------------------------------------------------------

    def ingest_wiki(self) -> List[LoreChunk]:
        """Scan the vault and convert markdown content into LoreChunks."""
        print(f"[WikiBridge] Ingesting wiki from: {self.wiki_root}")

        self.lore_chunks = []
        self.stats = {"files_seen": 0, "files_ingested": 0, "skipped_non_canon": 0, "skipped_empty": 0}

        if not os.path.isdir(self.wiki_root):
            print(f"[WikiBridge] Wiki root not found: {self.wiki_root}")
            return []

        for path in self._iter_markdown_files():
            self.stats["files_seen"] += 1
            content = self._read(path)
            if content is None:
                continue

            frontmatter, body = self._split_frontmatter(content)

            if self.canon_only and not self._is_canon(frontmatter):
                self.stats["skipped_non_canon"] += 1
                continue

            if not body.strip():
                self.stats["skipped_empty"] += 1
                continue

            before = len(self.lore_chunks)
            self._parse_content(path, body)
            if len(self.lore_chunks) > before:
                self.stats["files_ingested"] += 1

        self._report()
        return self.lore_chunks

    def _iter_markdown_files(self) -> Iterator[str]:
        """Yield every ingestable markdown file under the configured roots."""
        roots: List[str] = []
        if self.subdirs:
            for sub in self.subdirs:
                candidate = os.path.join(self.wiki_root, sub)
                if os.path.isdir(candidate):
                    roots.append(candidate)
                else:
                    print(f"[WikiBridge] Requested subdirectory not found, skipping: {candidate}")
        else:
            roots = [self.wiki_root]

        for root in roots:
            for dirpath, dirnames, filenames in os.walk(root):
                # Prune in place so os.walk does not descend into them.
                dirnames[:] = sorted(
                    d for d in dirnames
                    if d not in self.excluded_dirs and not d.startswith("."))

                for filename in sorted(filenames):
                    if not filename.endswith(".md") or filename in self.excluded_files:
                        continue
                    # A file literally named ".md" has no title to key facts on.
                    if not filename[:-3].strip():
                        continue
                    yield os.path.join(dirpath, filename)

    def _read(self, path: str) -> Optional[str]:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            print(f"[WikiBridge] Could not read {path}: {exc}")
            return None

    @staticmethod
    def _split_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
        """Split leading YAML frontmatter from the body. Flat scalars only."""
        match = _FRONTMATTER_RE.match(content)
        if not match:
            return {}, content

        fields: Dict[str, str] = {}
        for line in match.group(1).splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or ":" not in stripped:
                continue
            # Nested keys and list items are not needed here.
            if line.startswith((" ", "\t")) or stripped.startswith("- "):
                continue
            key, _, value = stripped.partition(":")
            fields[key.strip().lower()] = value.strip().strip("\"'")

        return fields, content[match.end():]

    def _is_canon(self, frontmatter: Dict[str, str]) -> bool:
        """
        Treat a page as canon unless it explicitly says otherwise.

        The World Builder vault marks every page canon / draft / deprecated and
        only the author promotes a draft. Drafts are unreviewed generated text,
        so feeding them to the GM as established world knowledge would leak
        unvetted material into play. Pages with no status field predate the
        convention and are ingested.
        """
        status = frontmatter.get("status", "").strip().lower()
        return status in ("", "canon")

    def _report(self) -> None:
        stats = self.stats
        print(
            f"[WikiBridge] Ingested {len(self.lore_chunks)} lore chunks from "
            f"{stats['files_ingested']}/{stats['files_seen']} pages."
        )
        if stats["skipped_non_canon"]:
            print(f"[WikiBridge] Skipped {stats['skipped_non_canon']} non-canon pages.")
        if stats["skipped_empty"]:
            print(f"[WikiBridge] Skipped {stats['skipped_empty']} empty pages.")
        if not self.lore_chunks and stats["files_seen"] == 0:
            print(f"[WikiBridge] No markdown pages found under {self.wiki_root}.")

    # --- parsing ------------------------------------------------------------

    def _parse_content(self, path: str, body: str) -> None:
        """Parse one page body into discrete facts."""
        entity_name = os.path.basename(path)[:-3].strip()
        entity_id = normalize_entity_id(entity_name)
        title_key = self._normalize_header(entity_name)

        for header, section_body in self._iter_sections(body):
            section_body = self._clean_body(section_body)
            if not section_body:
                continue

            # A machine-written section is not discarded wholesale: on stub pages
            # the only real description is a "[STUB] ..." line sitting inside the
            # generated relations block. Its bullets are already gone, so whatever
            # prose survives is the page's own description.
            machine = header is not None and self._is_machine_section(header)

            # Content before any heading, or under the page's own title heading,
            # is the page's overview rather than a subsection.
            is_intro = header is None or machine or self._normalize_header(header) == title_key

            if is_intro:
                prefix = entity_name
                importance = 3  # static world knowledge, page-level
                section_body = self._strip_redundant_title(section_body, entity_name)
            else:
                prefix = f"{entity_name} ({self._strip_markup(header)})"
                importance = 2

            # Bullet lists carry one fact per bullet, at any level — a stub
            # roster collapsed into a single clipped chunk would lose most of it.
            bullets = re.findall(r"^\s*[-*]\s+(.*\S)", section_body, re.MULTILINE)
            if bullets:
                for bullet in bullets:
                    self.lore_chunks.append(LoreChunk(
                        fact=f"{prefix}: {bullet.strip()}",
                        entity_id=entity_id,
                        importance=importance,
                        source_turn=0,  # 0 indicates static world knowledge
                    ))
            else:
                self.lore_chunks.append(LoreChunk(
                    fact=f"{prefix}: {_clip(section_body, 400 if not is_intro else 300)}",
                    entity_id=entity_id,
                    importance=importance,
                    source_turn=0,
                ))

    @staticmethod
    def _iter_sections(body: str) -> Iterator[Tuple[Optional[str], str]]:
        """
        Yield (header, body) for each ATX heading, header None for the preamble.

        Splits on every heading level. The previous "\\n##+" split missed H1
        headings, so the generated "# DNA Relations" block was swept into the
        page's intro and its machine-written relation bullets were ingested as
        top-importance world lore.
        """
        matches = list(_HEADING_RE.finditer(body))
        if not matches:
            yield None, body
            return

        preamble = body[:matches[0].start()]
        if preamble.strip():
            yield None, preamble

        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            yield match.group(2).strip(), body[match.end():end]

    @staticmethod
    def _normalize_header(header: str) -> str:
        """Reduce a heading to comparable words, dropping emoji and markup."""
        return " ".join(re.sub(r"[^a-z0-9]+", " ", header.lower()).split())

    @staticmethod
    def _strip_markup(header: str) -> str:
        """Drop emphasis markers and leading emoji from a heading for display."""
        text = re.sub(r"[*_`]+", "", header).strip()
        return re.sub(r"\A[^\w\[(\"']+", "", text).strip() or text

    @staticmethod
    def _strip_redundant_title(text: str, entity_name: str) -> str:
        """
        Drop a leading "[STUB] <page name>:" from a body.

        Every fact is already prefixed with the page name, so the vault's own
        stub marker would render as "Kaelen: [STUB] Kaelen:: The aging leader".
        """
        cleaned = re.sub(r"\A\[STUB\]\s*", "", text, flags=re.IGNORECASE)
        pattern = r"\A" + re.escape(entity_name) + r"\s*:+\s*\**\s*"
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip() or text.strip()

    def _is_machine_section(self, header: str) -> bool:
        """Match on prefix so parenthetical suffixes still count.

        The generated heading is "Unmade Connections (DNA Stubs)", which an
        exact comparison against "unmade connections" misses.
        """
        normalized = self._normalize_header(header)
        return any(normalized == name or normalized.startswith(name + " ")
                   for name in self.EXCLUDED_SECTIONS)

    @staticmethod
    def _clean_body(section_body: str) -> str:
        """
        Drop lines that carry no fact: horizontal rules, table separators, and
        machine-written relation bullets such as
        "- **Mentions_The Weaving Chamber**: [[Entity]]".

        Relations are dropped line by line rather than by section, so prose that
        shares a section with them survives.
        """
        kept = [
            line for line in section_body.splitlines()
            if not re.match(r"\s*(-{3,}|\*{3,}|_{3,})\s*$", line)
            and not re.match(r"\s*\|[\s:|-]+\|?\s*$", line)
            and not _RELATION_BULLET_RE.match(line)
        ]
        return "\n".join(kept).strip()

    # Retained for backwards compatibility with any external caller.
    def _parse_file(self, path: str) -> None:
        content = self._read(path)
        if content is None:
            return
        _, body = self._split_frontmatter(content)
        self._parse_content(path, body)


def _clip(text: str, limit: int) -> str:
    """Truncate to `limit`, marking the cut only when one actually happens."""
    collapsed = " ".join(text.split())
    return collapsed if len(collapsed) <= limit else collapsed[:limit].rstrip() + "..."


if __name__ == "__main__":
    import argparse

    from common.paths import PathConfigError, resolve_wiki_path

    ap = argparse.ArgumentParser(description="Test wiki ingestion.")
    ap.add_argument("--wiki", default=None,
                    help="Wiki directory to ingest (or set OBSIDIAN_WIKI_PATH)")
    ap.add_argument("--subdir", action="append", dest="subdirs", default=None,
                    help="Restrict to this top-level folder (repeatable)")
    ap.add_argument("--include-drafts", action="store_true",
                    help="Ingest non-canon pages too")
    ap.add_argument("--limit", type=int, default=5, help="Sample chunks to print")
    args = ap.parse_args()

    try:
        wiki_path = resolve_wiki_path(args.wiki)
    except PathConfigError as exc:
        raise SystemExit(f"{exc}\n  (pass --wiki PATH)")

    chunks = WikiBridge(
        wiki_path,
        subdirs=args.subdirs,
        canon_only=not args.include_drafts,
    ).ingest_wiki()

    # Vault prose can contain characters the console encoding cannot represent
    # (emoji, dashes); never let sampling output crash the run.
    encoding = sys.stdout.encoding or "utf-8"
    for chunk in chunks[:args.limit]:
        line = f"[{chunk.importance}] ({chunk.entity_id}) {chunk.fact}"
        print(line.encode(encoding, errors="replace").decode(encoding))
