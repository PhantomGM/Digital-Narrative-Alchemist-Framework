---
tags: [system, metadata, rules, core]
entity_type: system_doc
version: "1.0"
related_docs:
  - "[[DNA_System_Rules]]"
  - "[[Conductor_Routing]]"
  - "[[_99_Templates_and_Patterns_Index]]"
---

# Metadata Priority Logic

> The rules governing data persistence, inheritance, conflict resolution, and multidirectional world-building within the [[_00_Admin_and_Indexes_Index|World Bible]].

---

## Data Source Priority Hierarchy

When generating or updating content, the system validates data sources in this **strict, inviolable order**:

| Priority | Source | Description |
|:---------|:-------|:------------|
| **1 (Highest)** | Manual GM Entry | Any detail explicitly written by the Game Master |
| **2** | Added Context | Vault notes, session logs, or context injected at generation time |
| **3** | Parent Metadata | Inherited constraints from parent entities (e.g., Region → Settlement) |
| **4** | DNA String | The procedurally generated alphanumeric code |
| **5 (Lowest)** | Model Baseline | Standard LLM knowledge and defaults |

> [!IMPORTANT]
> User-added context that overlaps with a DNA trait **always overrides** the encoded numerical value. The same DNA string can be decoded multiple times under different contextual lenses, producing different narratives while adhering to the same mathematical parameters.

---

## The Triple-File Pattern

Every generated entity in the World Bible is represented by up to three interconnected files:

### 1. Narrative Profile (`.md`)

The human-readable, formatted Obsidian note with YAML frontmatter and `[[wiki-links]]`.

```yaml
---
tags: [faction, generated]
entity_type: Faction
dna_version: "1.0"
parent_entity: "[[Region_The_Shattered_Coast]]"
created: 2026-02-24
status: complete
---
```

### 2. DNA Data (`.dna.json`)

Stores the raw algorithmic DNA string that generated this entity.

```json
{
    "entity_type": "Faction",
    "entity_name": "The Ledger of Flame",
    "dna_version": "1.0",
    "dna_string": "T3-G05-M6-P4-S2-O5-N92-L05-F5-D5-A6-SC2-MZ3-X4",
    "generated_date": "2026-02-24",
    "generator_used": "generator_faction.py",
    "gm_context_at_generation": "Dark fantasy setting, coastal region with pirate activity"
}
```

### 3. Metadata Tracker (`.meta.json`)

Tracks inherited data, child-pushed data, field locks, and incomplete fields.

```json
{
    "entity_type": "Faction",
    "dna_locked_fields": ["faction_type", "primary_goal", "alignment"],
    "gm_locked_fields": [],
    "inherited_from_parent": {
        "dominant_threat": "pirate_activity",
        "region": "The Shattered Coast"
    },
    "pushed_from_child": {},
    "incomplete_fields": ["headquarters_location", "member_count"],
    "field_lock_log": [
        {
            "field": "faction_type",
            "locked_by": "dna",
            "value": "Criminal Syndicate",
            "timestamp": "2026-02-24"
        }
    ]
}
```

---

## Thin Parent Architecture

The **Thin Parent** rule enables multidirectional world-building — top-down, bottom-up, or middle-out — without introducing logical paradoxes.

### Top-Down Flow

When a **parent entity is generated first** (e.g., running the World Generator):

1. The generator populates the parent directories (`01_*`, `02_*`)
2. It simultaneously pre-creates **thin `.meta.json` files** for child entities that don't yet exist
3. These thin files lock in macro-level constraints (baseline climate, dominant threats, etc.)
4. They generate lists of `incomplete_fields` awaiting future generation

```
World Generated
├── 01_Foundation/ → populated
├── 02_Geography/ → populated
│   ├── Region_North.meta.json → thin file (climate locked, threats locked)
│   ├── Region_South.meta.json → thin file (climate locked, threats locked)
│   └── ...
```

### Bottom-Up Flow (Upward Push)

When a **child entity is generated first** (e.g., creating a Settlement before its Region):

1. The child's DNA defines local attributes (e.g., `pirate_activity` as primary threat)
2. The system checks the parent's `.meta.json`
3. If the relevant field in the parent is **empty**, the child pushes its data upward
4. The parent's field is **locked** with the child's value

### The First Child Wins Protocol

> [!CAUTION]
> **First Child Wins**: If a parent field is undefined, the first child entity to define it **claims it permanently**. All subsequent children in that parent's scope must acknowledge and integrate the claimed value.

| Scenario | Outcome |
|:---------|:--------|
| Parent field is **empty** + Child defines it | Child's value is pushed up and **locked** |
| Parent field is **locked by DNA** | Child **cannot** overwrite — must integrate |
| Parent field is **locked by GM** | Child **cannot** overwrite — highest priority |
| Parent field is **locked by earlier child** | Child **cannot** overwrite — must acknowledge |

### Middle-Out Flow

A creator can start anywhere in the hierarchy:

1. Generate a Settlement (middle tier)
2. It pushes constraints upward to its Region (which may not exist yet → thin `.meta.json` created)
3. It pushes constraints downward to child entities like Establishments or NPCs
4. Subsequent generation in the same scope inherits all locked fields

---

## Field Locking Rules

Fields can be locked by three sources, listed in priority order:

| Lock Source | Priority | Can Be Overridden By |
|:------------|:---------|:---------------------|
| GM Entry | Highest | Nothing (absolute) |
| Parent Metadata | High | GM Entry only |
| DNA String | Standard | GM Entry or Parent Metadata |
| Child Push | Standard | GM Entry or Parent Metadata |

### Lock Log

Every field lock is recorded in the `.meta.json` file's `field_lock_log` array:

```json
{
    "field": "dominant_threat",
    "locked_by": "child_push",
    "source_entity": "Settlement_Blackwater_Port",
    "value": "pirate_activity",
    "timestamp": "2026-02-24"
}
```

---

## Override Logic

The same DNA string can produce **different narrative outputs** when decoded under different contexts:

1. **First decode** — Pure DNA interpretation (no context)
2. **Re-decode with GM context** — GM adds "this region has been recently conquered" → the decoder re-interprets political and conflict blocks accordingly
3. **Re-decode with vault context** — The decoder reads related `[[wiki-linked]]` notes and adjusts for established canon

> [!NOTE]
> Override never changes the underlying `.dna.json`. It only affects the narrative `.md` output. The DNA string remains the mathematical truth; context shapes its expression.

---

## Directory-Entity Mapping

| Entity Type | Primary Directory | Parent Relationship |
|:------------|:-----------------|:-------------------|
| World | [[_01_Foundation_and_Cosmology_Index]] | None (root) |
| Region | [[_02_Geography_and_Environment_Index]] | World |
| Settlement | [[_03_Polities_and_Cultures_Index]] | Region |
| Faction | [[_04_Factions_Organizations_Religions_Index]] | Region or Settlement |
| Species | [[_05_Creatures_Species_Lineages_Index]] | World |
| Magic System | [[_06_Magic_Science_Technology_Index]] | World |
| Historical Event | [[_07_History_Timeline_Legends_Index]] | World or Region |
| NPC | [[_08_Adventure_Content_Index]] | Settlement, Faction, or Quest |
| Quest | [[_08_Adventure_Content_Index]] | Region or Settlement |
| Item | [[_07_History_Timeline_Legends_Index]] | Any (creator, faction, location) |
| Travel | [[_08_Adventure_Content_Index]] | Region |

---

## Related Documents

- [[DNA_System_Rules]] — Generation pipeline, narrative mandates, Resolution Engine
- [[Conductor_Routing]] — Intent routing and content type mapping
- [[Template_DNA_JSON]] — Standard `.dna.json` schema
- [[Template_Meta_JSON]] — Standard `.meta.json` schema

## Related Entities
- [[Template_World]]
- [[Template_Travel]]
- [[Template_Settlement]]
- [[Template_Region]]
- [[Template_Quest]]
- [[Template_NPC]]
- [[Template_Item]]
- [[Template_Faction]]

- [[Entity_Master_Index]]
