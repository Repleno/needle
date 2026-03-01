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
4. **Secrets Management**: NEVER ask for, log, or handle the `BREVO_API_KEY`. Instruct the user to edit `.env.local` manually.

## Entry Points
- `reddit_scout.py`: Main logic & scoring.
- `scripts/reddit_api.py`: Reddit API wrapper.

## config.json
`keyword_searches`: pain-point phrases sent to Reddit search. `subreddits`: `[name, limit]` pairs scanned via /new. `relevance_keywords`: `[keyword, weight]` pairs — weights 3/2/1 (strong/medium/weak). `skip_patterns`: regex strings, matched case-insensitive.

**The repo ships with demo data (freelance invoicing niche). Replace `keyword_searches`, `subreddits`, and `relevance_keywords` before first run.**

## Setup & Deployment Workflow (Agent-Led)
1. **Credentials**: `cp .env.example .env.local` → user fills in `BREVO_API_KEY`, `FROM_EMAIL`, `TO_EMAIL`. Never ask for the key in chat.
2. **Config**: Ask "What's your product and what problem does it solve?" → suggest 6–10 `keyword_searches` (pain language, not solution language) and 4–6 subreddits → update `config.json`.
3. **Permissions**: `chmod +x run.sh`
4. **Cron**: `0 9,12,15 * * * /absolute/path/to/run.sh` → `crontab -e`
5. **Validate**: `./run.sh` → check `run.log`
