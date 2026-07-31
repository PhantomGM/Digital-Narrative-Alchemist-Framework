"""Unit tests for the CanonComposer (Pile-3: compose from canon, no DNA)."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.registry import DNARegistry
from layer5_dna_substrate.canon_composer import CanonComposer


def _canon(reg, name, phenotype):
    eid = reg.register_element("region", "DNA", phenotype, name=name)
    reg._records[eid]["tags"].append("canonized")
    return eid


def _stub(reg, name, source_id, stype="location"):
    eid = reg.register_element(stype, "STUB", f"[STUB] {name}", name=name, tags=["stub"])
    reg._records[eid]["stub_metadata"] = {"name": name, "description": "a place", "source_id": source_id}
    reg.link_elements(source_id, eid, "peer", f"mentions_{name}")
    return eid


IRON = """### The Iron Dominion

The Dominion is a land of fortified mountains.

### Notable Landmarks

*   **The Bastion of the Unwavering Word:** A massive, strategically vital fortress at a key pass leading out of the Dominion toward the Ash Wastes. It is heavily garrisoned, its walls etched with countless invocations, its battlements bristling with scavenged energy weapons.
*   **The Iron Vaults:** Repurposed pre-Collapse bunkers.

### 🔗 Unmade Connections (DNA Stubs)
*   **[Location] The Bastion of the Unwavering Word:** The fortress guarding the pass.
"""


def build():
    reg = DNARegistry()
    iron = _canon(reg, "The Iron Dominion", IRON)
    bastion = _stub(reg, "The Bastion of the Unwavering Word", iron)
    # A name-only stub: canon mentions it once, terse, nowhere described.
    ghost = _stub(reg, "The Pale Sentinel", iron)  # not present in IRON prose
    return reg, iron, bastion, ghost


def test_gather_pulls_canon_blocks_not_relations():
    reg, iron, bastion, ghost = build()
    c = CanonComposer(reg)
    blocks = c.gather("The Bastion of the Unwavering Word", exclude_id=bastion)
    texts = [b for _, b in blocks]
    # The rich landmark description is captured...
    assert any("strategically vital fortress" in t for t in texts)
    # ...sourced to the canon page...
    assert all(src == "The Iron Dominion" for src, _ in blocks)
    # ...and the header/relations lines are not treated as description.
    assert not any(t.startswith("🧬") or "Mentions_" in t for t in texts)


def test_assess_triage():
    reg, iron, bastion, ghost = build()
    c = CanonComposer(reg)
    a = c.assess(reg.get_element(bastion))
    assert a["strategy"] == "compose" and a["rich_blocks"] >= 1
    assert "The Iron Dominion" in a["sources"]
    # A stub canon never describes → must be generated, not composed.
    g = c.assess(reg.get_element(ghost))
    assert g["strategy"] == "generate"


def test_compose_produces_sourced_page_from_canon_only():
    reg, iron, bastion, ghost = build()
    c = CanonComposer(reg)
    body = c.compose(reg.get_element(bastion))
    assert body is not None
    assert "Composed from canon" in body
    assert "strategically vital fortress" in body     # the canon fact
    assert "[[The Iron Dominion]]" in body            # cited to its source
    # A thinly-mentioned stub composes to nothing (caller routes it to generation).
    assert c.compose(reg.get_element(ghost)) is None


def test_compose_into_record_retags_and_marks_composed():
    reg, iron, bastion, ghost = build()
    c = CanonComposer(reg)
    assert c.compose_into_record(bastion) is True
    rec = reg.get_element(bastion)
    assert "stub" not in rec["tags"] and "canon-composed" in rec["tags"]
    assert rec["audit"]["status"] == "composed"
    assert rec["dna"] == "COMPOSED"
    assert c.compose_into_record(ghost) is False       # unchanged
    assert "stub" in reg.get_element(ghost)["tags"]


def test_triage_all_orders_compose_first():
    reg, iron, bastion, ghost = build()
    rows = CanonComposer(reg).triage_all()
    assert rows[0]["strategy"] == "compose"            # compose-ready first
    assert {r["name"] for r in rows} == {"The Bastion of the Unwavering Word", "The Pale Sentinel"}


if __name__ == "__main__":
    for fn in [test_gather_pulls_canon_blocks_not_relations, test_assess_triage,
               test_compose_produces_sourced_page_from_canon_only,
               test_compose_into_record_retags_and_marks_composed,
               test_triage_all_orders_compose_first]:
        fn(); print(f"✓ {fn.__name__}")
    print("All canon composer tests passed.")
