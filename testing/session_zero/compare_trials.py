"""
Trial 1 versus trial 2, checked defect by defect rather than by eye.

Same four players, same transcripts, same premise. The only variable is the
machinery: trial 1 used a hand-rolled (type, count) list and a safety block
pasted into a prompt string; trial 2 uses ContentContract and
ContextPackage.safety. So a difference here is attributable to the fix.

Each check below is a finding from 03_findings.md. Probes locate; a reader
decides -- the veil check in particular reports passages, not verdicts.

    .\\venv\\Scripts\\python.exe testing/session_zero/compare_trials.py
"""

import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from common.console import enable_safe_stdout  # noqa: E402
from layer5_dna_substrate.expansion_manager import _resolve_stub_type  # noqa: E402
from layer5_dna_substrate.phenotype_meta import parse_phenotype_tail  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
T1 = os.path.join(HERE, "pages")
T2 = os.path.join(HERE, "pages_trial2")

CLAUSTRO = (r"\b(air (running|runs) out|no air|squeez\w+|wriggl\w+|pinned|"
            r"trapped under|buried alive|cave-?in|walls clos\w+|"
            r"can'?t get out|entombed|suffocat\w+)\b")
GORE = (r"\b(viscera|entrails|gore|dismember\w+|flay\w+|disembowel\w+|"
        r"eye(ball)?s? (burst|torn|gouged))\b")
WARMTH = (r"\b(warm|laughter|laugh|meal|share[ds]?|welcome\w*|comfort\w*|"
          r"friendly|kind\w*|home|belong\w*|rest|quiet|safe)\b")


def pages(directory):
    return {os.path.basename(p): open(p, encoding="utf-8").read()
            for p in sorted(glob.glob(os.path.join(directory, "*.md")))}


def first_heading(text):
    m = re.search(r"^#{1,4}\s+(.+?)\s*$", text.replace("\r\n", "\n"), re.M)
    return m.group(1).replace("**", "").strip() if m else "(none)"


def find_page(docs, *needles):
    for name, text in docs.items():
        if any(n in name for n in needles):
            return name, text
    return None, ""


def section(title, ):
    print(f"\n{title}\n{'-' * len(title)}")


def main():
    if not os.path.isdir(T2):
        print(f"trial 2 not generated yet: {T2}")
        return
    a, b = pages(T1), pages(T2)
    print(f"trial 1: {len(a)} pages    trial 2: {len(b)} pages")

    # --- defect 1: a count is not a brief -----------------------------------
    section("1. Per-slot brief -- is the POI a mine?")
    for label, docs in (("trial 1", a), ("trial 2", b)):
        name, text = find_page(docs, "regional_poi", "_mine")
        head = first_heading(text) if text else "(absent)"
        is_mine = bool(re.search(r"\bmine\b|\bshaft\b|\bmaw\b", head, re.I))
        print(f"   {label}: {head[:60]:<60} {'MINE' if is_mine else '<-- NOT a mine'}")

    # --- defect 2: ordering / naming consistency ----------------------------
    section("2. Ordering -- was the language generated before the names?")
    for label, docs in (("trial 1", a), ("trial 2", b)):
        order = list(docs)
        ling = next((i for i, n in enumerate(order) if "linguistic" in n), None)
        town = next((i for i, n in enumerate(order)
                     if "settlement" in n or "_town" in n), None)
        verdict = ("language first" if ling is not None and town is not None
                   and ling < town else "<-- town named before its language")
        print(f"   {label}: linguistic at {ling}, town at {town}   {verdict}")

    # --- defect 3: tone -----------------------------------------------------
    section("3. Tone -- is there anywhere warm?")
    for label, docs in (("trial 1", a), ("trial 2", b)):
        name, text = find_page(docs, "_haven", "establishment")
        if not text:
            print(f"   {label}: no warm slot in the contract at all")
            continue
        warm = len(re.findall(WARMTH, text, re.I))
        dark = len(re.findall(r"\b(blood|dread|rot|corrupt\w*|menace|sinister|"
                              r"scream\w*|curse\w*|fear)\b", text, re.I))
        print(f"   {label}: {name} -- {warm} warm cues, {dark} dark cues")

    # --- regression: factions asymmetric ------------------------------------
    section("4. Regression -- are the three factions asymmetric in kind?")
    for label, docs in (("trial 1", a), ("trial 2", b)):
        names = [first_heading(t)[:44] for n, t in docs.items()
                 if "faction" in n]
        for n in names:
            print(f"   {label}: {n}")

    # --- regression: safety -------------------------------------------------
    section("5. Regression -- veil leaks (passages, not verdicts)")
    for label, docs in (("trial 1", a), ("trial 2", b)):
        hits = 0
        for name, text in docs.items():
            for pat, tag in ((CLAUSTRO, "CLAUSTRO"), (GORE, "GORE")):
                for m in re.finditer(pat, text, re.I):
                    hits += 1
                    s = max(0, m.start() - 70)
                    frag = " ".join(text[s:m.end() + 70].split())
                    print(f"   {label} {tag} {name}: ...{frag[:150]}...")
        if not hits:
            print(f"   {label}: no candidate passages")

    # --- regression: label leaks --------------------------------------------
    section("6. Regression -- does any page open with a template label?")
    bad_words = ("overview", "name:", "title", "quest title")
    for label, docs in (("trial 1", a), ("trial 2", b)):
        leaks = [f"{n}: {first_heading(t)}" for n, t in docs.items()
                 if any(w in first_heading(t).lower() for w in bad_words)]
        print(f"   {label}: {leaks if leaks else 'none'}")

    # --- branching ----------------------------------------------------------
    section("7. Branching factor -- stubs implied per entity")
    for label, docs in (("trial 1", a), ("trial 2", b)):
        stubs, typed = 0, {}
        for text in docs.values():
            meta = parse_phenotype_tail(text)
            for s in (meta or {}).get("stubs", []):
                stubs += 1
                t = _resolve_stub_type(s["type"])
                typed[t] = typed.get(t, 0) + 1
        print(f"   {label}: {stubs} stubs / {len(docs)} pages = "
              f"{stubs / max(len(docs), 1):.2f}")
        print(f"            {dict(sorted(typed.items(), key=lambda x: -x[1]))}")

    # --- cross-referencing --------------------------------------------------
    section("8. Regression -- do later pages name earlier entities?")
    for label, docs in (("trial 1", a), ("trial 2", b)):
        names = {n: first_heading(t) for n, t in docs.items()}
        order = list(docs)
        linked = sum(1 for i, n in enumerate(order)
                     if any(names[g] and names[g] in docs[n]
                            for g in order[:i]))
        print(f"   {label}: {linked}/{max(len(order) - 1, 1)} pages reference "
              f"an earlier entity")


if __name__ == "__main__":
    enable_safe_stdout()
    main()
