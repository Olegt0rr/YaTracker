"""Tests for the `FullIssue` fields carried by the search response.

The payload is the response sample of
https://yandex.ru/support/tracker/ru/api/issues/search-issues
with the masked (`********`) identifiers filled in.

Two of its keys used to be lost: `lastCommentUpdatedAt` (the automatic
alias would have been `lastCommentUpdateAt`) and `project`, which had no
field at all.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from yatracker.tracker.base import BaseTracker
from yatracker.types.full_issue import FullIssue

from tests.conftest import make_tracker

USER: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/users/1120000000000001",
    "id": "1120000000000001",
    "display": "Имя Фамилия",
    "cloudUid": "ajeppa7dgp531234abcd",
    "passportUid": 1120000000000001,
}

SEARCH_ISSUE: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issues/TREK-9844",
    "id": "593cd211ef7e8a3312345678",
    "key": "TREK-9844",
    "version": 7,
    "lastCommentUpdatedAt": "2017-07-18T13:33:44.291+0000",
    "summary": "subtask",
    "parent": {
        "self": "https://api.tracker.yandex.net/v3/issues/JUNE-2",
        "id": "593cd0acef7e8a3312345678",
        "key": "JUNE-2",
        "display": "Task",
    },
    "aliases": ["JUNE-3"],
    "updatedBy": USER,
    "description": "<#<html><head></head><body><div>test</div></body></html>#>",
    "sprint": [
        {
            "self": "https://api.tracker.yandex.net/v3/sprints/5301",
            "id": "5301",
            "display": "Sprint 1",
        },
    ],
    "type": {
        "self": "https://api.tracker.yandex.net/v3/issuetypes/2",
        "id": "2",
        "key": "task",
        "display": "Задача",
    },
    "priority": {
        "self": "https://api.tracker.yandex.net/v3/priorities/2",
        "id": "2",
        "key": "normal",
        "display": "Средний",
    },
    "createdAt": "2017-06-11T05:16:01.339+0000",
    "followers": [USER],
    "createdBy": USER,
    "votes": 0,
    "assignee": USER,
    "project": {
        "primary": {
            "self": "https://api.tracker.yandex.net/v3/projects/1",
            "id": "1",
            "display": "New project",
        },
        "secondary": [],
    },
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/TREK",
        "id": "111",
        "key": "TREK",
        "display": "My queue",
    },
    "updatedAt": "2017-07-18T13:33:44.291+0000",
    "status": {
        "self": "https://api.tracker.yandex.net/v3/statuses/1",
        "id": "1",
        "key": "open",
        "display": "Открыт",
    },
    "previousStatus": {
        "self": "https://api.tracker.yandex.net/v3/statuses/2",
        "id": "2",
        "key": "resolved",
        "display": "Решен",
    },
    "favorite": False,
}


class TestLastCommentUpdatedAt:
    def test_decodes_the_documented_key(self) -> None:
        issue = FullIssue.model_validate(SEARCH_ISSUE)
        assert issue.last_comment_update_at == datetime(
            2017,
            7,
            18,
            13,
            33,
            44,
            291000,
            tzinfo=timezone(timedelta(0)),
        )

    def test_stays_none_without_the_key(self) -> None:
        payload = {k: v for k, v in SEARCH_ISSUE.items() if k != "lastCommentUpdatedAt"}
        assert FullIssue.model_validate(payload).last_comment_update_at is None

    def test_payload_encodes_the_field_under_the_documented_key(self) -> None:
        result = BaseTracker._prepare_payload(
            {"last_comment_update_at": "2017-07-18T13:33:44.291+0000"},
            type_=FullIssue,
        )
        assert result == {"lastCommentUpdatedAt": "2017-07-18T13:33:44.291+0000"}


class TestProject:
    def test_decodes_primary_and_secondary(self) -> None:
        issue = FullIssue.model_validate(SEARCH_ISSUE)
        assert issue.project is not None
        assert issue.project.primary is not None
        assert issue.project.primary.id == "1"
        assert issue.project.primary.display == "New project"
        assert issue.project.primary.url == (
            "https://api.tracker.yandex.net/v3/projects/1"
        )
        assert issue.project.secondary == []

    def test_stays_none_without_the_key(self) -> None:
        payload = {k: v for k, v in SEARCH_ISSUE.items() if k != "project"}
        assert FullIssue.model_validate(payload).project is None

    def test_is_dropped_from_a_request_body_when_none(self) -> None:
        payload = {k: v for k, v in SEARCH_ISSUE.items() if k != "project"}
        issue = FullIssue.model_validate(payload)
        assert "project" not in issue._to_request()


class TestTags:
    """`tags` is a documented response parameter, absent from the samples."""

    def test_decodes_the_documented_key(self) -> None:
        payload = {**SEARCH_ISSUE, "tags": ["tag1", "tag2"]}
        assert FullIssue.model_validate(payload).tags == ["tag1", "tag2"]

    def test_stays_none_without_the_key(self) -> None:
        assert "tags" not in SEARCH_ISSUE
        assert FullIssue.model_validate(SEARCH_ISSUE).tags is None

    def test_is_dropped_from_a_request_body_when_none(self) -> None:
        issue = FullIssue.model_validate(SEARCH_ISSUE)
        assert "tags" not in issue._to_request()

    async def test_find_issues_decodes_it(self) -> None:
        tracker, _ = make_tracker([{**SEARCH_ISSUE, "tags": ["release"]}])
        issues = await tracker.find_issues(query="Queue: TREK")
        assert issues[0].tags == ["release"]


class TestUserReference:
    """The short `User` carries the account identifiers, too."""

    def test_decodes_passport_and_cloud_uid(self) -> None:
        issue = FullIssue.model_validate(SEARCH_ISSUE)
        assert issue.created_by.passport_uid == 1120000000000001
        assert issue.created_by.cloud_uid == "ajeppa7dgp531234abcd"

    def test_stays_none_without_the_keys(self) -> None:
        short_user = {k: v for k, v in USER.items() if k in {"self", "id", "display"}}
        payload = {**SEARCH_ISSUE, "createdBy": short_user}
        issue = FullIssue.model_validate(payload)
        assert issue.created_by.passport_uid is None
        assert issue.created_by.cloud_uid is None


class TestSearchResponse:
    async def test_find_issues_decodes_both_fields(self) -> None:
        tracker, _ = make_tracker([SEARCH_ISSUE])
        issues = await tracker.find_issues(query="Queue: TREK")

        assert len(issues) == 1
        issue = issues[0]
        assert issue.last_comment_update_at is not None
        assert issue.project is not None
        assert issue.project.primary is not None
        assert issue.project.primary.display == "New project"
