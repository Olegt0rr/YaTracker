"""Helpers rendering dates and timestamps the way Tracker API expects them."""

from __future__ import annotations

from datetime import date, datetime
from typing import overload
from warnings import warn

__all__ = ["NAIVE_DATETIME_WARNING", "to_tracker_date", "to_tracker_datetime"]

NAIVE_DATETIME_WARNING = (
    "Tracker API may work incorrectly with naive datetime. "
    "Please use Timezone-Aware objects."
)


@overload
def to_tracker_datetime(value: None, *, stacklevel: int = ...) -> None: ...


@overload
def to_tracker_datetime(value: datetime | str, *, stacklevel: int = ...) -> str: ...


@overload
def to_tracker_datetime(
    value: datetime | str | None,
    *,
    stacklevel: int = ...,
) -> str | None: ...


def to_tracker_datetime(
    value: datetime | str | None,
    *,
    stacklevel: int = 3,
) -> str | None:
    """Render a timestamp as ``YYYY-MM-DDThh:mm:ss.sss±hhmm``.

    That is the format Tracker API documents for every timestamp
    parameter. Strings and ``None`` are passed through verbatim, so a
    caller may always hand over a ready-made API string.

    A naive ``datetime`` is rendered without an offset and triggers a
    :class:`UserWarning`. ``stacklevel`` should point at the user's call
    site: ``3`` when this helper is called directly from a public method,
    plus one for every extra frame in between.
    """
    if not isinstance(value, datetime):
        return value

    if value.tzinfo is None:
        warn(NAIVE_DATETIME_WARNING, UserWarning, stacklevel=stacklevel)

    milliseconds = value.microsecond // 1000
    return f"{value:%Y-%m-%dT%H:%M:%S}.{milliseconds:03d}{value:%z}"


@overload
def to_tracker_date(value: None) -> None: ...


@overload
def to_tracker_date(value: date | str) -> str: ...


@overload
def to_tracker_date(value: date | str | None) -> str | None: ...


def to_tracker_date(value: date | str | None) -> str | None:
    """Render a date as ``YYYY-MM-DD``; strings and ``None`` pass through.

    A ``datetime`` is truncated to its date part.
    """
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value
