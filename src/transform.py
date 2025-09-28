from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional

from dateutil import parser as dateparser

from .utils import IpoItem, EarningsItem


def parse_date_safe(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        dt = dateparser.parse(value)
        if not dt:
            return None
        return dt.date()
    except Exception:
        return None


def normalize_from_json(month_payload: Dict[str, Any]) -> List[IpoItem]:
    """Normalize Nasdaq JSON month payload to IpoItem list.

    Handles current structure:
      data.upcoming.upcomingTable.rows[].expectedPriceDate
      data.priced.rows[].pricedDate
    Ignores "filed" and "withdrawn" for event generation.
    """
    items: List[IpoItem] = []
    if not isinstance(month_payload, dict):
        return items
    data = month_payload.get("data") or month_payload
    if not isinstance(data, dict):
        return items

    # Upcoming IPOs
    upcoming = data.get("upcoming")
    if isinstance(upcoming, dict):
        rows: Optional[List[Dict[str, Any]]] = None
        if isinstance(upcoming.get("upcomingTable"), dict):
            rows = upcoming["upcomingTable"].get("rows")  # type: ignore[index]
        if rows is None and isinstance(upcoming.get("rows"), list):
            rows = upcoming.get("rows")  # type: ignore[assignment]

        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                item = IpoItem(
                    company_name=str(row.get("companyName") or "Unknown Company"),
                    symbol=(str(row.get("proposedTickerSymbol")) if row.get("proposedTickerSymbol") else None),
                    status="UPCOMING",
                    expected_date=parse_date_safe(str(row.get("expectedPriceDate")) if row.get("expectedPriceDate") else None),
                    exchange=(str(row.get("proposedExchange")) if row.get("proposedExchange") else None),
                    price_range=(str(row.get("proposedSharePrice")) if row.get("proposedSharePrice") else None),
                    deal_size=(
                        str(row.get("dollarValueOfSharesOffered") or row.get("sharesOffered"))
                        if (row.get("dollarValueOfSharesOffered") or row.get("sharesOffered"))
                        else None
                    ),
                    link_url=None,
                )
                items.append(item)

    # Priced IPOs
    priced = data.get("priced")
    if isinstance(priced, dict) and isinstance(priced.get("rows"), list):
        for row in priced["rows"]:
            if not isinstance(row, dict):
                continue
            item = IpoItem(
                company_name=str(row.get("companyName") or "Unknown Company"),
                symbol=(str(row.get("proposedTickerSymbol")) if row.get("proposedTickerSymbol") else None),
                status="PRICED",
                expected_date=parse_date_safe(str(row.get("pricedDate")) if row.get("pricedDate") else None),
                exchange=(str(row.get("proposedExchange")) if row.get("proposedExchange") else None),
                price_range=(str(row.get("proposedSharePrice")) if row.get("proposedSharePrice") else None),
                deal_size=(
                    str(row.get("dollarValueOfSharesOffered") or row.get("sharesOffered"))
                    if (row.get("dollarValueOfSharesOffered") or row.get("sharesOffered"))
                    else None
                ),
                link_url=None,
            )
            items.append(item)

    return items


def normalize_from_html_rows(rows: List[Dict[str, Any]]) -> List[IpoItem]:
    items: List[IpoItem] = []
    for row in rows:
        company = row.get("company") or row.get("company name") or row.get("name")
        symbol = row.get("symbol") or row.get("ticker")
        status = row.get("status") or "UPCOMING"
        dt_str = row.get("date") or row.get("expected date")
        exchange = row.get("exchange")
        price_range = row.get("price range") or row.get("price")
        deal_size = row.get("deal size") or row.get("deal size ($mm)")
        url = None
        items.append(
            IpoItem(
                company_name=str(company or "Unknown Company"),
                symbol=str(symbol) if symbol else None,
                status=str(status or "UPCOMING").upper(),
                expected_date=parse_date_safe(str(dt_str) if dt_str else None),
                exchange=str(exchange) if exchange else None,
                price_range=str(price_range) if price_range else None,
                deal_size=str(deal_size) if deal_size else None,
                link_url=url,
            )
        )
    return items


def normalize_earnings_from_json(month_payload: Dict[str, Any]) -> List[EarningsItem]:
    """Normalize Nasdaq earnings JSON month payload to EarningsItem list.

    Current observed structures vary by date and API version. We try to be permissive.
    Common patterns:
      data.rows[] with fields like: symbol, companyname, date, time, epsconsensus, epsactual, url
      or deeply nested under data.calendar.rows[]
    """
    items: List[EarningsItem] = []
    if not isinstance(month_payload, dict):
        return items
    data = month_payload.get("data") or month_payload
    if not isinstance(data, dict):
        return items

    # Fallback date (for daily endpoints rows without explicit date)
    fallback_date: Optional[date] = None
    asof_value = data.get("asOf")
    if isinstance(asof_value, str):
        maybe_dt = parse_date_safe(asof_value)
        if maybe_dt:
            fallback_date = maybe_dt

    # Try a few likely structures
    candidate_lists: List[Optional[List[Dict[str, Any]]]] = []
    if isinstance(data.get("calendar"), dict) and isinstance(data["calendar"].get("rows"), list):
        candidate_lists.append(data["calendar"]["rows"])  # type: ignore[index]
    if isinstance(data.get("rows"), list):
        candidate_lists.append(data.get("rows"))  # type: ignore[arg-type]
    if isinstance(data.get("upcoming"), dict) and isinstance(data["upcoming"].get("rows"), list):
        candidate_lists.append(data["upcoming"]["rows"])  # type: ignore[index]

    rows: List[Dict[str, Any]] = []
    for lst in candidate_lists:
        if isinstance(lst, list):
            rows.extend([r for r in lst if isinstance(r, dict)])

    def get_str(d: Dict[str, Any], *keys: str) -> Optional[str]:
        for k in keys:
            v = d.get(k)
            if v is not None:
                s = str(v).strip()
                return s if s else None
        return None

    for row in rows:
        company = get_str(row, "companyname", "company", "name")
        symbol = get_str(row, "symbol", "ticker")
        dt_str = get_str(row, "date", "reportdate", "earningsdate")
        tod = get_str(row, "time", "timeofday", "timeOfDay")
        # Common naming variants
        eps_c = get_str(row, "epsconsensus", "eps_consensus", "epsConsensus", "epsForecast")
        eps_a = get_str(row, "epsactual", "eps_actual", "epsActual", "eps")
        url = get_str(row, "url", "link", "href")
        parsed_date = parse_date_safe(dt_str)
        if parsed_date is None:
            parsed_date = fallback_date

        time_clean = None
        if tod:
            t = tod.strip().lower()
            if t == "time-not-supplied":
                time_clean = "TBD"
            elif t in {"bmo", "amc"}:
                time_clean = t.upper()
            else:
                time_clean = tod

        items.append(EarningsItem(
            company_name=str(company or "Unknown Company"),
            symbol=str(symbol) if symbol else None,
            report_date=parsed_date,
            time_of_day=time_clean,
            eps_consensus=str(eps_c) if eps_c else None,
            eps_actual=str(eps_a) if eps_a else None,
            link_url=str(url) if url else None,
        ))

    return items
