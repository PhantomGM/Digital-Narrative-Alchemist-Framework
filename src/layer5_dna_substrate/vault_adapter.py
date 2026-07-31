"""
Read-only adapter over the Obsidian world-bible vault.

The vault is the world's long-term memory: canon pages, the Index roster,
and the World Overview pillars. The ContextAssembler reads it through this
adapter; nothing in the generation pipeline writes canon (drafts are synced
separately, and only the author promotes them).

Every accessor degrades gracefully: a missing vault, page, or section
yields empty output rather than an error, so the pipeline can run before
the vault exists or after pages are renamed.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_INDEX_LINE_RE = re.compile(
    r"^\s*[-*]\s*\[\[([^\]|]+)(?:\|[^\]]*)?\]\]\s*[-–—]\s*(.+?)\s*(?:\((canon|draft|deprecated)\))?\s*$"
)


class VaultAdapter:
    def __init__(self, vault_path: str,
                 overview_page: str = "World Overview.md",
                 index_page: str = "Index.md",
                 timeline_page: str = os.path.join("History", "Timeline.md")):
        self.vault_path = Path(vault_path)
        self.overview_page = overview_page
        self.index_page = index_page
        self.timeline_page = timeline_page
        self._page_cache: Dict[str, Optional[dict]] = {}

    # ── Page access ──────────────────────────────────────────

    def _read_page(self, relative_or_name: str) -> Optional[dict]:
        """
        Reads a page by vault-relative path, or by bare page name searched
        anywhere in the vault. Returns {"body": str, "status": str} or None.
        """
        key = relative_or_name.lower()
        if key in self._page_cache:
            return self._page_cache[key]

        result = None
        if self.vault_path.is_dir():
            candidate = self.vault_path / relative_or_name
            if not candidate.is_file():
                name = relative_or_name if relative_or_name.endswith(".md") else relative_or_name + ".md"
                matches = [p for p in self.vault_path.rglob(name) if ".obsidian" not in p.parts]
                candidate = matches[0] if matches else None
            if candidate:
                try:
                    text = candidate.read_text(encoding="utf-8")
                    status = "unknown"
                    fm_match = _FRONTMATTER_RE.match(text)
                    body = text
                    if fm_match:
                        body = text[fm_match.end():]
                        try:
                            fm = yaml.safe_load(fm_match.group(1)) or {}
                            status = str(fm.get("status", "unknown")).lower()
                        except yaml.YAMLError:
                            pass
                    result = {"body": body.strip(), "status": status}
                except OSError:
                    result = None

        self._page_cache[key] = result
        return result

    def page_excerpt(self, page_name: str, max_chars: int = 600) -> str:
        """
        Status-tagged excerpt of a page body, cut at a line boundary.
        Empty string when the page doesn't exist.
        """
        page = self._read_page(page_name)
        if not page:
            return ""
        tag = self._status_tag(page["status"])
        body = page["body"]
        if len(body) > max_chars:
            body = body[:max_chars].rsplit("\n", 1)[0].rstrip()
        return f"{tag} {page_name.removesuffix('.md')}\n{body}"

    @staticmethod
    def _status_tag(status: str) -> str:
        if status == "canon":
            return "[CANON - immutable, do not contradict]"
        if status == "deprecated":
            return "[DEPRECATED - no longer true]"
        return "[DRAFT - prefer, but may be renegotiated]"

    # ── World frame sources ──────────────────────────────────

    def world_overview(self) -> str:
        """The World Overview body (pillars, tone, themes), status-tagged."""
        page = self._read_page(self.overview_page)
        if not page:
            return ""
        return f"{self._status_tag(page['status'])}\n{page['body']}"

    def calendar_rules(self) -> str:
        """The '## Calendar' section of the Timeline page, if defined."""
        page = self._read_page(self.timeline_page)
        if not page:
            return ""
        match = re.search(r"##\s*Calendar\s*\n(.*?)(?=\n##\s|\Z)", page["body"], re.DOTALL)
        if not match:
            return ""
        section = match.group(1).strip()
        if not section or section.lower().startswith(("*undefined", "undefined")):
            return ""
        return f"{self._status_tag(page['status'])} Calendar\n{section}"

    # ── Roster ───────────────────────────────────────────────

    def roster(self) -> List[Dict[str, str]]:
        """
        Parses Index.md into [{"name", "gist", "status"}].
        The Index format is one line per page: '- [[Page]] - description (status)'.
        """
        page = self._read_page(self.index_page)
        if not page:
            return []
        entries = []
        for line in page["body"].splitlines():
            match = _INDEX_LINE_RE.match(line)
            if match:
                entries.append({
                    "name": match.group(1).strip(),
                    "gist": match.group(2).strip(),
                    "status": (match.group(3) or "unknown").lower(),
                })
        return entries
