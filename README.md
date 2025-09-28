# Nasdaq IPO & Earnings Calendars (ICS)

Generates iCalendar (ICS) feeds of Nasdaq IPOs and Earnings and publishes them daily via GitHub Actions.

## Subscription URLs

Published via a public feed repo:

### IPO-only feed
```
https://niusann.github.io/fical/ipo.ics      
```
### Earnings-only feed
```
https://niusann.github.io/fical/earnings.ics  
```
### Combined feed
```
https://niusann.github.io/fical/all.ics       
```

Subscribe to either or both in Google Calendar, Apple Calendar, or Outlook.

## How to Use

Choose one or more of the subscription URLs above and add them to your calendar app as an internet/ICS subscription (not as a one-time file import):

- Google Calendar (Web)
  1. Open Google Calendar in a browser.
  2. In the left sidebar, next to "Other calendars", click the "+" button ➜ "From URL".
  3. Paste the desired `.ics` URL (e.g., `https://niusann.github.io/fical/all.ics`) and click "Add calendar".
  4. Google refresh cadence is controlled by Google and may take several hours; changes can take up to 24 hours to appear.

- Apple Calendar (macOS)
  1. Open Calendar ➜ File ➜ New Calendar Subscription…
  2. Paste the `.ics` URL and click Subscribe.
  3. Set Auto-refresh to "Every day" (or more frequently if you prefer) and click OK.

- iOS (iPhone/iPad)
  1. Settings ➜ Calendar ➜ Accounts ➜ Add Account ➜ Other ➜ Add Subscribed Calendar.
  2. Paste the `.ics` URL into Server, tap Next, then Save.

- Outlook on the Web
  1. Calendar ➜ Add calendar ➜ Subscribe from web.
  2. Paste the `.ics` URL, give it a name, pick a color, then click Import.

- Outlook Desktop (Windows/macOS)
  1. Home ➜ Add Calendar ➜ From Internet…
  2. Paste the `.ics` URL and confirm.

Notes:
- Events are all-day entries. Earnings may include `BMO`, `AMC`, or `TBD` in the description.
- Feeds are regenerated daily at 08:00 UTC. Your calendar app controls how often it checks for updates.
- If entries look stale, try removing and re-adding the subscription or lowering the refresh interval (where supported).

## Feedback & Issues

There is no private issue tracker. Please use public GitHub Issues: [niusann/fical Issues](https://github.com/niusann/fical/issues)

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
- `dist/all.ics` – Combined feed (IPO + Earnings). Event titles are prefixed with `[IPO]` or `[ERN]`.
- `data/ipo.json` – latest IPO JSON snapshots (debugging)
- `data/earnings.json` – latest Earnings JSON snapshots (debugging)
- `data/archive/ipo/YYYY-MM-DD.json` – IPO snapshots by date
- `data/archive/earnings/YYYY-MM-DD.json` – Earnings snapshots by date

## Notes
- This project makes minimal requests (once/day) and sets a browser-like User-Agent.
- IPO: if the JSON API is blocked, the job falls back to best-effort HTML parsing.
- Earnings: monthly API can reject date-only queries; we fallback to per-day queries.
- Events without a concrete date are skipped to avoid noisy TBD items; Earnings `time` may appear as `BMO`, `AMC`, or `TBD` in the description.
