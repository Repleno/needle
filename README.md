# needle

**⚠️ Linux & macOS only.** (No Windows support)

![needle](foundtheneedle.png)

> Find the needle in the haystack. Daily Reddit scanner that surfaces buying signals before people know they need you.

Runs locally via cron — no cloud, no IP blocks.
Results are saved as a local HTML report (default) or sent to your inbox via Brevo.

---

## The backstory

I'm a founder. I know the drill: you need to find customers, but you don't want to spend €50/month on a "social listening" tool that just shows you a bunch of noise. I wanted something simple, local, and free that just works on my own machine. So I built needle for Linux and Mac.

It's not a SaaS. It's a script that runs on your machine. No monthly subscriptions, no data selling, just the buying signals you actually care about.

## The idea

Reddit is full of people who are describing your problem right now. Not in a product forum. Not on your landing page. In a real conversation with other founders, freelancers, or professionals — before they even know a solution exists.

needle finds these posts automatically every morning and alerts you locally (desktop notification + HTML report) or via email.

Your job: show up, answer as an expert, not as a salesperson.

## Why this works

Search Reddit for `"track client hours spreadsheet"` or `"forgot to log hours"`. You'll find real posts from real people with real pain. No marketing fluff, no polite euphemisms.

These people weren't looking for a solution — they were sharing their problem. That's your entry point. A genuine, helpful reply from someone who knows the topic is the opposite of cold outreach.

---

## Quickstart

```bash
git clone https://github.com/Repleno/needle.git && cd needle
```

Or let your AI assistant handle the setup — just point it at `SETUP.md`.

---

## Requirements

- Linux or macOS machine that's on during the day
- Python 3.8+
- **Zero external dependencies:** Uses only the Python Standard Library (no `pip install` required).
- **Optional:** Brevo account (free, 300 emails/day) — if you want email delivery.

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Repleno/needle.git
cd needle
```

### 2. Optional: Set up Brevo (for email delivery)

If you just want a local HTML report and desktop notifications, **skip to Step 4**.

1. Create an account at [brevo.com](https://brevo.com) (free)
2. Verify a sender email: **Settings → Senders & IPs → Add a sender**
3. Get your API key: **Settings → API Keys → Generate a new API key**

### 3. Optional: Configure credentials (for email delivery)

```bash
cp .env.example .env.local
chmod 600 .env.local
```

Edit `.env.local` with your values. `run.sh` automatically loads and exports these to the script.

```bash
BREVO_API_KEY="xkeysib-..."        # Brevo API key
FROM_EMAIL="scout@yourdomain.com"  # verified sender address in Brevo
TO_EMAIL="you@yourdomain.com"      # where reports are sent
```

Finally, set `"output_mode": "email"` in your `config.json`.

### 4. Customize keywords — **this is the most important step**

> **The `config.json` in this repo contains demo data** for a freelance invoicing tool.
> Before your first run, replace the keywords and subreddits with ones that match your product.
> Without this step, the reports will be relevant to someone else's business.

**Core principle: search for pain words, not solution words.**

| ❌ Solution word | ✅ Pain word |
|-----------------|-------------|
| time tracking software | forgot to log hours |
| invoicing tool | freelance invoicing chaos |
| billing app | manual time tracking |
| inventory tool | out of stock again |

The easiest way is the built-in **Visual Editor**:

1. Open `setup.html` in your browser.
2. Click **Import config.json** and load your file.
3. Replace `keyword_searches` and `subreddits` for your niche.
4. Click **Save config.json** and overwrite the file.

Alternatively, edit `config.json` directly — or point your LLM at `AGENTS.md` and ask it to suggest keywords for your product.

**How to find good keywords:**
- Read 10 posts in relevant subreddits — which phrases keep coming up?
- Ask your existing customers: "How did you describe this problem before you used us?"
- Use everyday language, not jargon.

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

### 6. Test run

```bash
./run.sh
```

Check `run.log` for output. A desktop notification will appear, and `report.html` will be created in your needle folder. By default, it will also auto-open in your browser.

---

## Reading the report

By default, needle saves an HTML report in the project root (`report.html`) and sends a desktop notification. If you've configured email mode, you'll receive the report in your inbox.

Each post gets a score based on weighted keywords in title, body, and subreddit. **The best part: You define the scoring logic yourself.** By adjusting keywords and weights in your config, you train the engine to find exactly what you're looking for.

- 🟢 **Score 15–20** — strong signal, reach out immediately
- 🟡 **Score 8–14** — worth checking if it's a fit
- ⚪ **Score 5–7** — weak signal
- Posts below 5 are not shown

**Automatic filters:**
- **Astroturfing (-5):** Posts that look like ads (product name + 3+ features + positive conclusion) are penalized.
- **Young account (-2):** Accounts under 30 days old are penalized.
- **Skip patterns:** Posts matching `[hiring]`, `for sale`, etc. are ignored.
- **Deduplication:** Same post won't appear again for 7 days.

On quiet days you still get a "Quiet day" report — so you know the scout ran.

---

## How to reply

**Goal: build trust, don't sell.**

1. Show you understand the problem (1 sentence).
2. Give a genuine, useful answer — even if your tool isn't the solution.
3. If it fits: mention it briefly at the end, without pressure.

**Example:**

> Post: "We still manage our client hours with Excel and it's getting messy. Anyone have a better solution?"

**Bad:** "Check out MyTool, it solves exactly that!"

**Good:** "I know this well — Excel breaks down at a certain scale because you forget to log hours manually. What usually helps as a first step: set up a dedicated reminder at the end of each day. Otherwise, the chaos moves into any tool you use. If you do want a tool: we're building something exactly for this — happy to show you what we have."

**Common mistakes:**
- **Selling too early.** If your first sentence contains a link, it looks like spam.
- **Generic replies.** "Great question! Have you considered time tracking?" — this smells like a bot.
- **Keyword inflation.** 10 precise keywords beat 50 broad ones.
- **Skipping the education.** Educate first, sell later. Reddit users are allergic to sales pitches — if you lead with value, they'll ask about your product themselves.
- **Using AI to write your replies.** People on Reddit can smell it instantly. Write in your own voice. Imperfect and human beats polished and robotic every time.

---

## Customizing

### Change the schedule

Edit your crontab (`crontab -e`) and adjust the hours to your local timezone.
`0 9,12,15 * * *` = three daily attempts, sends once on first success. [Cron syntax explained](https://crontab.guru).

### Custom scoring & keywords

**You are the engine.** You can fully customize which keywords add points and which ones subtract them. Override the default scoring weights and skip patterns in `config.json`:

```json
"settings": {
  "relevance_keywords": [
    ["your keyword", 5],    // adds 5 points if found
    ["competitor", -10],    // subtracts 10 points
    ["another one", 2]
  ],
  "skip_patterns": [
    "\\[hiring\\]",
    "for sale"
  ]
}
```

Once you recognize a pattern — certain subreddits or phrases that consistently deliver — update your `config.json` via the visual editor. The scout improves with every iteration as you fine-tune the ratings.

---

## Project structure

```
reddit_scout.py          ← Main script (scoring, astroturfing detection)
config.json              ← Keywords, subreddits, settings, email addresses
setup.html               ← Visual config editor (open locally in browser)
logo.svg                 ← Project logo (included in email reports)
run.sh                   ← Cron wrapper: runs once per day, retries on failure
.env.example             ← Credentials template (copy to .env.local)
tests/                   ← Unit tests (scoring, filtering, HTML, config)
scripts/
  reddit_api.py          ← Reddit Public API (stdlib only, no dependencies)
```

---

## FAQ

**Do I need a Reddit account?**
No. The script uses Reddit's public JSON API without authentication.

**Is this legal? Can Reddit come after me?**
Grey area, but the risk is very low at needle's scale. Reddit's Developer Terms technically require OAuth authentication, but the public `.json` endpoints (appending `.json` to any Reddit URL) have existed as an unofficial API for years and are widely used.

What can realistically happen:
- **IP throttling or block** — the most likely scenario if you hammer their servers. Needle makes a handful of requests per day, so this is unlikely.
- **Nothing** — at needle's volume (a few subreddits, once a day) you fly well under the radar.
- **Legal action** — extremely unlikely. Reddit pursues commercial scrapers and data resellers, not a local cron job finding 5 posts a day.

To stay in the clear: keep your cron to 1–3 runs per day, don't remove the `time.sleep()` calls between requests, and don't run needle from cloud IP ranges (GitHub Actions, AWS, etc.) — those get blocked anyway.

**Does it cost anything?**
The script itself is free. Local mode (HTML + Notifications) costs nothing.
**Brevo (optional):** Free up to 300 emails/day.

**Why local instead of GitHub Actions?**
Reddit blocks GitHub Actions IP ranges with HTTP 403. Running locally avoids this.

**What if nothing is found on a given day?**
You still get a "Quiet day" notification/report — so you know the scout ran. Tune your keywords, add different subs, or lower your threshold.

---

*Built with ❤️ by a german founder who refused to pay €50/month for social listening tools. · [needle](https://github.com/Repleno/needle)*
