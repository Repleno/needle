# needle Setup (Agent-Led)

## Step 1 — Understand the product
Ask: "What's your product and what problem does it solve? Share your URL or describe it."

If a URL is provided, crawl it and extract:
1. Product description
2. Target audience
3. Pain points addressed
4. Relevant keywords

Use this to suggest 6–10 `keyword_searches` (pain language, not solution language) and 4–6 subreddits. Update `config.json` accordingly.

## Step 2 — Credentials
Local mode is the default — no credentials needed. Skip to Step 3.

If you want email delivery, set `output_mode`: "email" in `config.json`, then create `.env.local` with `BREVO_API_KEY`, `FROM_EMAIL`, `TO_EMAIL`.

**NEVER read `.env.local` or any credential file. Never ask the user to paste a key into the chat. Credentials are the user's responsibility — your job ends at telling them which file to edit.**

## Step 3 — Permissions
```bash
chmod +x run.sh
```

## Step 4 — Cron
Get the absolute path with `pwd`, then:
```bash
crontab -e
```
Add: `0 9,12,15 * * * /absolute/path/to/run.sh`

## Step 5 — Validate
```bash
./run.sh
```
Tail `run.log` to confirm success.

## Step 6 - delete prompt from AGENTS.me
remove instruction: ## First-time setup
