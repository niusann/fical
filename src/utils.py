from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import List, Optional


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
        symbol_or_slug = self.symbol or slugify(self.company_name)
        ymd = self.expected_date.strftime("%Y%m%d") if self.expected_date else "tbd"
        return f"ipo-{symbol_or_slug}-{ymd}@nasdaq-ipo"

    def summary(self) -> str:
        base = self.symbol if self.symbol else "IPO"
        return f"{base} – {self.company_name}"


@dataclass(frozen=True)
class EarningsItem:
    company_name: str
    symbol: Optional[str]
    report_date: Optional[date]
    time_of_day: Optional[str]
    eps_consensus: Optional[str]
    eps_actual: Optional[str]
    link_url: Optional[str]

    def uid(self) -> str:
        symbol_or_slug = self.symbol or slugify(self.company_name)
        ymd = self.report_date.strftime("%Y%m%d") if self.report_date else "tbd"
        return f"earnings-{symbol_or_slug}-{ymd}@nasdaq-earnings"

    def uid_without_category_prefix(self) -> str:
        """Return a stable UID without the leading 'earnings-' category prefix.

        This is used for the standalone earnings feed to keep identifiers concise,
        while the combined feed continues to use the category-prefixed UID to
        avoid any ambiguity across mixed event types.
        """
        symbol_or_slug = self.symbol or slugify(self.company_name)
        ymd = self.report_date.strftime("%Y%m%d") if self.report_date else "tbd"
        return f"{symbol_or_slug}-{ymd}@nasdaq-earnings"

    def summary(self) -> str:
        base = self.symbol if self.symbol else "Earnings"
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
