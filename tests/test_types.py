"""Tests for the plain types: Duration, Transitions, Printable and helpers.

Also covers the "shortcut" coroutines that models expose by delegating
back to the tracker that produced them (``FullIssue.get_comments()``,
``Transition.execute()``, ``Worklog.delete()``, ...).
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from yatracker import YaTracker
from yatracker.types import (
    Comment,
    Duration,
    FullIssue,
    IssueLink,
    QueueVersionRef,
    Transition,
    Transitions,
    User,
)
from yatracker.utils.camel_case import camel_case

from tests.conftest import FakeClient, full_issue_body

STATUS: dict[str, Any] = {
    "self": "https://api/statuses/5",
    "id": "5",
    "key": "open",
    "display": "Open",
}
USER: dict[str, Any] = {"self": "https://api/users/4", "id": "4", "display": "User"}
SHORT_ISSUE: dict[str, Any] = {
    "self": "https://api/issues/1",
    "id": "1",
    "key": "TEST-1",
    "display": "Test issue",
}


def transition_payload(id_: str, display: str) -> dict[str, Any]:
    return {
        "self": f"https://api/issues/1/transitions/{id_}",
        "id": id_,
        "display": display,
        "to": STATUS,
    }


def comment_payload() -> dict[str, Any]:
    return {
        "self": "https://api/issues/1/comments/1",
        "id": 1,
        "text": "hello",
        "createdBy": USER,
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "version": 1,
    }


def issue_link_payload(direction: str = "outward") -> dict[str, Any]:
    return {
        "self": "https://api/issues/1/links/2",
        "id": 2,
        "type": {
            "self": "https://api/linktypes/relates",
            "id": "relates",
            "inward": "Relates",
            "outward": "Relates to",
        },
        "direction": direction,
        "object": SHORT_ISSUE,
        "createdBy": USER,
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "status": STATUS,
    }


def worklog_payload() -> dict[str, Any]:
    return {
        "self": "https://api/worklog/7",
        "id": 7,
        "version": 1,
        "issue": SHORT_ISSUE,
        "createdBy": USER,
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "start": "2024-01-01T00:00:00.000+0000",
        "duration": "PT1H",
    }


def encode(payload: Any) -> bytes:
    return json.dumps(payload).encode()


class TestDuration:
    @pytest.mark.parametrize(
        ("kwargs", "expected"),
        [
            ({"years": 1}, "P1Y"),
            ({"months": 2}, "P2M"),
            ({"days": 3}, "P3D"),
            ({"hours": 4}, "PT4H"),
            ({"minutes": 5}, "PT5M"),
            ({"seconds": 6}, "PT6S"),
        ],
    )
    def test_single_component(self, kwargs, expected) -> None:
        assert Duration(**kwargs).to_iso() == expected

    def test_all_components(self) -> None:
        duration = Duration(
            years=1,
            months=2,
            days=3,
            hours=4,
            minutes=5,
            seconds=6,
        )
        assert duration.to_iso() == "P1Y2M3DT4H5M6S"

    def test_time_only(self) -> None:
        assert Duration(hours=1, minutes=30).to_iso() == "PT1H30M"

    def test_date_only(self) -> None:
        assert Duration(years=1, days=2).to_iso() == "P1Y2D"

    def test_empty_duration_is_bare_p(self) -> None:
        assert Duration().to_iso() == "P"

    def test_from_iso_reads_every_component(self) -> None:
        assert Duration.from_iso("P1Y2M3DT4H5M6S") == Duration(
            years=1,
            months=2,
            days=3,
            hours=4,
            minutes=5,
            seconds=6,
        )

    def test_from_iso_round_trip(self) -> None:
        duration = Duration(months=2, days=3, minutes=15)
        assert Duration.from_iso(duration.to_iso()) == duration

    def test_from_iso_time_only_round_trip(self) -> None:
        """Time-only durations (the common worklog format) must parse."""
        duration = Duration(hours=2, minutes=30)
        assert Duration.from_iso("PT2H30M") == duration
        assert Duration.from_iso(duration.to_iso()) == duration

    def test_from_iso_ignores_weeks(self) -> None:
        """`weeks` is matched by the pattern but is not a Duration field."""
        assert Duration.from_iso("P1W2DT3H") == Duration(days=2, hours=3)

    @pytest.mark.parametrize("value", ["", "1H", "P", "12345", "PXY"])
    def test_from_iso_rejects_garbage(self, value) -> None:
        with pytest.raises(ValueError, match="ISO duration pattern"):
            Duration.from_iso(value)


class TestTransitions:
    def test_iterates_values_in_insertion_order(self) -> None:
        close = Transition.model_validate(transition_payload("close", "Close"))
        start = Transition.model_validate(transition_payload("start", "Start"))
        transitions = Transitions(close=close, start=start)

        assert list(transitions) == [close, start]

    def test_stops_after_the_last_value(self) -> None:
        close = Transition.model_validate(transition_payload("close", "Close"))
        transitions = Transitions(close=close)

        iterator = iter(transitions)
        assert next(iterator) is close
        with pytest.raises(StopIteration):
            next(iterator)

    def test_stays_a_dict(self) -> None:
        close = Transition.model_validate(transition_payload("close", "Close"))
        transitions = Transitions(close=close)

        assert transitions["close"] is close
        assert transitions.get("missing") is None


class TestPrintable:
    def test_display_is_used_when_set(self) -> None:
        assert str(User.model_validate(USER)) == "User"

    def test_class_name_is_used_when_display_is_none(self) -> None:
        payload = {"self": "https://api/versions/4", "id": "4"}
        ref = QueueVersionRef.model_validate(payload)
        assert ref.display is None
        assert str(ref) == "QueueVersionRef"

    def test_model_without_display_falls_back_to_field_dump(self) -> None:
        comment = Comment.model_validate(comment_payload())
        assert "display" not in Comment.model_fields
        assert "text='hello'" in str(comment)


class TestIssueLink:
    @pytest.mark.parametrize(
        ("direction", "expected"),
        [("outward", "Relates to"), ("inward", "Relates")],
    )
    def test_name_follows_direction(self, direction, expected) -> None:
        link = IssueLink.model_validate(issue_link_payload(direction))
        assert link.name == expected


class TestModelShortcuts:
    async def test_get_transitions(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, encode([transition_payload("close", "Close")]), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        transitions = await issue.get_transitions()
        assert isinstance(transitions, Transitions)
        assert transitions["close"].display == "Close"
        assert client.calls[1]["url"].endswith("/issues/1/transitions")

    async def test_get_comments(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, encode([comment_payload()]), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        comments = await issue.get_comments()
        assert [c.text for c in comments] == ["hello"]
        assert client.calls[1]["method"] == "GET"
        assert client.calls[1]["url"].endswith("/issues/1/comments")

    async def test_post_comment(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, encode(comment_payload()), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        comment = await issue.post_comment("hello", summonees=["user1"])
        assert comment.id == 1
        call = client.calls[1]
        assert call["method"] == "POST"
        assert call["url"].endswith("/issues/1/comments/")
        assert json.loads(call["data"]._value) == {
            "text": "hello",
            "summonees": ["user1"],
        }

    async def test_get_links(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, encode([issue_link_payload()]), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        links = await issue.get_links()
        assert [link.name for link in links] == ["Relates to"]
        assert client.calls[1]["url"].endswith("/issues/1/links")

    async def test_transition_execute(self) -> None:
        payload = transition_payload("close", "Close")
        client = FakeClient(
            responses=[
                (200, encode([payload]), {}),
                (200, encode([payload]), {}),
            ],
        )
        tracker = YaTracker(client=client)
        transitions = await tracker.get_transitions("TEST-1")

        await transitions["close"].execute()
        call = client.calls[1]
        assert call["method"] == "POST"
        assert call["url"] == f"{payload['self']}/_execute"

    async def test_worklog_delete(self) -> None:
        client = FakeClient(
            responses=[
                (200, encode([worklog_payload()]), {}),
                (200, b"", {}),
            ],
        )
        tracker = YaTracker(client=client)
        worklog = (await tracker.get_issue_worklog("TEST-1"))[0]

        assert await worklog.delete() is True
        call = client.calls[1]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/issues/1/worklog/7")

    async def test_full_issue_is_returned_with_tracker_attached(self) -> None:
        client = FakeClient(body=full_issue_body())
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        assert isinstance(issue, FullIssue)
        assert issue._tracker is tracker


class TestCamelCase:
    def test_empty_string_is_returned_as_is(self) -> None:
        assert camel_case("") == ""

    def test_trailing_underscore_is_stripped(self) -> None:
        assert camel_case("filter_") == "filter"

    def test_snake_case_is_converted(self) -> None:
        assert camel_case("attachment_ids") == "attachmentIds"
