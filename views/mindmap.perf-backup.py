import json
import re
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent.parent))

_DATA_PATH = Path(__file__).parent.parent / "data" / "sources.json"


def _short_label(s):
    """'Author Year' label: 'Kassem 2024', 'Newby & Ruffa 2026', 'Orion et al. 2019'."""
    author = (s.get("author") or "").strip()
    year = s.get("year")
    if not author or not year:
        return str(s.get("id", ""))

    parts = [p for p in re.split(r"\s*&\s*|\s+and\s+|;\s*", author) if p.strip()]

    def surname(p):
        p = p.strip()
        return p.split(",")[0].strip() if "," in p else p

    if len(parts) >= 3:
        lbl = f"{surname(parts[0])} et al."
    elif len(parts) == 2:
        lbl = f"{surname(parts[0])} & {surname(parts[1])}"
    else:
        lbl = surname(parts[0])
    return f"{lbl} {year}"


def _build_graph():
    """Build NODES / EDGES arrays from data/sources.json."""
    with open(_DATA_PATH, encoding="utf-8") as f:
        sources = json.load(f)

    # Tag frequency across the corpus
    freq = {}
    for s in sources:
        for t in s.get("tags", []):
            freq[t] = freq.get(t, 0) + 1

    # Radius: r = base + k*(sqrt(f)-1); smallest tag r≈4, most frequent r≈22 (capped)
    max_f = max(freq.values()) if freq else 1
    k = 18.0 / (max_f ** 0.5 - 1) if max_f > 1 else 0.0
    def tag_r(f):
        return min(22.0, round(4.0 + k * (f ** 0.5 - 1), 2))

    nodes, edges = [], []

    src_label = {}  # source node id -> label (for tag detail lists)
    for s in sources:
        sid = f"s_{s.get('id', '')}"
        label = _short_label(s)
        src_label[sid] = label
        nodes.append({
            "id": sid,
            "label": label,
            "type": "source",
            "r": 6,
            "title": s.get("title", ""),
            "author": s.get("author", ""),
            "year": s.get("year", ""),
            "stype": s.get("source_type") or s.get("type") or "",
            "publisher": s.get("publisher", ""),
            "abstract": s.get("abstract", ""),
            "clusters": s.get("thematic_clusters", []),
            "tags": s.get("tags", []),
        })
        for t in s.get("tags", []):
            edges.append({"s": sid, "t": f"t_{t}"})

    for t, f in freq.items():
        connected = sorted(
            ({"id": f"s_{s.get('id', '')}", "label": src_label[f"s_{s.get('id', '')}"]}
             for s in sources if t in s.get("tags", [])),
            key=lambda x: x["label"].lower(),
        )
        nodes.append({
            "id": f"t_{t}",
            "label": t,
            "type": "tag",
            "r": tag_r(f),
            "freq": f,
            "sources": connected,
        })

    n_tags = len(freq)
    n_sources = len(sources)
    return nodes, edges, n_tags, n_sources


_MINDMAP_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>UNIFIL Corpus Graph</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;600&family=Source+Sans+3:wght@300;400;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0e1118;--panel:#141820;--border:#242b3a;
  --blue:#2e6db4;--gold:#d4993a;--text:#cdd2e0;--muted:#5e6880;
}
body{font-family:'Source Sans 3',sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden}

/* HEADER */
header{background:var(--panel);border-bottom:1px solid var(--border);padding:8px 18px;display:flex;align-items:center;gap:12px;flex-shrink:0}
.eye{font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
h1{font-family:'Lora',serif;font-size:17px;color:#7aaddd;font-weight:600}
.stats{margin-left:auto;font-size:11px;color:var(--muted)}
.stats b{color:#7aaddd}

/* LAYOUT */
.workspace{display:flex;flex:1;overflow:hidden}

/* SIDEBAR */
.sb{width:260px;flex-shrink:0;background:var(--panel);border-right:1px solid var(--border);overflow-y:auto}
.ss{padding:10px 12px;border-bottom:1px solid var(--border)}
.sl{font-size:9px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:8px}
.row{display:flex;align-items:center;margin-bottom:5px}
.row:last-child{margin-bottom:0}
.row label{font-size:12px;flex:1}
.val{font-size:11px;color:var(--muted);width:34px;text-align:right}
input[type=range]{width:100%;margin-top:2px;accent-color:#4a8fc4;cursor:pointer}
.gap{height:6px}
.ck{display:flex;align-items:center;gap:6px;margin-bottom:6px;cursor:pointer;font-size:12px}
.ck:last-child{margin-bottom:0}
.ck input{accent-color:#4a8fc4;cursor:pointer;flex-shrink:0}
.dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
select,.si{width:100%;padding:5px 7px;font-size:12px;font-family:inherit;border:1px solid var(--border);border-radius:4px;background:#1a1f2c;color:var(--text);cursor:pointer;margin-bottom:6px}
select:last-child,.si:last-child{margin-bottom:0}
.si{outline:none}
.si:focus{border-color:#4a8fc4}
.brow{display:flex;gap:6px}
.btn{flex:1;padding:6px;font-size:11px;font-family:inherit;border:1px solid var(--border);border-radius:4px;background:#1a1f2c;color:var(--text);cursor:pointer}
.btn:hover{background:#222840}
.btnp{background:#1a3a6e!important;color:#7aaddd!important;border-color:#2e5fa0!important}
.btnp:hover{background:#1f4580!important}

/* CANVAS */
.cv{flex:1;position:relative;overflow:hidden}
svg{width:100%;height:100%;cursor:grab;background:var(--bg)}
svg:active{cursor:grabbing}

/* DETAIL PANEL */
.dp{position:absolute;right:0;top:0;bottom:0;width:286px;background:var(--panel);border-left:1px solid var(--border);display:flex;flex-direction:column;transform:translateX(100%);transition:transform .2s ease;z-index:10}
.dp.open{transform:translateX(0)}
.dph{padding:12px;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;gap:8px}
.dpdot{width:10px;height:10px;border-radius:50%;margin-top:3px;flex-shrink:0}
.dph h3{font-family:'Lora',serif;font-size:13px;color:#7aaddd;line-height:1.4;flex:1}
.dpt{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:2px}
.xbtn{background:none;border:none;cursor:pointer;color:var(--muted);font-size:17px;line-height:1;flex-shrink:0;padding:0}
.xbtn:hover{color:var(--text)}
.dpb{flex:1;overflow-y:auto;padding:12px}
.ds{margin-bottom:12px}
.ds h4{font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;font-weight:600}
.ds p{font-size:12px;line-height:1.55;color:var(--text)}
.chip{display:inline-block;padding:2px 7px;border-radius:10px;font-size:11px;margin:2px;border:1px solid var(--border);background:#1a1f2c;color:var(--text);cursor:pointer}
.chip:hover{background:#222840}

/* LEGEND */
.leg{background:var(--panel);border-top:1px solid var(--border);padding:6px 18px;display:flex;align-items:center;gap:14px;flex-shrink:0}
.li{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--muted)}
.ld{width:8px;height:8px;border-radius:50%}

/* TOOLTIP */
#tt{position:fixed;background:rgba(8,12,20,.95);color:#cdd2e0;border:1px solid #2a3348;padding:5px 10px;border-radius:4px;font-size:12px;pointer-events:none;opacity:0;transition:opacity .12s;z-index:200;max-width:190px;line-height:1.4}
.hint{position:absolute;bottom:8px;left:8px;background:rgba(14,17,24,.85);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:11px;color:var(--muted);backdrop-filter:blur(4px)}
</style>
</head>
<body>
<header>
  <span class="eye">Visual Overview</span>
  <h1>Corpus Graph — UNIFIL</h1>
  <div class="stats"><b>__NTAGS__</b> tags · <b>__NSOURCES__</b> sources</div>
</header>

<div class="workspace">
  <aside class="sb">
    <div class="ss"><div class="sl">Search</div><input class="si" id="iSearch" type="text" placeholder="Search tags &amp; sources…"></div>
    <div class="ss">
      <div class="sl">Node size</div>
      <div class="row"><label>Scale</label><span class="val" id="vSz">0.65×</span></div>
      <input type="range" id="rSz" min="0.2" max="2.5" step="0.05" value="0.65">
    </div>
    <div class="ss">
      <div class="sl">Links</div>
      <div class="row"><label>Opacity</label><span class="val" id="vLO">65%</span></div>
      <input type="range" id="rLO" min="5" max="100" step="5" value="65">
      <div class="gap"></div>
      <div class="row"><label>Width</label><span class="val" id="vLW">1.5</span></div>
      <input type="range" id="rLW" min="0.3" max="6" step="0.1" value="1.5">
    </div>
    <div class="ss">
      <div class="sl">Physics</div>
      <div class="row"><label>Repulsion</label><span class="val" id="vCh">−300</span></div>
      <input type="range" id="rCh" min="-1000" max="-30" step="10" value="-300">
      <div class="gap"></div>
      <div class="row"><label>Link distance</label><span class="val" id="vLD">140</span></div>
      <input type="range" id="rLD" min="30" max="350" step="10" value="140">
      <div class="gap"></div>
      <div class="row"><label>Gravity</label><span class="val" id="vGr">0.04</span></div>
      <input type="range" id="rGr" min="0" max="0.5" step="0.01" value="0.04">
    </div>
    <div class="ss">
      <div class="sl">Show types</div>
      <label class="ck"><input type="checkbox" checked data-t="tag"><span class="dot" style="background:#a8b4cc"></span>Show tags</label>
      <label class="ck"><input type="checkbox" checked data-t="source"><span class="dot" style="background:#d45050"></span>Show sources</label>
    </div>
    <div class="ss">
      <div class="sl">Filter by tag</div>
      <select id="sTag"><option value="">All tags</option></select>
    </div>
    <div class="ss">
      <div class="sl">Colour theme</div>
      <select id="sTh">
        <option value="def">UN dark (default)</option>
        <option value="cyber">Cyberpunk</option>
        <option value="arctic">Arctic blue</option>
        <option value="ember">Ember</option>
      </select>
    </div>
    <div class="ss">
      <div class="brow">
        <button class="btn btnp" id="btnRe">↺ Restart</button>
        <button class="btn" id="btnFit">⊡ Fit view</button>
      </div>
    </div>
  </aside>

  <div class="cv" id="cvWrap">
    <svg id="graph">
      <defs>
        <filter id="glow-link" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="glow-tag" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="b"/>
          <feFlood flood-color="#a8b4cc" flood-opacity="0.55" result="c"/>
          <feComposite in="c" in2="b" operator="in" result="g"/>
          <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="glow-source" x="-70%" y="-70%" width="240%" height="240%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b"/>
          <feFlood flood-color="#d45050" flood-opacity="0.75" result="c"/>
          <feComposite in="c" in2="b" operator="in" result="g"/>
          <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <g id="mainG"></g>
    </svg>
    <div class="hint">Scroll to zoom · Drag canvas to pan · Click node for details</div>
    <div class="dp" id="dPanel">
      <div class="dph">
        <div class="dpdot" id="dDot"></div>
        <div style="flex:1"><h3 id="dTitle"></h3><div class="dpt" id="dType"></div></div>
        <button class="xbtn" id="dClose">✕</button>
      </div>
      <div class="dpb" id="dBody"></div>
    </div>
  </div>
</div>

<div class="leg">
  <div class="li"><div class="ld" style="background:#a8b4cc"></div>Tag</div>
  <div class="li"><div class="ld" style="background:#d45050"></div>Source</div>
</div>
<div id="tt"></div>

<script>
const NODES = __NODES__;
const EDGE_DEFS = __EDGES__;

const PALETTES = {
  def:   {tag:"#a8b4cc",source:"#d45050",link:"#3a5a90"},
  cyber: {tag:"#9aa7c7",source:"#ff3366",link:"#441166"},
  arctic:{tag:"#8fa8c8",source:"#e06868",link:"#223355"},
  ember: {tag:"#b09a88",source:"#ff5533",link:"#442200"},
};
const TYPE_LBL={tag:"Tag",source:"Source"};

const CFG={
  scale:0.65, lo:0.65, lw:1.5,
  charge:-300, dist:140, grav:0.04,
  types:new Set(["tag","source"]),
  tag:"", search:"", pal:"def"
};

function esc(s){return String(s??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function tc(t){return PALETTES[CFG.pal][t]||"#888";}
function nodeR(d){return d.r*CFG.scale;}
function nodeFontSize(d){
  if(d.type==="tag") return Math.max(5,(6.5+d.r*0.12)*CFG.scale);
  return Math.max(5,6.5*CFG.scale);
}

const cvWrap=document.getElementById("cvWrap");
const svgSel=d3.select("#graph");
const mainG=d3.select("#mainG");
let W=cvWrap.clientWidth||900, H=cvWrap.clientHeight||600;
let simInst=null;
let curLinks=[],curLSel=null,curNSel=null;

const zoomBeh=d3.zoom().scaleExtent([0.08,8]).on("zoom",e=>mainG.attr("transform",e.transform));
svgSel.call(zoomBeh).on("dblclick.zoom",null);
svgSel.on("click",e=>{if(e.target===svgSel.node()||e.target.tagName==="svg")deselect();});

function build(){
  if(simInst){simInst.stop();simInst=null;}

  const vNodes=NODES.filter(n=>{
    if(!CFG.types.has(n.type)) return false;
    if(CFG.tag){
      if(n.type==="tag"&&n.label!==CFG.tag) return false;
      if(n.type==="source"&&!n.tags.includes(CFG.tag)) return false;
    }
    if(CFG.search){
      const h=(n.label+" "+(n.title||"")+" "+(n.author||"")).toLowerCase();
      if(!h.includes(CFG.search.toLowerCase())) return false;
    }
    return true;
  });
  const ids=new Set(vNodes.map(n=>n.id));
  const vLinks=EDGE_DEFS.filter(e=>ids.has(e.s)&&ids.has(e.t)).map(e=>({source:e.s,target:e.t,weight:1}));

  vNodes.forEach(n=>{
    if(!isFinite(n.x)||!isFinite(n.y)){
      const a=Math.random()*2*Math.PI, r=40+Math.random()*80;
      n.x=W/2+Math.cos(a)*r; n.y=H/2+Math.sin(a)*r; n.vx=0; n.vy=0;
    }
  });

  const sim=d3.forceSimulation(vNodes)
    .alphaDecay(0.028).velocityDecay(0.4)
    .force("link",    d3.forceLink(vLinks).id(d=>d.id).distance(CFG.dist).strength(0.7))
    .force("charge",  d3.forceManyBody().strength(CFG.charge))
    .force("center",  d3.forceCenter(W/2,H/2))
    .force("collide", d3.forceCollide().radius(d=>nodeR(d)+3).strength(0.85))
    .force("x",       d3.forceX(W/2).strength(CFG.grav))
    .force("y",       d3.forceY(H/2).strength(CFG.grav))
    .stop();
  for(let i=0;i<300;i++) sim.tick();

  mainG.selectAll("*").remove();

  const lG=mainG.append("g").attr("class","lG");
  const lSel=lG.selectAll("line").data(vLinks).enter().append("line")
    .attr("stroke",tc("link"))
    .attr("stroke-width",d=>CFG.lw*(d.weight||1)*1.3)
    .attr("stroke-opacity",CFG.lo)
    .style("filter","url(#glow-link)")
    .attr("x1",d=>d.source.x).attr("y1",d=>d.source.y)
    .attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);

  const nG=mainG.append("g").attr("class","nG");
  const nSel=nG.selectAll("g").data(vNodes).enter().append("g")
    .attr("transform",d=>`translate(${d.x},${d.y})`)
    .call(d3.drag()
      .on("start",(e,d)=>{if(!e.active)simInst.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y;})
      .on("drag", (e,d)=>{d.fx=e.x;d.fy=e.y;})
      .on("end",  (e,d)=>{if(!e.active)simInst.alphaTarget(0);d.fx=null;d.fy=null;}))
    .on("click",(e,d)=>{e.stopPropagation();selectNode(d);})
    .on("mouseenter",(e,d)=>{
      const tt=document.getElementById("tt");
      tt.innerHTML=`<strong style="color:${tc(d.type)}">${esc(d.label)}</strong>`;
      tt.style.opacity=1;
    })
    .on("mousemove",e=>{
      const tt=document.getElementById("tt");
      tt.style.left=(e.clientX+12)+"px";tt.style.top=(e.clientY-28)+"px";
    })
    .on("mouseleave",()=>document.getElementById("tt").style.opacity=0);

  nSel.append("circle")
    .attr("r",d=>nodeR(d))
    .attr("fill",d=>tc(d.type))
    .attr("stroke",d=>{const c=d3.color(tc(d.type));return c?c.brighter(.6)+"":"#fff";})
    .attr("stroke-width",1)
    .style("filter",d=>`url(#glow-${d.type})`);

  nSel.append("circle").attr("class","ring")
    .attr("r",d=>nodeR(d)+5).attr("fill","none")
    .attr("stroke","#fff").attr("stroke-width",2).attr("opacity",0)
    .attr("pointer-events","none");

  nSel.append("text")
    .attr("text-anchor","middle")
    .attr("y",d=>-(nodeR(d)+3.5))
    .attr("font-size",d=>nodeFontSize(d))
    .attr("fill",d=>d.type==="tag"?"#a8b4cc":"#c9a0a0")
    .attr("pointer-events","none")
    .text(d=>d.label.length>26?d.label.slice(0,25)+"…":d.label);

  sim.on("tick",()=>{
    lSel.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y)
        .attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
    nSel.attr("transform",d=>`translate(${d.x},${d.y})`);
  }).alpha(0).restart();

  simInst=sim;
  curLinks=vLinks;curLSel=lSel;curNSel=nSel;
}

function chipRow(items,jump){
  return items.map(it=>{
    const lbl=esc(typeof it==="string"?it:it.label);
    const j=jump&&it.id?` data-jump="${esc(it.id)}"`:"";
    return `<span class="chip"${j}>${lbl}</span>`;
  }).join("");
}

function selectNode(d){
  if(curNSel){
    curNSel.select("circle:not(.ring)").attr("opacity",n=>{
      if(n.id===d.id) return 1;
      const c=curLinks.some(l=>{const s=l.source.id||l.source,t=l.target.id||l.target;return(s===d.id&&t===n.id)||(t===d.id&&s===n.id);});
      return c?0.9:0.1;
    });
    curLSel.attr("stroke-opacity",l=>{
      const s=l.source.id||l.source,t=l.target.id||l.target;
      return s===d.id||t===d.id?1:CFG.lo*0.1;
    });
    curNSel.select(".ring").attr("opacity",n=>n.id===d.id?1:0);
  }

  document.getElementById("dDot").style.background=tc(d.type);
  document.getElementById("dTitle").textContent=d.label;
  document.getElementById("dType").textContent=TYPE_LBL[d.type]||d.type;

  let html="";
  if(d.type==="source"){
    html+=`<div class="ds"><h4>Title</h4><p>${esc(d.title)||"—"}</p></div>`;
    html+=`<div class="ds"><h4>Author</h4><p>${esc(d.author)||"—"}</p></div>`;
    html+=`<div class="ds"><h4>Year</h4><p>${esc(d.year)||"—"}</p></div>`;
    html+=`<div class="ds"><h4>Type</h4><p>${esc(d.stype)||"—"}</p></div>`;
    html+=`<div class="ds"><h4>Publisher</h4><p>${esc(d.publisher)||"—"}</p></div>`;
    if(d.abstract) html+=`<div class="ds"><h4>Abstract</h4><p>${esc(d.abstract)}</p></div>`;
    if(d.clusters&&d.clusters.length)
      html+=`<div class="ds"><h4>Thematic clusters</h4><div>${chipRow(d.clusters)}</div></div>`;
    if(d.tags&&d.tags.length)
      html+=`<div class="ds"><h4>Tags</h4><div>${chipRow(d.tags.map(t=>({id:"t_"+t,label:t})),true)}</div></div>`;
  } else {
    html+=`<div class="ds"><h4>Sources using this tag</h4><p>${d.freq}</p></div>`;
    html+=`<div class="ds"><h4>Sources (${d.sources.length})</h4><div>${chipRow(d.sources,true)}</div></div>`;
  }
  document.getElementById("dBody").innerHTML=html;
  document.getElementById("dPanel").classList.add("open");
}

function jumpTo(id){
  let d=null;
  if(curNSel) curNSel.each(n=>{if(n.id===id)d=n;});
  if(!d) d=NODES.find(n=>n.id===id);
  if(d) selectNode(d);
}

document.getElementById("dBody").addEventListener("click",e=>{
  const c=e.target.closest("[data-jump]");
  if(c) jumpTo(c.dataset.jump);
});

function deselect(){
  mainG.selectAll("circle:not(.ring)").attr("opacity",1);
  mainG.selectAll("line").attr("stroke-opacity",CFG.lo);
  mainG.selectAll(".ring").attr("opacity",0);
  document.getElementById("dPanel").classList.remove("open");
}

function $id(id){return document.getElementById(id);}

$id("rSz").addEventListener("input",function(){CFG.scale=+this.value;$id("vSz").textContent=(+this.value).toFixed(2)+"×";build();});
$id("rLO").addEventListener("input",function(){CFG.lo=this.value/100;$id("vLO").textContent=this.value+"%";mainG.selectAll(".lG line").attr("stroke-opacity",CFG.lo);});
$id("rLW").addEventListener("input",function(){CFG.lw=+this.value;$id("vLW").textContent=(+this.value).toFixed(1);mainG.selectAll(".lG line").attr("stroke-width",d=>CFG.lw*(d.weight||1)*1.3);});
$id("rCh").addEventListener("input",function(){CFG.charge=+this.value;$id("vCh").textContent=CFG.charge;if(simInst){simInst.force("charge").strength(CFG.charge);simInst.alpha(.6).restart();}});
$id("rLD").addEventListener("input",function(){CFG.dist=+this.value;$id("vLD").textContent=CFG.dist;if(simInst){simInst.force("link").distance(CFG.dist);simInst.alpha(.6).restart();}});
$id("rGr").addEventListener("input",function(){CFG.grav=+this.value;$id("vGr").textContent=CFG.grav.toFixed(2);if(simInst){simInst.force("x").strength(CFG.grav);simInst.force("y").strength(CFG.grav);simInst.alpha(.3).restart();}});
document.querySelectorAll("[data-t]").forEach(cb=>{cb.addEventListener("change",function(){this.checked?CFG.types.add(this.dataset.t):CFG.types.delete(this.dataset.t);build();});});
$id("sTag").addEventListener("change",function(){CFG.tag=this.value;build();});
$id("sTh").addEventListener("change",function(){CFG.pal=this.value;build();});
$id("iSearch").addEventListener("input",function(){CFG.search=this.value.trim();build();});
$id("btnRe").addEventListener("click",()=>{NODES.forEach(n=>{delete n.x;delete n.y;delete n.vx;delete n.vy;delete n.fx;delete n.fy;});build();});
$id("btnFit").addEventListener("click",()=>{svgSel.transition().duration(500).call(zoomBeh.transform,d3.zoomIdentity);deselect();});
$id("dClose").addEventListener("click",deselect);

NODES.filter(n=>n.type==="tag")
  .slice().sort((a,b)=>a.label.localeCompare(b.label))
  .forEach(n=>{
    const o=document.createElement("option");o.value=n.label;o.textContent=`${n.label} (${n.freq})`;$id("sTag").appendChild(o);
  });

new ResizeObserver(()=>{
  W=cvWrap.clientWidth||900;H=cvWrap.clientHeight||600;
  if(simInst){
    simInst.force("center",d3.forceCenter(W/2,H/2));
    simInst.force("x",d3.forceX(W/2).strength(CFG.grav));
    simInst.force("y",d3.forceY(H/2).strength(CFG.grav));
    simInst.alpha(.2).restart();
  }
}).observe(cvWrap);

build();
</script>
</body>
</html>"""


def show():
    st.markdown("""
    <style>
    /* Remove ALL Streamlit chrome for this page */
    #root > div:first-child { overflow: hidden !important; }
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stMain"] {
        padding: 0 !important;
        margin: 0 !important;
        overflow: hidden !important;
        height: 100vh !important;
    }
    .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
        overflow: hidden !important;
        height: 100vh !important;
    }
    /* Stretch the iframe itself */
    iframe {
        position: fixed !important;
        top: 0 !important;
        left: 265px !important;
        right: 0 !important;
        bottom: 0 !important;
        width: calc(100vw - 265px) !important;
        height: 100vh !important;
        border: none !important;
        display: block !important;
    }
    </style>
    """, unsafe_allow_html=True)

    nodes, edges, n_tags, n_sources = _build_graph()
    html = (_MINDMAP_HTML
            .replace("__NODES__", json.dumps(nodes, ensure_ascii=False))
            .replace("__EDGES__", json.dumps(edges, ensure_ascii=False))
            .replace("__NTAGS__", str(n_tags))
            .replace("__NSOURCES__", str(n_sources)))
    components.html(html, height=2000, scrolling=False)
