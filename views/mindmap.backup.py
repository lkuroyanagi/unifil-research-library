import streamlit as st
import streamlit.components.v1 as components
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

_MINDMAP_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>UNIFIL Lessons Mind Map</title>
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
@keyframes pulse{0%,100%{opacity:.4;r:attr(r)}50%{opacity:.85}}
.halo{animation:pulse 3s ease-in-out infinite}

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
  <h1>Lessons Mind Map — UNIFIL</h1>
  <div class="stats"><b>46</b> nodes · <b>13</b> clusters · <b>12</b> sources</div>
</header>

<div class="workspace">
  <aside class="sb">
    <div class="ss"><div class="sl">Search</div><input class="si" id="iSearch" type="text" placeholder="Search nodes…"></div>
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
      <label class="ck"><input type="checkbox" checked data-t="cluster"><span class="dot" style="background:#4a7fd4"></span>Thematic cluster</label>
      <label class="ck"><input type="checkbox" checked data-t="centre"><span class="dot" style="background:#d4993a"></span>UNIFIL centre</label>
      <label class="ck"><input type="checkbox" checked data-t="source"><span class="dot" style="background:#4ab0d4"></span>Source document</label>
      <label class="ck"><input type="checkbox" checked data-t="lesson"><span class="dot" style="background:#3abf6a"></span>Lesson</label>
      <label class="ck"><input type="checkbox" checked data-t="inference"><span class="dot" style="background:#d45050"></span>Inference</label>
    </div>
    <div class="ss">
      <div class="sl">Filter cluster</div>
      <select id="sCl"><option value="">All clusters</option></select>
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
        <filter id="glow-centre" x="-70%" y="-70%" width="240%" height="240%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="b"/>
          <feFlood flood-color="#d4993a" flood-opacity="0.85" result="c"/>
          <feComposite in="c" in2="b" operator="in" result="g"/>
          <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="glow-cluster" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b"/>
          <feFlood flood-color="#4a7fd4" flood-opacity="0.8" result="c"/>
          <feComposite in="c" in2="b" operator="in" result="g"/>
          <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="glow-source" x="-70%" y="-70%" width="240%" height="240%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b"/>
          <feFlood flood-color="#4ab0d4" flood-opacity="0.75" result="c"/>
          <feComposite in="c" in2="b" operator="in" result="g"/>
          <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="glow-lesson" x="-70%" y="-70%" width="240%" height="240%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b"/>
          <feFlood flood-color="#3abf6a" flood-opacity="0.75" result="c"/>
          <feComposite in="c" in2="b" operator="in" result="g"/>
          <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="glow-inference" x="-70%" y="-70%" width="240%" height="240%">
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
  <div class="li"><div class="ld" style="background:#4a7fd4"></div>Thematic cluster</div>
  <div class="li"><div class="ld" style="background:#d4993a"></div>UNIFIL centre</div>
  <div class="li"><div class="ld" style="background:#4ab0d4"></div>Source doc.</div>
  <div class="li"><div class="ld" style="background:#3abf6a"></div>Lesson</div>
  <div class="li"><div class="ld" style="background:#d45050"></div>Inference</div>
</div>
<div id="tt"></div>

<script>
const NODES = [
  {id:"C0",  label:"UNIFIL Lessons Learned",    type:"centre",   cl:null,   desc:"Central hub for all lessons learned, inferences, and source documents for the UNIFIL mission in Southern Lebanon."},
  {id:"CL1", label:"Force Protection",           type:"cluster",  cl:"CL1",  desc:"Protection of personnel, equipment, and infrastructure in the operational area."},
  {id:"CL2", label:"Host-State & LAF",           type:"cluster",  cl:"CL2",  desc:"Engagement with Lebanese Armed Forces and Lebanese state institutions."},
  {id:"CL3", label:"Operational Adaptation",     type:"cluster",  cl:"CL3",  desc:"Mission adaptation to evolving security and political environments."},
  {id:"CL4", label:"TCC Dynamics",               type:"cluster",  cl:"CL4",  desc:"Troop-Contributing Country coordination, command and control integration."},
  {id:"CL5", label:"Non-State Armed Actors",     type:"cluster",  cl:"CL5",  desc:"Relations with Hezbollah and other NSAAs; deconfliction and FOM."},
  {id:"CL6", label:"Monitoring & Technology",    type:"cluster",  cl:"CL6",  desc:"Surveillance systems, UAV use, incident reporting, and technology integration."},
  {id:"CL7", label:"De-mining & Stabilisation",  type:"cluster",  cl:"CL7",  desc:"Mine action, UXO clearance, post-conflict stabilization, Blue Line demarcation."},
  {id:"CL8", label:"Liaison & Tripartite",       type:"cluster",  cl:"CL8",  desc:"Operation of the Tripartite mechanism between Israel, Lebanon, and UNIFIL."},
  {id:"CL9", label:"CIMIC & Community",          type:"cluster",  cl:"CL9",  desc:"Civil-military cooperation, community engagement, quick-impact projects."},
  {id:"CL10",label:"Political Dynamics",         type:"cluster",  cl:"CL10", desc:"Political context, spoiler dynamics, mandate interpretation."},
  {id:"CL11",label:"DPKO-DPA Integration",       type:"cluster",  cl:"CL11", desc:"Integration of DPO and DPA planning and reporting."},
  {id:"CL12",label:"Mandate Evolution",          type:"cluster",  cl:"CL12", desc:"Changes to UNSCR 1701 interpretation and mandate renewals."},
  {id:"CL13",label:"Rules of Engagement",        type:"cluster",  cl:"CL13", desc:"Use of force, ROE interpretation, SOFA, and legal constraints."},
  {id:"S1",  label:"LL Report 2021",             type:"source",   cl:"CL1",  desc:"Annual lessons learned report for the 2021 reporting period.", year:2021},
  {id:"S2",  label:"Force Gen. Analysis 2022",   type:"source",   cl:"CL4",  desc:"Analysis of TCC performance and force generation challenges.", year:2022},
  {id:"S3",  label:"Blue Line Incident Log",     type:"source",   cl:"CL5",  desc:"Record of Blue Line violations and proximity incidents 2020–23.", year:2023},
  {id:"S4",  label:"CIMIC Assessment 2022",      type:"source",   cl:"CL9",  desc:"Evaluation of CIMIC activities and community impact.", year:2022},
  {id:"S5",  label:"UAV Integration Review",     type:"source",   cl:"CL6",  desc:"Review of UAV integration into UNIFIL surveillance architecture.", year:2023},
  {id:"S6",  label:"Tripartite Minutes",         type:"source",   cl:"CL8",  desc:"Compiled Tripartite mechanism meeting minutes 2019–22.", year:2022},
  {id:"S7",  label:"LAF Coordination Study",     type:"source",   cl:"CL2",  desc:"Study on coordination protocols between UNIFIL and the LAF.", year:2021},
  {id:"S8",  label:"Mine Action Report",         type:"source",   cl:"CL7",  desc:"Progress report on mine clearance and UXO disposal.", year:2023},
  {id:"S9",  label:"Res. 1701 Analysis",         type:"source",   cl:"CL12", desc:"Legal and operational analysis of UNSCR 1701 scope.", year:2022},
  {id:"S10", label:"ROE Review 2023",            type:"source",   cl:"CL13", desc:"Internal review of ROE application in complex scenarios.", year:2023},
  {id:"S11", label:"AAR Op. CEDAR 2022",         type:"source",   cl:"CL1",  desc:"After-action review of a force-protection operation.", year:2022},
  {id:"S12", label:"Sector East Review",         type:"source",   cl:"CL3",  desc:"Review of adaptation measures in Sector East post-2021.", year:2021},
  {id:"L1",  label:"IED awareness",              type:"lesson",   cl:"CL1",  desc:"Patrols require standardised IED-awareness protocols.", rec:"Develop a unified UNIFIL IED awareness SOP."},
  {id:"L2",  label:"Convoy spacing",             type:"lesson",   cl:"CL1",  desc:"Convoy spacing varies widely across TCCs, creating exploitable patterns.", rec:"Mandate minimum spacing and route variation doctrine."},
  {id:"L3",  label:"LAF joint patrols",          type:"lesson",   cl:"CL2",  desc:"Joint UNIFIL–LAF patrol frequency dropped 34% in 2022.", rec:"Establish minimum joint patrol targets in annual plans."},
  {id:"L4",  label:"Comms gaps – LAF",           type:"lesson",   cl:"CL2",  desc:"Radio interoperability between UNIFIL and LAF remains limited.", rec:"Provision encrypted cross-network radios to liaison officers."},
  {id:"L5",  label:"TCC caveats",                type:"lesson",   cl:"CL4",  desc:"National caveats restrict operational flexibility.", rec:"Report caveat impacts in mandate renewal documentation."},
  {id:"L6",  label:"FOM violations",             type:"lesson",   cl:"CL5",  desc:"FOM violations near the Blue Line increased 28% in 2023.", rec:"Establish 72-hour notification protocol for armed movements."},
  {id:"L7",  label:"UAV coverage gaps",          type:"lesson",   cl:"CL6",  desc:"Persistent UAV gaps during weather events and maintenance windows.", rec:"Develop redundant coverage rotation protocols."},
  {id:"L8",  label:"Incident reporting delays",  type:"lesson",   cl:"CL6",  desc:"Average incident report exceeds 4-hour target by 140 minutes.", rec:"Introduce mobile-first incident reporting tool."},
  {id:"L9",  label:"Mine clearance coord.",      type:"lesson",   cl:"CL7",  desc:"Clearance operations lack a unified tasking authority.", rec:"Establish a Mine Action Coordination Cell."},
  {id:"L10", label:"Tripartite preparation",     type:"lesson",   cl:"CL8",  desc:"Insufficient pre-meeting preparation reduces Tripartite effectiveness.", rec:"Mandate structured agenda prep with 5-day lead time."},
  {id:"L11", label:"CIMIC sustainability",       type:"lesson",   cl:"CL9",  desc:"Quick-impact projects frequently lack sustainability plans.", rec:"Require all CIMIC projects to include a handover plan."},
  {id:"L12", label:"ROE clarity for COs",        type:"lesson",   cl:"CL13", desc:"Contingent COs report insufficient understanding of ROE thresholds.", rec:"Conduct quarterly ROE workshops with case-study scenarios."},
  {id:"L13", label:"Mandate communication",      type:"lesson",   cl:"CL12", desc:"Rank-and-file soldiers have poor understanding of the mission mandate.", rec:"Integrate mandate orientation into pre-deployment training."},
  {id:"L14", label:"Innovation incentives",      type:"lesson",   cl:"CL3",  desc:"Lack of formal incentives for reporting innovative practices.", rec:"Create a UNIFIL Innovation Award."},
  {id:"L15", label:"DPKO-DPA gap",               type:"lesson",   cl:"CL11", desc:"Political analysis from DPA not shared with UNIFIL planning cells.", rec:"Establish monthly political briefing cycle, SRSG to Force HQ."},
  {id:"A1",  label:"Structural FOM degradation", type:"inference",cl:"CL5",  desc:"FOM degradation is structural, driven by long-term actor repositioning post-2021.", rec:"Commission a multi-year FOM trend study."},
  {id:"A2",  label:"TCC fatigue cycle",          type:"inference",cl:"CL4",  desc:"3-year TCC fatigue cycle correlates with reduced performance.", rec:"Proactively rotate high-fatigue TCCs."},
  {id:"A3",  label:"Technology–doctrine lag",    type:"inference",cl:"CL6",  desc:"Technology acquisition outpaces doctrinal adaptation by 18–24 months across UN PKO missions.", rec:"Establish technology integration doctrine teams."},
  {id:"A4",  label:"LAF capacity ceiling",       type:"inference",cl:"CL2",  desc:"LAF capacity has reached a ceiling constrained by fiscal, political, and structural factors.", rec:"Adjust UNIFIL planning assumptions regarding LAF."},
  {id:"A5",  label:"CIMIC–FOM correlation",      type:"inference",cl:"CL9",  desc:"CIMIC activity correlates positively with local community FOM cooperation.", rec:"Present CIMIC as a force-protection enabler."},
];

const EDGE_DEFS = [
  ...NODES.filter(n=>n.type==="cluster").map(n=>({s:n.id,t:"C0",w:2.5})),
  ...NODES.filter(n=>["lesson","inference","source"].includes(n.type)&&n.cl).map(n=>({s:n.id,t:n.cl,w:1})),
  {s:"A1",t:"CL8",w:.5},{s:"A1",t:"CL2",w:.5},{s:"A2",t:"CL5",w:.5},
  {s:"A3",t:"CL3",w:.5},{s:"A4",t:"CL8",w:.5},{s:"A5",t:"CL7",w:.5},
  {s:"L6",t:"CL8",w:.5},{s:"L3",t:"CL5",w:.5},{s:"L5",t:"CL13",w:.5},{s:"L15",t:"CL12",w:.5},
];

const PALETTES = {
  def:   {cluster:"#4a7fd4",centre:"#d4993a",source:"#4ab0d4",lesson:"#3abf6a",inference:"#d45050",link:"#3a5a90"},
  cyber: {cluster:"#cc00ff",centre:"#00ffcc",source:"#00aaff",lesson:"#aaff00",inference:"#ff3366",link:"#441166"},
  arctic:{cluster:"#5588cc",centre:"#88ccee",source:"#3399bb",lesson:"#77bbdd",inference:"#aaddff",link:"#223355"},
  ember: {cluster:"#cc5500",centre:"#ffaa00",source:"#ff7722",lesson:"#dd9900",inference:"#aa2200",link:"#442200"},
};
const TYPE_LBL={cluster:"Thematic cluster",centre:"UNIFIL LL / Centre",source:"Source document",lesson:"Source-derived lesson",inference:"Analytical inference"};

const CFG={
  scale:0.65, lo:0.65, lw:1.5,
  charge:-300, dist:140, grav:0.04,
  types:new Set(["cluster","centre","source","lesson","inference"]),
  cluster:"", search:"", pal:"def"
};

function tc(t){return PALETTES[CFG.pal][t]||"#888";}
function nodeR(t){return ({centre:22,cluster:13,source:6,lesson:5,inference:5.5}[t]||5)*CFG.scale;}
function nodeFontSize(t){
  if(t==="centre")  return Math.max(5,8.5*CFG.scale);
  if(t==="cluster") return Math.max(5,7*CFG.scale);
  return Math.max(5,6.5*CFG.scale);
}

const cvWrap=document.getElementById("cvWrap");
const svgSel=d3.select("#graph");
const mainG=d3.select("#mainG");
let W=cvWrap.clientWidth||900, H=cvWrap.clientHeight||600;
let simInst=null;

const zoomBeh=d3.zoom().scaleExtent([0.08,8]).on("zoom",e=>mainG.attr("transform",e.transform));
svgSel.call(zoomBeh).on("dblclick.zoom",null);
svgSel.on("click",e=>{if(e.target===svgSel.node()||e.target.tagName==="svg")deselect();});

function build(){
  if(simInst){simInst.stop();simInst=null;}

  const vNodes=NODES.filter(n=>{
    if(!CFG.types.has(n.type)) return false;
    if(CFG.cluster){
      if(n.type==="centre") return true;
      if(n.type==="cluster"&&n.id!==CFG.cluster) return false;
      if(n.type!=="cluster"&&n.cl!==CFG.cluster) return false;
    }
    if(CFG.search){
      const h=(n.label+" "+(n.desc||"")).toLowerCase();
      if(!h.includes(CFG.search.toLowerCase())) return false;
    }
    return true;
  });
  const ids=new Set(vNodes.map(n=>n.id));
  const vLinks=EDGE_DEFS.filter(e=>ids.has(e.s)&&ids.has(e.t)).map(e=>({source:e.s,target:e.t,weight:e.w}));

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
    .force("collide", d3.forceCollide().radius(d=>nodeR(d.type)+3).strength(0.85))
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
    .on("click",(e,d)=>{e.stopPropagation();selectNode(d,vLinks,lSel,nSel);})
    .on("mouseenter",(e,d)=>{
      const tt=document.getElementById("tt");
      tt.innerHTML=`<strong style="color:${tc(d.type)}">${d.label}</strong>`;
      tt.style.opacity=1;
    })
    .on("mousemove",e=>{
      const tt=document.getElementById("tt");
      tt.style.left=(e.clientX+12)+"px";tt.style.top=(e.clientY-28)+"px";
    })
    .on("mouseleave",()=>document.getElementById("tt").style.opacity=0);

  nSel.filter(d=>d.type==="centre").append("circle")
    .attr("class","halo")
    .attr("r",d=>nodeR(d.type)*2.2)
    .attr("fill","none")
    .attr("stroke","#d4993a")
    .attr("stroke-width",1.5)
    .attr("stroke-opacity",0.6)
    .attr("pointer-events","none");

  nSel.filter(d=>d.type==="cluster").append("circle")
    .attr("r",d=>nodeR(d.type)*1.5)
    .attr("fill","none")
    .attr("stroke",d=>tc(d.type))
    .attr("stroke-width",0.5)
    .attr("stroke-opacity",0.3)
    .attr("pointer-events","none");

  nSel.append("circle")
    .attr("r",d=>nodeR(d.type))
    .attr("fill",d=>tc(d.type))
    .attr("stroke",d=>{const c=d3.color(tc(d.type));return c?c.brighter(.6)+"":"#fff";})
    .attr("stroke-width",d=>d.type==="centre"?2:1)
    .style("filter",d=>`url(#glow-${d.type})`);

  nSel.append("circle").attr("class","ring")
    .attr("r",d=>nodeR(d.type)+5).attr("fill","none")
    .attr("stroke","#fff").attr("stroke-width",2).attr("opacity",0)
    .attr("pointer-events","none");

  nSel.each(function(d){
    const g=d3.select(this);
    const fz=nodeFontSize(d.type);
    const big=d.type==="centre"||d.type==="cluster";
    if(big){
      const words=d.label.split(" ");
      const mid=Math.ceil(words.length/2);
      const rows=words.length>1?[words.slice(0,mid).join(" "),words.slice(mid).join(" ")]:[d.label];
      const lh=fz+1.5;
      rows.filter(r=>r.length>0).forEach((row,i,arr)=>{
        g.append("text")
          .attr("text-anchor","middle").attr("dominant-baseline","central")
          .attr("y",(i-(arr.length-1)/2)*lh)
          .attr("font-size",fz).attr("font-weight","600")
          .attr("fill","#fff").attr("pointer-events","none")
          .text(row);
      });
    } else {
      g.append("text")
        .attr("text-anchor","middle")
        .attr("y",-(nodeR(d.type)+3.5))
        .attr("font-size",fz)
        .attr("fill","#a8b4cc").attr("pointer-events","none")
        .text(d.label.length>22?d.label.slice(0,21)+"…":d.label);
    }
  });

  sim.on("tick",()=>{
    lSel.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y)
        .attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
    nSel.attr("transform",d=>`translate(${d.x},${d.y})`);
  }).alpha(0).restart();

  simInst=sim;
}

function selectNode(d,vLinks,lSel,nSel){
  nSel.select("circle:not(.ring)").attr("opacity",n=>{
    if(n.id===d.id) return 1;
    const c=vLinks.some(l=>{const s=l.source.id||l.source,t=l.target.id||l.target;return(s===d.id&&t===n.id)||(t===d.id&&s===n.id);});
    return c?0.9:0.1;
  });
  lSel.attr("stroke-opacity",l=>{
    const s=l.source.id||l.source,t=l.target.id||l.target;
    return s===d.id||t===d.id?1:CFG.lo*0.1;
  });
  nSel.select(".ring").attr("opacity",n=>n.id===d.id?1:0);

  document.getElementById("dDot").style.background=tc(d.type);
  document.getElementById("dTitle").textContent=d.label;
  document.getElementById("dType").textContent=TYPE_LBL[d.type]||d.type;
  const cids=new Set(vLinks.flatMap(l=>{const s=l.source.id||l.source,t=l.target.id||l.target;return s===d.id?[t]:t===d.id?[s]:[];}));
  cids.delete(d.id);
  const cn=NODES.filter(n=>cids.has(n.id));
  let html=`<div class="ds"><h4>Description</h4><p>${d.desc||"—"}</p></div>`;
  if(d.rec)  html+=`<div class="ds"><h4>Recommendation</h4><p>${d.rec}</p></div>`;
  if(d.year) html+=`<div class="ds"><h4>Year</h4><p>${d.year}</p></div>`;
  if(d.cl&&d.type!=="cluster"&&d.type!=="centre"){
    const cl=NODES.find(n=>n.id===d.cl);
    if(cl) html+=`<div class="ds"><h4>Cluster</h4><p>${cl.label}</p></div>`;
  }
  if(cn.length){
    html+=`<div class="ds"><h4>Connected (${cn.length})</h4><div>`;
    cn.forEach(n=>html+=`<span class="chip" style="border-left:3px solid ${tc(n.type)}">${n.label}</span>`);
    html+="</div></div>";
  }
  document.getElementById("dBody").innerHTML=html;
  document.getElementById("dPanel").classList.add("open");
}

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
$id("sCl").addEventListener("change",function(){CFG.cluster=this.value;build();});
$id("sTh").addEventListener("change",function(){CFG.pal=this.value;build();});
$id("iSearch").addEventListener("input",function(){CFG.search=this.value.trim();build();});
$id("btnRe").addEventListener("click",()=>{NODES.forEach(n=>{delete n.x;delete n.y;delete n.vx;delete n.vy;delete n.fx;delete n.fy;});build();});
$id("btnFit").addEventListener("click",()=>{svgSel.transition().duration(500).call(zoomBeh.transform,d3.zoomIdentity);deselect();});
$id("dClose").addEventListener("click",deselect);

NODES.filter(n=>n.type==="cluster").forEach(n=>{
  const o=document.createElement("option");o.value=n.id;o.textContent=n.label;$id("sCl").appendChild(o);
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

    components.html(_MINDMAP_HTML, height=2000, scrolling=False)
