"""Tests for the autoactions category and its models.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/queues/create-autoaction
https://yandex.ru/support/tracker/ru/api/queues/get-autoaction
https://yandex.ru/support/tracker/ru/api/queues/view-autoaction-logs
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import TypeAdapter
from yatracker.types.autoaction import (
    Autoaction,
    AutoactionLaunch,
    AutoactionLaunchResult,
)
from yatracker.types.trigger import TriggerAction

from tests.conftest import make_tracker, sent_json

# GET /queues/{id}/autoactions/{id} response shape (get-autoaction.txt).
AUTOACTION: dict[str, Any] = {
    "id": 9,
    "self": "https://api.tracker.yandex.net/v3/queues/DESIGN/autoactions/9",
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/DESIGN",
        "id": "26",
        "key": "DESIGN",
        "display": "Design",
    },
    "name": "autoaction_name",
    "version": 4,
    "active": True,
    "created": "2021-04-15T04:49:44.802+0000",
    "updated": "2022-01-26T16:29:05.356+0000",
    "filter": {"priority": ["critical"]},
    "actions": [
        {
            "type": "Transition",
            "id": 1,
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/2",
                "id": "2",
                "key": "needInfo",
                "display": "Требуется информация",
            },
        },
    ],
    "enableNotifications": False,
    "lastLaunch": "2022-02-01T14:09:48.216+0000",
    "totalIssuesProcessed": 0,
    "intervalMillis": 3600000,
    "calendar": {"id": 2},
}

# POST /queues/{id}/autoactions response shape (create-autoaction.txt): same
# fields except no `lastLaunch` (the autoaction has never run yet).
CREATED_AUTOACTION: dict[str, Any] = {
    k: v for k, v in AUTOACTION.items() if k != "lastLaunch"
}
CREATED_AUTOACTION.update(
    {
        "version": 1,
        "created": "2022-01-21T17:10:22.993+0000",
        "updated": "2022-01-21T17:10:22.993+0000",
        "filter": {"assignee": ["13000000"], "priority": ["critical"]},
    },
)


class TestAutoactionDecoding:
    def test_full_response_decodes(self) -> None:
        autoaction = TypeAdapter(Autoaction).validate_json(json.dumps(AUTOACTION))
        assert autoaction.id == "9"
        assert autoaction.url == (
            "https://api.tracker.yandex.net/v3/queues/DESIGN/autoactions/9"
        )
        assert autoaction.queue.key == "DESIGN"
        assert autoaction.name == "autoaction_name"
        assert autoaction.version == 4
        assert autoaction.active is True
        assert autoaction.created == datetime(
            2021,
            4,
            15,
            4,
            49,
            44,
            802000,
            tzinfo=timezone.utc,
        )
        assert autoaction.updated == datetime(
            2022,
            1,
            26,
            16,
            29,
            5,
            356000,
            tzinfo=timezone.utc,
        )
        assert autoaction.filter_ == {"priority": ["critical"]}
        assert autoaction.query is None
        assert len(autoaction.actions) == 1
        assert autoaction.actions[0].type == "Transition"
        assert autoaction.enable_notifications is False
        assert autoaction.last_launch == datetime(
            2022,
            2,
            1,
            14,
            9,
            48,
            216000,
            tzinfo=timezone.utc,
        )
        assert autoaction.total_issues_processed == 0
        assert autoaction.interval_millis == 3600000
        assert autoaction.calendar is not None
        assert autoaction.calendar.id == "2"

    def test_response_without_last_launch_decodes(self) -> None:
        autoaction = TypeAdapter(Autoaction).validate_json(
            json.dumps(CREATED_AUTOACTION),
        )
        assert autoaction.last_launch is None
        assert autoaction.version == 1


class TestAutoactionEndpoints:
    async def test_get_autoaction_uses_autoaction_path(self) -> None:
        tracker, client = make_tracker(AUTOACTION)
        autoaction = await tracker.get_autoaction("DESIGN", 9)
        assert autoaction.id == "9"
        assert autoaction.name == "autoaction_name"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/DESIGN/autoactions/9")
        assert call["params"] is None

    async def test_create_autoaction_sends_exact_body(self) -> None:
        """Build the create-autoaction doc example.

        `filter_` is sent as `filter`, and `calendar` as a dict.
        """
        tracker, client = make_tracker(CREATED_AUTOACTION, status=200)
        autoaction = await tracker.create_autoaction(
            "DESIGN",
            "AutoactionName",
            actions=[TriggerAction(type="Transition", status={"key": "needInfo"})],
            filter_={"priority": ["critical"], "status": ["inProgress"]},
            calendar={"id": 2},
        )
        assert autoaction.id == "9"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/queues/DESIGN/autoactions")
        assert sent_json(call) == {
            "name": "AutoactionName",
            "filter": {"priority": ["critical"], "status": ["inProgress"]},
            "actions": [{"type": "Transition", "status": {"key": "needInfo"}}],
            "calendar": {"id": 2},
        }

    async def test_create_autoaction_with_query_instead_of_filter(self) -> None:
        tracker, client = make_tracker(CREATED_AUTOACTION)
        await tracker.create_autoaction(
            "DESIGN",
            "AutoactionName",
            actions=[{"type": "Transition", "status": {"key": "needInfo"}}],
            query='"Status": "In progress"',
        )

        call = client.calls[0]
        assert sent_json(call) == {
            "name": "AutoactionName",
            "query": '"Status": "In progress"',
            "actions": [{"type": "Transition", "status": {"key": "needInfo"}}],
        }

    async def test_create_autoaction_sends_optional_fields(self) -> None:
        tracker, client = make_tracker(CREATED_AUTOACTION)
        await tracker.create_autoaction(
            "DESIGN",
            "AutoactionName",
            actions=[{"type": "Transition", "status": {"key": "needInfo"}}],
            filter_={"priority": ["critical"]},
            active=True,
            enable_notifications=False,
            interval_millis=7200000,
        )

        call = client.calls[0]
        assert sent_json(call) == {
            "name": "AutoactionName",
            "filter": {"priority": ["critical"]},
            "actions": [{"type": "Transition", "status": {"key": "needInfo"}}],
            "active": True,
            "enableNotifications": False,
            "intervalMillis": 7200000,
        }

    async def test_create_autoaction_without_filter_and_query_raises(self) -> None:
        tracker, _client = make_tracker(CREATED_AUTOACTION)
        with pytest.raises(ValueError, match=r"filter_.*query"):
            await tracker.create_autoaction(
                "DESIGN",
                "AutoactionName",
                actions=[{"type": "Transition", "status": {"key": "needInfo"}}],
            )

    async def test_get_autoaction_logs_uses_logs_path(self) -> None:
        launch = {
            "id": "6819cc43d8f6f00000000001",
            "launchTime": "2025-05-06T08:45:55.778+0000",
            "searchHits": 3,
            "successes": 3,
            "failures": 0,
            "searchFailed": False,
        }
        tracker, client = make_tracker([launch])
        launches = await tracker.get_autoaction_logs("DESIGN", 9)
        assert len(launches) == 1
        assert launches[0].id == "6819cc43d8f6f00000000001"
        assert launches[0].search_hits == 3
        assert launches[0].successes == 3
        assert launches[0].failures == 0
        assert launches[0].search_failed is False
        assert launches[0].launch_time == datetime(
            2025,
            5,
            6,
            8,
            45,
            55,
            778000,
            tzinfo=timezone.utc,
        )

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/DESIGN/autoactions/9/logs")
        assert call["params"] is None

    async def test_get_autoaction_log_uses_logs_launch_path(self) -> None:
        result = {
            "id": 0,
            "issueReference": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-1",
                "id": "66f682f13f442b0000000001",
                "version": 0,
                "key": "TEST-1",
                "display": "My issue",
            },
            "status": {"value": "success", "display": "Success"},
        }
        tracker, client = make_tracker([result])
        results = await tracker.get_autoaction_log(
            "DESIGN",
            9,
            "6819cc43d8f6f00000000001",
        )
        assert len(results) == 1
        assert results[0].id == 0
        assert results[0].issue_reference is not None
        assert results[0].issue_reference.key == "TEST-1"
        assert results[0].issue_reference.version == 0
        assert results[0].issue_reference.display == "My issue"
        assert results[0].status is not None
        assert results[0].status.value == "success"
        assert results[0].status.display == "Success"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith(
            "/queues/DESIGN/autoactions/9/logs/6819cc43d8f6f00000000001",
        )


class TestAutoactionLaunchDecoding:
    def test_launch_result_decodes_from_view_autoaction_logs_doc(self) -> None:
        payload = {
            "id": 0,
            "issueReference": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-1",
                "id": "66f682f13f442b0000000001",
                "version": 0,
                "key": "TEST-1",
                "display": "My issue",
            },
            "status": {"value": "success", "display": "Success"},
        }
        result = TypeAdapter(AutoactionLaunchResult).validate_json(
            json.dumps(payload),
        )
        assert result.id == 0
        assert result.issue_reference is not None
        assert result.issue_reference.id == "66f682f13f442b0000000001"
        assert result.status is not None
        assert result.status.value == "success"

    def test_launch_decodes_from_view_autoaction_logs_doc(self) -> None:
        payload = {
            "id": "6819cc43d8f6f00000000001",
            "launchTime": "2025-05-06T08:45:55.778+0000",
            "searchHits": 3,
            "successes": 3,
            "failures": 0,
            "searchFailed": False,
        }
        launch = TypeAdapter(AutoactionLaunch).validate_json(json.dumps(payload))
        assert launch.id == "6819cc43d8f6f00000000001"
        assert launch.search_hits == 3
