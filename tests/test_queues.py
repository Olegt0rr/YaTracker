"""Tests for the queues category and the queue-related structs.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/concepts/queues/get-queue
https://yandex.ru/support/tracker/ru/concepts/queues/get-queues
https://yandex.ru/support/tracker/ru/concepts/queues/create-queue
https://yandex.ru/support/tracker/ru/concepts/queues/get-fields
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter
from yatracker import YaTracker
from yatracker.types import FullQueue, QueueField

from tests.conftest import FakeClient

USER = {
    "self": "https://api.tracker.yandex.net/v3/users/1111",
    "id": "1111",
    "display": "Имя Фамилия",
    "cloudUid": "ajeppa7dgp53",
    "passportUid": 1111,
}
ISSUE_TYPE = {
    "self": "https://api.tracker.yandex.net/v3/issuetypes/1",
    "id": "1",
    "key": "task",
    "display": "Задача",
}
PRIORITY = {
    "self": "https://api.tracker.yandex.net/v3/priorities/3",
    "id": "3",
    "key": "normal",
    "display": "Средний",
}

# `GET /queues/{id}` without `expand`: the response carries neither
# `teamUsers`/`issueTypes`/`versions`/`workflows` nor `issueTypesConfig`.
PLAIN_QUEUE: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/queues/TEST",
    "id": "3",
    "key": "TEST",
    "version": 5,
    "name": "Test",
    "lead": USER,
    "assignAuto": False,
    "defaultType": ISSUE_TYPE,
    "defaultPriority": PRIORITY,
    "denyVoting": False,
}

# `GET /queues/{id}?expand=all`.
EXPANDED_QUEUE: dict[str, Any] = {
    **PLAIN_QUEUE,
    "description": "My queue",
    "teamUsers": [USER],
    "issueTypes": [ISSUE_TYPE],
    "versions": [
        {
            "self": "https://api.tracker.yandex.net/v3/versions/4",
            "id": "4",
            "display": "My version",
        },
    ],
    "workflows": {"dev": [ISSUE_TYPE]},
    "issueTypesConfig": [
        {
            "issueType": ISSUE_TYPE,
            "workflow": {
                "self": "https://api.tracker.yandex.net/v3/workflows/dev",
                "id": "dev",
                "display": "dev",
            },
            "resolutions": [
                {
                    "self": "https://api.tracker.yandex.net/v3/resolutions/2",
                    "id": "2",
                    "key": "wontFix",
                    "display": "Won't fix",
                },
            ],
        },
    ],
}

# `POST /queues` 201 response: no `denyVoting`, but `allowExternals` is there.
CREATED_QUEUE: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/queues/DESIGN",
    "id": "111",
    "key": "DESIGN",
    "version": 1400150916068,
    "name": "Design",
    "lead": USER,
    "assignAuto": False,
    "allowExternals": False,
    "defaultType": ISSUE_TYPE,
    "defaultPriority": PRIORITY,
}

QUEUE_FIELD: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/fields/myfield",
    "id": "myfield",
    "name": "My field",
    "version": 1361890459119,
    "schema": {"type": "string", "required": False},
    "readonly": False,
    "options": True,
    "suggest": False,
    "queryProvider": {"type": "StringOptionalQueryProvider"},
    "order": 222,
}


def make_tracker(
    payload: Any = None,
    status: int = 200,
) -> tuple[YaTracker, FakeClient]:
    body = b"{}" if payload is None else json.dumps(payload).encode()
    client = FakeClient(status=status, body=body)
    return YaTracker(client=client), client


def sent_json(call: dict[str, Any]) -> Any:
    """Decode the JSON body attached to a captured request."""
    return json.loads(call["data"]._value)


class TestFullQueueDecoding:
    def test_plain_response_decodes(self) -> None:
        queue = TypeAdapter(FullQueue).validate_json(json.dumps(PLAIN_QUEUE))
        assert queue.id == "3"
        assert queue.key == "TEST"
        assert queue.lead.display == "Имя Фамилия"
        # expand-only fields stay unset instead of blowing up
        assert queue.team_users is None
        assert queue.issue_types is None
        assert queue.versions is None
        assert queue.workflows is None
        assert queue.issue_types_config is None

    def test_expanded_response_decodes_workflows_as_mapping(self) -> None:
        queue = TypeAdapter(FullQueue).validate_json(json.dumps(EXPANDED_QUEUE))
        assert queue.workflows is not None
        assert list(queue.workflows) == ["dev"]
        assert queue.workflows["dev"][0].key == "task"
        assert queue.versions is not None
        assert queue.versions[0].display == "My version"
        assert queue.issue_types_config is not None
        # `issueTypesConfig[].workflow` has no `key`
        assert queue.issue_types_config[0].workflow.key is None

    def test_v2_shaped_response_decodes(self) -> None:
        """`api_version="v2"` responses differ in a few places (see README)."""
        payload: dict[str, Any] = {
            **EXPANDED_QUEUE,
            # v2 sends numeric ids
            "id": 3,
            # v2 sends a plain array of workflows instead of a mapping
            "workflows": [
                {
                    "self": "https://api.tracker.yandex.net/v2/workflows/dev",
                    "id": "dev",
                    "display": "dev",
                },
            ],
            # v2 version refs carry no `display`
            "versions": [
                {"self": "https://api.tracker.yandex.net/v2/versions/4", "id": 4},
            ],
        }
        queue = TypeAdapter(FullQueue).validate_json(json.dumps(payload))

        assert queue.id == "3"
        assert isinstance(queue.workflows, list)
        assert queue.workflows[0].id == "dev"
        assert queue.versions is not None
        assert queue.versions[0].id == "4"
        assert queue.versions[0].display is None

    def test_created_queue_response_decodes(self) -> None:
        queue = TypeAdapter(FullQueue).validate_json(json.dumps(CREATED_QUEUE))
        assert queue.allow_externals is False
        assert queue.deny_voting is None

    def test_queue_field_reads_schema_key(self) -> None:
        field = TypeAdapter(QueueField).validate_json(json.dumps(QUEUE_FIELD))
        assert field.field_schema.type == "string"
        assert field.field_schema.required is False
        assert field.query_provider is not None


class TestQueueEndpoints:
    async def test_get_queue_without_expand(self) -> None:
        tracker, client = make_tracker(PLAIN_QUEUE)
        queue = await tracker.get_queue("TEST")
        assert queue.key == "TEST"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/TEST")
        assert call["params"] is None

    async def test_get_queue_passes_expand(self) -> None:
        tracker, client = make_tracker(EXPANDED_QUEUE)
        queue = await tracker.get_queue("TEST", expand="all")
        assert queue.workflows is not None

        assert client.calls[0]["params"] == {"expand": "all"}

    async def test_get_queues_decodes_list(self) -> None:
        tracker, client = make_tracker([PLAIN_QUEUE])
        queues = await tracker.get_queues(expand="all", per_page=10)
        assert len(queues) == 1

        assert client.calls[0]["params"] == {"expand": "all", "perPage": "10"}

    async def test_restore_queue_uses_post(self) -> None:
        tracker, client = make_tracker(PLAIN_QUEUE)
        await tracker.restore_queue("TEST")

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/queues/TEST/_restore")

    async def test_delete_tag_uses_post_with_body(self) -> None:
        tracker, client = make_tracker()
        assert await tracker.delete_tag_from_queue("TEST", "my-tag") is True

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/queues/TEST/tags/_remove")
        assert sent_json(call) == {"tag": "my-tag"}

    async def test_get_queue_fields_decodes_schema(self) -> None:
        tracker, client = make_tracker([QUEUE_FIELD])
        fields = await tracker.get_queue_fields("TEST")
        assert fields[0].field_schema.type == "string"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/TEST/fields")
