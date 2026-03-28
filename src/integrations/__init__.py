"""External integration modules (TimeAPI clock, FastF1 schedule)."""

from src.integrations.f1_schedule_service import (
    NextGrandPrixSchedule,
    ScheduleResolutionError,
    resolve_next_grand_prix_schedule,
)
from src.integrations.messages_ru import TIMEAPI_UNAVAILABLE_MESSAGE_RU
from src.integrations.timeapi_client import (
    TimeApiError,
    TimeApiNow,
    degraded_message_ru,
    fetch_timeapi_now,
)

__all__ = [
    "NextGrandPrixSchedule",
    "ScheduleResolutionError",
    "TIMEAPI_UNAVAILABLE_MESSAGE_RU",
    "TimeApiError",
    "TimeApiNow",
    "degraded_message_ru",
    "fetch_timeapi_now",
    "resolve_next_grand_prix_schedule",
]
