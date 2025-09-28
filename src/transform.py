from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional

from dateutil import parser as dateparser

from .utils import IpoItem


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
