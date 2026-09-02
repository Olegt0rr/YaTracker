"""Tests for the sprints category and the `FullSprint` struct.

Payloads are taken from the official documentation:
https://yandex.cloud/ru/docs/tracker/concepts/boards/get-sprints
https://yandex.cloud/ru/docs/tracker/concepts/boards/get-sprint
https://yandex.cloud/ru/docs/tracker/concepts/boards/post-sprint
https://yandex.cloud/ru/docs/tracker/concepts/boards/patch-sprint
https://yandex.cloud/ru/docs/tracker/concepts/boards/start-sprint
https://yandex.cloud/ru/docs/tracker/concepts/boards/archive-sprint
https://yandex.cloud/ru/docs/tracker/concepts/boards/delete-sprint
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from pydantic import TypeAdapter
from yatracker.types import FullIssue, FullSprint

from tests.conftest import full_issue_body, make_tracker, sent_json

# GET/POST/PATCH sprint response shape (shared by list, get, create, update,
# start and archive endpoints).
FULL_SPRINT: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/sprints/4411",
    "id": 4411,
    "version": 1435288720018,
    "name": "Sprint 1",
    "board": {
        "self": "https://api.tracker.yandex.net/v3/boards/3",
        "id": "3",
        "display": "My board",
    },
    "status": "in_progress",
    "archived": False,
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/33",
        "id": "33",
        "display": "Имя Фамилия",
    },
    "createdAt": "2015-06-23T17:03:24.799+0000",
    "startDate": "2015-06-01",
    "endDate": "2015-06-14",
    "startDateTime": "2015-06-01T07:00:00.000+0000",
    "endDateTime": "2015-06-14T07:00:00.000+0000",
}

# Short reference embedded in `FullIssue.sprint` (regression guard).
SPRINT_REF: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/sprints/4411",
    "id": "4411",
    "display": "Sprint 1",
}


class TestFullSprintDecoding:
    def test_full_response_decodes(self) -> None:
        sprint = TypeAdapter(FullSprint).validate_json(json.dumps(FULL_SPRINT))
        assert sprint.id == "4411"
        assert sprint.version == 1435288720018
        assert sprint.name == "Sprint 1"
        assert sprint.board.id == "3"
        assert sprint.board.display == "My board"
        assert sprint.status == "in_progress"
        assert sprint.archived is False
        assert sprint.created_by.display == "Имя Фамилия"
        assert sprint.created_at == datetime(
            2015,
            6,
            23,
            17,
            3,
            24,
            799000,
            tzinfo=timezone.utc,
        )
        assert sprint.start_date == date(2015, 6, 1)
        assert sprint.end_date == date(2015, 6, 14)
        assert sprint.start_date_time == datetime(
            2015,
            6,
            1,
            7,
            0,
            0,
            tzinfo=timezone.utc,
        )
        assert sprint.end_date_time == datetime(
            2015,
            6,
            14,
            7,
            0,
            0,
            tzinfo=timezone.utc,
        )

    def test_response_without_dates_decodes(self) -> None:
        payload = {
            k: v
            for k, v in FULL_SPRINT.items()
            if k not in {"startDate", "endDate", "startDateTime", "endDateTime"}
        }
        sprint = TypeAdapter(FullSprint).validate_json(json.dumps(payload))
        assert sprint.start_date is None
        assert sprint.end_date is None
        assert sprint.start_date_time is None
        assert sprint.end_date_time is None


class TestFullIssueSprintRegression:
    def test_issue_sprint_decodes_short_ref(self) -> None:
        """`FullIssue.sprint` stays the short `Sprint` ref, not `FullSprint`."""
        issue = TypeAdapter(FullIssue).validate_json(
            full_issue_body(sprint=[SPRINT_REF]),
        )
        assert issue.sprint is not None
        assert issue.sprint[0].id == "4411"
        assert issue.sprint[0].display == "Sprint 1"


class TestSprintEndpoints:
    async def test_get_sprints_uses_board_path(self) -> None:
        tracker, client = make_tracker([FULL_SPRINT])
        sprints = await tracker.get_sprints("3")
        assert len(sprints) == 1
        assert sprints[0].name == "Sprint 1"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/boards/3/sprints")

    async def test_get_sprint_uses_sprint_path(self) -> None:
        tracker, client = make_tracker(FULL_SPRINT)
        sprint = await tracker.get_sprint(4411)
        assert sprint.name == "Sprint 1"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/sprints/4411")

    async def test_create_sprint_sends_exact_body(self) -> None:
        tracker, client = make_tracker(FULL_SPRINT, status=201)
        sprint = await tracker.create_sprint(
            "New Sprint",
            1,
            date(2018, 10, 21),
            "2018-10-24",
        )
        assert sprint.id == "4411"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/sprints")
        assert sent_json(call) == {
            "name": "New Sprint",
            "board": {"id": "1"},
            "startDate": "2018-10-21",
            "endDate": "2018-10-24",
        }

    async def test_update_sprint_sends_if_match_and_partial_body(self) -> None:
        tracker, client = make_tracker(FULL_SPRINT)
        sprint = await tracker.update_sprint(
            4411,
            2,
            name="Renamed",
            status="in_progress",
        )
        assert sprint.name == "Sprint 1"

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/sprints/4411")
        assert call["headers"] == {"If-Match": '"2"'}
        assert sent_json(call) == {"name": "Renamed", "status": "in_progress"}

    async def test_update_sprint_renders_dates(self) -> None:
        tracker, client = make_tracker(FULL_SPRINT)
        await tracker.update_sprint(
            4411,
            2,
            start_date=date(2018, 10, 21),
            end_date="2018-10-24",
        )

        assert sent_json(client.calls[0]) == {
            "startDate": "2018-10-21",
            "endDate": "2018-10-24",
        }

    async def test_start_sprint_sends_if_match_and_no_body(self) -> None:
        tracker, client = make_tracker(FULL_SPRINT)
        sprint = await tracker.start_sprint(4411, 2)
        assert sprint.status == "in_progress"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/sprints/4411/_start")
        assert call["headers"] == {"If-Match": '"2"'}
        assert call.get("data") is None

    async def test_archive_sprint_sends_if_match_and_no_body(self) -> None:
        tracker, client = make_tracker(FULL_SPRINT)
        sprint = await tracker.archive_sprint(4411, 2)
        assert sprint.id == "4411"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/sprints/4411/_archive")
        assert call["headers"] == {"If-Match": '"2"'}
        assert call.get("data") is None

    async def test_delete_sprint_returns_true(self) -> None:
        tracker, client = make_tracker(status=204)
        assert await tracker.delete_sprint(4411) is True

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/sprints/4411")
