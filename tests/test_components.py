"""Tests for the components category and the `Component` struct.

Payloads are taken from the official documentation:
https://yandex.cloud/ru/docs/tracker/get-components
https://yandex.cloud/ru/docs/tracker/post-component
https://yandex.cloud/ru/docs/tracker/patch-component
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter
from yatracker.types import Component, FullIssue, FullQueue

from tests.conftest import (
    USER,
    full_issue_body,
    full_queue_body,
    make_tracker,
    sent_json,
)

# `GET /components` list item: carries `description` and `lead`.
COMPONENT: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/components/1",
    "id": 1,
    "version": 3,
    "name": "Test",
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/ORG",
        "id": "1",
        "key": "ORG",
        "display": "My queue",
    },
    "description": "My component",
    "lead": USER,
    "assignAuto": False,
}

# `POST /components` 201 response: no `description`, no `lead`.
CREATED_COMPONENT: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/components/111175",
    "id": 111175,
    "version": 1,
    "name": "Component",
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/TEST",
        "id": "12345",
        "key": "TEST",
        "display": "My queue",
    },
    "assignAuto": False,
}

# Short reference embedded into queue (`expand=components`) and issue payloads.
COMPONENT_REF: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/components/1",
    "id": 1,
    "display": "Test",
}

# `PATCH /components/{id}` 200 response: the version is bumped.
UPDATED_COMPONENT: dict[str, Any] = {**CREATED_COMPONENT, "version": 2}


class TestComponentDecoding:
    def test_full_response_decodes(self) -> None:
        component = TypeAdapter(Component).validate_json(json.dumps(COMPONENT))
        assert component.url.endswith("/components/1")
        # the API sends a number, `Base` coerces it to a string
        assert component.id == "1"
        assert component.version == 3
        assert component.name == "Test"
        assert component.queue.key == "ORG"
        assert component.description == "My component"
        assert component.lead is not None
        assert component.lead.display == "Имя Фамилия"
        assert component.assign_auto is False

    def test_created_response_decodes_without_optionals(self) -> None:
        component = TypeAdapter(Component).validate_json(
            json.dumps(CREATED_COMPONENT),
        )
        assert component.id == "111175"
        assert component.version == 1
        assert component.description is None
        assert component.lead is None
        assert component.assign_auto is False

    def test_missing_assign_auto_decodes_as_none(self) -> None:
        payload = {k: v for k, v in CREATED_COMPONENT.items() if k != "assignAuto"}
        component = TypeAdapter(Component).validate_json(json.dumps(payload))
        assert component.assign_auto is None

    def test_queue_expand_components_decodes_refs(self) -> None:
        """`GET /queues/{id}?expand=components` embeds short references."""
        queue = full_queue_body(components=[COMPONENT_REF])
        decoded = TypeAdapter(FullQueue).validate_json(json.dumps(queue))
        assert decoded.components is not None
        assert decoded.components[0].id == "1"
        assert decoded.components[0].display == "Test"

    def test_issue_components_decode_refs(self) -> None:
        issue = TypeAdapter(FullIssue).validate_json(
            full_issue_body(components=[COMPONENT_REF]),
        )
        assert issue.components is not None
        assert issue.components[0].url.endswith("/components/1")
        assert issue.components[0].display == "Test"


class TestComponentEndpoints:
    async def test_get_components_decodes_list(self) -> None:
        tracker, client = make_tracker([COMPONENT])
        components = await tracker.get_components()
        assert len(components) == 1
        assert components[0].name == "Test"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/components")
        assert call["params"] is None

    async def test_get_components_passes_pagination(self) -> None:
        tracker, client = make_tracker([COMPONENT])
        await tracker.get_components(per_page=100, page=2)

        assert client.calls[0]["params"] == {"perPage": "100", "page": "2"}

    async def test_get_queue_components_uses_queue_path(self) -> None:
        tracker, client = make_tracker([COMPONENT])
        components = await tracker.get_queue_components("ORG")
        assert components[0].queue.key == "ORG"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/ORG/components")

    async def test_create_component_sends_camel_case_body(self) -> None:
        tracker, client = make_tracker(CREATED_COMPONENT)
        component = await tracker.create_component(
            "Component",
            "TEST",
            assign_auto=True,
        )
        assert component.id == "111175"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/components")
        assert call["params"] is None
        # `queue` is the queue key; `None` fields are omitted
        assert sent_json(call) == {
            "name": "Component",
            "queue": "TEST",
            "assignAuto": True,
        }

    async def test_create_component_sends_optional_fields(self) -> None:
        tracker, client = make_tracker(CREATED_COMPONENT)
        await tracker.create_component(
            "Component",
            "TEST",
            description="My component",
            lead="artem",
        )

        assert sent_json(client.calls[0]) == {
            "name": "Component",
            "queue": "TEST",
            "description": "My component",
            "lead": "artem",
        }

    async def test_update_component_passes_version_param(self) -> None:
        tracker, client = make_tracker(UPDATED_COMPONENT)
        component = await tracker.update_component(111175, 1, name="Component")
        assert component.version == 2

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/components/111175")
        assert call["params"] == {"version": "1"}
        # neither `component_id` nor `version` leak into the body
        assert sent_json(call) == {"name": "Component"}

    async def test_update_component_keeps_false_assign_auto(self) -> None:
        tracker, client = make_tracker(UPDATED_COMPONENT)
        await tracker.update_component(
            "111175",
            "1",
            description="My component",
            lead="artem",
            assign_auto=False,
        )

        assert sent_json(client.calls[0]) == {
            "description": "My component",
            "lead": "artem",
            "assignAuto": False,
        }
