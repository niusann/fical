from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, List

from .utils import IpoItem, EarningsItem, utc_now


def ical_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def fold_line(line: str, limit: int = 75) -> List[str]:
    if len(line) <= limit:
        return [line]
    folded: List[str] = [line[:limit]]
    rest = line[limit:]
    while rest:
        folded.append(" " + rest[:limit - 1])
        rest = rest[limit - 1:]
    return folded


def format_all_day(d: date) -> str:
    return d.strftime("%Y%m%d")


def build_vevent(item: IpoItem, now: datetime, summary_prefix: str = "") -> List[str]:
    if item.expected_date is None:
        return []
    dtstamp = now.strftime("%Y%m%dT%H%M%SZ")
    dtstart = format_all_day(item.expected_date)
    dtend = format_all_day(item.expected_date + timedelta(days=1))

    description_parts: List[str] = []
    if item.status:
        description_parts.append(f"Status: {item.status}")
    if item.price_range:
        description_parts.append(f"Price Range: {item.price_range}")
    if item.deal_size:
        description_parts.append(f"Deal Size: {item.deal_size}")
    if item.exchange:
        description_parts.append(f"Exchange: {item.exchange}")
    description = ical_escape("\n".join(description_parts)) if description_parts else ""

    lines: List[str] = [
        "BEGIN:VEVENT",
        f"UID:{item.uid()}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"DTEND;VALUE=DATE:{dtend}",
        f"SUMMARY:{ical_escape(summary_prefix + item.summary())}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{description}")
    if item.link_url:
        lines.append(f"URL:{ical_escape(item.link_url)}")
    lines.append("CATEGORIES:IPO")
    lines.append("END:VEVENT")

    folded: List[str] = []
    for line in lines:
        folded.extend(fold_line(line))
    return folded


def build_calendar(items: Iterable[IpoItem]) -> str:
    now = utc_now()
    lines: List[str] = [
        "BEGIN:VCALENDAR",
        "PRODID:-//fical//nasdaq-ipo//EN",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "NAME:Nasdaq IPOs",
        "X-WR-CALNAME:Nasdaq IPOs",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]

    for item in items:
        event_lines = build_vevent(item, now)
        if event_lines:
            lines.extend(event_lines)

    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"


def build_earnings_vevent(
    item: EarningsItem,
    now: datetime,
    summary_prefix: str = "",
    use_bare_uid: bool = False,
) -> List[str]:
    if item.report_date is None:
        return []
    dtstamp = now.strftime("%Y%m%dT%H%M%SZ")
    dtstart = item.report_date.strftime("%Y%m%d")
    dtend = (item.report_date + timedelta(days=1)).strftime("%Y%m%d")

    description_parts: List[str] = []
    if item.time_of_day:
        description_parts.append(f"Time: {item.time_of_day}")
    if item.eps_consensus:
        description_parts.append(f"EPS Consensus: {item.eps_consensus}")
    if item.eps_actual:
        description_parts.append(f"EPS Actual: {item.eps_actual}")
    description = ical_escape("\n".join(description_parts)) if description_parts else ""

    uid_value = item.uid_without_category_prefix() if use_bare_uid else item.uid()

    lines: List[str] = [
        "BEGIN:VEVENT",
        f"UID:{uid_value}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"DTEND;VALUE=DATE:{dtend}",
        f"SUMMARY:{ical_escape(summary_prefix + item.summary())}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{description}")
    if item.link_url:
        lines.append(f"URL:{ical_escape(item.link_url)}")
    lines.append("CATEGORIES:EARNINGS")
    lines.append("END:VEVENT")

    folded: List[str] = []
    for line in lines:
        folded.extend(fold_line(line))
    return folded


def build_earnings_calendar(items: Iterable[EarningsItem]) -> str:
    now = utc_now()
    lines: List[str] = [
        "BEGIN:VCALENDAR",
        "PRODID:-//fical//nasdaq-earnings//EN",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "NAME:Nasdaq Earnings",
        "X-WR-CALNAME:Nasdaq Earnings",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]

    for item in items:
        event_lines = build_earnings_vevent(item, now, use_bare_uid=True)
        if event_lines:
            lines.extend(event_lines)

    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"


def build_combined_calendar(
    ipo_items: Iterable[IpoItem],
    earnings_items: Iterable[EarningsItem],
) -> str:
    """Build a single VCALENDAR containing both IPO and Earnings events.

    Prefixes event summaries with markers so they are distinguishable when
    subscribing to the combined feed.
    """
    now = utc_now()
    lines: List[str] = [
        "BEGIN:VCALENDAR",
        "PRODID:-//fical//nasdaq-all//EN",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "NAME:Nasdaq IPOs & Earnings",
        "X-WR-CALNAME:Nasdaq IPOs & Earnings",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]

    for item in ipo_items:
        event_lines = build_vevent(item, now, summary_prefix="[IPO] ")
        if event_lines:
            lines.extend(event_lines)

    for item in earnings_items:
        event_lines = build_earnings_vevent(item, now, summary_prefix="[EARNINGS] ")
        if event_lines:
            lines.extend(event_lines)

    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"
