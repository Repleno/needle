# needle Agent Context

## Purpose
Reddit scout for buying signals. Scans, scores, and emails reports via Brevo.

## Tech Stack
- **Python 3.8+**: Strictly **Standard Library only** (no `requests`, `praw`, etc.).
- **Data**: `config.json` (config), `seen_posts.json` (deduplication).

## Core Rules
1. **Zero Dependencies**: Use `urllib` and `json`. Do not add external packages.
2. **Logic Integrity**: Any change to scoring/filtering in `reddit_scout.py` MUST be verified via `tests/test_scoring.py`.
3. **Config Safety**: Do not break the `config.json` structure; it is shared with `setup.html`.
4. **Secrets Management**: NEVER read `.env.local` or any file containing credentials. NEVER ask the user to paste a key into the chat. Instruct the user to edit `.env.local` manually in their editor.

## Entry Points
- `reddit_scout.py`: Main logic & scoring.
- `scripts/reddit_api.py`: Reddit API wrapper.

## config.json
`keyword_searches`: pain-point phrases sent to Reddit search. `subreddits`: `[name, limit]` pairs scanned via /new. `relevance_keywords`: `[keyword, weight]` pairs — weights 3/2/1 (strong/medium/weak). `skip_patterns`: regex strings, matched case-insensitive.

**The repo ships with demo data (freelance invoicing niche). Replace `keyword_searches`, `subreddits`, and `relevance_keywords` before first run.**

## First-time setup
Read `SETUP.md` and follow the steps there.
