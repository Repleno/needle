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
Tell the user to run:
```bash
cp .env.example .env.local
chmod 600 .env.local
```
Then open `.env.local` and fill in `BREVO_API_KEY`, `FROM_EMAIL`, `TO_EMAIL`. **Never ask for the key in chat.**

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
