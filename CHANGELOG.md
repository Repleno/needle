# Changelog

All notable changes to this project will be documented in this file.

## [0.1] - 2026-03-01

Initial release. Reddit daily scanner that runs locally via cron.

### Features

- **Daily Reddit scanning** via local cron (free, no cloud infrastructure)
- **Keyword-based scoring** with word-boundary matching (no false positives)
- **Astroturfing detection** — penalizes fake testimonials
- **Young account penalty** — accounts under 30 days get -2 score
- **HTML email reports** via Brevo API with color-coded scores
- **Deduplication** with configurable TTL (default 7 days)
- **Fully configurable** via `config.json`:
  - Keywords and subreddits
  - Score threshold, time window, max results
  - Custom relevance keywords and skip patterns
- **Visual config editor** (`setup.html`) — edit config without touching JSON

### Technical

- Zero external dependencies (Python stdlib only)
- 32 unit tests covering scoring, filtering, HTML generation, config validation
- Config validation with clear error messages
- Email retry with exponential backoff (3 attempts)
- Reddit's public JSON API (no authentication required)
- Local credentials via `.env.local`

### Documentation

- Setup guide with 5-step quickstart
- Reply strategy playbook
- FAQ section

---

## Future Ideas

- [ ] Slack/Discord webhook integration
- [ ] Multiple recipient support
- [ ] Sentiment analysis for better scoring
- [ ] Web dashboard for viewing history
