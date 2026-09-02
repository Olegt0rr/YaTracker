"""Tests for the gaps (employee absences) category and its structs.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/gaps/post-gaps
https://yandex.ru/support/tracker/ru/api/gaps/search-gaps
https://yandex.ru/support/tracker/ru/api/gaps/delete-gaps
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest
from yatracker import YaTracker
from yatracker.tracker.categories.gaps import MAX_GAPS_PER_REQUEST
from yatracker.types.gap import Gap, GapsSearchResult

from tests.conftest import FakeClient, make_tracker, sent_json

BASE = "https://api.tracker.yandex.net/v3"

USER_GAP_1: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/users/1234567890123456",
    "uid": 1234567890123456,
    "login": "username1",
    "trackerUid": 1234567890123456,
    "passportUid": 1234567890,
    "cloudUid": "ajehs6sinuiii1234567",
    "firstName": "Имя",
    "lastName": "Фамилия",
    "display": "Иван Иванов",
    "email": "username@example.com",
    "external": False,
    "dismissed": False,
    "firstLoginDate": "2024-04-10T10:15:47.272+0000",
    "lastLoginDate": "2026-07-23T08:11:01.861+0000",
    "sources": ["directory"],
}

USER_GAP_2: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/users/9876543210987654",
    "uid": 9876543210987654,
    "login": "username2",
    "trackerUid": 9876543210987654,
    "passportUid": 9876543210,
    "cloudUid": "ajehs6sinuiii9876543",
    "firstName": "Имя",
    "lastName": "Фамилия",
    "display": "Петр Петров",
    "email": "username@example.com",
    "external": False,
    "dismissed": False,
    "firstLoginDate": "2024-03-05T09:00:00.000+0000",
    "lastLoginDate": "2026-07-22T17:30:00.000+0000",
    "sources": ["directory"],
}

# POST /v3/gaps response sample (two gaps, one per user).
CREATE_GAPS_RESPONSE: dict[str, Any] = {
    "gaps": [
        {
            "id": "68340a1f2b4c1a3d5e7f9011",
            "user": USER_GAP_1,
            "workflow": "vacation",
            "from": "2026-07-01T00:00:00.000+0000",
            "to": "2026-07-15T00:00:00.000+0000",
            "fullDay": True,
            "workInAbsence": False,
        },
        {
            "id": "68340a1f2b4c1a3d5e7f9012",
            "user": USER_GAP_2,
            "workflow": "trip",
            "from": "2026-07-10T00:00:00.000+0000",
            "to": "2026-07-20T00:00:00.000+0000",
            "fullDay": False,
            "workInAbsence": False,
        },
    ],
}

# POST /v3/gaps/_search response sample.
SEARCH_GAPS_RESPONSE: dict[str, Any] = {
    "userGaps": [
        {
            "user": USER_GAP_1,
            "gaps": [
                {
                    "id": "68340a1f2b4c1a3d5e7f9011",
                    "workflow": "vacation",
                    "from": "2026-07-01T00:00:00.000+0000",
                    "to": "2026-07-15T00:00:00.000+0000",
                    "fullDay": True,
                    "workInAbsence": False,
                },
            ],
        },
        {
            "user": USER_GAP_2,
            "gaps": [
                {
                    "id": "68340a1f2b4c1a3d5e7f9012",
                    "workflow": "trip",
                    "from": "2026-08-04T00:00:00.000+0000",
                    "to": "2026-08-08T00:00:00.000+0000",
                    "fullDay": True,
                    "workInAbsence": False,
                },
            ],
        },
    ],
    "hasMore": False,
}


# --- create_gaps -------------------------------------------------------


async def test_create_gaps_sends_camel_cased_body() -> None:
    tracker, client = make_tracker(CREATE_GAPS_RESPONSE)
    gaps = await tracker.create_gaps(
        [
            {
                "id": "68340a1f2b4c1a3d5e7f9011",
                "user": "username1",
                "workflow": "vacation",
                "from_": "2026-07-01T00:00:00.000Z",
                "to": "2026-07-15T00:00:00.000Z",
                "full_day": True,
                "work_in_absence": False,
            },
            {
                "user": "username2",
                "workflow": "trip",
                "from": datetime(2026, 7, 10, tzinfo=timezone.utc),
                "to": datetime(2026, 7, 20, tzinfo=timezone.utc),
            },
        ],
    )

    assert len(gaps) == 2
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/gaps"
    assert sent_json(call) == {
        "gaps": [
            {
                "id": "68340a1f2b4c1a3d5e7f9011",
                "user": "username1",
                "workflow": "vacation",
                "from": "2026-07-01T00:00:00.000Z",
                "to": "2026-07-15T00:00:00.000Z",
                "fullDay": True,
                "workInAbsence": False,
            },
            {
                "user": "username2",
                "workflow": "trip",
                "from": "2026-07-10T00:00:00.000+0000",
                "to": "2026-07-20T00:00:00.000+0000",
            },
        ],
    }


async def test_create_gaps_decodes_response() -> None:
    tracker, _ = make_tracker(CREATE_GAPS_RESPONSE)
    gaps = await tracker.create_gaps(
        [{"user": "u", "workflow": "vacation", "from_": "a", "to": "b"}],
    )

    assert isinstance(gaps[0], Gap)
    gap = gaps[0]
    assert gap.id == "68340a1f2b4c1a3d5e7f9011"
    assert gap.workflow == "vacation"
    assert gap.from_ == datetime(2026, 7, 1, tzinfo=timezone.utc)
    assert gap.to == datetime(2026, 7, 15, tzinfo=timezone.utc)
    assert gap.full_day is True
    assert gap.work_in_absence is False
    assert gap.user is not None
    assert gap.user.login == "username1"
    assert gap.user.display == "Иван Иванов"

    other = gaps[1]
    assert other.full_day is False


async def test_create_gaps_rejects_over_100() -> None:
    tracker, client = make_tracker(CREATE_GAPS_RESPONSE)
    gaps = [
        {"user": "u", "workflow": "vacation", "from_": "a", "to": "b"},
    ] * (MAX_GAPS_PER_REQUEST + 1)

    with pytest.raises(ValueError, match="100"):
        await tracker.create_gaps(gaps)

    assert client.calls == []


async def test_create_gaps_warns_on_naive_datetime() -> None:
    tracker, _ = make_tracker(CREATE_GAPS_RESPONSE)
    with pytest.warns(UserWarning, match="naive datetime") as record:
        await tracker.create_gaps(
            [
                {
                    "user": "u",
                    "workflow": "vacation",
                    "from_": datetime(2026, 7, 1, 0, 0, 0),  # noqa: DTZ001
                    "to": datetime(2026, 7, 15, 0, 0, 0),  # noqa: DTZ001
                },
            ],
        )

    # the warning must point at the caller, not at library internals
    assert record[0].filename == __file__


# --- create_gap ----------------------------------------------------------


async def test_create_gap_delegates_to_create_gaps() -> None:
    tracker, client = make_tracker({"gaps": [CREATE_GAPS_RESPONSE["gaps"][0]]})
    gap = await tracker.create_gap(
        "username1",
        "vacation",
        datetime(2026, 7, 1, tzinfo=timezone.utc),
        datetime(2026, 7, 15, tzinfo=timezone.utc),
        gap_id="68340a1f2b4c1a3d5e7f9011",
        full_day=True,
        work_in_absence=False,
    )

    assert isinstance(gap, Gap)
    assert gap.id == "68340a1f2b4c1a3d5e7f9011"
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/gaps"
    assert sent_json(call) == {
        "gaps": [
            {
                "id": "68340a1f2b4c1a3d5e7f9011",
                "user": "username1",
                "workflow": "vacation",
                "from": "2026-07-01T00:00:00.000+0000",
                "to": "2026-07-15T00:00:00.000+0000",
                "fullDay": True,
                "workInAbsence": False,
            },
        ],
    }


async def test_create_gap_omits_none_optional_fields() -> None:
    tracker, client = make_tracker({"gaps": [CREATE_GAPS_RESPONSE["gaps"][1]]})
    await tracker.create_gap(
        "username2",
        "trip",
        "2026-07-10T00:00:00.000Z",
        "2026-07-20T00:00:00.000Z",
    )

    payload = sent_json(client.calls[0])["gaps"][0]
    assert "id" not in payload
    assert "fullDay" not in payload
    assert "workInAbsence" not in payload


async def test_create_gap_warns_on_naive_datetime() -> None:
    tracker, _ = make_tracker({"gaps": [CREATE_GAPS_RESPONSE["gaps"][0]]})
    with pytest.warns(UserWarning, match="naive datetime") as record:
        await tracker.create_gap(
            "username1",
            "vacation",
            datetime(2026, 7, 1),  # noqa: DTZ001
            datetime(2026, 7, 15),  # noqa: DTZ001
        )

    # the warning must point at the caller, not at library internals
    assert record[0].filename == __file__


async def test_create_gap_raises_when_nothing_saved() -> None:
    tracker, _ = make_tracker({"gaps": []})
    with pytest.raises(ValueError, match="no absence record"):
        await tracker.create_gap(
            "username1",
            "vacation",
            datetime(2026, 7, 1, tzinfo=timezone.utc),
            datetime(2026, 7, 15, tzinfo=timezone.utc),
        )


# --- search_gaps / iter_gaps ----------------------------------------------


async def test_search_gaps_sends_users_and_window() -> None:
    tracker, client = make_tracker(SEARCH_GAPS_RESPONSE)
    result = await tracker.search_gaps(
        ["username1", "username2"],
        from_="2026-07-01T00:00:00.000Z",
        to="2026-08-31T23:59:59.999Z",
        per_page=20,
        page=1,
    )

    assert isinstance(result, GapsSearchResult)
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/gaps/_search"
    assert call["params"] == {"perPage": "20", "page": "1"}
    assert sent_json(call) == {
        "users": ["username1", "username2"],
        "from": "2026-07-01T00:00:00.000Z",
        "to": "2026-08-31T23:59:59.999Z",
    }
    assert result.has_more is False
    assert len(result.user_gaps) == 2


async def test_search_gaps_omits_none_params_and_body_fields() -> None:
    tracker, client = make_tracker(SEARCH_GAPS_RESPONSE)
    await tracker.search_gaps(["username1"])

    call = client.calls[0]
    assert call["params"] is None
    assert sent_json(call) == {"users": ["username1"]}


async def test_search_gaps_stringifies_int_user_ids() -> None:
    tracker, client = make_tracker(SEARCH_GAPS_RESPONSE)
    await tracker.search_gaps([111, 222])

    assert sent_json(client.calls[0])["users"] == ["111", "222"]


async def test_search_gaps_decodes_user_gaps() -> None:
    tracker, _ = make_tracker(SEARCH_GAPS_RESPONSE)
    result = await tracker.search_gaps(["username1", "username2"])

    first = result.user_gaps[0]
    assert first.user.login == "username1"
    assert len(first.gaps) == 1
    assert first.gaps[0].workflow == "vacation"
    # the search endpoint groups by user and leaves the nested one out
    assert first.gaps[0].user is None


async def test_iter_gaps_paginates_until_has_more_false() -> None:
    page1 = {
        "userGaps": [{"user": USER_GAP_1, "gaps": []}],
        "hasMore": True,
    }
    page2 = {
        "userGaps": [{"user": USER_GAP_2, "gaps": []}],
        "hasMore": False,
    }
    client = FakeClient(
        responses=[
            (200, json.dumps(page1).encode(), {}),
            (200, json.dumps(page2).encode(), {}),
        ],
    )
    tracker = YaTracker(client=client)

    results = [
        ug async for ug in tracker.iter_gaps(["username1", "username2"], per_page=1)
    ]

    assert [ug.user.login for ug in results] == ["username1", "username2"]
    assert client.calls[0]["params"] == {"perPage": "1", "page": "1"}
    assert client.calls[1]["params"] == {"perPage": "1", "page": "2"}


async def test_iter_gaps_stops_when_page_is_empty() -> None:
    client = FakeClient(body=json.dumps({"userGaps": [], "hasMore": True}).encode())
    tracker = YaTracker(client=client)

    results = [ug async for ug in tracker.iter_gaps(["username1"])]

    assert results == []
    assert len(client.calls) == 1


# --- delete_gap / delete_gaps ---------------------------------------------


async def test_delete_gap_sends_single_id() -> None:
    tracker, client = make_tracker(status=204)
    assert await tracker.delete_gap("68340a1f2b4c1a3d5e7f9011") is True

    call = client.calls[0]
    assert call["method"] == "DELETE"
    assert call["url"] == f"{BASE}/gaps"
    assert call["params"] == {"gapIds": "68340a1f2b4c1a3d5e7f9011"}


async def test_delete_gaps_joins_ids_with_comma() -> None:
    tracker, client = make_tracker(status=204)
    result = await tracker.delete_gaps(
        ["68340a1f2b4c1a3d5e7f9011", "68340a1f2b4c1a3d5e7f9012"],
    )

    assert result is True
    call = client.calls[0]
    assert call["method"] == "DELETE"
    assert call["url"] == f"{BASE}/gaps"
    assert call["params"] == {
        "gapIds": "68340a1f2b4c1a3d5e7f9011,68340a1f2b4c1a3d5e7f9012",
    }


async def test_delete_gaps_rejects_over_100() -> None:
    tracker, client = make_tracker(status=204)
    with pytest.raises(ValueError, match="100"):
        await tracker.delete_gaps(["id"] * (MAX_GAPS_PER_REQUEST + 1))

    assert client.calls == []


async def test_delete_gaps_rejects_bare_string() -> None:
    tracker, client = make_tracker(status=204)
    with pytest.raises(TypeError, match="sequence of absence record ids"):
        await tracker.delete_gaps("68340a1f2b4c1a3d5e7f9011")  # type: ignore[arg-type]

    assert client.calls == []


async def test_search_gaps_rejects_bare_string() -> None:
    tracker, client = make_tracker(SEARCH_GAPS_RESPONSE)
    with pytest.raises(TypeError, match="sequence of logins or ids"):
        await tracker.search_gaps("username1")  # type: ignore[arg-type]

    assert client.calls == []


async def test_iter_gaps_rejects_bare_string() -> None:
    tracker, client = make_tracker(SEARCH_GAPS_RESPONSE)
    with pytest.raises(TypeError, match="sequence of logins or ids"):
        async for _ in tracker.iter_gaps("username1"):  # type: ignore[arg-type]
            pass

    assert client.calls == []
