"""Next Grand Prix schedule from FastF1 relative to TimeAPI «now».

Authoritative instant comes from ``fetch_timeapi_now`` in
``src/integrations/timeapi_client.py`` (TIME-01).

Uses :func:`fastf1.get_event_schedule` with ``include_testing=False`` only.

**Ergast / pre-2018:** For seasons before 2018 the backend is often Ergast-backed; FastF1 may
assume conventional weekend layouts so **non-race** session UTC times can be approximate—**race**
time is the most reliable anchor. From 2018 onward the default backend exposes
``Session1DateUtc``…``Session5DateUtc`` as naive UTC per FastF1 docs. Treat
``schedule_data_quality="ergast_limited"`` accordingly for ``year < 2018``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

import fastf1
import pandas as pd
from pydantic import BaseModel, Field

from src.integrations.timeapi_client import fetch_timeapi_now

ScheduleDataQuality = Literal["full_2018_plus", "ergast_limited"]


class ScheduleResolutionError(Exception):
    """No upcoming non-testing GP could be resolved (empty data or calendar exhausted)."""


class NextGrandPrixSchedule(BaseModel):
    """Structured next-event payload for tools and callers."""

    event_name: str
    official_name: str | None
    country: str | None
    location: str | None
    event_date: date | datetime | None = Field(
        default=None,
        description="EventDate from FastF1 when present.",
    )
    sessions_utc: dict[str, datetime]
    schedule_data_quality: ScheduleDataQuality
    season_year: int = Field(..., description="Calendar year whose schedule supplied this event.")


def _as_date_or_dt(val: object) -> date | datetime | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, pd.Timestamp):
        return val.date() if val.hour == 0 and val.minute == 0 and val.second == 0 else val.to_pydatetime().replace(tzinfo=None)
    if isinstance(val, datetime):
        return val.replace(tzinfo=None) if val.tzinfo else val
    if isinstance(val, date):
        return val
    return None


def _session_label(row: pd.Series, n: int) -> str:
    col = f"Session{n}"
    if col in row.index and not pd.isna(row[col]):
        return str(row[col])
    return f"Session{n}"


def _quality_for_year(year: int) -> ScheduleDataQuality:
    return "ergast_limited" if year < 2018 else "full_2018_plus"


def _round_ok(row: pd.Series) -> bool:
    if "RoundNumber" not in row.index:
        return False
    rn = row["RoundNumber"]
    if pd.isna(rn):
        return False
    try:
        return int(float(rn)) > 0
    except (TypeError, ValueError):
        return False


def _is_testing_row(row: pd.Series) -> bool:
    if "EventFormat" not in row.index:
        return False
    fmt = row["EventFormat"]
    if pd.isna(fmt):
        return False
    return str(fmt).strip().lower() == "testing"


def _ordered_frame(df: pd.DataFrame) -> pd.DataFrame:
    if "EventDate" in df.columns:
        return df.sort_values("EventDate", kind="mergesort")
    return df


def _pick_from_year(df: pd.DataFrame, now_ts: pd.Timestamp, loaded_year: int) -> NextGrandPrixSchedule | None:
    if df is None or df.empty:
        return None
    work = _ordered_frame(df)
    for _, row in work.iterrows():
        if not _round_ok(row) or _is_testing_row(row):
            continue
        future_times: list[pd.Timestamp] = []
        for n in range(1, 6):
            dcol = f"Session{n}DateUtc"
            if dcol not in row.index:
                continue
            raw = row[dcol]
            if pd.isna(raw):
                continue
            ts = pd.Timestamp(raw)
            if ts > now_ts:
                future_times.append(ts)
        if not future_times:
            continue

        sessions_utc: dict[str, datetime] = {}
        for n in range(1, 6):
            dcol = f"Session{n}DateUtc"
            if dcol not in row.index:
                continue
            raw = row[dcol]
            if pd.isna(raw):
                continue
            ts = pd.Timestamp(raw).to_pydatetime().replace(tzinfo=None)
            sessions_utc[_session_label(row, n)] = ts

        event_name = ""
        if "EventName" in row.index and not pd.isna(row["EventName"]):
            event_name = str(row["EventName"])
        official = None
        if "OfficialEventName" in row.index and not pd.isna(row["OfficialEventName"]):
            official = str(row["OfficialEventName"])
        country = None
        if "Country" in row.index and not pd.isna(row["Country"]):
            country = str(row["Country"])
        location = None
        if "Location" in row.index and not pd.isna(row["Location"]):
            location = str(row["Location"])
        event_date: date | datetime | None = None
        if "EventDate" in row.index:
            event_date = _as_date_or_dt(row["EventDate"])

        return NextGrandPrixSchedule(
            event_name=event_name or official or "Unknown",
            official_name=official,
            country=country,
            location=location,
            event_date=event_date,
            sessions_utc=sessions_utc,
            schedule_data_quality=_quality_for_year(loaded_year),
            season_year=loaded_year,
        )
    return None


def resolve_next_grand_prix_schedule(season_year: int | None = None) -> NextGrandPrixSchedule:
    """Return the next non-testing GP whose earliest future session UTC is strictly after TimeAPI now.

    If ``season_year`` is ``None``, try the UTC calendar year of TimeAPI «now», then ``year + 1``.
    If ``season_year`` is set, try that year then ``season_year + 1``. Session filtering always
    uses the authoritative instant from :func:`fetch_timeapi_now`.
    """
    now = fetch_timeapi_now()
    now_ts = pd.Timestamp(now.utc_naive)

    if season_year is None:
        years = [now.utc_naive.year, now.utc_naive.year + 1]
    else:
        years = [season_year, season_year + 1]

    last_err: str | None = None
    for y in years:
        try:
            schedule = fastf1.get_event_schedule(y, include_testing=False)
        except Exception as e:
            last_err = str(e)
            continue
        if schedule is None:
            last_err = "get_event_schedule returned None"
            continue
        if hasattr(schedule, "empty") and schedule.empty:
            last_err = "empty schedule"
            continue
        if not isinstance(schedule, pd.DataFrame):
            last_err = "schedule is not a DataFrame"
            continue
        picked = _pick_from_year(schedule, now_ts, y)
        if picked is not None:
            return picked

    detail = f" ({last_err})" if last_err else ""
    raise ScheduleResolutionError(f"No upcoming grand prix found for years {years}{detail}")
