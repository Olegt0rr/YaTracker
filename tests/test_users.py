"""Tests for the users category and the `User`/`FullUser`/`UsersPage` structs.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/users/get-users
https://yandex.ru/support/tracker/ru/api/users/get-users-relative
https://yandex.ru/support/tracker/ru/api/users/get-user
https://yandex.ru/support/tracker/ru/api/users/get-user-info
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import TypeAdapter
from yatracker.types.user import FullUser, User, UsersPage

from tests.conftest import make_tracker

# The users-list, relative-pagination (per-item), get-user and get-myself
# endpoints all answer with (a list/object wrapping) this same user shape.
FULL_USER: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/users/1234567890",
    "uid": 1234567890,
    "login": "username",
    "trackerUid": 1234567890,
    "passportUid": 1234567890,
    "cloudUid": "bfbdrb1aa248abcd1234",
    "firstName": "Имя",
    "lastName": "Фамилия",
    "display": "Имя Фамилия",
    "email": "mail@example.com",
    "groups": [
        {
            "self": "https://api.tracker.yandex.net/v3/groups/5",
            "id": "5",
            "display": "Developers",
        },
    ],
    "external": False,
    "hasLicense": True,
    "dismissed": False,
    "useNewFilters": True,
    "disableNotifications": False,
    "firstLoginDate": "2019-08-22T14:56:57.981+0000",
    "lastLoginDate": "2022-06-22T17:44:32.981+0000",
    "welcomeMailSent": True,
}

# Relative-pagination sample additionally carries `sources` (position is
# documented but absent from every sample).
RELATIVE_USER: dict[str, Any] = {**FULL_USER, "sources": ["directory"]}

# Short user reference embedded into other API objects (issues, queues,
# comments, ...): only `self`, `id`, `display`.
USER_REF: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/users/1111",
    "id": "1111",
    "display": "Имя Фамилия",
}


class TestFullUserDecoding:
    def test_full_response_decodes(self) -> None:
        user = TypeAdapter(FullUser).validate_json(json.dumps(FULL_USER))
        assert user.url == "https://api.tracker.yandex.net/v3/users/1234567890"
        assert user.uid == "1234567890"
        assert user.login == "username"
        assert user.tracker_uid == "1234567890"
        assert user.passport_uid == "1234567890"
        assert user.cloud_uid == "bfbdrb1aa248abcd1234"
        assert user.first_name == "Имя"
        assert user.last_name == "Фамилия"
        assert user.display == "Имя Фамилия"
        assert user.email == "mail@example.com"
        assert user.groups is not None
        assert len(user.groups) == 1
        assert user.groups[0].id == "5"
        assert user.groups[0].display == "Developers"
        assert user.external is False
        assert user.has_license is True
        assert user.dismissed is False
        assert user.use_new_filters is True
        assert user.disable_notifications is False
        assert user.welcome_mail_sent is True
        assert user.first_login_date == datetime(
            2019,
            8,
            22,
            14,
            56,
            57,
            981000,
            tzinfo=timezone.utc,
        )
        assert user.last_login_date == datetime(
            2022,
            6,
            22,
            17,
            44,
            32,
            981000,
            tzinfo=timezone.utc,
        )
        # `id` is not present in any documented sample.
        assert user.id is None
        assert user.sources is None
        assert user.position is None

    def test_relative_response_decodes_sources(self) -> None:
        user = TypeAdapter(FullUser).validate_json(json.dumps(RELATIVE_USER))
        assert user.sources == ["directory"]

    def test_response_without_groups_decodes(self) -> None:
        payload = {k: v for k, v in FULL_USER.items() if k != "groups"}
        user = TypeAdapter(FullUser).validate_json(json.dumps(payload))
        assert user.groups is None


class TestShortUserRegression:
    def test_short_ref_decodes(self) -> None:
        """The legacy `User` short model still decodes `self`/`id`/`display`."""
        user = TypeAdapter(User).validate_json(json.dumps(USER_REF))
        assert user.url == "https://api.tracker.yandex.net/v3/users/1111"
        assert user.id == "1111"
        assert user.display == "Имя Фамилия"


class TestGetUsers:
    async def test_sends_get_and_decodes_list(self) -> None:
        tracker, client = make_tracker([FULL_USER])
        users = await tracker.get_users()
        assert len(users) == 1
        assert users[0].uid == "1234567890"
        assert isinstance(users[0], FullUser)

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/users")
        assert call["params"] is None

    async def test_sends_all_params(self) -> None:
        tracker, client = make_tracker([FULL_USER])
        await tracker.get_users(
            per_page=50,
            page=2,
            id_=12345,
            email="mail@example.com",
            group=5,
            expand="groups",
        )

        call = client.calls[0]
        assert call["params"] == {
            "perPage": "50",
            "page": "2",
            "id": "12345",
            "email": "mail@example.com",
            "group": "5",
            "expand": "groups",
        }

    async def test_none_params_are_not_sent(self) -> None:
        tracker, client = make_tracker([FULL_USER])
        await tracker.get_users()

        call = client.calls[0]
        assert call["params"] is None


class TestGetUsersRelative:
    async def test_sends_get_relative_path_and_decodes_page(self) -> None:
        tracker, client = make_tracker({"users": [FULL_USER], "hasNext": True})
        page = await tracker.get_users_relative()
        assert isinstance(page, UsersPage)
        assert page.has_next is True
        assert len(page.users) == 1
        assert page.users[0].login == "username"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/users/_relative")
        assert call["params"] is None

    async def test_sends_per_page_id_and_expand_params(self) -> None:
        tracker, client = make_tracker({"users": [], "hasNext": False})
        await tracker.get_users_relative(per_page=50, id_=1234567890, expand="groups")

        call = client.calls[0]
        assert call["params"] == {
            "perPage": "50",
            "id": "1234567890",
            "expand": "groups",
        }

    async def test_none_params_are_not_sent(self) -> None:
        tracker, client = make_tracker({"users": [], "hasNext": False})
        await tracker.get_users_relative()

        call = client.calls[0]
        assert call["params"] is None

    async def test_empty_page_decodes_defaults(self) -> None:
        tracker, client = make_tracker({})
        page = await tracker.get_users_relative()
        assert page.users == []
        assert page.has_next is False
        assert client.calls[0]["params"] is None


class TestGetUser:
    async def test_sends_get_with_user_id_in_path(self) -> None:
        tracker, client = make_tracker(FULL_USER)
        user = await tracker.get_user(1234567890)
        assert user.login == "username"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/users/1234567890")
        assert call["params"] is None

    async def test_accepts_login_style_id(self) -> None:
        tracker, client = make_tracker(FULL_USER)
        await tracker.get_user("login:12345")

        call = client.calls[0]
        assert call["url"].endswith("/users/login:12345")

    async def test_sends_expand_param(self) -> None:
        tracker, client = make_tracker(FULL_USER)
        await tracker.get_user("username", expand="groups")

        call = client.calls[0]
        assert call["params"] == {"expand": "groups"}

    async def test_none_expand_is_not_sent(self) -> None:
        tracker, client = make_tracker(FULL_USER)
        await tracker.get_user("username")

        call = client.calls[0]
        assert call["params"] is None


class TestGetMyself:
    async def test_sends_get_to_myself_endpoint(self) -> None:
        tracker, client = make_tracker(FULL_USER)
        user = await tracker.get_myself()
        assert isinstance(user, FullUser)
        assert user.login == "username"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/v3/myself")
        assert call["params"] is None

    async def test_sends_expand_param(self) -> None:
        tracker, client = make_tracker(FULL_USER)
        await tracker.get_myself(expand="groups")

        call = client.calls[0]
        assert call["params"] == {"expand": "groups"}


class TestIterUsers:
    async def test_walks_pages_and_stops_on_empty(self) -> None:
        user_1 = {**FULL_USER, "uid": 1}
        user_2 = {**FULL_USER, "uid": 2}
        page_1 = {"users": [user_1, user_2], "hasNext": True}
        page_2 = {"users": [], "hasNext": False}
        tracker, client = make_tracker(None)
        client.responses = [
            (200, json.dumps(page_1).encode(), {}),
            (200, json.dumps(page_2).encode(), {}),
        ]

        users = [user async for user in tracker.iter_users(per_page=2)]

        assert [u.uid for u in users] == ["1", "2"]
        assert len(client.calls) == 2
        # first call: no `id` cursor
        assert client.calls[0]["params"] == {"perPage": "2"}
        # second call: uid of the last user from the first page
        assert client.calls[1]["params"] == {"perPage": "2", "id": "2"}

    async def test_stops_immediately_on_empty_first_page(self) -> None:
        tracker, client = make_tracker({"users": [], "hasNext": False})

        users = [user async for user in tracker.iter_users()]

        assert users == []
        assert len(client.calls) == 1

    async def test_skips_cursor_user_and_stops_when_not_advancing(self) -> None:
        """The docs describe `id` as the user the next page starts *from*.

        With such an inclusive cursor the last user of a page comes back
        at the top of the next one, and the final page is never empty.
        """
        user_1, user_2, user_3 = ({**FULL_USER, "uid": i} for i in (1, 2, 3))
        tracker, client = make_tracker(None)
        client.responses = [
            (
                200,
                json.dumps({"users": [user_1, user_2], "hasNext": True}).encode(),
                {},
            ),
            (
                200,
                json.dumps({"users": [user_2, user_3], "hasNext": True}).encode(),
                {},
            ),
            (200, json.dumps({"users": [user_3], "hasNext": False}).encode(), {}),
        ]

        users = [user async for user in tracker.iter_users(per_page=2)]

        assert [u.uid for u in users] == ["1", "2", "3"]
        assert len(client.calls) == 3
        assert client.calls[2]["params"] == {"perPage": "2", "id": "3"}

    async def test_stops_when_page_does_not_advance_despite_has_next(self) -> None:
        """Guards against a server that keeps `hasNext: true` forever."""
        user_1, user_2 = ({**FULL_USER, "uid": i} for i in (1, 2))
        same_page = json.dumps({"users": [user_1, user_2], "hasNext": True}).encode()
        tracker, client = make_tracker(None)
        client.responses = [(200, same_page, {}), (200, same_page, {})]

        users = [user async for user in tracker.iter_users()]

        assert [u.uid for u in users] == ["1", "2"]
        assert len(client.calls) == 2

    async def test_stops_on_has_next_false_even_without_cursor_repeat(self) -> None:
        user_1 = {**FULL_USER, "uid": 1}
        tracker, client = make_tracker({"users": [user_1], "hasNext": False})

        users = [user async for user in tracker.iter_users()]

        assert [u.uid for u in users] == ["1"]
        assert len(client.calls) == 1

    async def test_forwards_expand_param(self) -> None:
        tracker, client = make_tracker({"users": [], "hasNext": False})

        _ = [user async for user in tracker.iter_users(expand="groups")]

        assert client.calls[0]["params"] == {"expand": "groups"}

    async def test_per_page_one_is_sent_as_two(self) -> None:
        """A one-user page could only ever hold the (inclusive) cursor."""
        user_1, user_2, user_3 = ({**FULL_USER, "uid": i} for i in (1, 2, 3))
        tracker, client = make_tracker(None)
        client.responses = [
            (
                200,
                json.dumps({"users": [user_1, user_2], "hasNext": True}).encode(),
                {},
            ),
            (
                200,
                json.dumps({"users": [user_2, user_3], "hasNext": False}).encode(),
                {},
            ),
        ]

        users = [user async for user in tracker.iter_users(per_page=1)]

        assert [u.uid for u in users] == ["1", "2", "3"]
        assert client.calls[0]["params"] == {"perPage": "2"}
        assert client.calls[1]["params"] == {"perPage": "2", "id": "2"}
