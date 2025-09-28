from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/market-activity/ipos",
}


def get_http_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    session.timeout = 20
    return session


def fetch_nasdaq_json_for_month(session: requests.Session, month_start: date) -> Optional[Dict[str, Any]]:
    # Nasdaq often requires a v13 JSON endpoint; keep this flexible.
    # Example historical endpoint (may change):
    # https://api.nasdaq.com/api/ipo/calendar?date=2025-09
    ym = f"{month_start.year:04d}-{month_start.month:02d}"
    url = f"https://api.nasdaq.com/api/ipo/calendar?date={ym}"
    try:
        r = session.get(url)
        if r.status_code != 200:
            logging.warning("JSON fetch non-200: %s", r.status_code)
            return None
        data = r.json()
        # Expecting structure with 'data' field; be forgiving
        if not isinstance(data, dict):
            return None
        return data
    except Exception as exc:
        logging.warning("JSON fetch failed for %s: %s", month_start, exc)
        return None


def fetch_nasdaq_html_calendar(session: requests.Session) -> Optional[str]:
    try:
        url = "https://www.nasdaq.com/market-activity/ipos"
        r = session.get(url, headers={"Accept": "text/html,application/xhtml+xml"})
        if r.status_code != 200:
            logging.warning("HTML fetch non-200: %s", r.status_code)
            return None
        return r.text
    except Exception as exc:
        logging.warning("HTML fetch failed: %s", exc)
        return None


def parse_html_fallback(html: str) -> List[Dict[str, Any]]:
    # Minimal best-effort parser; selectors may need updates over time.
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    table = soup.find("table")
    if not table:
        return rows
    headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) != len(headers):
            continue
        row = {headers[i]: cells[i] for i in range(len(headers))}
        rows.append(row)
    return rows
