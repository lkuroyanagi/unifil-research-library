import json
import re
from pathlib import Path

# Single authoritative stylesheet injected after the Design's <style> block is stripped.
# Colour variables from the Design are kept but translated to app-palette hex values.
# All layout, typography, spacing, and card styling comes from the app's native style.
_STYLE_OVERRIDES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ── Colour variables (Design palette → app-native hex) ── */
:root {
  --bg:       #F5F4F0;
  --bg-card:  #ffffff;
  --navy:     #1a1a2e;
  --navy-mid: #1a3a5c;
  --muted:    #8a9ab0;
  --divider:  #E8E5DE;
  --spine:    #9ab8d0;
  /* Category colours — muted, readable on beige/white */
  --c-unifil:      #2a748a;   --c-unifil-bg:    #e4f2f5;
  --c-military:    #8a4a1a;   --c-military-bg:  #f5ede3;
  --c-attack:      #8a2828;   --c-attack-bg:    #f5e4e4;
  --c-politics:    #5a3a80;   --c-politics-bg:  #ede4f5;
  --c-un:          #2a508a;   --c-un-bg:        #e4ecf5;
  --c-ceasefire:   #2a7a5a;   --c-ceasefire-bg: #e4f5ee;
}

/* ── Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  background: var(--bg);
  color: #3a3a3a;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 14px;
  line-height: 1.6;
  min-height: 100vh;
}

/* ── Header — matches .library-header / .library-title ── */
.page-header {
  background: var(--bg);
  border-bottom: 1px solid var(--divider);
  padding: 1.5rem 48px 1rem;
  position: static;
  z-index: auto;
}
.header-eyebrow { display: none; }
.header-top     { display: flex; align-items: baseline; gap: 16px; margin-bottom: 6px; }
.header-title {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--navy);
  letter-spacing: -0.01em;
  line-height: 1.2;
}
.header-stats  { display: flex; gap: 20px; margin-left: auto; align-items: center; }
.stat-item     { display: flex; align-items: baseline; gap: 4px; }
.stat-num {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.88rem;
  font-weight: 600;
  color: #6b7c8d;
  line-height: 1;
}
.stat-label {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 400;
  color: var(--muted);
  text-transform: lowercase;
  letter-spacing: 0;
  margin-top: 0;
}

/* ── Filter bar — light, no heavy box ── */
.controls-bar {
  background: var(--bg);
  border-bottom: 1px solid var(--divider);
  padding: 10px 48px;
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
  position: static;
  z-index: auto;
}
.controls-section { display: flex; align-items: center; gap: 12px; }
.controls-label {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  white-space: nowrap;
}
/* Dual range slider */
.range-wrap {
  position: relative; width: 240px; max-width: 240px;
  flex-shrink: 0; height: 28px; display: flex; align-items: center;
}
.range-track {
  position: absolute; width: 100%; height: 3px;
  background: var(--divider); border-radius: 2px; pointer-events: none;
}
.range-fill {
  position: absolute; height: 3px;
  background: var(--navy-mid); border-radius: 2px; pointer-events: none;
}
.range-input {
  position: absolute; width: 100%; height: 3px;
  background: none; -webkit-appearance: none; appearance: none; pointer-events: none;
}
.range-input::-webkit-slider-thumb {
  -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%;
  background: var(--navy-mid); border: 2px solid var(--bg-card);
  box-shadow: 0 1px 4px rgba(0,0,0,0.2); pointer-events: all; cursor: pointer;
}
.range-input::-moz-range-thumb {
  width: 14px; height: 14px; border-radius: 50%;
  background: var(--navy-mid); border: 2px solid var(--bg-card); pointer-events: all; cursor: pointer;
}
.range-val {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.82rem; font-weight: 600;
  color: var(--navy-mid); min-width: 32px; text-align: center;
}
/* Category filter pills */
.pill-wrap { display: flex; gap: 6px; flex-wrap: wrap; }
.pill {
  display: flex; align-items: center; gap: 5px;
  padding: 2px 8px; border-radius: 3px;
  border: 1.5px solid transparent;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.68rem; font-weight: 500;
  cursor: pointer; background: #ECEAE4; color: #6b7c8d; white-space: nowrap;
}
.pill:hover { border-color: currentColor; }
.pill.active { background: var(--navy-mid); color: white; border-color: var(--navy-mid); }
.pill-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.result-count {
  margin-left: auto;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted);
}

/* ── Main layout ── */
.main-wrap {
  display: grid; grid-template-columns: 200px 1fr;
  max-width: 1140px; margin: 0 auto;
  padding: 24px 32px 80px; gap: 0;
}

/* ── Left decade nav ── */
.decade-nav { padding-top: 8px; padding-right: 24px; align-self: start; }
.decade-nav-label {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.68rem; font-weight: 600;
  letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--muted); margin-bottom: 12px;
}
.decade-nav-item {
  display: flex; align-items: center; gap: 8px; padding: 5px 0;
  cursor: pointer; border: none; background: none; width: 100%; text-align: left;
}
.decade-nav-year {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.82rem; font-weight: 600; color: var(--muted); min-width: 36px;
}
.decade-nav-item.active .decade-nav-year { color: var(--navy-mid); }
.decade-nav-bar {
  height: 3px; background: var(--divider); border-radius: 2px;
  flex: 1; position: relative; overflow: hidden;
}
.decade-nav-item.active .decade-nav-bar { background: var(--spine); }
.decade-nav-fill {
  position: absolute; left: 0; top: 0; height: 100%;
  background: var(--navy-mid); border-radius: 2px;
}
.decade-nav-count { font-size: 0.68rem; color: var(--muted); min-width: 20px; text-align: right; }

/* ── Density chart ── */
.density-wrap {
  margin-bottom: 24px; padding: 12px 16px;
  background: white; border: 1px solid var(--divider); border-radius: 3px;
}
.density-label {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.68rem; font-weight: 600;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px;
}
.density-chart { display: flex; align-items: flex-end; gap: 2px; height: 48px; }
.density-bar-wrap {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; height: 100%; justify-content: flex-end; cursor: pointer; gap: 3px;
}
.density-bar { width: 100%; border-radius: 2px 2px 0 0; background: var(--spine); min-height: 2px; }
.density-bar-wrap:hover .density-bar,
.density-bar-wrap.active .density-bar { background: var(--navy-mid); }
.density-bar-year { font-size: 0.6rem; color: var(--muted); white-space: nowrap; }

/* ── Decade section headings ── */
.decade-section { margin-bottom: 0; }
.decade-heading {
  display: flex; align-items: center; gap: 16px;
  padding: 20px 0 12px; position: static;
  background: var(--bg);
}
.decade-heading::before {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0;
  height: 1px; background: var(--divider);
}
.decade-year-label {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 1.1rem; font-weight: 700; color: var(--navy); letter-spacing: -0.01em; line-height: 1;
}
.decade-pill {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--muted); background: var(--divider); padding: 2px 7px; border-radius: 10px;
}

/* ── Spine ── */
.timeline-wrap { position: relative; }
.events-column { position: relative; padding-left: 32px; padding-top: 4px; }
.spine-line { position: absolute; left: 8px; top: 0; bottom: 0; width: 2px; background: var(--divider); }

/* ── Event rows ── */
.event-row {
  display: grid; grid-template-columns: 90px 1fr;
  gap: 0 16px; padding: 0; margin-bottom: 0.6rem;
  align-items: start; position: relative; opacity: 1;
}
.event-row.filtered-out { display: none; }
.event-date-col { text-align: right; padding-top: 2px; position: relative; }
.event-date {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); line-height: 1.4;
}
.spine-dot {
  position: absolute; right: -25px; top: 5px;
  width: 10px; height: 10px; border-radius: 50%;
  border: 2px solid var(--bg); box-shadow: 0 0 0 1.5px var(--spine); z-index: 2;
}
.event-row:hover .spine-dot { transform: scale(1.3); }

/* ── Event cards — Sources Timeline card style ── */
.event-card {
  background: white;
  border: 1px solid #ddd8cc;
  border-left: 3px solid var(--navy-mid);
  border-radius: 3px;
  padding: 0.9rem 1.1rem;
  cursor: default;
}
.event-row:hover .event-card { box-shadow: 0 1px 6px rgba(26,58,92,0.08); }
.event-card-top { display: flex; align-items: flex-start; gap: 6px; margin-bottom: 3px; }

/* ── Category badge — tag style, per-colour ── */
.event-category-badge {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.68rem; font-weight: 500;
  letter-spacing: 0.07em; text-transform: uppercase;
  padding: 2px 6px; border-radius: 3px;
  white-space: nowrap; flex-shrink: 0; margin-top: 1px;
}

/* ── Event text ── */
.event-title {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 0.95rem; font-weight: 700;
  color: var(--navy-mid); margin-bottom: 0.2rem; letter-spacing: 0.01em;
}
.event-desc {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.83rem; line-height: 1.5; color: #3a3a3a;
}
.event-source {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.72rem; color: var(--muted); margin-top: 4px; font-style: italic;
}
.no-results {
  padding: 48px 0; text-align: center;
  color: var(--muted); font-style: italic; font-size: 0.9rem;
}

/* ── Edit controls ── */
.edit-btn {
  position: absolute; top: 8px; right: 8px;
  width: 26px; height: 26px; border-radius: 4px;
  border: 1px solid var(--divider); background: var(--bg); color: var(--muted);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  opacity: 0; flex-shrink: 0;
}
.event-row:hover .edit-btn { opacity: 1; }
.edit-btn:hover { background: var(--navy-mid); color: white; border-color: var(--navy-mid); }
.edit-form { display: flex; flex-direction: column; gap: 8px; }
.edit-textarea {
  width: 100%; font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.83rem; line-height: 1.5; color: #1a1a2e;
  background: #FAFAF8; border: 1.5px solid var(--navy-mid);
  border-radius: 3px; padding: 8px 10px; resize: vertical; min-height: 80px; outline: none;
}
.edit-source-input {
  font-family: 'IBM Plex Sans', sans-serif; font-size: 0.72rem; color: var(--muted);
  background: #FAFAF8; border: 1.5px solid var(--divider);
  border-radius: 3px; padding: 5px 8px; outline: none; width: 100%;
}
.edit-actions { display: flex; gap: 6px; justify-content: flex-end; }
.edit-save-btn {
  padding: 4px 14px; background: var(--navy-mid); color: white;
  border: none; border-radius: 3px;
  font-family: 'IBM Plex Sans', sans-serif; font-size: 0.72rem; font-weight: 600; cursor: pointer;
}
.edit-cancel-btn {
  padding: 4px 10px; background: none; color: var(--muted);
  border: 1px solid var(--divider); border-radius: 3px;
  font-family: 'IBM Plex Sans', sans-serif; font-size: 0.72rem; cursor: pointer;
}
.edited-marker {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  color: #6b7c8d; margin-left: auto; align-self: center;
}

/* ── Tweaks panel — not needed in app context ── */
.tweaks-panel { display: none; }

/* ── Responsive ── */
@media (max-width: 700px) {
  .page-header  { padding: 1rem 16px 0.75rem; }
  .header-stats { display: none; }
  .controls-bar { padding: 10px 16px; }
  .main-wrap    { grid-template-columns: 1fr; padding: 12px; }
  .decade-nav   { display: none; }
}
</style>
"""

CAT_MAP = {
    "UNIFIL":                 "unifil",
    "Israel-Lebanon":         "israel-lb",
    "Hezbollah":              "hezbollah",
    "Lebanese Politics":      "lb-politics",
    "Regional / International": "regional-intl",
}

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]


def _parse_date(date_str):
    import re
    date_str = str(date_str).strip()
    # Handle "Mon YYYY" or "DD Mon YYYY" format
    month_names = ["jan","feb","mar","apr","may","jun",
                   "jul","aug","sep","oct","nov","dec"]
    words = date_str.split()
    for w in words:
        if w.lower() in month_names:
            # find the year (4-digit number)
            for ww in words:
                if re.match(r'^\d{4}$', ww):
                    year = int(ww)
                    return date_str, year
    # Handle YYYY, YYYY-MM, YYYY-MM-DD
    parts = date_str.split("-")
    try:
        year = int(parts[0])
    except ValueError:
        return date_str, 0
    if len(parts) == 1:
        return date_str, year
    elif len(parts) == 2:
        try:
            month = MONTHS[int(parts[1]) - 1]
            return f"{month} {year}", year
        except (ValueError, IndexError):
            return date_str, year
    else:
        try:
            month = MONTHS[int(parts[1]) - 1]
            return f"{int(parts[2])} {month} {year}", year
        except (ValueError, IndexError):
            return date_str, year


def load_events(json_path="data/unifil_timeline.json"):
    raw = json.loads(Path(json_path).read_text())
    events = []
    for item in raw:
        display_date, year = _parse_date(item["date"])
        events.append({
            "year":   year,
            "date":   display_date,
            "cat":    CAT_MAP.get(item["category"], "regional-intl"),
            "title":  item["event"],
            "desc":   item["description"],
            "source": item.get("source", ""),
        })
    events.sort(key=lambda e: e["year"])
    return events


def build_html(json_path="data/unifil_timeline.json",
               html_path="Event Timeline.html"):
    events = load_events(json_path)
    html = Path(html_path).read_text(encoding="utf-8")
    events_json = json.dumps(events, ensure_ascii=False)
    html = re.sub(
        r'const EVENTS = \[.*?\];',
        f'const EVENTS = {events_json};',
        html,
        flags=re.DOTALL,
    )
    # Update header stats to reflect real counts
    min_year = min(e["year"] for e in events)
    max_year = max(e["year"] for e in events)
    years_covered = max_year - min_year + 1
    html = re.sub(
        r'(<div class="stat-num">)\d+(</div><div class="stat-label">Events</div>)',
        rf'\g<1>{len(events)}\2',
        html,
    )
    html = re.sub(
        r'(<div class="stat-num">)\d+(</div><div class="stat-label">Years Covered</div>)',
        rf'\g<1>{years_covered}\2',
        html,
    )
    # Also fix the yearMin/yearMax initial state and MIN/MAX_YEAR constants
    html = html.replace(
        'const [yearMin, setYearMin] = useState(1969);',
        'const [yearMin, setYearMin] = useState(1945);',
    )
    html = html.replace(
        'const [yearMax, setYearMax] = useState(2006);',
        f'const [yearMax, setYearMax] = useState({max_year});',
    )
    html = html.replace(
        'const MIN_YEAR = 1969; const MAX_YEAR = 2006;',
        f'const MIN_YEAR = 1945; const MAX_YEAR = {max_year};',
    )
    # Strip ALL <style> blocks from the Design HTML
    html = re.sub(r'<style>.*?</style>', '', html, flags=re.DOTALL)
    # Strip any external stylesheet <link> tags
    html = re.sub(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', '', html, flags=re.IGNORECASE)
    # Inject the single authoritative app stylesheet before </head>
    html = html.replace('</head>', f'{_STYLE_OVERRIDES}</head>', 1)
    Path("debug_timeline.html").write_text(html, encoding="utf-8")
    return html
