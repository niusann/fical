# Nasdaq IPO & Earnings Calendars (ICS)

Generates iCalendar (ICS) feeds of Nasdaq IPOs and Earnings and publishes them daily via GitHub Actions.

## Subscription URLs

Published via a public feed repo:

```
https://niusann.github.io/fical/ipo.ics
https://niusann.github.io/fical/earnings.ics
```

Subscribe to either or both in Google Calendar, Apple Calendar, or Outlook.

## How it works

- Fetches Nasdaq IPO data (JSON API where available; falls back to HTML parsing if needed).
- Fetches Nasdaq Earnings data (JSON API). If the monthly endpoint rejects date-only queries, falls back to daily endpoints.
- Normalizes entries and generates all-day VEVENTs for IPO expected/priced dates and Earnings report dates.
- Publishes `dist/*.ics` to GitHub Pages daily at 08:00 UTC.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Outputs:
- `dist/ipo.ics` – IPO calendar feed
- `dist/earnings.ics` – Earnings calendar feed
- `data/latest.json` – latest IPO JSON snapshots (debugging)
- `data/latest-earnings.json` – latest Earnings JSON snapshots (debugging)
- `data/archive/*.json` – dated snapshots (includes `earnings-YYYY-MM-DD.json`)

## Notes
- This project makes minimal requests (once/day) and sets a browser-like User-Agent.
- IPO: if the JSON API is blocked, the job falls back to best-effort HTML parsing.
- Earnings: monthly API can reject date-only queries; we fallback to per-day queries.
- Events without a concrete date are skipped to avoid noisy TBD items; Earnings `time` may appear as `BMO`, `AMC`, or `TBD` in the description.
