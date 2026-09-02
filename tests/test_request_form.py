"""Tests for `Base._to_request`: models sent back into a request body.

A model read from the API carries read-only fields, embedded objects and
date formats the endpoints do not accept back. `_convert_value` renders
every model through its own request form, so the same object renders the
same way wherever it reaches a request body.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/entities/checklists/patch-checklist
https://yandex.ru/support/tracker/ru/api/entities/keyresults
https://yandex.ru/support/tracker/ru/api/entities/metric
https://yandex.ru/support/tracker/ru/api/dashboards/create-widget
https://yandex.ru/support/tracker/ru/api/filters/update-filter
"""

from __future__ import annotations

import warnings
from datetime import date, datetime, timezone
from typing import Any

import pytest
from yatracker.tracker.base import BaseTracker, _convert_value
from yatracker.types.checklist import ChecklistAssignee
from yatracker.types.dashboard import WidgetBucket
from yatracker.types.entity import (
    Entity,
    EntityChecklistItem,
    EntityDeadline,
    EntityKeyResult,
    EntityMetricItem,
)
from yatracker.types.filter import FilterSort
from yatracker.types.ref import FieldRef

from tests.conftest import USER, make_tracker, sent_json

# --- payloads -----------------------------------------------------------------

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

# The assignee of a checklist item, straight from the `patch-checklist`
# response sample: unlike a key result assignee it carries no `self`.
CHECKLIST_ASSIGNEE: dict[str, Any] = {
    "id": "133000",
    "passportUid": 133000,
    "login": "username",
    "display": "Имя Фамилия",
}

# One checklist item as the API returns it, with every read-only field.
DECODED_ITEM: dict[str, Any] = {
    "id": "6586d91f99a40477",
    "text": "First list item",
    "textHtml": "<p>First list item</p>",
    "checked": False,
    "assignee": CHECKLIST_ASSIGNEE,
    "deadline": {
        "date": "2021-05-09T00:00:00.000+0000",
        "deadlineType": "date",
        "isExceeded": False,
    },
    "checklistItemType": "standard",
}


def entity_payload(fields: dict[str, Any] | None = None) -> dict[str, Any]:
    return {**ENTITY_BASE, "fields": fields or {}}


async def decoded_checklist_item(
    payload: dict[str, Any],
) -> EntityChecklistItem:
    """Read one checklist item back through the API, like a user would."""
    tracker, _ = make_tracker(entity_payload({"checklistItems": [payload]}))
    entity = await tracker.get_entity("project", "1", fields="checklistItems")
    items = entity.fields.checklist_items
    assert items is not None
    return items[0]


# --- the same item on both paths ----------------------------------------------


class TestChecklistItemRendersTheSameEverywhere:
    async def test_update_entity_matches_edit_entity_checklist(self) -> None:
        item = await decoded_checklist_item(DECODED_ITEM)

        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity(
            "project",
            "1",
            values={"checklistItems": [item]},
        )
        await tracker.edit_entity_checklist("project", "1", [item])

        through_values = sent_json(client.calls[0])["fields"]["checklistItems"]
        through_checklist = sent_json(client.calls[1])
        assert through_values == through_checklist

    async def test_read_only_fields_never_reach_the_wire(self) -> None:
        item = await decoded_checklist_item(DECODED_ITEM)

        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity(
            "project",
            "1",
            values={"checklistItems": [item]},
        )

        assert sent_json(client.calls[0])["fields"]["checklistItems"] == [
            {
                "id": "6586d91f99a40477",
                "text": "First list item",
                "checked": False,
                "assignee": "133000",
                "deadline": {
                    "date": "2021-05-09T00:00:00.000+0000",
                    "deadlineType": "date",
                },
            },
        ]

    async def test_checklist_assignee_without_self_decodes(self) -> None:
        # the documented checklist assignee object has no `self` key, so
        # the regular `User` model (whose `url` is required) would reject
        # every real response
        item = await decoded_checklist_item(DECODED_ITEM)

        assert isinstance(item.assignee, ChecklistAssignee)
        assert item.assignee.id == "133000"
        assert item.assignee.login == "username"
        assert item.assignee.passport_uid == 133000


# --- deadlines ----------------------------------------------------------------


class TestDeadlineRendering:
    async def test_naive_deadline_warns_and_keeps_the_time(self) -> None:
        naive = datetime(2024, 3, 1, 12, 0)  # noqa: DTZ001
        tracker, client = make_tracker(entity_payload())

        with pytest.warns(UserWarning, match="Timezone-Aware") as record:
            await tracker.update_entity(
                "project",
                "1",
                values={
                    "checklistItems": [
                        EntityChecklistItem(
                            id="1",
                            deadline=EntityDeadline(date=naive),
                        ),
                    ],
                },
            )

        assert record[0].filename == __file__
        assert sent_json(client.calls[0])["fields"]["checklistItems"][0][
            "deadline"
        ] == {"date": "2024-03-01T12:00:00.000", "deadlineType": "date"}

    async def test_aware_deadline_uses_the_documented_offset_form(self) -> None:
        # pydantic would render the same moment as `...T12:00:00Z`,
        # which the API does not document
        aware = datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc)
        tracker, client = make_tracker(entity_payload())

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await tracker.update_entity(
                "project",
                "1",
                values={
                    "checklistItems": [
                        EntityChecklistItem(
                            id="1",
                            deadline=EntityDeadline(date=aware),
                        ),
                    ],
                },
            )

        rendered = sent_json(client.calls[0])["fields"]["checklistItems"][0]
        assert rendered["deadline"] == {
            "date": "2024-03-01T12:00:00.000+0000",
            "deadlineType": "date",
        }

    async def test_bare_date_is_midnight_utc_on_the_checklist_path(self) -> None:
        tracker, client = make_tracker(entity_payload())

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await tracker.edit_entity_checklist(
                "project",
                "1",
                [
                    EntityChecklistItem(
                        id="1",
                        deadline=EntityDeadline(date=date(2025, 6, 3)),
                    ),
                ],
            )

        assert sent_json(client.calls[0])[0]["deadline"] == {
            "date": "2025-06-03T00:00:00.000+0000",
            "deadlineType": "date",
        }

    async def test_bare_date_stays_a_plain_date_on_its_own(self) -> None:
        # a key result deadline is documented as `YYYY-MM-DD`
        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity(
            "project",
            "1",
            values={
                "deadline": EntityDeadline(
                    date=date(2025, 6, 3),
                    deadline_type="date",
                ),
            },
        )

        assert sent_json(client.calls[0])["fields"]["deadline"] == {
            "date": "2025-06-03",
            "deadlineType": "date",
        }

    def test_deadline_without_a_date_renders_only_its_type(self) -> None:
        deadline = EntityDeadline(deadline_type="quarter")
        assert _convert_value(deadline) == {"deadlineType": "quarter"}

    def test_deadline_without_anything_renders_empty(self) -> None:
        assert _convert_value(EntityDeadline()) == {}

    def test_is_exceeded_is_always_dropped(self) -> None:
        deadline = EntityDeadline(
            date=date(2025, 6, 3),
            deadline_type="date",
            is_exceeded=True,
        )
        assert "isExceeded" not in _convert_value(deadline)


# --- models that must stay verbatim -------------------------------------------


class TestVerbatimModels:
    async def test_key_result_keeps_the_response_shape(self) -> None:
        # the `remove` operator of `keyResultItems` requires the object
        # exactly as the API returned it, `self` links included
        key_result = {
            "id": "6789000",
            "type": "binary",
            "text": "My key result",
            "assignee": USER,
            "deadline": {"date": "2025-06-03", "deadlineType": "date"},
        }
        tracker, client = make_tracker(
            entity_payload({"keyResultItems": [key_result]}),
        )
        entity = await tracker.get_entity("goal", "1", fields="keyResultItems")
        items = entity.fields.key_result_items
        assert items is not None
        assert isinstance(items[0], EntityKeyResult)

        await tracker.update_entity(
            "goal",
            "1",
            values={"keyResultItems": {"remove": items[0]}},
        )

        sent = sent_json(client.calls[1])["fields"]["keyResultItems"]["remove"]
        # the assignee stays the object the API sent — `self`, `id`,
        # `display` and the account identifiers `passportUid`/`cloudUid`
        # — not a bare id, and the deadline keeps its response shape
        assert sent == {
            "id": "6789000",
            "type": "binary",
            "text": "My key result",
            "assignee": USER,
            "deadline": {"date": "2025-06-03", "deadlineType": "date"},
        }

    async def test_metric_item_keeps_the_response_shape(self) -> None:
        metric = {
            "id": "6586d91f99a40477",
            "text": "Metric",
            "url": "https://example.com/metric",
        }
        tracker, client = make_tracker(entity_payload({"metricItems": [metric]}))
        entity = await tracker.get_entity("goal", "1", fields="metricItems")
        items = entity.fields.metric_items
        assert items is not None
        assert isinstance(items[0], EntityMetricItem)

        await tracker.update_entity(
            "goal",
            "1",
            values={"metricItems": {"remove": items[0]}},
        )

        sent = sent_json(client.calls[1])["fields"]["metricItems"]["remove"]
        assert sent == metric

    async def test_entity_reaching_a_body_is_dumped_verbatim(self) -> None:
        tracker, _ = make_tracker(entity_payload())
        entity = await tracker.get_entity("project", "1")

        assert isinstance(entity, Entity)
        dumped = _convert_value(entity)
        assert dumped["self"] == ENTITY_BASE["self"]
        assert dumped["createdBy"]["self"] == USER["self"]


# --- dashboards and filters ---------------------------------------------------


class TestWidgetBucketRequestForm:
    def test_type_is_renamed_to_unit(self) -> None:
        bucket = WidgetBucket(type="weeks", count=2, board_id="10")
        assert _convert_value(bucket) == {
            "unit": "weeks",
            "count": 2,
            "boardId": "10",
        }

    def test_unset_fields_are_dropped(self) -> None:
        assert _convert_value(WidgetBucket(type="days")) == {"unit": "days"}

    def test_inside_a_prepared_payload(self) -> None:
        payload = BaseTracker._prepare_payload(
            {"bucket": WidgetBucket(type="sprints", count=1, board_id="10")},
        )
        assert payload == {
            "bucket": {"unit": "sprints", "count": 1, "boardId": "10"},
        }


class TestFilterSortRequestForm:
    def test_field_object_becomes_a_key(self) -> None:
        sort = FilterSort(
            field=FieldRef(
                url="https://api.tracker.yandex.net/v3/fields/created",
                id="created",
                display="Дата создания",
            ),
            is_ascending=False,
        )
        assert _convert_value(sort) == {"field": "created", "isAscending": False}

    def test_unset_direction_is_dropped(self) -> None:
        sort = FilterSort(field=FieldRef(url="u", id="created"))
        assert _convert_value(sort) == {"field": "created"}

    def test_inside_a_prepared_payload(self) -> None:
        sort = FilterSort(field=FieldRef(url="u", id="key"), is_ascending=True)
        payload = BaseTracker._prepare_payload({"sorts": [sort]})
        assert payload == {"sorts": [{"field": "key", "isAscending": True}]}
