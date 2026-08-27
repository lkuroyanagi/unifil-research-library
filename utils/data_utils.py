import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

THEMATIC_CLUSTERS = [
    "Mandate evolution",
    "Member State, P5, UNSC Dynamics",
    "Tripartite Liaison Mechanism & Liaison",
    "Monitoring, reporting & technology",
    "TCC/Command",
    "Relations with Host State",
    "Protection of Civilians",
    "Force protection & safety",
    "Operational adaptation & innovation",
    "Relations with non-state armed actors",
    "De-mining",
    "CIMIC & community relations",
    "DPKO-DPPA integration",
    "Maritime Task Force",
]

SOURCE_TYPES = ["Academic", "Policy", "Think Tank", "UN Document", "Opinion / Primary", "Media", "NGO", "Other"]

def load_sources():
    path = DATA_DIR / "sources.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_gaps():
    path = DATA_DIR / "gaps.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_gaps(gaps):
    path = DATA_DIR / "gaps.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(gaps, f, indent=2, ensure_ascii=False)

def save_sources(sources):
    path = DATA_DIR / "sources.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)

def load_actor_meta():
    path = DATA_DIR / "actors_meta.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_actor_meta(meta):
    path = DATA_DIR / "actors_meta.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

def get_all_tags(sources):
    tags = set()
    for s in sources:
        tags.update(s.get("tags", []))
    return sorted(tags)

def get_all_actors(sources):
    actors = set()
    for s in sources:
        actors.update(s.get("actors", []))
    return sorted(actors)

def get_all_countries(sources):
    countries = set()
    for s in sources:
        c = s.get("country_of_origin", "")
        if c:
            countries.add(c)
    return sorted(countries)

def filter_sources(sources, clusters=None, source_types=None, countries=None, 
                   search_query=None, year_range=None, tags=None):
    filtered = sources
    
    if clusters:
        filtered = [s for s in filtered if any(c in s.get("thematic_clusters", []) for c in clusters)]
    
    if source_types:
        filtered = [s for s in filtered if s.get("source_type") in source_types]
    
    if countries:
        filtered = [s for s in filtered if s.get("country_of_origin") in countries]
    
    if tags:
        filtered = [s for s in filtered if any(t in s.get("tags", []) for t in tags)]
    
    if year_range:
        filtered = [s for s in filtered if year_range[0] <= s.get("year", 0) <= year_range[1]]
    
    if search_query:
        q = search_query.lower()
        filtered = [s for s in filtered if (
            q in s.get("title", "").lower() or
            q in s.get("author", "").lower() or
            q in s.get("abstract", "").lower() or
            any(q in tag.lower() for tag in s.get("tags", [])) or
            any(q in actor.lower() for actor in s.get("actors", []))
        )]
    
    return filtered

def get_cluster_coverage(sources):
    coverage = {c: [] for c in THEMATIC_CLUSTERS}
    for s in sources:
        for c in s.get("thematic_clusters", []):
            if c in coverage:
                coverage[c].append(s)
    return coverage

def get_inferred_gaps(sources):
    coverage = get_cluster_coverage(sources)
    gaps = []
    for cluster, srcs in coverage.items():
        if len(srcs) < 2:
            gaps.append({
                "id": f"auto_{cluster.lower().replace(' ', '_').replace('&', 'and')[:30]}",
                "title": f"Thin coverage: {cluster}",
                "description": f"Only {len(srcs)} source(s) currently mapped to this cluster.",
                "thematic_clusters": [cluster],
                "status": "Open",
                "source": "Auto-inferred",
                "added_by": "System",
                "date_added": ""
            })
    return gaps
