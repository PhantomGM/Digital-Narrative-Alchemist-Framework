# Trial 6 — the first world whose names obey its own language

Run 2026-08-08. Identical machinery to trial 5 with one addition: the harness now
populates `ContextPackage.naming` and `roster` from the live registry, so the
language generated at slot 3 reaches all fourteen entities after it. Trials 1
through 5 generated a language and discarded it — see PROJECT_STATE §5, which had
already recorded and fixed this failure one layer down.

17 entities, contract satisfied, 46 stubs implied, 45 ghosted, 1 deferred.

---

## The result

| | Trial 5 (naming discarded) | Trial 6 (naming live) |
| :--- | :--- | :--- |
| World | The Gilded Shiver | The Vesper Reach |
| Language | The Resonant Utterance | **Vesper Cant** |
| Station | Tether-End | Drift-Lock Four |
| Route | The Iron Ribbon | The Cold-Drift Bypass |
| Galley | The Butter-Burner | The Salt-Vent Galley |
| Factions | Sovereign Reclamation Trust · Threshold Concord · Ribbon-Way Consortium | Vault-Strip **Line** · Choke-Weld **Line** · Gate-Tally **Guild** |
| Crew | Kaelen Vance · Sariel Finch · Bess "The Barnacle" Marrow | **Brak-Tally · Vex-Seam · Tor-Vane** |

Trial 5's names are a mishmash — a hyphenated station, a Latinate corporate
triple, and three generic fantasy forename-surnames. Trial 6 is a system.

**Conventions the world invented and then kept:**

* Personal names are a monosyllabic root plus a trade or lineage tag: *Brak-Tally*,
  *Vex-Seam*, *Tor-Vane*.
* Places carry a numeric sector designation: *Grave-Span **Nine***, *Drift-Lock
  **Four***, *Iron-Vent **Eight***.
* Factions take `-Line` or `Guild`.
* Roots recur across unrelated entities — *Vesper* in the world and the language,
  *Grave-* in the corridor and the creature, *-Vent* in the hulk and the galley.

**Zero model-default names.** No Kaelen, Vance, Lyra, Seraphina or Rian anywhere
in seventeen pages. "Kaelen" had appeared in trial 1, trial 5 and four of seven
NPC alignment tests; §5 records the same defaults surfacing as Vane ×3 and Lyra ×2
across five worlds. The block suppresses them completely.

## What still leaks

**One verbatim reuse in sixteen.** The station is named **Drift-Lock Four**, which
is location example #4 in its own naming block — an illustrative name promoted to
an entity, three lines below a disclaimer forbidding exactly that. §5 records this
failure mode as `Scribe Veris Thal`.

It is much reduced rather than fixed. Wiring `naming` alone produced reuse on the
first NPC tested (1 of 1, "Rian"); adding `roster` took it to 1 of 16. The roster
lists names already spent, and example names are not entities, so they are not on
it. The obvious next move is to put them there — mark the demonstrations as
unavailable rather than trusting a sentence that asks nicely.

Root-sharing is **not** a defect and should not be fixed: *Brak-Tally* from
*Brak-Sera*, *Vex-Seam* from *Vex-Thorne*, `-Line` and `-Vent` and `Guild` recurring
throughout. Morphemes recur in real languages, and "build new names in their style"
invites precisely this.

## A new question the fix raises

**All seventeen names are hyphenated compounds**, and that uniformity originates in
the language rather than in its application: the linguistic decoder specified
compound construction for *all three* name classes, so a world obeying it faithfully
comes out monotone. Trial 5's variety was the variety of having no rules at all.

That is a `linguistic` decoder question rather than a naming-pipeline one — a
richer language would differentiate its classes, giving people one construction,
places another, institutions a third. Worth noting that `linguistic` is one of the
fourteen decoders that has never had a refinement pass.

## Cost

Decode times roughly doubled — 120–157s against trial 5's 55–90s — because the
naming block and roster add four to five thousand characters to every prompt. The
branching factor came in at **2.71** against trial 5's 2.88 and trial 2's 3.81,
which is three points now trending the same direction but still three points.
