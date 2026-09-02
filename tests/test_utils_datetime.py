"""Tests for the shared Tracker date/time formatting helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone, tzinfo

import pytest
from yatracker.utils.datetime import to_tracker_date, to_tracker_datetime


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

    def test_tzinfo_without_offset_counts_as_naive(self) -> None:
        class NoOffset(tzinfo):
            def utcoffset(self, dt: datetime | None) -> timedelta | None:  # noqa: ARG002
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
