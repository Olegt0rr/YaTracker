"""Tests for the shared Tracker date/time formatting helpers."""

from __future__ import annotations

import sys
import warnings
from datetime import date, datetime, timedelta, timezone, tzinfo
from functools import partial
from pathlib import Path
from typing import Any

import pytest
import yatracker
from yatracker.utils.datetime import (
    to_tracker_date,
    to_tracker_datetime,
    user_stacklevel,
)

# A file name inside the installed package: frames compiled with it are
# indistinguishable from real library frames for `user_stacklevel`.
PACKAGE_FILE = str(Path(yatracker.__file__).parent / "_frames_for_tests.py")

FAKE_LIBRARY_MODULE = """
import sys


def leaf(measure):
    return measure(sys._getframe(0))


def nest(inner):
    return inner()
"""


def call_through_library_frames(depth: int) -> int:
    """Ask `user_stacklevel` from `depth` nested frames that look like yatracker."""
    namespace: dict[str, Any] = {}
    exec(compile(FAKE_LIBRARY_MODULE, PACKAGE_FILE, "exec"), namespace)  # noqa: S102

    # `functools.partial` is implemented in C and adds no Python frame
    call = partial(namespace["leaf"], user_stacklevel)
    for _ in range(depth - 1):
        call = partial(namespace["nest"], call)
    return call()


class TestUserStacklevel:
    def test_call_from_user_code_is_the_frame_itself(self) -> None:
        assert user_stacklevel(sys._getframe(0)) == 1

    def test_user_frames_are_never_skipped(self) -> None:
        def helper() -> int:
            # this file is not part of the package, so the very first
            # frame already belongs to "user code"
            return user_stacklevel(sys._getframe(0))

        assert helper() == 1

    def test_one_library_frame_points_at_its_caller(self) -> None:
        assert call_through_library_frames(1) == 2

    def test_every_library_frame_in_between_is_skipped(self) -> None:
        assert call_through_library_frames(2) == 3
        assert call_through_library_frames(5) == 6

    def test_missing_frame_falls_back_to_the_last_level(self) -> None:
        # `sys._getframe` may be unavailable and the walk may run out of
        # frames; both end up here instead of raising
        assert user_stacklevel(None) == 0


class TestToTrackerDatetime:
    def test_none_and_str_pass_through(self) -> None:
        assert to_tracker_datetime(None) is None
        assert to_tracker_datetime("2024-01-01T00:00:00.000+0000") == (
            "2024-01-01T00:00:00.000+0000"
        )

    def test_aware_datetime_uses_documented_offset_form(self) -> None:
        utc = datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=timezone.utc)
        assert to_tracker_datetime(utc) == "2024-01-01T12:30:45.123+0000"

        plus_three = datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=3)))
        assert to_tracker_datetime(plus_three) == "2024-01-01T00:00:00.000+0300"

        minus_five = datetime(
            2024,
            1,
            1,
            tzinfo=timezone(-timedelta(hours=5, minutes=30)),
        )
        assert to_tracker_datetime(minus_five) == "2024-01-01T00:00:00.000-0530"

    def test_naive_datetime_warns_and_has_no_offset(self) -> None:
        with pytest.warns(UserWarning, match="naive datetime") as record:
            result = to_tracker_datetime(datetime(2024, 1, 1), stacklevel=2)  # noqa: DTZ001
        assert result == "2024-01-01T00:00:00.000"
        assert record[0].filename == __file__

    def test_naive_datetime_warning_points_at_the_caller_by_default(self) -> None:
        with pytest.warns(UserWarning, match="naive datetime") as record:
            to_tracker_datetime(datetime(2024, 1, 1))  # noqa: DTZ001
        assert record[0].filename == __file__

    def test_naive_datetime_warning_skips_intermediate_library_frames(self) -> None:
        # `_build_deadline` -> `_checklist_item_payload` -> the public
        # method: none of those frames may be blamed for the warning
        from yatracker.tracker.categories.entity_checklists import (  # noqa: PLC0415
            _checklist_item_payload,
        )

        with pytest.warns(UserWarning, match="naive datetime") as record:
            _checklist_item_payload(
                text="Item",
                checked=None,
                assignee=None,
                deadline=datetime(2024, 1, 1),  # noqa: DTZ001
            )
        assert record[0].filename == __file__

    def test_warn_false_stays_quiet(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert to_tracker_datetime(datetime(2024, 1, 1), warn=False) == (  # noqa: DTZ001
                "2024-01-01T00:00:00.000"
            )

    def test_tzinfo_without_offset_counts_as_naive(self) -> None:
        class NoOffset(tzinfo):
            def utcoffset(self, dt: datetime | None) -> timedelta | None:  # noqa: ARG002
                return None

            def dst(self, dt: datetime | None) -> timedelta | None:  # noqa: ARG002
                return None

            def tzname(self, dt: datetime | None) -> str | None:  # noqa: ARG002
                return None

        value = datetime(2024, 1, 1, tzinfo=NoOffset())
        with pytest.warns(UserWarning, match="naive datetime"):
            assert to_tracker_datetime(value) == "2024-01-01T00:00:00.000"


class TestToTrackerDate:
    def test_none_and_str_pass_through(self) -> None:
        assert to_tracker_date(None) is None
        assert to_tracker_date("2024-01-01") == "2024-01-01"

    def test_date_and_datetime(self) -> None:
        assert to_tracker_date(date(2024, 1, 31)) == "2024-01-31"
        aware = datetime(2024, 1, 31, 23, 59, tzinfo=timezone.utc)
        assert to_tracker_date(aware) == "2024-01-31"
