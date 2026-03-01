# needle

> Find the needle in the haystack. Daily Reddit scanner that surfaces buying signals before people know they need you.

Runs locally via cron — no cloud, no IP blocks.
Results land in your inbox every morning as an email report with a clean, branded UI.

---

## Requirements

- Linux or macOS machine that's on during the day
- Python 3.8+
- **Zero external dependencies:** Uses only the Python Standard Library (no `pip install` required).
- Brevo account (free, 300 emails/day)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Repleno/needle.git
cd needle
```

### 2. Set up Brevo

1. Create an account at [brevo.com](https://brevo.com) (free)
2. Verify a sender email: **Settings → Senders & IPs → Add a sender**
3. Get your API key: **Settings → API Keys → Generate a new API key**

### 3. Configure credentials

```bash
cp .env.example .env.local
chmod 600 .env.local
```

Edit `.env.local` with your values. Note: `run.sh` automatically loads and exports these variables to the script.

```bash
BREVO_API_KEY="xkeysib-..."   # Brevo API key
FROM_EMAIL="scout@yourdomain.com"  # verified sender address in Brevo
TO_EMAIL="you@yourdomain.com"      # where reports are sent
```

### 4. Customize keywords

The easiest way to configure needle is using the built-in **Visual Editor**:

1. Open `setup.html` in your browser.
2. Load your current `config.json`.
3. Adjust `keyword_searches`, `subreddits`, and `settings` for your business.
4. Download the updated `config.json`.

Alternatively, edit `config.json` manually - or ask your favorite LLM to help you. just point the the @AGENTS.md file. 

### 5. Set up cron

```bash
chmod +x run.sh
crontab -e
```

Add this line — `run.sh` sends once per day and retries on failure.  
**Tip:** Use `pwd` in your terminal to get the full path to the `needle` folder.

```
0 9,12,15 * * * /absolute/path/to/needle/run.sh
```

> Times are in your **system timezone** (check with `timedatectl`).
> Adjust hours so the runs land when you want them — e.g. 10:00, 13:00, 16:00 local time.

### 6. Test run

```bash
./run.sh
```

Check `run.log` for output. You should receive the first email within seconds.

---

## Scoring

Each post gets a score based on weighted keywords in the title, body, and subreddit:

- 🟢 **Score 15–20** — high relevance, reach out immediately
- 🟡 **Score 8–14** — worth checking if it's a fit
- ⚪ **Score 5–7** — weak signal
- Posts below 5 are not shown

### Filters & Penalties
- **Astroturfing protection (-5):** Posts that look like ads (specific product name + 3+ features + positive conclusion) are automatically penalized.
- **Young account penalty (-2):** Posts from accounts under 30 days old are penalized.
- **Skip patterns:** Posts matching phrases like `[hiring]` or `for sale` are ignored.
- **Deduplication:** Sent posts won't appear again for 7 days (TTL) using a timestamped tracking system.

---

## Reply strategy

You are **not** the salesperson — you are the expert.

**Bad:** "Hey, check out my tool!"

**Good:** Answer the problem honestly. Explain how others solve it. If your tool fits, mention it briefly at the end.

---

## Customizing

### Change the schedule

Edit your crontab (`crontab -e`) and adjust the hours to your local timezone.
`0 9,12,15 * * *` = three daily attempts, sends once on first success. [Cron syntax explained](https://crontab.guru).

### Custom scoring keywords

You can override the default scoring keywords and filters in `config.json`:
```json
"settings": {
  "relevance_keywords": [
    ["your keyword", 3],
    ["another keyword", 2]
  ],
  "skip_patterns": [
    "\\[hiring\\]",
    "for sale"
  ]
}
```

---

## Project structure

```
reddit_scout.py          ← Main script (scoring, astroturfing detection)
config.json              ← Keywords, subreddits, settings, email addresses
setup.html               ← Visual config editor (open locally in browser)
logo.svg                 ← Project logo (included in email reports)
seen_posts.json          ← Deduplication tracking (timestamp-based TTL)
run.sh                   ← Cron wrapper: runs once per day, retries on failure
.env.example             ← Credentials template (copy to .env.local)
test_scoring.py          ← Scoring logic unit tests
scripts/
  reddit_api.py          ← Reddit Public API (standard urllib, no dependencies)
```

---

## FAQ

**Do I need a Reddit account?**
No. The script uses Reddit's public JSON API without authentication.

**Does it cost anything?**
The script itself is free. Brevo: free up to 300 emails/day.

**Why local instead of GitHub Actions?**
Reddit blocks GitHub Actions IP ranges with HTTP 403. Running locally avoids this.

**What if nothing is found on a given day?**
You still get a "Quiet day" email — so you know the scout ran. Tune your keywords, add different subs, or check your threshold.

---

*Built with love by a german founder  [needle](https://github.com/Repleno/needle)*
