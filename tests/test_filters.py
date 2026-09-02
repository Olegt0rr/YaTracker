"""Tests for the filters category and the `Filter` struct.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/filters/create-filter
https://yandex.ru/support/tracker/ru/api/filters/get-filter
https://yandex.ru/support/tracker/ru/api/filters/update-filter
"""

from __future__ import annotations

from typing import Any

import pytest
from yatracker.types.filter import Filter, FilterSort
from yatracker.types.ref import FieldRef

from tests.conftest import make_tracker, sent_json

BASE = "https://api.tracker.yandex.net/v3"

# POST /v3/filters/ response sample.
CREATE_FILTER_RESPONSE: dict[str, Any] = {
    "id": 12345,
    "self": "https://api.tracker.yandex.net/v3/filters/12345",
    "name": "Мои открытые задачи",
    "filter": {
        "assignee": "me()",
        "status": "open",
    },
    "favorite": False,
    "permissions": {
        "READ": {
            "users": [],
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/5",
                    "id": "5",
                    "display": "Все сотрудники",
                },
            ],
            "roles": [],
        },
        "WRITE": {
            "users": [
                {
                    "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                    "id": "1234567890",
                    "display": "Имя Фамилия",
                    "cloudUid": "ajevuhegoiuhfasjhiu",
                    "passportUid": 1234567890,
                },
            ],
            "groups": [],
            "roles": [],
        },
    },
    "owner": {
        "self": "https://api.tracker.yandex.net/v3/users/1234567890",
        "id": "1234567890",
        "display": "Имя Фамилия",
        "cloudUid": "ajevuhegoiuhfasjhiu",
        "passportUid": 1234567890,
    },
}

# GET /v3/filters/<id> response sample.
GET_FILTER_RESPONSE: dict[str, Any] = {
    "id": 12345,
    "self": "https://api.tracker.yandex.net/v3/filters/12345",
    "name": "Мои открытые задачи",
    "filter": {
        "assignee": "me()",
        "status": "open",
    },
    "fields": [
        {
            "self": "https://api.tracker.yandex.net/v3/fields/key",
            "id": "key",
            "display": "Ключ",
        },
        {
            "self": "https://api.tracker.yandex.net/v3/fields/summary",
            "id": "summary",
            "display": "Задача",
        },
        {
            "self": "https://api.tracker.yandex.net/v3/fields/status",
            "id": "status",
            "display": "Статус",
        },
    ],
    "groupBy": {
        "self": "https://api.tracker.yandex.net/v3/fields/status",
        "id": "status",
        "display": "Статус",
    },
    "favorite": False,
    "permissions": {
        "READ": {
            "users": [],
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/5",
                    "id": "5",
                    "display": "Все сотрудники",
                },
            ],
            "roles": [],
        },
        "WRITE": {
            "users": [
                {
                    "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                    "id": "1234567890",
                    "display": "Имя Фамилия",
                    "cloudUid": "ajevuhegoiuhfasjhiu",
                    "passportUid": 1234567890,
                },
            ],
            "groups": [],
            "roles": [],
        },
    },
    "owner": {
        "self": "https://api.tracker.yandex.net/v3/users/1234567890",
        "id": "1234567890",
        "display": "Имя Фамилия",
        "cloudUid": "ajevuhegoiuhfasjhiu",
        "passportUid": 1234567890,
    },
}

# PATCH /v3/filters/<id> response sample (sort by field object).
UPDATE_FILTER_RESPONSE: dict[str, Any] = {
    "id": 12345,
    "self": "https://api.tracker.yandex.net/v3/filters/12345",
    "name": "Новое название фильтра",
    "filter": {
        "assignee": "me()",
        "status": "open",
    },
    "sorts": [
        {
            "field": {
                "self": "https://api.tracker.yandex.net/v3/fields/priority",
                "id": "priority",
                "display": "Приоритет",
            },
            "isAscending": False,
        },
    ],
    "favorite": False,
    "permissions": {
        "WRITE": {
            "users": [
                {
                    "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                    "id": "1234567890",
                    "display": "Имя Фамилия",
                    "cloudUid": "ajevuhegoiuhfasjhiu",
                    "passportUid": 1234567890,
                },
            ],
            "groups": [],
            "roles": [],
        },
        "READ": {
            "users": [],
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/5",
                    "id": "5",
                    "display": "Все сотрудники",
                },
            ],
            "roles": [],
        },
    },
    "owner": {
        "self": "https://api.tracker.yandex.net/v3/users/1234567890",
        "id": "1234567890",
        "display": "Имя Фамилия",
        "cloudUid": "ajevuhegoiuhfasjhiu",
        "passportUid": 1234567890,
    },
}


# --- create_filter ----------------------------------------------------------


async def test_create_filter_sends_minimal_body() -> None:
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE, status=201)
    filter_ = await tracker.create_filter("Мои открытые задачи")

    assert isinstance(filter_, Filter)
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/filters/"
    assert sent_json(call) == {"name": "Мои открытые задачи"}


async def test_create_filter_sends_filter_conditions() -> None:
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE, status=201)
    await tracker.create_filter(
        "Мои открытые задачи",
        filter_={"status": "open", "assignee": "me()"},
    )

    assert sent_json(client.calls[0]) == {
        "name": "Мои открытые задачи",
        "filter": {"status": "open", "assignee": "me()"},
    }


async def test_create_filter_sends_query_fields_sorts_dict_form() -> None:
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE, status=201)
    await tracker.create_filter(
        "Открытые задачи",
        query="Status: Open",
        fields=["key", "summary", "status"],
        sorts=[{"field": "created", "isAscending": False}],
        group_by="status",
        folder="My folder",
    )

    assert sent_json(client.calls[0]) == {
        "name": "Открытые задачи",
        "query": "Status: Open",
        "fields": ["key", "summary", "status"],
        "sorts": [{"field": "created", "isAscending": False}],
        "groupBy": "status",
        "folder": "My folder",
    }


async def test_create_filter_encodes_filtersort_objects() -> None:
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE, status=201)
    sort = FilterSort(
        field=FieldRef(url="f", id="priority", display="Приоритет"),
        is_ascending=False,
    )
    await tracker.create_filter("Test", sorts=[sort])

    assert sent_json(client.calls[0])["sorts"] == [
        {"field": "priority", "isAscending": False},
    ]


async def test_create_filter_sort_without_is_ascending_omits_key() -> None:
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE, status=201)
    sort = FilterSort(field=FieldRef(url="f", id="created"))
    await tracker.create_filter("Test", sorts=[sort])

    assert sent_json(client.calls[0])["sorts"] == [{"field": "created"}]


async def test_create_filter_group_by_and_folder_as_dict() -> None:
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE, status=201)
    await tracker.create_filter(
        "Test",
        group_by={"id": "status"},
        folder={"id": "42"},
    )

    payload = sent_json(client.calls[0])
    assert payload["groupBy"] == {"id": "status"}
    assert payload["folder"] == {"id": "42"}


async def test_create_filter_passes_kwargs() -> None:
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE, status=201)
    await tracker.create_filter("Test", custom_field="value")

    assert sent_json(client.calls[0])["customField"] == "value"


async def test_create_filter_decodes_response() -> None:
    tracker, _ = make_tracker(CREATE_FILTER_RESPONSE, status=201)
    filter_ = await tracker.create_filter("Мои открытые задачи")

    assert filter_.id == "12345"
    assert filter_.url == "https://api.tracker.yandex.net/v3/filters/12345"
    assert filter_.name == "Мои открытые задачи"
    assert filter_.filter_ == {"assignee": "me()", "status": "open"}
    assert filter_.query is None
    assert filter_.favorite is False
    assert filter_.permissions is not None
    assert filter_.permissions.read is not None
    assert filter_.permissions.read.groups[0].display == "Все сотрудники"
    assert filter_.permissions.write is not None
    assert filter_.permissions.write.users[0].id == "1234567890"
    assert filter_.owner is not None
    assert filter_.owner.display == "Имя Фамилия"


# --- get_filter ---------------------------------------------------------


async def test_get_filter_request() -> None:
    tracker, client = make_tracker(GET_FILTER_RESPONSE)
    filter_ = await tracker.get_filter(12345)

    assert isinstance(filter_, Filter)
    call = client.calls[0]
    assert call["method"] == "GET"
    assert call["url"] == f"{BASE}/filters/12345"
    assert call["params"] is None


async def test_get_filter_decodes_fields_and_group_by() -> None:
    tracker, _ = make_tracker(GET_FILTER_RESPONSE)
    filter_ = await tracker.get_filter(12345)

    assert filter_.fields is not None
    assert [f.id for f in filter_.fields] == ["key", "summary", "status"]
    assert filter_.fields[0].display == "Ключ"
    assert filter_.group_by is not None
    assert filter_.group_by.id == "status"
    assert filter_.group_by.display == "Статус"


# --- update_filter ----------------------------------------------------------


async def test_update_filter_sends_partial_body() -> None:
    tracker, client = make_tracker(UPDATE_FILTER_RESPONSE)
    filter_ = await tracker.update_filter(12345, name="Новое название фильтра")

    assert isinstance(filter_, Filter)
    call = client.calls[0]
    assert call["method"] == "PATCH"
    assert call["url"] == f"{BASE}/filters/12345"
    payload = sent_json(call)
    assert payload == {"name": "Новое название фильтра"}
    assert "filterId" not in payload
    assert "filter_id" not in payload


async def test_update_filter_replaces_filter_conditions_fully() -> None:
    tracker, client = make_tracker(UPDATE_FILTER_RESPONSE)
    await tracker.update_filter(
        12345,
        filter_={"priority": "critical", "assignee": "me()"},
    )

    assert sent_json(client.calls[0]) == {
        "filter": {"priority": "critical", "assignee": "me()"},
    }


async def test_update_filter_sorts_dict_form() -> None:
    tracker, client = make_tracker(UPDATE_FILTER_RESPONSE)
    await tracker.update_filter(
        12345,
        sorts=[{"field": "priority", "isAscending": False}],
    )

    assert sent_json(client.calls[0]) == {
        "sorts": [{"field": "priority", "isAscending": False}],
    }


async def test_update_filter_sorts_filtersort_round_trip() -> None:
    """A `FilterSort` from a previous response can be re-sent as is."""
    tracker, _ = make_tracker(GET_FILTER_RESPONSE)
    filter_ = await tracker.get_filter(12345)
    assert filter_.group_by is not None
    sort = FilterSort(field=filter_.group_by, is_ascending=True)

    tracker2, client2 = make_tracker(UPDATE_FILTER_RESPONSE)
    await tracker2.update_filter(12345, sorts=[sort])

    assert sent_json(client2.calls[0])["sorts"] == [
        {"field": "status", "isAscending": True},
    ]


async def test_update_filter_decodes_sorts_field_object() -> None:
    tracker, _ = make_tracker(UPDATE_FILTER_RESPONSE)
    filter_ = await tracker.update_filter(12345, name="x")

    assert filter_.sorts is not None
    assert filter_.sorts[0].field.id == "priority"
    assert filter_.sorts[0].field.display == "Приоритет"
    assert filter_.sorts[0].is_ascending is False


async def test_create_filter_rejects_a_bare_sort() -> None:
    """A single rule (a dict or a `FilterSort`) would be iterated key by key."""
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE)
    with pytest.raises(TypeError, match="sequence of sorting rules"):
        await tracker.create_filter(
            "Test",
            sorts={"field": "created"},  # type: ignore[arg-type]
        )

    assert client.calls == []


async def test_update_filter_rejects_a_bare_filter_sort_model() -> None:
    tracker, client = make_tracker(UPDATE_FILTER_RESPONSE)
    sort = FilterSort(field=FieldRef(self="s", id="created"), is_ascending=True)
    with pytest.raises(TypeError, match="sequence of sorting rules"):
        await tracker.update_filter(12345, sorts=sort)  # type: ignore[arg-type]

    assert client.calls == []


async def test_create_filter_splits_a_comma_separated_fields_string() -> None:
    """The API wants an array; a string must not go out as a JSON string."""
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE)
    await tracker.create_filter("Test", fields="key, summary ,status")

    assert sent_json(client.calls[0])["fields"] == ["key", "summary", "status"]


async def test_update_filter_splits_a_comma_separated_fields_string() -> None:
    tracker, client = make_tracker(UPDATE_FILTER_RESPONSE)
    await tracker.update_filter(12345, fields="key,summary")

    assert sent_json(client.calls[0])["fields"] == ["key", "summary"]


async def test_create_filter_accepts_a_tuple_of_fields() -> None:
    tracker, client = make_tracker(CREATE_FILTER_RESPONSE)
    await tracker.create_filter("Test", fields=("key", "summary"))

    assert sent_json(client.calls[0])["fields"] == ["key", "summary"]
