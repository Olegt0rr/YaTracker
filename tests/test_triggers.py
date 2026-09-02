"""Tests for the triggers category and its action/condition models.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/queues/get-triggers
https://yandex.ru/support/tracker/ru/api/queues/get-trigger
https://yandex.ru/support/tracker/ru/api/queues/create-trigger
https://yandex.ru/support/tracker/ru/api/queues/change-trigger
https://yandex.ru/support/tracker/ru/api/queues/change-trigger-actions
https://yandex.ru/support/tracker/ru/api/queues/change-trigger-conditions
https://yandex.ru/support/tracker/ru/api/queues/view-trigger-logs
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, ClassVar

import pytest
from pydantic import TypeAdapter
from yatracker import YaTracker
from yatracker.types.trigger import (
    Trigger,
    TriggerAction,
    TriggerCondition,
    TriggerWebhookLog,
)

from tests.conftest import FakeClient, make_tracker, sent_json

# GET/POST/PATCH trigger response shape (shared by list, get, create and
# update endpoints).
TRIGGER: dict[str, Any] = {
    "id": 16,
    "self": "https://api.tracker.yandex.net/v3/queues/DESIGN/triggers/16",
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/DESIGN",
        "id": "26",
        "key": "DESIGN",
        "display": "Design",
    },
    "name": "trigger_name",
    "order": "0.0002",
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
    "conditions": [
        {
            "type": "Or",
            "conditions": [
                {"type": "Event.comment-create"},
            ],
        },
    ],
    "version": 1,
    "active": True,
}


def _trigger_body(id_: int | str, **overrides: Any) -> dict[str, Any]:
    """Build a minimal `Trigger` payload for pagination tests."""
    trigger: dict[str, Any] = {
        "self": f"https://api.tracker.yandex.net/v3/queues/DESIGN/triggers/{id_}",
        "id": id_,
        "queue": {
            "self": "https://api.tracker.yandex.net/v3/queues/DESIGN",
            "id": "26",
            "key": "DESIGN",
            "display": "Design",
        },
        "name": f"trigger_{id_}",
        "order": "0.0001",
        "version": 1,
        "active": True,
    }
    trigger.update(overrides)
    return trigger


class TestTriggerDecoding:
    def test_full_response_decodes(self) -> None:
        trigger = TypeAdapter(Trigger).validate_json(json.dumps(TRIGGER))
        assert trigger.id == "16"
        assert (
            trigger.url == "https://api.tracker.yandex.net/v3/queues/DESIGN/triggers/16"
        )
        assert trigger.queue.key == "DESIGN"
        assert trigger.name == "trigger_name"
        assert trigger.order == "0.0002"
        assert trigger.version == 1
        assert trigger.active is True

        assert len(trigger.actions) == 1
        action = trigger.actions[0]
        assert action.type == "Transition"
        assert action.id == "1"
        assert action.status.key == "needInfo"  # type: ignore[union-attr]

        assert len(trigger.conditions) == 1
        condition = trigger.conditions[0]
        assert condition.type == "Or"
        assert condition.conditions is not None
        assert condition.conditions[0].type == "Event.comment-create"


class TestTriggerEndpoints:
    async def test_get_triggers_sends_pagination_params(self) -> None:
        tracker, client = make_tracker([TRIGGER])
        triggers = await tracker.get_triggers("DESIGN", per_page=20, id_=15)
        assert len(triggers) == 1
        assert triggers[0].name == "trigger_name"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/DESIGN/triggers")
        assert call["params"] == {"perPage": "20", "id": "15"}

    async def test_get_triggers_without_params_sends_none(self) -> None:
        tracker, client = make_tracker([TRIGGER])
        await tracker.get_triggers("DESIGN")

        assert client.calls[0]["params"] is None

    async def test_get_trigger_uses_trigger_path(self) -> None:
        tracker, client = make_tracker(TRIGGER)
        trigger = await tracker.get_trigger("DESIGN", 16)
        assert trigger.id == "16"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/DESIGN/triggers/16")

    async def test_create_trigger_sends_exact_body_with_models(self) -> None:
        """Build the create-trigger doc example from model instances.

        Their snake_case attrs (`checklist_items`, ...) get camelCased.
        """
        tracker, client = make_tracker(TRIGGER, status=200)
        trigger = await tracker.create_trigger(
            "DESIGN",
            "TriggerName",
            actions=[TriggerAction(type="Transition", status={"key": "open"})],
            conditions=[
                TriggerCondition(type="CommentFullyMatchCondition", word="Open"),
            ],
        )
        assert trigger.id == "16"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/queues/DESIGN/triggers")
        assert sent_json(call) == {
            "name": "TriggerName",
            "actions": [{"type": "Transition", "status": {"key": "open"}}],
            "conditions": [{"type": "CommentFullyMatchCondition", "word": "Open"}],
        }

    async def test_create_trigger_sends_exact_body_with_dicts(self) -> None:
        """Same doc example, passed as raw dicts (already in wire format)."""
        tracker, client = make_tracker(TRIGGER, status=200)
        await tracker.create_trigger(
            "DESIGN",
            "TriggerName",
            actions=[{"type": "Transition", "status": {"key": "open"}}],
            conditions=[{"type": "CommentFullyMatchCondition", "word": "Open"}],
        )

        call = client.calls[0]
        assert sent_json(call) == {
            "name": "TriggerName",
            "actions": [{"type": "Transition", "status": {"key": "open"}}],
            "conditions": [{"type": "CommentFullyMatchCondition", "word": "Open"}],
        }

    async def test_create_trigger_omits_none_fields(self) -> None:
        tracker, client = make_tracker(TRIGGER)
        await tracker.create_trigger(
            "DESIGN",
            "TriggerName",
            actions=[{"type": "Transition", "status": "open"}],
        )

        call = client.calls[0]
        assert sent_json(call) == {
            "name": "TriggerName",
            "actions": [{"type": "Transition", "status": "open"}],
        }

    async def test_update_trigger_sends_version_query_param(self) -> None:
        tracker, client = make_tracker(TRIGGER)
        trigger = await tracker.update_trigger(
            "DESIGN",
            16,
            1,
            actions=[{"type": "Transition", "status": {"key": "needInfo"}}],
            conditions=[
                {
                    "type": "Or",
                    "conditions": [
                        {
                            "type": "CommentFullyMatchCondition",
                            "word": "Need info",
                        },
                        {
                            "type": "CommentFullyMatchCondition",
                            "word": "Нужна информация",
                        },
                    ],
                },
            ],
        )
        assert trigger.id == "16"

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/queues/DESIGN/triggers/16")
        assert call["params"] == {"version": "1"}
        assert sent_json(call) == {
            "actions": [{"type": "Transition", "status": {"key": "needInfo"}}],
            "conditions": [
                {
                    "type": "Or",
                    "conditions": [
                        {
                            "type": "CommentFullyMatchCondition",
                            "word": "Need info",
                        },
                        {
                            "type": "CommentFullyMatchCondition",
                            "word": "Нужна информация",
                        },
                    ],
                },
            ],
        }

    async def test_update_trigger_create_checklist_action_via_model(self) -> None:
        """Build change-trigger example 2 from a `TriggerAction` model.

        `checklist_items` gets camelCased to `checklistItems`.
        """
        tracker, client = make_tracker(TRIGGER)
        await tracker.update_trigger(
            "DESIGN",
            16,
            2,
            actions=[
                TriggerAction(
                    type="CreateChecklist",
                    checklist_items=[
                        {
                            "text": "Сделать то",
                            "assignee": "username",
                            "deadline": {"date": "2025-05-23"},
                        },
                        {
                            "text": "Сделать это",
                            "assignee": "username",
                            "deadline": {"date": "2025-05-23"},
                        },
                        {"text": "Отчитаться за все"},
                    ],
                ),
            ],
        )

        call = client.calls[0]
        assert call["params"] == {"version": "2"}
        assert sent_json(call) == {
            "actions": [
                {
                    "type": "CreateChecklist",
                    "checklistItems": [
                        {
                            "text": "Сделать то",
                            "assignee": "username",
                            "deadline": {"date": "2025-05-23"},
                        },
                        {
                            "text": "Сделать это",
                            "assignee": "username",
                            "deadline": {"date": "2025-05-23"},
                        },
                        {"text": "Отчитаться за все"},
                    ],
                },
            ],
        }

    async def test_update_trigger_deactivate_sends_only_active(self) -> None:
        tracker, client = make_tracker(TRIGGER)
        await tracker.update_trigger("DESIGN", 16, 4, active=False)

        call = client.calls[0]
        assert call["params"] == {"version": "4"}
        assert sent_json(call) == {"active": False}

    async def test_update_trigger_move_and_activate(self) -> None:
        tracker, client = make_tracker(TRIGGER)
        await tracker.update_trigger("DESIGN", 16, 4, before=6, active=True)

        call = client.calls[0]
        assert call["params"] == {"version": "4"}
        assert sent_json(call) == {"before": 6, "active": True}

    async def test_update_trigger_omits_none_fields(self) -> None:
        tracker, client = make_tracker(TRIGGER)
        await tracker.update_trigger("DESIGN", 16, 1, name="Renamed")

        call = client.calls[0]
        assert sent_json(call) == {"name": "Renamed"}


class TestIterTriggers:
    async def test_iterates_multiple_pages_with_cursor_dedup(self) -> None:
        page1 = json.dumps(
            [_trigger_body(1), _trigger_body(2), _trigger_body(3)],
        ).encode()
        # The docs describe `id` as the trigger the next page *starts
        # from*, so the server is expected to repeat the cursor trigger
        # at the top of the next page.
        page2 = json.dumps(
            [_trigger_body(3), _trigger_body(4), _trigger_body(5)],
        ).encode()
        page3 = b"[]"

        client = FakeClient(
            responses=[(200, page1, {}), (200, page2, {}), (200, page3, {})],
        )
        tracker = YaTracker(client=client)

        triggers = [t async for t in tracker.iter_triggers("DESIGN", per_page=3)]
        assert [t.id for t in triggers] == ["1", "2", "3", "4", "5"]
        assert len(client.calls) == 3

        assert client.calls[0]["params"] == {"perPage": "3"}
        assert client.calls[1]["params"] == {"perPage": "3", "id": "3"}
        assert client.calls[2]["params"] == {"perPage": "3", "id": "5"}

    async def test_stops_on_empty_page(self) -> None:
        page1 = json.dumps([_trigger_body(1)]).encode()
        page2 = b"[]"

        client = FakeClient(responses=[(200, page1, {}), (200, page2, {})])
        tracker = YaTracker(client=client)

        triggers = [t async for t in tracker.iter_triggers("DESIGN")]
        assert [t.id for t in triggers] == ["1"]
        assert len(client.calls) == 2

    async def test_stops_when_page_does_not_advance_past_cursor(self) -> None:
        """A page whose last id equals the cursor is treated as the last one.

        This also covers a server ignoring `id`: iteration stops instead
        of looping forever, and nothing from that page is yielded again.
        """
        page1 = json.dumps([_trigger_body(1), _trigger_body(3)]).encode()
        page2 = json.dumps([_trigger_body(3)]).encode()

        client = FakeClient(responses=[(200, page1, {}), (200, page2, {})])
        tracker = YaTracker(client=client)

        triggers = [t async for t in tracker.iter_triggers("DESIGN")]
        assert [t.id for t in triggers] == ["1", "3"]
        assert len(client.calls) == 2

    async def test_empty_first_page_yields_nothing(self) -> None:
        tracker, client = make_tracker(payload=[])

        triggers = [t async for t in tracker.iter_triggers("DESIGN")]
        assert triggers == []
        assert len(client.calls) == 1


class TestGetTriggerLogs:
    LOG_ENTRY: ClassVar[dict[str, Any]] = {
        "startTime": "2025-02-25T14:22:03.596+0000",
        "endTime": "2025-02-25T14:22:03.831+0000",
        "duration": 235,
        "triggerId": 123,
        "actionId": 1,
        "issueId": "66f682f13f442b0000000001",
        "request": {
            "method": "POST",
            "endpoint": "https://api.telegram.org/bot123/sendMessage",
            "headers": {
                "X-Startrek-Transport": "vNCc/aRh5",
                "Content-Type": "application/json",
            },
            "body": '{\n"chat_id":"-4116","parse_mode":"markdown","text":"Привет!"\n}',
            "webhookAuthContext": {"type": "noauth"},
        },
        "response": {
            "headers": {"Content-Type": "XXX"},
            "statusCode": 200,
        },
        "id": "67bdd20b604a9c0000000001",
    }

    def test_log_entry_decodes(self) -> None:
        log = TypeAdapter(TriggerWebhookLog).validate_json(json.dumps(self.LOG_ENTRY))
        assert log.id == "67bdd20b604a9c0000000001"
        assert log.trigger_id == "123"
        assert log.action_id == "1"
        assert log.issue_id == "66f682f13f442b0000000001"
        assert log.duration == 235
        assert log.start_time == datetime(
            2025,
            2,
            25,
            14,
            22,
            3,
            596000,
            tzinfo=timezone.utc,
        )
        assert log.request is not None
        assert log.request.method == "POST"
        assert log.request.webhook_auth_context == {"type": "noauth"}
        assert log.response is not None
        assert log.response.status_code == 200

    async def test_sends_issue_id_and_limit_params(self) -> None:
        tracker, client = make_tracker([self.LOG_ENTRY])
        logs = await tracker.get_trigger_logs(
            "DEV",
            6,
            issue_id="DEV-123",
            limit=100,
        )
        assert len(logs) == 1

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/DEV/triggers/6/webhooks/log")
        assert call["params"] == {"issueId": "DEV-123", "limit": "100"}

    async def test_renders_datetime_from_and_to_via_isoformat(self) -> None:
        # Naive on purpose: the doc's `from`/`to` example carries no UTC
        # offset (`YYYY-MM-DDThh:mm:ss`), unlike `startTime`/`endTime`.
        tracker, client = make_tracker([self.LOG_ENTRY])
        await tracker.get_trigger_logs(
            "DEV",
            6,
            from_=datetime(2025, 9, 23, 0, 0, 0),  # noqa: DTZ001
            to=datetime(2025, 9, 23, 23, 59, 59),  # noqa: DTZ001
        )

        call = client.calls[0]
        assert call["params"] == {
            "from": "2025-09-23T00:00:00",
            "to": "2025-09-23T23:59:59",
        }

    async def test_passes_string_from_and_to_through_untouched(self) -> None:
        tracker, client = make_tracker([self.LOG_ENTRY])
        await tracker.get_trigger_logs(
            "DEV",
            6,
            from_="2025-09-23T00:00:00",
            to="2025-09-23T23:59:59",
        )

        call = client.calls[0]
        assert call["params"] == {
            "from": "2025-09-23T00:00:00",
            "to": "2025-09-23T23:59:59",
        }

    async def test_without_params_sends_none(self) -> None:
        tracker, client = make_tracker([self.LOG_ENTRY])
        await tracker.get_trigger_logs("DEV", 6)

        assert client.calls[0]["params"] is None


# ---------------------------------------------------------------------------
# Every documented action/condition example round-trips through the models
# to exactly the doc JSON.
# ---------------------------------------------------------------------------

ACTION_EXAMPLES: list[dict[str, Any]] = [
    # Изменить статус задачи
    {"type": "Transition", "status": "В работе"},
    # Вычислить значение
    {"type": "CalculateFormula", "formula": "now()+3M", "resultField": "start"},
    # Изменить значения в полях (incl. `update: {"resolution": null}`)
    {
        "type": "Update",
        "update": {
            "description": "Новая задача",
            "tags": {"add": "Новый тег"},
            "resolution": None,
        },
    },
    # Переместить задачу
    {"type": "Move", "queue": "TESTQUEUE"},
    # Добавить комментарий
    {
        "type": "CreateComment",
        "text": "Обращение создано {{currentDateTime.date}}",
        "fromRobot": False,
    },
    # Создать чеклист
    {
        "type": "CreateChecklist",
        "checklistItems": [
            {
                "text": "Сделать то",
                "assignee": "username",
                "deadline": {"date": "2025-05-23"},
            },
            {
                "text": "Сделать это",
                "assignee": "username",
                "deadline": {"date": "2025-05-23"},
            },
            {"text": "Отчитаться за все"},
        ],
    },
    # HTTP-запрос
    {
        "type": "Webhook",
        "endpoint": "https://api.example.com/messenger/sendMessage",
        "method": "GET",
        "contentType": "application/json; charset=UTF-8",
        "headers": {"Content-Language": "ru-RU"},
        "authContext": {"password": "********", "type": "basic", "login": "user1"},
        "body": {"message": "Успех"},
    },
    # Создать задачу
    {
        "type": "CreateIssue",
        "queue": "TESTQUEUE",
        "summary": "Новая задача",
        "fieldTemplates": {
            "followers": ["user1", "user2"],
            "assignee": "user3",
            "dueDate": "2024-10-31",
            "description": "Создана триггером {{currentDateTime.date}}",
            "priority": "critical",
            "type": "milestone",
            "tags": ["new task", "by trigger"],
        },
        "fromRobot": True,
    },
]


@pytest.mark.parametrize("example", ACTION_EXAMPLES, ids=lambda e: e["type"])
def test_trigger_action_round_trips_doc_example(example: dict[str, Any]) -> None:
    action = TypeAdapter(TriggerAction).validate_json(json.dumps(example))
    assert action.model_dump(mode="json", by_alias=True, exclude_none=True) == example


CONDITION_EXAMPLES: list[dict[str, Any]] = [
    {"type": "Event.update"},
    {"type": "ChecklistDone"},
    {
        "type": "CommentNoneMatchCondition",
        "words": ["Version 0.1", "Version 0.2"],
        "ignoreCase": True,
        "removeMarkup": True,
        "noMatchBefore": False,
    },
    {"type": "CommentAuthorNot", "user": "user1"},
    {"type": "CommentMessageInternal"},
    {"type": "CommentMessageExternal"},
    {
        "type": "RemovedLinkCondition",
        "relationship": ["is parent task for", "is epic of"],
    },
    {"type": "FieldChangedCondition", "field": "priority"},
    {"type": "FieldEquals", "field": "priority", "value": "blocker"},
    {"type": "FieldBecameEqual", "field": "priority", "value": "blocker"},
    {"type": "FieldIsNotEmpty", "field": "assignee"},
    {"type": "FieldIsEmpty", "field": "assignee"},
    {"type": "FieldBecameEmpty", "field": "assignee"},
    {"type": "FieldBecameNotEmpty", "field": "assignee"},
    {
        "type": "DateGreaterCondition",
        "field": "createdAt",
        "value": "2023-10-28T09:25:00",
    },
    {
        "type": "DateLessOrEqualCondition",
        "field": "end",
        "value": "2023-10-28T09:25:00",
    },
    {"type": "UserInGroups", "field": "createdBy", "value": "1"},
    {"type": "UserNotInGroups", "field": "createdBy", "value": ["1", "4"]},
    {
        "type": "Container.SizeGreaterOrEquals",
        "field": "votedBy",
        "value": 5,
    },
    {"type": "Container.SizeEquals", "field": "components", "value": 5},
    {
        "type": "ContainerContainsAll",
        "field": "followers",
        "value": ["user11", "user22"],
        "noMatchBefore": True,
    },
    {"type": "LessOrEqualCondition", "field": "storyPoints", "value": 5},
    {"type": "BecameGreaterCondition", "field": "votes", "value": 6},
    {
        "type": "ContainsNoneOfStrings",
        "field": "description",
        "value": ["Test task", "12345"],
        "ignoreCase": True,
    },
    {
        "type": "FieldEqualsString",
        "field": "summary",
        "value": "New-Task",
        "ignoreCase": False,
    },
    # A logical group nesting elementary conditions (get-triggers response).
    {
        "type": "Or",
        "conditions": [{"type": "Event.comment-create"}],
    },
    # A group nesting another group (change-trigger example 3).
    {
        "type": "Or",
        "conditions": [
            {
                "type": "And",
                "conditions": [
                    {
                        "ignoreCase": False,
                        "noMatchBefore": False,
                        "removeMarkup": False,
                        "type": "CommentFullyMatchCondition",
                        "word": "Need info",
                    },
                    {
                        "type": "FieldEquals",
                        "field": "status",
                        "value": "inProgress",
                    },
                ],
            },
            {
                "ignoreCase": False,
                "noMatchBefore": False,
                "removeMarkup": False,
                "type": "CommentFullyMatchCondition",
                "word": "No data",
            },
        ],
    },
]


@pytest.mark.parametrize("example", CONDITION_EXAMPLES, ids=lambda e: e["type"])
def test_trigger_condition_round_trips_doc_example(example: dict[str, Any]) -> None:
    condition = TypeAdapter(TriggerCondition).validate_json(json.dumps(example))
    dumped = condition.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped == example
