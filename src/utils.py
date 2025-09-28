from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, List, Optional


ISO_DATE_FMT = "%Y-%m-%d"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def today_utc() -> date:
    return utc_now().date()


@dataclass(frozen=True)
class IpoItem:
    company_name: str
    symbol: Optional[str]
    status: str
    expected_date: Optional[date]
    exchange: Optional[str]
    price_range: Optional[str]
    deal_size: Optional[str]
    link_url: Optional[str]

    def uid(self) -> str:
        symbol_or_slug = (self.symbol or slugify(self.company_name))
        ymd = self.expected_date.strftime("%Y%m%d") if self.expected_date else "tbd"
        return f"ipo-{symbol_or_slug}-{ymd}@nasdaq-ipo"

    def summary(self) -> str:
        base = f"{self.symbol} IPO" if self.symbol else "IPO"
        return f"{base} – {self.company_name}"


def slugify(value: str) -> str:
    allowed = [c.lower() if c.isalnum() else "-" for c in value]
    slug = "".join(allowed)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def json_dump_pretty(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def month_range(start: date, months: int) -> List[date]:
    out: List[date] = []
    y, m = start.year, start.month
    for _ in range(months):
        out.append(date(y, m, 1))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out
