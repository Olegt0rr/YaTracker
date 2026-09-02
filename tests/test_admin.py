"""Tests for the admin dictionaries category and its structs.

Covers issue types, priorities, resolutions and statuses. Payloads are
taken verbatim from the official documentation:
https://yandex.ru/support/tracker/ru/api/admin/get-issue-types
https://yandex.ru/support/tracker/ru/api/admin/create-issue-type
https://yandex.ru/support/tracker/ru/api/admin/patch-issue-type
https://yandex.ru/support/tracker/ru/api/admin/get-priorities
https://yandex.ru/support/tracker/ru/api/admin/create-priority
https://yandex.ru/support/tracker/ru/api/admin/patch-priority
https://yandex.ru/support/tracker/ru/api/admin/get-resolutions
https://yandex.ru/support/tracker/ru/api/admin/create-resolution
https://yandex.ru/support/tracker/ru/api/admin/patch-resolution
https://yandex.ru/support/tracker/ru/api/admin/get-statuses
https://yandex.ru/support/tracker/ru/api/admin/create-status
https://yandex.ru/support/tracker/ru/api/admin/patch-status

Note on a documentation quirk: the create/patch issue-type and
create/patch status pages render their *response* body wrapped in a
JSON array (``[{...}]``), unlike create/patch priority and
create/patch resolution, which render a plain object. These four
methods therefore decode through ``_decode_single``, which accepts
both shapes and returns the single object; an empty array raises
``ValueError`` instead of ``IndexError``. Both shapes are covered
below.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import TypeAdapter
from yatracker.types.issue_type import FullIssueType, IssueType
from yatracker.types.localized_name import LocalizedName
from yatracker.types.priority import Priority
from yatracker.types.resolution import FullResolution, Resolution
from yatracker.types.status import FullStatus, Status

from tests.conftest import make_tracker, sent_json

# --------------------------------------------------------------------------
# Issue types
# --------------------------------------------------------------------------

# GET /issuetypes response list item.
ISSUE_TYPE_LIST_ITEM: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issuetypes/1",
    "id": 1,
    "version": 1,
    "key": "task",
    "name": "Задача",
    "description": "A task that needs to be done.",
}

# POST /issuetypes response (object form; see module docstring).
ISSUE_TYPE_CREATED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issuetypes/23",
    "id": 23,
    "version": 1,
    "key": "client",
    "name": "Клиент",
}

# PATCH /issuetypes/{id} response (object form; see module docstring).
ISSUE_TYPE_PATCHED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issuetypes/23",
    "id": 23,
    "version": 2,
    "key": "client",
    "name": "Покупатель",
}

# Short reference embedded into issues/queues (e.g. `FullIssue.type`).
ISSUE_TYPE_REF: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issuetypes/1",
    "id": "1",
    "key": "task",
    "display": "Задача",
}


class TestFullIssueTypeDecoding:
    def test_list_item_decodes(self) -> None:
        issue_type = TypeAdapter(FullIssueType).validate_json(
            json.dumps(ISSUE_TYPE_LIST_ITEM),
        )
        assert issue_type.id == "1"
        assert issue_type.version == 1
        assert issue_type.key == "task"
        assert issue_type.name == "Задача"
        assert issue_type.description == "A task that needs to be done."
        assert issue_type.deleted is None

    def test_deleted_flag_decodes(self) -> None:
        """Docs describe `deleted` in the params table but show no sample."""
        payload = {**ISSUE_TYPE_LIST_ITEM, "deleted": True}
        issue_type = TypeAdapter(FullIssueType).validate_json(json.dumps(payload))
        assert issue_type.deleted is True


class TestShortIssueTypeDecoding:
    def test_short_ref_decodes(self) -> None:
        issue_type = TypeAdapter(IssueType).validate_json(json.dumps(ISSUE_TYPE_REF))
        assert issue_type.id == "1"
        assert issue_type.key == "task"
        assert issue_type.display == "Задача"


class TestIssueTypeEndpoints:
    async def test_get_issue_types(self) -> None:
        tracker, client = make_tracker([ISSUE_TYPE_LIST_ITEM])
        issue_types = await tracker.get_issue_types()
        assert len(issue_types) == 1
        assert issue_types[0].name == "Задача"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/issuetypes")
        assert call["params"] is None

    async def test_create_issue_type_sends_exact_body_localized_name(self) -> None:
        tracker, client = make_tracker(ISSUE_TYPE_CREATED, status=201)
        issue_type = await tracker.create_issue_type(
            "client",
            LocalizedName(ru="Клиент", en="Customer"),
        )
        assert issue_type.id == "23"
        assert issue_type.name == "Клиент"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/issuetypes")
        assert sent_json(call) == {
            "key": "client",
            "name": {"ru": "Клиент", "en": "Customer"},
        }

    async def test_create_issue_type_accepts_plain_dict_name(self) -> None:
        """A plain dict is equivalent to `LocalizedName` when fully populated."""
        tracker, client = make_tracker(ISSUE_TYPE_CREATED, status=201)
        await tracker.create_issue_type(
            "client",
            {"ru": "Клиент", "en": "Customer"},
        )

        call = client.calls[0]
        assert sent_json(call) == {
            "key": "client",
            "name": {"ru": "Клиент", "en": "Customer"},
        }

    async def test_localized_name_drops_unset_language(self) -> None:
        """`LocalizedName` excludes `None` fields; a partial dict has no such key."""
        tracker, client = make_tracker(ISSUE_TYPE_CREATED, status=201)
        await tracker.create_issue_type("client", LocalizedName(ru="Клиент"))

        assert sent_json(client.calls[0]) == {
            "key": "client",
            "name": {"ru": "Клиент"},
        }

    async def test_update_issue_type_sends_version_param_and_partial_body(
        self,
    ) -> None:
        tracker, client = make_tracker(ISSUE_TYPE_PATCHED)
        issue_type = await tracker.update_issue_type(
            23,
            version=1,
            name=LocalizedName(ru="Покупатель", en="Customer"),
        )
        assert issue_type.name == "Покупатель"
        assert issue_type.version == 2

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/issuetypes/23")
        assert call["params"] == {"version": "1"}
        assert sent_json(call) == {"name": {"ru": "Покупатель", "en": "Customer"}}

    async def test_update_issue_type_without_version_sends_no_params(self) -> None:
        tracker, client = make_tracker(ISSUE_TYPE_PATCHED)
        await tracker.update_issue_type(23, name={"ru": "Покупатель"})

        call = client.calls[0]
        assert call["params"] is None
        assert sent_json(call) == {"name": {"ru": "Покупатель"}}

    async def test_create_issue_type_accepts_the_documented_array_shape(self) -> None:
        tracker, _ = make_tracker([ISSUE_TYPE_CREATED], status=201)
        issue_type = await tracker.create_issue_type("client", {"ru": "Клиент"})
        assert issue_type.id == "23"

    async def test_update_issue_type_accepts_the_documented_array_shape(self) -> None:
        tracker, _ = make_tracker([ISSUE_TYPE_PATCHED])
        issue_type = await tracker.update_issue_type(23, name={"ru": "Покупатель"})
        assert issue_type.version == 2

    async def test_create_issue_type_raises_on_an_empty_array(self) -> None:
        tracker, _ = make_tracker([], status=201)
        with pytest.raises(ValueError, match="empty array"):
            await tracker.create_issue_type("client", {"ru": "Клиент"})

    async def test_update_issue_type_raises_on_an_empty_array(self) -> None:
        tracker, _ = make_tracker([])
        with pytest.raises(ValueError, match="empty array"):
            await tracker.update_issue_type(23, name={"ru": "Покупатель"})


# --------------------------------------------------------------------------
# Priorities
# --------------------------------------------------------------------------

# GET /priorities response list item.
PRIORITY_LIST_ITEM: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/priorities/5",
    "id": 5,
    "key": "normal",
    "version": 1341632717561,
    "name": "Средний",
    "order": 5,
}

# POST /priorities response.
PRIORITY_CREATED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/priorities/6",
    "id": 6,
    "key": "one",
    "version": 1,
    "name": "Название на русском",
    "description": "Описание",
    "order": 60,
}

# PATCH /priorities/{id} response.
PRIORITY_PATCHED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/priorities/6",
    "id": 6,
    "key": "one",
    "version": 2,
    "name": "Низкий",
    "description": "Описание",
    "order": 60,
}


class TestPriorityDecoding:
    def test_localized_response_decodes(self) -> None:
        priority = TypeAdapter(Priority).validate_json(
            json.dumps(PRIORITY_LIST_ITEM),
        )
        assert priority.id == "5"
        assert priority.key == "normal"
        assert priority.version == 1341632717561
        assert priority.name == "Средний"
        assert priority.order == 5
        assert priority.display is None
        assert priority.description is None

    def test_non_localized_response_name_is_a_dict(self) -> None:
        """Synthetic sample: docs describe `localized=false` in prose only.

        With `localized=false` the docs say `name` "contains duplicates
        of the names in other languages", but show no JSON example, so
        this payload models that shape rather than quoting the docs.
        """
        payload = {
            **PRIORITY_LIST_ITEM,
            "name": {"ru": "Средний", "en": "Normal"},
        }
        priority = TypeAdapter(Priority).validate_json(json.dumps(payload))
        assert priority.name == {"ru": "Средний", "en": "Normal"}


class TestPriorityEndpoints:
    async def test_get_priorities_defaults_to_localized_true(self) -> None:
        tracker, client = make_tracker([PRIORITY_LIST_ITEM])
        priorities = await tracker.get_priorities()
        assert len(priorities) == 1
        assert priorities[0].name == "Средний"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/priorities")
        assert call["params"] == {"localized": "true"}

    async def test_get_priorities_localized_false_sends_lowercase_param(
        self,
    ) -> None:
        tracker, client = make_tracker([PRIORITY_LIST_ITEM])
        await tracker.get_priorities(localized=False)

        call = client.calls[0]
        assert call["params"] == {"localized": "false"}

    async def test_create_priority_sends_exact_body(self) -> None:
        tracker, client = make_tracker(PRIORITY_CREATED, status=201)
        priority = await tracker.create_priority(
            "one",
            LocalizedName(en="English name", ru="Название на русском"),
            60,
            "Описание",
        )
        assert priority.id == "6"
        assert priority.order == 60

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/priorities")
        assert sent_json(call) == {
            "name": {"en": "English name", "ru": "Название на русском"},
            "key": "one",
            "order": 60,
            "description": "Описание",
        }

    async def test_update_priority_sends_version_param_and_partial_body(
        self,
    ) -> None:
        tracker, client = make_tracker(PRIORITY_PATCHED)
        priority = await tracker.update_priority(
            "one",
            version=1,
            name={"en": "Low", "ru": "Низкий"},
            description="Описание",
        )
        assert priority.name == "Низкий"
        assert priority.version == 2

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/priorities/one")
        assert call["params"] == {"version": "1"}
        assert sent_json(call) == {
            "name": {"en": "Low", "ru": "Низкий"},
            "description": "Описание",
        }

    async def test_update_priority_without_version_sends_no_params(self) -> None:
        tracker, client = make_tracker(PRIORITY_PATCHED)
        await tracker.update_priority("one", description="Описание")

        call = client.calls[0]
        assert call["params"] is None
        assert sent_json(call) == {"description": "Описание"}


# --------------------------------------------------------------------------
# Resolutions
# --------------------------------------------------------------------------

# GET /resolutions response list item.
RESOLUTION_LIST_ITEM: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/resolutions/1",
    "id": 1,
    "key": "fixed",
    "version": 1,
    "name": "Решен",
    "description": "Решен",
    "order": 0,
}

# POST /resolutions response.
RESOLUTION_CREATED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/resolutions/9",
    "id": 9,
    "key": "myResolution",
    "version": 1,
    "name": "Моя резолюция",
    "order": 90,
}

# PATCH /resolutions/{id} response.
RESOLUTION_PATCHED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/resolutions/9",
    "id": 9,
    "key": "myResolution",
    "version": 2,
    "name": "Не будет исправлено",
    "description": "Issue won't be fixed",
    "order": 90,
}

# Short reference embedded into issues (e.g. `FullIssue.resolution`).
RESOLUTION_REF: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/resolutions/1",
    "id": "1",
    "key": "fixed",
    "display": "Решен",
}


class TestFullResolutionDecoding:
    def test_list_item_decodes(self) -> None:
        resolution = TypeAdapter(FullResolution).validate_json(
            json.dumps(RESOLUTION_LIST_ITEM),
        )
        assert resolution.id == "1"
        assert resolution.key == "fixed"
        assert resolution.version == 1
        assert resolution.name == "Решен"
        assert resolution.description == "Решен"
        assert resolution.order == 0


class TestShortResolutionDecoding:
    def test_short_ref_decodes(self) -> None:
        resolution = TypeAdapter(Resolution).validate_json(
            json.dumps(RESOLUTION_REF),
        )
        assert resolution.id == "1"
        assert resolution.key == "fixed"
        assert resolution.display == "Решен"


class TestResolutionEndpoints:
    async def test_get_resolutions(self) -> None:
        tracker, client = make_tracker([RESOLUTION_LIST_ITEM])
        resolutions = await tracker.get_resolutions()
        assert len(resolutions) == 1
        assert resolutions[0].name == "Решен"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/resolutions")
        assert call["params"] is None

    async def test_create_resolution_sends_exact_body(self) -> None:
        tracker, client = make_tracker(RESOLUTION_CREATED, status=201)
        resolution = await tracker.create_resolution(
            "myResolution",
            LocalizedName(ru="Моя резолюция", en="My resolution"),
        )
        assert resolution.id == "9"
        assert resolution.order == 90

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/resolutions")
        assert sent_json(call) == {
            "key": "myResolution",
            "name": {"ru": "Моя резолюция", "en": "My resolution"},
        }

    async def test_update_resolution_sends_version_param_and_full_body(
        self,
    ) -> None:
        tracker, client = make_tracker(RESOLUTION_PATCHED)
        resolution = await tracker.update_resolution(
            9,
            version=1,
            name={"ru": "Не будет исправлено", "en": "Won't be fixed"},
            description="Issue won't be fixed",
            order=350,
        )
        assert resolution.name == "Не будет исправлено"
        assert resolution.version == 2

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/resolutions/9")
        assert call["params"] == {"version": "1"}
        assert sent_json(call) == {
            "name": {"ru": "Не будет исправлено", "en": "Won't be fixed"},
            "description": "Issue won't be fixed",
            "order": 350,
        }

    async def test_update_resolution_without_version_sends_no_params(self) -> None:
        tracker, client = make_tracker(RESOLUTION_PATCHED)
        await tracker.update_resolution(9, order=350)

        call = client.calls[0]
        assert call["params"] is None
        assert sent_json(call) == {"order": 350}


# --------------------------------------------------------------------------
# Statuses
# --------------------------------------------------------------------------

# GET /statuses response list item.
STATUS_LIST_ITEM: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/statuses/1",
    "id": 1,
    "version": 1,
    "key": "open",
    "name": "Открыт",
    "description": "Открыт",
    "order": 200,
    "type": "new",
}

# POST /statuses response (object form; see module docstring).
STATUS_CREATED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/statuses/29",
    "id": 29,
    "version": 1,
    "key": "pause",
    "name": "On pause",
    "description": "Issue is paused",
    "order": 350,
    "type": "paused",
}

# PATCH /statuses/{id} response (object form; see module docstring).
STATUS_PATCHED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/statuses/29",
    "id": 29,
    "version": 2,
    "key": "pause",
    "name": "On pause",
    "description": "Issue is paused",
    "order": 350,
    "type": "paused",
}

# Short reference embedded into issues (e.g. `FullIssue.status`).
STATUS_REF: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/statuses/1",
    "id": "1",
    "key": "open",
    "display": "Открыт",
}


class TestFullStatusDecoding:
    def test_list_item_decodes(self) -> None:
        status = TypeAdapter(FullStatus).validate_json(json.dumps(STATUS_LIST_ITEM))
        assert status.id == "1"
        assert status.version == 1
        assert status.key == "open"
        assert status.name == "Открыт"
        assert status.description == "Открыт"
        assert status.order == 200
        assert status.type == "new"


class TestShortStatusDecoding:
    def test_short_ref_decodes(self) -> None:
        status = TypeAdapter(Status).validate_json(json.dumps(STATUS_REF))
        assert status.id == "1"
        assert status.key == "open"
        assert status.display == "Открыт"


class TestStatusEndpoints:
    async def test_get_statuses(self) -> None:
        tracker, client = make_tracker([STATUS_LIST_ITEM])
        statuses = await tracker.get_statuses()
        assert len(statuses) == 1
        assert statuses[0].type == "new"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/statuses")
        assert call["params"] is None

    async def test_create_status_sends_type_field(self) -> None:
        tracker, client = make_tracker(STATUS_CREATED, status=201)
        status = await tracker.create_status(
            "myStatus",
            LocalizedName(ru="Мой статус", en="My status"),
            "paused",
        )
        assert status.id == "29"
        assert status.type == "paused"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/statuses")
        assert sent_json(call) == {
            "key": "myStatus",
            "name": {"ru": "Мой статус", "en": "My status"},
            "type": "paused",
        }

    async def test_update_status_sends_version_param_and_full_body(self) -> None:
        tracker, client = make_tracker(STATUS_PATCHED)
        status = await tracker.update_status(
            29,
            version=1,
            name={"ru": "Мой статус", "en": "My status"},
            description="My status description",
            order=350,
            type_="paused",
        )
        assert status.name == "On pause"
        assert status.version == 2

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/statuses/29")
        assert call["params"] == {"version": "1"}
        assert sent_json(call) == {
            "name": {"ru": "Мой статус", "en": "My status"},
            "description": "My status description",
            "order": 350,
            "type": "paused",
        }

    async def test_update_status_without_version_sends_no_params(self) -> None:
        tracker, client = make_tracker(STATUS_PATCHED)
        await tracker.update_status(29, type_="paused")

        call = client.calls[0]
        assert call["params"] is None
        assert sent_json(call) == {"type": "paused"}

    async def test_create_status_accepts_the_documented_array_shape(self) -> None:
        tracker, _ = make_tracker([STATUS_CREATED], status=201)
        status = await tracker.create_status("myStatus", {"ru": "Мой"}, "paused")
        assert status.id == "29"

    async def test_update_status_accepts_the_documented_array_shape(self) -> None:
        tracker, _ = make_tracker([STATUS_PATCHED])
        status = await tracker.update_status(29, type_="paused")
        assert status.version == 2

    async def test_create_status_raises_on_an_empty_array(self) -> None:
        tracker, _ = make_tracker([], status=201)
        with pytest.raises(ValueError, match="empty array"):
            await tracker.create_status("myStatus", {"ru": "Мой"}, "paused")

    async def test_update_status_raises_on_an_empty_array(self) -> None:
        tracker, _ = make_tracker([])
        with pytest.raises(ValueError, match="empty array"):
            await tracker.update_status(29, type_="paused")
