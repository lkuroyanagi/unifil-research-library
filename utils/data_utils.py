import base64
import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

# Repo saves are committed to, and the branch on it. Both are overridable via
# env vars for testing/forking, but default to the deployed values.
GITHUB_REPO = os.environ.get("GITHUB_REPO", "lkuroyanagi/unifil-research-library")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
GITHUB_API = "https://api.github.com"


class GitHubSaveError(RuntimeError):
    """Raised when a save-to-GitHub commit fails. Callers should catch this
    specifically and show the user a clear message — a failure here means
    the edit was NOT persisted anywhere durable, so it must not be treated
    as a silent success."""


def _resolve_secret(name: str) -> str:
    """
    Resolve a secret by name, checked in this order (same precedence used
    for ANTHROPIC_API_KEY in utils/chat_utils.py — see that module for the
    full rationale):

    1. .env in the project root, for local development — re-read on every
       call with override=True so editing the file takes effect with no
       server restart. Skipped entirely if no .env file exists (e.g. on
       Streamlit Cloud), so it can never clobber a real deployment secret.
    2. The process environment — covers Streamlit Cloud, which injects every
       top-level secrets.toml key directly as an env var.
    3. st.secrets directly — a fallback for a secret that isn't mirrored
       into the environment (e.g. nested under a [section]).
    """
    if _ENV_PATH.exists():
        from dotenv import load_dotenv
        load_dotenv(_ENV_PATH, override=True)

    value = os.environ.get(name, "")
    if value:
        return value

    try:
        import streamlit as st
        secret = st.secrets.get(name, "")
        if secret:
            return secret
    except Exception:
        pass  # not running inside Streamlit, or no secrets.toml configured

    return ""


def _current_github_token() -> str:
    return _resolve_secret("GITHUB_TOKEN")


def _github_headers(token: str) -> dict:
    return {
        **({"Authorization": f"Bearer {token}"} if token else {}),
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _github_get_sha(repo_path: str, token: str):
    """Return the current blob SHA of a file in the repo, or None if it
    doesn't exist there yet (a fresh-create rather than an update)."""
    import requests
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{repo_path}"
    resp = requests.get(
        url, headers=_github_headers(token),
        params={"ref": GITHUB_BRANCH}, timeout=15,
    )
    if resp.status_code == 404:
        return None
    if not resp.ok:
        raise GitHubSaveError(
            f"Could not read current '{repo_path}' from GitHub "
            f"(HTTP {resp.status_code}): {resp.text[:300]}"
        )
    return resp.json().get("sha")


def _github_put_json(repo_path: str, data, commit_message: str):
    """
    Commit `data` (a JSON-serialisable object) to `repo_path` in GITHUB_REPO
    on GITHUB_BRANCH, via the GitHub Contents API. Fetches the current file's
    SHA first so the API can detect a concurrent edit (HTTP 409) rather than
    silently clobbering someone else's save.
    """
    import requests

    token = _current_github_token()
    if not token:
        raise GitHubSaveError(
            "No GITHUB_TOKEN configured — cannot save to GitHub. "
            "Set it in .env locally or in Streamlit Cloud's secrets."
        )

    sha = _github_get_sha(repo_path, token)

    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    payload = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{repo_path}"
    resp = requests.put(url, headers=_github_headers(token), json=payload, timeout=20)

    if resp.status_code == 409:
        raise GitHubSaveError(
            "Someone else saved a change to this file moments ago "
            "(GitHub rejected the commit as out of date). Please reload "
            "and try your edit again."
        )
    if resp.status_code in (401, 403):
        raise GitHubSaveError(
            f"GitHub rejected the save — the configured GITHUB_TOKEN is "
            f"invalid or lacks write access to {GITHUB_REPO} "
            f"(HTTP {resp.status_code})."
        )
    if not resp.ok:
        raise GitHubSaveError(
            f"GitHub save failed for '{repo_path}' (HTTP {resp.status_code}): "
            f"{resp.text[:300]}"
        )


def save_sources_to_github(sources):
    """Commit the full sources list to data/sources.json in GITHUB_REPO."""
    _github_put_json("data/sources.json", sources, "Update sources via web editor")


def save_gaps_to_github(gaps):
    """Commit the full gaps list to data/gaps.json in GITHUB_REPO."""
    _github_put_json("data/gaps.json", gaps, "Update gaps via web editor")

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

def _write_gaps_local(gaps):
    path = DATA_DIR / "gaps.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(gaps, f, indent=2, ensure_ascii=False)
        f.write("\n")

def _write_sources_local(sources):
    path = DATA_DIR / "sources.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)
        f.write("\n")

def save_gaps(gaps):
    """
    Persist the full gaps list. If a GITHUB_TOKEN is configured (typically:
    running on Streamlit Cloud), commits straight to the GitHub repo, then
    also mirrors the write locally so this running session's own reads stay
    consistent immediately — Streamlit Cloud's filesystem is ephemeral and
    won't reflect the new commit until the app is next redeployed, so without
    this the editor wouldn't even see their own save take effect.

    Raises GitHubSaveError if the GitHub commit fails (a stale conflicting
    edit, an invalid token, etc.) — the local mirror is intentionally
    skipped in that case, so a failed save is never mistaken for a saved one.
    With no GITHUB_TOKEN configured at all (plain local development), this
    is just a local file write, exactly as before.
    """
    if _current_github_token():
        save_gaps_to_github(gaps)
    _write_gaps_local(gaps)

def save_sources(sources):
    """See save_gaps() above — identical GitHub-or-local dispatch, for
    data/sources.json."""
    if _current_github_token():
        save_sources_to_github(sources)
    _write_sources_local(sources)

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
