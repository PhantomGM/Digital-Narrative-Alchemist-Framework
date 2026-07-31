"""Unit tests for the TimelineComposer (Pile-2 deriver)."""

import os
import sys
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from layer5_dna_substrate.timeline_composer import TimelineComposer, parse_sort


def test_parse_sort_grammar():
    assert parse_sort("42 AS") == (42.0, False)
    assert parse_sort("c. 1 BS") == (-1.0, True)
    assert parse_sort("**0**") == (0.0, False)
    assert parse_sort("c. 0–40 AS")[0] == 0.0 and parse_sort("c. 0–40 AS")[1] is True
    assert parse_sort("c. 180 AS") == (180.0, True)
    assert parse_sort("**312 AS**") == (312.0, False)
    # Undated
    assert parse_sort("— *disputed*") == (None, False)
    assert parse_sort("—")[0] is None


def test_sort_orders_bs_before_as_and_undated_first():
    c = TimelineComposer(vault_path=".")
    events = [
        {"date_label": "312 AS", "event": "present", "era": "Post-Collapse", "sources": "x"},
        {"date_label": "**0**", "event": "The Sky-Shatter", "era": "The Collapse", "sources": "x"},
        {"date_label": "c. 1 BS", "event": "silence", "era": "The Collapse", "sources": "x"},
        {"date_label": "— *disputed*", "event": "golden age height", "era": "Golden Age", "sources": "x"},
        {"date_label": "42 AS", "event": "accord", "era": "Post-Collapse", "sources": "x"},
    ]
    order = [e["event"] for e in c.sort(events)]
    assert order == ["golden age height", "silence", "The Sky-Shatter", "accord", "present"]


def test_detect_conflicts():
    c = TimelineComposer(vault_path=".")
    events = [
        {"date_label": "**0**", "event": "The Sky-Shatter: sky ruptures", "era": "The Collapse", "sources": "[[The Collapse]]"},
        {"date_label": "**0**", "event": "Something else at zero", "era": "The Collapse", "sources": "[[X]]"},
        {"date_label": "42 AS", "event": "an event with no source", "era": "Post-Collapse", "sources": ""},
        {"date_label": "gibberish", "event": "unparseable date event", "era": "Post-Collapse", "sources": "[[Y]]"},
    ]
    issues = " | ".join(c.detect_conflicts(events))
    assert "year 0" in issues                    # two events at year zero
    assert "Missing source" in issues
    assert "Unparseable date" in issues


def _write_timeline(root, chronology_rows):
    os.makedirs(os.path.join(root, "History"))
    body = (
        "---\ntype: meta\nstatus: canon\n---\n\n# Timeline\n\n"
        "## Calendar\n\nThe Tally. Present is 312 AS.\n\n"
        "## Chronology\n\nOrdering is relative.\n\n"
        "| Date | Event | Era | Source |\n| ---- | ----- | --- | ------ |\n"
        + "\n".join(chronology_rows) + "\n\n"
        "## Eras\n\n- Golden Age\n- The Collapse\n- Post-Collapse\n"
    )
    path = os.path.join(root, "History", "Timeline.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


def test_seed_and_roundtrip_reproduces_table():
    """The deriver must reproduce a hand-built table from its own parsed rows, and
    leave the Calendar and Eras sections untouched."""
    root = tempfile.mkdtemp(prefix="tl_")
    try:
        rows = [
            "| — *disputed* | The Golden Age at its height | Golden Age | [[Skarn]] |",
            "| c. 1 BS | The Great Silence | The Collapse | [[The Collapse]] |",
            "| **0** | **The Sky-Shatter:** the sky ruptures | The Collapse | [[The Collapse]] |",
            "| 42 AS | The Blighted Accord is struck | Post-Collapse | [[The Blighted Foundry]] |",
            "| **312 AS** | **The present.** | Post-Collapse | [[Skarn]] |",
        ]
        path = _write_timeline(root, rows)
        store = os.path.join(root, "History", "timeline_events.json")
        c = TimelineComposer(root, store_path=store)

        events = c.seed_from_timeline_md()
        assert len(events) == 5
        assert events[0]["era"] == "Golden Age"

        report = c.write_timeline(events)
        assert report["events"] == 5 and report["conflicts"] == []

        after = open(path, encoding="utf-8").read()
        # Every original row survived, in sorted order
        for r in rows:
            assert r in after, f"row lost: {r}"
        # Sorted correctly: Silence (c.1 BS) before Sky-Shatter (0) before Accord (42 AS)
        assert after.index("Great Silence") < after.index("Sky-Shatter") < after.index("Blighted Accord")
        # Authored sections preserved
        assert "## Calendar" in after and "The Tally. Present is 312 AS." in after
        assert "## Eras" in after and "Ordering is relative." in after
        # Idempotent: composing again yields identical bytes
        c.write_timeline(events)
        assert open(path, encoding="utf-8").read() == after
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_new_event_lands_in_correct_position():
    root = tempfile.mkdtemp(prefix="tl2_")
    try:
        rows = [
            "| c. 1 BS | The Great Silence | The Collapse | [[The Collapse]] |",
            "| 42 AS | The Blighted Accord | Post-Collapse | [[The Blighted Foundry]] |",
            "| **312 AS** | **The present.** | Post-Collapse | [[Skarn]] |",
        ]
        path = _write_timeline(root, rows)
        c = TimelineComposer(root, store_path=os.path.join(root, "History", "timeline_events.json"))
        events = c.seed_from_timeline_md()
        # A newly canonized dated fact, appended to the store as a structured event.
        events.append({"date_label": "c. 180 AS", "event": "The Hegemony is founded",
                       "era": "Post-Collapse", "sources": "[[The Sundergate Hegemony]]"})
        c.write_timeline(events)
        after = open(path, encoding="utf-8").read()
        # 180 AS slots between the Accord (42) and the present (312)
        assert after.index("Blighted Accord") < after.index("Hegemony is founded") < after.index("The present")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    test_parse_sort_grammar()
    test_sort_orders_bs_before_as_and_undated_first()
    test_detect_conflicts()
    test_seed_and_roundtrip_reproduces_table()
    test_new_event_lands_in_correct_position()
    print("All timeline composer tests passed.")
