"""Tests for the applications/external links categories.

Also covers the `Application`/`RemoteLink`/`RemoteLinkObject` structs.
Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/issues/get-applications
https://yandex.ru/support/tracker/ru/api/issues/get-external-links
https://yandex.ru/support/tracker/ru/api/issues/add-external-link
https://yandex.ru/support/tracker/ru/api/issues/delete-external-link
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter
from yatracker import YaTracker
from yatracker.types import Application, LinkDirection, RemoteLink

from tests.conftest import FakeClient, make_tracker, sent_json

# `GET /applications` list item.
APPLICATION: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/applications/my-application",
    "id": "my-application",
    "type": "my-application",
    "name": "Application name",
}

# `GET /issues/{issue_id}/remotelinks` list item; also the shape returned
# by `POST /issues/{issue_id}/remotelinks`.
REMOTE_LINK: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issues/TEST-1/remotelinks/51000001",
    "id": 51000001,
    "type": {
        "self": "https://api.tracker.yandex.net/v3/linktypes/relates",
        "id": "relates",
        "inward": "Связана",
        "outward": "Связана",
    },
    "direction": "outward",
    "object": {
        "self": (
            "https://api.tracker.yandex.net/v3/applications/"
            "ru.yandex.bitbucket/objects/1357001000000001"
        ),
        "id": "1357001000000001",
        "key": "TEST-17",
        "application": {
            "self": "https://api.tracker.yandex.net/v3/applications/2581100000000001",
            "id": "2581100000000001",
            "type": "app",
            "name": "test-app",
        },
    },
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "createdAt": "2021-07-14T18:59:54.552+0000",
    "updatedAt": "2021-07-14T18:59:54.552+0000",
}


class TestApplicationDecoding:
    def test_full_response_decodes(self) -> None:
        application = TypeAdapter(Application).validate_json(
            json.dumps(APPLICATION),
        )
        assert application.url.endswith("/applications/my-application")
        assert application.id == "my-application"
        assert application.type == "my-application"
        assert application.name == "Application name"


class TestRemoteLinkDecoding:
    def test_full_response_decodes(self) -> None:
        link = TypeAdapter(RemoteLink).validate_json(json.dumps(REMOTE_LINK))
        assert link.url.endswith("/remotelinks/51000001")
        # the API sends a number for `id`, and unlike string fields
        # `Base` does not coerce it: the field itself is typed `int`
        assert link.id == 51000001
        assert link.type.id == "relates"
        assert link.direction == LinkDirection.OUTWARD
        assert link.object.key == "TEST-17"
        assert link.object.application.name == "test-app"
        assert link.created_by.id == "1111"
        assert link.updated_by is not None
        assert link.updated_by.id == "1111"
        assert link.created_at.tzinfo is not None
        assert link.updated_at is not None
        assert link.updated_at.tzinfo is not None
        # OUTWARD direction -> `.name` reads `type.outward`
        assert link.name == link.type.outward

    def test_inward_direction_uses_type_inward_for_name(self) -> None:
        payload = {**REMOTE_LINK, "direction": "inward"}
        link = TypeAdapter(RemoteLink).validate_json(json.dumps(payload))
        assert link.direction == LinkDirection.INWARD
        assert link.name == link.type.inward

    def test_decodes_without_updated_by_and_updated_at(self) -> None:
        payload = {
            k: v for k, v in REMOTE_LINK.items() if k not in {"updatedBy", "updatedAt"}
        }
        link = TypeAdapter(RemoteLink).validate_json(json.dumps(payload))
        assert link.updated_by is None
        assert link.updated_at is None
        # required fields are unaffected
        assert link.created_by.id == "1111"
        assert link.object.key == "TEST-17"


class TestApplicationsEndpoints:
    async def test_get_applications_decodes_list(self) -> None:
        tracker, client = make_tracker([APPLICATION])
        applications = await tracker.get_applications()
        assert len(applications) == 1
        assert applications[0].name == "Application name"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/applications")


class TestExternalLinksEndpoints:
    async def test_get_remote_links_decodes_list(self) -> None:
        tracker, client = make_tracker([REMOTE_LINK])
        links = await tracker.get_remote_links("TEST-1")
        assert len(links) == 1
        assert links[0].object.key == "TEST-17"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/issues/TEST-1/remotelinks")

    async def test_add_remote_link_sends_body_without_backlink(self) -> None:
        tracker, client = make_tracker(REMOTE_LINK)
        link = await tracker.add_remote_link(
            "TEST-1",
            key="TEST-17",
            origin="ru.yandex.bitbucket",
        )
        assert link.object.key == "TEST-17"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/issues/TEST-1/remotelinks")
        # `backlink` not passed -> no query params at all
        assert call["params"] is None
        assert sent_json(call) == {
            "key": "TEST-17",
            "origin": "ru.yandex.bitbucket",
            "relationship": "RELATES",
        }

    async def test_add_remote_link_sends_custom_relationship_verbatim(self) -> None:
        tracker, client = make_tracker(REMOTE_LINK)
        await tracker.add_remote_link(
            "TEST-1",
            key="TEST-17",
            origin="ru.yandex.bitbucket",
            relationship="DUPLICATES",
        )

        assert sent_json(client.calls[0]) == {
            "key": "TEST-17",
            "origin": "ru.yandex.bitbucket",
            "relationship": "DUPLICATES",
        }

    async def test_add_remote_link_backlink_true_sets_query_param(self) -> None:
        tracker, client = make_tracker(REMOTE_LINK)
        await tracker.add_remote_link(
            "TEST-1",
            key="TEST-17",
            origin="ru.yandex.bitbucket",
            backlink=True,
        )

        call = client.calls[0]
        assert call["params"] == {"backlink": "true"}
        # `backlink` is a query param only, never part of the body
        assert "backlink" not in sent_json(call)

    async def test_add_remote_link_backlink_false_sets_query_param(self) -> None:
        tracker, client = make_tracker(REMOTE_LINK)
        await tracker.add_remote_link(
            "TEST-1",
            key="TEST-17",
            origin="ru.yandex.bitbucket",
            backlink=False,
        )

        call = client.calls[0]
        assert call["params"] == {"backlink": "false"}
        assert "backlink" not in sent_json(call)

    async def test_delete_remote_link(self) -> None:
        client = FakeClient(body=b"")
        tracker = YaTracker(client=client)
        assert await tracker.delete_remote_link("TEST-1", 51000001) is True

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/issues/TEST-1/remotelinks/51000001")
