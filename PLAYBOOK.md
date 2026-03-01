# needle Outreach Playbook
### How to find the right conversations every day — without spamming

---

## The idea

Reddit is full of people who are describing your problem right now. Not in a product forum. Not on your landing page. In a real conversation with other founders, freelancers, or professionals — before they even know a solution exists.

The **needle** scout finds these posts automatically every morning and sends them to you by email.

Your job: show up, answer as an expert, not as a salesperson.

---

## Why this works

Search Reddit for `"track client hours spreadsheet"` or `"forgot to log hours"`. You'll find real posts from real people with real pain. No marketing fluff, no polite euphemisms.

These people weren't looking for a solution — they were sharing their problem. That's your entry point. A genuine, helpful reply from someone who knows the topic is the opposite of cold outreach.

---

## Setup (10 minutes)

**What you need:**
- Linux or macOS machine that's on during the day
- Python 3.8+
- Brevo account → [brevo.com](https://brevo.com) (free, 300 emails/day)

**Step by step:**

1. **Clone the repo** — `git clone https://github.com/Repleno/needle.git`
2. **Set up Brevo** — create an account, verify a sender email, and generate an API key.
3. **Add credentials** — copy `.env.example` to `.env.local` and fill in your values:
   - `BREVO_API_KEY` — your Brevo API key
   - `FROM_EMAIL` — your verified sender address
   - `TO_EMAIL` — where the report should go
4. **Customize keywords** — open `setup.html` in your browser, load `config.json`, edit keywords/subreddits, and download the update.
5. **Set up cron** — add to crontab: `0 9,12,15 * * * /path/to/needle/run.sh`
6. **Test** — run `./run.sh` once manually to confirm the email arrives.

From then on, a report lands in your inbox every morning.

---

## Customizing keywords

This is the most important step. The scout is only as good as its keywords.

**Core principle:** Search for pain words, not solution words.

| ❌ Solution word | ✅ Pain word |
|-----------------|-------------|
| time tracking software | forgot to log hours |
| invoicing tool | freelance invoicing chaos |
| billing app | manual time tracking |
| inventory tool | out of stock again |

**How to find good keywords:**
- Read 10 posts in relevant subreddits — which phrases keep coming up?
- Ask your existing customers: "How did you describe this problem before you used us?"
- Use everyday language, not jargon.

---

## Reading the email report

You get a daily email with up to 10 posts, sorted by relevance.

```
🟢 Score 15–20   Reach out immediately — strong signal
🟡 Score 8–14    Check if it's really a fit
⚪ Score 5–7     Weak/contextual signal
```

The score is based on keywords. Posts that look like paid promotion (astroturfing) or come from very new accounts are automatically penalized.

On quiet days, you get a "Quiet day" email — so you know the scout ran.

---

## How to reply

**Goal:** Build trust, don't sell.

**The pattern:**
1. Show you understand the problem (1 sentence).
2. Give a genuine, useful answer — even if your tool isn't the solution.
3. If it fits: mention it briefly at the end, without pressure.

**Example:**

> Post: "We still manage our client hours with Excel and it's getting messy. Anyone have a better solution?"

**Bad reply:**
> "Check out MyTool, it solves exactly that!"

**Good reply:**
> "I know this well — Excel breaks down at a certain scale because you forget to log hours manually. What usually helps as a first step: set up a dedicated reminder at the end of each day. Otherwise, the chaos moves into any tool you use. If you do want a tool: we're building something exactly for this — happy to show you what we have."

---

## Common mistakes

**Selling too early.** If your first sentence contains a link, it looks like spam.

**Generic replies.** "Great question! Have you considered time tracking?" — this smells like a bot.

**Keyword inflation.** If you add too many keywords, quality drops. 10 precise ones beat 50 broad ones.

---

## Evolving the setup

Once you recognize a pattern — certain subreddits or phrases that consistently deliver — update your `config.json` via the visual editor. The scout improves with every iteration.

---

*Built with Reddit Public API and Brevo. Runs locally via cron. 100% Free.*
