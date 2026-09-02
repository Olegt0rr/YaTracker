"""Tests for the entity attachments API (projects, portfolios and goals).

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/entities/attachments/add-attachment
https://yandex.ru/support/tracker/ru/api/entities/attachments/delete-attachment
https://yandex.ru/support/tracker/ru/api/entities/attachments/get-all-attachments
https://yandex.ru/support/tracker/ru/api/entities/attachments/get-attachment
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from yatracker.types.attachment import Attachment
from yatracker.types.entity import Entity

from tests.conftest import USER, make_tracker

# --- payload builders --------------------------------------------------------


def attachment_payload(**overrides: Any) -> dict[str, Any]:
    """Build the `get-attachment`/`get-all-attachments` response shape."""
    payload: dict[str, Any] = {
        "self": "https://api.tracker.yandex.net/v3/attachments/5",
        "id": "5",
        "name": "flowers.jpg",
        "content": "api.tracker.yandex.net/v3/attachments/5/flowers.jpg",
        "createdBy": USER,
        "createdAt": "2024-01-11T06:24:57.635+0000",
        "mimetype": "image/jpeg",
        "size": 20466,
        "metadata": {"size": "236x295"},
    }
    payload.update(overrides)
    return payload


CSV_ATTACHMENT: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/attachments/3",
    "id": "3",
    "name": "Shops.csv",
    "content": "api.tracker.yandex.net/v3/attachments/3/Shops.csv",
    "createdBy": USER,
    "createdAt": "2023-12-25T07:21:36.722+0000",
    "mimetype": "text/csv",
    "size": 559,
}


def entity_with_attachment_payload(**overrides: Any) -> dict[str, Any]:
    """Build the `add-attachment` response shape: an `Entity` with attachments."""
    payload: dict[str, Any] = {
        "self": "https://api.tracker.yandex.net/v3/entities/project/6586d6fee2b9ef74",
        "id": "6586d6fee2b9ef74",
        "version": 78,
        "shortId": 4,
        "entityType": "project",
        "createdBy": USER,
        "createdAt": "2023-12-23T12:47:58.405+0000",
        "updatedAt": "2024-01-13T14:06:29.747+0000",
        "attachments": [
            {
                "self": "https://api.tracker.yandex.net/v3/attachments/4",
                "id": "4",
                "name": "newimage.jpg",
                "content": "api.tracker.yandex.net/v3/attachments/4/newimage.jpg",
                "createdBy": USER,
                "createdAt": "2024-01-11T06:24:57.635+0000",
                "mimetype": "image/jpeg",
                "size": 20466,
            },
        ],
    }
    payload.update(overrides)
    return payload


# --- decoding ------------------------------------------------------------------


class TestAttachmentDecoding:
    async def test_get_attachment_decodes(self) -> None:
        tracker, _ = make_tracker(attachment_payload())
        attachment = await tracker.get_entity_attachment(
            "project",
            "6586d6fee2b9ef74",
            5,
        )

        assert isinstance(attachment, Attachment)
        assert attachment.id == "5"
        assert attachment.name == "flowers.jpg"
        assert attachment.content == (
            "api.tracker.yandex.net/v3/attachments/5/flowers.jpg"
        )
        assert attachment.created_by.display == "Имя Фамилия"
        assert attachment.created_at == datetime(
            2024,
            1,
            11,
            6,
            24,
            57,
            635000,
            tzinfo=timezone.utc,
        )
        assert attachment.mimetype == "image/jpeg"
        assert attachment.size == 20466
        assert attachment.metadata is not None
        assert attachment.metadata.size == "236x295"

    async def test_get_all_attachments_decodes_list(self) -> None:
        tracker, _ = make_tracker([CSV_ATTACHMENT, attachment_payload()])
        attachments = await tracker.get_entity_attachments(
            "project",
            "6586d6fee2b9ef74",
        )

        assert len(attachments) == 2
        assert attachments[0].name == "Shops.csv"
        assert attachments[0].metadata is None
        assert attachments[1].name == "flowers.jpg"
        assert attachments[1].metadata is not None

    async def test_attach_file_returns_entity_with_attachments(self) -> None:
        tracker, _ = make_tracker(entity_with_attachment_payload())
        entity = await tracker.attach_file_to_entity(
            "project",
            "6586d6fee2b9ef74",
            "30",
        )

        assert isinstance(entity, Entity)
        assert entity.id == "6586d6fee2b9ef74"
        assert entity.version == 78
        assert entity.short_id == 4
        assert entity.entity_type == "project"
        assert entity.attachments is not None
        assert entity.attachments[0].id == "4"
        assert entity.attachments[0].name == "newimage.jpg"


# --- get_entity_attachments ----------------------------------------------------


class TestGetEntityAttachments:
    async def test_sends_get(self) -> None:
        tracker, client = make_tracker([attachment_payload()])
        await tracker.get_entity_attachments("project", "6586d6fee2b9ef74")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith(
            "/v3/entities/project/6586d6fee2b9ef74/attachments",
        )
        assert call["params"] is None
        assert call["data"] is None


# --- get_entity_attachment ------------------------------------------------------


class TestGetEntityAttachment:
    async def test_sends_get(self) -> None:
        tracker, client = make_tracker(attachment_payload())
        await tracker.get_entity_attachment("project", "6586d6fee2b9ef74", 5)

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith(
            "/v3/entities/project/6586d6fee2b9ef74/attachments/5",
        )
        assert call["params"] is None
        assert call["data"] is None


# --- attach_file_to_entity -------------------------------------------------------


class TestAttachFileToEntity:
    async def test_sends_post_without_body(self) -> None:
        tracker, client = make_tracker(entity_with_attachment_payload())
        await tracker.attach_file_to_entity("project", "6586d6fee2b9ef74", "30")

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith(
            "/v3/entities/project/6586d6fee2b9ef74/attachments/30",
        )
        assert call["params"] is None
        # unlike `attach_file` for issues, this is not a multipart upload:
        # the temporary file was already uploaded, so there is no body.
        assert call["data"] is None

    async def test_file_id_as_int(self) -> None:
        tracker, client = make_tracker(entity_with_attachment_payload())
        await tracker.attach_file_to_entity("project", "1", 30)

        assert client.calls[0]["url"].endswith("/v3/entities/project/1/attachments/30")

    async def test_query_params(self) -> None:
        tracker, client = make_tracker(entity_with_attachment_payload())
        await tracker.attach_file_to_entity(
            "project",
            "1",
            "30",
            notify=False,
            notify_author=True,
            expand="attachments",
        )

        assert client.calls[0]["params"] == {
            "notify": "false",
            "notifyAuthor": "true",
            "expand": "attachments",
        }

    async def test_fields_param_accepts_string(self) -> None:
        tracker, client = make_tracker(entity_with_attachment_payload())
        await tracker.attach_file_to_entity("project", "1", "30", fields="summary")

        assert client.calls[0]["params"] == {"fields": "summary"}

    async def test_fields_param_joins_sequence(self) -> None:
        tracker, client = make_tracker(entity_with_attachment_payload())
        await tracker.attach_file_to_entity(
            "project",
            "1",
            "30",
            fields=["summary", "entityStatus"],
        )

        assert client.calls[0]["params"] == {"fields": "summary,entityStatus"}

    async def test_no_params_when_not_given(self) -> None:
        tracker, client = make_tracker(entity_with_attachment_payload())
        await tracker.attach_file_to_entity("project", "1", "30")

        assert client.calls[0]["params"] is None


# --- delete_entity_attachment -----------------------------------------------------


class TestDeleteEntityAttachment:
    async def test_sends_delete(self) -> None:
        tracker, client = make_tracker()
        result = await tracker.delete_entity_attachment("project", "1", 123)

        call = client.calls[0]
        assert result is True
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/v3/entities/project/1/attachments/123")
        assert call["params"] is None
        assert call["data"] is None


# --- unknown entity type ------------------------------------------------------


class TestUnknownEntityType:
    async def test_entity_type_is_sent_as_is(self) -> None:
        # `EntityType` documents the kinds Tracker has today, but a kind
        # added later must not be rejected client-side.
        tracker, client = make_tracker([attachment_payload()])
        await tracker.get_entity_attachments("epic", "1")  # type: ignore[arg-type]

        assert client.calls[0]["url"].endswith("/v3/entities/epic/1/attachments")
