"""Tests for the macros category and the `Macro` / `FieldRef` structs.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/get-macroses
https://yandex.ru/support/tracker/ru/get-macros
https://yandex.ru/support/tracker/ru/post-macros
https://yandex.ru/support/tracker/ru/patch-macros
https://yandex.ru/support/tracker/ru/delete-macros
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter
from yatracker.types import Macro

from tests.conftest import make_tracker, sent_json

# `GET /queues/{id}/macros/{id}` (and list item) response, verbatim from the
# docs. `id` is a Number in the API; `Base` coerces it to a string, same as
# `Component`. `issueUpdate` in RESPONSES is a list of
# `{field: {self, id, display}, update: {<operator>: value}}` objects — the
# opposite shape from the request body (see `MACRO_REQUEST` below).
MACRO: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/queues/TEST/macros/3",
    "id": 3,
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/TEST",
        "id": "1",
        "key": "TEST",
        "display": "My queue",
    },
    "name": "My macro",
    "body": (
        "Test comment\n{{currentUser}}{{currentDateTime.date}}"
        "{{currentDateTime}}\n{{issue.author}}"
    ),
    "issueUpdate": [
        {
            "field": {
                "self": "https://api.tracker.yandex.net/v3/fields/tags",
                "id": "tags",
                "display": "Теги",
            },
            "update": {"add": ["tag 1", "tag 2"]},
        },
    ],
}

# `body`/`issueUpdate` are optional in responses (e.g. a macro created
# without either).
MACRO_WITHOUT_OPTIONALS: dict[str, Any] = {
    k: v for k, v in MACRO.items() if k not in {"body", "issueUpdate"}
}


class TestMacroDecoding:
    def test_full_response_decodes(self) -> None:
        macro = TypeAdapter(Macro).validate_json(json.dumps(MACRO))
        assert macro.url.endswith("/queues/TEST/macros/3")
        # the API sends a number, `Base` coerces it to a string
        assert macro.id == "3"
        assert macro.queue.key == "TEST"
        assert macro.name == "My macro"
        assert macro.body == MACRO["body"]
        assert len(macro.issue_update) == 1
        assert macro.issue_update[0].field.id == "tags"
        assert macro.issue_update[0].update == {"add": ["tag 1", "tag 2"]}

    def test_response_without_optionals_decodes(self) -> None:
        macro = TypeAdapter(Macro).validate_json(json.dumps(MACRO_WITHOUT_OPTIONALS))
        assert macro.body is None
        assert macro.issue_update == []


class TestMacroEndpoints:
    async def test_get_macros_decodes_list(self) -> None:
        tracker, client = make_tracker([MACRO])
        # queue id given as int
        macros = await tracker.get_macros(1)
        assert len(macros) == 1
        assert macros[0].name == "My macro"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/1/macros")
        assert call["params"] is None

    async def test_get_macro(self) -> None:
        tracker, client = make_tracker(MACRO)
        # queue id given as str, macro id given as int
        macro = await tracker.get_macro("TEST", 3)
        assert macro.id == "3"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/TEST/macros/3")
        assert call["params"] is None

    async def test_create_macro_sends_name_only(self) -> None:
        tracker, client = make_tracker(MACRO, status=201)
        macro = await tracker.create_macro("TEST", "Test macro")
        assert macro.name == "My macro"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/queues/TEST/macros")
        assert call["params"] is None
        # `queue_id` doesn't leak into the body, and `None` fields are
        # omitted
        assert sent_json(call) == {"name": "Test macro"}

    async def test_create_macro_sends_body_and_issue_update(self) -> None:
        tracker, client = make_tracker(MACRO, status=201)
        await tracker.create_macro(
            "TEST",
            "Test macro",
            body="Test comment\n{{currentDateTime}}\n{{issue.author}}",
            issue_update={
                "description": "New task",
                "tags": {"add": "New tag"},
                "resolution": None,
            },
        )

        # `BaseTracker._prepare_payload` drops only *top-level* `None`
        # kwargs; `_convert_value` keeps `None` nested inside dicts, so the
        # `resolution: None` entry must survive on the wire as JSON `null`
        # (it clears the field) rather than being dropped.
        assert sent_json(client.calls[0]) == {
            "name": "Test macro",
            "body": "Test comment\n{{currentDateTime}}\n{{issue.author}}",
            "issueUpdate": {
                "description": "New task",
                "tags": {"add": "New tag"},
                "resolution": None,
            },
        }

    async def test_update_macro_excludes_ids_from_body(self) -> None:
        tracker, client = make_tracker(MACRO)
        # queue id given as str, macro id given as str
        macro = await tracker.update_macro("TEST", "3", "My macro")
        assert macro.id == "3"

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/queues/TEST/macros/3")
        assert call["params"] is None
        # neither `queue_id` nor `macro_id` leak into the body
        assert sent_json(call) == {"name": "My macro"}

    async def test_update_macro_sends_unset_body_verbatim(self) -> None:
        tracker, client = make_tracker(MACRO)
        await tracker.update_macro("TEST", "3", "My macro", body={"unset": 1})

        assert sent_json(client.calls[0]) == {
            "name": "My macro",
            "body": {"unset": 1},
        }

    async def test_delete_macro_returns_true(self) -> None:
        # a `DELETE` responds with 204 and an empty body
        tracker, client = make_tracker(status=204)
        client.body = b""
        # queue id given as str, macro id given as int
        assert await tracker.delete_macro("TEST", 3) is True

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/queues/TEST/macros/3")
        # no request body is sent at all (so `queue_id`/`macro_id` can't
        # leak into one)
        assert call["data"] is None
