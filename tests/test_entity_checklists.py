"""Tests for the entity checklists API (projects and portfolios, issue #14).

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/entities/checklists/add-checklist
https://yandex.ru/support/tracker/ru/api/entities/checklists/patch-checklist
https://yandex.ru/support/tracker/ru/api/entities/checklists/patch-checklist-item
https://yandex.ru/support/tracker/ru/api/entities/checklists/move-checklist-item
https://yandex.ru/support/tracker/ru/api/entities/checklists/delete-checklist-item
https://yandex.ru/support/tracker/ru/api/entities/checklists/delete-checklist
"""

from __future__ import annotations

import warnings
from datetime import date, datetime, timezone
from typing import Any

import pytest
from yatracker.types.entity import Entity, EntityChecklistItem, EntityDeadline

from tests.conftest import USER, make_tracker, sent_json

# --- payload builders --------------------------------------------------------

# `GET/POST/PATCH/DELETE /entities/project/<id>/checklistItems` response shape,
# shared by every method in this module.
ENTITY_BASE: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/entities/project/6586d6fee2b9ef74",
    "id": "6586d6fee2b9ef74",
    "version": 133,
    "shortId": 0,
    "entityType": "project",
    "createdBy": USER,
    "createdAt": "2023-12-13T15:06:27.231Z",
    "updatedAt": "2023-12-13T15:06:27.231Z",
}


def entity_with_checklist_payload(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the `{entity, fields: {checklistItems}}` response the docs show."""
    return {**ENTITY_BASE, "fields": {"checklistItems": items}}


def entity_without_fields_payload() -> dict[str, Any]:
    """Build the `delete-checklist` response: the entity without `fields`."""
    return dict(ENTITY_BASE)


# Two checklist items straight from the `add-checklist` response sample.
TWO_ITEMS: list[dict[str, Any]] = [
    {
        "id": "6586d91f99a40477",
        "text": "First list item",
        "checked": False,
        "checklistItemType": "standard",
    },
    {
        "id": "6586d91f99a40477",
        "text": "Second list item",
        "checked": True,
        "checklistItemType": "standard",
    },
]


# --- add_entity_checklist_item ------------------------------------------------


class TestAddEntityChecklistItem:
    async def test_sends_post_with_full_body(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.add_entity_checklist_item(
            "project",
            "6586d6fee2b9ef74",
            "Item text",
            checked=True,
            assignee="username",
            deadline="2021-05-09T00:00:00.000+0000",
        )

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith(
            "/v3/entities/project/6586d6fee2b9ef74/checklistItems",
        )
        assert call["params"] is None
        assert sent_json(call) == {
            "text": "Item text",
            "checked": True,
            "assignee": "username",
            "deadline": {
                "date": "2021-05-09T00:00:00.000+0000",
                "deadlineType": "date",
            },
        }

    async def test_only_text_is_sent_by_default(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.add_entity_checklist_item("project", "1", "First list item")

        assert sent_json(client.calls[0]) == {"text": "First list item"}

    async def test_query_params(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.add_entity_checklist_item(
            "project",
            "1",
            "Item",
            notify=False,
            notify_author=True,
            fields=["checklistItems", "summary"],
            expand="attachments",
        )

        assert client.calls[0]["params"] == {
            "fields": "checklistItems,summary",
            "expand": "attachments",
            "notify": "false",
            "notifyAuthor": "true",
        }

    async def test_portfolio_entity_type_in_uri(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.add_entity_checklist_item("portfolio", 42, "Item")

        assert client.calls[0]["url"].endswith(
            "/v3/entities/portfolio/42/checklistItems",
        )

    async def test_decodes_entity_and_checklist_items(self) -> None:
        tracker, _ = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        entity = await tracker.add_entity_checklist_item("project", "1", "Item")

        assert isinstance(entity, Entity)
        assert entity.version == 133
        items = entity.fields.checklist_items
        assert items is not None
        assert len(items) == 2
        assert items[0].text == "First list item"
        assert items[0].checked is False
        assert items[0].checklist_item_type == "standard"
        assert items[1].checked is True

    async def test_deadline_as_aware_datetime(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        deadline = datetime(2021, 5, 9, 12, 30, tzinfo=timezone.utc)
        await tracker.add_entity_checklist_item(
            "project",
            "1",
            "Item",
            deadline=deadline,
        )

        assert sent_json(client.calls[0])["deadline"] == {
            "date": "2021-05-09T12:30:00.000+0000",
            "deadlineType": "date",
        }

    async def test_deadline_as_bare_date(self) -> None:
        # the docs document the date only as a full timestamp, so a bare
        # `date` is sent as midnight UTC
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.add_entity_checklist_item(
            "project",
            "1",
            "Item",
            deadline=date(2021, 5, 9),
        )

        assert sent_json(client.calls[0])["deadline"] == {
            "date": "2021-05-09T00:00:00.000+0000",
            "deadlineType": "date",
        }

    async def test_bare_date_deadline_does_not_warn(self) -> None:
        # the midnight-UTC timestamp is built by the library, not by the
        # user, so it must not trigger the naive-datetime warning
        tracker, _ = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await tracker.add_entity_checklist_item(
                "project",
                "1",
                "Item",
                deadline=date(2021, 5, 9),
            )

    async def test_deadline_as_entity_deadline_keeps_its_type(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.add_entity_checklist_item(
            "project",
            "1",
            "Item",
            deadline=EntityDeadline(date=date(2021, 5, 9), deadline_type="quarter"),
        )

        assert sent_json(client.calls[0])["deadline"] == {
            "date": "2021-05-09T00:00:00.000+0000",
            "deadlineType": "quarter",
        }

    async def test_deadline_as_ready_made_string_passes_through(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.add_entity_checklist_item(
            "project",
            "1",
            "Item",
            deadline="2021-05-09",
        )

        assert sent_json(client.calls[0])["deadline"] == {
            "date": "2021-05-09",
            "deadlineType": "date",
        }

    async def test_deadline_as_entity_deadline_with_datetime(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        deadline = EntityDeadline(
            date=datetime(2021, 5, 9, 8, tzinfo=timezone.utc),
        )
        await tracker.add_entity_checklist_item(
            "project",
            "1",
            "Item",
            deadline=deadline,
        )

        # `deadline_type` left as `None` on the model defaults to "date".
        assert sent_json(client.calls[0])["deadline"] == {
            "date": "2021-05-09T08:00:00.000+0000",
            "deadlineType": "date",
        }

    async def test_naive_deadline_warns(self) -> None:
        tracker, _ = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        with pytest.warns(UserWarning, match="naive datetime") as record:
            await tracker.add_entity_checklist_item(
                "project",
                "1",
                "Item",
                deadline=datetime(2021, 5, 9, 8),  # noqa: DTZ001
            )

        # the warning points at this file, not at the library internals
        assert record[0].filename == __file__

    async def test_entity_deadline_without_a_date_is_not_sent(self) -> None:
        # nothing to put in the `date` key, so the whole object is left
        # out rather than sent half-built
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.add_entity_checklist_item(
            "project",
            "1",
            "Item",
            deadline=EntityDeadline(deadline_type="date"),
        )

        assert sent_json(client.calls[0]) == {"text": "Item"}


# --- EntityChecklistItem request form ----------------------------------------


class TestChecklistItemRequestForm:
    """The model renders its own request body, whatever fields it has."""

    async def test_only_the_id_is_sent_for_a_bare_item(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist(
            "project",
            "1",
            [EntityChecklistItem(id="1")],
        )

        assert sent_json(client.calls[0]) == [{"id": "1"}]

    async def test_text_without_checked(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist(
            "project",
            "1",
            [EntityChecklistItem(id="1", text="Item")],
        )

        assert sent_json(client.calls[0]) == [{"id": "1", "text": "Item"}]

    async def test_checked_without_text(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist(
            "project",
            "1",
            [EntityChecklistItem(id="1", checked=False)],
        )

        # `False` is a value, not an absent field
        assert sent_json(client.calls[0]) == [{"id": "1", "checked": False}]

    async def test_deadline_of_the_item_is_rendered_as_a_timestamp(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist(
            "project",
            "1",
            [
                EntityChecklistItem(
                    id="1",
                    deadline=EntityDeadline(
                        date=date(2021, 5, 9),
                        deadline_type="date",
                    ),
                ),
            ],
        )

        assert sent_json(client.calls[0]) == [
            {
                "id": "1",
                "deadline": {
                    "date": "2021-05-09T00:00:00.000+0000",
                    "deadlineType": "date",
                },
            },
        ]

    async def test_dateless_deadline_of_the_item_is_omitted(self) -> None:
        # a deadline object without a date (e.g. only the read-only
        # `isExceeded`) has nothing to send, so the key is omitted, the
        # same way `_build_deadline` treats it for the single-item methods
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist(
            "project",
            "1",
            [EntityChecklistItem(id="1", deadline=EntityDeadline())],
        )

        assert sent_json(client.calls[0]) == [{"id": "1"}]

    async def test_read_only_fields_are_dropped(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        item = EntityChecklistItem(
            id="1",
            text="Item",
            text_html="<p>Item</p>",
            checklist_item_type="standard",
        )
        await tracker.edit_entity_checklist("project", "1", [item])

        assert sent_json(client.calls[0]) == [{"id": "1", "text": "Item"}]


# --- deadline decoding regression (`date` -> `DateOrDatetime`) ---------------


class TestChecklistDeadlineDecoding:
    async def test_non_midnight_deadline_decodes_as_datetime(self) -> None:
        items = [
            {
                "id": "1",
                "text": "Item",
                "checked": False,
                "deadline": {
                    "date": "2024-05-01T12:00:00.000+0000",
                    "deadlineType": "date",
                },
                "checklistItemType": "standard",
            },
        ]
        tracker, _ = make_tracker(entity_with_checklist_payload(items))
        entity = await tracker.add_entity_checklist_item("project", "1", "Item")

        deadline = entity.fields.checklist_items[0].deadline
        assert deadline is not None
        assert deadline.date == datetime(2024, 5, 1, 12, tzinfo=timezone.utc)
        assert type(deadline.date) is datetime

    async def test_bare_date_deadline_decodes_as_date(self) -> None:
        items = [
            {
                "id": "1",
                "text": "Item",
                "checked": False,
                "deadline": {"date": "2024-05-01", "deadlineType": "date"},
                "checklistItemType": "standard",
            },
        ]
        tracker, _ = make_tracker(entity_with_checklist_payload(items))
        entity = await tracker.add_entity_checklist_item("project", "1", "Item")

        deadline = entity.fields.checklist_items[0].deadline
        assert deadline is not None
        assert deadline.date == date(2024, 5, 1)
        assert type(deadline.date) is date


# --- edit_entity_checklist -----------------------------------------------------


class TestEditEntityChecklist:
    async def test_sends_patch_with_json_array_body(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist(
            "project",
            "1",
            [
                {"id": "658953a65c0f1b21", "text": "First list item"},
                {
                    "id": "658953a65c0f1b22",
                    "text": "Second list item",
                    "assignee": 190000000,
                    "checked": True,
                },
            ],
        )

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/v3/entities/project/1/checklistItems")
        body = sent_json(call)
        assert isinstance(body, list)
        assert body == [
            {"id": "658953a65c0f1b21", "text": "First list item"},
            {
                "id": "658953a65c0f1b22",
                "text": "Second list item",
                "assignee": 190000000,
                "checked": True,
            },
        ]

    async def test_accepts_entity_checklist_item_models(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        item = EntityChecklistItem(id="1", text="Item", checked=True)
        await tracker.edit_entity_checklist("project", "1", [item])

        assert sent_json(client.calls[0]) == [
            {"id": "1", "text": "Item", "checked": True},
        ]

    async def test_decoded_items_are_re_encoded_for_the_request(self) -> None:
        # an item read back from the API carries an assignee object and
        # read-only fields the endpoint does not accept: sending it back
        # unchanged must not put them on the wire
        item = {
            "id": "6586d91f99a40477",
            "text": "First list item",
            "textHtml": "<p>First list item</p>",
            "checked": False,
            "assignee": USER,
            "deadline": {
                "date": "2021-05-09T00:00:00.000+0000",
                "deadlineType": "date",
                "isExceeded": False,
            },
            "checklistItemType": "standard",
        }
        tracker, client = make_tracker(entity_with_checklist_payload([item]))
        entity = await tracker.get_entity("project", "1", fields="checklistItems")
        items = entity.fields.checklist_items
        assert items is not None

        await tracker.edit_entity_checklist("project", "1", items)

        assert sent_json(client.calls[1]) == [
            {
                "id": "6586d91f99a40477",
                "text": "First list item",
                "checked": False,
                "assignee": "1111",
                "deadline": {
                    "date": "2021-05-09T00:00:00.000+0000",
                    "deadlineType": "date",
                },
            },
        ]

    async def test_query_params(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist(
            "project",
            "1",
            [{"id": "1", "text": "Item"}],
            notify=True,
            notify_author=False,
            fields="checklistItems",
            expand="attachments",
        )

        assert client.calls[0]["params"] == {
            "fields": "checklistItems",
            "expand": "attachments",
            "notify": "true",
            "notifyAuthor": "false",
        }

    async def test_decodes_response(self) -> None:
        tracker, _ = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        entity = await tracker.edit_entity_checklist(
            "project",
            "1",
            [{"id": "1", "text": "Item"}],
        )

        assert isinstance(entity, Entity)
        assert entity.fields.checklist_items is not None
        assert len(entity.fields.checklist_items) == 2

    async def test_bare_dict_item_raises_type_error(self) -> None:
        tracker, _ = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        with pytest.raises(TypeError, match="sequence of checklist items"):
            await tracker.edit_entity_checklist(
                "project",
                "1",
                {"id": "1", "text": "Item"},  # type: ignore[arg-type]
            )

    async def test_items_accept_a_generator(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist(
            "project",
            "1",
            (item for item in ({"text": "One"}, {"text": "Two"})),
        )

        assert sent_json(client.calls[0]) == [{"text": "One"}, {"text": "Two"}]

    async def test_bare_model_item_raises_type_error(self) -> None:
        tracker, _ = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        with pytest.raises(TypeError, match="sequence of checklist items"):
            await tracker.edit_entity_checklist(
                "project",
                "1",
                EntityChecklistItem(id="1", text="Item"),  # type: ignore[arg-type]
            )

    async def test_empty_sequence_raises_value_error(self) -> None:
        tracker, _ = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        with pytest.raises(ValueError, match="At least one checklist item"):
            await tracker.edit_entity_checklist("project", "1", [])


# --- edit_entity_checklist_item -----------------------------------------------


class TestEditEntityChecklistItem:
    async def test_sends_patch_to_item_uri(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist_item(
            "project",
            "1",
            "6586d91f99a40477",
            text="Modified list item",
            checked=True,
        )

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith(
            "/v3/entities/project/1/checklistItems/6586d91f99a40477",
        )
        assert sent_json(call) == {"text": "Modified list item", "checked": True}

    async def test_deadline_and_assignee_in_body(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist_item(
            "project",
            "1",
            "item-1",
            assignee="username",
            deadline="2021-05-09T00:00:00.000+0000",
        )

        assert sent_json(client.calls[0]) == {
            "assignee": "username",
            "deadline": {
                "date": "2021-05-09T00:00:00.000+0000",
                "deadlineType": "date",
            },
        }

    async def test_query_params(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.edit_entity_checklist_item(
            "project",
            "1",
            "item-1",
            text="Item",
            notify=False,
            notify_author=True,
            fields="checklistItems",
        )

        assert client.calls[0]["params"] == {
            "fields": "checklistItems",
            "notify": "false",
            "notifyAuthor": "true",
        }

    async def test_decodes_response(self) -> None:
        tracker, _ = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        entity = await tracker.edit_entity_checklist_item(
            "project",
            "1",
            "item-1",
            text="Item",
        )

        assert isinstance(entity, Entity)

    async def test_nothing_to_change_raises_value_error(self) -> None:
        tracker, _ = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        with pytest.raises(ValueError, match="at least one field"):
            await tracker.edit_entity_checklist_item("project", "1", "item-1")


# --- move_entity_checklist_item -------------------------------------------------


class TestMoveEntityChecklistItem:
    async def test_sends_post_with_before(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.move_entity_checklist_item(
            "project",
            "1",
            "6586d6fee2b9ef73",
            "6586d6fee2b9ef72",
        )

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith(
            "/v3/entities/project/1/checklistItems/6586d6fee2b9ef73/_move",
        )
        assert sent_json(call) == {"before": "6586d6fee2b9ef72"}
        assert call["params"] is None

    async def test_query_params(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.move_entity_checklist_item(
            "project",
            "1",
            "item-1",
            "item-2",
            fields="checklistItems",
            expand="attachments",
        )

        assert client.calls[0]["params"] == {
            "fields": "checklistItems",
            "expand": "attachments",
        }

    async def test_decodes_moved_order(self) -> None:
        items = [
            {
                "id": "a",
                "text": "First checklist item",
                "checked": False,
                "checklistItemType": "standard",
            },
            {
                "id": "b",
                "text": "Third checklist item",
                "checked": True,
                "checklistItemType": "standard",
            },
            {
                "id": "c",
                "text": "Second checklist item",
                "checked": True,
                "checklistItemType": "standard",
            },
        ]
        tracker, _ = make_tracker(entity_with_checklist_payload(items))
        entity = await tracker.move_entity_checklist_item("project", "1", "b", "c")

        assert entity.fields.checklist_items is not None
        assert [i.id for i in entity.fields.checklist_items] == ["a", "b", "c"]


# --- delete_entity_checklist_item -----------------------------------------------


class TestDeleteEntityChecklistItem:
    async def test_sends_delete_and_decodes_the_entity(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        entity = await tracker.delete_entity_checklist_item(
            "project",
            "1",
            "6586d6fee2b9ef72",
        )

        assert isinstance(entity, Entity)
        assert entity.id == "6586d6fee2b9ef74"
        assert entity.fields is not None
        items = entity.fields.checklist_items or []
        assert [item.text for item in items] == [
            "First list item",
            "Second list item",
        ]
        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith(
            "/v3/entities/project/1/checklistItems/6586d6fee2b9ef72",
        )
        assert call["data"] is None

    async def test_query_params(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.delete_entity_checklist_item(
            "project",
            "1",
            "item-1",
            notify=True,
            notify_author=True,
        )

        assert client.calls[0]["params"] == {
            "notify": "true",
            "notifyAuthor": "true",
        }

    async def test_fields_and_expand_are_sent(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.delete_entity_checklist_item(
            "project",
            "1",
            "item-1",
            fields=["checklistItems", "summary"],
            expand="attachments",
        )

        assert client.calls[0]["params"] == {
            "fields": "checklistItems,summary",
            "expand": "attachments",
        }

    async def test_no_query_params_by_default(self) -> None:
        tracker, client = make_tracker(entity_with_checklist_payload(TWO_ITEMS))
        await tracker.delete_entity_checklist_item("project", "1", "item-1")

        assert client.calls[0]["params"] is None


# --- delete_entity_checklist ----------------------------------------------------


class TestDeleteEntityChecklist:
    async def test_sends_delete_to_checklist_uri_and_decodes_the_entity(self) -> None:
        tracker, client = make_tracker(entity_without_fields_payload())
        entity = await tracker.delete_entity_checklist("project", "1")

        assert isinstance(entity, Entity)
        assert entity.id == "6586d6fee2b9ef74"
        assert entity.version == 133
        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/v3/entities/project/1/checklistItems")
        assert call["data"] is None

    async def test_fields_and_expand_are_sent(self) -> None:
        tracker, client = make_tracker(entity_without_fields_payload())
        await tracker.delete_entity_checklist(
            "project",
            "1",
            fields="checklistItems",
            expand="attachments",
        )

        assert client.calls[0]["params"] == {
            "fields": "checklistItems",
            "expand": "attachments",
        }

    async def test_query_params(self) -> None:
        tracker, client = make_tracker(entity_without_fields_payload())
        await tracker.delete_entity_checklist(
            "project",
            "1",
            notify=False,
            notify_author=False,
        )

        assert client.calls[0]["params"] == {
            "notify": "false",
            "notifyAuthor": "false",
        }

    async def test_decodes_a_response_without_a_fields_block(self) -> None:
        # the `delete-checklist` sample answers with the entity and no
        # `fields` block at all: the whole checklist is gone.
        tracker, client = make_tracker(entity_without_fields_payload())
        entity = await tracker.delete_entity_checklist("portfolio", 7)

        assert entity.fields is not None
        assert entity.fields.checklist_items is None
        assert client.calls[0]["url"].endswith(
            "/v3/entities/portfolio/7/checklistItems",
        )
