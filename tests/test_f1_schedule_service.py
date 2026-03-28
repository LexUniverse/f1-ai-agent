"""Unit tests for FastF1 schedule resolver (synthetic DataFrames, mocked TimeAPI)."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from src.integrations import (
    NextGrandPrixSchedule,
    ScheduleResolutionError,
    TimeApiNow,
    resolve_next_grand_prix_schedule,
)


def _freeze_now(monkeypatch: pytest.MonkeyPatch, utc_naive: datetime) -> None:
    unix = int(utc_naive.replace(tzinfo=timezone.utc).timestamp())
    monkeypatch.setattr(
        "src.integrations.f1_schedule_service.fetch_timeapi_now",
        lambda: TimeApiNow(unix_timestamp=unix, utc_naive=utc_naive),
    )


def test_picks_later_round_when_now_between_events(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch, datetime(2024, 5, 10, 12, 0, 0))
    df = pd.DataFrame(
        [
            {
                "RoundNumber": 1,
                "EventFormat": "conventional",
                "EventName": "Early GP",
                "EventDate": pd.Timestamp("2024-05-01"),
                "Session1DateUtc": pd.Timestamp("2024-05-03 12:00:00"),
                "Session1": "FP1",
            },
            {
                "RoundNumber": 2,
                "EventFormat": "conventional",
                "EventName": "Late GP",
                "EventDate": pd.Timestamp("2024-06-01"),
                "Session1DateUtc": pd.Timestamp("2024-06-07 14:00:00"),
                "Session1": "FP1",
            },
        ]
    )

    monkeypatch.setattr(
        "src.integrations.f1_schedule_service.fastf1.get_event_schedule",
        lambda year, include_testing=False: df if year == 2024 else pd.DataFrame(),
    )

    out = resolve_next_grand_prix_schedule()
    assert isinstance(out, NextGrandPrixSchedule)
    assert out.event_name == "Late GP"
    assert out.season_year == 2024
    assert "FP1" in out.sessions_utc


def test_skips_round_zero_and_testing(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch, datetime(2024, 5, 10, 12, 0, 0))
    df = pd.DataFrame(
        [
            {
                "RoundNumber": 0,
                "EventFormat": "conventional",
                "EventName": "Bad",
                "EventDate": pd.Timestamp("2024-05-20"),
                "Session1DateUtc": pd.Timestamp("2024-05-22 12:00:00"),
                "Session1": "X",
            },
            {
                "RoundNumber": 3,
                "EventFormat": "testing",
                "EventName": "Test",
                "EventDate": pd.Timestamp("2024-05-21"),
                "Session1DateUtc": pd.Timestamp("2024-05-23 12:00:00"),
                "Session1": "T",
            },
            {
                "RoundNumber": 4,
                "EventFormat": "conventional",
                "EventName": "Real",
                "EventDate": pd.Timestamp("2024-05-25"),
                "Session1DateUtc": pd.Timestamp("2024-05-26 12:00:00"),
                "Session1": "FP1",
            },
        ]
    )
    monkeypatch.setattr(
        "src.integrations.f1_schedule_service.fastf1.get_event_schedule",
        lambda year, include_testing=False: df if year == 2024 else pd.DataFrame(),
    )

    out = resolve_next_grand_prix_schedule()
    assert out.event_name == "Real"


def test_year_rollover_second_schedule_call(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch, datetime(2024, 12, 15, 12, 0, 0))
    df2024 = pd.DataFrame(
        [
            {
                "RoundNumber": 1,
                "EventFormat": "conventional",
                "EventName": "Past",
                "EventDate": pd.Timestamp("2024-03-01"),
                "Session1DateUtc": pd.Timestamp("2024-03-01 12:00:00"),
                "Session1": "FP1",
            },
        ]
    )
    df2025 = pd.DataFrame(
        [
            {
                "RoundNumber": 1,
                "EventFormat": "conventional",
                "EventName": "Next season",
                "EventDate": pd.Timestamp("2025-03-01"),
                "Session1DateUtc": pd.Timestamp("2025-03-05 12:00:00"),
                "Session1": "FP1",
            },
        ]
    )
    years: list[int] = []

    def fake_get(year: int, include_testing: bool = False) -> pd.DataFrame:
        assert include_testing is False
        years.append(year)
        if year == 2024:
            return df2024
        if year == 2025:
            return df2025
        return pd.DataFrame()

    monkeypatch.setattr(
        "src.integrations.f1_schedule_service.fastf1.get_event_schedule",
        fake_get,
    )

    out = resolve_next_grand_prix_schedule()
    assert out.event_name == "Next season"
    assert years == [2024, 2025]


def test_pre_2018_marks_ergast_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch, datetime(2007, 6, 1, 12, 0, 0))
    df = pd.DataFrame(
        [
            {
                "RoundNumber": 3,
                "EventFormat": "conventional",
                "EventName": "Canada",
                "Country": "Canada",
                "Location": "Montreal",
                "EventDate": pd.Timestamp("2007-06-10"),
                "Session1DateUtc": pd.Timestamp("2007-06-08 16:00:00"),
                "Session1": "FP1",
            },
        ]
    )
    monkeypatch.setattr(
        "src.integrations.f1_schedule_service.fastf1.get_event_schedule",
        lambda year, include_testing=False: df if year == 2007 else pd.DataFrame(),
    )

    out = resolve_next_grand_prix_schedule(season_year=2007)
    assert out.schedule_data_quality == "ergast_limited"


def test_schedule_resolution_error_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_now(monkeypatch, datetime(2024, 5, 10, 12, 0, 0))
    monkeypatch.setattr(
        "src.integrations.f1_schedule_service.fastf1.get_event_schedule",
        lambda year, include_testing=False: pd.DataFrame(),
    )
    with pytest.raises(ScheduleResolutionError):
        resolve_next_grand_prix_schedule()


def test_import_star_surface() -> None:
    """Stable re-exports from package (explicit import avoids star)."""
    from src.integrations import (  # noqa: PLC0415
        NextGrandPrixSchedule,
        ScheduleResolutionError,
        TIMEAPI_UNAVAILABLE_MESSAGE_RU,
        TimeApiError,
        TimeApiNow,
        degraded_message_ru,
        fetch_timeapi_now,
        resolve_next_grand_prix_schedule,
    )

    assert callable(fetch_timeapi_now)
    assert callable(resolve_next_grand_prix_schedule)
    assert callable(degraded_message_ru)
    assert TIMEAPI_UNAVAILABLE_MESSAGE_RU
    assert TimeApiError and TimeApiNow and NextGrandPrixSchedule and ScheduleResolutionError
