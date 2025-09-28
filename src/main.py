from __future__ import annotations

import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import List

from .utils import IpoItem, configure_logging, json_dump_pretty, month_range, today_utc
from .fetch import get_http_session, fetch_nasdaq_json_for_month, fetch_nasdaq_html_calendar, parse_html_fallback
from .transform import normalize_from_json, normalize_from_html_rows
from .build_ics import build_calendar

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DIST_DIR = Path(__file__).resolve().parent.parent / "dist"


def unique_by_uid(items: List[IpoItem]) -> List[IpoItem]:
    seen = set()
    out: List[IpoItem] = []
    for item in items:
        uid = item.uid()
        if uid in seen:
            continue
        seen.add(uid)
        out.append(item)
    return out


def main() -> int:
    configure_logging()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "archive").mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    session = get_http_session()

    # Fetch 3-month horizon (current + next 2 months)
    months = month_range(date(today_utc().year, today_utc().month, 1), 3)

    all_items: List[IpoItem] = []
    json_snapshots = {}

    for m in months:
        payload = fetch_nasdaq_json_for_month(session, m)
        if payload:
            json_snapshots[m.strftime('%Y-%m')] = payload
            items = normalize_from_json(payload)
            all_items.extend(items)

    if not all_items:
        html = fetch_nasdaq_html_calendar(session)
        if html:
            rows = parse_html_fallback(html)
            all_items = normalize_from_html_rows(rows)

    # Keep only items with an expected date
    all_items = [i for i in all_items if i.expected_date is not None]

    # Deduplicate by UID
    items = unique_by_uid(all_items)

    # Sort by date then company name
    items.sort(key=lambda i: (i.expected_date or date.max, i.company_name))

    # Write latest JSON snapshot for debugging
    latest_path = DATA_DIR / "latest.json"
    with latest_path.open("w", encoding="utf-8") as f:
        f.write(json_dump_pretty(json_snapshots))

    # Optionally archive by date
    archive_path = DATA_DIR / "archive" / f"{today_utc().isoformat()}.json"
    with archive_path.open("w", encoding="utf-8") as f:
        f.write(json_dump_pretty(json_snapshots))

    # Build ICS
    ics = build_calendar(items)
    ics_path = DIST_DIR / "ipo.ics"
    with ics_path.open("w", encoding="utf-8", newline="") as f:
        f.write(ics)

    logging.info("Generated %s with %d events", ics_path, len(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
