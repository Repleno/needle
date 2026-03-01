#!/usr/bin/env python3
"""
Reddit Outreach Scout
=====================
Scans Reddit daily for buying signals and pain points, sends an email report.
Runs locally via cron. Results land in your inbox every morning.

ARCHITECTURE:
  1. keyword_searches (from config.json) are sent to Reddit's search API (t=week).
  2. subreddits (from config.json) are scanned via /new to catch fresh posts.
  3. Every collected post is scored using RELEVANCE_KEYWORDS (weighted keyword matching).
  4. Posts below SCORE_THRESHOLD or older than RECENT_HOURS are discarded.
  5. SKIP_PATTERNS filter out job postings, self-promo, etc. (score = -1).
  6. Astroturfing detection penalizes fake product recommendations (-5).
  7. Only posts that make it into the email are marked as "seen" (TTL: SEEN_TTL_DAYS).
  8. Results are sent as an HTML email via Brevo API.

HOW TO CUSTOMIZE:
  - To change WHAT is searched: edit keyword_searches in config.json
  - To change WHERE is searched: edit subreddits in config.json
  - To change HOW posts are scored: edit RELEVANCE_KEYWORDS below (keyword, weight) pairs
  - To change WHAT is filtered out: edit SKIP_PATTERNS below (regex patterns)
  - To tune sensitivity: adjust the constants in the "Tuning constants" block below

SCORING EXPLAINED:
  Each post gets points for every RELEVANCE_KEYWORD found in title + body + subreddit.
  Weight 3 = strong signal (e.g. "out of stock", "ran out")
  Weight 2 = medium signal (e.g. "spreadsheet", "forgot", "chaos")
  Weight 1 = weak/contextual signal (e.g. "tool", "recommend", "app")
  Score is capped at 20, then astroturfing penalty (-5) and young account penalty (-2)
  are subtracted. Posts below SCORE_THRESHOLD are discarded.
"""

import json
import time
import sys
import re
import os
from html import escape as html_escape
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Paths (relative to this script — works locally) ─────
BASE_DIR    = Path(__file__).parent
SCRIPT_DIR  = BASE_DIR / "scripts"
CONFIG_FILE = BASE_DIR / "config.json"
SEEN_FILE   = BASE_DIR / "seen_posts.json"

# ── Default settings (overridden by config.json) ─────────────────────────────
DEFAULT_SETTINGS = {
    "score_threshold": 5,      # Minimum score for a post to appear in the report
    "recent_hours": 24,        # Only show posts created within this window
    "seen_ttl_days": 7,        # Sent posts won't reappear for this many days
    "search_time": "week",     # Reddit search time filter (day/week/month/year/all)
    "max_results": 10,         # Max posts per email report
}

# ── Relevance keywords for scoring (keyword, weight) ─────────────────────────
# Edit these to match your business. Higher weight = stronger signal.
# Use pain-point language, not solution language:
#   Bad:  ("inventory software", 3)
#   Good: ("out of stock", 3), ("forgot to reorder", 3)
# Keep weights balanced — too many weak (1-point) keywords create noise.
RELEVANCE_KEYWORDS = [
    # Strong signal (weight 3) — clear buying pain or problem statement
    ("inventory", 3), ("stock", 3), ("reorder", 3), ("replenish", 3),
    ("out of stock", 3), ("ran out", 3), ("bill of materials", 3),
    # Medium signal (weight 2) — related context
    ("material", 2), ("supplies", 2), ("supply", 2),
    ("excel", 2), ("spreadsheet", 2), ("manual", 2), ("tracking", 2),
    ("ordering", 2), ("overstock", 2), ("forgot", 2), ("chaos", 2),
    ("warehouse", 2), ("procurement", 2), ("purchase order", 2), ("bom", 2),
    # Weak/contextual signal (weight 1) — be selective here
    ("small business", 1), ("contractor", 1), ("craftsman", 1),
    ("tool", 1), ("recommend", 1), ("software", 1), ("app", 1),
]

# ── Skip patterns — posts matching these are excluded immediately ─────────────
SKIP_PATTERNS = [
    r"\[hiring\]", r"\[job\]", r"job posting", r"we're hiring",
    r"for sale", r"selling", r"buy my", r"check out my",
    r"i made this", r"launched", r"introducing", r"promocode",
]

# ── Astroturfing detection ────────────────────────────────────────────────────
# A post is penalized (-5) if ALL THREE conditions are met:
#   1. Contains a specific product name (capitalized, not in GENERIC_PRODUCT_TERMS)
#   2. Mentions 3+ feature keywords from ASTRO_FEATURE_KEYWORDS
#   3. Has a positive conclusion phrase (without a dissatisfaction signal)
# This catches fake product testimonials while preserving genuine leads.
GENERIC_PRODUCT_TERMS = {
    "excel", "sheets", "google sheets", "erp", "crm", "saas", "software",
    "app", "tool", "system", "spreadsheet", "database", "notion", "airtable",
    "trello", "slack", "quickbooks", "xero", "sap", "oracle", "shopify",
    "woocommerce", "monday", "asana", "jira", "zoho", "hubspot",
}

ASTRO_FEATURE_KEYWORDS = [
    "tracking", "crm", "ordering", "dashboard", "analytics", "integration",
    "automation", "reporting", "scanning", "barcode", "sync", "alerts",
    "notifications", "forecasting", "purchasing", "receiving", "workflow",
    "api", "mobile app", "cloud", "real-time", "real time", "insights",
]

ASTRO_POSITIVE_PHRASES = [
    "what stood out was", "game changer", "game-changer", "changed how i",
    "didn't fix everything but", "did not fix everything but",
    "highly recommend", "can't imagine going back", "never looked back",
    "transformed our", "revolutionized", "wish i had found",
    "blown away", "exceeded expectations", "worth every penny",
    "solved our", "exactly what we needed", "perfect solution",
    "best decision", "so much easier", "saves us so much",
]

ASTRO_DISSATISFACTION_PHRASES = [
    "looking for alternatives", "alternative to", "currently using",
    "frustrated with", "annoyed with", "fed up with", "has anyone compared",
    "switching from", "moving away from", "thinking of leaving",
    "disappointed with", "unhappy with", "not happy with",
    "doesn't work", "does not work", "broken", "missing feature",
    "anyone else have issues", "problems with", "issue with",
]

COMMON_WORDS = {
    "we", "i", "it", "the", "this", "that", "they", "he", "she", "you",
    "our", "my", "his", "her", "their", "its", "your", "what", "when",
    "where", "who", "how", "why", "which", "not", "but", "and", "for",
    "with", "has", "had", "have", "was", "were", "are", "been", "being",
    "got", "get", "did", "does", "do", "can", "will", "just", "also",
    "after", "before", "since", "while", "though", "although", "because",
    "reddit", "post", "update", "edit", "tldr", "thanks", "thank",
}


# ── Constants ─────────────────────────────────────────────────────────────────
# Logo SVG encoded as base64 (split for line length compliance)
LOGO_BASE64 = (
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1"
    "MTIgNTEyIiB3aWR0aD0iNTEyIiBoZWlnaHQ9IjUxMiI+CiAgPGRlZnM+CiAgICA8IS0tIEdy"
    "YWRpZW50cyAtLT4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iYmdHcmFkaWVudCIgeDE9IjAl"
    "IiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUi"
    "IHN0b3AtY29sb3I9IiMwZjE3MmEiIC8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3Rv"
    "cC1jb2xvcj0iIzFlMjkzYiIgLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFy"
    "R3JhZGllbnQgaWQ9Im5lZWRsZUdyYWRpZW50IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUi"
    "IHkyPSIxMDAlIj4KICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiNhNWI0ZmMi"
    "IC8+CiAgICA8c3RvcCBvZmZzZXQ9IjUwJSIgc3RvcC1jb2xvcj0iIzYzNjZmMSIgLz4KICAg"
    "IDxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iIzQzMzhjYSIgLz4KICAgIDwvbGlu"
    "ZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9InNpZ25hbEdyYWRpZW50IiB4"
    "MT0iMCUiIHkxPSIxMDAlIiB4Mj0iMTAwJSIgeTI9IjAlIj4KICAgIDxzdG9wIG9mZnNldD0i"
    "MCUiIHN0b3AtY29sb3I9IiMyMmM1NWUiIC8+CiAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0"
    "b3AtY29sb3I9IiMxMGI5ODEiIC8+CiAgICA8L2xpbmVhckdyYWRpZW50PgogICAgCiAgICA8"
    "IS0tIEdsb3cgRWZmZWN0IC0tPgogICAgPGZpbHRlciBpZD0iZ2xvd3ciIHg9Ii0yMCUiIHk9"
    "Ii0yMCUiIHdpZHRoPSIxNDAlIiBoZWlnaHQ9IjE0MCUiPgogICAgICA8ZmVHYXVzc2lhbkJs"
    "dXIgc3RkRGV2aWF0aW9uPSI2IiByZXN1bHQ9ImJsdXIiIC8+CiAgICAgIDxmZUNvbXBvc2l0"
    "ZSBpbj0iU291cmNlR3JhcGhpYyIgaW4yPSJibHVyIiBvcGVyYXRvcj0ib3ZlciIgLz4KICAg"
    "IDwvZmlsdGVyPgogICAgPGZpbHRlciBpZD0iZ2xvd1N0cm9uZyIgeD0iLTMwJSIgeT0iLTMw"
    "JSIgd2lkdGg9IjE2MCUiIGhlaWdodD0iMTYwJSI+CiAgICAgIDxmZUdhdXNzaWFuQmx1ciBz"
    "dGREZXZpYXRpb249IjEyIiByZXN1bHQ9ImJsdXIiIC8+CiAgICAgIDxmZUNvbXBvc2l0ZSBp"
    "bj0iU291cmNlR3JhcGhpYyIgaW4yPSJibHVyIiBvcGVyYXRvcj0ib3ZlciIgLz4KICAgIDwv"
    "ZmlsdGVyPgogIDwvZGVmcz4KCiAgPCEtLSBCYWNrZ3JvdW5kIC0tPgogIDxyZWN0IHdpZHRo"
    "PSI1MTIiIGhlaWdodD0iNTEyIiByeD0iMTEyIiBmaWxsPSJ1cmwoI2JnR3JhZGllbnQpIiAv"
    "PgogIAogIDwhLS0gUmFkYXIgLyBIYXlzdGFjayBBYnN0cmFjdGlvbiAtLT4KICA8ZyB0cmFu"
    "c2Zvcm09InRyYW5zbGF0ZSgyNTYsIDI1NikiPgogICAgPGNpcmNsZSByPSIxODAiIGZpbGw9"
    "Im5vbmUiIHN0cm9rZT0iIzMzNDE1NSIgc3Ryb2tlLXdpZHRoPSIyIiAvPgogICAgPGNpcmNs"
    "ZSByPSIxMzAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzQ3NTU2OSIgc3Ryb2tlLXdpZHRoPSI0"
    "IiBzdHJva2UtZGFzaGFycmF5PSIxMiAxNiIgLz4KICAgIDxjaXJjbGUgcj0iODAiIGZpbGw9"
    "Im5vbmUiIHN0cm9rZT0iIzY0NzQ4YiIgc3Ryb2tlLXdpZHRoPSIyIiBvcGFjaXR5PSIwLjUi"
    "IC8+CiAgPC9nPgoKICA8IS0tIFRoZSBOZWVkbGUgLS0+CiAgPGcgdHJhbnNmb3JtPSJyb3Rh"
    "dGUoNDUgMjU2IDI1NikiPgogICAgPCEtLSBOZWVkbGUgQm9keSAtLT4KICAgIDxwYXRoIGQ9"
    "Ik0yNTIgODAgTDI2MCA4MCBMMjY2IDM4MCBMMjU2IDQ0MCBMMjQ2IDM4MCBaIiBmaWxsPSJ1"
    "cmwoI25lZWRsZUdyYWRpZW50KSIgZmlsdGVyPSJ1cmwoI2dsb3cpIiAvPgogICAgPCEtLSBO"
    "ZWVkbGUgRXllIC0tPgogICAgPGVsbGlwc2UgY3g9IjI1NiIgY3k9IjEzMCIgcng9IjMiIHJ5"
    "PSIxNiIgZmlsbD0iIzBmMTcyYSIgLz4KICAgIDwhLS0gSGlnaGxpZ2h0IFJlZmxlY3Rpb24g"
    "LS0+CiAgICA8cGF0aCBkPSJNMjU0IDkwIEwyNTYgOTAgTDI1OCAzNTAgTDI1NiAzNjAgTDI1"
    "NCAzNTAgWiIgZmlsbD0iI2ZmZmZmZiIgb3BhY2l0eT0iMC40IiAvPgogIDwvZz4KCiAgPCEt"
    "LSBUaGUgU2lnbmFsIChUaGUgZm91bmQgaXRlbSAvIEJ1eWluZyBTaWduYWwpIC0tPgogIDxn"
    "IHRyYW5zZm9ybT0idHJhbnNsYXRlKDMyMCwgMTYwKSIgZmlsdGVyPSJ1cmwoI2dsb3dTdHJv"
    "bmcpIj4KICAgIDxjaXJjbGUgY3g9IjAiIGN5PSIwIiByPSIxNiIgZmlsbD0idXJsKCNzaWdu"
    "YWxHcmFkaWVudCkiIC8+CiAgICA8Y2lyY2xlIGN4PSIwIiBjeT0iMCIgcj0iMzIiIGZpbGw9"
    "Im5vbmUiIHN0cm9rZT0iIzIyYzU1ZSIgc3Ryb2tlLXdpZHRoPSI0IiBvcGFjaXR5PSIwLjYi"
    "IC8+CiAgICA8Y2lyY2xlIGN4PSIwIiBjeT0iMCIgcj0iNDgiIGZpbGw9Im5vbmUiIHN0cm9r"
    "ZT0iIzIyYzU1ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtZGFzaGFycmF5PSI2IDYiIG9w"
    "YWNpdHk9IjAuMyIgLz4KICA8L2c+Cjwvc3ZnPg=="
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg: str):
    """Log a message with timestamp to stdout."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def validate_config(cfg: dict) -> list[str]:
    """Validate config and return list of warnings/errors."""
    errors = []
    _s = cfg.get("settings", {})

    # Validate numeric settings
    if not isinstance(_s.get("score_threshold", 5), int) or _s.get("score_threshold", 5) < 0:
        errors.append("settings.score_threshold must be a non-negative integer")
    if not isinstance(_s.get("recent_hours", 24), int) or _s.get("recent_hours", 24) < 1:
        errors.append("settings.recent_hours must be a positive integer")
    if not isinstance(_s.get("seen_ttl_days", 7), int) or _s.get("seen_ttl_days", 7) < 1:
        errors.append("settings.seen_ttl_days must be a positive integer")
    if not isinstance(_s.get("max_results", 10), int) or _s.get("max_results", 10) < 1:
        errors.append("settings.max_results must be a positive integer")
    if _s.get("search_time", "week") not in ("hour", "day", "week", "month", "year", "all"):
        errors.append("settings.search_time must be one of: hour, day, week, month, year, all")

    # Validate email
    if not cfg.get("from_email"):
        errors.append("from_email is required (set via FROM_EMAIL env var or config.json)")
    if not cfg.get("to_email"):
        errors.append("to_email is required (set via TO_EMAIL env var or config.json)")

    # Validate arrays
    if not cfg.get("keyword_searches") and not cfg.get("subreddits"):
        errors.append("At least one of keyword_searches or subreddits must be configured")

    return errors


def load_config() -> dict:
    """Load and validate config from config.json and environment variables."""
    if not CONFIG_FILE.exists():
        print("ERROR: config.json not found.")
        sys.exit(1)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = json.load(f)

    # Email addresses: env var overrides config.json
    cfg["from_email"] = os.environ.get("FROM_EMAIL", cfg.get("from_email", ""))
    cfg["to_email"]   = os.environ.get("TO_EMAIL",   cfg.get("to_email", ""))

    # Brevo API key: ONLY from env var, never from config.json
    api_key = os.environ.get("BREVO_API_KEY", "")
    if not api_key:
        print("ERROR: Environment variable BREVO_API_KEY is not set.")
        print("Set it in .env.local or export BREVO_API_KEY='xkeysib-...'")
        sys.exit(1)
    cfg["brevo_api_key"] = api_key

    # Validate config
    errors = validate_config(cfg)
    if errors:
        print("CONFIG ERRORS:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    return cfg


def load_seen(seen_ttl_days: int) -> dict:
    """Load seen posts as {id: timestamp} dict, purge entries older than seen_ttl_days."""
    if SEEN_FILE.exists():
        with open(SEEN_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        # Migration: old format (list) → new format (dict)
        if isinstance(raw, list):
            return {}
        cutoff = (datetime.now(timezone.utc) - timedelta(days=seen_ttl_days)).timestamp()
        return {k: v for k, v in raw.items() if v > cutoff}
    return {}


def save_seen(seen: dict):
    """Save seen posts dict to disk."""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f)


# ── Reddit API (module-level import) ──────────────────────────────────────────
sys.path.insert(0, str(SCRIPT_DIR))
try:
    from reddit_api import api_get, clean_post
    _HAS_REDDIT_API = True
except ImportError:
    _HAS_REDDIT_API = False


def _enrich(raw_posts: list[dict]) -> list[dict]:
    """Apply clean_post() and attach author_created_utc for age checks."""
    result: list[dict] = []
    for p in raw_posts:
        cleaned = clean_post(p)
        cleaned["author_created_utc"] = p.get("data", p).get("author_created_utc")
        result.append(cleaned)
    return result


def fetch_subreddit(subreddit: str, sort: str = "new", limit: int = 15) -> list[dict]:
    """Fetch posts from a subreddit via /r/{subreddit}/{sort}.json."""
    if not _HAS_REDDIT_API:
        return []
    try:
        data = api_get(f"r/{subreddit}/{sort}", {"limit": min(limit, 100)})
        return _enrich(data.get("data", {}).get("children", []))
    except (RuntimeError, OSError, ValueError) as e:
        log(f"  ⚠ Error fetching r/{subreddit}: {e}")
        return []


def search_reddit(query: str, sort: str = "new", time_filter: str = "week", limit: int = 10) -> list[dict]:
    """Search Reddit-wide for posts matching a query."""
    if not _HAS_REDDIT_API:
        return []
    try:
        params = {
            "q": query, "sort": sort, "t": time_filter,
            "limit": min(limit, 100), "type": "link"
        }
        data = api_get("search", params)
        return _enrich(data.get("data", {}).get("children", []))
    except (RuntimeError, OSError, ValueError) as e:
        log(f"  ⚠ Error searching \"{query}\": {e}")
        return []


# ── Scoring ───────────────────────────────────────────────────────────────────

def detect_astroturfing_penalty(post: dict) -> int:
    """Returns a negative penalty if the post looks like astroturfing. See rules above."""
    raw_text = (post.get("title") or "") + " " + (post.get("selftext") or "")
    text = raw_text.lower()
    penalty = 0

    # 1. Specific product name (capitalized word, not a generic term)
    body = post.get("selftext") or ""
    body_sentence_starters = set(re.findall(r'(?:(?:^|[.!?])\s*)([A-Z][a-zA-Z]+)', body))
    candidates = re.findall(r'\b[A-Z][a-zA-Z]{2,}(?:\s[A-Z][a-zA-Z]+)?\b', raw_text)
    specific_products = [
        p for p in candidates
        if p.lower() not in GENERIC_PRODUCT_TERMS
        and p.lower() not in COMMON_WORDS
        and p not in body_sentence_starters
    ]
    has_product  = len(specific_products) > 0

    # 2. Three or more feature keywords attributed to the product
    has_features = sum(1 for kw in ASTRO_FEATURE_KEYWORDS if kw in text) >= 3

    # 3. Positive conclusion without a genuine dissatisfaction signal
    has_positive  = any(phrase in text for phrase in ASTRO_POSITIVE_PHRASES)
    has_complaint = any(phrase in text for phrase in ASTRO_DISSATISFACTION_PHRASES)

    if has_product and has_features and has_positive and not has_complaint:
        penalty -= 5

    # Young account penalty
    author_created = post.get("author_created_utc")
    if author_created:
        age_days = (datetime.now(timezone.utc) - datetime.fromtimestamp(float(author_created), tz=timezone.utc)).days
        if age_days < 30:
            penalty -= 2

    return penalty


def score_post(post: dict, relevance_keywords: list, skip_patterns: list) -> int:
    """Calculate relevance score (0–20) with penalties. Returns -1 for skipped posts."""
    text = (
        (post.get("title") or "") + " " +
        (post.get("selftext") or "") + " " +
        (post.get("subreddit") or "")
    ).lower()

    for skip_pattern in skip_patterns:
        if re.search(skip_pattern, text, re.IGNORECASE):
            return -1

    score = 0
    for keyword, weight in relevance_keywords:
        # Use word boundaries to avoid false positives (e.g. "stock" matching "stockbroker")
        kw_pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(kw_pattern, text):
            score += weight

    score = min(score, 20)
    score += detect_astroturfing_penalty(post)
    return score


def is_recent(post: dict, recent_hours: int) -> bool:
    """Returns True if the post was created within the last recent_hours hours."""
    created = post.get("created_utc")
    if not created:
        return False
    cutoff    = datetime.now(timezone.utc) - timedelta(hours=recent_hours)
    post_time = datetime.fromtimestamp(float(created), tz=timezone.utc)
    return post_time >= cutoff


# ── Collection & filtering ────────────────────────────────────────────────────

def collect_posts(cfg: dict, search_time: str) -> list[dict]:
    """Collect all posts from keyword searches + subreddit scans, deduplicated by ID."""
    all_posts  = {}
    searches   = cfg.get("keyword_searches", [])
    subreddits = cfg.get("subreddits", [])
    total      = len(searches) + len(subreddits)
    done       = 0

    for query in searches:
        posts = search_reddit(query, sort="new", time_filter=search_time, limit=10)
        for p in posts:
            pid = p.get("id") or p.get("url")
            if pid and pid not in all_posts:
                all_posts[pid] = p
        done += 1
        log(f"  [{done}/{total}] Search: \"{query}\" → {len(posts)} posts")
        time.sleep(2)

    for sub_entry in subreddits:
        subreddit, limit = sub_entry[0], sub_entry[1]
        posts = fetch_subreddit(subreddit, sort="new", limit=limit)
        for p in posts:
            pid = p.get("id") or p.get("url")
            if pid and pid not in all_posts:
                all_posts[pid] = p
        done += 1
        log(f"  [{done}/{total}] Subreddit: r/{subreddit} → {len(posts)} posts")
        time.sleep(2)

    return list(all_posts.values())


def filter_and_score(posts: list[dict], seen: dict, settings: dict,
                     relevance_keywords: list, skip_patterns: list) -> list[dict]:
    """Filter, score, and rank posts. Returns top max_results above score_threshold."""
    results = []
    score_threshold = settings["score_threshold"]
    recent_hours = settings["recent_hours"]
    max_results = settings["max_results"]

    for post in posts:
        pid = post.get("id") or post.get("url") or ""
        if pid in seen:
            continue
        if not is_recent(post, recent_hours):
            continue
        score = score_post(post, relevance_keywords, skip_patterns)
        if score < score_threshold:
            continue
        post["_score"] = score
        results.append(post)

    results.sort(key=lambda x: (-x["_score"], -float(x.get("created_utc", 0))))
    return results[:max_results]


# ── Email ─────────────────────────────────────────────────────────────────────

def format_email_html(posts: list[dict], date_str: str, repo_url: str = "") -> str:
    """Build the HTML email report from scored posts."""
    if not posts:
        body = """
        <div style="text-align:center;padding:40px;color:#888;">
            <h2>🤫 Quiet day</h2>
            <p>No relevant posts found in the last 24 hours.</p>
        </div>"""
    else:
        cards = ""
        for post in posts:
            score     = post.get("_score", 0)
            subreddit = html_escape(post.get("subreddit", "?"))
            title     = html_escape(post.get("title", "(no title)"))
            raw_text  = (post.get("selftext") or "")[:300]
            truncated = len(post.get("selftext") or "") > 300
            text      = html_escape(raw_text) + ("…" if truncated else "")
            url = post.get("url") or post.get("permalink") or "#"
            if url.startswith("/r/"):
                url = "https://reddit.com" + url

            created = post.get("created_utc")
            age = ""
            if created:
                mins = int((datetime.now(timezone.utc) - datetime.fromtimestamp(float(created), tz=timezone.utc)).total_seconds() / 60)
                age  = f"{mins}min" if mins < 60 else f"{mins // 60}h"

            score_color = "#22c55e" if score >= 15 else "#f59e0b" if score >= 8 else "#94a3b8"

            cards += f"""
            <div style="border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                    <span style="background:#f1f5f9;color:#475569;font-size:12px;padding:2px 8px;border-radius:99px;">r/{subreddit}</span>
                    <div style="display:flex;gap:8px;align-items:center;">
                        {f'<span style="color:#94a3b8;font-size:12px;">{age} ago</span>' if age else ''}
                        <span style="background:{score_color};color:white;font-size:12px;font-weight:bold;padding:2px 8px;border-radius:99px;">Score {score}</span>
                    </div>
                </div>
                <h3 style="margin:0 0 8px 0;font-size:15px;color:#1e293b;">
                    <a href="{url}" style="color:#1e293b;text-decoration:none;">{title}</a>
                </h3>
                {f'<p style="margin:0 0 12px 0;color:#64748b;font-size:13px;line-height:1.5;">{text}</p>' if text else ''}
                <a href="{url}" style="color:#6366f1;font-size:13px;font-weight:500;">→ Open post</a>
            </div>"""

        body = f"""
        <div style="margin-bottom:20px;padding:14px 16px;background:#f8fafc;border-radius:8px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
            <span style="color:#1e293b;font-weight:600;">{len(posts)} relevant posts · last 24h</span>
            <div style="display:flex;gap:12px;font-size:12px;">
                <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#22c55e;margin-right:4px;vertical-align:middle;"></span>Score 15–20 · reach out now</span>
                <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#f59e0b;margin-right:4px;vertical-align:middle;"></span>Score 8–14 · check if it fits</span>
                <span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#94a3b8;margin-right:4px;vertical-align:middle;"></span>Score 5–7 · weak signal</span>
            </div>
        </div>
        {cards}"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:640px;margin:0 auto;padding:24px;color:#1e293b;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-bottom:2px solid #6366f1;padding-bottom:16px;margin-bottom:24px;">
        <tr>
            <td align="left" valign="middle">
                <h1 style="margin:0;font-size:20px;color:#6366f1;">needle</h1>
                <p style="margin:4px 0 0;color:#64748b;font-size:14px;">Found in the haystack · {date_str}</p>
            </td>
            <td align="right" valign="middle">
                <img src="data:image/svg+xml;base64,{LOGO_BASE64}" width="48" height="48" alt="needle logo" style="display:block;">
            </td>
        </tr>
    </table>
    {body}
    <div style="border-top:1px solid #e2e8f0;margin-top:32px;padding-top:16px;color:#94a3b8;font-size:12px;">
        Auto-generated{f' · <a href="{repo_url}" style="color:#94a3b8;">needle</a>' if repo_url else ''}
    </div>
</body></html>"""


def send_email(cfg: dict, subject: str, html: str, max_retries: int = 3) -> bool:
    """Send email via Brevo transactional email API with retry logic."""
    import urllib.request
    import urllib.error

    payload = json.dumps({
        "sender":      {"email": cfg["from_email"], "name": "needle"},
        "to":          [{"email": cfg["to_email"]}],
        "subject":     subject,
        "htmlContent": html,
    }).encode("utf-8")

    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=payload,
            headers={
                "api-key":      cfg["brevo_api_key"],
                "Content-Type": "application/json",
                "Accept":       "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
                log(f"Email sent: {result.get('messageId', 'ok')}")
                return True
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            log(f"Email error {e.code} (attempt {attempt}/{max_retries}): {error_body}")
            if e.code >= 500 and attempt < max_retries:
                time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s
                continue
            return False
        except OSError as e:
            log(f"Email error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            return False
    return False


def main():
    """Main entry point: collect posts, score, filter, and send email report."""
    log("=" * 50)
    log("Reddit Outreach Scout started")
    cfg  = load_config()

    # Build settings from defaults + config.json overrides
    _s = cfg.get("settings", {})
    settings = {
        "score_threshold": _s.get("score_threshold", DEFAULT_SETTINGS["score_threshold"]),
        "recent_hours":    _s.get("recent_hours",    DEFAULT_SETTINGS["recent_hours"]),
        "seen_ttl_days":   _s.get("seen_ttl_days",   DEFAULT_SETTINGS["seen_ttl_days"]),
        "search_time":     _s.get("search_time",     DEFAULT_SETTINGS["search_time"]),
        "max_results":     _s.get("max_results",     DEFAULT_SETTINGS["max_results"]),
    }

    # Keywords and skip patterns: config.json overrides module defaults
    relevance_keywords = _s.get("relevance_keywords", RELEVANCE_KEYWORDS)
    skip_patterns = _s.get("skip_patterns", SKIP_PATTERNS)

    seen = load_seen(settings["seen_ttl_days"])

    log("Collecting posts...")
    all_posts = collect_posts(cfg, settings["search_time"])
    log(f"Total collected: {len(all_posts)} posts (before filter)")

    top_posts = filter_and_score(all_posts, seen, settings, relevance_keywords, skip_patterns)
    log(f"After filter: {len(top_posts)} relevant posts (score >= {settings['score_threshold']})")

    # Mark ONLY sent posts as seen (with current timestamp for TTL tracking)
    now_ts   = datetime.now(timezone.utc).timestamp()
    new_seen = dict(seen)
    for p in top_posts:
        pid = p.get("id") or p.get("url")
        if pid:
            new_seen[pid] = now_ts
    save_seen(new_seen)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject  = (
        f"needle · {date_str} — {len(top_posts)} signal{'s' if len(top_posts) != 1 else ''} found"
        if top_posts else
        f"needle · {date_str} — quiet day"
    )
    repo_url = cfg.get("repo_url", "")
    html = format_email_html(top_posts, date_str, repo_url)
    send_email(cfg, subject, html)

    log("Reddit Outreach Scout finished")
    log("=" * 50)


if __name__ == "__main__":
    main()
