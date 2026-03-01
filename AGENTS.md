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

## Setup & Deployment Workflow (Agent-Led)
If the user wants to set up needle, guide them through these steps:

1. **Credentials (User Action Required)**: 
   - Tell the user to `cp .env.example .env.local`.
   - Instruct the user to open `.env.local` and paste their `BREVO_API_KEY` manually.
   - **IMPORTANT:** Never ask the user to provide the key in the chat. Keep secrets local.
2. **Configuration**:
   - Read `config.json`. 
   - Ask the user for their business niche to suggest/update `keyword_searches` and `subreddits`.
3. **Execution Permissions**:
   - Ensure `run.sh` is executable (`chmod +x run.sh`).
4. **Automation (Cron)**:
   - Identify the absolute path to `run.sh` using `pwd`.
   - Provide the exact crontab line: `0 9,12,15 * * * /absolute/path/to/run.sh`.
   - Instruct the user to run `crontab -e` and paste the line.
5. **Validation**:
   - Ask the user to run `./run.sh` once to verify the setup.
   - Tail `run.log` to confirm success.
