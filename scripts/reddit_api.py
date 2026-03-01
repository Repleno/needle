#!/usr/bin/env python3
"""
Reddit public JSON API wrapper.

Uses Reddit's public JSON API — no account, no app registration, no credentials needed.
Works from any residential or office IP. Zero external dependencies (stdlib only).
"""
import json
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://www.reddit.com"
_UA      = "needle-scout/1.0 (github.com/Repleno/needle)"


def api_get(path: str, params: dict = None) -> dict:
    """Make a GET request to the Reddit public JSON API."""
    url = f"{BASE_URL}/{path}.json"
    merged = {"raw_json": "1"}
    if params:
        merged.update({k: v for k, v in params.items() if v is not None})
    url += "?" + urllib.parse.urlencode(merged)

    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RuntimeError("Rate limited — wait a moment and retry.") from exc
        if exc.code == 404:
            raise RuntimeError(f"Not found: {url}") from exc
        raise RuntimeError(f"HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc


def clean_post(p: dict) -> dict:
    """Extract the fields needle needs from a Reddit post object."""
    data = p.get("data", p)
    return {
        "id":               data.get("id"),
        "title":            data.get("title"),
        "subreddit":        data.get("subreddit"),
        "author":           data.get("author"),
        "score":            data.get("score"),
        "upvote_ratio":     data.get("upvote_ratio"),
        "num_comments":     data.get("num_comments"),
        "url":              data.get("url"),
        "permalink":        f"https://reddit.com{data.get('permalink', '')}",
        "selftext":         (data.get("selftext") or "")[:500],
        "created_utc":      data.get("created_utc"),
        "is_self":          data.get("is_self"),
        "link_flair_text":  data.get("link_flair_text"),
    }


def format_count(n) -> str:
    """Format large numbers (1234567 → 1.2M)."""
    if n is None:
        return "0"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def clean_comment(c: dict) -> dict:
    """Extract fields from a Reddit comment object."""
    data = c.get("data", c)
    return {
        "id":          data.get("id"),
        "author":      data.get("author"),
        "body":        (data.get("body") or "")[:300],
        "score":       data.get("score"),
        "created_utc": data.get("created_utc"),
    }


def clean_subreddit(s: dict) -> dict:
    """Extract fields from a Reddit subreddit object."""
    data = s.get("data", s)
    return {
        "name":         data.get("display_name"),
        "title":        data.get("title"),
        "description":  (data.get("public_description") or "")[:200],
        "subscribers":  data.get("subscribers"),
        "active_users": data.get("accounts_active"),
        "created_utc":  data.get("created_utc"),
        "url":          f"https://reddit.com/r/{data.get('display_name')}",
        "over18":       data.get("over18"),
    }


def clean_user(u: dict) -> dict:
    """Extract fields from a Reddit user object."""
    data = u.get("data", u)
    return {
        "name":          data.get("name"),
        "link_karma":    data.get("link_karma"),
        "comment_karma": data.get("comment_karma"),
        "created_utc":   data.get("created_utc"),
        "is_mod":        data.get("is_mod"),
        "verified":      data.get("verified"),
    }


def print_post(p: dict):
    """Print a post in a readable format."""
    if not p:
        return
    print(f"id:        {p.get('id', '')}")
    print(f"title:     {p.get('title', '')}")
    print(f"subreddit: r/{p.get('subreddit', '')}")
    print(f"author:    u/{p.get('author', '')}")
    ratio = int((p.get("upvote_ratio") or 0) * 100)
    print(f"score:     {format_count(p.get('score'))} ({ratio}% upvoted)")
    print(f"comments:  {format_count(p.get('num_comments'))}")
    print(f"url:       {p.get('permalink', '')}")
    if p.get("link_flair_text"):
        print(f"flair:     {p['link_flair_text']}")
    if p.get("selftext"):
        print("---")
        print(f"text: {p['selftext']}")


def print_subreddit(s: dict):
    """Print a subreddit in a readable format."""
    if not s:
        return
    print(f"name:        r/{s.get('name', '')}")
    print(f"title:       {s.get('title', '')}")
    print(f"subscribers: {format_count(s.get('subscribers'))}")
    print(f"active:      {format_count(s.get('active_users'))} online")
    print(f"nsfw:        {s.get('over18', False)}")
    print(f"url:         {s.get('url', '')}")
    if s.get("description"):
        print(f"description: {s['description']}")


def print_user(u: dict):
    """Print a user in a readable format."""
    if not u:
        return
    print(f"name:          u/{u.get('name', '')}")
    print(f"link_karma:    {format_count(u.get('link_karma'))}")
    print(f"comment_karma: {format_count(u.get('comment_karma'))}")
    print(f"verified:      {u.get('verified', False)}")
    print(f"is_mod:        {u.get('is_mod', False)}")


def print_posts_list(posts: list, label: str = "posts"):
    """Print a compact list of posts."""
    cleaned = [clean_post(p) for p in posts if p]
    print(f"{label}[{len(cleaned)}]{{title,subreddit,score,comments}}:")
    for p in cleaned:
        title    = (p["title"] or "")[:60]
        score    = format_count(p["score"])
        comments = format_count(p["num_comments"])
        print(f"  {title},r/{p['subreddit']},{score},{comments}")


def print_comments_list(comments: list, label: str = "comments"):
    """Print a compact list of comments."""
    cleaned = [clean_comment(c) for c in comments if c.get("kind") == "t1"]
    print(f"{label}[{len(cleaned)}]{{author,body,score}}:")
    for c in cleaned:
        body = (c["body"] or "")[:60].replace("\n", " ")
        print(f"  u/{c['author']},{body},{c['score']}")


def print_pagination(data: dict):
    """Print pagination cursor if more results are available."""
    after = data.get("after")
    if after:
        print("---")
        print("has_next_page: True")
        print(f"next_cursor: {after}")
