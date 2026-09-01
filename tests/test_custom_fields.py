"""Tests for the custom (local) fields extension story."""

from __future__ import annotations

import json
from typing import Any

from yatracker.tracker.base import BaseTracker
from yatracker.tracker.client import BaseClient
from yatracker.types import FullIssue, FullQueue, field

LOCAL_FIELD = "64a5--userId"


class HelpIssue(FullIssue):
    """Issue with a queue local field."""

    user_id: int | None = field(default=None, name=LOCAL_FIELD)


class FakeClient(BaseClient):
    """In-memory client returning canned responses."""

    def __init__(self, status: int = 200, body: bytes = b"{}") -> None:
        super().__init__(org_id="1", token="token")
        self.status = status
        self.body = body
        self.calls: list[dict[str, Any]] = []

    async def _make_request(
        self,
        method: str,
        url: Any,
        **kwargs,
    ) -> tuple[int, bytes, dict[str, str]]:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self.status, self.body, {}

    async def close(self) -> None:
        return


def make_tracker() -> BaseTracker:
    return BaseTracker(client=FakeClient())


def full_issue_dict(**overrides) -> dict[str, Any]:
    issue = {
        "self": "https://api/issues/1",
        "id": "1",
        "key": "TEST-1",
        "version": 1,
        "summary": "summary",
        "type": {"self": "t", "id": "1", "key": "bug", "display": "Bug"},
        "priority": {"self": "p", "id": "2", "key": "minor", "display": "Minor"},
        "queue": {"self": "q", "id": "3", "key": "TEST", "display": "Test"},
        "favorite": False,
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "createdBy": {"self": "u", "id": "4", "display": "User"},
        "votes": 0,
        "status": {"self": "s", "id": "5", "key": "open", "display": "Open"},
    }
    issue.update(overrides)
    return issue


def full_queue_dict(**overrides) -> dict[str, Any]:
    queue = {
        "self": "https://api/queues/TEST",
        "id": "3",
        "key": "TEST",
        "version": 1,
        "name": "Test",
        "lead": {"self": "u", "id": "4", "display": "User"},
        "assignAuto": False,
        "defaultType": {"self": "t", "id": "1", "key": "bug", "display": "Bug"},
        "defaultPriority": {
            "self": "p",
            "id": "2",
            "key": "minor",
            "display": "Minor",
        },
    }
    queue.update(overrides)
    return queue


class TestCustomFieldRoundTrip:
    def test_payload_uses_raw_local_field_name(self) -> None:
        result = BaseTracker._prepare_payload(
            {"summary": "s", "queue": "HELP", "user_id": 42},
            type_=HelpIssue,
        )
        assert result == {"summary": "s", "queue": "HELP", LOCAL_FIELD: 42}

    def test_decode_populates_custom_field(self) -> None:
        tracker = make_tracker()
        body = json.dumps(full_issue_dict(**{LOCAL_FIELD: 42})).encode()
        issue = tracker._decode(HelpIssue, body)
        assert isinstance(issue, HelpIssue)
        assert issue.user_id == 42

    def test_decode_without_custom_field_uses_default(self) -> None:
        tracker = make_tracker()
        issue = tracker._decode(HelpIssue, json.dumps(full_issue_dict()).encode())
        assert issue.user_id is None

    def test_legacy_name_matches_alias(self) -> None:
        assert HelpIssue.model_fields["user_id"].alias == LOCAL_FIELD


class TestTrackerInjection:
    def test_injected_on_top_level_model(self) -> None:
        tracker = make_tracker()
        issue = tracker._decode(FullIssue, json.dumps(full_issue_dict()).encode())
        assert issue._tracker is tracker

    def test_injected_inside_list(self) -> None:
        tracker = make_tracker()
        body = json.dumps([full_issue_dict(), full_issue_dict(key="TEST-2")]).encode()
        issues = tracker._decode(list[FullIssue], body)
        assert len(issues) == 2
        for issue in issues:
            assert issue._tracker is tracker

    def test_injected_inside_dict_value(self) -> None:
        tracker = make_tracker()
        body = json.dumps(
            full_queue_dict(
                workflows={
                    "dev": [{"self": "t", "id": "1", "key": "bug", "display": "Bug"}],
                },
            ),
        ).encode()
        queue = tracker._decode(FullQueue, body)
        assert queue.workflows is not None
        assert queue.workflows["dev"][0]._tracker is tracker

    def test_not_injected_without_context(self) -> None:
        issue = FullIssue(**full_issue_dict())
        assert issue._tracker is None


class TestNumberCoercion:
    def test_numeric_id_coerced_to_str(self) -> None:
        tracker = make_tracker()
        body = json.dumps(full_queue_dict(id=3)).encode()
        queue = tracker._decode(FullQueue, body)
        assert queue.id == "3"
