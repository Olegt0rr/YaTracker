"""Tests for the queue access rights, queue tags and queue version methods.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/queues/get-tags
https://yandex.ru/support/tracker/ru/api/queues/create-version
https://yandex.ru/support/tracker/ru/api/queues/get-user-access
https://yandex.ru/support/tracker/ru/api/queues/get-group-access
https://yandex.ru/support/tracker/ru/api/queues/manage-access
https://yandex.ru/support/tracker/ru/api/queues/get-component-user-access
https://yandex.ru/support/tracker/ru/api/queues/get-component-group-access
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import pytest
from yatracker.types.component import Component
from yatracker.types.queue_permissions import (
    ComponentGroupAccess,
    ComponentUserAccess,
    QueueAccessChange,
    QueueAccessUpdate,
    QueueGroupAccess,
    QueuePermissions,
    QueueUserAccess,
)
from yatracker.types.queue_version import QueueVersion
from yatracker.types.ref import Ref
from yatracker.types.user import User

from tests.conftest import make_tracker, sent_json, user_ref

# ---------------------------------------------------------------------------
# Sample payloads, verbatim from the doc pages.
# ---------------------------------------------------------------------------

TAGS_BODY: list[str] = ["tag1", "tag2", "tag3"]

USER_ACCESS_BODY: dict[str, Any] = {
    "user": user_ref(
        self="https://api.tracker.yandex.net/v3/users/11111111",
        id="11111111",
        display="Имя Фамилия",
        cloudUid="ajeppa7dgp53",
        passportUid=11111111,
    ),
    "permissions": {
        "CREATE": {
            "users": [
                user_ref(
                    self="https://api.tracker.yandex.net/v3/users/11111111",
                    id="11111111",
                    display="Имя Фамилия",
                    cloudUid="ajeppa7dgp53",
                    passportUid=11111111,
                ),
            ],
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/5",
                    "id": "5",
                    "display": "All users",
                },
            ],
            "roles": [
                {
                    "self": "https://api.tracker.yandex.net/v3/roles/queue-lead",
                    "id": "queue-lead",
                    "display": "Владелец очереди",
                },
            ],
        },
    },
    "components": [
        {
            "self": "https://api.tracker.yandex.net/v3/components/1",
            "id": "1",
            "display": "Component 1",
        },
    ],
}

GROUP_ACCESS_BODY: dict[str, Any] = {
    "group": {
        "self": "https://api.tracker.yandex.net/v3/groups/5",
        "id": "5",
        "display": "All users",
    },
    "permissions": {
        "CREATE": {
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/5",
                    "id": "5",
                    "display": "All users",
                },
            ],
        },
    },
    "components": [
        {
            "self": "https://api.tracker.yandex.net/v3/components/1",
            "id": "1",
            "display": "Component 1",
        },
    ],
}

COMPONENT_USER_ACCESS_BODY: dict[str, Any] = {
    "user": user_ref(
        self="https://api.tracker.yandex.net/v3/users/11111111",
        id="11111111",
        display="Имя Фамилия",
        cloudUid="ajeppa7dgp53",
        passportUid=11111111,
    ),
    "component": {
        "self": "https://api.tracker.yandex.net/v3/components/1",
        "id": 1,
        "version": 2,
        "name": "Component 1",
        "queue": {
            "self": "https://api.tracker.yandex.net/v3/queues/TEST",
            "id": "1",
            "key": "TEST",
            "display": "My queue",
        },
        "lead": user_ref(
            self="https://api.tracker.yandex.net/v3/users/11111111",
            id="11111111",
            display="Имя Фамилия",
            cloudUid="ajeppa7dgp53",
            passportUid=11111111,
        ),
        "assignAuto": False,
    },
    "permissions": {
        "CREATE": {
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/5",
                    "id": "5",
                    "display": "All users",
                },
            ],
        },
    },
}

COMPONENT_GROUP_ACCESS_BODY: dict[str, Any] = {
    "group": {
        "self": "https://api.tracker.yandex.net/v3/groups/5",
        "id": "5",
        "display": "All users",
    },
    "component": {
        "self": "https://api.tracker.yandex.net/v3/components/1",
        "id": 1,
        "version": 2,
        "name": "Component 1",
        "queue": {
            "self": "https://api.tracker.yandex.net/v3/queues/TEST",
            "id": "1",
            "key": "TEST",
            "display": "My queue",
        },
        "lead": user_ref(
            self="https://api.tracker.yandex.net/v3/users/11111111",
            id="11111111",
            display="Имя Фамилия",
            cloudUid="ajeppa7dgp53",
            passportUid=11111111,
        ),
        "assignAuto": False,
    },
    "permissions": {
        "CREATE": {
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/5",
                    "id": "5",
                    "display": "All users",
                },
            ],
        },
    },
}

# First JSON sample of the manage-access doc page (request body).
MANAGE_ACCESS_REQUEST_BODY: dict[str, Any] = {
    "create": {"groups": [3, 5]},
    "write": {
        "users": {"remove": ["username1", "username2"]},
        "groups": {"add": [4]},
        "roles": {"add": ["author", "assignee"]},
    },
    "read": {
        "groups": {"add": [4]},
        "roles": {"add": ["follower"]},
    },
    "grant": {
        "users": {"remove": ["username3", "username4"]},
    },
}

# Пример 1: plain-list grantees overwrite the current ones.
MANAGE_ACCESS_EXAMPLE_1: dict[str, Any] = {
    "create": {"users": ["user1"]},
    "write": {"users": ["user1"]},
}

# Пример 2: {add, remove} grantees.
MANAGE_ACCESS_EXAMPLE_2: dict[str, Any] = {
    "grant": {"users": {"add": ["user1"], "remove": [12345]}},
}

# Пример 3: deny access.
MANAGE_ACCESS_EXAMPLE_3: dict[str, Any] = {
    "deny": {"users": ["user1"]},
}

MANAGE_ACCESS_RESPONSE_BODY: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/queues/TESTQUEUE/permissions",
    "version": 11,
    "create": {
        "self": "https://api.tracker.yandex.net/v3/queues/TESTQUEUE/permissions/create",
        "users": [
            user_ref(
                self="https://api.tracker.yandex.net/v3/users/11111111",
                id="11111111",
                display="Имя Фамилия",
                cloudUid="ajeppa7dgp53",
                passportUid=11111111,
            ),
        ],
        "roles": [
            {
                "self": "https://api.tracker.yandex.net/v3/roles/author",
                "id": "author",
                "display": "Автор",
            },
            {
                "self": "https://api.tracker.yandex.net/v3/roles/queue-lead",
                "id": "queue-lead",
                "display": "Владелец очереди",
            },
            {
                "self": "https://api.tracker.yandex.net/v3/roles/assignee",
                "id": "assignee",
                "display": "Исполнитель",
            },
        ],
    },
    "write": {
        "self": "https://api.tracker.yandex.net/v3/queues/TESTQUEUE/permissions/write",
        "users": [
            user_ref(
                self="https://api.tracker.yandex.net/v3/users/11111111",
                id="11111111",
                display="Имя Фамилия",
                cloudUid="ajeppa7dgp53",
                passportUid=11111111,
            ),
        ],
        "roles": [
            {
                "self": "https://api.tracker.yandex.net/v3/roles/author",
                "id": "author",
                "display": "Автор",
            },
            {
                "self": "https://api.tracker.yandex.net/v3/roles/queue-lead",
                "id": "queue-lead",
                "display": "Владелец очереди",
            },
            {
                "self": "https://api.tracker.yandex.net/v3/roles/assignee",
                "id": "assignee",
                "display": "Исполнитель",
            },
        ],
    },
    "grant": {
        "self": "https://api.tracker.yandex.net/v3/queues/TESTQUEUE/permissions/grant",
        "users": [
            user_ref(
                self="https://api.tracker.yandex.net/v3/users/11111111",
                id="11111111",
                display="Имя Фамилия",
                cloudUid="ajeppa7dgp53",
                passportUid=11111111,
            ),
        ],
        "roles": [
            {
                "self": "https://api.tracker.yandex.net/v3/roles/author",
                "id": "author",
                "display": "Автор",
            },
            {
                "self": "https://api.tracker.yandex.net/v3/roles/queue-lead",
                "id": "queue-lead",
                "display": "Владелец очереди",
            },
            {
                "self": "https://api.tracker.yandex.net/v3/roles/assignee",
                "id": "assignee",
                "display": "Исполнитель",
            },
        ],
    },
    "deny": {
        "self": "https://api.tracker.yandex.net/v3/queues/TESTQUEUE/permissions/deny",
        "users": [
            user_ref(
                self="https://api.tracker.yandex.net/v3/users/11111111",
                id="11111111",
                display="Имя Фамилия",
                cloudUid="ajeppa7dgp53",
                passportUid=11111111,
            ),
        ],
    },
}

# Пример of create-version: request body.
CREATE_VERSION_REQUEST_BODY: dict[str, Any] = {
    "queue": "TESTQUEUE",
    "name": "version 0.1",
    "description": "Test version 1",
    "startDate": "2023-10-03",
    "dueDate": "2024-06-03",
}

# create-version response item (as returned inside the doc's list wrapper).
CREATE_VERSION_RESPONSE_ITEM: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/versions/1",
    "id": 1,
    "version": 1,
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/TESTQUEUE",
        "id": "6",
        "key": "TESTQUEUE",
        "display": "Test Queue",
    },
    "name": "version 0.1",
    "description": "Test version 1",
    "startDate": "2023-10-03",
    "dueDate": "2024-06-03",
    "released": False,
    "archived": False,
}


class TestGetQueueTags:
    async def test_get_queue_tags_uses_tags_path_and_decodes_list(self) -> None:
        tracker, client = make_tracker(TAGS_BODY)
        tags = await tracker.get_queue_tags("TEST")
        assert tags == ["tag1", "tag2", "tag3"]

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/TEST/tags")


class TestCreateQueueVersion:
    async def test_sends_exact_body_and_decodes_list_response(self) -> None:
        tracker, client = make_tracker([CREATE_VERSION_RESPONSE_ITEM])
        version = await tracker.create_queue_version(
            "TESTQUEUE",
            "version 0.1",
            description="Test version 1",
            start_date="2023-10-03",
            due_date="2024-06-03",
        )

        call = client.calls[0]
        assert call["method"] == "POST"
        # The implementation posts to the top-level `/versions` resource,
        # as documented at the top of the create-version page; the
        # doc's worked example instead shows `/queues/TEST/versions`,
        # which is a doc inconsistency (see final report).
        assert call["url"].endswith("/versions")
        assert not call["url"].endswith("/queues/TESTQUEUE/versions")
        assert sent_json(call) == CREATE_VERSION_REQUEST_BODY

        assert isinstance(version, QueueVersion)
        assert version.id == 1
        assert version.version == 1
        assert version.queue.key == "TESTQUEUE"
        assert version.queue.id == "6"
        assert version.name == "version 0.1"
        assert version.description == "Test version 1"
        assert version.start_date == date(2023, 10, 3)
        assert version.due_date == date(2024, 6, 3)
        assert version.released is False
        assert version.archived is False

    async def test_optional_fields_omitted_when_none(self) -> None:
        tracker, client = make_tracker([CREATE_VERSION_RESPONSE_ITEM])
        await tracker.create_queue_version("TESTQUEUE", "version 0.1")

        assert sent_json(client.calls[0]) == {
            "queue": "TESTQUEUE",
            "name": "version 0.1",
        }

    async def test_accepts_date_objects_and_renders_yyyy_mm_dd(self) -> None:
        tracker, client = make_tracker([CREATE_VERSION_RESPONSE_ITEM])
        await tracker.create_queue_version(
            "TESTQUEUE",
            "version 0.1",
            start_date=date(2023, 10, 3),
            due_date=date(2024, 6, 3),
        )

        assert sent_json(client.calls[0]) == {
            "queue": "TESTQUEUE",
            "name": "version 0.1",
            "startDate": "2023-10-03",
            "dueDate": "2024-06-03",
        }

    async def test_accepts_bare_object_response(self) -> None:
        """Every other single-object endpoint answers with a bare object.

        `create_queue_version` must accept that shape too, not only the
        list-wrapped one shown in the doc sample.
        """
        tracker, _client = make_tracker(CREATE_VERSION_RESPONSE_ITEM)
        version = await tracker.create_queue_version("TESTQUEUE", "version 0.1")

        assert isinstance(version, QueueVersion)
        assert version.id == 1
        assert version.name == "version 0.1"

    async def test_type_subclass_passthrough_with_list_response(self) -> None:
        class MyVersion(QueueVersion):
            pass

        tracker, _client = make_tracker([CREATE_VERSION_RESPONSE_ITEM])
        version = await tracker.create_queue_version(
            "TESTQUEUE",
            "version 0.1",
            MyVersion,
        )
        assert isinstance(version, MyVersion)

    async def test_type_subclass_passthrough_with_object_response(self) -> None:
        class MyVersion(QueueVersion):
            pass

        tracker, _client = make_tracker(CREATE_VERSION_RESPONSE_ITEM)
        version = await tracker.create_queue_version(
            "TESTQUEUE",
            "version 0.1",
            _type=MyVersion,
        )
        assert isinstance(version, MyVersion)

    async def test_empty_array_response_raises_value_error(self) -> None:
        """An empty array must not surface as a bare `IndexError`."""
        tracker, _client = make_tracker([])
        with pytest.raises(ValueError, match="empty array"):
            await tracker.create_queue_version("TESTQUEUE", "version 0.1")


class TestGetQueueUserAccess:
    async def test_uses_user_permissions_path_and_decodes(self) -> None:
        tracker, client = make_tracker(USER_ACCESS_BODY)
        access = await tracker.get_queue_user_access("TEST", "11111111")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/TEST/permissions/users/11111111")

        assert isinstance(access, QueueUserAccess)
        assert isinstance(access.user, User)
        assert access.user.id == "11111111"
        assert access.user.display == "Имя Фамилия"

        create = access.permissions["CREATE"]
        assert isinstance(create.users[0], User)
        assert create.users[0].id == "11111111"
        assert isinstance(create.groups[0], Ref)
        assert create.groups[0].id == "5"
        assert create.groups[0].display == "All users"
        assert isinstance(create.roles[0], Ref)
        assert create.roles[0].id == "queue-lead"
        assert create.roles[0].display == "Владелец очереди"
        # `QueueAccessGrantees.url` is not sent inside the `permissions`
        # mapping (only the top-level `QueuePermissions` blocks carry it).
        assert create.url is None

        assert access.components is not None
        assert access.components[0].id == "1"
        assert access.components[0].display == "Component 1"


class TestGetQueueGroupAccess:
    async def test_uses_group_permissions_path_and_decodes(self) -> None:
        tracker, client = make_tracker(GROUP_ACCESS_BODY)
        access = await tracker.get_queue_group_access("TEST", 5)

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/queues/TEST/permissions/groups/5")

        assert isinstance(access, QueueGroupAccess)
        assert isinstance(access.group, Ref)
        assert access.group.id == "5"
        assert access.group.display == "All users"

        create = access.permissions["CREATE"]
        assert create.users is None
        assert create.roles is None
        assert isinstance(create.groups[0], Ref)
        assert create.groups[0].id == "5"

        assert access.components is not None
        assert access.components[0].id == "1"


class TestUpdateQueueAccess:
    async def test_manage_access_first_sample_round_trips(self) -> None:
        """Round-trip the doc's first JSON sample.

        It mixes plain-list and {add, remove} grantees across
        create/write/read/grant; `deny` is left unset and must not
        appear in the body.
        """
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)
        await tracker.update_queue_access(
            "TESTQUEUE",
            create=QueueAccessUpdate(groups=[3, 5]),
            write=QueueAccessUpdate(
                users=QueueAccessChange(remove=["username1", "username2"]),
                groups=QueueAccessChange(add=[4]),
                roles=QueueAccessChange(add=["author", "assignee"]),
            ),
            read=QueueAccessUpdate(
                groups=QueueAccessChange(add=[4]),
                roles=QueueAccessChange(add=["follower"]),
            ),
            grant=QueueAccessUpdate(
                users=QueueAccessChange(remove=["username3", "username4"]),
            ),
        )

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/queues/TESTQUEUE/permissions")
        assert sent_json(call) == MANAGE_ACCESS_REQUEST_BODY
        assert "deny" not in sent_json(call)

    async def test_manage_access_first_sample_round_trips_with_plain_dicts(
        self,
    ) -> None:
        """Every block also accepts the equivalent plain dict."""
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)
        await tracker.update_queue_access(
            "TESTQUEUE",
            create={"groups": [3, 5]},
            write={
                "users": {"remove": ["username1", "username2"]},
                "groups": {"add": [4]},
                "roles": {"add": ["author", "assignee"]},
            },
            read={
                "groups": {"add": [4]},
                "roles": {"add": ["follower"]},
            },
            grant={"users": {"remove": ["username3", "username4"]}},
        )

        assert sent_json(client.calls[0]) == MANAGE_ACCESS_REQUEST_BODY

    async def test_example_1_plain_list_overwrites(self) -> None:
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)
        await tracker.update_queue_access(
            "TESTQUEUE",
            create=QueueAccessUpdate(users=["user1"]),
            write=QueueAccessUpdate(users=["user1"]),
        )

        assert sent_json(client.calls[0]) == MANAGE_ACCESS_EXAMPLE_1

    async def test_example_2_add_and_remove(self) -> None:
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)
        await tracker.update_queue_access(
            "TESTQUEUE",
            grant=QueueAccessUpdate(
                users=QueueAccessChange(add=["user1"], remove=[12345]),
            ),
        )

        assert sent_json(client.calls[0]) == MANAGE_ACCESS_EXAMPLE_2

    async def test_example_3_deny(self) -> None:
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)
        await tracker.update_queue_access(
            "TESTQUEUE",
            deny=QueueAccessUpdate(users=["user1"]),
        )

        assert sent_json(client.calls[0]) == MANAGE_ACCESS_EXAMPLE_3

    async def test_none_blocks_are_all_omitted(self) -> None:
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)
        await tracker.update_queue_access(
            "TESTQUEUE",
            create=QueueAccessUpdate(users=["user1"]),
        )

        assert sent_json(client.calls[0]) == {"create": {"users": ["user1"]}}

    async def test_no_permissions_raises(self) -> None:
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)

        with pytest.raises(ValueError, match="requires `create`"):
            await tracker.update_queue_access("TESTQUEUE")

        assert client.calls == []

    async def test_empty_model_permission_raises(self) -> None:
        # an all-`None` `QueueAccessUpdate` renders to `{}`; a plain list
        # overwrites the grantees, so sending `{"create": {}}` is dangerous.
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)

        with pytest.raises(ValueError, match="'create'"):
            await tracker.update_queue_access(
                "TESTQUEUE",
                create=QueueAccessUpdate(),
            )

        assert client.calls == []

    async def test_empty_dict_permission_raises(self) -> None:
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)

        with pytest.raises(ValueError, match="'write'"):
            await tracker.update_queue_access("TESTQUEUE", write={})

        assert client.calls == []

    async def test_empty_permission_next_to_a_real_one_still_raises(self) -> None:
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)

        with pytest.raises(ValueError, match="'deny'"):
            await tracker.update_queue_access(
                "TESTQUEUE",
                create=QueueAccessUpdate(users=["user1"]),
                deny={},
            )

        assert client.calls == []

    async def test_response_decodes_into_queue_permissions(self) -> None:
        tracker, client = make_tracker(MANAGE_ACCESS_RESPONSE_BODY)
        permissions = await tracker.update_queue_access(
            "TESTQUEUE",
            create=QueueAccessUpdate(users=["user1"]),
        )

        assert isinstance(permissions, QueuePermissions)
        assert permissions.url == (
            "https://api.tracker.yandex.net/v3/queues/TESTQUEUE/permissions"
        )
        assert permissions.version == 11

        assert permissions.create is not None
        assert permissions.create.url == (
            "https://api.tracker.yandex.net/v3/queues/TESTQUEUE/permissions/create"
        )
        assert isinstance(permissions.create.users[0], User)
        assert permissions.create.users[0].id == "11111111"
        assert [role.id for role in permissions.create.roles] == [
            "author",
            "queue-lead",
            "assignee",
        ]

        assert permissions.write is not None
        assert permissions.grant is not None

        assert permissions.deny is not None
        assert permissions.deny.roles is None
        assert isinstance(permissions.deny.users[0], User)
        assert permissions.deny.users[0].id == "11111111"

        call = client.calls[0]
        assert call["method"] == "PATCH"


class TestGetComponentUserAccess:
    async def test_uses_component_user_permissions_path_and_decodes(self) -> None:
        tracker, client = make_tracker(COMPONENT_USER_ACCESS_BODY)
        access = await tracker.get_component_user_access(1, "11111111")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/components/1/permissions/users/11111111")

        assert isinstance(access, ComponentUserAccess)
        assert isinstance(access.user, User)
        assert access.user.id == "11111111"

        assert isinstance(access.component, Component)
        assert access.component.id == "1"
        assert access.component.version == 2
        assert access.component.name == "Component 1"
        assert access.component.queue.key == "TEST"
        assert access.component.lead is not None
        assert access.component.lead.id == "11111111"
        assert access.component.assign_auto is False

        create = access.permissions["CREATE"]
        assert isinstance(create.groups[0], Ref)
        assert create.groups[0].id == "5"


class TestGetComponentGroupAccess:
    async def test_uses_component_group_permissions_path_and_decodes(self) -> None:
        tracker, client = make_tracker(COMPONENT_GROUP_ACCESS_BODY)
        access = await tracker.get_component_group_access(1, 5)

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/components/1/permissions/groups/5")

        assert isinstance(access, ComponentGroupAccess)
        assert isinstance(access.group, Ref)
        assert access.group.id == "5"
        assert access.group.display == "All users"

        assert isinstance(access.component, Component)
        assert access.component.id == "1"
        assert access.component.name == "Component 1"

        create = access.permissions["CREATE"]
        assert isinstance(create.groups[0], Ref)
        assert create.groups[0].id == "5"


def test_manage_access_response_body_is_json_serializable() -> None:
    """Sanity check that the fixture above is valid JSON (guards typos)."""
    assert json.loads(json.dumps(MANAGE_ACCESS_RESPONSE_BODY))["version"] == 11
