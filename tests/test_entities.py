"""Tests for the entities API (projects, portfolios and goals, issue #15).

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/entities/about-entities
https://yandex.ru/support/tracker/ru/api/entities/create-entity
https://yandex.ru/support/tracker/ru/api/entities/get-entity
https://yandex.ru/support/tracker/ru/api/entities/update-entity
https://yandex.ru/support/tracker/ru/api/entities/delete-entity
https://yandex.ru/support/tracker/ru/api/entities/search-entities
https://yandex.ru/support/tracker/ru/api/entities/bulkchange-entities
https://yandex.ru/support/tracker/ru/api/entities/get-events-relative
"""

from __future__ import annotations

import json
import warnings
from datetime import date, datetime, timezone
from typing import Any

import pytest
from yatracker import YaTracker
from yatracker.types import BulkChange
from yatracker.types.entity import (
    Entity,
    EntityChecklistItem,
    EntityDeadline,
    EntityEvents,
    EntityFields,
    EntityLink,
    EntitySearchResult,
)

from tests.conftest import (
    USER,
    FakeClient,
    attachment_body,
    bulk_change_body,
    bulk_change_payload,
    make_tracker,
    sent_json,
)

# --- payload builders --------------------------------------------------------

# `POST /entities/project` 201 response: note there is no `fields` key at all.
CREATED_ENTITY: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/entities/project/655f3be523db2132",
    "id": "655f3be523db2132",
    "version": 1,
    "shortId": 6,
    "entityType": "project",
    "createdBy": USER,
    "createdAt": "2023-11-23T11:47:49.743+0000",
    "updatedAt": "2023-11-23T11:47:49.743+0000",
}


def entity_payload(**overrides: Any) -> dict[str, Any]:
    """Build a `GET /entities/project/{id}` payload."""
    payload: dict[str, Any] = {
        **CREATED_ENTITY,
        "attachments": [json.loads(attachment_body())],
        "fields": {
            "summary": "Название проекта",
            "teamAccess": None,
            "author": USER,
            "parentEntity": {
                "primary": {
                    "self": (
                        "https://api.tracker.yandex.net/v3/entities/portfolio/67ffd7e3"
                    ),
                    "id": "67ffd7e3",
                    "display": "My portfolio",
                },
                "secondary": [],
            },
        },
    }
    payload.update(overrides)
    return payload


def entity_body(**overrides: Any) -> bytes:
    return json.dumps(entity_payload(**overrides)).encode()


def search_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "hits": 8,
        "pages": 1,
        "values": [entity_payload()],
        "orderBy": "entityStatus",
    }
    payload.update(overrides)
    return payload


def search_body(**overrides: Any) -> bytes:
    return json.dumps(search_payload(**overrides)).encode()


EVENTS: dict[str, Any] = {
    "events": [
        {
            "id": "6a4b9ad0d4a1e0e0d3a1b2c3",
            "author": USER,
            "date": "2024-01-13T10:51:17.821+0000",
            "transport": "v3",
            "display": "Issue updated",
            "changes": [
                {
                    "diff": "<added>User Name</added>",
                    "field": {"id": "teamUsers", "display": "Participants"},
                },
            ],
        },
    ],
    "hasNext": True,
    "hasPrev": True,
}


# --- decoding ----------------------------------------------------------------


class TestEntityDecoding:
    async def test_create_response_without_fields(self) -> None:
        tracker, _ = make_tracker(CREATED_ENTITY)
        entity = await tracker.create_entity("project", "Название проекта")

        assert entity.id == "655f3be523db2132"
        assert entity.version == 1
        assert entity.short_id == 6
        assert entity.entity_type == "project"
        assert entity.created_by.display == "Имя Фамилия"
        assert entity.created_at == datetime(
            2023,
            11,
            23,
            11,
            47,
            49,
            743000,
            tzinfo=timezone.utc,
        )
        assert entity.attachments is None
        # missing `fields` decodes into an empty model, not `None`
        assert isinstance(entity.fields, EntityFields)
        assert entity.fields.summary is None

    async def test_get_response_decodes(self) -> None:
        tracker, _ = make_tracker(entity_payload())
        entity = await tracker.get_entity("project", "655f3be523db2132")

        assert entity.fields.summary == "Название проекта"
        # `null` is a meaningful value here: access is not restricted
        assert entity.fields.team_access is None
        assert entity.fields.author is not None
        assert entity.fields.author.id == "1111"

        parent = entity.fields.parent_entity
        assert parent is not None
        assert parent.primary is not None
        assert parent.primary.id == "67ffd7e3"
        assert parent.primary.display == "My portfolio"
        assert parent.secondary == []

        assert entity.attachments is not None
        assert entity.attachments[0].name == "a.txt"

    async def test_extra_fields_are_preserved(self) -> None:
        payload = entity_payload()
        payload["fields"]["customField"] = 1
        tracker, _ = make_tracker(payload)
        entity = await tracker.get_entity("project", "1")

        assert entity.fields.model_extra == {"customField": 1}
        assert entity.fields.customField == 1

    @pytest.mark.parametrize(
        "field_name",
        ["start", "end", "lastCommentUpdatedAt"],
    )
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("2023-11-23", date(2023, 11, 23)),
            (
                "2023-11-23T11:47:49.743+0000",
                datetime(2023, 11, 23, 11, 47, 49, 743000, tzinfo=timezone.utc),
            ),
            # a midnight timestamp keeps its time and offset instead of
            # collapsing into a bare `date`
            (
                "2023-11-23T00:00:00.000+0000",
                datetime(2023, 11, 23, tzinfo=timezone.utc),
            ),
            ("2023-11-23T00:00:00Z", datetime(2023, 11, 23, tzinfo=timezone.utc)),
        ],
    )
    def test_date_or_datetime_in_both_modes(
        self,
        field_name: str,
        raw: str,
        expected: date,
    ) -> None:
        from_json = EntityFields.model_validate_json(json.dumps({field_name: raw}))
        from_python = EntityFields.model_validate({field_name: raw})

        attr = {
            "start": "start",
            "end": "end",
            "lastCommentUpdatedAt": "last_comment_updated_at",
        }[field_name]
        for fields in (from_json, from_python):
            value = getattr(fields, attr)
            assert value == expected
            assert type(value) is type(expected)

    def test_date_or_datetime_objects_pass_through(self) -> None:
        # python-mode input that is already a `date`/`datetime` is kept as is
        start = date(2023, 11, 23)
        end = datetime(2023, 11, 23, tzinfo=timezone.utc)
        fields = EntityFields.model_validate({"start": start, "end": end})

        assert fields.start == start
        assert type(fields.start) is date
        assert fields.end == end
        assert type(fields.end) is datetime

    async def test_start_and_end_dates(self) -> None:
        payload = entity_payload()
        payload["fields"]["start"] = "2023-11-23"
        payload["fields"]["end"] = "2023-11-23T11:47:49.743+0000"
        tracker, _ = make_tracker(payload)
        entity = await tracker.get_entity("project", "1")

        # a bare date stays a `date`, a timestamp becomes a `datetime`
        assert entity.fields.start == date(2023, 11, 23)
        assert not isinstance(entity.fields.start, datetime)
        assert entity.fields.end == datetime(
            2023,
            11,
            23,
            11,
            47,
            49,
            743000,
            tzinfo=timezone.utc,
        )

    async def test_issue_queues_decode_into_queues(self) -> None:
        payload = entity_payload()
        payload["fields"]["issueQueues"] = [
            {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                "id": "1",
                "key": "TEST",
                "display": "My queue",
            },
        ]
        tracker, _ = make_tracker(payload)
        entity = await tracker.get_entity("project", "1")

        assert entity.fields.issue_queues is not None
        queue = entity.fields.issue_queues[0]
        assert queue.key == "TEST"
        assert queue.display == "My queue"

    async def test_checklist_metrics_and_key_results_decode(self) -> None:
        payload = entity_payload()
        payload["fields"].update(
            {
                "checklistItems": [
                    {
                        "id": "1",
                        "text": "Step",
                        "textHtml": "<p>Step</p>",
                        "checked": False,
                        "assignee": USER,
                        "deadline": {
                            "date": "2024-01-13",
                            "deadlineType": "date",
                            "isExceeded": False,
                        },
                        "checklistItemType": "standard",
                    },
                ],
                "metricItems": [{"id": "2", "text": "Metric", "url": "https://ya.ru"}],
                "keyResultItems": [
                    {
                        "id": "3",
                        "text": "Key result",
                        "type": "value",
                        "progress": {"start": 0, "end": 10, "current": 5},
                        "achieved": False,
                        "assignee": USER,
                    },
                ],
                "quarter": ["2024 Q1"],
                "tags": ["tag"],
                "progressPercentage": 0.5,
                "linkedGoalsCount": 2,
                "linkedProjectsCount": 3,
                "entityStatus": "in_progress",
            },
        )
        tracker, _ = make_tracker(payload)
        fields = (await tracker.get_entity("goal", "1")).fields

        assert fields.checklist_items is not None
        item = fields.checklist_items[0]
        assert item.text_html == "<p>Step</p>"
        assert item.checklist_item_type == "standard"
        assert item.deadline is not None
        assert item.deadline.date == date(2024, 1, 13)
        assert item.deadline.is_exceeded is False

        assert fields.metric_items is not None
        assert fields.metric_items[0].link == "https://ya.ru"

        assert fields.key_result_items is not None
        key_result = fields.key_result_items[0]
        assert key_result.type == "value"
        assert key_result.progress is not None
        assert key_result.progress.current == 5

        assert fields.quarter == ["2024 Q1"]
        assert fields.tags == ["tag"]
        assert fields.progress_percentage == 0.5
        assert fields.linked_goals_count == 2
        assert fields.linked_projects_count == 3
        assert fields.entity_status == "in_progress"

    async def test_search_result_decodes(self) -> None:
        tracker, _ = make_tracker(search_payload())
        result = await tracker.search_entities("project")

        assert isinstance(result, EntitySearchResult)
        assert result.hits == 8
        assert result.pages == 1
        assert result.order_by == "entityStatus"
        assert len(result.values) == 1
        assert isinstance(result.values[0], Entity)

    async def test_events_decode(self) -> None:
        tracker, _ = make_tracker(EVENTS)
        events = await tracker.get_entity_events("project", "1")

        assert isinstance(events, EntityEvents)
        assert events.has_next is True
        assert events.has_prev is True

        event = events.events[0]
        assert event.transport == "v3"
        assert event.display == "Issue updated"
        assert event.author is not None
        assert event.date == datetime(
            2024,
            1,
            13,
            10,
            51,
            17,
            821000,
            tzinfo=timezone.utc,
        )
        change = event.changes[0]
        assert change.diff == "<added>User Name</added>"
        assert change.field is not None
        assert change.field.id == "teamUsers"
        assert change.field.display == "Participants"


# --- create_entity -----------------------------------------------------------


class TestCreateEntity:
    async def test_sends_post_with_fields(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity("project", "Название проекта")

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/v3/entities/project")
        assert call["params"] is None
        assert sent_json(call) == {"fields": {"summary": "Название проекта"}}

    async def test_values_and_kwargs_are_camel_cased(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity(
            "goal",
            "Goal",
            values={"entity_status": "at_risk"},
            team_users=["agent007"],
        )

        assert client.calls[0]["url"].endswith("/v3/entities/goal")
        assert sent_json(client.calls[0])["fields"] == {
            "summary": "Goal",
            "entityStatus": "at_risk",
            "teamUsers": ["agent007"],
        }

    async def test_dates_are_rendered(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity(
            "project",
            "Project",
            values={"start": date(2023, 11, 23)},
            end=datetime(2023, 11, 23, 11, 47, 49, 743000, tzinfo=timezone.utc),
        )

        fields = sent_json(client.calls[0])["fields"]
        assert fields["start"] == "2023-11-23"
        assert fields["end"] == "2023-11-23T11:47:49.743+0000"

    async def test_none_kwargs_are_dropped_and_values_kept(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity(
            "project",
            "Project",
            values={"lead": None},
            description=None,
        )

        assert sent_json(client.calls[0])["fields"] == {
            "summary": "Project",
            "lead": None,
        }

    async def test_links_accept_models_and_dicts(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity(
            "project",
            "Project",
            links=[
                EntityLink(relationship="works towards", entity="1234"),
                {"relationship": "parent entity", "entity": "5678"},
            ],
        )

        assert sent_json(client.calls[0])["links"] == [
            {"relationship": "works towards", "entity": "1234"},
            {"relationship": "parent entity", "entity": "5678"},
        ]

    async def test_no_links_key_without_links(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity("project", "Project")

        assert "links" not in sent_json(client.calls[0])

    async def test_fields_query_param_is_joined(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity(
            "project",
            "Project",
            fields=["summary", "entityStatus"],
        )

        assert client.calls[0]["params"] == {"fields": "summary,entityStatus"}

    async def test_fields_query_param_accepts_string(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity("project", "Project", fields="summary")

        assert client.calls[0]["params"] == {"fields": "summary"}

    async def test_unknown_entity_type_is_sent_as_is(self) -> None:
        # `EntityType` documents the kinds Tracker has today, but a kind
        # added later must not be rejected client-side.
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity("epic", "Project")  # type: ignore[arg-type]

        assert client.calls[0]["url"].endswith("/v3/entities/epic")

    async def test_links_must_be_a_sequence(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        link = EntityLink(relationship="works towards", entity="1234")
        for bare in (link, {"relationship": "works towards", "entity": "1234"}, "1234"):
            with pytest.raises(TypeError, match="sequence of links"):
                await tracker.create_entity("project", "Project", links=bare)  # type: ignore[arg-type]

        assert client.calls == []

    async def test_links_accept_any_collection(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        links = (EntityLink(relationship="works towards", entity="1234"),)
        await tracker.create_entity(
            "project",
            "Project",
            links=(link for link in links),
        )

        assert sent_json(client.calls[0])["links"] == [
            {"relationship": "works towards", "entity": "1234"},
        ]

    async def test_dates_inside_a_tuple_are_rendered(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        await tracker.create_entity(
            "project",
            "Project",
            values={
                "dates": (
                    datetime(2023, 11, 23, 10, 0, tzinfo=timezone.utc),
                    date(2023, 11, 24),
                ),
            },
        )

        assert sent_json(client.calls[0])["fields"]["dates"] == [
            "2023-11-23T10:00:00.000+0000",
            "2023-11-24",
        ]


# --- get_entity --------------------------------------------------------------


class TestGetEntity:
    async def test_sends_get(self) -> None:
        tracker, client = make_tracker(entity_payload())
        await tracker.get_entity("portfolio", 6)

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/v3/entities/portfolio/6")
        assert call["params"] is None

    async def test_fields_and_expand_params(self) -> None:
        tracker, client = make_tracker(entity_payload())
        await tracker.get_entity(
            "project",
            "1",
            fields=("summary", "author"),
            expand="attachments",
        )

        assert client.calls[0]["params"] == {
            "fields": "summary,author",
            "expand": "attachments",
        }


# --- update_entity -----------------------------------------------------------


class TestUpdateEntity:
    async def test_sends_patch_with_fields_and_comment(self) -> None:
        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity(
            "project",
            "1",
            values={"entity_status": "at_risk"},
            comment="Всё плохо",
        )

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/v3/entities/project/1")
        assert sent_json(call) == {
            "fields": {"entityStatus": "at_risk"},
            "comment": "Всё плохо",
        }

    async def test_comment_is_omitted_when_not_given(self) -> None:
        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity("project", "1", summary="New")

        assert sent_json(client.calls[0]) == {"fields": {"summary": "New"}}

    async def test_links_only_is_enough(self) -> None:
        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity(
            "project",
            "1",
            links=[EntityLink(relationship="is supported by", entity="42")],
        )

        assert sent_json(client.calls[0]) == {
            "links": [{"relationship": "is supported by", "entity": "42"}],
        }

    async def test_params(self) -> None:
        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity(
            "project",
            "1",
            summary="New",
            fields=["summary"],
            expand="attachments",
        )

        assert client.calls[0]["params"] == {
            "fields": "summary",
            "expand": "attachments",
        }

    async def test_nothing_to_change(self) -> None:
        tracker, client = make_tracker(entity_payload())
        with pytest.raises(ValueError, match="at least one field"):
            await tracker.update_entity("project", "1")

        assert client.calls == []


# --- delete_entity -----------------------------------------------------------


class TestDeleteEntity:
    async def test_sends_delete(self) -> None:
        tracker, client = make_tracker()
        result = await tracker.delete_entity("project", "1")

        call = client.calls[0]
        assert result is True
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/v3/entities/project/1")
        assert call["params"] is None

    @pytest.mark.parametrize(
        ("with_board", "expected"),
        [(True, "true"), (False, "false")],
    )
    async def test_with_board_param(self, with_board: bool, expected: str) -> None:  # noqa: FBT001
        tracker, client = make_tracker()
        await tracker.delete_entity("goal", "1", with_board=with_board)

        assert client.calls[0]["params"] == {"withBoard": expected}


# --- search_entities ---------------------------------------------------------


class TestSearchEntities:
    async def test_sends_post_to_search_url(self) -> None:
        tracker, client = make_tracker(search_payload())
        await tracker.search_entities("project")

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/v3/entities/project/_search")
        assert call["params"] is None
        assert sent_json(call) == {}

    async def test_full_body(self) -> None:
        tracker, client = make_tracker(search_payload())
        await tracker.search_entities(
            "project",
            query="Проект",
            filter_={"followers": "notEmpty()", "entity_status": "in_progress"},
            order_by="entityStatus",
            order_asc=True,
            root_only=False,
        )

        assert sent_json(client.calls[0]) == {
            "input": "Проект",
            "filter": {
                "followers": "notEmpty()",
                "entityStatus": "in_progress",
            },
            "orderBy": "entityStatus",
            "orderAsc": True,
            "rootOnly": False,
        }

    async def test_params(self) -> None:
        tracker, client = make_tracker(search_payload())
        await tracker.search_entities(
            "project",
            fields=["summary"],
            per_page=50,
            page=2,
        )

        assert client.calls[0]["params"] == {
            "fields": "summary",
            "perPage": "50",
            "page": "2",
        }


# --- iter_entities -----------------------------------------------------------


class TestIterEntities:
    async def test_pages_until_last_page(self) -> None:
        client = FakeClient(
            responses=[
                (200, search_body(pages=2), {}),
                (200, search_body(pages=2), {}),
            ],
        )
        tracker = YaTracker(client=client)

        entities = [entity async for entity in tracker.iter_entities("project")]

        assert len(entities) == 2
        assert [call["params"]["page"] for call in client.calls] == ["1", "2"]

    async def test_stops_on_empty_page(self) -> None:
        client = FakeClient(
            responses=[
                (200, search_body(pages=5), {}),
                (200, search_body(pages=5, values=[]), {}),
            ],
        )
        tracker = YaTracker(client=client)

        entities = [entity async for entity in tracker.iter_entities("project")]

        assert len(entities) == 1
        assert len(client.calls) == 2

    async def test_passes_filters_and_per_page(self) -> None:
        client = FakeClient(responses=[(200, search_body(), {})])
        tracker = YaTracker(client=client)

        entities = [
            entity
            async for entity in tracker.iter_entities(
                "goal",
                query="Цель",
                filter_={"entity_status": "at_risk"},
                per_page=10,
            )
        ]

        assert len(entities) == 1
        call = client.calls[0]
        assert call["url"].endswith("/v3/entities/goal/_search")
        assert call["params"] == {"perPage": "10", "page": "1"}
        assert sent_json(call) == {
            "input": "Цель",
            "filter": {"entityStatus": "at_risk"},
        }


# --- bulk_update_entities ----------------------------------------------------


class TestBulkUpdateEntities:
    async def test_sends_post_with_meta_entities(self) -> None:
        tracker, client = make_tracker(bulk_change_payload())
        entity = Entity.model_validate(CREATED_ENTITY)
        bulk_change = await tracker.bulk_update_entities(
            "project",
            ["id1", entity],
            values={"entity_status": "at_risk"},
            comment="Обновление",
            links=[{"relationship": "works towards", "entity": "1234"}],
            followers="agent007",
        )

        call = client.calls[0]
        assert isinstance(bulk_change, BulkChange)
        assert call["method"] == "POST"
        assert call["url"].endswith("/v3/entities/project/bulkchange/_update")
        assert sent_json(call) == {
            "metaEntities": ["id1", "655f3be523db2132"],
            "values": {
                "fields": {"entityStatus": "at_risk", "followers": "agent007"},
                "comment": "Обновление",
                "links": [{"relationship": "works towards", "entity": "1234"}],
            },
        }

    async def test_returned_bulk_change_can_wait(self) -> None:
        client = FakeClient(
            responses=[
                (200, bulk_change_body(), {}),
                (200, bulk_change_body(status="COMPLETE"), {}),
            ],
        )
        tracker = YaTracker(client=client)
        bulk_change = await tracker.bulk_update_entities(
            "project",
            ["id1"],
            values={"entityStatus": "at_risk"},
        )
        finished = await bulk_change.wait(interval=0.01)

        assert finished.is_complete is True
        assert client.calls[1]["url"].endswith(
            "/v3/bulkchange/1ab23cd4e5678901abcdef12"
        )

    async def test_bare_string_entities(self) -> None:
        # a bare id string would be iterated character by character
        tracker, client = make_tracker(bulk_change_payload())
        with pytest.raises(TypeError, match="sequence of entity ids"):
            await tracker.bulk_update_entities(
                "project",
                "655f3be523db2132",  # type: ignore[arg-type]
                entity_status="x",
            )
        assert client.calls == []

    async def test_bare_entity_or_mapping_entities(self) -> None:
        # pydantic models and dicts are iterable too, but a single one
        # of them is a bare value, not a collection of entities
        tracker, client = make_tracker(bulk_change_payload())
        entity = Entity.model_validate(CREATED_ENTITY)
        for bare in (entity, {"id": entity.id}):
            with pytest.raises(TypeError, match="sequence of entity ids"):
                await tracker.bulk_update_entities(
                    "project",
                    bare,  # type: ignore[arg-type]
                    entity_status="x",
                )
        assert client.calls == []

        assert client.calls == []

    async def test_empty_entities(self) -> None:
        tracker, client = make_tracker(bulk_change_payload())
        with pytest.raises(ValueError, match="At least one entity"):
            await tracker.bulk_update_entities("project", [], values={"a": 1})

        assert client.calls == []

    async def test_nothing_to_change(self) -> None:
        tracker, client = make_tracker(bulk_change_payload())
        with pytest.raises(ValueError, match="at least one field"):
            await tracker.bulk_update_entities("project", ["id1"])

        assert client.calls == []


# --- get_entity_events -------------------------------------------------------


class TestGetEntityEvents:
    async def test_sends_get(self) -> None:
        tracker, client = make_tracker(EVENTS)
        await tracker.get_entity_events("project", "1")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/v3/entities/project/1/events/_relative")
        assert call["params"] is None

    async def test_params(self) -> None:
        tracker, client = make_tracker(EVENTS)
        await tracker.get_entity_events(
            "project",
            "1",
            per_page=50,
            from_="6a4b",
            new_events_on_top=False,
            direction="forward",
        )

        assert client.calls[0]["params"] == {
            "perPage": "50",
            "from": "6a4b",
            "newEventsOnTop": "false",
            "direction": "forward",
        }

    async def test_selected_param(self) -> None:
        tracker, client = make_tracker(EVENTS)
        await tracker.get_entity_events("project", "1", selected="6a4b")

        assert client.calls[0]["params"] == {"selected": "6a4b"}

    async def test_from_and_selected_are_exclusive(self) -> None:
        tracker, client = make_tracker(EVENTS)
        with pytest.raises(ValueError, match="not both"):
            await tracker.get_entity_events(
                "project",
                "1",
                from_="1",
                selected="2",
            )

        assert client.calls == []


# --- model shortcuts ---------------------------------------------------------


class TestEntityShortcuts:
    async def test_refresh(self) -> None:
        client = FakeClient(
            responses=[
                (200, entity_body(), {}),
                (200, entity_body(version=2), {}),
            ],
        )
        tracker = YaTracker(client=client)
        entity = await tracker.get_entity("project", "655f3be523db2132")
        refreshed = await entity.refresh(fields=["summary"])

        assert refreshed.version == 2
        call = client.calls[1]
        assert call["method"] == "GET"
        assert call["url"].endswith("/v3/entities/project/655f3be523db2132")
        assert call["params"] == {"fields": "summary"}

    async def test_update(self) -> None:
        client = FakeClient(
            responses=[
                (200, entity_body(), {}),
                (200, entity_body(version=2), {}),
            ],
        )
        tracker = YaTracker(client=client)
        entity = await tracker.get_entity("project", "655f3be523db2132")
        updated = await entity.update(entity_status="at_risk", comment="ok")

        assert updated.version == 2
        call = client.calls[1]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/v3/entities/project/655f3be523db2132")
        assert sent_json(call) == {
            "fields": {"entityStatus": "at_risk"},
            "comment": "ok",
        }

    async def test_delete(self) -> None:
        client = FakeClient(
            responses=[(200, entity_body(), {}), (200, b"{}", {})],
        )
        tracker = YaTracker(client=client)
        entity = await tracker.get_entity("project", "655f3be523db2132")
        result = await entity.delete(with_board=True)

        assert result is True
        call = client.calls[1]
        assert call["method"] == "DELETE"
        assert call["params"] == {"withBoard": "true"}

    async def test_get_events(self) -> None:
        client = FakeClient(
            responses=[
                (200, entity_body(), {}),
                (200, json.dumps(EVENTS).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        entity = await tracker.get_entity("project", "655f3be523db2132")
        events = await entity.get_events(per_page=10, from_="e1")

        assert events.has_next is True
        call = client.calls[1]
        assert call["url"].endswith(
            "/v3/entities/project/655f3be523db2132/events/_relative",
        )
        assert call["params"] == {"perPage": "10", "from": "e1"}

    async def test_get_events_forwards_every_parameter(self) -> None:
        client = FakeClient(
            responses=[
                (200, entity_body(), {}),
                (200, json.dumps(EVENTS).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        entity = await tracker.get_entity("project", "655f3be523db2132")
        await entity.get_events(
            per_page=5,
            selected="e2",
            new_events_on_top=True,
            direction="backward",
        )

        assert client.calls[1]["params"] == {
            "perPage": "5",
            "selected": "e2",
            "newEventsOnTop": "true",
            "direction": "backward",
        }

    async def test_get_events_from_and_selected_are_exclusive(self) -> None:
        client = FakeClient(responses=[(200, entity_body(), {})])
        tracker = YaTracker(client=client)
        entity = await tracker.get_entity("project", "655f3be523db2132")

        with pytest.raises(ValueError, match="not both"):
            await entity.get_events(from_="e1", selected="e2")

        assert len(client.calls) == 1


# --- set rendering -----------------------------------------------------------


class TestSetFieldRendering:
    """A set has no order of its own, so it is sorted before it is sent.

    Iteration order depends on `PYTHONHASHSEED`, which would make the
    request body differ between runs; `_convert_value` in
    `yatracker.tracker.base` sorts sets for the same reason.
    """

    async def test_a_top_level_set_is_sorted(self) -> None:
        tags = {"gamma", "alpha", "delta", "beta"}
        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity("project", "1", values={"tags": tags})

        assert sent_json(client.calls[0])["fields"]["tags"] == sorted(tags)

    async def test_a_nested_frozenset_is_sorted(self) -> None:
        tags = frozenset({"gamma", "alpha", "delta", "beta"})
        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity("project", "1", tags={"add": tags})

        assert sent_json(client.calls[0])["fields"]["tags"]["add"] == sorted(tags)

    async def test_a_set_of_kwargs_is_sorted_too(self) -> None:
        queues = {30, 10, 20}
        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity("project", "1", issue_queues=queues)

        assert sent_json(client.calls[0])["fields"]["issueQueues"] == sorted(queues)

    async def test_an_unsortable_set_is_kept_as_is(self) -> None:
        # `sorted` raises `TypeError` on mixed types; the values must
        # still reach the body, in whatever order the set yields them
        values = {"a", 1}
        tracker, client = make_tracker(entity_payload())
        await tracker.update_entity("project", "1", values={"tags": values})

        assert sorted(
            sent_json(client.calls[0])["fields"]["tags"],
            key=repr,
        ) == sorted(values, key=repr)


# --- naive datetime warning --------------------------------------------------

NAIVE = datetime(2023, 11, 23, 10, 0)  # noqa: DTZ001
AWARE = datetime(2023, 11, 23, 10, 0, tzinfo=timezone.utc)


def _emit_unrelated() -> None:
    """Warn from a fixed location, so a `default` filter can dedupe it."""
    warnings.warn("unrelated", DeprecationWarning, stacklevel=1)


class TestNaiveDatetimeWarning:
    """The warning must point at the user's call, not at a library frame."""

    async def test_flat_value_is_attributed_to_the_caller(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        with pytest.warns(UserWarning, match="Timezone-Aware") as record:
            await tracker.create_entity("project", "P", values={"start": NAIVE})

        assert len(record) == 1
        assert record[0].filename == __file__
        assert sent_json(client.calls[0])["fields"]["start"] == (
            "2023-11-23T10:00:00.000"
        )

    async def test_keyword_value_is_attributed_to_the_caller(self) -> None:
        tracker, _ = make_tracker(CREATED_ENTITY)
        with pytest.warns(UserWarning, match="Timezone-Aware") as record:
            await tracker.create_entity("project", "P", start=NAIVE)

        assert len(record) == 1
        assert record[0].filename == __file__

    async def test_nested_value_is_attributed_to_the_caller(self) -> None:
        tracker, _ = make_tracker(CREATED_ENTITY)
        with pytest.warns(UserWarning, match="Timezone-Aware") as record:
            await tracker.create_entity(
                "project",
                "P",
                values={"deadline": {"date": NAIVE}},
            )

        assert len(record) == 1
        assert record[0].filename == __file__

    async def test_warns_once_per_request(self) -> None:
        tracker, _ = make_tracker(entity_payload())
        with pytest.warns(UserWarning, match="Timezone-Aware") as record:
            await tracker.update_entity(
                "project",
                "1",
                values={"start": NAIVE, "dates": [NAIVE, NAIVE]},
                end=NAIVE,
            )

        assert len(record) == 1
        assert record[0].filename == __file__

    async def test_a_bare_value_and_a_model_warn_once_together(self) -> None:
        """The walk finds the bare value, the model warns while rendering."""
        tracker, client = make_tracker(entity_payload())
        with pytest.warns(UserWarning, match="Timezone-Aware") as record:
            await tracker.update_entity(
                "project",
                "1",
                values={
                    "start": NAIVE,
                    "checklistItems": [
                        EntityChecklistItem(
                            id="1", deadline=EntityDeadline(date=NAIVE)
                        ),
                    ],
                },
            )

        assert len(record) == 1
        assert record[0].filename == __file__
        fields = sent_json(client.calls[0])["fields"]
        assert fields["start"] == "2023-11-23T10:00:00.000"
        assert fields["checklistItems"][0]["deadline"] == {
            "date": "2023-11-23T10:00:00.000",
            "deadlineType": "date",
        }

    async def test_a_model_alone_still_warns_once(self) -> None:
        tracker, _ = make_tracker(entity_payload())
        with pytest.warns(UserWarning, match="Timezone-Aware") as record:
            await tracker.update_entity(
                "project",
                "1",
                values={
                    "checklistItems": [
                        EntityChecklistItem(
                            id="1", deadline=EntityDeadline(date=NAIVE)
                        ),
                    ],
                },
            )

        assert len(record) == 1
        assert record[0].filename == __file__

    async def test_search_filter_is_attributed_to_the_caller(self) -> None:
        tracker, _ = make_tracker(search_payload())
        with pytest.warns(UserWarning, match="Timezone-Aware") as record:
            await tracker.search_entities("project", filter_={"start": NAIVE})

        assert len(record) == 1
        assert record[0].filename == __file__

    async def test_iter_filter_is_attributed_to_the_caller(self) -> None:
        # `iter_entities` delegates to `search_entities`, adding a frame
        # that the warning must still look past
        tracker, _ = make_tracker(search_payload())
        pages = tracker.iter_entities("project", filter_={"start": NAIVE})
        with pytest.warns(UserWarning, match="Timezone-Aware") as record:
            await anext(pages)
        await pages.aclose()

        assert record[0].filename == __file__

    async def test_an_unrelated_warning_is_still_deduplicated(self) -> None:
        # rendering used to run inside `warnings.catch_warnings`, which
        # bumps the filters version and thereby resets the
        # `__warningregistry__` of every module: a `default` filter then
        # stopped deduplicating in the caller's own code
        tracker, _ = make_tracker(entity_payload())

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("default")
            _emit_unrelated()
            await tracker.update_entity("project", "1", values={"start": AWARE})
            _emit_unrelated()

        assert [str(warning.message) for warning in caught] == ["unrelated"]

    async def test_aware_datetime_does_not_warn(self) -> None:
        tracker, client = make_tracker(CREATED_ENTITY)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await tracker.create_entity(
                "project",
                "P",
                values={"start": AWARE, "dates": (AWARE,)},
                end=AWARE,
            )

        assert sent_json(client.calls[0])["fields"]["start"] == (
            "2023-11-23T10:00:00.000+0000"
        )
