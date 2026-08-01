"""
Carve a small, self-contained example registry out of a working one.

The working registry is a world in progress: it grows every run, it carries the
full prose of every page, and it belongs to whoever is building that world. The
repository still needs example data — a populated registry is the most useful
thing a stranger can find when trying to get the pipeline running — but it needs
a fixed, curated slice rather than a live world.

Curation is authorial, so selection is by name and nothing is chosen
automatically. The mechanical part is making the result *coherent*: an entity
whose edges point at records that were left behind produces a registry that
loads fine and then breaks every deriver that walks it, so edges to excluded
entities are pruned rather than carried.
"""

from typing import Dict, List, Optional, Set


def resolve_names(registry_data: dict, names: List[str]) -> Dict[str, str]:
    """name -> id, for the requested names. Raises on anything unmatched."""
    records = registry_data.get("records") or {}
    by_name = {}
    for entity_id, record in records.items():
        meta = record.get("stub_metadata") or {}
        label = (record.get("name") or meta.get("name") or "").strip()
        if label:
            by_name.setdefault(label, entity_id)

    resolved, missing = {}, []
    for name in names:
        if name in by_name:
            resolved[name] = by_name[name]
        else:
            missing.append(name)
    if missing:
        raise KeyError("not in the registry: " + ", ".join(sorted(missing)))
    return resolved


def neighbours(registry_data: dict, ids: Set[str]) -> Set[str]:
    """Everything one hop from the given ids, in any relation."""
    edges = registry_data.get("edges") or {}
    out: Set[str] = set()
    for entity_id in ids:
        for items in (edges.get(entity_id) or {}).values():
            for item in items:
                other = item.get("id") if isinstance(item, dict) else item
                if other:
                    out.add(other)
    return out


def build_showcase(registry_data: dict, names: List[str],
                   include_neighbours: bool = False,
                   drop_fields: Optional[Set[str]] = None) -> dict:
    """
    A registry containing only the named entities, with edges made consistent.

    `include_neighbours` pulls in whatever the selection points at, which is
    usually what makes a graph worth looking at — a lone canon page has nothing
    to draw. `drop_fields` can strip heavy or private fields (`phenotype`,
    `summary`) when the point is to show shape rather than content.
    """
    records = registry_data.get("records") or {}
    edges = registry_data.get("edges") or {}

    keep = set(resolve_names(registry_data, names).values())
    if include_neighbours:
        keep |= neighbours(registry_data, keep)
    keep &= set(records)

    out_records = {}
    for entity_id in sorted(keep):
        record = dict(records[entity_id])
        for field in (drop_fields or set()):
            record.pop(field, None)
        # A stub whose source was left behind would point into nothing.
        meta = record.get("stub_metadata")
        if isinstance(meta, dict) and meta.get("source_id") not in keep:
            meta = dict(meta)
            meta["source_id"] = None
            record["stub_metadata"] = meta
        record["tags"] = [t for t in (record.get("tags") or [])
                          if not (t.startswith("from_") and t[5:] not in keep)]
        out_records[entity_id] = record

    out_edges = {}
    for entity_id in sorted(keep):
        relations = edges.get(entity_id) or {}
        pruned = {}
        for relation, items in relations.items():
            surviving = [i for i in items
                         if (i.get("id") if isinstance(i, dict) else i) in keep]
            if surviving:
                pruned[relation] = surviving
        out_edges[entity_id] = pruned

    tag_index: Dict[str, List[str]] = {}
    for entity_id, record in out_records.items():
        for tag in record.get("tags") or []:
            tag_index.setdefault(tag, []).append(entity_id)

    return {
        "records": out_records,
        "edges": out_edges,
        "tag_index": {k: sorted(v) for k, v in sorted(tag_index.items())},
    }


def summarise(showcase: dict) -> dict:
    """Counts for the CLI to print and for tests to assert on."""
    records = showcase["records"]
    types: Dict[str, int] = {}
    prose = 0
    for record in records.values():
        types[record.get("type", "?")] = types.get(record.get("type", "?"), 0) + 1
        prose += len(record.get("phenotype") or "")
    relations = sum(len(items) for rels in showcase["edges"].values()
                    for items in rels.values())
    return {"records": len(records), "edge_items": relations,
            "types": types, "prose_chars": prose}
