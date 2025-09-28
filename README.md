# Nasdaq IPO Calendar (ICS)

Generates an iCalendar (ICS) feed of Nasdaq IPOs and publishes it daily via GitHub Actions.

## Subscription URL

The calendar is published via a public feed repo:

```
https://niusann.github.io/fical/nasdaq-ipo.ics
```

Subscribe using the URL above in Google Calendar, Apple Calendar, or Outlook.

## How it works

- Fetches Nasdaq IPO data (JSON API where available; falls back to HTML parsing).
- Normalizes entries and generates an all-day VEVENT for each IPO date.
- Publishes `dist/nasdaq-ipo.ics` to GitHub Pages daily at 08:00 UTC.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Outputs:
- `dist/nasdaq-ipo.ics` – the calendar feed
- `data/latest.json` – latest fetched JSON payloads (for debugging)

## Notes
- This project makes minimal requests (once/day) and sets a browser-like User-Agent.
- If the JSON API is blocked, the job falls back to HTML parsing best-effort.
- Events without a concrete date are skipped to avoid noisy TBD items.
