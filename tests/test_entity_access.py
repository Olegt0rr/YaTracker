"""Tests for the entity access API (projects, portfolios and goals, issue #14).

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/entities/get-access
https://yandex.ru/support/tracker/ru/api/entities/patch-access
"""

from __future__ import annotations

from typing import Any

import pytest
from yatracker.types.entity_access import (
    EntityAccessChange,
    EntityAccessRule,
    EntityPermissions,
)

from tests.conftest import make_tracker, sent_json, user_ref

# --- payload builders --------------------------------------------------------

# `GET .../extendedPermissions` (and the `PATCH` response) sample.
PERMISSIONS_RESPONSE: dict[str, Any] = {
    "acl": {
        "READ": {
            "users": [
                user_ref(
                    self="https://api.tracker.yandex.net/v3/users/11",
                    id="11",
                    display="Имя Фамилия",
                    passportUid=11,
                ),
            ],
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/1",
                    "id": "1",
                    "display": "Группа 1",
                },
            ],
            "roles": [],
        },
        "GRANT": {
            "users": [],
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/2",
                    "id": "2",
                    "display": "Группа 2",
                },
            ],
            "roles": ["AUTHOR", "OWNER"],
        },
        "WRITE": {
            "users": [],
            "groups": [
                {
                    "self": "https://api.tracker.yandex.net/v3/groups/3",
                    "id": "3",
                    "display": "Группа 3",
                },
            ],
            "roles": ["CLIENT", "AUTHOR", "FOLLOWER", "OWNER", "MEMBER"],
        },
    },
    "permissionSources": [
        {
            "self": "https://api.tracker.yandex.net/v3/entities/portfolio/67ffd7e3",
            "id": "67ffd7e3",
            "display": "My portfolio",
        },
    ],
    "parentEntities": {
        "primary": {
            "self": "https://api.tracker.yandex.net/v3/entities/portfolio/67ffd7e3",
            "id": "67ffd7e3",
            "display": "My portfolio",
        },
        "secondary": [],
    },
}


def permissions_payload(**overrides: Any) -> dict[str, Any]:
    return {**PERMISSIONS_RESPONSE, **overrides}


# --- get_entity_access -------------------------------------------------------


class TestGetEntityAccess:
    async def test_sends_get_to_extended_permissions_uri(self) -> None:
        tracker, client = make_tracker(permissions_payload())
        await tracker.get_entity_access("project", "655f8cc52")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith(
            "/v3/entities/project/655f8cc52/extendedPermissions",
        )
        assert call["params"] is None
        assert call["data"] is None

    async def test_goal_entity_type_in_uri(self) -> None:
        tracker, client = make_tracker(permissions_payload())
        await tracker.get_entity_access("goal", 7)

        assert client.calls[0]["url"].endswith(
            "/v3/entities/goal/7/extendedPermissions",
        )

    async def test_decodes_acl_users_groups_and_roles(self) -> None:
        tracker, _ = make_tracker(permissions_payload())
        permissions = await tracker.get_entity_access("project", "1")

        assert isinstance(permissions, EntityPermissions)
        assert permissions.acl.read is not None
        assert permissions.acl.read.users[0].id == "11"
        assert permissions.acl.read.users[0].display == "Имя Фамилия"
        assert permissions.acl.read.groups[0].id == "1"
        assert permissions.acl.read.groups[0].display == "Группа 1"
        assert permissions.acl.read.roles == []

        assert permissions.acl.grant is not None
        assert permissions.acl.grant.roles == ["AUTHOR", "OWNER"]
        assert permissions.acl.grant.groups[0].id == "2"

        assert permissions.acl.write is not None
        assert permissions.acl.write.roles == [
            "CLIENT",
            "AUTHOR",
            "FOLLOWER",
            "OWNER",
            "MEMBER",
        ]

    async def test_decodes_permission_sources_and_parent_entities(self) -> None:
        tracker, _ = make_tracker(permissions_payload())
        permissions = await tracker.get_entity_access("project", "1")

        assert len(permissions.permission_sources) == 1
        assert permissions.permission_sources[0].id == "67ffd7e3"
        assert permissions.permission_sources[0].display == "My portfolio"

        assert permissions.parent_entities is not None
        assert permissions.parent_entities.primary is not None
        assert permissions.parent_entities.primary.id == "67ffd7e3"
        assert permissions.parent_entities.secondary == []

    async def test_empty_acl_when_inheriting(self) -> None:
        # `acl` comes back empty while the entity inherits its access
        # settings from `permissionSources`.
        payload = {
            "acl": {},
            "permissionSources": [
                {
                    "self": "https://api.tracker.yandex.net/v3/entities/portfolio/1",
                    "id": "1",
                    "display": "Portfolio",
                },
            ],
        }
        tracker, _ = make_tracker(payload)
        permissions = await tracker.get_entity_access("project", "1")

        assert permissions.acl.read is None
        assert permissions.acl.write is None
        assert permissions.acl.grant is None
        assert permissions.parent_entities is None


# --- update_entity_access -----------------------------------------------------


class TestUpdateEntityAccess:
    async def test_grant_with_model_sends_uppercase_keys(self) -> None:
        tracker, client = make_tracker(permissions_payload())
        grant = EntityAccessChange(
            read=EntityAccessRule(users=["username1", "username2"]),
            write=EntityAccessRule(groups=[1, 2]),
        )
        await tracker.update_entity_access("project", "655f8cc52", grant=grant)

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith(
            "/v3/entities/project/655f8cc52/extendedPermissions",
        )
        assert call["params"] is None
        assert sent_json(call) == {
            "acl": {
                "grant": {
                    "READ": {"users": ["username1", "username2"]},
                    "WRITE": {"groups": [1, 2]},
                },
            },
        }

    async def test_grant_and_revoke_with_dicts(self) -> None:
        tracker, client = make_tracker(permissions_payload())
        await tracker.update_entity_access(
            "project",
            "1",
            grant={"READ": {"users": ["username1"], "groups": [], "roles": []}},
            revoke={
                "READ": {"users": {"uid": 123}, "groups": 3, "roles": []},
                "WRITE": {"users": [], "groups": [], "roles": "FOLLOWER"},
            },
        )

        assert sent_json(client.calls[0]) == {
            "acl": {
                "grant": {
                    "READ": {"users": ["username1"], "groups": [], "roles": []},
                },
                "revoke": {
                    "READ": {"users": {"uid": 123}, "groups": 3, "roles": []},
                    "WRITE": {"users": [], "groups": [], "roles": "FOLLOWER"},
                },
            },
        }

    async def test_permission_sources_as_single_string(self) -> None:
        tracker, client = make_tracker(permissions_payload())
        await tracker.update_entity_access(
            "project",
            "655f8cc52",
            permission_sources="67ffd7e3",
        )

        assert sent_json(client.calls[0]) == {"permissionSources": "67ffd7e3"}

    async def test_permission_sources_as_sequence(self) -> None:
        tracker, client = make_tracker(permissions_payload())
        await tracker.update_entity_access(
            "project",
            "1",
            permission_sources=["a", "b"],
        )

        assert sent_json(client.calls[0]) == {"permissionSources": ["a", "b"]}

    async def test_empty_permission_sources_stops_inheriting(self) -> None:
        tracker, client = make_tracker(permissions_payload())
        await tracker.update_entity_access(
            "project",
            "655f8cc52",
            permission_sources=[],
            grant={"WRITE": {"users": [], "groups": 2, "roles": []}},
        )

        assert sent_json(client.calls[0]) == {
            "permissionSources": [],
            "acl": {"grant": {"WRITE": {"users": [], "groups": 2, "roles": []}}},
        }

    async def test_decodes_response(self) -> None:
        tracker, _ = make_tracker(permissions_payload())
        permissions = await tracker.update_entity_access(
            "project",
            "1",
            permission_sources=[],
        )

        assert isinstance(permissions, EntityPermissions)
        assert permissions.acl.read is not None
        assert permissions.acl.read.users[0].id == "11"

    async def test_nothing_to_change_raises_value_error(self) -> None:
        tracker, _ = make_tracker(permissions_payload())
        with pytest.raises(ValueError, match=r"grant.*revoke.*permission_sources"):
            await tracker.update_entity_access("project", "1")
