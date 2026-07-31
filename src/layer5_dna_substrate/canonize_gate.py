"""
The Canonize Gate: selection pressure between generation and the world bible.

For each decoded (non-stub) entity, the gate:
  1. Assembles the entity's ContextPackage and takes its canon_slice() —
     the same truth that guided generation now judges it.
  2. Audits the prose (tail split off first) with the ConsistencyAuditor
     in fail-closed mode.
  3. On a contradiction with a pinpointed sentence, applies the auditor's
     surgical patch and re-audits, up to max_rounds.
  4. Ends in one of four states, stored on the registry record:
       consistent - clean on the first audit
       patched    - clean after surgical fixes (phenotype updated, tail intact)
       flagged    - a contradiction the loop couldn't fix; the author decides
       unreviewed - the audit itself failed; retry later, never trust silently

The gate never promotes anything to canon: it prepares drafts and evidence.
Promotion stays with the author, in the vault.
"""

from datetime import date
from typing import Dict, List, Optional

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.context_assembler import ContextAssembler, AssemblyRequest, resolve_locale
from layer5_dna_substrate.phenotype_meta import split_phenotype_tail

_OOC_MARKER = "[OOC System Message"


class CanonizeGate:
    def __init__(self, registry: DNARegistry, assembler: ContextAssembler, auditor,
                 max_rounds: int = 3):
        self.registry = registry
        self.assembler = assembler
        self.auditor = auditor
        self.max_rounds = max_rounds

    def _reviewable_ids(self, force: bool = False) -> List[str]:
        """Decoded entities that still need review (all of them when force=True)."""
        ids = []
        for entity_id, record in self.registry._records.items():
            if "stub" in record.get("tags", []):
                continue
            if not record.get("phenotype"):
                continue
            prior = record.get("audit", {}).get("status")
            if not force and prior in ("consistent", "patched"):
                continue
            ids.append(entity_id)
        return ids

    async def review_entity(self, entity_id: str) -> Dict:
        """
        Runs the audit→patch→re-audit loop for one entity.
        Returns a report dict and stores the verdict on the registry record.
        """
        record = self.registry.get_element(entity_id)
        if not record:
            return {"entity_id": entity_id, "status": "unreviewed", "notes": ["not in registry"]}

        package = self.assembler.assemble(AssemblyRequest(
            element_type=record["type"],
            anchor_id=entity_id,
            locale_id=resolve_locale(self.registry, entity_id),
        ))
        canon_state = package.canon_slice()

        original_prose, tail = split_phenotype_tail(record.get("phenotype", ""))
        prose = original_prose
        notes: List[str] = []
        status: Optional[str] = None
        rounds = 0

        while rounds < self.max_rounds:
            rounds += 1
            result = await self.auditor.audit(prose, canon_state, fail_open=False)

            if result["status"] == "error":
                status = "unreviewed"
                notes.append(f"audit error: {result.get('correction_note', '')}")
                break

            if result["status"] == "valid":
                status = "consistent" if rounds == 1 else "patched"
                break

            # Invalid
            note = result.get("correction_note", "")
            notes.append(note)

            if not result.get("offending_text"):
                # No pinpointed sentence: nothing to patch surgically —
                # this is a judgment call for the author, not the machine.
                status = "flagged"
                break

            patched = await self.auditor.patch(prose, result, current_state=canon_state)
            if not patched or _OOC_MARKER in patched:
                # Patch failed internally; never let its fallback note near the vault
                status = "flagged"
                notes.append("surgical patch failed")
                break
            prose = patched

        if status is None:
            # Loop exhausted while still invalid
            status = "flagged"
            notes.append(f"still inconsistent after {self.max_rounds} audit rounds")

        # Only a fully valid end state may rewrite the phenotype; a flagged
        # entity keeps its original prose so the author sees the real conflict.
        if status == "patched":
            record["phenotype"] = prose.rstrip() + ("\n\n" + tail + "\n" if tail else "\n")

        record["audit"] = {
            "status": status,
            "notes": notes,
            "rounds": rounds,
            "reviewed": date.today().isoformat(),
        }

        print(f"[CanonizeGate] {record.get('name') or entity_id[:8]}: {status}"
              + (f" ({notes[-1]})" if notes else ""))
        return {"entity_id": entity_id, "name": record.get("name"), "status": status,
                "rounds": rounds, "notes": notes}

    async def review_all(self, force: bool = False) -> List[Dict]:
        """Reviews every decoded entity sequentially. Returns the reports."""
        reports = []
        for entity_id in self._reviewable_ids(force=force):
            reports.append(await self.review_entity(entity_id))

        summary = {}
        for report in reports:
            summary[report["status"]] = summary.get(report["status"], 0) + 1
        print(f"[CanonizeGate] Review complete: {summary or 'nothing to review'}")
        return reports
