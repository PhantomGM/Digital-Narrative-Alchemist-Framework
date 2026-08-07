# Third-party rules content — licence notices

**Status: resolved by untracking.** `data/` is no longer in this repository —
it is gitignored, so nothing here redistributes Paizo's content. The notices
below are kept for anyone who supplies their own copy of the data, and for the
record of why it was removed.

`src/layer4_rules/PF2EDNA/data/` contains rules content from Pathfinder Second
Edition, owned by Paizo Inc. Neither the framework's PolyForm Noncommercial
licence nor the CC BY-NC covering the example world applies to it, and the author
of this repository cannot grant rights to it.

The content is not merely mechanical. `conditions.json` carries Paizo's prose
verbatim ("You can't see. All normal terrain is difficult terrain to you…"), with
`compendium/` cross-links showing it was extracted from a third-party Obsidian
compendium that was itself redistributing Paizo's text.

---

## ORC License Notice

> This product is licensed under the ORC License to be held in the Library of
> Congress and available online at various locations including
> paizo.com/orclicense, azoralaw.com/orclicense, and others. All warranties are
> disclaimed as set forth therein.

## Trademark Notice

> Paizo, the Paizo golem, Pathfinder, Starfinder, and other trademarks owned by
> Paizo are property of Paizo Inc. All rights reserved.

## Attribution Notice

**This section is incomplete and must be completed before this content is
relied upon as properly licensed.**

The ORC License requires a notice identifying *each* Licensor or creator of the
Licensed Material actually used, including upstream licensors. That means naming
the specific Paizo works the data came from — for example:

> Pathfinder Player Core © 2023 Paizo Inc. Designed by Logan Bonner, Jason
> Bulmahn, Stephen Radney-MacFarland, and Mark Seifter. Authors: …

…with a full entry per work used, plus a credit line for the intermediate
compendium this data was extracted from.

**Nothing in this repository records which works these are.** The data files
carry no `source` field, no book reference, and no licence header. That
information exists only wherever the original Obsidian compendium came from.

---

## What is unresolved

### 1. Which licence applies is genuinely ambiguous

Pathfinder 2e content splits at the 2023 Remaster:

* **Pre-Remaster (legacy)** content is licensed under the **OGL 1.0a**.
* **Remaster** content is licensed under the **ORC License**.

The two require *different notices*. A scan of `data/` finds terminology from
**both**:

| Marker | Occurrences | Indicates |
| :--- | ---: | :--- |
| `Flat-Footed` | 24 | **Legacy** — the Remaster renamed this *Off-Guard* |
| `Evil` (alignment) | 1 | **Legacy** — the Remaster removed alignment |
| `ancestry` | 29 | Remaster |
| `Holy` / `Unholy` / `Void` | 5 | Remaster — replaced alignment damage |
| `races.json` (filename) | — | Legacy — the Remaster renamed races to ancestries |

So the corpus is mixed, and the ORC notice above may be the wrong instrument for
part of it. Applying an ORC notice to OGL-licensed legacy content would be an
inaccurate legal statement, which is worse than having no notice at all.

### 2. What has to happen

Only the author can resolve this, because it turns on where the source compendium
came from:

1. **Identify the source.** Which Obsidian PF2e compendium was `data/` extracted
   from, and what licence notice did *it* carry? That notice names the upstream
   works and is the thing to reproduce here.
2. **Decide the licence path** — ORC, OGL 1.0a, both, or Paizo's Community Use
   Policy (which is noncommercial and would sit comfortably with this project's
   own noncommercial licence, but has its own separate requirements).
3. **Complete the Attribution Notice above** with the actual work list.
4. If the ORC path is chosen, the **full ORC License text** must accompany the
   work, not just the notice. It is available at paizo.com/orclicense.

### 3. What was done

`data/` is **gitignored and untracked** as of `4fd7183`. Ten files left the
repository; none were deleted locally.

This cartridge is a test fixture, not a product dependency — it exists to prove
the rules layer hot-swaps between a trivial system (`coin_flip`), a rules-light
one (`one_page_5e`) and a detailed one. Nothing requires the detailed one to be
Pathfinder, and nothing requires the data to be published. Untracking removes the
redistribution question without touching the architecture: `resolvers/` is
original code, and **the full suite passes with `data/` absent** — verified by
moving it aside and running all 1026 tests, which is why this was preferable to
guessing at a notice.

**Untracking does not unpublish.** The files remain in the history of earlier
commits. This stops the accrual; it does not undo it.

**To use the data-backed paths**, place your own copy in `data/`. The resolvers
expect the filenames listed in `manifest.json`. If you then redistribute, the
notices above become your responsibility and §1 is still unanswered.

---

*Not legal advice. This file records what was verified from the repository's own
contents and from Paizo's published licence terms; the determination in §1 needs
a human who knows the data's provenance.*
