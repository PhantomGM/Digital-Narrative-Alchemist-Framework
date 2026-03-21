# QA Audit Report: PF2EDNA Cartridge

**Date:** March 20, 2026
**Target:** `src/rulesets/PF2EDNA`
**Blueprint Specification:** `ruleset_ingestion_blueprint.md` ($1.0)

---

## 1. Structural Audit (Phase 1)
**Status:** 🟡 PARTIAL PASS

The cartridge successfully implements the required directory structure, but contains extra builder artifacts that should be cleaned up.

| Check | Status | Notes |
|:---|:---|:---|
| Required Directories (`resolvers/`, `data/`, `knowledge/`) | ✅ PASS | All present and populated. |
| `arbiter.py` Exists | ✅ PASS | Present at root. |
| `manifest.json` Exists | ✅ PASS | Present at root. |
| Extraneous Files | ⚠️ WARN | Found `extract_dbs.py` and `extract_simple.py`. These builder scripts should not be shipped in the runtime cartridge. |

---

## 2. API & Interface Contract Audit
**Status:** ✅ PASS

The integration boundary between the DNA framework and the Layer IV cartridge is fully functional.

| Check | Status | Notes |
|:---|:---|:---|
| `GameSystemArbiter` implemented | ✅ PASS | Correctly defined in `arbiter.py`. |
| `resolve_action()` signature | ✅ PASS | Implemented and routing correctly. |
| `query_data()` signature | ✅ PASS | Implemented with basic JSON/SQLite driver logic. |
| `get_knowledge()` signature | ✅ PASS | Implemented. |
| Lazy-loaded resolvers (I-01) | ✅ PASS | Used `importlib` in `_get_resolver()` to prevent load latency. |
| Smoke Tests included (R-05) | ✅ PASS | Base smoke tests present in `arbiter.py` and `resolvers/combat.py`. |

---

## 3. Schema & Modality Audit (Phases 2 & 3)
**Status:** 🔴 FAIL

The cartridge largely respects the 3-tier data separation (Semantic vs Tabular vs Executable) but fails strict YAML/JSON schema validation defined in the blueprint.

### manifest.json Violations
1. **Missing Required Fields (§4):** `author` and `description` are missing.
2. **Capability Structure Mismatch:** Blueprint §4 requires a dictionary of booleans (e.g., `"combat_resolution": true`). The PF2EDNA manifest provides a `list` of strings.
3. **Knowledge Files Structure Mismatch:** Blueprint §4 requires a list of path strings (e.g., `["knowledge/lore.md"]`). The PF2EDNA manifest provides a `dict` mapping topics to paths.

### Integration Rule Violations
1. **SQLite _meta Table (T-07):** Needs verification — `data/spells.db`, `items.db`, and `monsters.db` must contain a `_meta` table with `schema_version` and `source_system`.

### Successes
* **Resolver Purity (R-01/R-02):** Resolvers are pure functions with no LLM calls (verified in `combat.py`).
* **ID Normalization (T-01):** JSON databases use correct `snake_case` IDs (verified in `classes.json`).
* **Semantic Purity (P-05):** Markdown files contain pure flavor/guidance without execution logic (verified in `roleplay_rules.md`).

---

## Remediation Plan

To achieve Minimum Viable Cartridge (MVC) compliance and authorize deployment, the following fixes are required:

1. **Delete extraneous builder scripts:** Remove `extract_dbs.py` and `extract_simple.py` from the cartridge directory.
2. **Fix `manifest.json`:**
   - Add `author` and `description` fields.
   - Refactor the `capabilities` array into a dictionary of boolean flags.
   - Update `arbiter.py` (if necessary) to handle `knowledge_files` as a list of strings instead of a dict, or update the blueprint to accept a dict (which is actually a better design for `get_knowledge(topic)` routing).
3. **Verify SQLite Schemas:** Ensure `_meta` tables exist in all `.db` files per rule `T-07`.

**Authorization:** Deployment DENIED pending remediation of `manifest.json` schema violations.
