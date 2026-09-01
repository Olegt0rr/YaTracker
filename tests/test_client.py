"""Tests for the client request/response pipeline."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import pytest
from yatracker import YaTracker
from yatracker.exceptions import (
    AlreadyExistsError,
    NotAuthorizedError,
    ObjectNotFoundError,
    SufficientRightsError,
    YaTrackerError,
)
from yatracker.tracker.client import AIOHTTPClient, _get_ssl_context
from yatracker.types import FullIssue

from tests.conftest import FakeClient, full_issue_body

if TYPE_CHECKING:
    # `typing.Self` only exists on 3.11+, the package still supports 3.10
    from typing import Self


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, NotAuthorizedError),
        (403, SufficientRightsError),
        (404, ObjectNotFoundError),
        (409, AlreadyExistsError),
        (500, YaTrackerError),
    ],
)
async def test_error_statuses_raise_typed_exceptions(status, error) -> None:
    client = FakeClient(status=status, body=b'{"errors": {}}')
    with pytest.raises(error):
        await client.request(method="GET", uri="/issues/TEST-1")


async def test_request_without_payload_sends_no_body() -> None:
    client = FakeClient()
    await client.request(method="GET", uri="/issues/TEST-1")
    assert client.calls[0]["data"] is None


async def test_request_with_payload_sends_json_bytes() -> None:
    client = FakeClient()
    await client.request(method="POST", uri="/issues/", payload={"summary": "s"})
    data = client.calls[0]["data"]
    assert bytes(data._value) == b'{"summary":"s"}'


async def test_get_issue_decodes_full_issue() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    issue = await tracker.get_issue("TEST-1")
    assert isinstance(issue, FullIssue)
    assert issue.key == "TEST-1"
    assert issue.status.key == "open"


async def test_move_issue_params_are_strings() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    await tracker.move_issue(
        "TEST-1",
        "QUEUE",
        notify=False,
        notify_author=True,
        move_all_fields=True,
        initial_status=True,
    )
    params = client.calls[0]["params"]
    assert params == {
        "queue": "QUEUE",
        "notify": "false",
        "notifyAuthor": "true",
        "moveAllFields": "true",
        "initialStatus": "true",
    }


async def test_find_issues_sends_filters() -> None:
    client = FakeClient(body=b"[]")
    tracker = YaTracker(client=client)
    await tracker.find_issues(
        filter_={"queue": "TEST"},
        query="Key: TEST-1",
        keys="TEST-1",
        order="+key",
    )
    call = client.calls[0]
    payload = json.loads(bytes(call["data"]._value))
    assert payload == {
        "filter": {"queue": "TEST"},
        "query": "Key: TEST-1",
        "keys": "TEST-1",
    }
    assert call["params"] == {"order": "+key"}


async def test_tracker_async_context_manager_closes_client() -> None:
    client = FakeClient(body=full_issue_body())
    closed = False

    async def close() -> None:
        nonlocal closed
        closed = True

    client.close = close  # type: ignore[method-assign]
    async with YaTracker(client=client) as tracker:
        assert await tracker.get_issue("TEST-1")
    assert closed is True


def test_ssl_context_is_built_once() -> None:
    assert _get_ssl_context() is _get_ssl_context()


async def test_close_without_session_is_a_noop() -> None:
    client = AIOHTTPClient(org_id="1", token="token")
    assert client._session is None
    await client.close()


async def test_get_session_is_cached_and_recreated_after_close() -> None:
    client = AIOHTTPClient(org_id="1", token="token")
    session = client.get_session()
    assert client.get_session() is session
    assert session.headers["X-Org-ID"] == "1"

    await session.close()
    new_session = client.get_session()
    assert new_session is not session
    assert not new_session.closed

    await client.close()
    assert new_session.closed


async def test_close_is_idempotent() -> None:
    client = AIOHTTPClient(org_id="1", token="token")
    session = client.get_session()
    await client.close()
    assert session.closed
    # the second call must not try to close an already closed session
    await client.close()


class _FakeResponse:
    """Minimal stand-in for `aiohttp.ClientResponse`."""

    def __init__(self, status: int, body: bytes, headers: dict[str, str]) -> None:
        self.status = status
        self.headers = headers
        self._body = body

    async def read(self) -> bytes:
        return self._body

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        return


class _FakeSession:
    """Minimal stand-in for `aiohttp.ClientSession`."""

    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.calls: list[tuple[str, str]] = []

    def request(self, method: str, url: str, **_kwargs: object) -> _FakeResponse:
        self.calls.append((method, url))
        return self._response


async def test_make_request_returns_status_body_and_headers() -> None:
    client = AIOHTTPClient(org_id="1", token="token")
    session = _FakeSession(_FakeResponse(200, b'{"ok": true}', {"X-Total-Count": "3"}))
    client.get_session = lambda: session  # type: ignore[method-assign,return-value]

    body, headers = await client.request_with_headers(
        method="GET",
        uri="/issues/TEST-1",
    )

    assert body == b'{"ok": true}'
    assert headers == {"X-Total-Count": "3"}
    assert session.calls == [
        ("GET", "https://api.tracker.yandex.net/v3/issues/TEST-1"),
    ]


async def test_make_request_logs_error_responses(caplog) -> None:
    client = AIOHTTPClient(org_id="1", token="token")
    session = _FakeSession(_FakeResponse(500, b"boom", {}))
    client.get_session = lambda: session  # type: ignore[method-assign,return-value]

    with (
        caplog.at_level(logging.WARNING, logger="yatracker.tracker.client"),
        pytest.raises(YaTrackerError, match="boom"),
    ):
        await client.request(method="GET", uri="/issues/TEST-1")

    assert "boom" in caplog.text
