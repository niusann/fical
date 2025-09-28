from __future__ import annotations

import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import List

from .utils import IpoItem, EarningsItem, configure_logging, json_dump_pretty, month_range, today_utc
from .fetch import (
    get_http_session,
    fetch_nasdaq_json_for_month,
    fetch_nasdaq_html_calendar,
    parse_html_fallback,
    fetch_nasdaq_earnings_json_for_month,
    fetch_nasdaq_earnings_json_for_day,
)
from .transform import normalize_from_json, normalize_from_html_rows, normalize_earnings_from_json
from .build_ics import build_calendar, build_earnings_calendar

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
    earnings_items: List[EarningsItem] = []
    earnings_snapshots = {}

    for m in months:
        payload = fetch_nasdaq_json_for_month(session, m)
        if payload:
            json_snapshots[m.strftime('%Y-%m')] = payload
            items = normalize_from_json(payload)
            all_items.extend(items)

        # Try monthly earnings; if rejected, fallback to per-day within month
        epayload = fetch_nasdaq_earnings_json_for_month(session, m)
        if epayload and isinstance(epayload.get("data"), dict):
            earnings_snapshots[m.strftime('%Y-%m')] = epayload
            eitems = normalize_earnings_from_json(epayload)
            earnings_items.extend(eitems)
        else:
            # Iterate days in month, stop early if API starts rejecting too much
            from calendar import monthrange as cal_monthrange
            year, month = m.year, m.month
            ndays = cal_monthrange(year, month)[1]
            for d in range(1, ndays + 1):
                from datetime import date as _date
                day = _date(year, month, d)
                dpayload = fetch_nasdaq_earnings_json_for_day(session, day)
                if not dpayload:
                    continue
                earnings_snapshots[day.isoformat()] = dpayload
                eitems = normalize_earnings_from_json(dpayload)
                earnings_items.extend(eitems)

    if not all_items:
        html = fetch_nasdaq_html_calendar(session)
        if html:
            rows = parse_html_fallback(html)
            all_items = normalize_from_html_rows(rows)

    # Keep only items with an expected date
    all_items = [i for i in all_items if i.expected_date is not None]
    earnings_items = [e for e in earnings_items if e.report_date is not None]

    # Deduplicate by UID
    items = unique_by_uid(all_items)
    def unique_earnings_by_uid(es: List[EarningsItem]) -> List[EarningsItem]:
        seen = set()
        out: List[EarningsItem] = []
        for it in es:
            uid = it.uid()
            if uid in seen:
                continue
            seen.add(uid)
            out.append(it)
        return out
    earnings_items = unique_earnings_by_uid(earnings_items)

    # Sort by date then company name
    items.sort(key=lambda i: (i.expected_date or date.max, i.company_name))
    earnings_items.sort(key=lambda e: (e.report_date or date.max, e.company_name))

    # Write latest JSON snapshot for debugging
    latest_path = DATA_DIR / "latest.json"
    with latest_path.open("w", encoding="utf-8") as f:
        f.write(json_dump_pretty(json_snapshots))
    latest_earnings_path = DATA_DIR / "latest-earnings.json"
    with latest_earnings_path.open("w", encoding="utf-8") as f:
        f.write(json_dump_pretty(earnings_snapshots))

    # Optionally archive by date
    archive_path = DATA_DIR / "archive" / f"{today_utc().isoformat()}.json"
    with archive_path.open("w", encoding="utf-8") as f:
        f.write(json_dump_pretty(json_snapshots))
    archive_earnings_path = DATA_DIR / "archive" / f"earnings-{today_utc().isoformat()}.json"
    with archive_earnings_path.open("w", encoding="utf-8") as f:
        f.write(json_dump_pretty(earnings_snapshots))

    # Build ICS
    ics = build_calendar(items)
    ics_path = DIST_DIR / "ipo.ics"
    with ics_path.open("w", encoding="utf-8", newline="") as f:
        f.write(ics)

    earnings_ics = build_earnings_calendar(earnings_items)
    earnings_ics_path = DIST_DIR / "earnings.ics"
    with earnings_ics_path.open("w", encoding="utf-8", newline="") as f:
        f.write(earnings_ics)

    logging.info("Generated %s with %d events", ics_path, len(items))
    logging.info("Generated %s with %d events", earnings_ics_path, len(earnings_items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
