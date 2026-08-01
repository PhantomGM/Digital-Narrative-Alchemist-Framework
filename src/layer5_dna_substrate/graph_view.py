"""
Render the registry as an interactive knowledge graph.

The registry has always been a graph: entities with types and gists, joined by
labelled edges the generator recorded as it built the world. Nothing here is
inferred and no model is called — every node and edge is something the pipeline
wrote down at the time, which is why this is a deriver rather than an extraction.

Two facts about the edge store shape it, and both are easy to get wrong:

  * `peer` edges are stored on BOTH endpoints, so the 212 peer entries are ~106
    relationships. They must be de-duplicated or every link is drawn twice.
  * containment is counter-intuitive. link_elements(A, B, "parent") means A is the
    parent OF B, and is stored as edges[A]["parent"] = [B]. So edges[X]["parent"]
    lists what X *contains*, and edges[X]["child"] lists X's containers.
"""

import html
import json
from datetime import date
from typing import Dict, List, Optional

# One colour per type. Types absent from the world simply never appear.
TYPE_COLOURS = {
    "npc": "#e8825a", "faction": "#c2536a", "culture": "#b5739e",
    "creature": "#7d9a4f", "item": "#d9a842", "text": "#6ba3c4",
    "lore": "#8a7fc4", "chronicle": "#8c8378", "linguistic": "#5fa8a0",
    "location": "#4f8fc0", "settlement": "#5aa6d4", "region": "#3d7ba8",
    "realm": "#2f6690", "regional_poi": "#6fb3d9", "establishment": "#8ec6e6",
    "wonder": "#d4b25f", "travel": "#9db8c9", "world": "#c9a86a",
    "trap": "#a85c5c", "quest": "#a8875c", "system": "#7a9e8f",
    "agency": "#b0607f", "deity": "#d9c76a",
}
DEFAULT_COLOUR = "#8892a0"


def _status_of(record: dict) -> str:
    tags = record.get("tags") or []
    if "stub" in tags:
        return "stub"
    if "canonized" in tags:
        return "canon"
    return "draft"


def build_graph(registry_data: dict) -> Dict[str, List[dict]]:
    """
    Turn a saved registry into {"nodes": [...], "edges": [...]}.

    Pure and deterministic: same registry in, same graph out, so the rendered
    page can be regenerated without drifting.
    """
    records = registry_data.get("records") or {}
    edge_store = registry_data.get("edges") or {}

    nodes = []
    for entity_id, record in sorted(records.items(), key=lambda kv: kv[0]):
        meta = record.get("stub_metadata") or {}
        name = (record.get("name") or meta.get("name") or "").strip()
        if not name:
            name = f"{record.get('type', 'entity')} (unnamed)"
        nodes.append({
            "id": entity_id,
            "name": name,
            "type": record.get("type") or "unknown",
            "status": _status_of(record),
            "gist": (record.get("gist") or meta.get("description") or "").strip(),
            "audit": (record.get("audit") or {}).get("status", "") if isinstance(
                record.get("audit"), dict) else "",
        })

    known = {n["id"] for n in nodes}
    seen = set()
    edges = []

    def add(source: str, target: str, label: str, kind: str) -> None:
        if source not in known or target not in known or source == target:
            return
        # Peers are recorded on both endpoints; collapse to one undirected edge.
        key = (kind, *sorted((source, target))) if kind == "peer" else (kind, source, target)
        if key in seen:
            return
        seen.add(key)
        edges.append({"source": source, "target": target,
                      "label": label or kind, "kind": kind})

    for entity_id, relations in sorted(edge_store.items()):
        for item in relations.get("parent", []):
            # edges[X]["parent"] holds what X CONTAINS — see module docstring.
            add(entity_id, item.get("id"), item.get("label", "contains"), "contains")
        for item in relations.get("peer", []):
            add(entity_id, item.get("id"), item.get("label", "related"), "peer")

    degree = {n["id"]: 0 for n in nodes}
    for edge in edges:
        degree[edge["source"]] += 1
        degree[edge["target"]] += 1
    for node in nodes:
        node["degree"] = degree[node["id"]]

    return {"nodes": nodes, "edges": edges}


def _payload(graph: dict) -> str:
    """JSON safe to embed in a <script> block."""
    raw = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    return raw.replace("</", "<\\/")


def render_html(graph: dict, title: str = "World Graph",
                subtitle: Optional[str] = None) -> str:
    """A self-contained page: no CDN, no fonts, no network of any kind."""
    counts: Dict[str, int] = {}
    for node in graph["nodes"]:
        counts[node["type"]] = counts.get(node["type"], 0) + 1
    legend = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    colours = {t: TYPE_COLOURS.get(t, DEFAULT_COLOUR) for t in counts}
    stats = (f"{len(graph['nodes'])} entities · {len(graph['edges'])} relationships · "
             f"{sum(1 for n in graph['nodes'] if n['status'] == 'canon')} canon · "
             f"{sum(1 for n in graph['nodes'] if n['status'] == 'stub')} unmade")

    filters = "\n".join(
        f'<label class="f"><input type="checkbox" checked data-type="{html.escape(t)}">'
        f'<span class="sw" style="background:{colours[t]}"></span>'
        f'{html.escape(t)} <em>{n}</em></label>'
        for t, n in legend)

    return f"""<!doctype html>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#12141a; color:#d8dce4;
         font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; overflow:hidden; }}
  #wrap {{ display:flex; height:100vh; }}
  #side {{ width:290px; flex:0 0 290px; padding:16px; overflow-y:auto;
           background:#171a21; border-right:1px solid #262b36; }}
  h1 {{ font-size:16px; margin:0 0 4px; }}
  .sub {{ color:#8b93a3; font-size:12px; margin:0 0 14px; }}
  h2 {{ font-size:11px; text-transform:uppercase; letter-spacing:.08em;
        color:#7d8698; margin:18px 0 8px; }}
  input[type=search] {{ width:100%; padding:7px 9px; background:#0f1116;
        border:1px solid #2b3140; border-radius:5px; color:#d8dce4; }}
  .f {{ display:flex; align-items:center; gap:7px; padding:2px 0;
        font-size:12.5px; cursor:pointer; }}
  .f em {{ color:#6d7688; font-style:normal; margin-left:auto; }}
  .sw {{ width:10px; height:10px; border-radius:2px; flex:0 0 10px; }}
  #detail {{ margin-top:6px; font-size:12.5px; }}
  #detail .n {{ font-size:15px; font-weight:600; color:#fff; }}
  #detail .m {{ color:#8b93a3; margin:2px 0 8px; }}
  #detail .g {{ color:#c3c9d4; }}
  #detail ul {{ list-style:none; padding:0; margin:10px 0 0; }}
  #detail li {{ padding:3px 0; border-top:1px solid #232833; cursor:pointer; }}
  #detail li:hover {{ color:#fff; }}
  #detail .rel {{ color:#6d7688; font-size:11px; }}
  button {{ margin-top:12px; width:100%; padding:6px; background:#222833;
            border:1px solid #313847; border-radius:5px; color:#c3c9d4;
            font-size:12px; cursor:pointer; }}
  button:hover {{ background:#2a3140; color:#fff; }}
  canvas {{ flex:1; min-width:0; display:block; cursor:grab; }}
  .hint {{ color:#5f6878; font-size:11px; margin-top:14px; }}
</style>
<div id="wrap">
  <div id="side">
    <h1>{html.escape(title)}</h1>
    <p class="sub">{html.escape(subtitle or stats)}</p>
    <input type="search" id="q" placeholder="Search entities…">
    <h2>Types</h2>
    {filters}
    <h2>Status</h2>
    <label class="f"><input type="checkbox" id="onlyCanon"> canon only</label>
    <label class="f"><input type="checkbox" id="hideStubs"> hide unmade stubs</label>
    <h2>Selected</h2>
    <div id="detail"><span class="sub">Click a node.</span></div>
    <button id="fit">Fit to view</button>
    <p class="hint">Drag to pan · scroll to zoom · drag a node to pin it,
       double-click to release</p>
  </div>
  <canvas id="c"></canvas>
</div>
<script>
const DATA = {_payload(graph)};
const COLOURS = {json.dumps(colours)};
const DEFAULT_COLOUR = {json.dumps(DEFAULT_COLOUR)};

const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const byId = new Map(DATA.nodes.map(n => [n.id, n]));
DATA.edges.forEach(e => {{ e.s = byId.get(e.source); e.t = byId.get(e.target); }});

// CW/CH are CSS pixels -- the coordinate space everything else works in. The
// backing store is scaled by devicePixelRatio only so the render is not blurry.
let W = 0, H = 0, CW = 0, CH = 0;
function resize() {{
  const r = cv.getBoundingClientRect();
  CW = r.width; CH = r.height;
  W = cv.width = CW * devicePixelRatio; H = cv.height = CH * devicePixelRatio;
  ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
}}
addEventListener('resize', () => {{ resize(); fit(); }});

// deterministic start positions so the layout settles the same way each open
let seed = 7;
const rnd = () => (seed = seed * 1103515245 % 2147483647) / 2147483647;
DATA.nodes.forEach(n => {{
  n.x = 400 + (rnd() - .5) * 600; n.y = 300 + (rnd() - .5) * 500;
  n.vx = n.vy = 0; n.r = 4 + Math.min(11, Math.sqrt(n.degree) * 2.4);
}});

const state = {{ hidden: new Set(), canonOnly: false, hideStubs: false,
                 q: '', sel: null, pan: {{x:0,y:0}}, zoom: 1 }};

const visible = n => !state.hidden.has(n.type)
  && !(state.canonOnly && n.status !== 'canon')
  && !(state.hideStubs && n.status === 'stub');

function tick() {{
  const nodes = DATA.nodes.filter(visible);
  // repulsion
  for (let i = 0; i < nodes.length; i++) {{
    const a = nodes[i];
    for (let j = i + 1; j < nodes.length; j++) {{
      const b = nodes[j];
      let dx = b.x - a.x, dy = b.y - a.y, d2 = dx*dx + dy*dy || 1;
      if (d2 > 90000) continue;
      const f = 900 / d2, d = Math.sqrt(d2);
      const fx = dx / d * f, fy = dy / d * f;
      a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy;
    }}
  }}
  // springs
  for (const e of DATA.edges) {{
    if (!visible(e.s) || !visible(e.t)) continue;
    const dx = e.t.x - e.s.x, dy = e.t.y - e.s.y;
    const d = Math.hypot(dx, dy) || 1, f = (d - 90) * 0.006;
    const fx = dx / d * f, fy = dy / d * f;
    e.s.vx += fx; e.s.vy += fy; e.t.vx -= fx; e.t.vy -= fy;
  }}
  const cx = CW / 2, cy = CH / 2;
  for (const n of nodes) {{
    if (n.pinned) {{ n.vx = n.vy = 0; continue; }}
    n.vx += (cx - n.x) * 0.0016; n.vy += (cy - n.y) * 0.0016;
    n.vx *= 0.86; n.vy *= 0.86;
    n.x += n.vx; n.y += n.vy;
  }}
}}

function draw() {{
  ctx.clearRect(0, 0, W, H);
  ctx.save();
  ctx.translate(state.pan.x, state.pan.y); ctx.scale(state.zoom, state.zoom);
  const q = state.q.toLowerCase();
  const match = n => q && n.name.toLowerCase().includes(q);

  for (const e of DATA.edges) {{
    if (!visible(e.s) || !visible(e.t)) continue;
    const hot = state.sel && (e.s.id === state.sel.id || e.t.id === state.sel.id);
    ctx.strokeStyle = hot ? 'rgba(220,228,240,.55)' : 'rgba(150,162,180,.13)';
    ctx.lineWidth = hot ? 1.4 : (e.kind === 'contains' ? 1.1 : .7);
    ctx.beginPath(); ctx.moveTo(e.s.x, e.s.y); ctx.lineTo(e.t.x, e.t.y); ctx.stroke();
  }}
  for (const n of DATA.nodes) {{
    if (!visible(n)) continue;
    const col = COLOURS[n.type] || DEFAULT_COLOUR;
    const on = !q || match(n);
    ctx.globalAlpha = on ? 1 : .18;
    ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, 6.284);
    if (n.status === 'stub') {{
      ctx.strokeStyle = col; ctx.lineWidth = 1.6; ctx.setLineDash([3,2]);
      ctx.stroke(); ctx.setLineDash([]);
    }} else {{
      ctx.fillStyle = col; ctx.fill();
      if (n.status === 'canon') {{
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.4; ctx.stroke();
      }}
    }}
    if (state.sel && state.sel.id === n.id) {{
      ctx.beginPath(); ctx.arc(n.x, n.y, n.r + 4, 0, 6.284);
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.stroke();
    }}
    if (n.r > 7 || match(n) || (state.sel && state.sel.id === n.id)) {{
      ctx.fillStyle = '#e6eaf1'; ctx.font = '11px sans-serif';
      ctx.fillText(n.name, n.x + n.r + 4, n.y + 3.5);
    }}
    ctx.globalAlpha = 1;
  }}
  ctx.restore();
}}

// Frame the visible graph. Without this the view depends on the window matching
// whatever size the layout happened to settle at, and a narrow pane shows nothing.
function fit() {{
  const nodes = DATA.nodes.filter(visible);
  if (!nodes.length || !CW) return;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const n of nodes) {{
    x0 = Math.min(x0, n.x - n.r); y0 = Math.min(y0, n.y - n.r);
    x1 = Math.max(x1, n.x + n.r); y1 = Math.max(y1, n.y + n.r);
  }}
  const pad = 40;
  const k = Math.min((CW - pad * 2) / Math.max(1, x1 - x0),
                     (CH - pad * 2) / Math.max(1, y1 - y0));
  state.zoom = Math.max(0.12, Math.min(2.2, k));
  state.pan.x = CW / 2 - (x0 + x1) / 2 * state.zoom;
  state.pan.y = CH / 2 - (y0 + y1) / 2 * state.zoom;
}}

let frame = 0;
function loop() {{
  tick(); draw();
  // Refit while the layout is still spreading, then leave the view to the user.
  if (++frame < 240 && frame % 20 === 0) fit();
  requestAnimationFrame(loop);
}}

// Labels are stored as the generator wrote them ("mentions_Ash_Wastes"). The data
// stays verbatim; only the reading copy is unpicked.
const pretty = s => s.replace(/_/g, ' ');

function select(n) {{
  state.sel = n;
  const d = document.getElementById('detail');
  if (!n) {{ d.innerHTML = '<span class="sub">Click a node.</span>'; return; }}
  const links = DATA.edges
    .filter(e => e.source === n.id || e.target === n.id)
    .map(e => {{ const o = e.source === n.id ? e.t : e.s;
                 return {{o, label: e.label}}; }})
    .filter(x => x.o && visible(x.o));
  d.innerHTML =
    '<div class="n"></div><div class="m"></div><div class="g"></div>' +
    '<ul></ul>';
  d.querySelector('.n').textContent = n.name;
  d.querySelector('.m').textContent =
    n.type + ' · ' + n.status + (n.audit ? ' · ' + n.audit : '') +
    ' · ' + links.length + ' link' + (links.length === 1 ? '' : 's');
  d.querySelector('.g').textContent = n.gist || '(no gist recorded)';
  const ul = d.querySelector('ul');
  for (const x of links) {{
    const li = document.createElement('li');
    li.textContent = x.o.name;
    const s = document.createElement('div');
    s.className = 'rel'; s.textContent = pretty(x.label);
    li.appendChild(s);
    li.onclick = () => select(x.o);
    ul.appendChild(li);
  }}
}}

function at(mx, my) {{
  const x = (mx - state.pan.x) / state.zoom, y = (my - state.pan.y) / state.zoom;
  let best = null, bd = 1e9;
  for (const n of DATA.nodes) {{
    if (!visible(n)) continue;
    const d = Math.hypot(n.x - x, n.y - y);
    if (d < n.r + 6 && d < bd) {{ bd = d; best = n; }}
  }}
  return best;
}}

let drag = null, panning = false, last = null;
cv.addEventListener('mousedown', ev => {{
  const r = cv.getBoundingClientRect();
  const n = at(ev.clientX - r.left, ev.clientY - r.top);
  if (n) {{ drag = n; n.pinned = true; select(n); }}
  else {{ panning = true; last = [ev.clientX, ev.clientY]; select(null); }}
}});
addEventListener('mousemove', ev => {{
  const r = cv.getBoundingClientRect();
  if (drag) {{
    drag.x = (ev.clientX - r.left - state.pan.x) / state.zoom;
    drag.y = (ev.clientY - r.top - state.pan.y) / state.zoom;
  }} else if (panning) {{
    state.pan.x += ev.clientX - last[0]; state.pan.y += ev.clientY - last[1];
    last = [ev.clientX, ev.clientY];
  }}
}});
addEventListener('mouseup', () => {{ drag = null; panning = false; }});
cv.addEventListener('dblclick', ev => {{
  const r = cv.getBoundingClientRect();
  const n = at(ev.clientX - r.left, ev.clientY - r.top);
  if (n) n.pinned = false;
}});
cv.addEventListener('wheel', ev => {{
  ev.preventDefault();
  const k = ev.deltaY < 0 ? 1.12 : 1 / 1.12;
  const r = cv.getBoundingClientRect();
  const mx = ev.clientX - r.left, my = ev.clientY - r.top;
  state.pan.x = mx - (mx - state.pan.x) * k;
  state.pan.y = my - (my - state.pan.y) * k;
  state.zoom *= k;
}}, {{passive:false}});

document.querySelectorAll('[data-type]').forEach(cb => cb.onchange = () => {{
  cb.checked ? state.hidden.delete(cb.dataset.type)
             : state.hidden.add(cb.dataset.type);
  frame = 0;  // let the layout resettle and refit around what is left
}});
document.getElementById('onlyCanon').onchange = e => {{
  state.canonOnly = e.target.checked; frame = 0;
}};
document.getElementById('hideStubs').onchange = e => {{
  state.hideStubs = e.target.checked; frame = 0;
}};
document.getElementById('q').oninput = e => state.q = e.target.value.trim();
document.getElementById('fit').onclick = () => fit();

// Settle the layout before the first paint so the graph opens framed rather
// than as a ball at the centre that slowly unfolds.
resize();
for (let i = 0; i < 120; i++) tick();
fit();
loop();
</script>
"""


def write_html(registry_data: dict, out_path: str, title: str = "World Graph") -> dict:
    """Build and write the page. Returns a small report."""
    graph = build_graph(registry_data)
    subtitle = (f"{len(graph['nodes'])} entities · {len(graph['edges'])} relationships · "
                f"derived from the DNA registry, {date.today().isoformat()}")
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_html(graph, title=title, subtitle=subtitle))
    return {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
            "path": out_path}
