"""Tests for the issue-fields category and its structs.

Global fields, field categories and local queue fields. Payloads are taken
verbatim from the official documentation:
https://yandex.ru/support/tracker/ru/api/issues/get-global-fields
https://yandex.ru/support/tracker/ru/api/issues/get-issue-fields
https://yandex.ru/support/tracker/ru/api/issues/create-field
https://yandex.ru/support/tracker/ru/api/issues/patch-issue-field-name
https://yandex.ru/support/tracker/ru/api/issues/patch-issue-field-value
https://yandex.ru/support/tracker/ru/api/issues/create-issue-field-category
https://yandex.ru/support/tracker/ru/api/issues/patch-issue-field-category
https://yandex.ru/support/tracker/ru/api/queues/get-local-fields
https://yandex.ru/support/tracker/ru/api/queues/get-info-local-field
https://yandex.ru/support/tracker/ru/api/queues/create-local-field
https://yandex.ru/support/tracker/ru/api/queues/edit-local-field
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import TypeAdapter
from yatracker import YaTracker
from yatracker.types.issue_field import IssueField
from yatracker.types.local_field import LocalField
from yatracker.types.localized_name import LocalizedName
from yatracker.types.queue_field import QueueField
from yatracker.types.queue_field_options_provider import (
    QueueFieldOptionsProvider,
)

from tests.conftest import FakeClient, make_tracker, sent_json
from tests.test_queues import QUEUE_FIELD

# `GET /fields` response shape (one element of the array).
GLOBAL_FIELD: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/fields/standard_field_key",
    "id": "standard_field_key",
    "name": "standard_field_name",
    "key": "standard_field_key",
    "version": 0,
    "schema": {"type": "string", "required": True},
    "readonly": True,
    "options": True,
    "suggest": True,
    "suggestProvider": {"type": "QueueSuggestProvider"},
    "optionsProvider": {"type": "QueueOptionsProvider"},
    "queryProvider": {"type": "QueueQueryProvider"},
    "order": 1,
    "category": {
        "self": "https://api.tracker.yandex.net/v3/fields/categories/0000000000000001********",
        "id": "0000000000000001********",
        "display": "Системные",
    },
    "type": "standard",
}

# `GET /fields/{id}` response shape: no `key`, no `type`.
ISSUE_FIELD: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/fields/ruName",
    "id": "ruName",
    "name": "Field name",
    "description": "Field description",
    "version": 3,
    "schema": {"type": "array", "items": "string", "required": False},
    "readonly": False,
    "options": True,
    "suggest": True,
    "suggestProvider": {"type": "UserSuggestProvider"},
    "optionsProvider": {
        "type": "FixedListOptionsProvider",
        "values": ["Value 1", "Value 2"],
    },
    "queryProvider": {"type": "StringOptionalQueryProvider"},
    "order": 14,
    "category": {
        "self": "https://api.tracker.yandex.net/v3/fields/categories/58bc3b921d9c********",
        "id": "58bc3b921d9c********",
        "display": "Системные",
    },
}

# `POST /fields` response shape (also reused for the update-field tests,
# whose responses share this exact shape per the docs).
CREATED_FIELD: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/fields/global_field_key",
    "id": "global_field_key",
    "name": "Field name",
    "description": "Field description",
    "key": "global_field_key",
    "version": 1,
    "schema": {"type": "array", "items": "string", "required": False},
    "readonly": False,
    "options": True,
    "suggest": False,
    "optionsProvider": {
        "type": "FixedListOptionsProvider",
        "needValidation": True,
        "values": ["First item", "Second item", "Third item"],
    },
    "queryProvider": {"type": "StringOptionalQueryProvider"},
    "order": 5,
    "category": {
        "self": "https://api.tracker.yandex.net/v3/fields/categories/0000000000000001********",
        "id": "0000000000000001********",
        "display": "Системные",
    },
    "type": "standard",
}

# `POST /fields/categories` response shape.
CREATED_CATEGORY: dict[str, Any] = {
    "id": "604f9920d23cd5********",
    "name": "category_name",
    "self": "https://api.tracker.yandex.net/v3/fields/categories/604f9920d23cd5********",
    "version": 1,
}

# `GET /fields/categories` has no page of its own in the reference; the
# listing is assumed to answer with the objects of the create/patch pages,
# so the first entry is `CREATED_CATEGORY` verbatim and the second one adds
# the `order`/`description` of the request bodies.
FIELD_CATEGORIES: list[dict[str, Any]] = [
    {
        "id": "604f9920d23cd5********",
        "name": "category_name",
        "self": (
            "https://api.tracker.yandex.net/v3/fields/categories/604f9920d23cd5********"
        ),
        "version": 1,
    },
    {
        "id": "58bc3b921d9c********",
        "name": "Системные",
        "self": (
            "https://api.tracker.yandex.net/v3/fields/categories/58bc3b921d9c********"
        ),
        "version": 2,
        "order": 400,
        "description": "Текстовое описание",
    },
]

# `PATCH /fields/categories/{id}` response shape.
UPDATED_CATEGORY: dict[str, Any] = {
    "id": "604f9920d23cd5********",
    "name": "category_name",
    "self": "https://api.tracker.yandex.net/v3/fields/categories/604f9920d23cd5********",
    "version": 2,
}

# `GET /queues/{id}/localFields` response shape (one element of the array).
LOCAL_FIELD: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/queues/ORG/localFields/loc_field_key",
    "id": "6054ae3a2b6b2c7f********--loc_field_key",
    "name": "loc_field_name",
    "description": "Field description",
    "key": "loc_field_key",
    "version": 1,
    "schema": {"type": "string", "required": False},
    "readonly": False,
    "options": False,
    "suggest": False,
    "optionsProvider": {
        "type": "FixedListOptionsProvider",
        "needValidation": True,
        "values": ["First item", "Second item", "Third item"],
    },
    "queryProvider": {"type": "StringOptionalQueryProvider"},
    "order": 3,
    "category": {
        "self": "https://api.tracker.yandex.net/v3/fields/categories/0000000000000001********",
        "id": "0000000000000001********",
        "display": "Системные",
    },
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/ORG",
        "id": "1",
        "key": "ORG",
        "display": "My queue",
    },
    "type": "local",
}

# `GET /queues/{id}/localFields/{key}` response shape (same fields, `type`
# is listed first in the docs -- order must not matter).
LOCAL_FIELD_INFO: dict[str, Any] = {
    "type": "local",
    "self": "https://api.tracker.yandex.net/v3/queues/ORG/localFields/loc_field_key",
    "id": "6054ae3a2b6b2c7f********--loc_field_key",
    "name": "loc_field_name",
    "description": "Local field description",
    "key": "loc_field_key",
    "version": 1,
    "schema": {"type": "string", "required": False},
    "readonly": True,
    "options": True,
    "suggest": False,
    "optionsProvider": {
        "type": "FixedListOptionsProvider",
        "needValidation": True,
        "values": ["First item", "Second item", "Third item"],
    },
    "queryProvider": {"type": "StringOptionalQueryProvider"},
    "order": 3,
    "category": {
        "self": "https://api.tracker.yandex.net/v3/fields/categories/0000000000000001********",
        "id": "0000000000000001********",
        "display": "Системные",
    },
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/ORG",
        "id": "1",
        "key": "ORG",
        "display": "My queue",
    },
}

# `POST /queues/{id}/localFields` response shape: notably no `queue` key.
CREATED_LOCAL_FIELD: dict[str, Any] = {
    "type": "local",
    "self": "https://api.tracker.yandex.net/v3/queues/ORG/localFields/loc_field_key",
    "id": "6054ae3a2b6b2c7f********--loc_field_key",
    "name": "Field name",
    "description": "Field description",
    "key": "loc_field_key",
    "version": 1,
    "schema": {"type": "string", "required": False},
    "readonly": True,
    "options": False,
    "suggest": False,
    "queryProvider": {"type": "StringOptionalQueryProvider"},
    "order": 100,
    "category": {
        "self": "https://api.tracker.yandex.net/v3/fields/categories/0000000000000003********",
        "id": "0000000000000003********",
        "display": "Системные",
    },
}

# `PATCH /queues/{id}/localFields/{key}` response shape.
UPDATED_LOCAL_FIELD: dict[str, Any] = {
    "type": "local",
    "self": "https://api.tracker.yandex.net/v3/queues/ORG/localFields/loc_field_key",
    "id": "6054ae3a2b6b2c7f********--loc_field_key",
    "name": "Field name",
    "description": "Field description",
    "key": "loc_field_key",
    "version": 2,
    "schema": {"type": "string", "required": False},
    "readonly": True,
    "options": True,
    "suggest": False,
    "optionsProvider": {
        "type": "FixedListOptionsProvider",
        "needValidation": True,
        "values": ["First item", "Second item", "Third item"],
    },
    "queryProvider": {"type": "StringOptionalQueryProvider"},
    "order": 102,
    "category": {
        "self": "https://api.tracker.yandex.net/v3/fields/categories/0000000000000002********",
        "id": "0000000000000002********",
        "display": "Системные",
    },
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/ORG",
        "id": "1",
        "key": "ORG",
        "display": "My queue",
    },
}


class TestIssueFieldDecoding:
    def test_global_field_decodes(self) -> None:
        field = TypeAdapter(IssueField).validate_json(json.dumps(GLOBAL_FIELD))
        assert field.id == "standard_field_key"
        assert field.key == "standard_field_key"
        assert field.name == "standard_field_name"
        assert field.version == 0
        assert field.field_schema.type == "string"
        assert field.field_schema.required is True
        assert field.readonly is True
        assert field.options is True
        assert field.suggest is True
        assert field.suggest_provider is not None
        assert field.suggest_provider.type == "QueueSuggestProvider"
        assert field.options_provider is not None
        assert field.options_provider.type == "QueueOptionsProvider"
        assert field.query_provider is not None
        assert field.query_provider.type == "QueueQueryProvider"
        assert field.order == 1
        assert field.category is not None
        assert field.category.id == "0000000000000001********"
        assert field.category.display == "Системные"
        assert field.type == "standard"

    def test_issue_field_decodes_without_key_and_type(self) -> None:
        """`GET /fields/{id}` omits `key` and `type`; both stay unset."""
        field = TypeAdapter(IssueField).validate_json(json.dumps(ISSUE_FIELD))
        assert field.id == "ruName"
        assert field.key is None
        assert field.type is None
        assert field.description == "Field description"
        assert field.version == 3
        assert field.field_schema.type == "array"
        assert field.field_schema.items == "string"
        assert field.options_provider is not None
        assert field.options_provider.values == ["Value 1", "Value 2"]
        assert field.options_provider.need_validation is None


class TestGlobalFieldEndpoints:
    async def test_get_global_fields(self) -> None:
        tracker, client = make_tracker([GLOBAL_FIELD])
        fields = await tracker.get_global_fields()
        assert len(fields) == 1
        assert fields[0].id == "standard_field_key"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/fields")

    async def test_get_field(self) -> None:
        tracker, client = make_tracker(ISSUE_FIELD)
        field = await tracker.get_field("ruName")
        assert field.name == "Field name"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/fields/ruName")

    async def test_create_field_sends_id_and_type_keys(self) -> None:
        tracker, client = make_tracker(CREATED_FIELD, status=201)
        field = await tracker.create_field(
            LocalizedName(
                en="Название на английском языке",
                ru="Название на русском языке",
            ),
            "global_field_key",
            "0000000000000001********",
            "ru.yandex.startrek.core.fields.StringFieldType",
        )
        assert field.id == "global_field_key"
        assert field.options_provider is not None
        assert field.options_provider.need_validation is True

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/fields")
        assert sent_json(call) == {
            "name": {
                "en": "Название на английском языке",
                "ru": "Название на русском языке",
            },
            "id": "global_field_key",
            "category": "0000000000000001********",
            "type": "ru.yandex.startrek.core.fields.StringFieldType",
        }

    async def test_create_field_with_options_provider_and_plain_dict_name(
        self,
    ) -> None:
        """`name` also accepts a plain dict, not only `LocalizedName`."""
        tracker, client = make_tracker(CREATED_FIELD, status=201)
        await tracker.create_field(
            {"en": "Название на английском языке", "ru": "Название на русском языке"},
            "myglobalfield",
            "0000000000000003********",
            "ru.yandex.startrek.core.fields.StringFieldType",
            options_provider={
                "type": "FixedListOptionsProvider",
                "values": [
                    "первый элемент списка",
                    "второй элемент списка",
                    "третий элемент списка",
                ],
            },
        )

        call = client.calls[0]
        assert sent_json(call) == {
            "name": {
                "en": "Название на английском языке",
                "ru": "Название на русском языке",
            },
            "id": "myglobalfield",
            "category": "0000000000000003********",
            "type": "ru.yandex.startrek.core.fields.StringFieldType",
            "optionsProvider": {
                "type": "FixedListOptionsProvider",
                "values": [
                    "первый элемент списка",
                    "второй элемент списка",
                    "третий элемент списка",
                ],
            },
        }

    async def test_create_field_localized_name_drops_unset_language(self) -> None:
        """A `LocalizedName` with only one language sends only that key."""
        tracker, client = make_tracker(CREATED_FIELD, status=201)
        await tracker.create_field(
            LocalizedName(en="English only"),
            "global_field_key",
            "0000000000000001********",
            "ru.yandex.startrek.core.fields.StringFieldType",
        )

        assert sent_json(client.calls[0])["name"] == {"en": "English only"}

    async def test_create_field_omits_unset_optional_fields(self) -> None:
        tracker, client = make_tracker(CREATED_FIELD, status=201)
        await tracker.create_field(
            LocalizedName(en="Name", ru="Название"),
            "global_field_key",
            "0000000000000001********",
            "ru.yandex.startrek.core.fields.StringFieldType",
        )

        body = sent_json(client.calls[0])
        for key in (
            "optionsProvider",
            "order",
            "description",
            "readonly",
            "visible",
            "hidden",
            "container",
        ):
            assert key not in body

    async def test_update_field_name_sends_version_query(self) -> None:
        """The `patch-issue-field-name` use case: rename via `version` query."""
        tracker, client = make_tracker(ISSUE_FIELD)
        field = await tracker.update_field(
            "ruName",
            3,
            name=LocalizedName(en="en_name", ru="ru_name"),
        )
        assert field.id == "ruName"

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/fields/ruName")
        assert call["params"] == {"version": "3"}
        assert sent_json(call) == {"name": {"en": "en_name", "ru": "ru_name"}}

    async def test_update_field_value_sends_full_body(self) -> None:
        """The `patch-issue-field-value` use case: change allowed values."""
        tracker, client = make_tracker(ISSUE_FIELD)
        await tracker.update_field(
            "ruName",
            3,
            name=LocalizedName(
                en="Название поля на английском языке",
                ru="Название поля на русском языке",
            ),
            category="0000000000000002********",
            order=102,
            description="Описание поля",
            readonly=True,
            hidden=False,
            visible=False,
            options_provider={
                "type": "FixedListOptionsProvider",
                "values": ["значение 1", "значение 2"],
            },
        )

        call = client.calls[0]
        assert call["params"] == {"version": "3"}
        assert sent_json(call) == {
            "name": {
                "en": "Название поля на английском языке",
                "ru": "Название поля на русском языке",
            },
            "category": "0000000000000002********",
            "order": 102,
            "description": "Описание поля",
            "readonly": True,
            "hidden": False,
            "visible": False,
            "optionsProvider": {
                "type": "FixedListOptionsProvider",
                "values": ["значение 1", "значение 2"],
            },
        }

    async def test_options_provider_read_back_drops_read_only_keys(self) -> None:
        """A provider read from the API can be edited and sent back as is.

        `CREATED_FIELD` carries the read-only `needValidation` the API
        sends; `optionsProvider` documents only `type` and `values` as
        request keys, so the round trip must not leak it back.
        """
        client = FakeClient(
            responses=[
                (200, json.dumps(CREATED_FIELD).encode(), {}),
                (200, json.dumps(CREATED_FIELD).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)

        field = await tracker.get_field("global_field_key")
        provider = field.options_provider
        assert provider is not None
        assert provider.need_validation is True
        assert provider.values == ["First item", "Second item", "Third item"]

        provider.values = ["First item", "Fourth item"]
        await tracker.update_field(
            "global_field_key",
            1,
            options_provider=provider,
        )

        body = sent_json(client.calls[1])
        assert body == {
            "optionsProvider": {
                "type": "FixedListOptionsProvider",
                "values": ["First item", "Fourth item"],
            },
        }
        assert "needValidation" not in body["optionsProvider"]

    async def test_options_provider_without_values_sends_only_type(self) -> None:
        tracker, client = make_tracker(CREATED_FIELD)
        await tracker.update_field(
            "global_field_key",
            1,
            options_provider=QueueFieldOptionsProvider(
                type="FixedUserListOptionsProvider",
                need_validation=True,
            ),
        )

        assert sent_json(client.calls[0]) == {
            "optionsProvider": {"type": "FixedUserListOptionsProvider"},
        }

    async def test_update_field_omits_unset_fields(self) -> None:
        tracker, client = make_tracker(ISSUE_FIELD)
        await tracker.update_field("ruName", 3, order=5)

        call = client.calls[0]
        assert sent_json(call) == {"order": 5}
        # `field_id` and `version` never leak into the body
        assert "id" not in sent_json(call)
        assert "version" not in sent_json(call)


class TestFieldCategoryEndpoints:
    async def test_get_field_categories(self) -> None:
        tracker, client = make_tracker(FIELD_CATEGORIES)
        categories = await tracker.get_field_categories()

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/fields/categories")
        assert call.get("params") is None

        assert [c.id for c in categories] == [
            "604f9920d23cd5********",
            "58bc3b921d9c********",
        ]
        # the create/patch samples carry neither `order` nor `description`
        assert categories[0].order is None
        assert categories[0].description is None
        # the listing does, and the model keeps them
        assert categories[1].order == 400
        assert categories[1].description == "Текстовое описание"

    async def test_get_field_categories_ignores_undocumented_keys(self) -> None:
        # the response shape is undocumented, so anything else the endpoint
        # sends must not break the decoding.
        payload = [{**FIELD_CATEGORIES[0], "somethingNew": {"a": 1}}]
        tracker, _ = make_tracker(payload)
        categories = await tracker.get_field_categories()

        assert len(categories) == 1
        assert categories[0].name == "category_name"

    async def test_create_field_category_sends_exact_body(self) -> None:
        tracker, client = make_tracker(CREATED_CATEGORY, status=201)
        category = await tracker.create_field_category(
            LocalizedName(
                en="Название на английском языке",
                ru="Название на русском языке",
            ),
            400,
            description="Текстовое описание",
        )
        assert category.id == "604f9920d23cd5********"
        assert category.name == "category_name"
        assert category.version == 1

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/fields/categories")
        assert sent_json(call) == {
            "name": {
                "en": "Название на английском языке",
                "ru": "Название на русском языке",
            },
            "description": "Текстовое описание",
            "order": 400,
        }

    async def test_update_field_category_sends_version_query(self) -> None:
        tracker, client = make_tracker(UPDATED_CATEGORY)
        category = await tracker.update_field_category(
            "604f9920d23cd5********",
            LocalizedName(en="en_name", ru="ru_name"),
            400,
            version=1,
            description="description",
        )
        assert category.version == 2

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/fields/categories/604f9920d23cd5********")
        assert call["params"] == {"version": "1"}
        assert sent_json(call) == {
            "name": {"en": "en_name", "ru": "ru_name"},
            "order": 400,
            "description": "description",
        }

    async def test_update_field_category_without_version_sends_no_query(
        self,
    ) -> None:
        tracker, client = make_tracker(UPDATED_CATEGORY)
        await tracker.update_field_category(
            "604f9920d23cd5********",
            {"en": "en_name"},
            5,
        )

        call = client.calls[0]
        assert call["params"] is None
        assert sent_json(call) == {"name": {"en": "en_name"}, "order": 5}

    async def test_update_field_category_requires_name_and_order(self) -> None:
        """The reference lists both as required parameters of the body."""
        tracker, client = make_tracker(UPDATED_CATEGORY)
        with pytest.raises(TypeError):
            await tracker.update_field_category(  # type: ignore[call-arg]
                "604f9920d23cd5********",
                order=5,
            )
        assert client.calls == []


class TestLocalFieldDecoding:
    def test_local_field_decodes_prefixed_id_and_queue(self) -> None:
        field = TypeAdapter(LocalField).validate_json(json.dumps(LOCAL_FIELD))
        assert field.id == "6054ae3a2b6b2c7f********--loc_field_key"
        assert field.key == "loc_field_key"
        assert field.type == "local"
        assert field.queue is not None
        assert field.queue.id == "1"
        assert field.queue.key == "ORG"
        assert field.queue.display == "My queue"
        assert field.category is not None
        assert field.category.id == "0000000000000001********"
        assert field.options_provider is not None
        assert field.options_provider.need_validation is True

    def test_local_field_decodes_without_queue(self) -> None:
        """The create-local-field response omits `queue` entirely."""
        field = TypeAdapter(LocalField).validate_json(
            json.dumps(CREATED_LOCAL_FIELD),
        )
        assert field.queue is None
        assert field.id == "6054ae3a2b6b2c7f********--loc_field_key"


class TestLocalFieldEndpoints:
    async def test_get_local_fields(self) -> None:
        tracker, client = make_tracker([LOCAL_FIELD])
        fields = await tracker.get_local_fields("ORG")
        assert len(fields) == 1
        assert fields[0].key == "loc_field_key"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/ORG/localFields")

    async def test_get_local_field(self) -> None:
        tracker, client = make_tracker(LOCAL_FIELD_INFO)
        field = await tracker.get_local_field("ORG", "loc_field_key")
        assert field.type == "local"
        assert field.queue is not None
        assert field.queue.key == "ORG"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/ORG/localFields/loc_field_key")

    async def test_create_local_field_sends_id_key_and_no_version_query(
        self,
    ) -> None:
        tracker, client = make_tracker(CREATED_LOCAL_FIELD, status=200)
        field = await tracker.create_local_field(
            "DESIGN",
            LocalizedName(
                en="Название на английском языке",
                ru="Название на русском языке",
            ),
            "loc_field_key",
            "0000000000000003********",
            "ru.yandex.startrek.core.fields.StringFieldType",
        )
        assert field.id == "6054ae3a2b6b2c7f********--loc_field_key"
        assert field.queue is None

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/queues/DESIGN/localFields")
        assert call["params"] is None
        assert sent_json(call) == {
            "name": {
                "en": "Название на английском языке",
                "ru": "Название на русском языке",
            },
            "id": "loc_field_key",
            "category": "0000000000000003********",
            "type": "ru.yandex.startrek.core.fields.StringFieldType",
        }

    async def test_create_local_field_with_options_provider(self) -> None:
        tracker, client = make_tracker(CREATED_LOCAL_FIELD)
        await tracker.create_local_field(
            "DESIGN",
            LocalizedName(en="en", ru="ru"),
            "loc_field_key",
            "0000000000000003********",
            "ru.yandex.startrek.core.fields.StringFieldType",
            options_provider={
                "type": "FixedListOptionsProvider",
                "values": [
                    "первый элемент списка",
                    "второй элемент списка",
                    "третий элемент списка",
                ],
            },
        )

        body = sent_json(client.calls[0])
        assert body["optionsProvider"] == {
            "type": "FixedListOptionsProvider",
            "values": [
                "первый элемент списка",
                "второй элемент списка",
                "третий элемент списка",
            ],
        }

    async def test_update_local_field_sends_no_query_params(self) -> None:
        """Unlike `update_field`, the local-field PATCH takes no `version`."""
        tracker, client = make_tracker(UPDATED_LOCAL_FIELD)
        field = await tracker.update_local_field(
            "ORG",
            "loc_field_key",
            name=LocalizedName(
                en="Название поля на английском языке",
                ru="Название поля на русском языке",
            ),
            category="0000000000000002********",
            order=102,
            description="Описание поля",
            readonly=True,
            visible=False,
            hidden=False,
        )
        assert field.version == 2

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/queues/ORG/localFields/loc_field_key")
        assert call["params"] is None
        assert sent_json(call) == {
            "name": {
                "en": "Название поля на английском языке",
                "ru": "Название поля на русском языке",
            },
            "category": "0000000000000002********",
            "order": 102,
            "description": "Описание поля",
            "readonly": True,
            "visible": False,
            "hidden": False,
        }

    async def test_update_local_field_with_options_provider_only(self) -> None:
        tracker, client = make_tracker(UPDATED_LOCAL_FIELD)
        await tracker.update_local_field(
            "ORG",
            "loc_field_key",
            options_provider={
                "type": "FixedListOptionsProvider",
                "values": [
                    "Первый элемент списка",
                    "Второй элемент списка",
                    "Третий элемент списка",
                ],
            },
        )

        assert sent_json(client.calls[0]) == {
            "optionsProvider": {
                "type": "FixedListOptionsProvider",
                "values": [
                    "Первый элемент списка",
                    "Второй элемент списка",
                    "Третий элемент списка",
                ],
            },
        }

    async def test_update_local_field_omits_unset_fields(self) -> None:
        tracker, client = make_tracker(UPDATED_LOCAL_FIELD)
        await tracker.update_local_field("ORG", "loc_field_key", order=1)

        body = sent_json(client.calls[0])
        assert body == {"order": 1}


class TestQueueFieldRegression:
    """`GET /queues/{id}/fields` payloads must still decode as `QueueField`.

    `IssueField`/`LocalField` extend `QueueField` with keys that endpoint
    never sends (`key`, `category`, `type`, ...); this guards that the base
    shape used by `get_queue_fields` (tested in `tests/test_queues.py`)
    stayed untouched.
    """

    def test_get_queue_fields_payload_decodes_as_queue_field(self) -> None:
        field = TypeAdapter(QueueField).validate_json(json.dumps(QUEUE_FIELD))
        assert field.id == "myfield"
        assert field.name == "My field"
        assert field.field_schema.type == "string"
        assert field.field_schema.required is False
        assert field.readonly is False
        assert field.options is True
        assert field.suggest is False
        assert field.query_provider is not None
        assert field.query_provider.type == "StringOptionalQueryProvider"
        assert field.order == 222
        assert field.options_provider is None
