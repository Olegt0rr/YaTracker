"""Helpers rendering dates and timestamps the way Tracker API expects them."""

from __future__ import annotations

import os
import sys
import warnings
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import FrameType

__all__ = [
    "NAIVE_DATETIME_WARNING",
    "suppress_naive_warnings",
    "to_tracker_date",
    "to_tracker_datetime",
    "user_stacklevel",
]

NAIVE_DATETIME_WARNING = (
    "Tracker API may work incorrectly with naive datetime. "
    "Please use Timezone-Aware objects."
)

_NAIVE_WARNINGS_SUPPRESSED: ContextVar[bool] = ContextVar(
    "yatracker_naive_warnings_suppressed",
    default=False,
)


@contextmanager
def suppress_naive_warnings() -> Iterator[None]:
    """Render naive datetimes without warning about them.

    A caller that walks a whole payload (the entities API does) reports
    the naive values once, from its own frame, and the helpers rendering
    the individual values must stay quiet while it does. A
    :class:`~contextvars.ContextVar` is used rather than
    `warnings.catch_warnings`, which is not thread-safe and resets the
    `__warningregistry__` of every module in the process, breaking the
    deduplication of `once`/`default` filters in the user's own code.

    Only the naive-datetime warning is silenced; anything else raised
    while rendering propagates as usual.
    """
    token = _NAIVE_WARNINGS_SUPPRESSED.set(True)
    try:
        yield
    finally:
        _NAIVE_WARNINGS_SUPPRESSED.reset(token)


# Every module of the library lives under this prefix, so a frame whose
# file does not start with it belongs to the code that called us.
_PACKAGE_ROOT = f"{Path(__file__).parent.parent}{os.sep}"


def user_stacklevel(frame: FrameType | None) -> int:
    """Return the `stacklevel` of the first frame outside of yatracker.

    Pass the frame that calls :func:`warnings.warn` (usually
    ``sys._getframe(0)``) and the result is the `stacklevel` that makes
    the warning point at the user's own code, however many internal
    helpers there are in between.

    :param frame: Frame the warning is raised from.
    :return: `stacklevel` for `warnings.warn` called from that frame.
    """
    level = 1
    while frame is not None:
        if not frame.f_code.co_filename.startswith(_PACKAGE_ROOT):
            return level
        frame = frame.f_back
        level += 1
    return level - 1


@overload
def to_tracker_datetime(
    value: None,
    *,
    stacklevel: int | None = ...,
    warn: bool = ...,
) -> None: ...


@overload
def to_tracker_datetime(
    value: date | datetime | str,
    *,
    stacklevel: int | None = ...,
    warn: bool = ...,
) -> str: ...


@overload
def to_tracker_datetime(
    value: date | datetime | str | None,
    *,
    stacklevel: int | None = ...,
    warn: bool = ...,
) -> str | None: ...


def to_tracker_datetime(
    value: date | datetime | str | None,
    *,
    stacklevel: int | None = None,
    warn: bool = True,
) -> str | None:
    """Render a timestamp as ``YYYY-MM-DDThh:mm:ss.sss±hhmm``.

    That is the format Tracker API documents for every timestamp
    parameter. Strings and ``None`` are passed through verbatim, so a
    caller may always hand over a ready-made API string.

    A bare ``date`` carries no time and no offset at all, so it is
    rendered as midnight UTC (``YYYY-MM-DDT00:00:00.000+0000``). UTC is
    picked rather than the local zone of the machine because the same
    ``date`` then reaches the API as the same instant wherever the code
    runs; pass an aware ``datetime`` when the offset matters. A bare
    ``date`` never warns: it is not a naive ``datetime``, it is a value
    that has no time to be naive about.

    A naive ``datetime`` is rendered without an offset and triggers a
    :class:`UserWarning`. By default the warning points at the first
    frame outside of the library, so callers do not have to count the
    helpers in between; pass ``stacklevel`` explicitly to override that.
    Pass ``warn=False`` when the caller warns about naive values on its
    own (the entities API does that once per request instead of once per
    value); a caller that cannot reach every rendering site can silence
    them all with :func:`suppress_naive_warnings` instead.
    """
    # `datetime` is a subclass of `date`, so it is matched first
    if not isinstance(value, datetime):
        if isinstance(value, date):
            value = datetime.combine(value, time.min, tzinfo=timezone.utc)
        else:
            return value

    # Python's definition of naive: no tzinfo, or a tzinfo without an offset
    if warn and not _NAIVE_WARNINGS_SUPPRESSED.get() and value.utcoffset() is None:
        if stacklevel is None:
            stacklevel = user_stacklevel(sys._getframe(0))  # noqa: SLF001
        warnings.warn(NAIVE_DATETIME_WARNING, UserWarning, stacklevel=stacklevel)

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
